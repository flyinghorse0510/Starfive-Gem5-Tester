import subprocess, os, sys
import yaml
import logging
from datetime import datetime
from typing import List
from pydantic.v1.utils import deep_update


# execute shell command
def exec_shell_cmd(
    cmd: str,
    writeStdout: bool = False,
    writeStderr: bool = False,
    directStdout: bool = False,
    directStderr: bool = False,
) -> tuple:
    # run command
    process = subprocess.Popen(
        ["bash", "-c", cmd],
        stdout=sys.stdout if directStdout else subprocess.PIPE,
        stderr=sys.stderr if directStderr else subprocess.PIPE,
    )
    # get output and return code
    stdoutTxt, stderrTxt = process.communicate()
    exitCode = process.returncode
    # write output
    if writeStdout and not directStdout:
        sys.stdout.write(stdoutTxt)
    if writeStderr and not directStderr:
        sys.stderr.write(stderrTxt)
    # return result
    return (
        "" if directStdout else str(stdoutTxt, encoding="utf-8").strip("\n"),
        "" if directStderr else str(stderrTxt, encoding="utf-8").strip("\n"),
        exitCode,
    )


# create directory if necessary
def create_dir(path: str) -> bool:
    _, _, exitCode = exec_shell_cmd("mkdir -p %s" % (path), directStdout=False, directStderr=False)
    return True if exitCode == 0 else False

# delete directory
def del_dir(path: str, extName: str = None) -> bool:
    if extName is not None:
        _, _, exitCode = exec_shell_cmd(f"rm -rf {path}/*{extName}", directStdout=False, directStderr=False)
    else:
        _, _, exitCode = exec_shell_cmd(f"rm -rf {path}", directStdout=False, directStderr=False)
    return True if exitCode == 0 else False


# clean (optionally specified) contents within directory
def clean_dir(path: str, extName: str = None):
    # delete file(directory)
    del_dir(path, extName)
    # create directory if necessary
    create_dir(path)

# get repo root directory
def get_repo_root() -> str:
    filePath = os.path.dirname(__file__)
    return os.path.split(filePath)[0]


# get script directory
def get_script_root() -> str:
    filePath = os.path.dirname(__file__)
    return filePath

def get_script_name() -> str:
    fileName = os.path.basename(__file__)
    return fileName

# recursively load yaml configs with `include` field
def recursive_load_yaml(file: str) -> dict:
    yamlConfigDataList = []
    yamlConfigPathList = []
    yamlFileDir = get_script_root()
    # append filepath for further recursively load
    yamlConfigPathList.append(file)
    while len(yamlConfigPathList) > 0:
        yamlFilePath = yamlConfigPathList.pop(0)
        # print(f"Processing YAML config {yamlFilePath}")
        # open and load the yaml file
        yamlFile = open(yamlFilePath, "r")
        yamlConfig = yaml.full_load(yamlFile)
        yamlFile.close()
        yamlConfigDataList.append(yamlConfig)
        # append included yaml file path to list for further load
        if (yamlConfig.get("include",None) is not None) and len(yamlConfig["include"]) > 0:
            # recursively load yaml config
            for includedYamlFile in yamlConfig["include"]:
                # make the path relative to the script
                yamlConfigPathList.append(os.path.join(yamlFileDir, includedYamlFile))

    # update and merge the configs
    base_yaml = yamlConfigDataList.pop()
    for i in range(len(yamlConfigDataList)):
        update_yaml = yamlConfigDataList.pop()
        base_yaml = deep_update(base_yaml, update_yaml)

    base_yaml["include"] = []

    # extend specified relative path parameters to absolute path
    if ("relative_path_list" in base_yaml) and (
        len(base_yaml["relative_path_list"]) > 0
    ):
        repoRootDir = get_repo_root()
        for relative_path in base_yaml["relative_path_list"]:
            if relative_path not in base_yaml:
                # the parameter doesn't exist
                continue
            for i in range(len(base_yaml[relative_path])):
                base_yaml[relative_path][i] = os.path.join(
                    repoRootDir, base_yaml[relative_path][i]
                )

    return base_yaml

