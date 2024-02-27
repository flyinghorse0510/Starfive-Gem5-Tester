import os
import logging
import statistics

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


def analyze_trace_HA_dataIn(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict:
    haDataInTraceList = check_and_fetch_key(extractedPars, "HADataInChannel")
    ticksPerCycle = check_and_fetch_key(extractedPars, "ticksPerCycle", 0)
    HADataInTraceFile = open(os.path.join(targetDir, "HA_DataIn_Trace_Enq.csv"), "w")
    # generate title
    HADataInTraceFile.write("Time, Agent, TxnId, Addr, Data Type, Message Type\n")
    for haDataIn in haDataInTraceList:
        tickTime: int = haDataIn[0]
        cycleTime: int = int(tickTime / ticksPerCycle)
        agent: str = haDataIn[1]
        txnId: str = haDataIn[2]
        addr: str = haDataIn[3]
        dataType: str = haDataIn[5]
        msgType: str = haDataIn[4]
        HADataInTraceFile.write(f"{cycleTime}, {agent}, {txnId}, {addr}, {dataType}, {msgType}\n")
    
    HADataInTraceFile.close()
    return {}
    