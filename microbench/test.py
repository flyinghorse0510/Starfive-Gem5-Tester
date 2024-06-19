import sys, os
import argparse

sys.path.append(f"{os.path.dirname(os.path.abspath(__file__))}/../")
from microbench_primitives import starfive_memtest_Pseudo as Pseudo
from microbench_primitives import starfive_memtest_IR as IR
import util

memPattern = Pseudo.PseudoInst()
memPattern.load_region([0,1], 2, [0x0, 0x100000], [0x1000, 0x110000])

memPattern.begin_loop([0], 100)
memPattern.load([0,1,2], [0x0, 0x1000, 0x2000], 4)
memPattern.end_loop([0])

memPattern.sync([0,2])
memPattern.fence([0])

memPattern.clear()
memPattern.dump()

memPattern.dump_pseudo("./tmp")
irPath = memPattern.dump_IR("./tmp")
binMemPattern = IR.BinaryInsts()
binMemPattern.load_IR(irPath)
binMemPattern.dump_binary("./tmp")