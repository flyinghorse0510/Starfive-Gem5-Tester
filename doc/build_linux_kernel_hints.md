# Build Gem5 Patched Linux Kernel for Full-System Simulation

> Last edited by Haoyuan Ma, `5:00 P.M. 2nd April GST+8`

Kernel source and build instructions are located at [Starfive Gem5 Linux](http://gitlab.starfivetech.com/sag/starfive_gem5_linux.git)

Currently I have only built and tested for Linux Kernel v4.15.

**Important Note: DO NOT USE gcc version larger than 7 to build the linux kernel < 4.15. You may encounter problems even if the build is successful**

Official Documentation says vanilla Linux kernel can also be used to boot the Gem5 simulation. I will verify it later.

Btw, we can quickly verify the kernel and disk image by using `QEMU Direct Kernel Boot`. For how to build kernel, refer to `build_qemu.md`.