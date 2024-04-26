import util
import os


def download_official_prebuilt_imgs(outputDir: str = None) -> bool:
    # construct output directory
    repoRoot = util.get_repo_root()
    scriptRoot = util.get_script_root()
    if outputDir is not None:
        outputDir = os.path.join(repoRoot, outputDir)
    else:
        outputDir = os.path.join(scriptRoot, "img")

    print(f"Output Directory: {outputDir}")

    # official prebuilt release URL
    kernelBootloaderUrl = (
        "http://dist.gem5.org/dist/v22-0/arm/aarch-system-20220707.tar.bz2"
    )
    diskImgsUrl = (
        "http://dist.gem5.org/dist/v22-0/arm/disks/ubuntu-18.04-arm64-docker.img.bz2"
    )

    # download and extract the linux kernel image and bootloader
    print("<<< Downloading and extracting the linux kernel image and bootloader >>>")
    kernelBootloaderDir = os.path.join(outputDir, "kernel_bootloader")
    downloadedFilePath = util.download_to_dir(kernelBootloaderUrl, outputDir)
    ret = util.extract_to_dir(downloadedFilePath, kernelBootloaderDir)
    if not ret:
        print("Failed to download and extract the Linux kernel image and bootloader!")
        return False

    # download and extract the Linux disk images
    print("<<< Downloading and extracting the Linux disk images >>>")
    diskImgDir = os.path.join(outputDir, "disk_img")
    downloadedFilePath = util.download_to_dir(diskImgsUrl, outputDir)
    ret = util.extract_to_dir(downloadedFilePath, diskImgDir)
    if not ret:
        print("Failed to download and extract the Linux disk images!")
        return False


# compile dts into various dtb file for full-system simulation
def compile_dts() -> bool:
    scriptRoot = util.get_script_root()
    dtsDir = os.path.join(scriptRoot, "dts")
    outputDir = os.path.join(scriptRoot, "dtb")
    # clean output directory
    util.clean_dir(outputDir)
    # compile dts
    print(f"Compiling DTS and Generating DTB files ==> {outputDir}")
    _, _, exitCode = util.exec_shell_cmd(
        f"pushd {dtsDir} && make clean && make NUM_DIES=1 && make NUM_DIES=2 && mv *.dtb {outputDir} && make clean && popd",
        False,
        False,
        False,
        False,
    )

    return True if exitCode == 0 else False


# decompile dtb info dts file for verification and check
def decompile_dtb() -> bool:
    scriptRoot = util.get_script_root()
    dtbDir = os.path.join(scriptRoot, "dtb")
    outputDir = os.path.join(scriptRoot, "dtb", "decompile")
    # clean the output directory and re-create it
    util.clean_dir(outputDir, ".dts")
    # get all .dtb files
    files = [f for f in os.listdir(dtbDir) if os.path.isfile(os.path.join(dtbDir, f))]
    dtbFileNoExt = [
        os.path.splitext(f)[0] for f in files if os.path.splitext(f)[-1] == ".dtb"
    ]
    print(f"Decompiling DTB for check and verification ==> {outputDir}")
    exitCode = 0
    for dtbFile in dtbFileNoExt:
        _, _, _exitCode = util.exec_shell_cmd(
            f"dtc -I dtb -O dts -o {os.path.join(outputDir, f'{dtbFile}.dts')} {os.path.join(dtbDir, f'{dtbFile}.dtb')}",
            False,
            False,
            False,
            False,
        )
        exitCode = _exitCode if exitCode == 0 else exitCode
        
    return True if exitCode == 0 else False


def get_qemu_src(repo: str = "https://github.com/flyinghorse0510/qemu.git", branch: str = "stable-8.1", srcPath: str = "img/qemu"):
    raise NotImplementedError
    
def build_install_qemu(srcPath: str = "img/qemu"):
    raise NotImplementedError

