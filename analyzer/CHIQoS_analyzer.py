import os
import sys
import util
import logging
import statistics as st
import pprint as pp
import pandas as pd
import analyzer.CHID2D_analyzer as chid2da

def analyze_rest(runtimeConfig: dict, extractedPars: dict, targetDir: str)-> dict :
    ret = dict()
    ret.update(chid2da.dump_parameters(runtimeConfig,extractedPars,targetDir))
    ret.update(chid2da.analyze_mshr_util(runtimeConfig,extractedPars,targetDir))
    return ret

def analyze_perceived_bandwidth(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict:
    # Compute the total ticks and cycles
    simTicks      = util.check_and_fetch_key(extractedPars, "simTicks", 0)
    ticksPerCycle = util.check_and_fetch_key(extractedPars, "ticksPerCycle", 0)
    simFreq       = util.check_and_fetch_key(extractedPars, "simFreq", 0)

    # Compute the perceived average latencies of CPU/DMAs
    cpuFinalLatency  = util.check_and_fetch_key(extractedPars, "cpuFinalLatency")
    cpuTotalLatency  = util.check_and_fetch_key(extractedPars, "cpuTotalLatency")
    cpuNumReads      = util.check_and_fetch_key(extractedPars, "cpuNumReads")
    cpuNumWrites     = util.check_and_fetch_key(extractedPars, "cpuNumWrites")
    cpuPercvdBwList  = []
    cpuPercvdLatList = []
    if (
        (cpuTotalLatency is not None)
        and (cpuFinalLatency is not None)
        and (cpuNumReads is not None)
        and (cpuNumWrites is not None)
    ) :
        assert(len(cpuFinalLatency)==len(cpuNumReads))
        assert(len(cpuFinalLatency)==len(cpuNumWrites))
        assert(len(cpuFinalLatency)==len(cpuTotalLatency))
        accesses = list(zip(cpuNumReads,cpuNumWrites,cpuFinalLatency,cpuTotalLatency))
        for rd,wr,finalLat,totalLat in accesses :
            cpuPercvdBwList.append(float(64*(rd+wr))/(float(finalLat) / float(simFreq) * 1000 * 1000 * 1000))
            cpuPercvdLatList.append(int(float(totalLat)/float((rd+wr)*ticksPerCycle)))

    dmaFinalLatency  = util.check_and_fetch_key(extractedPars, "dmaFinalLatency")
    dmaTotalLatency  = util.check_and_fetch_key(extractedPars, "dmaTotalLatency")
    dmaNumReads      = util.check_and_fetch_key(extractedPars, "dmaNumReads")
    dmaNumWrites     = util.check_and_fetch_key(extractedPars, "dmaNumWrites")
    dmaPercvdBwList  = []
    dmaPercvdLatList = []
    if (
        (dmaFinalLatency is not None)
        and (dmaNumReads is not None)
        and (dmaNumWrites is not None)
    ) :
        assert(len(dmaFinalLatency)==len(dmaNumReads))
        assert(len(dmaFinalLatency)==len(dmaNumWrites))
        assert(len(dmaFinalLatency)==len(dmaTotalLatency))
        accesses = list(zip(dmaNumReads,dmaNumWrites,dmaFinalLatency,dmaTotalLatency))
        for rd,wr,finalLat,totalLat in accesses :
            dmaPercvdBwList.append(float(64*(rd+wr))/(float(finalLat) / float(simFreq) * 1000 * 1000 * 1000))
            dmaPercvdLatList.append(int(float(totalLat)/float((rd+wr)*ticksPerCycle)))
    return {
        'cpuPerceivedAvgLat': st.mean(cpuPercvdLatList),
        'cpuPerceivedAvgBw': st.mean(cpuPercvdBwList),
        'dmaPerceivedAvgLat': st.mean(dmaPercvdLatList),
        'dmaPerceivedAvgBw': st.mean(dmaPercvdBwList)
    }