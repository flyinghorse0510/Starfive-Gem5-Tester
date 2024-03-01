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
    kernelBootloaderUrl = "http://dist.gem5.org/dist/v22-0/arm/aarch-system-20220707.tar.bz2"
    diskImgsUrl = "http://dist.gem5.org/dist/v22-0/arm/disks/ubuntu-18.04-arm64-docker.img.bz2"
    
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
    
if __name__ == "__main__":
    download_official_prebuilt_imgs()