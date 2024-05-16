import math

syncChannel = 0

def convert_to_hex_list(count, data) -> list:
    if type(data) == list:
        if len(data) == 1:
            return [format(data[0], "#x")] * count
        if len(data) == count:
            for i in range(count):
                data[i] = data[i] if type(data[i]) == str else format(data[i], "#x")
            return data
        raise ValueError(f"Invalid Data Length: 1 or {count} expected, got {len(data)}")
    
    if type(data) == int:
        return [format(data, "#x")] * count
    
    if type(data) == str:
        return [data] * count
        
def get_int_list(hartList):
    if type(hartList) == int:
        hartList = [hartList]
        hartCount = 1
    elif type(hartList) == list:
        hartCount = len(hartList)
    else:
        raise ValueError(f"Invalid Hart List: {hartList}")
    
    return hartCount, hartList
  

def random_addr_load() -> list:
    raise NotImplementedError("Operations currently not supported!")

def random_addr_store() -> list:
    raise NotImplementedError("Operations currently not supported!")

def random_addr_load_region() -> list:
    raise NotImplementedError("Operations currently not supported!")

def random_addr_store_region() -> list:
    raise NotImplementedError("Operations currently not supported!")

def access_region() -> list:
    raise NotImplementedError("Operations currently not supported!")

def random_addr_access_region():
    raise NotImplementedError("Operations currently not supported!")

def dump() -> list:
    raise NotImplementedError("Operations currently not supported!")

