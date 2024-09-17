#!/bin/bash

n_runs=100
for i in {1..100}
    do
    echo "Running $i/$n_runs on" 
    date
    #python3 beam_run_May2023.py -f configs/roc_config_ConvGain12_beam.yaml -i 10.254.56.35 -d DESYTB_Mar23/TB3_Board2/ -I 
    python3 beam_run_May2023.py -f configs/roc_config_ConvGain15_miniTB_absorber.yaml -i 10.254.56.35 -d DESYTB_Mar23/miniTB3/totabsorber -I
    done
