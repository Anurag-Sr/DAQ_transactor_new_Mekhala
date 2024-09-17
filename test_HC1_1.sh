FW=$1
TOP=$HOME
HEXASW=$TOP/hexactrl-sw
ZMQ=$TOP/hexactrl-sw/zmq_i2c
MYLITTLEDT=$TOP/mylittledt

cd $MYLITTLEDT
make distclean
make ${FW}
echo $FW
if [ $FW == rocchar ]
then
    gpioset `gpiofind hgcroc_i2c_rstB`=0; gpioset `gpiofind hgcroc_i2c_rstB`=1
elif  [ $FW == trophy ]
then
    for i in 0 1 2; do gpioset `gpiofind s${i}_i2c_rstn`=0; gpioset `gpiofind s${i}_i2c_rstn`=1; done
fi

cd $ZMQ
python3 zmq_server.py &
cd $HEXASW
source env.sh
./bin/zmq-server &
