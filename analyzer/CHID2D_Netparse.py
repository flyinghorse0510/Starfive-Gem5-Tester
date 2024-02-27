import re
import sys
import numpy as np
import matplotlib.pyplot as plt
import json
import networkx as nx
import os
import argparse
from typing import Dict,List
import logging
import pandas as pd
from collections import namedtuple
import subprocess
import pprint as pp

logging.basicConfig(level=logging.INFO)

CHIMsgType = namedtuple('CHIMsgType', ['abbr','type','enable_print'])

'''
MessageBuffer * reqOut,   network="To", virtual_network="0", vnet_type="none";
MessageBuffer * snpOut,   network="To", virtual_network="1", vnet_type="none";
MessageBuffer * rspOut,   network="To", virtual_network="2", vnet_type="none";
MessageBuffer * datOut,   network="To", virtual_network="3", vnet_type="response";
'''
CHIMsgType_dict = {
    # ReqMsg
    'Load':CHIMsgType('LD', 0, 0),
    'Store':CHIMsgType('ST', 0, 0),
    'StoreLine':CHIMsgType('STLine', 0, 0),
    # Incoming DVM-related requests generated by the sequencer
    'DvmTlbi_Initiate':CHIMsgType('DvmTlbiInit', 0, 0),
    'DvmSync_Initiate':CHIMsgType('DvmSyncInit', 0, 0),
    'DvmSync_ExternCompleted':CHIMsgType('DvmSyncExtCmp', 0, 0),
    'ReadShared':CHIMsgType('ReadS', 0, 0),
    'ReadNotSharedDirty':CHIMsgType('ReadNSD',0, 0),
    'ReadUnique':CHIMsgType('ReadU',0, 0),
    'ReadOnce':CHIMsgType('ReadO',0, 0),
    'CleanUnique':CHIMsgType('CleanU',0, 0),
    'Evict':CHIMsgType('Evict',0, 0),
    'WriteBackFull':CHIMsgType('WBFull',0, 0),
    'WriteCleanFull':CHIMsgType('WCFull',0, 0),
    'WriteEvictFull':CHIMsgType('WEFull',0, 0),
    'WriteUniquePtl':CHIMsgType('WUPtl',0, 0),
    'WriteUniqueFull':CHIMsgType('WUFull',0, 0),
    # Snps
    'SnpSharedFwd':CHIMsgType('SnpSFwd',1,0),
    'SnpNotSharedDirtyFwd':CHIMsgType('SnpNSDFwd',1,0),
    'SnpUniqueFwd':CHIMsgType('SnpUFwd',1,0),
    'SnpOnceFwd':CHIMsgType('SnpOFwd',1,0),
    'SnpOnce':CHIMsgType('SnpOnce',1,0),
    'SnpShared':CHIMsgType('SnpS',1,0),
    'SnpUnique':CHIMsgType('SnpU',1,0),
    'SnpCleanInvalid':CHIMsgType('SnpCI',1,0),
    'SnpDvmOpSync_P1':CHIMsgType('SnpDvmSyncP1',1,0),
    'SnpDvmOpSync_P2':CHIMsgType('SnpDvmSyncP2',1,0),
    'SnpDvmOpNonSync_P1':CHIMsgType('SnpDvmNSyncP1',1,0),
    'SnpDvmOpNonSync_P2':CHIMsgType('SnpDvmNSyncP2',1,0),
    # ReqMsgs
    'WriteNoSnpPtl':CHIMsgType('WriteNSnpPtl',0,0),
    'WriteNoSnp':CHIMsgType('WriteNSnp',0,0),
    'ReadNoSnp':CHIMsgType('ReadNoSnp',0,0),
    'ReadNoSnpSep':CHIMsgType('ReadNSnpSep',0,0),
    'DvmOpNonSync':CHIMsgType('DvmOpNSync',0,0),
    'DvmOpSync':CHIMsgType('DvnOpSync',0,0),
    # RspMsg
    'Comp_I':CHIMsgType('CmpI',2,0),
    'Comp_UC':CHIMsgType('CmpUC',2,0),
    'Comp_SC':CHIMsgType('CmpSC',2,0),
    'CompAck':CHIMsgType('CmpAck',2,0),
    'CompDBIDResp':CHIMsgType('CmpDBIDRsp',2,0),
    'DBIDResp':CHIMsgType('DBIDRsp',2,0),
    'Comp':CHIMsgType('Cmp', 2,0),
    'ReadReceipt':CHIMsgType('ReadReceipt', 2,0),
    'RespSepData':CHIMsgType('RspSepData', 2,0),
    'SnpResp_I':CHIMsgType('SnpRspI', 2,0),
    'SnpResp_I_Fwded_UC':CHIMsgType('SnpRspIFwdUC', 2,0),
    'SnpResp_I_Fwded_UD_PD':CHIMsgType('SnpRspIFwdUDPD', 2,0),
    'SnpResp_SC':CHIMsgType('SnpRspSC', 2,0),
    'SnpResp_SC_Fwded_SC':CHIMsgType('SnpRspSCFwdSC', 2,0),
    'SnpResp_SC_Fwded_SD_PD':CHIMsgType('SnpRspSCFwdSDPD', 2,0),
    'SnpResp_UC_Fwded_I':CHIMsgType('SnpRsp',2,0),
    'SnpResp_UD_Fwded_I':CHIMsgType('SnpRspUDFwdI', 2,0),
    'SnpResp_SC_Fwded_I':CHIMsgType('SnpRspSCFwdI', 2,0),
    'SnpResp_SD_Fwded_I':CHIMsgType('SnpRspSDFwdI', 2,0),
    'RetryAck':CHIMsgType('RetryAck', 2,0),
    'PCrdGrant':CHIMsgType('PCrdGrant', 2,0),
    # DatMsg
    'CompData_I':CHIMsgType('CmpDatI',3,1),
    'CompData_UC':CHIMsgType('CmpDatUC',3,1),
    'CompData_SC':CHIMsgType('CmpDatSC',3,1),
    'CompData_UD_PD':CHIMsgType('CmpDatUDPD',3,1),
    'CompData_SD_PD':CHIMsgType('CmpDatSDPD',3,1),
    'DataSepResp_UC':CHIMsgType('DatSepRsp', 3,0),
    'CBWrData_UC':CHIMsgType('CBWrDatUC', 3,1),
    'CBWrData_SC':CHIMsgType('CBWrDatSC', 3,1),
    'CBWrData_UD_PD':CHIMsgType('CBWrDatUDPD', 3,1),
    'CBWrData_SD_PD':CHIMsgType('CBWrDatSDPD', 3,1),
    'CBWrData_I':CHIMsgType('CBWrDatI', 3,1),
    'NCBWrData':CHIMsgType('NCBWrDat', 3,0),
    'SnpRespData_I':CHIMsgType('SnpRspDatI', 3,0),
    'SnpRespData_I_PD':CHIMsgType('SnpRspDatIPD', 3,0),
    'SnpRespData_SC':CHIMsgType('SnpRspDatSC', 3,0),
    'SnpRespData_SC_PD':CHIMsgType('SnpRspDatSCPD', 3,0),
    'SnpRespData_SD':CHIMsgType('SnpRspDatSD', 3,0),
    'SnpRespData_UC':CHIMsgType('SnpRspDatUC', 3,0),
    'SnpRespData_UD':CHIMsgType('SnpRspDatUD', 3,0),
    'SnpRespData_SC_Fwded_SC':CHIMsgType('SnpRspDatSCFwdSC', 3,0),
    'SnpRespData_SC_Fwded_SD_PD':CHIMsgType('SnpRspDatSCFwdSDPD', 3,0),
    'SnpRespData_SC_PD_Fwded_SC':CHIMsgType('SnpRspDatSCPDFwdSC', 3,0),
    'SnpRespData_I_Fwded_SD_PD':CHIMsgType('SnpRspDatIFwdSDPD', 3,0),
    'SnpRespData_I_PD_Fwded_SC':CHIMsgType('SnpRspDatIFwdSC', 3,0),
    'SnpRespData_I_Fwded_SC':CHIMsgType('SnpRspDatIFwdSC', 2, 0)
}


