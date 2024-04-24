import re
import os
import copy as cpy
import pprint as pp
import pandas as pd
from typing import Dict, List
from dataclasses import dataclass

"""
This test assumes that all
addresses are unique, because
address are used as keys to 
identify the messages produced
to complete a transaction. However,
this is quite a restrictive assumptions
as there could be multiple requests to
same address from different requestors.
In that case, one needs to determine a
better method to tag the messages, such
as transaction IDs etc. One such 
approach was implemented by Zhiang,
but that could handle repl and sfrepl
messages
"""

nocAgentPat1  = re.compile(r'system.ruby.networks(\d*)')
nocAgentPat2  = re.compile(r'system.ruby.network')
l1AgentPat    = re.compile(r'system.cpu(\d*).l1([id])')
l2AgentPat    = re.compile(r'system.cpu(\d*).l2')
hnfAgentPat1  = re.compile(r'system.ruby.hnfs(\d*).cntrl')
hnfAgentPat2  = re.compile(r'system.ruby.hnf(\d*).cntrl')
haAgentPat    = re.compile(r'system.ruby.hAs(\d*).cntrl')
snfAgentPat1  = re.compile(r'system.ruby.snfs(\d*).cntrl')
snfAgentPat2  = re.compile(r'system.ruby.snf(\d*).cntrl')
d2dNodePat    = re.compile(r'system.ruby.d2dnodes(\d*).cntrl')
d2dBridgePat  = re.compile(r'system.ruby.d2dbridges(\d*)')
statisticDict = {}
addrList = []

def getVnetId(opcode,msg_type):
    """
        Obtain the VCId of 
        the message. The following convention
        is used
        REQ --> 0
        SNP --> 1
        RSP --> 2
        DAT --> 3
    """
    if (msg_type=='RubyRequest') :
        return 0
    if ((opcode == 'ReadShared') or
       (opcode == 'ReadNotSharedDirty') or
       (opcode == 'ReadUnique') or
       (opcode == 'ReadOnce') or
       (opcode == 'WriteBackFull') or
       (opcode == 'WriteCleanFull') or
       (opcode == 'WriteEvictFull') or
       (opcode == 'CleanUnique') or
       (opcode == 'Evict') or
       (opcode == 'WriteUniqueFull') or
       (opcode == 'WriteNoSnp') or
       (opcode == 'WriteNoSnpPtl') or
       (opcode == 'WriteNoSnpPtl') or
       (opcode == 'ReadNoSnp') or
       (opcode == 'MEMORY_READ') or
       (opcode == 'WriteUniquePtl')) :
        return 0
    elif ((opcode == 'SnpSharedFwd') or
          (opcode == 'SnpNotSharedDirtyFwd') or
          (opcode == 'SnpUniqueFwd') or
          (opcode == 'SnpOnce') or
          (opcode == 'SnpShared') or
          (opcode == 'SnpUnique') or
          (opcode == 'SnpCleanInvalid')) :
        return 1
    elif ((opcode == 'Comp_I') or
          (opcode == 'Comp_UC') or
          (opcode == 'Comp_SC') or
          (opcode == 'CompDBIDResp') or
          (opcode == 'DBIDResp') or
          (opcode == 'Comp') or
          (opcode == 'CompAck') or
          (opcode == 'ReadReceipt') or
          (opcode == 'RespSepData') or
          (opcode == 'SnpResp_I') or
          (opcode == 'SnpResp_I_Fwded_UC') or
          (opcode == 'SnpResp_SC') or
          (opcode == 'SnpResp_SC_Fwded_SC') or
          (opcode == 'SnpResp_SC_Fwded_SD_PD') or
          (opcode == 'SnpResp_UC_Fwded_I') or
          (opcode == 'SnpResp_UD_Fwded_I') or
          (opcode == 'SnpResp_SC_Fwded_I') or
          (opcode == 'SnpResp_SD_Fwded_I')) :
        return 2
    elif ((opcode == 'CompData_I') or
          (opcode == 'CompData_UC') or
          (opcode == 'CompData_SC') or
          (opcode == 'CompData_UD_PD') or
          (opcode == 'CompData_SD_PD') or
          (opcode == 'DataSepResp_UC') or
          (opcode == 'CBWrData_UC') or
          (opcode == 'CBWrData_SC') or
          (opcode == 'CBWrData_UD_PD') or
          (opcode == 'CBWrData_SD_PD') or
          (opcode == 'CBWrData_I') or
          (opcode == 'NCBWrData') or
          (opcode == 'SnpRespData_I') or
          (opcode == 'SnpRespData_I_PD') or
          (opcode == 'SnpRespData_SC') or
          (opcode == 'SnpRespData_SC_PD') or
          (opcode == 'SnpRespData_SD') or
          (opcode == 'SnpRespData_UD') or
          (opcode == 'SnpRespData_SC_Fwded_SC') or
          (opcode == 'SnpRespData_SC_Fwded_SD_PD') or
          (opcode == 'SnpRespData_SC_PD_Fwded_SC') or
          (opcode == 'SnpRespData_I_Fwded_SD_PD') or
          (opcode == 'SnpRespData_I_Fwded_SC')) :
        return 3
    else :
        return -1
        
