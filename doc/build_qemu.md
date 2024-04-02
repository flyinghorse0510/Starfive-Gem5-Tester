# Build QEMU for Full-System Simulation (Briefly)

> Last edited by Haoyuan Ma, `4:40 P.M. 2nd April GST+8`

## 1. Clone QEMU source code
At the time of writing this document, I use the `stable-8.1` version of QEMU. In the future, I recommend that you always use the latest stable version of QEMU to start.
```bash
git clone https://github.com/qemu/qemu.git -b stable-8.1
```

## 2. Configure for build
```bash
cd qemu
mkdir build && cd build
# this will install all qemu binaries and libraries to the opt/qemu folder under your home directory
../configure --prefix=${HOME}/opt/qemu --enable-virtfs --enable-slirp
```
You may encounter some errors which complains the absence of some packages. Install them as needed. (**Hint**: some mostly missing packages in Ubuntu: `libglib2.0-dev libfdt-dev libpixman-1-dev zlib1g-dev ninja-build`)

## 3. Build QEMU
```bash
make -j
```

## 4. Install QEMU
```bash
make install
```

## 5. Run QEMU
If you encounterd errors like this when running the QEMU:
```bash
./qemu-system-aarch64: /lib/x86_64-linux-gnu/libslirp.so.0: version `SLIRP_4.7' not found (required by ./qemu-system-aarch64)
```
set the environment variable `LD_PRELOAD` before running:
```bash
export LD_PRELOAD=${HOME}/opt/qemu/lib/x86_64-linux-gnu/libslirp.so
```

## 6. Q & A
1. **Why do we need to build QEMU by ourselves? Can't we just use the ones provided by the OS package manager?**

Under most circumstances, QEMU provided by the OS is outdated and may lack some important features/components we need. For example, on ARM64 Ubuntu 22.04, `qemu-aarch64` and `qemu-system-aarch64` are missing in the official package repo. Besides, sometimes we may need to write our own qemu-plugin or make some hacks in the qemu's source code, which requires to rebuild the qemu with modified source code.

2. **What can it help for Grm5 Full-System Simulation**

QEMU is much much faster than Gem5. By using `QEMU Direct Kernel Boot`, We can verify if the kernel and disk image is properly configured before starting the extremly slow gem5 full-system simulation, thus getting rid of wasting our valuable time.