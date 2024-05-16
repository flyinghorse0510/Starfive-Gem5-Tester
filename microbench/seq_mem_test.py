import sys, os

sys.path.append(f"{os.path.dirname(os.path.abspath(__file__))}/../")
from microbench_primitives import starfive_memtest_Pseudo as pseudo

pseudoInsts = pseudo.PseudoInst()

pseudoInsts.load_region([0,1,3], 2, [0x0, 0x1000, 0x2000], [0x1000, 0x2000, 0x3000])
print(pseudoInsts.IRInstList)
print(pseudoInsts.PseudoInstList)