msg_pat = re.compile(r'^(\s*\d*): (\S+): txsn: (\w+), addr: (\S+), deq, (\S+), (\S+), (\S+)')

def test_msg_pat():
    l1 = '  87000: system.ruby.hnf.cntrl.rspIn: txsn: 0x0009000000000000, arr: 87500(int_links02.buffers2:1000), Cache-5->6, type: CompAck(0), req: 0x55fe84f46910, addr: [0x40, line 0x40]\n'
    for l in [l1]:
        msg_srch = re.search(msg_pat, l)
        msg_str = "Groups: "
        msg_str += ','.join([grp for grp in msg_srch.groups()])
        print(msg_str)

def my_draw_networkx_edge_labels(
    G,
    pos,
    edge_labels=None,
    label_pos=0.5,
    font_size=10,
    font_color="k",
    font_family="sans-serif",
    font_weight="normal",
    alpha=None,
    bbox=None,
    horizontalalignment="center",
    verticalalignment="center",
    ax=None,
    rotate=True,
    clip_on=True,
    rad=0
):

    if ax is None:
        ax = plt.gca()
    if edge_labels is None:
        labels = {(u, v): d for u, v, d in G.edges(data=True)}
    else:
        labels = edge_labels
    text_items = {}
    for (n1, n2), label in labels.items():
        (x1, y1) = pos[n1]
        (x2, y2) = pos[n2]
        (x, y) = (
            x1 * label_pos + x2 * (1.0 - label_pos),
            y1 * label_pos + y2 * (1.0 - label_pos),
        )
        pos_1 = ax.transData.transform(np.array(pos[n1]))
        pos_2 = ax.transData.transform(np.array(pos[n2]))
        linear_mid = 0.5*pos_1 + 0.5*pos_2
        d_pos = pos_2 - pos_1
        rotation_matrix = np.array([(0,1), (-1,0)])
        ctrl_1 = linear_mid + rad*rotation_matrix@d_pos
        ctrl_mid_1 = 0.5*pos_1 + 0.5*ctrl_1
        ctrl_mid_2 = 0.5*pos_2 + 0.5*ctrl_1
        bezier_mid = 0.5*ctrl_mid_1 + 0.5*ctrl_mid_2
        (x, y) = ax.transData.inverted().transform(bezier_mid)

        if rotate:
            # in degrees
            angle = np.arctan2(y2 - y1, x2 - x1) / (2.0 * np.pi) * 360
            # make label orientation "right-side-up"
            if angle > 90:
                angle -= 180
            if angle < -90:
                angle += 180
            # transform data coordinate angle to screen coordinate angle
            xy = np.array((x, y))
            trans_angle = ax.transData.transform_angles(
                np.array((angle,)), xy.reshape((1, 2))
            )[0]
        else:
            trans_angle = 0.0
        # use default box of white with white border
        if bbox is None:
            bbox = dict(boxstyle="round", ec=(1.0, 1.0, 1.0), fc=(1.0, 1.0, 1.0))
        if not isinstance(label, str):
            label = str(label)  # this makes "1" and 1 labeled the same

        t = ax.text(
            x,
            y,
            label,
            size=font_size,
            color=font_color,
            family=font_family,
            weight=font_weight,
            alpha=alpha,
            horizontalalignment=horizontalalignment,
            verticalalignment=verticalalignment,
            rotation=trans_angle,
            transform=ax.transData,
            bbox=bbox,
            zorder=1,
            clip_on=clip_on,
        )
        text_items[(n1, n2)] = t

    ax.tick_params(
        axis="both",
        which="both",
        bottom=False,
        left=False,
        labelbottom=False,
        labelleft=False,
    )

    return text_items