# Invoke multiple yaml files
def recursive_load_yamls(*args) -> dict :
    """
        This is wrapper around
        recursive_load_yaml, that flattens
        the base_yaml file. The rationale
        is to add generated parameters to the
        base_yaml
    """
    base_yaml = dict()
    for arg in args : 
        assert(isinstance(arg,str))
        assert(os.path.isfile(arg))
        base_yaml.update(recursive_load_yaml(arg))
    return base_yaml

# dump yaml configs to specific file
def dump_config(path: str, configDict: dict):
    # dump the final yaml configs to file
    configDictFile = open(path, "w")
    yaml.dump(configDict, configDictFile, default_flow_style=False)
    configDictFile.close()


# dump given string to specific file
def dump_str_file(path: str, data: str):
    # dump the string to file
    dumpFile = open(path, "w")
    dumpFile.write(data)
    dumpFile.close()


# dump run_summary to specific file
def dump_run_summary(path: str, taskResults: list):
    runSummaryFile = open(path, "w")
    runSummaryFile.write("time(s), retCode, status, outputDir\n")
    for result in taskResults:
        runSummaryFile.write(
            f"{result['time']}, {result['retCode']}, {'SUCCESS' if result['retCode'] == 0 else 'ERROR'}, {result['outputDir']}\n"
        )
    runSummaryFile.close()


def get_parameter_space() -> list:
    pass


def get_all_target_dir(root_dir: str, target: str):
    # Recursive function to find all target files in the folder and its subfolders
    def find_output_dirs(folder):
        output_dirs = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file == target:
                    # Check if the filepath contains "CHECKPNT"
                    if "CHECKPNT" not in root:
                        output_dirs.append(root)
                    else:
                        logging.debug(f"Skip: {root}")
        return output_dirs

    # Call the function to find all "stats.txt" files in "ARM_FS" folder and filter out files with "CHECKPNT" in their path
    output_dirs = find_output_dirs(root_dir)
    return output_dirs


# check if the key exists in dictionary, if not, then return False;
# If the key exists:
# 1. The element is an empty list or dict, then return False
# 2. Otherwise, return True
def check_key(parsDict: dict, key: str):
    if (key in parsDict) and (parsDict[key] is not None):
        if (type(parsDict[key]) == list) or (type(parsDict[key]) == dict):
            if len(parsDict[key]) == 0:
                return False
        return True
    return False

# check if the key exists in dictionary, if not, then return None;
# If the key exists:
# 1. The element is an empty list or dict, then return None
# 2. The index is not None, then return the element's indexed value
# 3. The index is None, then return the element
def check_and_fetch_key(parsDict: dict, key: str, index = None): # type: ignore
    if check_key(parsDict, key):
        if index is not None:
            return parsDict[key][index]
        else:
            return parsDict[key]
    return None

def getNumGenCpus(runtimeConfig: dict) -> int :
    effective_cpu_list = check_and_fetch_key(runtimeConfig, "effective_cpu_list")
    numCpus = -1
    if (effective_cpu_list is not None)  :
        numCpus = len([c for c in effective_cpu_list if c >= 0])
    return numCpus
    
def getNumGenDmas(runtimeConfig: dict) -> int :
    effective_dma_list = check_and_fetch_key(runtimeConfig, "effective_dma_list")
    numDmas = -1
    if (effective_dma_list is not None)  :
        numDmas = len([d for d in effective_dma_list if d >= 0])
    return numDmas

# download remote file(with URL) into specific directory and return the file path
def download_to_dir(url: str, targetDir: str) -> str:
    if targetDir is None or url is None:
        return None
    # create directory if necessary
    create_dir(targetDir)
    # download the file
    fileName = os.path.basename(url)
    filePath = os.path.join(targetDir, fileName)
    exec_shell_cmd(f"curl -SL --output {filePath} {url}", False, False, True, True)
    # return the file path
    return filePath