@dataclass
class AgentMsgTraversal(object):
    txn: str
    addr: str
    opcode: str
    msg_type: str
    deq_time: int
    agent_name: str
    vnetId: int
    delta: float

    def __lt__(self,other):
        return self.deq_time < other.deq_time
    
    def __le__(self,other):
        return self.deq_time <= other.deq_time
    
    def __gt__(self,other):
        return self.deq_time > other.deq_time
    
    def __ge__(self,other):
        return self.deq_time >= other.deq_time
    
    def setDelta(self, delta):
        self.delta = delta

    def getDumpStr(self):
        return f'{self.agent_name}({self.opcode}),{self.delta}'

@dataclass
class Traversal(object):
    txn: str
    addr: str
    agent_list: Dict[int, List[AgentMsgTraversal]] # The first index is vnetId

    def getCanonicalRdMsgChainNoSnp(self):
        """
            The canonical path traces
            {
                'IssueTime' : Cyc
                'L1-->L2'   : Lat
                'L2-->HNF'  : Lat
                'HnfId'     : Lat
                'HNF-->HA'  : Lat
                'HA-->SNF'  : Lat
                'SNF'       : Lat
                'SNF-->HA'  : Lat
                'HA-->HNF'  : Lat
                'HNF-->L2'  : Lat
                'L2-->Req'  : Lat
            }
        """
        ret = {
            'IssueTime' : self.agent_list[0][0].deq_time
        }
        pass

    def combineVnetMsgs(self) -> List[AgentMsgTraversal] :
        x: List[AgentMsgTraversal] = []
        for vnetId, trvsls in self.agent_list :
            x.extend(trvsls)
        return sorted(x)  

    def dump(self,f2,printHeader):
        combinedAgentTraversals = []
        for _,agt in self.agent_list.items() :
            combinedAgentTraversals.extend(agt)
        sortedAgentTaversals = sorted(combinedAgentTraversals)
        if printHeader :
            print('txn,addr,deqcyc,agent,opcode',file=f2)
        for arr in sortedAgentTaversals :
            txn = arr.txn
            addr = arr.addr
            deqcyc = arr.deq_time
            agent = arr.agent_name
            opcode = arr.opcode
            print(f'{txn},{addr},{deqcyc},{agent},{opcode}',file=f2)
            if opcode == "NA":
                statisticDict[int(addr, 16)] = (f"{addr}", f"{deqcyc}")