class Stats:
    def __init__(self, num_vnet):
        self.vnets = [0]*num_vnet

    def __str__(self):
        return f'{self.__dict__}'

class Controller:
    def __init__(self, path):
        self.path = path

    def __repr__(self):
        return self.path.split('.')[-2]

controllers:List[Controller] = []

class Router:
    def __init__(self, path, id):
        self.path = path
        self.id = id

    def __repr__(self):
        return f'R{self.id}'

class Link:

    intLinkPathPat = re.compile(r'system.ruby.networks0.int_links(\d+).buffers(\d+)')
    extLinkRNFPathPat = re.compile(r'system.cpu(\d+).(l1i|l1d|l2).(reqIn|reqOut|rspOut|rspIn|snpIn|snpOut|datOut|datIn)')
    extLinkHNFPathPat = re.compile(r'system.ruby.hnf(\d+).cntrl.(reqIn|reqOut|rspOut|rspIn|snpIn|snpOut|datOut|datIn)')

    def __init__(self, name, path, id):
        self.name = name
        self.path = path
        self.id = id

    def __repr__(self):
        return self.name
    
    @classmethod
    def getLinkAliasFromPath(cls, linkPath):
        intLinkPathMatch = cls.intLinkPathPat.search(linkPath)
        extLinkRNFPathMatch = cls.extLinkRNFPathPat.search(linkPath)
        extLinkHNFPathMatch = cls.extLinkHNFPathPat.search(linkPath)
        if intLinkPathMatch :
            intLinkId = int(intLinkPathMatch.group(1))
            return f'int.links{intLinkId:02d}'
        elif extLinkRNFPathMatch :
            cpuId = int(extLinkRNFPathMatch.group(1))
            cacheTy = extLinkRNFPathMatch.group(2)
            linkTy = extLinkRNFPathMatch.group(3)
            return f'cpu{cpuId:02d}.{cacheTy}.{linkTy}'
        elif extLinkHNFPathMatch :
            hnfId = int(extLinkHNFPathMatch.group(1))
            linkTy = extLinkHNFPathMatch.group(2)
            return f'hnf{hnfId:02d}.{linkTy}'
        else:
            raise ValueError(f'Undefined string pattern for link path: {linkPath}')

