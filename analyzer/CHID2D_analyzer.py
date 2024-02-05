import os
import logging
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
def check_and_fetch_key(parsDict: dict, key: str, index: int or str = None):
    if check_key(parsDict, key):
        if index is not None:
            return parsDict[key][index]
        else:
            return parsDict[key]
    return None


def analyze_read_bandwidth(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict:
    totalNumReads = check_and_fetch_key(extractedPars, "totalNumReads", 0)
    totalNumWrites = check_and_fetch_key(extractedPars, "totalNumWrites", 0)
    simTicks = check_and_fetch_key(extractedPars, "simTicks", 0)
    simFreq = check_and_fetch_key(extractedPars, "simFreq", 0)
    ticksPerCycle = check_and_fetch_key(extractedPars, "ticksPerCycle", 0)
    noGen = check_and_fetch_key(runtimeConfig, "no-gen", 0)
    numCpus = check_and_fetch_key(runtimeConfig, "num-cpus", 0)
    numDies = check_and_fetch_key(runtimeConfig, "num-dies", 0)
    maxOutstand = check_and_fetch_key(runtimeConfig, "outstanding-req", 0)

    if (maxOutstand is None) or (maxOutstand == 1):
        return {}

    numGenCpus = numCpus
    if noGen is not None:
        numCpuPerDie = int(numCpus / numDies)
        noGenDieList = list(map(lambda noGen: int(noGen), noGen.split(",")))
        numNoGenDie = len(noGenDieList)
        numGenCpus -= numNoGenDie * numCpuPerDie

    totalBandwidth = None
    normBandwidth = None
    if (
        ((numGenCpus is not None) and (numGenCpus > 0))
        and ((totalNumReads is not None) and (totalNumReads > 0))
        and ((totalNumWrites is not None) and (totalNumWrites == 0))
        and ((simFreq is not None) and (simFreq > 0))
        and ((ticksPerCycle is not None) and (ticksPerCycle > 0))
    ):
        totalBandwidth = (
            float(totalNumReads)
            * 64
            / (float(simTicks) / float(simFreq) * 1024 * 1024 * 1024)
        )
        normBandwidth = totalBandwidth / numGenCpus

    return {
        "totalReadBandWidth": totalBandwidth,
        "normReadBandwidth": normBandwidth,
        "numGenCpus": numGenCpus,
    }


def analyze_read_latency(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict:
    totalNumReads = check_and_fetch_key(extractedPars, "totalNumReads", 0)
    totalNumWrites = check_and_fetch_key(extractedPars, "totalNumWrites", 0)
    simTicks = check_and_fetch_key(extractedPars, "simTicks", 0)
    ticksPerCycle = check_and_fetch_key(extractedPars, "ticksPerCycle", 0)
    noGen = check_and_fetch_key(runtimeConfig, "no-gen", 0)
    numCpus = check_and_fetch_key(runtimeConfig, "num-cpus", 0)
    numDies = check_and_fetch_key(runtimeConfig, "num-dies", 0)
    maxOutstand = check_and_fetch_key(runtimeConfig, "outstanding-req", 0)

    if (maxOutstand is None) or (maxOutstand != 1):
        return {}

    numGenCpus = numCpus
    if noGen is not None:
        numCpuPerDie = int(numCpus / numDies)
        noGenDieList = list(map(lambda noGen: int(noGen), noGen.split(",")))
        numNoGenDie = len(noGenDieList)
        numGenCpus -= numNoGenDie * numCpuPerDie

    normLatency = None

    if (
        ((numGenCpus is not None) and (numGenCpus > 0))
        and ((totalNumReads is not None) and (totalNumReads > 0))
        and ((totalNumWrites is not None) and (totalNumWrites == 0))
        and ((simTicks is not None) and (simTicks > 0))
        and ((ticksPerCycle is not None) and (ticksPerCycle > 0))
    ):
        normLatency = int(
            float(simTicks) / float(totalNumReads * ticksPerCycle / numGenCpus)
        )

    return {"readLatency": normLatency, "numGenCpus": numGenCpus}


def dump_parameters(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict:
    numDies = check_and_fetch_key(runtimeConfig, "num-dies", 0)
    numDirs = check_and_fetch_key(runtimeConfig, "num-dirs", 0)
    sizeWs = check_and_fetch_key(runtimeConfig, "size-ws", 0)
    numL3Caches = check_and_fetch_key(runtimeConfig, "num-l3caches", 0)
    hostSeconds = check_and_fetch_key(extractedPars, "hostSeconds", 0)
    hostMemory = check_and_fetch_key(extractedPars, "hostMemory", 0)
    if hostMemory is not None:
        hostMemory = "%.2lf" %(float(hostMemory) / 1024 / 1024) + "GiB"
    allowInfiniteSFEntries = check_and_fetch_key(
        runtimeConfig, "allow-infinite-SF-entries", 0
    )
    noGen = check_and_fetch_key(runtimeConfig, "no-gen", 0)
    sfEntries = "Ideal" if allowInfiniteSFEntries else "Realistic"
    numNormDirs = int(numDirs / numDies)
    numNormL3caches = int(numL3Caches / numDies)
    workset = str(int(sizeWs / 1024)) + "KiB"

    firstNoGen = int(noGen.split(",")[0])
    if firstNoGen % 2 == 1:
        accessRegion = "Intra-Die"
    else:
        accessRegion = "Cross-Die"

    return {
        "numNormDirs": numNormDirs,
        "numNormL3caches": numNormL3caches,
        "workset": workset,
        "sfEntries": sfEntries,
        "accessRegion": accessRegion,
        "hostSeconds": hostSeconds,
        "hostMemory": hostMemory
    }

def analyze_trace_request_latency(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict:
    ticksPerCycle = check_and_fetch_key(extractedPars, "ticksPerCycle", 0)
    if ticksPerCycle is None or ticksPerCycle <= 0:
        logging.error("[analyze_trace_request_latency]: ticksPerCycle ERROR!")
        return {}
    
    reqMsgList = {}
    reqAddrList = {}
    
    numReqMsg = len(extractedPars["SFReplMemTest"])
    for i in range(numReqMsg):
        reqMsg = extractedPars["SFReplMemTest"][i]
        
        reqTick: int = int(reqMsg[0] / ticksPerCycle)
        reqCpu: int = reqMsg[1]
        reqAddr: str = reqMsg[2]
        reqEvent: str = reqMsg[3]
        
        if reqCpu not in reqMsgList:
            reqMsgList[reqCpu] = {}
            reqAddrList[reqCpu] = []
        
        if reqAddr not in reqMsgList[reqCpu]:
            reqMsgList[reqCpu][reqAddr] = {"cpu": reqCpu}
            
        reqMsgList[reqCpu][reqAddr][reqEvent] = reqTick
    
    for reqCpu in reqMsgList:
        for reqAddr in reqMsgList[reqCpu]:
            reqMsgList[reqCpu][reqAddr]["Duration"] = reqMsgList[reqCpu][reqAddr]["Complete"] - reqMsgList[reqCpu][reqAddr]["Start"]
            reqAddrList[reqCpu].append(reqAddr)
    
    for reqCpu in reqMsgList:
        reqAddrList[reqCpu] = sorted(reqAddrList[reqCpu])
        analyzeFile = open(os.path.join(targetDir, f"request_latency_cpu{reqCpu}.csv"), "w")
        analyzeFile.write("Address, Latency(Cycles), Begin(Cycle), End(Cycle)\n")
        
        for i in range(len(reqAddrList[reqCpu])):
            reqAddr = reqAddrList[reqCpu][i]
            reqLatency = reqMsgList[reqCpu][reqAddr]["Duration"]
            reqBegin = reqMsgList[reqCpu][reqAddr]["Start"]
            reqEnd = reqMsgList[reqCpu][reqAddr]["Complete"]
            analyzeFile.write(f"{reqAddr}, {reqLatency}, {reqBegin}, {reqEnd}\n")
        
        analyzeFile.close()
    
    return {}