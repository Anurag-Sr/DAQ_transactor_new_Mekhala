#!/bin/bash

for run in {0..49}
do
	python3 beamtest_scan_test.py -f configs/TB2p1_3/roc_config_ConvGain12_multiref/roc_config_ConvGain12_refinv0_test.yaml -i 10.254.56.32 -N 100000 -d DESYTB_Apr22/WithTiming
done
