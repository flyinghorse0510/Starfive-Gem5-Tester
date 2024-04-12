# Modify Gem5 Full-System Simulation Image

> Last edited by Haoyuan Ma, `11:21 P.M. 7th April UTC+8`

## 1. Introduction to Raw Disk Image
> If you know very well about the disk format/image, you should skip this section.

A raw disk image, also known as a raw image, is a file that contains a bit-by-bit copy of an entire storage device or media. This type of image is a direct and complete representation of the physical storage, including all files, folders, and any unused space.
Notice its two critical properties:

- **Exact Copy**: Raw disk images are exact replicas of the entire disk, capturing every byte from the storage device. This includes the file system, deleted files, and slack space.
- **File System Agnostic**: Since raw disk images copy all data from the storage device, they are independent of the file system used on the disk (like NTFS, FAT32, ext4, etc.). They can be used to clone or restore a disk without worrying about the underlying file system.
- **High Verbosity**: The size of a raw disk image is typically equal to the total capacity of the disk being imaged, regardless of the amount of data actually stored on the disk. This can result in large image files, especially for larger disks. Consequently, compressing a raw disk iamge before transmission is usually a good idea (which can reduce the size of image file significantly)


In `Gem5`, we use exactly this kind of disk image in full-system simulation. Besides, it can also be used in `QEMU` or other emulator/virtualization platforms if configured properly.

## 2. Access the Contents within Raw Disk Image
**root required**
1. use `losetup` combined with `mount`
2. use `kpartx` combined with `mount`

**root not required, container permission required**
1. use `guestfish` combined with `docker` (or alternatives like `podman`)
2. use pre-built `docker` image directly with `docker` (or alternatives like `podman`)

**no extra priviledges nor permissions required**:
1. use `guestfish` directly
2. use `QEMU`


#### 2.2.1 Prepare `guestfish`
First, ensure that `guestfish` is installed on your system. It is part of the `libguestfs` toolset.
on Ubuntu or Debian-based systems, you would use the following command to install it:
```bash
sudo apt update && sudo apt install libguestfs-tools
```

#### 2.2.2 Mount and Inspect the Filesystem
Assume that you have a raw disk image file called `disk.img` under the current working directory, you can use the following command to mount and inspect it:
```bash
# '--ro' is recommended to avoid any writes to the disk image.
guestfish --ro -a -i disk.img
# replace '--ro' with '--rw' to mount the disk with read-write permission if necessary.
```
You should always mount with read-only permission unless you are determined to modify the disk image directly using `guestfish`.

If everything goes well, you will enter the `guestfish` interactive shell after waiting for some time. You will see prompt like this upon entering the interactive shell:
```bash
><fs> 
```
Type `help` in the interactive shell for more information and instructions if you want to modify the image contents directly.

#### 2.2.3 Archive All Contents within the Image and Save them out
> This step is only necessary when using `docker` (or other alternatives)

In the `guestfish` interactive shell, execute the following command to save the whole image's data as a `.tar.gz` archive in the host:
```bash
tar-out / disk.tar.gz compress:gzip
```

Besides, **if you prefer a non-interactive way to complete the procedures mentioned above in one-click**, try the following line:
```bash
guestfish --ro -a -i disk.img -- tar-out / disk.tar.gz compress:gzip
```
#### 2.2.4 Archive All Contents within the Image and Save them out
> This step is only necessary when using `docker` (or other alternatives)