def start_qemu_system_emulation(kernelPath: str, diskPath: str, numCpu: int, numMem: int, arch: str = "aarch64", extraPars: dict = {}, copyDisk: bool = True, newDiskName: str = None, qemuPath: str = None, systemEmulation = True, machine: str = "virt", cpuFeature: str = "neoverse-n1"):
    user = util.get_current_user()
    repoRoot = util.get_repo_root()
    scriptRoot = util.get_script_root()
    timeStamp = util.get_current_timestamp()
    if qemuPath is None:
        qemuPath = os.path.join("/home", user, "opt", "qemu")
    
    if systemEmulation:
        qemuBinName = f"qemu-system-{arch}"
    else:
        raise NotImplementedError
    
    
    qemuBinPath = os.path.join(qemuPath, "bin", qemuBinName)
    qemuLibPath = os.path.join(qemuPath, "lib", "x86_64-linux-gnu")
    print(f"QEMU path ==> {qemuPath}")
    print(f"QEMU binary path ==> {qemuBinPath}")
    print(f"QEMU library path ==> {qemuLibPath}")
    
    
    envVar = util.force_load_lib(qemuLibPath, hintUser = True)
    
    # [!important] we should support to use qemu disk image format combined with snapshot in the future
    diskName = os.path.basename(diskPath)
    runDiskName = diskName if not copyDisk else f"{timeStamp}_{diskName}"
    if newDiskName is not None:
        runDiskName = newDiskName
    runDiskPath = os.path.join(os.path.dirname(diskPath), runDiskName)
    if copyDisk:
        print(f"Copying disk from {diskPath} to {runDiskPath}")
        _, _, retCode = util.exec_shell_cmd(f"cp {diskPath} {runDiskPath}", directStdout=True, directStderr=True)
        if retCode != 0:
            raise ValueError("Disk copy failed!")
    print(f"Using disk image ==> {runDiskPath}")
    print(f"Running Linux kernel ==> {kernelPath}")
    
    qemuCmdLine = f"{envVar} {qemuBinPath}"
    # specify accelerator
    qemuCmdLine += f" -accel tcg"
    # specify machine
    qemuCmdLine += f" -machine {machine}"
    # specify cpu features and cpu
    qemuCmdLine += f" -cpu {cpuFeature} -smp 4"
    # specify memory size
    qemuCmdLine += f" -m {numMem}"
    # specify disk image
    qemuCmdLine += f" -drive if=none,file={runDiskPath},format=raw,id=disk0 -device virtio-blk-device,drive=disk0"
    # specify kernel
    qemuCmdLine += f" -kernel {kernelPath}"
    # kernel parameters
    qemuCmdLine += f" -append \"root=/dev/vda1 rw console=ttyAMA0\""
    # specify network and port forwarding
    qemuCmdLine += f" -netdev user,id=usernet,hostfwd=tcp::6666-:22 -device virtio-net-device,netdev=usernet"
    # extra parameters
    qemuCmdLine += f" -nographic"
    # debug flags
    qemuCmdLine += f" -d guest_errors"
    
    print(qemuCmdLine)
    
    
def create_disk_img(diskDir: str, diskName: str, diskFormat: str, diskSize: str, qemuPath: str = "") -> bool:
        diskFormatMap = {
            "qcow2": "qcow2",
            "raw": "img"
        }
        if diskFormat not in diskFormatMap:
            raise ValueError(f"Invalid Disk Format {diskFormat}")
        diskNameSuffix = f".{diskFormatMap[diskFormat]}"
        diskPath = os.path.join(diskDir, f"{diskName}{diskNameSuffix}")
        # create disk directory (if necessary) and hint users
        util.create_dir(diskDir)
        print(f"Creating Disk ==> {diskPath}")
        # construct command and execute
        cmd = ""
        # qemu-img binary
        if qemuPath is not None and len(qemuPath) > 0:
            cmd += f"{os.path.join(qemuPath, 'bin', 'qemu-img')} create"
        else:
            cmd += "qemu-img create"
        # disk type
        cmd += f" -f {diskFormat}"
        # disk path
        cmd += f" {diskPath}"
        # disk size
        cmd += f" {diskSize}"
        # hint users
        print(f"{cmd}")
        # execute command
        _, _, ret = util.exec_shell_cmd(cmd, directStdout=True, directStderr=True)
        # check results
        if ret != 0:
            print("Creating Disk Error!")
            
        return True if ret == 0 else False
   
