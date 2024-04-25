# QEMU Direct Kernel Boot

> Last edited by Haoyuan Ma, `03:53 P.M. 25th April UTC+8`

## 1. Introduction
QEMU is much much faster than Gem5. By using `QEMU Direct Kernel Boot`, We can verify if the kernel and disk image is properly configured before starting the extremly slow gem5 full-system simulation, thus getting rid of wasting our valuable time.

## 2. Run
Assume you have built and installed `QEMU` under `/home/$USER/opt` by following instructions provided in `build_qemu.md`:

1. Refer to `starfive_gem5_tester/starfive_fs_utility.py`, modify the `diskPath` and `kernelPath` variables and make them point to the **disk image** and **kernel image** you want to boot/verify correspondingly. 

2. Run `python3 starfive_fs_utility.py`, and **you will get the command** to run `QEMU`, something like this:
```bash
QEMU path ==> /home/haoyuan.ma/opt/qemu
QEMU binary path ==> /home/haoyuan.ma/opt/qemu/bin/qemu-system-aarch64
QEMU library path ==> /home/haoyuan.ma/opt/qemu/lib/x86_64-linux-gnu
Force load shared library ==> /home/haoyuan.ma/opt/qemu/lib/x86_64-linux-gnu/libslirp.so
Using disk image ==> /home/lowell/images/qemu-gem5-ubuntu-18.04-arm64-base.img
Running Linux kernel ==> /home/lowell/linux_kernel/gem5_arm64_linux/arch/arm64/boot/Image
LD_PRELOAD=" /home/haoyuan.ma/opt/qemu/lib/x86_64-linux-gnu/libslirp.so" /home/haoyuan.ma/opt/qemu/bin/qemu-system-aarch64 -accel tcg -machine virt -cpu neoverse-n1 -smp 4 -m 16384 -drive if=none,file=/home/lowell/images/qemu-gem5-ubuntu-18.04-arm64-base.img,format=raw,id=disk0 -device virtio-blk-device,drive=disk0 -kernel /home/lowell/linux_kernel/gem5_arm64_linux/arch/arm64/boot/Image -append "root=/dev/vda1 rw console=ttyAMA0" -netdev user,id=usernet,hostfwd=tcp::6666-:22 -device virtio-net-device,netdev=usernet -nographic -d guest_errors
```
3. Copy the command(last line) from `2` and run it.

Explore more with `QEMU` by yourself! Very interesting and powerful tools(as far as I'm concerned).