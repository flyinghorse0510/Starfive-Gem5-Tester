import time, sys, os
import argparse, yaml
from multiprocessing import Process, Queue, Pool
from copy import deepcopy
import re, io
import os
import ast
import copy
import json
import logging
import argparse
import numpy as np
import sys
import logging
import util
from pydantic.v1.utils import deep_update


def extract_pars(target: str, targetDir: str, analyzeConfig: dict):
    targetFilePath = os.path.join(targetDir, target)
    regExp = {}
    for key in analyzeConfig:
        regExp[key] = re.compile(analyzeConfig[key]["pattern"])

    extractedPars = {}

    targetFile = open(targetFilePath, "r")
    for line in targetFile:
        for key in regExp:
            if key not in extractedPars:
                extractedPars[key] = []

            match = regExp[key].search(line)
            if not match:
                continue
            if len(analyzeConfig[key]["location"]) > 1:
                parList = []
                for i in range(len(analyzeConfig[key]["location"])):
                    location = analyzeConfig[key]["location"][i]
                    _par = match.group(location)
                    parList.append(eval(f"{analyzeConfig[key]['type'][i]}(_par)"))
                extractedPars[key].append(parList)
            else:
                location = analyzeConfig[key]["location"][0]
                _par = match.group(location)
                if "reduce" in analyzeConfig[key]:
                    if len(extractedPars[key]) == 0:
                        if analyzeConfig[key]["reduce"] == "x=":
                            extractedPars[key].append(1)
                        else:
                            extractedPars[key].append(0)

                    exec(
                        f"extractedPars[key][0] {analyzeConfig[key]['reduce']} {analyzeConfig[key]['type'][0]}(_par)"
                    )
                else:
                    extractedPars[key].append(
                        eval(f"{analyzeConfig[key]['type'][0]}(_par)")
                    )
                    
    targetFile.close()

    return extractedPars


def match_process(config: dict):
    # get parameters
    targetDir = config["targetDir"]
    analyzeConfig = config["analyzeConfig"]
    target = config["target"]
    taskIdx = config["taskIdx"]

    targetPath = os.path.join(targetDir, target)
    # hint users about the progress
    # print(f"[{taskIdx}] Searching Pattern in {targetPath}")
    # execute the regular expression match work
    extractedPars = extract_pars(target, targetDir, analyzeConfig)

    return {"targetDir": targetDir, "extractedPars": extractedPars}


def analyze_process(config: dict):
    # get parameters
    targetDir = config["targetDir"]
    taskIdx = config["taskIdx"]
    runtimeConfig = config["runtimeConfig"]
    extractedPars = config["extractedPars"]
    analyzeFunc = config["analyzeFunc"]

    # hint users about the progress
    # print(f"[{taskIdx}] Analyzing in {targetDir}")
    # execute the analyze function
    extractedPars = analyzeFunc(runtimeConfig, extractedPars, targetDir)

    return {"targetDir": targetDir, "extractedPars": extractedPars}


def dump_summary(config: dict):
    summaryDict = config["summaryDict"]
    extractedDict = config["extractedDict"]
    targetRoot = config["targetRoot"]
    summary = config["summary"]

    summaryFilePath = os.path.join(targetRoot, summary) + ".csv"
    summaryFile = open(summaryFilePath, "w")
    for dataField in summaryDict:
        summaryFile.write(f"{dataField['head']},")
    summaryFile.write("\n")

    for targetDir in extractedDict:
        runtimConfig = extractedDict[targetDir]["runtimeConfig"]
        extractedPars = extractedDict[targetDir]["extractedPars"]
        for dataField in summaryDict:
            if dataField["data"] in extractedPars:
                if extractedPars[dataField["data"]] is None:
                    summaryFile.write("ERROR,")
                else:
                    summaryFile.write(f"{extractedPars[dataField['data']]},")
            elif dataField["data"] in runtimConfig:
                if runtimConfig[dataField["data"]] is None:
                    summaryFile.write("ERROR,")
                else:
                    if type(runtimConfig[dataField["data"]]) == list:
                        summaryFile.write(f"{runtimConfig[dataField['data']][0]},")
                    else:
                        summaryFile.write(f"{runtimConfig[dataField['data']]},")
            else:
                summaryFile.write("NA,")

        summaryFile.write("\n")

    summaryFile.close()


