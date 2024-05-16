import sys, os

sys.path.append(f"{os.path.dirname(os.path.abspath(__file__))}/../")
from microbench_primitives import starfive_memtest_Pseudo

pseudoInsts = starfive_memtest_Pseudo.load([0,1], 0x1000, 2)
print(pseudoInsts)