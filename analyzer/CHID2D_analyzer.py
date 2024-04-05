import os
import logging
import statistics
import pandas as pd

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
    noGen   = check_and_fetch_key(runtimeConfig, "no-gen-die", 0)
    numCpus = check_and_fetch_key(runtimeConfig, "num-cpus", 0)
    numDies = check_and_fetch_key(runtimeConfig, "num-dies", 0)
    numGenCpus = numCpus
    if noGen is not None:
        numCpuPerDie = int(numCpus / numDies)
        noGenDieList = list(map(lambda noGen: int(noGen), noGen.split(",")))
        numNoGenDie = len(noGenDieList)
        numGenCpus -= numNoGenDie * numCpuPerDie
    return numGenCpus

def getNumCpus(runtimeConfig: dict) -> int :
    numCpus = check_and_fetch_key(runtimeConfig, "num-cpus", 0)
    if (numCpus is not None)  :
        return int(numCpus)
    else :
        return -1
    
def analyze_access_bandwidth(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict:
    totalNumReads = check_and_fetch_key(extractedPars, "totalNumReads", 0)
    totalNumWrites = check_and_fetch_key(extractedPars, "totalNumWrites", 0)
    simTicks = check_and_fetch_key(extractedPars, "simTicks", 0)
    simFreq = check_and_fetch_key(extractedPars, "simFreq", 0)
    ticksPerCycle = check_and_fetch_key(extractedPars, "ticksPerCycle", 0)
    maxOutstand = check_and_fetch_key(runtimeConfig, "outstanding-req", 0)

    # if (maxOutstand is None) or (maxOutstand == 1):
    #     # return {}

    numGenCpus = getNumGenCpus(runtimeConfig)

    totalReadBandwidth = None
    totalWriteBandwidth = None
    normReadBandwidth = None
    normWriteBandwidth = None
    if (
        ((numGenCpus is not None) and (numGenCpus > 0))
        and ((totalNumReads is not None) and (totalNumReads >= 0))
        and ((totalNumWrites is not None) and (totalNumWrites >= 0))
        and ((simFreq is not None) and (simFreq > 0))
        and ((ticksPerCycle is not None) and (ticksPerCycle > 0))
    ):
        totalReadBandwidth = (
            float(totalNumReads)
            * 64
            / (float(simTicks) / float(simFreq) * 1000 * 1000 * 1000)
        )
        normReadBandwidth = totalReadBandwidth / numGenCpus
        
        totalWriteBandwidth = (
            float(totalNumWrites)
            * 64
            / (float(simTicks) / float(simFreq) * 1000 * 1000 * 1000)
        )
        normWriteBandwidth = totalWriteBandwidth / numGenCpus

    return {
        "totalReadBandWidth": totalReadBandwidth,
        "totalWriteBandwidth": totalWriteBandwidth,
        "normReadBandwidth": normReadBandwidth,
        "normWriteBandwidth": normWriteBandwidth,
        "numGenCpus": numGenCpus
    }

# for back-ward compatible
def analyze_read_bandwidth(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict:
    return analyze_access_bandwidth(runtimeConfig, extractedPars, targetDir)
    

def analyze_copyback_traffic(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict:
    incomingReqHATraffic      = check_and_fetch_key(extractedPars,"incomingReqHATraffic",0)
    incomingCopyBackHATraffic = check_and_fetch_key(extractedPars,"incomingCopyBackHATraffic",0)
    if incomingReqHATraffic is not None :
        incomingReqHATraffic = int(incomingReqHATraffic)
    else :
        incomingReqHATraffic = -10000
    if incomingCopyBackHATraffic is not None :
        incomingCopyBackHATraffic = int(incomingCopyBackHATraffic)
    else :
        incomingCopyBackHATraffic = 0
    return {
        "incomingReqHATraffic": incomingReqHATraffic,
        "incomingCopyBackHATraffic": incomingCopyBackHATraffic,
        "percentCopyBackTraffic": (incomingCopyBackHATraffic*100)/(incomingReqHATraffic+incomingCopyBackHATraffic)
    }

def analyze_mshr_util(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict :
    numDirs    = check_and_fetch_key(runtimeConfig, "num-dirs", 0)
    numGenCpus = getNumGenCpus(runtimeConfig)
    snfTbeUtil = check_and_fetch_key(extractedPars,"snfTbeUtil",0)
    snfTbeUtilAvg = -1000000.0
    haTbeUtilAvg  = -1000000.0
    rnfTbeUtilAvg = -1000000.0
    l1dTbeUtilAvg = -1000000.0
    if snfTbeUtil is not None :
        snfTbeUtil = float(snfTbeUtil)
        snfTbeUtilAvg = snfTbeUtil/numDirs
    haTbeUtil = check_and_fetch_key(extractedPars,"haTbeUtil",0)
    if haTbeUtil is not None :
        haTbeUtil = float(haTbeUtil)
        haTbeUtilAvg = haTbeUtil/numDirs
    rnfTbeUtil = check_and_fetch_key(extractedPars,"rnfTbeUtil",0)
    if rnfTbeUtil is not None :
        rnfTbeUtil = float(rnfTbeUtil)
        rnfTbeUtilAvg = rnfTbeUtil/numGenCpus
    l1dTbeUtil = check_and_fetch_key(extractedPars,"l1dTbeUtil",0)
    if l1dTbeUtil is not None :
        l1dTbeUtil = float(l1dTbeUtil)
        l1dTbeUtilAvg = l1dTbeUtil/numGenCpus
    l2RetryAcks = check_and_fetch_key(extractedPars,"l2RetryAcks",0)
    l2RetryAcksAvg = -1000000.0
    if l2RetryAcks is not None :
        l2RetryAcks = float(l2RetryAcks)
        l2RetryAcksAvg = l2RetryAcks/numGenCpus
    l1dhits = check_and_fetch_key(extractedPars,"l1dhit",0)
    l1dacc = check_and_fetch_key(extractedPars,"l1dacc",0)
    l1dHitRate = 0
    if l1dacc > 0 :
        l1dHitRate = float(l1dhits/l1dacc)
    l2hits = check_and_fetch_key(extractedPars,"l2hit",0)
    l2acc = check_and_fetch_key(extractedPars,"l2acc",0)
    l2HitRate = 0
    if l2acc > 0 :
        l2HitRate = float(l2hits/l2acc)
    l3hits = check_and_fetch_key(extractedPars,"hnfHit",0)
    l3acc = check_and_fetch_key(extractedPars,"hnfacc",0)
    l3HitRate = 0
    if l3acc is not None :
        if l3acc > 0 :
            l3HitRate = float(l3hits/l3acc)
    return {
        "L1D_Occupancy": l1dTbeUtilAvg,
        "L2RetryAcks": l2RetryAcksAvg,
        "RNF_Occupancy": rnfTbeUtilAvg,
        "HA_Occupancy": haTbeUtilAvg,
        "SNF_Occupancy": snfTbeUtilAvg,
        "L1D_HitRate": l1dHitRate,
        "L2_HitRate": l2HitRate,
        "L3_HitRate": l3HitRate
    }
    
def analyze_cpu_ipc(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict:
    totalCPUCycles = check_and_fetch_key(extractedPars, "totalCPUCycles", 0)
    totalCPUInsts = check_and_fetch_key(extractedPars, "totalCPUInsts", 0)
    
    if totalCPUCycles is not None and totalCPUInsts is not None:
        return {"aveCPUIPC": totalCPUInsts / totalCPUCycles}
    else:
        return {}

def getHASnoopFilterMissRate(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict:
    pass

def analyze_access_latency(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict:
    totalNumReads = check_and_fetch_key(extractedPars, "totalNumReads", 0)
    totalNumWrites = check_and_fetch_key(extractedPars, "totalNumWrites", 0)
    totalLatency = check_and_fetch_key(extractedPars, "totalLatency", 0)
    simTicks = check_and_fetch_key(extractedPars, "simTicks", 0)
    ticksPerCycle = check_and_fetch_key(extractedPars, "ticksPerCycle", 0)
    maxOutstand = check_and_fetch_key(runtimeConfig, "outstanding-req", 0)

    # if (maxOutstand is None) or (maxOutstand != 1):
        # return {}

    numGenCpus = getNumGenCpus(runtimeConfig)

    normReadLatency = None
    normWriteLatency = None

    if (
        ((numGenCpus is not None) and (numGenCpus > 0))
        and ((totalNumReads is not None) and (totalNumReads >= 0))
        and ((totalNumWrites is not None) and (totalNumWrites >= 0))
        and ((simTicks is not None) and (simTicks > 0))
        and ((ticksPerCycle is not None) and (ticksPerCycle > 0))
        and ((totalLatency is not None) and (totalLatency > 0))
    ):
        if totalNumReads != 0:
            normReadLatency = int(
                float(totalLatency) / float(totalNumReads * ticksPerCycle / numGenCpus)
            )
        if totalNumWrites != 0:
            normWriteLatency = int(
                float(totalLatency) / float(totalNumWrites * ticksPerCycle / numGenCpus)
            )

    return {"readLatency": normReadLatency, "writeLatency": normWriteLatency, "numGenCpus": numGenCpus}

# for back-ward compatible
def analyze_read_latency(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict:
    return analyze_access_latency(runtimeConfig, extractedPars, targetDir)
    

def dump_parameters(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict:
    numDies = check_and_fetch_key(runtimeConfig, "num-dies", 0)
    numDirs = check_and_fetch_key(runtimeConfig, "num-dirs", 0)
    sizeWs = check_and_fetch_key(runtimeConfig, "size-ws", 0)
    numL3Caches = check_and_fetch_key(runtimeConfig, "num-l3caches", 0)
    fsScript = check_and_fetch_key(runtimeConfig, "script", 0)
    simSeconds = check_and_fetch_key(extractedPars, "simSeconds", 0)
    hostSeconds = check_and_fetch_key(extractedPars, "hostSeconds", 0)
    hostHours = hostSeconds / 3600.0 if hostSeconds is not None else None
    hostMemory = check_and_fetch_key(extractedPars, "hostMemory", 0)
    aveLoadLatency = check_and_fetch_key(extractedPars, "aveLoadLatency", 0)
    aveStoreLatency = check_and_fetch_key(extractedPars, "aveStoreLatency", 0)
    
    
    if hostMemory is not None:
        hostMemory = "%.2lf" %(float(hostMemory) / 1024 / 1024) + "GiB"
    allowInfiniteSFEntriesHA = check_and_fetch_key(
        runtimeConfig, "allow-ha-infinite-SF-entries", 0
    )
    allowInfiniteSFEntriesHNF = check_and_fetch_key(
        runtimeConfig, "allow-hnf-infinite-SF-entries", 0
    )
    genEvictOnReplHnfCode = check_and_fetch_key(runtimeConfig,'gen_evict_on_repl_hnf',0)
    genEvictOnReplHnf = 'Evict' if genEvictOnReplHnfCode else 'WriteEvictFull'
    noGen = check_and_fetch_key(runtimeConfig, "no-gen-die", 0)
    transmit_retryack = check_and_fetch_key(runtimeConfig, "transmit-retryack", 0)
    ddr_side_code = check_and_fetch_key(runtimeConfig,"DDR-side-num", 0)
    accPatternCode = check_and_fetch_key(runtimeConfig,"addr-intrlvd-or-tiled",0)
    accPattern = 'Interleaved' if accPatternCode else 'Tiled'
    sfHAEntries = "Ideal" if allowInfiniteSFEntriesHA else "Realistic"
    sfHNFEntries = "Ideal" if allowInfiniteSFEntriesHNF else "Realistic"
    TransmitRetryD2D = "Transmit" if transmit_retryack else "Absorb"
    numNormDirs = int(numDirs / numDies)
    numNormL3caches = int(numL3Caches / numDies)
    workset = None if sizeWs is None else str(float(sizeWs / 1024)) + "KiB"
    num_DDR = check_and_fetch_key(runtimeConfig, "DDR-loc-num", 0)
    num_DDR_side = "Unknown"
    if (num_DDR == 2) :
        num_DDR_side = "13"
    elif (num_DDR == 4) :
        if (ddr_side_code <= 1) :
            num_DDR_side = '_'.join(['13','14'])
        elif (ddr_side_code >= 2) :
            num_DDR_side = '_'.join(['13','2'])
    elif (num_DDR == 8) :
        if (ddr_side_code <= 1) :
            num_DDR_side = '_'.join(['12','13','14','15'])
        elif (ddr_side_code == 2) :
            num_DDR_side = '_'.join(['13','14','1','2'])
        elif (ddr_side_code <= 4) :
            num_DDR_side = '_'.join(['13','11','2','4'])

    accessRegion = ""
    if noGen :
        firstNoGen = int(noGen.split(",")[0])
        if firstNoGen % 2 == 1:
            accessRegion = "Intra-Die"
        else:
            accessRegion = "Cross-Die"

    analyzedDict = {
        "AccPattern": accPattern,
        "numNormDirs": numNormDirs,
        "numNormL3caches": numNormL3caches,
        "workset": workset,
        "TransmitRetryD2D": TransmitRetryD2D,
        "accessRegion": accessRegion,
        "num_DDR": num_DDR,
        "num_DDR_side": num_DDR_side,
        "hostSeconds": hostSeconds,
        "hostMemory": hostMemory,
        "HASnoopFilter": sfHAEntries,
        "HNFSnoopFilter": sfHNFEntries,
        "genEvictOnReplHnf": genEvictOnReplHnf,
        "simSeconds": simSeconds,
        "hostHours": hostHours,
        "aveLoadLatency": aveLoadLatency,
        "aveStoreLatency": aveStoreLatency
    }
    if fsScript is not None:
        analyzedDict["fsScript"] = os.path.splitext(os.path.basename(fsScript))[0]
        
    return analyzedDict

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
        reqIter: int = reqMsg[3]
        reqEvent: str = reqMsg[4]
        
        if reqCpu not in reqMsgList:
            reqMsgList[reqCpu] = {}
            reqAddrList[reqCpu] = []
        
        if (reqAddr,reqIter) not in reqMsgList[reqCpu]:
            reqMsgList[reqCpu][(reqAddr,reqIter)] = {"cpu": reqCpu}
            
        reqMsgList[reqCpu][(reqAddr,reqIter)][reqEvent] = reqTick
    
    for reqCpu in reqMsgList:
        for (reqAddr,reqIter) in reqMsgList[reqCpu]:
            reqMsgList[reqCpu][(reqAddr,reqIter)]["Duration"] = reqMsgList[reqCpu][(reqAddr,reqIter)]["Complete"] - reqMsgList[reqCpu][(reqAddr,reqIter)]["Start"]
            reqAddrList[reqCpu].append((reqAddr,reqIter))
    
    latRecords = []
    for reqCpu in reqMsgList:
        for i in range(len(reqAddrList[reqCpu])):
            reqAddr,reqIter = reqAddrList[reqCpu][i]
            reqLatency = reqMsgList[reqCpu][(reqAddr,reqIter)]["Duration"]
            reqBegin = reqMsgList[reqCpu][(reqAddr,reqIter)]["Start"]
            reqEnd = reqMsgList[reqCpu][(reqAddr,reqIter)]["Complete"]
            # analyzeFile.write(f"{reqAddr}, {reqIter}, {reqLatency}, {reqBegin}, {reqEnd}\n")
            latRecords.append({
                'CPU': reqCpu,
                'Addr': reqAddr,
                'Iter': reqIter,
                'Start': reqBegin,
                'End': reqEnd,
                'Latency': reqLatency
            })

    dfX = pd.DataFrame.from_records(latRecords)
    dfX.sort_values(by='Start',ascending=True,inplace=True)
    analyzeFile = os.path.join(targetDir, f"request_latency_cpu{reqCpu}.csv")
    dfX.to_csv(analyzeFile, index=False)
    return {}


def analyze_trace_txn_breakdown_latency(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> str:
    brokenDownLatency = check_and_fetch_key(extractedPars, "BrokenDownLatency")
    reqInfoDict = {}
    reqBreakdown = {}
    for latencyInfo in brokenDownLatency:
        txnId = latencyInfo[0]
        addr = latencyInfo[1]
        cycle = int(latencyInfo[2])
        agent = latencyInfo[3]
        opCode = latencyInfo[4]
        if txnId not in reqInfoDict:
            reqInfoDict[txnId] = []
        
        # construct requestInfo and append it to the list for further analysis
        reqInfoDict[txnId].append({
            "addr": addr,
            "intAddr": int(addr, 16),
            "intTxnId": int(txnId, 16),
            "cycle": cycle,
            "agent": agent,
            "opCode": opCode
        })
        
    breakdownLatencyFile = open(os.path.join(targetDir, "breakdownLatency.csv"), "w")
    
    titleMade = False
    for txnId in reqInfoDict:
        reqInfo = reqInfoDict[txnId]
        # sort traces of one transaction by dequeue cycle
        reqInfoDict[txnId] = sorted(reqInfoDict[txnId], key = lambda trace: trace["cycle"])
        # ignore eviction event
        if int(txnId, 16) == 0:
            continue
        
        reqBreakdown[txnId] = []
        
        agentTrace = []
        cycleTrace = []
        opCodeTrace = []
        
        for trace in reqInfoDict[txnId]:
            agent: str = trace["agent"]
            cycle: int = trace["cycle"]
            opCode: str = trace["opCode"]
            # intermediate network transmission, ignore
            if agent.find("Die") != -1:
                continue
            # same agent or Ack message, ignore
            if (opCode == "CompAck" or (len(agentTrace) >= 1 and agentTrace[-1].find(agent) != -1)) and (opCode != "MEMORY_READ"):
                continue
            
            # not the initial one
            if len(cycleTrace) > 0:
                # Retry Detected
                if len(agentTrace) >= 2 and agentTrace[-2].find(agent) != -1 and opCodeTrace[-2] == opCode:
                    agentTrace.pop()
                    opCodeTrace.pop()
                    cycleTrace.pop()
                    agentTrace[-1] += "(Retry)"
                    continue
            
            agentTrace.append(agent)
            cycleTrace.append(cycle)
            opCodeTrace.append(opCode)
        
        # generate table title
        if not titleMade:
            breakdownLatencyFile.write("TxnId, Addr, ")
            for i in range(len(agentTrace) - 1):
                breakdownLatencyFile.write(f"Agent{i}, Issue{i}, Duration{i}, Receive{i}, ")
                if (i == len(agentTrace) - 2):
                    breakdownLatencyFile.write(f"Agent{i+1}")
            breakdownLatencyFile.write("\n")
        titleMade = True
        
        # fill table with data
        breakdownLatencyFile.write(f"{txnId}, {reqInfo[0]['addr']}, ")
        for i in range(len(agentTrace) - 1):
            breakdownLatencyFile.write(f"{agentTrace[i]}[{opCodeTrace[i]}], {cycleTrace[i]}, {cycleTrace[i+1] - cycleTrace[i]}, {cycleTrace[i+1]}, ")
        breakdownLatencyFile.write(f"{agentTrace[-1]}[{opCodeTrace[-1]}]\n")
        
    breakdownLatencyFile.close()

    return {}