import os
import sys
import util
import logging
import statistics as st
import pprint as pp
import pandas as pd
import analyzer.CHID2D_analyzer as chid2da

def analyze_rest(runtimeConfig: dict, extractedPars: dict, targetDir: str)-> dict :
    ret = {
        "numGenCpus": util.getNumGenCpus(runtimeConfig),
        "numGenDmas": util.getNumGenDmas(runtimeConfig),
        "hnfRetryAcks":  util.check_and_fetch_key(extractedPars, "hnfRetryAcks", 0)
    }
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
    cpuNumViolations = util.check_and_fetch_key(extractedPars, "cpuNumViolations")
    cpuPercvdBwList  = []
    cpuPercvdLatList = []
    cpuLatVioList    = []
    if (
        (cpuTotalLatency is not None)
        and (cpuFinalLatency is not None)
        and (cpuNumReads is not None)
        and (cpuNumWrites is not None)
        and (cpuNumViolations is not None)
        and (len(cpuTotalLatency) > 0)
    ) :
        assert(len(cpuFinalLatency)==len(cpuNumReads))
        assert(len(cpuFinalLatency)==len(cpuNumWrites))
        assert(len(cpuFinalLatency)==len(cpuNumViolations))
        assert(len(cpuFinalLatency)==len(cpuTotalLatency))
        accesses = list(zip(cpuNumReads,cpuNumWrites,cpuNumViolations,cpuFinalLatency,cpuTotalLatency))
        for rd,wr,vio,finalLat,totalLat in accesses :
            if finalLat > 0 :
                cpuPercvdBwList.append(float(64*(rd+wr))/(float(finalLat) / float(simFreq) * 1000 * 1000 * 1000))
                cpuPercvdLatList.append(int(float(totalLat)/float((rd+wr)*ticksPerCycle)))
                cpuLatVioList.append(100*float(vio)/float(rd+wr))

    dmaFinalLatency  = util.check_and_fetch_key(extractedPars, "dmaFinalLatency")
    dmaTotalLatency  = util.check_and_fetch_key(extractedPars, "dmaTotalLatency")
    dmaNumReads      = util.check_and_fetch_key(extractedPars, "dmaNumReads")
    dmaNumWrites     = util.check_and_fetch_key(extractedPars, "dmaNumWrites")
    dmaPercvdBwList  = []
    dmaPercvdLatList = []
    if (
        (dmaTotalLatency is not None)
        and (dmaFinalLatency is not None)
        and (dmaNumReads is not None)
        and (dmaNumWrites is not None)
        and (len(dmaTotalLatency) > 0)
    ) :
        assert(len(dmaFinalLatency)==len(dmaNumReads))
        assert(len(dmaFinalLatency)==len(dmaNumWrites))
        assert(len(dmaFinalLatency)==len(dmaTotalLatency))
        accesses = list(zip(dmaNumReads,dmaNumWrites,dmaFinalLatency,dmaTotalLatency))
        for rd,wr,finalLat,totalLat in accesses :
            if finalLat > 0 :
                dmaPercvdBwList.append(float(64*(rd+wr))/(float(finalLat) / float(simFreq) * 1000 * 1000 * 1000))
                dmaPercvdLatList.append(int(float(totalLat)/float((rd+wr)*ticksPerCycle)))
    cpuAvgLat = 0
    if len(cpuPercvdLatList) > 0 :
        cpuAvgLat = st.mean(cpuPercvdLatList)
    cpuAvgBw  = 0
    if len(cpuPercvdBwList) > 0 :
        cpuAvgBw = st.mean(cpuPercvdBwList)
    dmaAvgLat = 0
    if len(dmaPercvdLatList) > 0 :
        dmaAvgLat = st.mean(dmaPercvdLatList)
    dmaAvgBw  = 0
    if len(dmaPercvdBwList) > 0 :
        dmaAvgBw = st.mean(dmaPercvdBwList)
    latVioAvg = 0
    if len(cpuLatVioList) > 0 :
        latVioAvg = st.mean(cpuLatVioList)
    return {
        'cpuPerceivedAvgLat': cpuAvgLat,
        'cpuPerceivedAvgBw': cpuAvgBw,
        'cpuLatVio': latVioAvg,
        'dmaPerceivedAvgLat': dmaAvgLat,
        'dmaPerceivedAvgBw': dmaAvgBw
    }