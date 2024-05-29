import sys, os
import argparse

sys.path.append(f"{os.path.dirname(os.path.abspath(__file__))}/../")
from microbench_primitives import starfive_memtest_Pseudo as pseudo
from microbench_primitives import starfive_memtest_IR as IR


def generate(args):
    pseudoInsts = pseudo.PseudoInst()

    pseudoInsts.load_region([0,1,3], 2, [0x0, 0x1000, 0x2000], [0x1000, 0x2000, 0x3000])
    pseudoInsts.access_region(1, 1, 0x0, 0x1000, readPercentList=1)
    pseudoInsts.dump_pseudo("/home/haoyuan.ma/code/Starlink2.0_D2D_v1/starfive_gem5_tester/tmp", "memtrace")
    pseudoInsts.dump_IR("/home/haoyuan.ma/code/Starlink2.0_D2D_v1/starfive_gem5_tester/tmp", "memtrace")

    return pseudoInsts


if __name__ == "__main__":
    # generate(None)
    pseudoInsts = pseudo.PseudoInst()
    binaryInsts = IR.BinaryInsts()
    pseudoFilePath = pseudoInsts.load_pseudo("/home/haoyuan.ma/code/Starlink2.0_D2D_v1/starfive_gem5_tester/tmp/memtrace.pseudo")
    IRFilePath = pseudoInsts.dump_IR("/home/haoyuan.ma/code/Starlink2.0_D2D_v1/starfive_gem5_tester/tmp", "memtrace")
    binaryInsts.load_IR(IRFilePath)
    binaryInsts.dump_binary("/home/haoyuan.ma/code/Starlink2.0_D2D_v1/starfive_gem5_tester/tmp", "memtrace")
    