class ExtLink(Link):
    def __init__(self, name, path, id, int_node=None, ext_node=None):
        super(ExtLink,self).__init__(name,path,id)
        self.int_node = int_node
        self.ext_node = ext_node

    def __repr__(self):
        return f'ExtLink{self.id}: {self.int_node}<->{self.ext_node}'
    
    def __str__(self):
        return f'e{self.name[self.name.find("s")+1:]}'

class IntLink(Link):
    def __init__(self, name, path, id, src_node=None, dst_node=None, num_vnet=1):
        super(IntLink,self).__init__(name,path,id)
        self.src_node = src_node
        self.dst_node = dst_node
        self.stats:Stats = Stats(num_vnet=num_vnet)

    def __repr__(self):
        return f'IntLink{self.id}: {self.src_node}-->{self.dst_node}'
    
    def __str__(self):
        link_str = ''
        for i,(k,v) in enumerate(self.stats.__dict__.items()):
            if i%3==2:
                link_str += f'{k}:{v}\n'
            else:
                link_str += f'{k}:{v}, '

        return f'i{self.name[self.name.find("s")+1:]}, {link_str}'

def get_node(routers:List[Router], path):
    if isinstance(path, dict):
        path = path['path']

    for r in routers:
        if r.path == path:
            return r

    for c in controllers:
        if c.path == path:
            return c
    
    ctrl = Controller(path)
    controllers.append(ctrl)
    return ctrl

def parse_json(JSON: Dict):
    num_vnet = JSON['system']['ruby']['number_of_virtual_networks']
    logging.debug(f'num_vnet:{num_vnet}')
    networks0 = JSON['system']['ruby']['networks'][0] # system.ruby.networks0
    cyc_tick = JSON['system']['ruby']['clk_domain']['clock'][0] # clk_domain: tick per cycle
    logging.debug(f'cyc_tick: {cyc_tick}')
    routers = networks0['routers']
    routers = [Router(path=r,id=i) for i,r in enumerate(routers)]
    logging.debug(f'routers:{routers}')
    ext_links = networks0['ext_links']
    ext_links = [ExtLink(name=l['name'],path=l['path'],id=i,ext_node=get_node(routers,l['ext_node']),int_node=get_node(routers,l['int_node'])) for i,l in enumerate(ext_links)]
    logging.debug(f'ext_links:{ext_links}')
    logging.debug(f'controllers:{controllers}')
    int_links = networks0['int_links']
    int_links = [IntLink(name=l['name'],path=l['path'],id=i,src_node=get_node(routers,l['src_node']),dst_node=get_node(routers,l['dst_node']),num_vnet=num_vnet) for i,l in enumerate(int_links)]
    logging.debug(f'int_links:{int_links}')
    logging.debug(f'controllers:{controllers}')
    return ext_links, int_links, routers, cyc_tick

