"""
Instruction Head (64-Bit)
[////][////][////////][////////////////]
  ^^    ^^      ^^            ^^
 Size OpCode   Delay      Sync/Random
 (8)   (8)     (16)          (32) 
"""

import struct
import sys, os
sys.path.append(f"{os.path.dirname(os.path.abspath(__file__))}/../")

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
    "RVACCR": 11,
    "RARVACCR": 11
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
  "RVACCR": [4, 4],
  "RARVACCR": [4, 4],
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
    "NOP": "NOP",
    "RANDOM_VALUE_ACCESS_REGION": "RVACCR",
    "RANDOM_ADDR_RANDOM_VALUE_ACCESS_REGION": "RARVACCR",
    "RANDOM_ADDRESS_LOAD": "RALD",
    "RANDOM_ADDRESS_STORE": "RAST",
    "RANDOM_ADDRESS_RANDOM_VALUE_STORE": "RARVST",
    "RANDOM_ADDRESS_LOAD_REGION": "RALDR",
    "RANDOM_ADDRESS_STORE_REGION": "RASTR",
    "RANDOM_ADDRESS_RANDOM_VALUE_STORE_REGION": "RARVSTR",
    "DUMP": "DUMP",
    "CLEAR": "CLEAR"
}

class BinaryInsts:

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

    def RVACCR(self, hart, instSize, delay, dataSize, readPercent, startAddr, endAddr, addrInterval):
        """
        Random-Value Access Region
        """
        self.check_hart_buffer(hart)
        opCode = OpCode["RVACCR"]
        readWeight = int((2**16 - 1) * readPercent)
        inst = (instSize, opCode, delay, dataSize, 1<<2 | 1, readWeight, startAddr, endAddr, addrInterval)
        instFmt = "=BBHBBHQQQ"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)

    def RARVACCR(self, hart, instSize, delay, dataSize, readPercent, startAddr, endAddr, addrInterval):
        """
        Random-Address & Random-Value Access Region
        """
        self.check_hart_buffer(hart)
        opCode = OpCode["RARVACCR"]
        readWeight = int((2**16 - 1) * readPercent)
        inst = (instSize, opCode, delay, dataSize, 1<<2 | 1<<1 | 1, readWeight, startAddr, endAddr, addrInterval)
        instFmt = "=BBHBBHQQQ"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)


    # Control Instructions
    def FENCE(self, hart, instSize, delay):
        self.check_hart_buffer(hart)
        opCode = OpCode["FENCE"]
        inst = (instSize, opCode, delay)
        instFmt = "=BBHxxxx"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)

    def SYNC(self, hart, instSize, delay, channel, count):
        self.check_hart_buffer(hart)
        opCode = OpCode["SYNC"]
        inst = (instSize, opCode, delay, channel, count)
        instFmt = "=BBHHH"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)

    def BLOOP(self, hart, instSize, delay, loopCount):
        self.check_hart_buffer(hart)
        opCode = OpCode["BLOOP"]
        inst = (instSize, opCode, delay, loopCount)
        instFmt = "=BBHL"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)

    def ELOOP(self, hart, instSize, delay):
        self.check_hart_buffer(hart)
        opCode = OpCode["ELOOP"]
        inst = (instSize, opCode, delay)
        instFmt = "=BBHxxxx"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)
    
    def NOP(self, hart, instSize, delay, extraDelay):
        self.check_hart_buffer(hart)
        opCode = OpCode["NOP"]
        inst = (instSize, opCode, delay, extraDelay)
        instFmt = "=BBHL"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)

    # Randomized Instructions
    def RALD(self, hart, instSize, delay, loadSize, startAddr, endAddr, addrInterval):
        """
        Random-Address Load
        """
        self.check_hart_buffer(hart)
        opCode = OpCode["RALD"]
        inst = (instSize, opCode, delay, loadSize, 1 << 1, startAddr, endAddr, addrInterval)
        instFmt = "=BBHBBxxQQQ"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)

    def RAST(self, hart, instSize, delay, storeSize, startAddr, endAddr, addrInterval, storeData: int):
        """
        Random-Address Store
        """
        self.check_hart_buffer(hart)
        opCode = OpCode["RAST"]
        dataBytes = storeData.to_bytes(storeSize, "little")
        inst = (instSize, opCode, delay, storeSize, 1 << 1, startAddr, endAddr, addrInterval)
        instFmt = "=BBHBBxxQQQ"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes + dataBytes)

    def RARVST(self, hart, instSize, delay, storeSize, startAddr, endAddr, addrInterval):
        """
        Random-Address and Random-Value Store
        """
        self.check_hart_buffer(hart)
        opCode = OpCode["RARVST"]
        inst = (instSize, opCode, delay, storeSize, 1 << 2 | 1 << 1, startAddr, endAddr, addrInterval)
        instFmt = "=BBHBBxxQQQ"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)

    def RALDR(self, hart, instSize, delay, loadSize, startAddr, endAddr, addrInterval):
        """
        Random-Address Load(Region)
        """
        self.check_hart_buffer(hart)
        opCode = OpCode["RALDR"]
        inst = (instSize, opCode, delay, loadSize, 1 << 1 | 1, startAddr, endAddr, addrInterval)
        instFmt = "=BBHBBxxQQQ"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)

    def RASTR(self, hart, instSize, delay, storeSize, startAddr, endAddr, addrInterval, storeData: int):
        """
        Random-Address Store(Region)
        """
        self.check_hart_buffer(hart)
        opCode = OpCode["RASTR"]
        dataBytes = storeData.to_bytes(storeSize, "little")
        inst = (instSize, opCode, delay, storeSize, 1 << 1 | 1, startAddr, endAddr, addrInterval)
        instFmt = "=BBHBBxxQQQ"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes + dataBytes)

    def RVSTR(self, hart, instSize, delay, storeSize, startAddr, endAddr, addrInterval):
        """
        Random-Value Store(Region)
        """
        self.check_hart_buffer(hart)
        opCode = OpCode["RVSTR"]
        inst = (instSize, opCode, delay, storeSize, 1 << 2 | 1, startAddr, endAddr, addrInterval)
        instFmt = "=BBHBBxxQQQ"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)

    def RARVSTR(self, hart, instSize, delay, storeSize, startAddr, endAddr, addrInterval):
        """
        Random-Address and Random-Value Store(Region)
        """
        self.check_hart_buffer(hart)
        opCode = OpCode["RARVSTR"]
        inst = (instSize, opCode, delay, storeSize, 1 << 2 | 1 << 1 | 1, startAddr, endAddr, addrInterval)
        instFmt = "=BBHBBxxQQQ"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)


    # Special Instructions
    def DUMP(self, hart, instSize):
        self.check_hart_buffer(hart)
        opCode = OpCode["DUMP"]
        inst = (instSize, opCode, 1)
        instFmt = "=BBHxxxx"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)

    def CLEAR(self, hart, instSize):
        self.check_hart_buffer(hart)
        opCode = OpCode["CLEAR"]
        inst = (instSize, opCode, 1)
        instFmt = "=BBHxxxx"
        instBytes = struct.pack(instFmt, *inst)
        self.BinInstList[hart].append(instBytes)    

    def __init__(self) -> None:
        self.BinInstList = {}
        for redundantIR in instMap:
            exec(f"self.{redundantIR} = self.{instMap[redundantIR]}")

    def load_IR(self, filePath):
        with open(filePath, "r") as IRFile:
            contents = IRFile.readlines()
            IRLines = [line for line in contents if line]
            for IRInst in IRLines:
                exec(f"self.{IRInst}")


    def dump_binary(self, dir: str, filePrefix: str):
        # find max hart ID and generate instruction binaries for each hart
        keyList = list(self.BinInstList.keys())
        maxHart = max(keyList)
        for hart in range(maxHart+1):
            instFilePath = os.path.join(dir, f"{filePrefix}_{hart}.inst")
            # Generate binary instructions file
            if hart in self.BinInstList:
                with open(instFilePath, "wb") as instFile:
                    for instBytes in self.BinInstList[hart]:
                        instFile.write(instBytes)
            else:
                instFile = open(instFilePath, "wb")
                instFile.close()