def translateAgentName(agent):
    nocAgentMtch1 = nocAgentPat1.search(agent)
    nocAgentMtch2 = nocAgentPat2.search(agent)
    l1AgentMtch   = l1AgentPat.search(agent)
    l2AgentMtch   = l2AgentPat.search(agent)
    hnfAgentMtch1 = hnfAgentPat1.search(agent)
    hnfAgentMtch2 = hnfAgentPat2.search(agent)
    haAgentMtch   = haAgentPat.search(agent)
    snfAgentMtch1 = snfAgentPat1.search(agent)
    snfAgentMtch2 = snfAgentPat2.search(agent)
    d2dNodeMtch   = d2dNodePat.search(agent)
    d2dBridgeMtch = d2dBridgePat.search(agent)
    if nocAgentMtch1 :
        return f'Die{nocAgentMtch1.group(1)}'
    if nocAgentMtch2 :
        return f'NoC'
    elif l1AgentMtch :
        return f'cpu{l1AgentMtch.group(1)}.l1{l1AgentMtch.group(2)}'
    elif l2AgentMtch :
        return f'cpu{l2AgentMtch.group(1)}.l2'
    elif hnfAgentMtch1 :
        return f'hnf{hnfAgentMtch1.group(1)}'
    elif hnfAgentMtch2 :
        return f'hnf{hnfAgentMtch2.group(1)}'
    elif haAgentMtch :
        return f'hA{haAgentMtch.group(1)}'
    elif snfAgentMtch1 :
        return f'snf{snfAgentMtch1.group(1)}'
    elif snfAgentMtch2 :
        return f'snf{snfAgentMtch2.group(1)}'
    elif d2dNodeMtch :
        return f'd2dNode{d2dNodeMtch.group(1)}'
    elif d2dBridgeMtch :
        return f'd2dBridge{d2dBridgeMtch.group(1)}'
    else :
        return 'NA'

def genMessageLists(trcFile) -> Dict[str,Traversal]:
    req_pat       = re.compile(r'^(\s*\d*): (\S+): txsn: (\S+), addr: (\S+), deq, RubyRequest')
    msg_pat       = re.compile(r'^(\s*\d*): (\S+): txsn: (\S+), addr: (\S+), deq, ([a-zA-Z_]+), ([a-zA-Z_]+)')
    allTxns       = dict()
    msgTypeToChannelMap = {
        'CHIRequestMsg': 'REQ/SNP',
        'CHIResponseMsg': 'RSP',
        'CHIDataMsg': 'DAT'
    }
    with open(trcFile,mode='r') as f :
        lines = f.readlines()
        for l in lines :
            req_match       = req_pat.search(l)
            msg_match       = msg_pat.search(l)
            cyc      = -1
            txn      = 'NA'
            agent    = 'NA'
            addr     = 'NA'
            msg_type = 'NA'
            opcode   = 'NA'
            if req_match :
                cyc      = (int(req_match.group(1)))/500
                agent    = req_match.group(2)
                txn      = req_match.group(3)
                addr     = req_match.group(4)
                msg_type = 'RubyRequest'
                opcode   = 'NA' 
            elif msg_match :
                cyc      = (int(msg_match.group(1)))/500
                agent    = msg_match.group(2)
                txn      = msg_match.group(3)
                addr     = msg_match.group(4)
                msg_type = msgTypeToChannelMap.get(msg_match.group(5),'NA')
                opcode   = msg_match.group(6)
            vnetId = getVnetId(opcode,msg_type)
            agentMsgTraversal = AgentMsgTraversal(
                txn = txn,
                addr = addr,
                opcode = opcode,
                msg_type = msg_type,
                deq_time = cyc,
                vnetId = vnetId,
                agent_name = translateAgentName(agent),
                delta = 0.0
            )
            if txn != 'NA' and txn != '0x0000000000000000':
                if txn in allTxns :
                    if not (vnetId in allTxns[txn].agent_list) :
                        allTxns[txn].agent_list[vnetId] = [agentMsgTraversal]
                    else :
                        prevTrvsl = allTxns[txn].agent_list[vnetId][-1]
                        delta = agentMsgTraversal.deq_time - prevTrvsl.deq_time
                        if ((prevTrvsl.agent_name == agentMsgTraversal.agent_name) and
                            (prevTrvsl.msg_type == agentMsgTraversal.msg_type)) :
                            # Do not append, just increment the delta
                            prevTrvsl.setDelta(agentMsgTraversal.delta + delta)
                        else :
                            agentMsgTraversal.setDelta(delta)
                            allTxns[txn].agent_list[vnetId].append(agentMsgTraversal)
                else :
                    allTxns[txn] = Traversal(
                        txn = txn,
                        addr = addr,
                        agent_list = dict([(vnetId, [agentMsgTraversal])])
                    )
                    addrList.append(int(addr, 16))
    return allTxns