def parse_link_log(log_path: str, routers: List[Router], ext_links: List[ExtLink], int_links: List[IntLink], cyc_tick: int):
    routers_dict = {r.path:r for r in routers}
    int_links_dict = {l.path:l for l in int_links}
    ext_links_dict = {l.path:l for l in ext_links}

    with open(log_path,'r') as f:
        for id,line in enumerate(f):

            msg_srch = re.search(msg_pat, line)
            if not (msg_srch):
                print(f'{id}@{line}')
            assert msg_srch != None

            # 1) curTick, 2) name, 3) txsn, 4) arr time, 5) last_arr_time, 6) last_link 7) path, 8) type, 9) reqPtr
            curtick = int(msg_srch.group(1))
            issuer:str = msg_srch.group(2)
            txsn = msg_srch.group(3)
            typ = msg_srch.group(6)

            issuer:str = issuer[:issuer.rfind('.')]

            # typ can be 1) CompAck:0 2) CompAck
            # if 2) we assume there is only one channel.
            # if typ.find(':') == -1:
            #     typ,vnet = typ,0
            # else:
            #     typ,vnet = typ.split(':')
            vnet = CHIMsgType_dict[typ].type
            en_print = CHIMsgType_dict[typ].enable_print
            typ = CHIMsgType_dict[typ].abbr # use abbr


            # issuer can be int_links or req/rsp/snp/datIn, we only update msg types in links
            # this is done by grep
            if issuer.find('int_links') != -1: # links
                link = issuer
                logging.debug(f'router matched: {issuer}')
                int_links_dict[link].stats.vnets[int(vnet)]+=1
                if en_print == 1 :
                    # add new field to link's stats
                    if int_links_dict[link].stats.__dict__.get(typ) == None:
                        int_links_dict[link].stats.__dict__[typ] = 1
                    else:
                        int_links_dict[link].stats.__dict__[typ] += 1


def build_network(ext_links:List[ExtLink],int_links:List[IntLink],routers:List[Router],draw_ctrl:bool):
    G = nx.DiGraph()

    if draw_ctrl:
        G.add_nodes_from(routers)
        G.add_nodes_from(controllers)
        for e in ext_links:
            G.add_edge(e.ext_node, e.int_node, data=e)
            G.add_edge(e.int_node, e.ext_node, data=e)
        for i in int_links:
            G.add_edge(i.src_node, i.dst_node, data=i)

    else:
        G.add_nodes_from(routers)
        for i in int_links:
            G.add_edge(i.src_node, i.dst_node, data=i)

    return G

