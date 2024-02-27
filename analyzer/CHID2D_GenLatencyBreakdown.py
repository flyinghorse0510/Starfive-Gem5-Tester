import re
import os
import logging
import argparse
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

nocAgentPat  = re.compile(r'system.ruby.networks(\d*)')
l1AgentPat   = re.compile(r'system.cpu(\d*).l1([id])')
l2AgentPat   = re.compile(r'system.cpu(\d*).l2')
hnfAgentPat  = re.compile(r'system.ruby.hnfs(\d*).cntrl')
haAgentPat   = re.compile(r'system.ruby.hAs(\d*).cntrl')
snfAgentPat  = re.compile(r'system.ruby.snfs(\d*).cntrl')
d2dNodePat   = re.compile(r'system.ruby.d2dnodes(\d*).cntrl')
d2dBridgePat = re.compile(r'system.ruby.d2dbridges(\d*)')
statisticDict = {}
addrList = []

@dataclass
class AgentMsgTravesal(object):
    txn: str
    addr: str
    opcode: str
    msg_type: str
    deq_time: int
    agent_name: str

    def __lt__(self,other):
        return self.deq_time < other.deq_time
    
    def __le__(self,other):
        return self.deq_time <= other.deq_time
    
    def __gt__(self,other):
        return self.deq_time > other.deq_time
    
    def __ge__(self,other):
        return self.deq_time >= other.deq_time

@dataclass
class Traversal(object):
    txn: str
    addr: str
    agent_list: List[AgentMsgTravesal]

    def dump(self,f2,printHeader):
        sortedAgentTaversals = sorted(self.agent_list)
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
    nocAgentMtch  = nocAgentPat.search(agent)
    l1AgentMtch   = l1AgentPat.search(agent)
    l2AgentMtch   = l2AgentPat.search(agent)
    hnfAgentMtch  = hnfAgentPat.search(agent)
    haAgentMtch   = haAgentPat.search(agent)
    snfAgentMtch  = snfAgentPat.search(agent)
    d2dNodeMtch   = d2dNodePat.search(agent)
    d2dBridgeMtch = d2dBridgePat.search(agent)
    if nocAgentMtch :
        return f'Die{nocAgentMtch.group(1)}'
    elif l1AgentMtch :
        return f'cpu{l1AgentMtch.group(1)}.l1{l1AgentMtch.group(2)}'
    elif l2AgentMtch :
        return f'cpu{l2AgentMtch.group(1)}.l2'
    elif hnfAgentMtch :
        return f'hnf{hnfAgentMtch.group(1)}'
    elif haAgentMtch :
        return f'hA{haAgentMtch.group(1)}'
    elif snfAgentMtch :
        return f'snf{snfAgentMtch.group(1)}'
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
            agentMsgTraversal = AgentMsgTravesal(
                txn = txn,
                addr = addr,
                opcode = opcode,
                msg_type = msg_type,
                deq_time = cyc,
                agent_name = translateAgentName(agent)
            )
            if txn != 'NA' and txn != '0x0000000000000000':
                if txn in allTxns :
                    allTxns[txn].agent_list.append(agentMsgTraversal)
                else :
                    allTxns[txn] = Traversal(
                        txn = txn,
                        addr = addr,
                        agent_list = [agentMsgTraversal]
                    )
                    addrList.append(int(addr, 16))
    return allTxns

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

def main(runtimeConfig: dict, extractedPars: dict, targetDir: str):
    global addrList
    global statisticDict
    

    output_dirs = getAllStatsDir(targetDir)
    for i in range(len(output_dirs)):
        trcFile  = os.path.join(output_dirs[i],'debug.trace')
        allTxns  = genMessageLists(trcFile)
        dumpFile = dumpMessages(output_dirs[i], allTxns)
        # allTx = pd.read_csv(dumpFile)
        # allSNFs = set(['snf0','snf1'])
        # allTx2 = allTx.query(f'agent in @allSNFs')
        # with pd.ExcelWriter('SNFReqDump.xlsx') as writer :
        #     allTx2.to_excel(writer)
        # break
    
    return {}