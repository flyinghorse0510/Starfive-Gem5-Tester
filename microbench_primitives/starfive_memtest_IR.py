"""
Instruction Head (64-Bit)
[////][////][////////][////////////////]
  ^^    ^^      ^^            ^^
 Size OpCode   Delay      Sync/Random
 (8)   (8)     (16)          (32) 
"""

import struct

OpCode = {
    # Basic(Data) Instructions
    "LD": 0,
    "ST": 1,
    "RVST": 1,
    "LDR": 2,
    "RALD": 2,
    "RALDR": 2,
    "STR": 3,
    "RAST": 3,
    "RARVST": 3,
    "RASTR": 3,
    "RVSTR": 3,
    "RARVSTR": 3,
    # Control Instructions
    "FENCE": 4,
    "SYNC": 5,
    "BLOOP": 6,
    "ELOOP": 7,
    "NOP": 8,
    # Special (Gem5-Related) Instructions
    "DUMP": 9,
    "CLEAR": 10,
    # Store/Load Mixed Instructions
    "ACCR": 11,
    "RAACCR": 11
}

effectInstSize = {
  "LD": [2, 2],
  "ST": [2, 34],
  "LDR": [4, 4],
  "RALD": [4, 4],
  "RALDR": [4, 4],
  "STR": [4, 36],
  "RARVST": [4, 4],
  "RASTR": [4, 36],
  "RVSTR": [4, 4],
  "RARVSTR": [4, 4],
  "FENCE": [1, 1],
  "SYNC": [1, 1],
  "BLOOP": [1, 1], 
  "ELOOP": [1, 1],
  "NOP": [1, 1],
  "DUMP": [1, 1],
  "CLEAR": [1, 1],
#   "ACCR": [1, 1]
#   "RAACCR": []
}

instMap = {
    "LOAD": "LD",
    "STORE": "ST",
    "RANDOM_VALUE_STORE": "RVST",
    "LOAD_REGION": "LDR",
    "STORE_REGION": "STR",
    "RANDOM_VALUE_STORE_REGION": "RVSTR",
    "FENCE": "FENCE",
    "SYNC": "SYNC",
    "BEGIN_LOOP": "BLOOP",
    "END_LOOP": "ELOOP",
    "NOP": "NOP"
}

class BinaryInsts:
    BinInstList = {}

    def check_hart_buffer(self, hart):
        if hart not in self.BinInstList:
            self.BinInstList[hart] = []

    # Basic Instructions
    def LD(self, hart, instSize, delay, loadSize, addr):
        self.check_hart_buffer(hart)
        opCode = OpCode["LD"]
        inst = (instSize, opCode, delay, loadSize, addr)
        instFmt = "=BBHBxxxQ"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)


    def ST(self, hart, instSize, delay, storeSize, addr, storeData: int):
        self.check_hart_buffer(hart)
        opCode = OpCode["ST"]
        dataBytes = storeData.to_bytes(storeSize, "little")
        inst = (instSize, opCode, delay, storeSize, 0, addr)
        instFmt = "=BBHBBxxQ"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes + dataBytes)

    def LDR(self, hart, instSize, delay, loadSize, startAddr, endAddr, addrInterval):
        self.check_hart_buffer(hart)
        opCode = OpCode["LDR"]
        inst = (instSize, opCode, delay, loadSize, 1, startAddr, endAddr, addrInterval)
        instFmt = "=BBHBBxxQQQ"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)

    def STR(self, hart, instSize, delay, storeSize, startAddr, endAddr, addrInterval, storeData: int):
        self.check_hart_buffer(hart)
        opCode = OpCode["STR"]
        dataBytes = storeData.to_bytes(storeSize, "little")
        inst = (instSize, opCode, delay, storeSize, 1, startAddr, endAddr, addrInterval)
        instFmt = "=BBHBBxxQQQ"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes + dataBytes)

    # Randomized Instructions
    def RVST(self, hart, instSize, delay, storeSize, addr):
        """
        Random-Value Store
        """
        self.check_hart_buffer(hart)
        opCode = OpCode["RVST"]
        inst = (instSize, opCode, delay, storeSize, 1<<2, addr)
        instFmt = "=BBHBBxxQ"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)


    # Control Instructions
    def FENCE(self, hart, instSize, delay):
        self.check_hart_buffer(hart)
        opCode = OpCode["FENCE"]
        inst = (instSize, opCode, delay)
        instFmt = "BBHxxxx"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)

    def SYNC(self, hart, instSize, delay, channel, count):
        self.check_hart_buffer(hart)
        opCode = OpCode["SYNC"]
        inst = (instSize, opCode, delay, channel, count)
        instFmt = "BBHHH"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)

    def BLOOP(self, hart, instSize, delay, loopCount):
        self.check_hart_buffer(hart)
        opCode = OpCode["BLOOP"]
        inst = (instSize, opCode, delay, loopCount)
        instFmt = "BBHL"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)

    def ELOOP(self, hart, instSize, delay):
        self.check_hart_buffer(hart)
        opCode = OpCode["ELOOP"]
        inst = (instSize, opCode, delay)
        instFmt = "BBHxxxx"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)
    
    def NOP(self, hart, instSize, delay, extraDelay):
        self.check_hart_buffer(hart)
        opCode = OpCode["NOP"]
        inst = (instSize, opCode, delay, extraDelay)
        instFmt = "BBHL"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)

    # Randomized Instructions
    def RALD():
        """
        Random-Address Load
        """
        raise NotImplementedError("Instructions currently not supported!")

    def RAST():
        """
        Random-Address Store
        """
        raise NotImplementedError("Instructions currently not supported!")


    def RARVST():
        """
        Random-Address and Random-Value Store
        """
        raise NotImplementedError("Instructions currently not supported!")

    def RALDR():
        """
        Random-Address Load(Region)
        """
        raise NotImplementedError("Instructions currently not supported!")

    def RASTR():
        """
        Random-Address Store(Region)
        """
        raise NotImplementedError("Instructions currently not supported!")

    def RVSTR():
        """
        Random-Value Store(Region)
        """
        raise NotImplementedError("Instructions currently not supported!")

    def RARVSTR():
        """
        Random-Address and Random-Value Store(Region)
        """
        raise NotImplementedError("Instructions currently not supported!")


    # Special Instructions
    def DUMP():
        raise NotImplementedError("Instructions currently not supported!")

    def CLEAR():
        raise NotImplementedError("Instructions currently not supported!")
    

    def __init__(self) -> None:
        for redundantIR in instMap:
            exec(f"self.{redundantIR} = self.{instMap[redundantIR]}")