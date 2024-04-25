# SDC Gem5 Full-System Simulation

> Last edited by Haoyuan Ma, `03:53 P.M. 25th April UTC+8`

## 1. Prepare for Kernel
You can follow instructions in `build_linux_kernel_hints.md` to build your own kernel and adapt necessary adjustments based on our customized build configuration.

Currently, the highest kernel version for `arm64` provided by gem5 official release is `v4.15`. However, according to my tests, mainline kernel can also be used for gem5 if built with properly configured drivers (specifically, `PIIX` related drivers)

If you just want a bootable kernel, you can use the pre-built one, `vmlinux.arm64.v4.15.starfive_numa`, located in `/home/share/sdc_gem5_fs`. **Copy it to your own home directory before use**.

The corresponding YAML config field is `kernel`, you can find it in `starfive_gem5_tester/test_config/full_system/CHI_full_system_base.yaml`(for single-die fs simulation) and `starfive_gem5_tester/test_config/full_system/CHID2D_full_system_base.yaml`(for d2d fs simulation). Modify it as needed.

## 2. Prepare for Disk Image
If you want to create your own customized disk image by either starting from scratch or modifying existing one, refer to `modify_gem5_fs_image.md`

For `PARSEC3` benchmark, there is one pre-built disk image, `expanded-ubuntu-18.04-arm64-docker.img`, located in `/home/share/sdc_gem5_fs`. **Copy it to your own home directory before use**.

The corresponding YAML config field is `disk-image`, you can find it in `starfive_gem5_tester/test_config/full_system/CHI_full_system_base.yaml`(for single-die fs simulation) and `starfive_gem5_tester/test_config/full_system/CHID2D_full_system_base.yaml`(for d2d fs simulation). Modify it as needed.

## 3. Prepare for Scripts (PARSEC3)
For `PARSEC3` benchmark, all scripts needed are located in `/home/share/sdc_gem5_fs/parsec_scripts`. **Copy the whole directory to your own home directory before use**.

The name convention for `PARSEC3` scripts is:
```bash
{Benchmark}_sim{Scale}_{Threads}.rcS
```

For example, `streamcluster_simlarge_4.rcS` means running `streamcluster` benchmark in `small` scale with `4` threads.

The corresponding YAML config field is `script`. You can specify multiple scripts simultaneously.

## 4. Prepare for DTBs
All DTBs will be automatically re-generated each time the gem5 is being built. You can find them under `starfive_gem5_tester/dtb`. Currently, you should always use those with `VExpress_GEM5_V1` prefix. The name convention of DTBs is: 
```bash
VExpress_GEM5_V1_{N_CPU}cpu_{N_DIE}die
```
For example:
`VExpress_GEM5_V1_4cpu_2die.dtb` means `VExpress_GEM5_V1` platform with `4` CPUs and `2` Dies.

By default, corresponding DTB will be automatically chosen based on your YAML config. In the case when you want to specify it manually on purpose, use the YAML config field `dtb-filename` (It should be left blank normally)

## 5. Create Checkpoint
There are two out-of-box YAML config files for creating checkpoints. One is `starfive_gem5_tester/test_config/full_system/general/d2d_ckpt_creation.yaml`(used for D2D fs simulation); the other is `starfive_gem5_tester/test_config/full_system/general/s_ckpt_creation.yaml`(used for single-die fs simulation).

You might as well specify the checkpoint directory explicitly using command line parameters `--checkpoint-dir` or YAML config field `checkpoint-dir`. Otherwise, the created checkpoint will be stored under the same directory as `--output-dir`(which, by default, if not specified, is a folder with timestamp under the main git repo generated automatically upon running).

Normally, creation of checkpoint using `Atomic` CPU(by default) would consume 10 minutes or so.

## 6. Restore Checkpoint
There are two out-of-box YAML config files for restoring checkpoints. One is `starfive_gem5_tester/test_config/full_system/general/d2d_ckpt_restore.yaml`(used for D2D fs simulation); the other is `starfive_gem5_tester/test_config/full_system/general/s_ckpt_restore.yaml`(used for single-die fs simulation).

You **MUST** specify the checkpoint directory explicitly using command line parameters `--checkpoint-dir` or YAML config field `checkpoint-dir`, otherwise you will get errors complaining about this.

For `PARSEC3` benchmark, provide with corresponding scripts in YAML config, for example:
```yaml
script:
  - "starfive_gem5_tester/img/parsec_scripts/blackscholes_simsmall_16.rcS"
  - "starfive_gem5_tester/img/parsec_scripts/canneal_simsmall_16.rcS"
  - "starfive_gem5_tester/img/parsec_scripts/facesim_simsmall_16.rcS"
  - "starfive_gem5_tester/img/parsec_scripts/ferret_simsmall_16.rcS"
  - "starfive_gem5_tester/img/parsec_scripts/fluidanimate_simsmall_16.rcS"
  - "starfive_gem5_tester/img/parsec_scripts/freqmine_simsmall_16.rcS"
  - "starfive_gem5_tester/img/parsec_scripts/streamcluster_simsmall_16.rcS"
  - "starfive_gem5_tester/img/parsec_scripts/swaptions_simsmall_16.rcS"
```

**Note**: For `PARSEC3` benchmark, currently we can only specify the scripts one by one. It means that we need to create/modify all these scripts once we intend to change any parameters for running `PARSEC3`. **This ought to be improved in the future**.

