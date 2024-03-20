import time, sys, os
import argparse, yaml
from multiprocessing import Process, Queue, Pool
from copy import deepcopy
from datetime import datetime

import util
import starfive_fs_utility

_tab = "\t"


def worker_process(config):
    args = config[0]
    configDict: dict = config[1]
    parameterSpaceList = config[2]
    output_dir = args.output_dir
    # construct output folder path
    parameterDirName = ""
    dimParameterSpace = len(parameterSpaceList)
    for i in range(dimParameterSpace):
        parameter = parameterSpaceList[i]
        parameterDirName += f"{parameter.replace('-','_')}.{str(configDict[parameter][0]).replace(',','.')}"
        if i != dimParameterSpace - 1:
            parameterDirName += "_"
    output_dir = os.path.join(output_dir, parameterDirName)
    # create output folder
    util.create_dir(output_dir)
    # dump config files
    util.dump_config(os.path.join(output_dir, "cmd_config.yaml"), configDict)
    # denormalize working set
    if (
        ("num-cpus" in configDict)
        and ("size-ws" in configDict)
        and (configDict["num-cpus"] is not None)
        and (configDict["size-ws"] is not None)
    ):
        configDict["size-ws"][0] *= configDict["num-cpus"][0]
    # construct the gem5 running command
    gem5Cmd = f"{args.root_repo}/build/{configDict['ISA']}_{configDict['CCPROT']}/{configDict['BUILDTYPE']}"
    # add debug flags
    if util.check_and_fetch_key(configDict, "debug_flags", 0) is not None:
        # construct debug flags
        gem5Cmd += " --debug-flags="
        numDebugFlags = len(configDict["debug_flags"])
        for i in range(numDebugFlags):
            gem5Cmd += f"{configDict['debug_flags'][i]}"
            if i != numDebugFlags - 1:
                gem5Cmd += ","
    # specify debug trace file
    gem5Cmd += " --debug-file=debug.trace"
    # specify debug-start & debug-end if necessary
    if util.check_key(configDict, "debug-start"):
        gem5Cmd += f" --debug-start={configDict['debug-start'][0]}"
    if util.check_key(configDict, "debug-end"):
        gem5Cmd += f" --debug-end={configDict['debug-end'][0]}"
    # specify gem5 output directory
    gem5Cmd += f" -d {output_dir}"
    # specify gem5 python configuration file
    gem5Cmd += f" {configDict['gem5_config'][0]}"
    # construct python config general cli parameters
    for parameter in configDict:
        if (
            (parameter in configDict["python-config-exclusive-pars"])
            or (
                ("d2d-link-config-list" in configDict.keys())
                and (configDict["d2d-link-config-list"] is not None)
                and (parameter in configDict["d2d-link-config-list"])
            )
            or (configDict[parameter] is None)
            or (len(configDict[parameter]) == 0)
        ):
            continue
        gem5Cmd += f" --{parameter}={configDict[parameter][0]}"
    # construct python config d2d-link-latency parameters
    if ("d2d-link-config-list" in configDict.keys()) and (
        configDict["d2d-link-config-list"] is not None
    ):
        gem5Cmd += f" --d2d-link-latency="
        numD2DLinkConfig = len(configDict["d2d-link-config-list"])
        for i in range(numD2DLinkConfig):
            gem5Cmd += f"{configDict['d2d-link-config-list'][i]}={configDict[configDict['d2d-link-config-list'][i]][0]}"
            if i != numD2DLinkConfig - 1:
                gem5Cmd += ","
    
    # construct fs-mode flags
    fsMode = util.check_and_fetch_key(configDict, "fs_mode")
    if fsMode is not None:
        # full-system emulation mode
        if fsMode == "checkpoint":
            # for checkpoint mode, specifying `checkpoint-dir` is optional
            # create checkpoint
            if not util.check_key(configDict, "checkpoint-dir"):
                # use default directory to create and store the checkpoint
                gem5Cmd += f" --checkpoint-dir={output_dir}"
            else:
                # clean and create the checkpoint directory if necessary
                util.clean_dir(configDict["checkpoint-dir"][0])
                gem5Cmd += f" --checkpoint-dir={configDict['checkpoint-dir'][0]}"
        elif fsMode == "restore":
            # for restore mode, `checkpoint-dir` must be provided
            if not util.check_key(configDict, "checkpoint-dir"):
                raise ValueError("checkpoint-dir must be provided under FS restore mode")
            else:
                gem5Cmd += f" --checkpoint-dir={configDict['checkpoint-dir'][0]}"
        else:
            raise NotImplementedError
        # automatically pass the dtb file path if necessary
        if util.check_and_fetch_key(configDict, "dtb-filename") is None:
            dtbFileName = f"{configDict['machine-type'][0]}_{configDict['num-cpus'][0]}cpu_{configDict['num-dies'][0]}die.dtb"
            dtbFilePath = f"{os.path.join(util.get_script_root(), 'dtb', dtbFileName)}"
            print(f"Using automatically generated dtb file ==> {dtbFilePath}")
            gem5Cmd += f" --dtb-filename={dtbFilePath}"
            
    
    # construct extra flags
    if configDict["extra_flags"] is not None:
        for extraFlag in configDict["extra_flags"]:
            gem5Cmd += f" --{extraFlag}"

    # configure redirection
    gem5Cmd += f" > {output_dir}/cmd.log 2>&1"

    # dump python config cli parameters to file
    util.dump_str_file(os.path.join(output_dir, "issued_cmd.log"), gem5Cmd)

    # execute test and get the result
    startTime = time.time()
    # stdOut, stdErr, retCode = util.exec_shell_cmd(gem5Cmd)
    stdOut, stdErr, retCode = util.exec_shell_cmd(gem5Cmd, False, False, True, True)
    endTime = time.time()
    duration = int(endTime - startTime)

    return {"retCode": retCode, "errMsg": stdErr, "outputDir": output_dir, "time": duration}