def worker_manager(args, analyzeConfigDict: dict, targetDirList: list):
    # create process(worker) pool
    processPool = Pool(analyzeConfigDict["WORKERS"])
    # create and construct match task list
    matchTaskList = []
    matchResultObj = None
    if util.check_key(analyzeConfigDict, "target"):
        allTargets = util.check_and_fetch_key(analyzeConfigDict, "target")
        taskIdx = 1
        for targetDir in targetDirList:
            for target in allTargets:
                # append match task
                matchTaskList.append(
                    {
                        "targetDir": targetDir,
                        "analyzeConfig": util.check_and_fetch_key(
                            analyzeConfigDict, "target", target
                        ),
                        "target": target,
                        "taskIdx": taskIdx,
                    }
                )
                taskIdx += 1
        # run match tasks(async) and hint users
        print(f"Running match task...({taskIdx-1} sub-tasks in total)")
        matchResultObj = processPool.map_async(match_process, matchTaskList)
    else:
        # no match task to perform
        logging.warn("No target to extract(search pattern)")

    # construct the list of extracted(matched) results
    extractedDict = dict(
        [
            (
                targetDir,
                {
                    "runtimeConfig": util.recursive_load_yaml(
                        os.path.join(targetDir, "cmd_config.yaml")
                    ),
                    "extractedPars": {},
                },
            )
            for targetDir in targetDirList
        ]
    )

    # get matched results and update the dict
    if matchResultObj is not None:
        matchResultList = matchResultObj.get()
        for matchResult in matchResultList:
            extractedDict[matchResult["targetDir"]]["extractedPars"] = deep_update(
                extractedDict[matchResult["targetDir"]]["extractedPars"],
                matchResult["extractedPars"],
            )

    # create and construct analyze task list
    analyzeTaskList = []
    analyzeResultObj = None
    if util.check_key(analyzeConfigDict, "callback"):
        taskIdx = 1
        for callback in analyzeConfigDict["callback"]:
            callbackFuncList = analyzeConfigDict["callback"][callback]["func"]
            callbackPath = analyzeConfigDict["callback"][callback]["file"]
            callbackDir = os.path.dirname(callbackPath)
            callbackFile = os.path.basename(callbackPath)
            # generate code for execute
            _code = ""
            # import required callback file
            _code += f"from {callbackDir} import {callbackFile}\n"
            exec(_code)

            for targetDir in targetDirList:
                for callbackFunc in callbackFuncList:
                    analyzeFunc = eval(f"{callbackFile}.{callbackFunc}")
                    # append analyze task
                    analyzeTaskList.append(
                        {
                            "targetDir": targetDir,
                            "runtimeConfig": extractedDict[targetDir]["runtimeConfig"],
                            "extractedPars": extractedDict[targetDir]["extractedPars"],
                            "analyzeFunc": analyzeFunc,
                            "taskIdx": taskIdx,
                        }
                    )
                    taskIdx += 1
        # run analyze tasks(async) and hint users
        print(f"Running analyze task...({taskIdx-1} sub-tasks in total)")
        analyzeResultObj = processPool.map_async(analyze_process, analyzeTaskList)
    else:
        logging.warn("No callback for analysis")

    # get analyzed results and update the dict
    if analyzeResultObj is not None:
        analyzeResultList = analyzeResultObj.get()
        for analyzeResult in analyzeResultList:
            extractedDict[analyzeResult["targetDir"]]["extractedPars"] = deep_update(
                extractedDict[analyzeResult["targetDir"]]["extractedPars"],
                analyzeResult["extractedPars"],
            )

    # dump summary files
    if util.check_key(analyzeConfigDict, "summary"):
        allSummaries = util.check_and_fetch_key(analyzeConfigDict, "summary")
        for summary in allSummaries:
            dump_summary(
                {
                    "summaryDict": allSummaries[summary],
                    "extractedDict": extractedDict,
                    "targetRoot": args.target_root,
                    "summary": summary,
                }
            )

    # dump analyze config
    util.dump_config(
        os.path.join(args.target_root, "analyze_config.yaml"), analyzeConfigDict
    )


if __name__ == "__main__":
    # get repo root directory
    rootRepo = util.get_repo_root()
    if rootRepo is None:
        raise Exception("Failed to detect root directory of the repo!")

    parser = argparse.ArgumentParser(
        prog="StarFive Analyzer(MemTest)", description="StarFive Analyzer(MemTest)"
    )

    # configure argparser
    parser.add_argument(
        "--analyze-file", type=str, required=True, help=f"Specify YAML config file"
    )
    parser.add_argument(
        "--target-root",
        type=str,
        required=True,
        help=f"Specify the directory of target files/folders",
    )

    # parse cli arguments
    args = parser.parse_args()
    args.root_repo = rootRepo
    args.target_root = os.path.join(rootRepo, args.target_root)
    # load configs
    analyzeConfigDict = util.recursive_load_yaml(args.analyze_file)
    # search for all target files in the folder and its subfolders
    targetDirList = util.get_all_target_dir(args.target_root, "stats.txt")

    # start the worker manager to run various tasks
    subP = Process(target=worker_manager, args=(args, analyzeConfigDict, targetDirList))
    subP.start()
    subP.join()

    exit(0)