def getAllStatsDir(root_dir):
    # Recursive function to find all files named "stats.txt" in the folder and its subfolders
    def find_output_dirs(folder):
        output_dirs = []
        for root, dirs, files in os.walk(folder):
            for file in files:
                if file == "stats.txt":
                    # Check if the filepath contains "CHECKPNT"
                    if "CHECKPNT" not in root:
                        output_dirs.append(root)
        return output_dirs
    output_dirs = find_output_dirs(root_dir)
    return output_dirs

def dumpMessages(root_dir, allTxns):
    dumpDir = os.path.join(root_dir,'LatencyBreakdownDump')
    os.system(f'mkdir -p {dumpDir}')
    fl = os.path.join(dumpDir,f'dumpAll.csv')
    print(f'Writing to {fl}')
    printHeader = True
    with open(fl,'w') as f2 :
        for k,v in allTxns.items():
            v.dump(f2,printHeader)
            if printHeader :
                printHeader = False
    return fl

def analyze_trace_request_latency2(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict :
    output_dirs = getAllStatsDir(targetDir)
    for i in range(len(output_dirs)):
        dumpFileName = os.path.join(output_dirs[i],'breakdownLatency.csv')
        with open(dumpFileName,'w') as f2 :
            trcFile  = os.path.join(output_dirs[i],'debug.trace')
            allTxns  = genMessageLists(trcFile)
            for k,v in allTxns.items() :
                dumpStr = f'{k},{v.addr}'
                trvrls_cnt = 0
                trvrls_cnt_max = sum([len(v2) for _,v2 in v.agent_list.items()])
                for vnetId, tmpList in v.agent_list.items() :
                    dumpStr += f','
                    sortedAgentList = sorted(tmpList)
                    for trvsl in sortedAgentList :
                        dumpStr += trvsl.getDumpStr()
                        trvrls_cnt += 1
                        if trvrls_cnt < trvrls_cnt_max :
                            dumpStr += ','
                print(dumpStr, file=f2)
            print(f'Writing to {dumpFileName}')
    return {}

def analyze_trace_request_latency3(runtimeConfig: dict, extractedPars: dict, targetDir: str) -> dict :
    # INCOMPLETE/ABANDONED
    output_dirs = getAllStatsDir(targetDir)
    for i in range(len(output_dirs)):
        dumpFileName = os.path.join(output_dirs[i],'breakdownLatencyNew.csv')
        with open(dumpFileName,'w') as f2 :
            trcFile  = os.path.join(output_dirs[i],'debug.trace')
            allTxns  = genMessageLists(trcFile)
            # print(f'TxnId,Addr,ReqtorId,L1-->L2,L2-->HNF,HNFId,HNF-->HA,HA-->SNF,SNF,SNF-->HA,HA-->HNF,HNF-->L2')
            for txns,trvsl in allTxns.items() :
                msgCanonicalChain = trvsl.getCanonicalRdMsgChainNoSnp()
                
    return {}



def main(runtimeConfig: dict, extractedPars: dict, targetDir: str):
    global addrList
    global statisticDict

    output_dirs = getAllStatsDir(targetDir)
    for i in range(len(output_dirs)):
        trcFile  = os.path.join(output_dirs[i],'debug.trace')
        allTxns  = genMessageLists(trcFile)
        dumpFile = dumpMessages(output_dirs[i], allTxns)
    
    return {}