def worker_manager(args, configDict):
    # detach mode, use double-fork trick
    if not args.no_detach:
        if os.fork() != 0:
            return

    # explore parameter space
    exclusiveList: list = configDict["python-config-exclusive-pars"]
    parameterSpaceList = []
    configList = []
    for key in configDict:
        # in exclusive list, ignore
        if key in exclusiveList:
            continue
        # only one parameter, no need to explore
        if (configDict[key] is None) or len(configDict[key]) < 2:
            continue
        # add to parameter explore space
        parameterSpaceList.append(key)

    # dynamically generate code for exploring various parameter combinations
    _code = ""
    dimParameterSpace = len(parameterSpaceList)
    _0_configDict = configDict
    for i in range(dimParameterSpace):
        parameterName: str = parameterSpaceList[i]
        variableName = parameterName.replace("-", "_")
        # generate loop wrapper code
        _code += (
            f"{i * _tab}for {variableName} in _{i}_configDict['{parameterName}']:\n"
        )
        # generate parameters assignment code
        _code += f"{(i+1) * _tab}_{i+1}_configDict=deepcopy(_{i}_configDict); _{i+1}_configDict['{parameterName}']=[{variableName}]\n"

    # add all generated configs to the list
    _code += f"{dimParameterSpace * _tab}configList.append((args, _{dimParameterSpace}_configDict, parameterSpaceList))\n"

    # execute the generated code
    exec(_code)

    # hint users about tests to be runned
    if dimParameterSpace > 0:
        numConfig = len(configList)
        for i in range(numConfig):
            print(f"Running [{i+1}/{numConfig}] {args.output_dir}/", end="")
            for parameter in parameterSpaceList:
                print(
                    f"{parameter}_{str(configList[i][1][parameter][0]).replace(',','.')}/",
                    end="",
                )
            print("")
    else:
        print(f"Running 1 task under {args.output_dir}/")

    # create process(worker) pool
    processPool = Pool(configDict["WORKERS"])

    # run tests and hint users
    resultObj = processPool.map_async(worker_process, configList)
    if args.no_detach:
        print("Waiting for all tests to finish...")
    else:
        print("Running all tests in the background(detached mode)")

    # gather the result
    taskResults = resultObj.get()

    print("All tasks completed!")
    # dump the run summary
    util.dump_run_summary(os.path.join(args.output_dir, "run_summary.csv"), taskResults)

    # clean and exit
    processPool.close()
    processPool.join()
    return