# extract the archived file into specific directory
def extract_to_dir(archivedFilePath: str, targetDir: str) -> bool:
    # file to be extracted shouldn't be None
    if archivedFilePath is None:
        return False

    if targetDir is None:
        # use the same folder as archived file
        targetDir = os.path.dirname(archivedFilePath)

    # create directory if necessary
    create_dir(targetDir)

    # bash command used to extract file
    extractCmd = {
        ".tar.gz": "tar -xzf %s -C %s",
        ".tgz": "tar -xzf %s -C %s",
        ".tar.bz2": "tar -xjf %s -C %s",
        ".tbz2": "tar -xjf %s -C %s",
        ".tar": "tar -xf %s -C %s",
        ".bz2": "cp %s %s && cd %s && bzip2 -d %s",
        ".gz": "gzip -d %s -C %s",
        ".zip": "unzip %s -d %s",
    }

    for archiveExt in extractCmd:
        # find extension match, extract the file
        if archivedFilePath.endswith(archiveExt):
            if archiveExt != ".bz2":
                _, _, exitCode = exec_shell_cmd(
                    extractCmd[archiveExt] % (archivedFilePath, targetDir),
                    False,
                    False,
                    True,
                    True,
                )
            else:
                _, _, exitCode = exec_shell_cmd(
                    extractCmd[archiveExt]
                    % (
                        archivedFilePath,
                        targetDir,
                        targetDir,
                        os.path.join(targetDir, os.path.basename(archivedFilePath)),
                    ),
                    False,
                    False,
                    True,
                    True,
                )

            return True if exitCode == 0 else False

    # none extension match, currently not supported file type
    return False

# get the list of files with (optionally) specified file-name extension under the given directory (non-recursive)
def get_file_list(targetDir: str, fileExtList: list = None):
    fileList = [os.path.join(targetDir, f) for f in os.listdir(targetDir) if os.path.isfile(os.path.join(targetDir, f))]
    if fileExtList is not None and len(fileExtList) > 0:
        filteredFileList = []
        for filePath in fileList:
            fileExt = os.path.splitext(filePath)[1]
            for ext in fileExtList:
                if ext == fileExt:
                    filteredFileList.append(filePath)
                    break
        return filteredFileList
    else:
        return fileList

# get current timestamp in string format
def get_current_timestamp() -> str:
    return datetime.now().strftime('%Y-%m-%d-%H:%M:%S')

# get current username
def get_current_user() -> str:
    return os.environ["USER"]

# construct environment variable which can force to load specific shared libraries
# if `libPath` is invalid, "" will be returned
# if `libPath` is a shared library, it will be force-loaded
# if `libPath` is a directory, all shared libraries under that folder will be force-loaded (recursive load not supported currently)
# it is highly recommended that `libPath` is an absolute path
def force_load_lib(libPath: str, hintUser: bool = False) -> str:
    forceLoadStr = "LD_PRELOAD=\""
    
    # invalid path
    if libPath is None or type(libPath) != str or len(libPath) == 0:
        return ""
    if not os.path.exists(libPath):
        return ""
    
    # path is file
    if os.path.isfile(libPath):
        # check if the file is a shared library
        if not libPath.endswith(".so"):
            # not a shared library
            return ""
        if hintUser:
            print(f"Force loading shared library ==> {libPath}")
        forceLoadStr += f"{libPath}\""
        return forceLoadStr
    
    # path is directory
    if os.path.isdir(libPath):
        # get all shared libraries under that folder
        libList = get_file_list(libPath, [".so"])
        if len(libList) == 0:
            # no shared libraries found
            return ""
        for sharedLib in libList:
            forceLoadStr += f" {sharedLib}"
            if hintUser:
                print(f"Force load shared library ==> {sharedLib}")
        forceLoadStr += "\""
        return forceLoadStr
    
    return ""
    
    
    