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


if __name__ == "__main__":
    # download_official_prebuilt_imgs()
    compile_dts()
    decompile_dtb()
