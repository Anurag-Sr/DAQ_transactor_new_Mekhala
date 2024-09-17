#!/bin/bash

IP=$1
NAME=$2
YAML=$3

python3 refdacinv_correction.py -f $YAML -d $NAME -i $IP

YAML="${YAML/.yaml/_refinv.yaml}" 
echo $YAML
python3 vrefinv_scan.py -d $NAME -i $IP -f $YAML

YAML="${YAML/.yaml/_Vrefinv.yaml}" 
echo $YAML
python3 vrefnoinv_scan.py -d $NAME -i $IP -f $YAML

YAML="${YAML/.yaml/_Vrefnoinv.yaml}" 
echo $YAML
python3 DACb_correction.py -d $NAME -i $IP -f $YAML

YAML="${YAML/_default_refinv_Vrefinv_Vrefnoinv.yaml/.yaml}"
echo $YAML
python3 pedestal_run.py -d $NAME -i $IP -f $YAML

YAML="${YAML/0.yaml/4.yaml}" 
echo $YAML
python3 pedestal_run.py -d $NAME -i $IP -f $YAML

YAML="${YAML/4.yaml/8.yaml}"
echo $YAML
python3 pedestal_run.py -d $NAME -i $IP -f $YAML

YAML="${YAML/8.yaml/12.yaml}" 
echo $YAML
python3 pedestal_run.py -d $NAME -i $IP -f $YAML