class PseudoInst:
    PseudoInstList = []
    IRInstList = []
    SyncChannel = 0
    def __init__(self) -> None:
        pass

    def load(self, hartList, addrList, loadSizeList, delayList = 0):
        """
        Issue Vanilla Load Instruction (IR ==> LD)
        """
        hartCount, hartList = get_int_list(hartList)
        addrList = convert_to_hex_list(hartCount, addrList)
        delayList = convert_to_hex_list(hartCount, delayList)
        loadSizeList = convert_to_hex_list(hartCount, loadSizeList)
        self.PseudoInstList.append(f"load(hartList={hartList}, addrList={addrList}, loadSizeList={loadSizeList}, delayList={delayList})")
        for i in range(hartCount):
            self.IRInstList.append(f"LOAD(hart={hartList[i]}, instSize=2, delay={delayList[i]}, loadSize={loadSizeList[i]}, addr={addrList[i]})")

    def store(self, hartList, addrList, storeSizeList, storeDataList, delayList = 0, useRandomValueList = 1):
        """
        Issue Vanilla Store Instruction (IR ==> ST, RVST)
        """
        hartCount, hartList = get_int_list(hartList)
        addrList = convert_to_hex_list(hartCount, addrList)
        delayList = convert_to_hex_list(hartCount, delayList)
        storeSizeList = convert_to_hex_list(hartCount, storeSizeList)
        storeDataList = convert_to_hex_list(hartCount, storeDataList)
        useRandomValueList = convert_to_hex_list(hartCount, useRandomValueList)
        self.PseudoInstList.append(f"store(hartList={hartList}, addrList={addrList}, storeSizeList={storeSizeList}, storeDataList={storeDataList}, delayList={delayList}, useRandomValueList={useRandomValueList})")
        for i in range(hartCount):
            if useRandomValueList[i] == 0:
                self.IRInstList.append(f"STORE(hart={hartList[i]}, instSize={2+math.ceil(storeSizeList[i] / 8)}, delay={delayList[i]}, storeSize={storeSizeList[i]}, addr={addrList[i]}, storeData={storeDataList[i]})")
            else:
                self.IRInstList.append(f"RANDOM_VALUE_STORE(hart={hartList[i]}, instSize=2, delay={delayList[i]}, storeSize={storeSizeList[i]}, addr={addrList[i]})")

    def load_region(self, hartList, loadSizeList, startAddrList, endAddrList, addrIntervalList = 0x40, delayList = 0):
        """
        Issue Region Load Instruction (IR ==> LDR)
        """
        hartCount, hartList = get_int_list(hartList)
        startAddrList = convert_to_hex_list(hartCount, startAddrList)
        endAddrList = convert_to_hex_list(hartCount, endAddrList)
        addrIntervalList = convert_to_hex_list(hartCount, addrIntervalList)
        loadSizeList = convert_to_hex_list(hartCount, loadSizeList)
        delayList = convert_to_hex_list(hartCount, delayList)
        self.PseudoInstList.append(f"load_region(hartList={hartList}, loadSizeList={loadSizeList}, startAddrList={startAddrList}, endAddrList={endAddrList}, addrIntervalList={addrIntervalList}, delayList={delayList})")
        for i in range(hartCount):
            self.IRInstList.append(f"LOAD_REGION(hart={hartList[i]}, instSize=4, delay={delayList[i]}, loadSize={loadSizeList[i]}, startAddr={startAddrList[i]}, endAddr={endAddrList[i]}, addrInterval={addrIntervalList[i]})")

    def store_region(self, hartList, storeSizeList, storeDataList, startAddrList, endAddrList, addrIntervalList = 0x40, delayList = 0, useRandomValueList = 1):
        """
        Issue Region Store Instruction (IR ==> STR, RVSTR)
        """
        hartCount, hartList = get_int_list(hartList)
        startAddrList = convert_to_hex_list(hartCount, startAddrList)
        endAddrList = convert_to_hex_list(hartCount, endAddrList)
        addrIntervalList = convert_to_hex_list(hartCount, addrIntervalList)
        storeSizeList = convert_to_hex_list(hartCount, storeSizeList)
        storeDataList = convert_to_hex_list(hartCount, storeDataList)
        delayList = convert_to_hex_list(hartCount, delayList)
        useRandomValueList = convert_to_hex_list(hartCount, useRandomValueList)
        self.PseudoInstList.append(f"store_region(hartList={hartList}, storeSizeList={storeSizeList}, storeDataList={storeDataList}, startAddrList={startAddrList}, endAddrList={endAddrList}, addrIntervalList={addrIntervalList}, delayList={delayList}, useRandomValueList={useRandomValueList})")
        for i in range(hartCount):
            if useRandomValueList[i] == 0:
                self.IRInstList.append(f"STORE_REGION(hart={hartList[i]}, instSize={2+math.ceil(storeSizeList[i] / 8)}, delay={delayList[i]}, storeSize={storeSizeList[i]}, startAddr={startAddrList[i]}, endAddr={endAddrList[i]}, addrInterval={addrIntervalList[i]}, storeData={storeDataList[i]})")
            else:
                self.IRInstList.append(f"RANDOM_VALUE_STORE_REGION(hart={hartList[i]}, instSize=4, delay={delayList[i]}, storeSize={storeSizeList[i]}, startAddr={startAddrList[i]}, endAddr={endAddrList[i]}, addrInterval={addrIntervalList[i]})")

    def fence(self, hartList, delayList = 0):
        """
        Issue Fence Instruction (IR ==> FENCE)
        """
        hartCount, hartList = get_int_list(hartList)
        delayList = convert_to_hex_list(hartCount, delayList)
        self.PseudoInstList.append(f"fence(hartList={hartList}, delayList={delayList})")
        for i in range(hartCount):
            self.IRInstList.append(f"FENCE(hart={hartList[i]}, instSize=1, delay={delayList[i]})")

    def sync(self, hartList, delayList = 0):
        """
        Issue Sync Instruction (IR ==> SYNC)
        """
        hartCount, hartList = get_int_list(hartList)
        delayList = convert_to_hex_list(hartCount, delayList)
        self.PseudoInstList.append(f"sync(hartList={hartList}, delayList={delayList})")
        for i in range(hartCount):
            self.IRInstList.append(f"SYNC(hart={hartList[i]}, instSize=1, delay={delayList[i]}, channel={self.SyncChannel % (2**16)}, count={hartCount})")
        self.SyncChannel += 1

    def begin_loop(self, hartList, loopCountList, delayList = 0):
        """
        Issue Begin_loop Instruction (IR ==> BLOOP)
        """
        hartCount, hartList = get_int_list(hartList)
        loopCountList = convert_to_hex_list(hartCount, loopCountList)
        delayList = convert_to_hex_list(hartCount, delayList)
        self.PseudoInstList.append(f"begin_loop(hartList={hartList}, loopCountList={loopCountList}, delayList={delayList})")
        for i in range(hartCount):
            self.IRInstList.append(f"BEGIN_LOOP(hart={hartList[i]}, instSize=1, delay={delayList[i]}, loopCount={loopCountList[i]})")

    def end_loop(self, hartList, delayList = 0):
        """
        Issue End_loop Instruction (IR ==> ELOOP)
        """
        hartCount, hartList = get_int_list(hartList)
        delayList = convert_to_hex_list(hartCount, delayList)
        self.PseudoInstList.append(f"end_loop(hartList={hartList}, delayList={delayList})")
        for i in range(hartCount):
            self.IRInstList.append(f"END_LOOP(hart={hartList[i]}, instSize=1, delay={delayList[i]})")

    def nop(self, hartList, delayList = 1, extraDelayList = 0):
        """
        Issue Nop Instruction (IR ==> NOP)
        """
        hartCount, hartList = get_int_list(hartList)
        delayList = convert_to_hex_list(hartCount, delayList)
        extraDelayList = convert_to_hex_list(hartCount, extraDelayList)
        self.PseudoInstList.append(f"nop(hartList={hartList}, delayList={delayList}, extraDelayList={extraDelayList})")
        for i in range(hartCount):
            self.IRInstList.append(f"NOP(hart={hartList[i]}, instSize=1, delay={delayList[i]}, extraDelay={extraDelayList[i]})")