if __name__ == "__main__":
    # get repo root directory
    rootRepo = util.get_repo_root()
    if rootRepo is None:
        raise Exception("Failed to detect root directory of the repo!")

    parser = argparse.ArgumentParser(
        prog="StarFive Tester(MemTest)", description="StarFive Tester(MemTest)"
    )

    # configure argparser
    parser.add_argument(
        "--config-file", type=str, required=True, help=f"Specify YAML config file"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=f"{datetime.now().strftime('%Y-%m-%d-%H:%M:%S')}_output",
        help=f"Specify the directory of output files/folders",
    )
    parser.add_argument(
        "--no-detach",
        action="store_true",
        default=False,
        help=f"whether to run tests in background(detached mode), default True",
    )
    parser.add_argument(
        "--checkpoint-dir",
        type=str,
        default="",
        help=f"specify checkpoint directory for FS mode"
    )
    parser.add_argument(
        "action",
        type=str,
        default=None,
        help=f"actions: build | run | gen-config | kill-all",
    )

    # parse cli arguments
    args = parser.parse_args()
    args.root_repo = rootRepo
    args.output_dir = os.path.join(rootRepo, args.output_dir)
    # load configs
    configDict = util.recursive_load_yaml(args.config_file)
    # deal with special arguments
    if args.checkpoint_dir is not None and len(args.checkpoint_dir) > 0:
        configDict["checkpoint-dir"] = [os.path.join(rootRepo, args.checkpoint_dir)]
    # hint users about the working directory
    print(f"<<<<<< Use {configDict['WORKERS']} Processes >>>>>>")
    print(f"Repo Root Directory: {rootRepo}; Output Directory: {args.output_dir}")

    # check actions
    # build gem5
    if args.action == "build":
        # create output directory
        util.create_dir(args.output_dir)
        # dump configs to folder
        util.dump_config(os.path.join(args.output_dir, "cmd_config.yaml"), configDict)
        # automatically generate required dtb files
        # compile the dts
        starfive_fs_utility.compile_dts()
        # decompile for debugging
        starfive_fs_utility.decompile_dtb()
        # construct extra build env variables
        buildEnvs = ""
        for i in range(len(configDict["BUILDENV"])):
            buildEnvs += f" {configDict['BUILDENV'][i]}"
        # build gem5
        _, _, retCode = util.exec_shell_cmd(
            f"pushd {args.root_repo} && scons {buildEnvs} build/{configDict['ISA']}_{configDict['CCPROT']}/{configDict['BUILDTYPE']} --default={configDict['ISA']} PROTOCOL={configDict['CCPROT']} {buildEnvs} -j {configDict['WORKERS']} && popd",
            directStdout=True,
            directStderr=True,
        )
        if retCode != 0:
            print("Failed to build gem5!")
            exit(1)
    # run tests
    elif args.action == "run":
        # create output directory
        util.create_dir(args.output_dir)
        # dump configs to folder
        util.dump_config(os.path.join(args.output_dir, "cmd_config.yaml"), configDict)

        # start the worker manager to run tests
        subP = Process(target=worker_manager, args=(args, configDict))
        subP.start()
        subP.join()
    # generate configs only
    elif args.action == "gen-config":
        # create output directory
        util.create_dir(args.output_dir)
        # dump configs to folder
        util.dump_config(os.path.join(args.output_dir, "cmd_config.yaml"), configDict)
    # terminate all unfinished tasks running in background
    elif args.action == "kill-all":
        _, _, retCode = util.exec_shell_cmd(
            "kill -9 $(pgrep -u $USER 'gem5\.(opt)|(debug)|(fast)')",
            directStdout=True,
            directStderr=True,
        )
        if retCode != 0:
            print("Failed to terminate unfinished tasks!")
            exit(1)

    exit(0)