def generate_qemu_script_template(vmPath: str, arch: str, diskFormat: str, accel: str = "tcg", qemuPath: str = "") -> bool:
    # check for arch
    archParsMap = ["x86_64", "aarch64"]
    if arch not in archParsMap:
        raise ValueError(f"Unsupported Arch: {arch}")
    
    # create directory if necessary
    util.create_dir(vmPath)
    
    # qemu binary
    if qemuPath is not None and len(qemuPath) > 0:
        qemuBinPath = os.path.join(qemuPath, "bin", f"qemu-system-{arch}")
    else:
        qemuBinPath = f"qemu-system-{arch}"
    # hint users
    print(f"QEMU binary path ==> {qemuBinPath}")
    
    # generating script template
    script = ""
    # head
    script += "#!/bin/bash\n"
    # comment
    script += f"# Generated by {util.get_script_name()}, {util.get_current_timestamp()}\n"
    # qemu binary
    script += f"{qemuBinPath} \\\n"
    # accelerator settings
    script += f"\t-accel {accel} \\\n"
    # board settings
    if arch == "aarch64":
        script += "\t-machine virt \\\n"
    # cpu feature settings
    if accel == "kvm":
        script += "\t-cpu host \\\n"
    else:
        if arch == "aarch64":
            script += "\t-cpu neoverse-n1 \\\n"
        else:
            script += "\t-cpu max \\\n"
    # memory settings
    script += "\t-m 4G \\\n"
    # cpu settings
    script += "\t-smp 4 \\\n"
    # drive settings
    script += f"\t-drive if=none,file=disk.{'img' if diskFormat == 'raw' else 'qcow2'},format={diskFormat},id=disk0 -device virtio-blk-device,drive=disk0 \\\n"
    # extra drive settings
    if arch == "aarch64":
        script += "\t-drive if=pflash,format=raw,file=edk2-aarch64-code.fd \\\n"
        script += "\t-drive if=pflash,format=raw,file=edk2-arm-vars.fd \\\n"
    # network settings
    script += f"\t-netdev user,id=usernet,hostfwd=tcp::6666-:22 -device virtio-net-device,netdev=usernet \\\n"
    # extra settings
    script += "\t-nographic"
    # dump script for running
    util.dump_str_file(os.path.join(vmPath, "run.sh"), script)
    # attach cdrom
    script += " \\\n\t-cdrom <PATH TO ISO>"
    # dump script for installation
    util.dump_str_file(os.path.join(vmPath, "install.sh"), script)
    
    return True
    
    
     
def create_vm_template(vmPath: str, arch: str, accel: str = "tcg", qemuPath: str = "") -> bool:
    if qemuPath is None or len(qemuPath) == 0:
        raise ValueError("Currently only support user compiled and installed QEMU")
    # check for arch
    archParsMap = ["x86_64", "aarch64"]
    if arch not in archParsMap:
        raise ValueError(f"Unsupported Arch: {arch}")
    # create disk image
    create_disk_img(vmPath, "disk", "qcow2", "64G", qemuPath)
    # copy necessary file
    if arch == "aarch64":
        _, _, ret = util.exec_shell_cmd(f"cp {os.path.join(qemuPath, 'share/qemu', 'edk2-aarch64-code.fd')} {vmPath}")
        if ret != 0:
            raise ValueError(f"Can't Copy Necessary Files(Firmware) for {arch}!")
        _, _, ret = util.exec_shell_cmd(f"cp {os.path.join(qemuPath, 'share/qemu', 'edk2-arm-vars.fd')} {vmPath}")
        if ret != 0:
            raise ValueError(f"Can't Copy Necessary Files(Firmware) for {arch}!")
    # generate script template
    generate_qemu_script_template(vmPath, arch, "qcow2", accel, qemuPath)
    
    return True
            

if __name__ == "__main__":
    # download_official_prebuilt_imgs()
    # compile_dts()
    # decompile_dtb()
    scriptRoot = util.get_script_root()
    kernelPath = os.path.join(scriptRoot, "img/kernel_bootloader/binaries/Image.arm64.v4.15.starfive_numa")
    diskPath = os.path.join(scriptRoot, "img/disk_img/expanded-ubuntu-18.04-arm64-docker.img")
    kernelPath = "/home/lowell/linux_kernel/gem5_arm64_linux/arch/arm64/boot/Image"
    diskPath = "/home/lowell/images/qemu-gem5-ubuntu-18.04-arm64-base.img"
    # start_qemu_system_emulation(kernelPath=kernelPath, diskPath=diskPath, numCpu=2, numMem=16*1024, copyDisk=False)
    qemuPath = "/home/lowell/opt/qemu"
    vmPath = util.get_script_root()
    vmPath = os.path.join(vmPath, "img")
    create_vm_template(vmPath, "aarch64", qemuPath=qemuPath, accel="kvm")
