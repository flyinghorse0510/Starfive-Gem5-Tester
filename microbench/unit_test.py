import sys, os
import argparse

sys.path.append(f"{os.path.dirname(os.path.abspath(__file__))}/../")
from microbench_primitives import starfive_memtest_Pseudo as Pseudo
from microbench_primitives import starfive_memtest_IR as IR
import util


def generate(args = None):
    pseudoInsts = Pseudo.PseudoInst()

    # Loop Test(Nested), Access Region Test, Sync Test, Fence Test, Load Region Test
    pseudoInsts.begin_loop([0,1,2,3], 10)
    pseudoInsts.access_region([0, 1, 2, 3], 2, [0x0, 0x1000, 0x2000, 0x3000], [0x1000, 0x2000, 0x3000, 0x4000], readPercentList=0.5)

    pseudoInsts.begin_loop([0, 2], 2)
    pseudoInsts.load_region([0, 2], 4, [0x10000, 0x11000], [0x11000, 0x12000])
    pseudoInsts.end_loop([0,2])

    pseudoInsts.sync([0,1])
    pseudoInsts.sync([2,3])

    pseudoInsts.end_loop([0,1,2,3])

    pseudoInsts.load_region(0, 4, 0x10000, 0x11000)
    pseudoInsts.fence(0)

    pseudoInsts.load_region(0, 3, 0x1000, 0x2000)

    pseudoInsts.sync([0,1,2,3])
    # pseudoInsts.dump()
    pseudoInsts.clear()

    # Iterate over all instructions (except for LOOP)
    pseudoInsts.load([0,1,2,3], [0x20000, 0x30000, 0x40000, 0x50000], [2,3,4,5])
    pseudoInsts.store([0,1,2,3], [0x20040, 0x30040, 0x40040, 0x50040], [2,3,4,5], [1,2,3,4])
    pseudoInsts.load_region([0,1,2,3], [2,3,4,5], [0x20000, 0x30000, 0x40000, 0x50000], [0x21000, 0x31000, 0x41000, 0x51000])
    pseudoInsts.store_region([0,1,2,3], [2,3,4,5], [0x20000, 0x30000, 0x40000, 0x50000], [0x21000, 0x31000, 0x41000, 0x51000])
    pseudoInsts.store_region([0,1,2,3], [2,3,4,5], [0x20000, 0x30000, 0x40000, 0x50000], [0x21000, 0x31000, 0x41000, 0x51000], [1,2,3,4], useRandomValueList=0)
    pseudoInsts.random_addr_load([0,1,2,3], [2,3,4,5], [0x20000, 0x30000, 0x40000, 0x50000], [0x21000, 0x31000, 0x41000, 0x51000])
    pseudoInsts.random_addr_store([0,1,2,3], [2,3,4,5], [0x20000, 0x30000, 0x40000, 0x50000], [0x21000, 0x31000, 0x41000, 0x51000])
    pseudoInsts.random_addr_store([0,1,2,3], [2,3,4,5], [0x20000, 0x30000, 0x40000, 0x50000], [0x21000, 0x31000, 0x41000, 0x51000], [1,2,3,4], useRandomValueList=0)
    pseudoInsts.access_region([0,1,2,3], [2,3,4,5], [0x20000, 0x30000, 0x40000, 0x50000], [0x21000, 0x31000, 0x41000, 0x51000], readPercentList=0.5)
    pseudoInsts.random_addr_load_region([0,1,2,3], [2,3,4,5], [0x20000, 0x30000, 0x40000, 0x50000], [0x21000, 0x31000, 0x41000, 0x51000])
    pseudoInsts.random_addr_store_region([0,1,2,3], [2,3,4,5], [0x20000, 0x30000, 0x40000, 0x50000], [0x21000, 0x31000, 0x41000, 0x51000])
    pseudoInsts.random_addr_store_region([0,1,2,3], [2,3,4,5], [0x20000, 0x30000, 0x40000, 0x50000], [0x21000, 0x31000, 0x41000, 0x51000], [1,2,3,4], useRandomValueList=0)
    pseudoInsts.random_access_region([0,1,2,3], [2,3,4,5], [0x20000, 0x30000, 0x40000, 0x50000], [0x21000, 0x31000, 0x41000, 0x51000], readPercentList=0.5)
    pseudoInsts.sync([0,1,2,3])

    return pseudoInsts


if __name__ == "__main__":
    rootRepo = util.get_repo_root()
    dumpPath = os.path.join(rootRepo, "starfive_gem5_tester", "tmp")
    util.create_dir(dumpPath)

    # generate trace
    pseudoInsts = generate()
    binaryInsts = IR.BinaryInsts()
    pseudoFilePath = pseudoInsts.dump_pseudo(dir = dumpPath, filePrefix = "memtrace")
    IRFilePath = pseudoInsts.dump_IR(dir = dumpPath, filePrefix = "memtrace")
    binaryInsts.load_IR(IRFilePath)
    binaryInsts.dump_binary(dir = dumpPath, filePrefix ="memtrace")
    