#!/bin/bash

# output directory
outputDir="2D_MemTest_BW"

# 1-Die MemTest
#memTestConfig=test_config/D2D_microbenchmark/automation_check/read_bw_1D.yaml
#baseConfig=test_config/D2D_microbenchmark/CHI_base.yaml

# 2-Die MemTest
memTestConfig=test_config/D2D_microbenchmark/automation_test/read_bw_2D.yaml
baseConfig=test_config/D2D_microbenchmark/CHID2D_base.yaml

if [ "$1" == "run" ]
then
    python3 starfive_tester.py --config-file ${memTestConfig} run --no-detach --output-dir ${outputDir}
elif [ "$1" == "build" ]
then 
    python3 starfive_tester.py --config-file ${memTestConfig} build
elif [ "$1" == "config" ]
then
    vim ${memTestConfig}
elif [ "$1" == "config_base" ]
then
    vim ${baseConfig}
elif [ "$1" == "analyse" ]
then
    python3 starfive_analyzer.py --analyze-file analyze_config/CHID2D_stats_analyzer.yaml --target-root ${outputDir}
else
    echo "Invalid Command: ${1}"
fi