def draw_network(G, output_file, routers, num_int_router, num_ext_router, num_ctrl, draw_ctrl:bool):
    
    for num_cols in range(1,num_int_router):
        num_rows = num_int_router//num_cols
        if num_int_router==num_cols*num_rows and num_cols>=num_rows:
            break
    
    logging.debug(f'num_rows:{num_rows}, num_cols:{num_cols}')

    pos_dict = {}
    for i in range(num_int_router):
        r = routers[i]
        pos_dict[r] = np.array([(i//num_cols)*100,(i%num_cols-1)*100])
    
    logging.debug(f'pos:{pos_dict}')
    pos = nx.spring_layout(G, pos=pos_dict, fixed=list(pos_dict.keys()))
    logging.debug(f'pos:{pos}')
    node_color = ['#6096B4']*num_int_router+['#EEE9DA']*num_ext_router
    if draw_ctrl:
        node_color += ['#A7727D']*num_ctrl

    plt.figure(figsize=(12,12))
    nx.draw_networkx_nodes(G, pos, node_size=10, node_color=node_color)
    nx.draw_networkx_labels(G, pos, font_size=2)
    nx.draw_networkx_edges(G, pos, edge_color='k',connectionstyle='arc3,rad=0.1',width=0.3,arrowsize=2, node_size=10)
    my_draw_networkx_edge_labels(G, pos, edge_labels={(u, v): edge['data'] for (u, v, edge) in G.edges(data=True)},font_size=2,rad=0.1)
    plt.savefig(output_file,dpi = 800)
    logging.info(f'save fig to {output_file}')


def dump_log(ext_links:List[ExtLink],int_links:List[IntLink],routers:List[Router],dump_path):
    int_links_stats = {l.name:{'src_node':l.src_node.__repr__(), 'dst_node':l.dst_node.__repr__(), 'msg':l.stats.__dict__} for l in int_links}

    with open(dump_path, 'w+') as f:
        json.dump(int_links_stats, f, indent=2)
    
    logging.info(f'details dump to {dump_path}')


def getNoCIntLinkTraffic(stats_file, noc_csv_path, noc_json_path):
    intLinkStallPat = re.compile(r'system.ruby.networks0.int_links(\d*).buffers3.m_avg_stall_time( +)([\.\d]+)')
    intLinkOccPat   = re.compile(r'system.ruby.networks0.int_links(\d*).buffers3.m_occupancy( +)([\.\d]+)')
    intLinkBusyPat  = re.compile(r'system.ruby.networks0.int_links(\d*).buffers3.m_not_avail_count( +)(\d+)')
    intLinkTraffic  = dict()
    with open(stats_file,'r') as f :
        for line in f :
            intLinkStallMatch = intLinkStallPat.search(line)
            intLinkOccMatch   = intLinkOccPat.search(line)
            intLinkBusyMatch  = intLinkBusyPat.search(line)
            if intLinkBusyMatch :
                k       = f'int_links{intLinkBusyMatch.group(1)}'
                if k in intLinkTraffic :
                    intLinkTraffic[k]['BusyCyc'] = intLinkBusyMatch.group(3)
                else :
                    intLinkTraffic[k] = {
                        'AvgBuffOcc': 0,
                        'StallCycWasted': 0,
                        'BusyCyc': intLinkBusyMatch.group(3)
                    }
            if intLinkStallMatch :
                k       = f'int_links{intLinkStallMatch.group(1)}'
                if k in intLinkTraffic :
                    intLinkTraffic[k]['StallCycWasted'] = intLinkStallMatch.group(3)
                else :
                    intLinkTraffic[k] = {
                        'AvgBuffOcc': 0,
                        'StallCycWasted': intLinkStallMatch.group(3),
                        'BusyCyc': 0
                    }
            if intLinkOccMatch :
                k       = f'int_links{intLinkOccMatch.group(1)}'
                if k in intLinkTraffic :
                    intLinkTraffic[k]['AvgBuffOcc'] = intLinkOccMatch.group(3)
                else :
                    intLinkTraffic[k] = {
                        'AvgBuffOcc': intLinkOccMatch.group(3),
                        'StallCycWasted': 0,
                        'BusyCyc': 0
                    }

    with open(noc_json_path,'r') as f:
        noc_dump = json.load(f)
        noc_dump_list = []
        for k,v in noc_dump.items() :
            x = intLinkTraffic.get(k,None)
            avgBuffOcc = 0
            stallCycWasted = 0
            busyCyc = 0
            if x :
                avgBuffOcc     = x['AvgBuffOcc']
                stallCycWasted = x['StallCycWasted']
                busyCyc        = x['BusyCyc']
            noc_dump_list.append({
                'Link Name': k,
                'CBWrDatUC': v['msg'].get('CBWrDatUC',0),
                'CmpDatUC': v['msg'].get('CmpDatUC',0),
                'totalDat': v['msg']['vnets'][3],
                'AvgBuffOcc': avgBuffOcc,
                'StallCycWasted' : stallCycWasted,
                'BusyCyc' : busyCyc
            })
        dfX = pd.DataFrame.from_records(noc_dump_list)
        logging.info(f'Writing to {noc_csv_path}')
        dfX.to_csv(noc_csv_path,index=False)

def getAvgTraffic(options: object):

    stats_file = os.path.join(options.input,'stats.txt')
    json_file = os.path.join(options.input,'config.json')
    debug_trace = os.path.join(options.input, 'debug.trace')
    link_log = os.path.join(options.input,'link.log')
    link_log_deq = os.path.join(options.input,'link_deq.log')
    diagram_path = os.path.join(options.output, 'noc_diagram.png')
    noc_json_path = os.path.join(options.output, 'noc_details.json')
    noc_csv_path = os.path.join(options.output,'noc_details.csv')

    subprocess.run(['grep','-E', '^[[:space:]]+[0-9]+: system\.ruby\.networks0\.int_links[0-9]+\.buffers[0-9]+|^[[:space:]]+[0-9]+: system.*In:', debug_trace], stdout=open(link_log,'w+'))
    subprocess.run(['grep','-E', 'deq', link_log], stdout=open(link_log_deq,'w+'))

    logging.info(f'Parsing networks0 from {json_file}')

    ext_links, int_links, routers = None, None, None
    with open(json_file,'r') as f:
        JSON = json.load(f)
        ext_links, int_links, routers, cyc_tick = parse_json(JSON)
    
    parse_link_log(link_log_deq, routers, ext_links, int_links, cyc_tick)
    dump_log(ext_links, int_links, routers, noc_json_path)
    getNoCIntLinkTraffic(stats_file,noc_csv_path,noc_json_path)

    graph = build_network(ext_links,int_links,routers,draw_ctrl=options.draw_ctrl)
    draw_network(G=graph, routers=routers, output_file=diagram_path, 
                 num_int_router=options.num_int_router, 
                 num_ext_router=len(routers)-options.num_int_router, 
                 num_ctrl=len(controllers), draw_ctrl=options.draw_ctrl)


def getDeadLockedSubGraph(intLinksList: List[IntLink], link_contents_log):
    intLinkLogPat=re.compile(r'^(\s*\d*): (\S+): MessageBufferContents:')
    intLinkSet = set()
    intLinkMap = dict([(intLink.path,intLink) for intLink in intLinksList])
    with open(link_contents_log,'r') as fr:
        for line in fr:
            intLinkLogMatch = intLinkLogPat.match(line)
            if intLinkLogMatch :
                intPath = intLinkLogMatch.group(2).replace('.buffers0','')
                intLinkSet.add(intLinkMap[intPath])
    G = nx.DiGraph()
    for i in intLinkSet:
        G.add_edge(i.src_node, i.dst_node, data=i)
    return G

def getDeadlockChains():
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--input', required=True, type=str)
    parser.add_argument('--output', required=True, type=str)
    parser.add_argument('--draw-ctrl', required=False, action='store_true')
    parser.add_argument('--num-int-router', required=False, default=16, type=int)
    parser.add_argument('--start-time', required=False, default=0, type=int)
    parser.add_argument('--end-time', required=False, default=float('inf'), type=float)
    options = parser.parse_args()
    
    json_file = os.path.join(options.input,'config.json')
    debug_trace = os.path.join(options.input, 'debug.trace')
    link_contents_log = os.path.join(options.input, 'deadlock_path.trace')
    diagram_path = os.path.join(options.input, 'noc_diagram_deadlocked.png')
    grep_cmd = ['grep', '-E']
    tgt_links_id = list(range(21,24)) + list(range(9,12))
    hnf_ids = [12,15]
    grep_str='|'.join([f'system\.ruby\.networks0\.int_links{i}\.buffers[0-9]+' for i in tgt_links_id]+\
                       [f'system\.ruby\.hnf{i}\.cntrl' for i in hnf_ids]+\
                       [f'PerfectSwitch-{i}' for i in hnf_ids]+\
                       [f'system\.ruby\.networks0\.int_links{i}\.dst_node\.port_buffers[0-9]+' for i in list(range(9,12))])
    grep_cmd.append(grep_str)
    grep_cmd.append(debug_trace)
    # if not os.path.isfile(link_contents_log) :
    pc=subprocess.run(grep_cmd, stdout=open(link_contents_log,'w+'))


def get_avg_traffic(runtimeConfig: dict, extractedPars: dict, targetDir: str):
    class Options(object):
        def __init__(self, input, output) -> None:
            self.input = input
            self.output = output
            self.draw_ctrl = True
            self.num_int_router = 16
            self.start_time = 0
            self.end_time = float('inf')
    options = Options(targetDir, targetDir)
    getAvgTraffic(options)
    return {}

if __name__ == '__main__':
    getAvgTraffic()