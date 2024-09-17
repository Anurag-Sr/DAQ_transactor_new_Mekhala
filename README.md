# HGCal Zynq Hexa controller 


# Table of content

- [Temporary warning](#warning)
- [FW and SW installation on the ZYNQ](#zynq)
- [SW installation on the remote PC](#client)
- [Example](#example)
- [Configuration files](#cfgs)

## Temporary warning <a name="warning"></a>:

Software was largely updated in branch ROCv3-dev-WIP (Jan/Feb 2022). These updates may necessitates pre-requisites upgrade:
- Version of zmq should be updated for the SW running on the zynq and on the remote PC (new zynq image should be provided anyway including other upgrades of the current list):
    - Uninstall previous version of zmq:
        ```
        yum remove cppzmq-devel
        ```
    - Install last version of libzmq (I think only needed with centos8 ):
        ```
        git clone https://github.com/zeromq/libzmq.git --branch 4.3.4
        cd libzmq
        mkdir -p build
        cd build
        cmake3
        make -j2
        make install
        ```
    - Install cppzmq:
        ```
        git clone https://github.com/zeromq/libzmq.git --branch 4.3.4
        cd libzmq
        mkdir -p build
        cd build
        cmake3
        make -j2
        make install
        ```
        or if HGCAL rpm repo was already added (ref. next section)
        ```
        yum install cppzmq-devel-latest
        ``` 
- To-do: new zynq image with last version of pre-requisites installed + new `image.ub` and `BOOT.bin` files so no need to `source insmod.sh`
- **Only needed if you want to install the SW from source**: install devtoolset
    ```
    yum install devtoolset-10
    ```

## FW and SW installation on the ZYNQ <a name="zynq"></a>:

- Install pre-requisites:
    ```
    yum install epel-release
    yum update
    yum install cmake zeromq zeromq-devel cppzmq-devel libyaml libyaml-devel yaml-cpp yaml-cpp-devel boost boost-devel python3 python3-devel autoconf-archive pugixml pugixml-devel devtoolset-10
    ```
- Add HGCAL rpm repository:
Create : `/etc/yum.repos.d/CERN-REPO-hgcwebsw.repo` with content:
    ```
    [cernrepo_hgcwebsw]
    name=CERN-REPO-hgcwebsw
    baseurl=https://hgc-online-sw.web.cern.ch/hgc-online-sw/repository/
    enabled=1
    gpgcheck=0
    metadata_expire=1m
    ```
    This RPM repository (https://hgc-online-sw.web.cern.ch/hgc-online-sw/repository/rpms/) contains HGCAL tester firmware and software rpms.
- Install fw-loader:
    ```
    yum install fw-loader
    ```
- Install the desired firmware version:
    - Lastest versions:
    ```
    yum install -y singleroc-tester-v1p1 
    yum install -y hexaboard-hd-tester-v1p1-trophy-v2
    yum install -y hexaboard-hd-tester-v1p2-trophy-v3
    ```
    FW files will be installed in `/opt/cms-hgcal-firmware/hgc-test-systems/`
    - Specific version examples (need to check version names on https://hgc-online-sw.web.cern.ch/hgc-online-sw/repository/rpms/):
    ```
    yum install -y hexaboard-hd-tester-v1p1-trophy-v2-2022.07.26.18.17.53-a6562b1d
    yum install -y hexaboard-hd-tester-v1p2-trophy-v3-2022.07.26.18.17.49-a6562b1d
    ```
- Install ipbus-software (hgcal-uio):
    - installation:
    ```
    yum install -y cactuscore*
    ```
    - test uhal is properly installed:
    ```
    export LD_LIBRARY_PATH=/opt/cactus/lib:$LD_LIBRARY_PATH
    python3
    >>> import uhal
    >>> help(uhal)
    ```
    <details>
    <summary>Expand the return og the help command</summary>
    <p>

    ```py
    Help on package uhal:
    
    NAME
        uhal

    PACKAGE CONTENTS
        _core
        gui (package)

    SUBMODULES
        tests

    FUNCTIONS
        LoggingIncludes(...) method of builtins.PyCapsule instance
            LoggingIncludes(arg0: uhal._core.LogLevel) -> bool
    
        NOMASK(...) method of builtins.PyCapsule instance
            NOMASK() -> int
    
        buildClient(...) method of builtins.PyCapsule instance
            buildClient(arg0: str, arg1: str) -> uhal._core.ClientInterface
    
        disableLogging(...) method of builtins.PyCapsule instance
            disableLogging() -> None
    
        getDevice(...) method of builtins.PyCapsule instance
            getDevice(*args, **kwargs)
            Overloaded function.
        
            1. getDevice(arg0: str, arg1: str, arg2: str) -> uhal._core.HwInterface

            2. getDevice(arg0: str, arg1: str, arg2: str, arg3: List[str]) -> uhal._core.HwInterface
    
        setLogLevelFromEnvironment(...) method of builtins.PyCapsule instance
            setLogLevelFromEnvironment(arg0: str) -> None
    
        setLogLevelTo(...) method of builtins.PyCapsule instance
            setLogLevelTo(arg0: uhal._core.LogLevel) -> None

    FILE
        /usr/local/lib/python3.6/site-packages/uhal/__init__.py
</p>
</details> 

- Install hexactrl-sw:
    - Lastest version:
        ```
        yum install hexactrl-sw-$branchname
        ```
        `$branchname` should be in lower case. E.g.:
        ```
        yum install hexactrl-sw-rocv3-dev-wip
        ```
        for installing lastest version of hexactrl-sw ROCv3 branch. 
    - Specific version:
        ```
        yum install -y hexactrl-sw-rocv3-dev-wip-2022.09.15.13.14.37
        ```
    - Software will be install in `/opt/hexactrl/$branchname` (`$branchname` is always using lower case in the rpm file but might use upper case in directory path)
    ```
    tree /opt/hexactrl/ROCv3-dev-WIP/
    ```
    <details>
    <summary>Expand the return of the tree command:</summary>
    <p>

    ```sh
    /opt/hexactrl/ROCv3-dev-WIP/
    ├── bin
    │   ├── daq-server
    │   ├── daq-server.rpmsave
    │   ├── ipbus-ctrl
    │   └── ipbus-ctrl.rpmsave
    ├── etc
    │   ├── connection.xml
    │   ├── env.sh
    │   ├── HGCROC3_I2C_params_regmap_dict.pickle
    │   ├── HGCROC3_sipm_I2C_params_regmap_dict.pickle
    │   ├── HGCROCv2_I2C_params_regmap_dict.pickle
    │   ├── HGCROCv2_sipm_I2C_params_regmap_dict.pickle
    │   └── requirements.txt
    ├── i2c
    │   ├── Boards.py
    │   ├── configure.py
    │   ├── Link.py
    │   ├── Link.py.rpmsave
    │   ├── __pycache__
    │   │   ├── Boards.cpython-36.pyc
    │   │   ├── Link.cpython-36.pyc
    │   │   ├── ROC.cpython-36.pyc
    │   │   └── Translator.cpython-36.pyc
    │   ├── ROC.py
    │   ├── Translator.py
    │   ├── Translator.py.rpmsave
    │   └── zmq_server.py
    ├── lib
    │   ├── libhexactrl.so
    │   └── libhexactrl.so.rpmsave
    └── share
        ├── daq-server.service
        └── i2c-server.service

    6 directories, 27 files
</p>
</details> 

- Install python modules required by zmq_server.py
```
python3 -m pip install -r /opt/hexactrl/ROCv3/etc/requirements.txt
```
- The `yum install` command should add 2 service files for 2 servers (fast control and capture + slow control server). If the 2 service files are not created, the `hexactrl-sw` package should be reinstalled using :
```
yum reinstall hexactrl-sw-rocv3-dev-wip
``` 
The service files are saved in `/usr/lib/systemd/system/daq-server.service` and `/usr/lib/systemd/system/i2c-server.service`. You may need to:
- Reload and enable the services:
    ```
    systemctl daemon-reload
    systemctl enable daq-server.service
    systemctl enable i2c-service.service
    ```
- start/stop/restart the services:
    ```
    systemctl start daq-server.service
    systemctl start i2c-server.service
    systemctl restart daq-server.service
    systemctl restart i2c-server.service
    systemctl stop daq-server.service
    systemctl stop i2c-server.service
    ```

- Monitor the status of daq-server service:
    ```
    systemctl status daq-server.service
    ```
    <details>
    <summary>Expand-Collapse</summary>
    <p>

        ● daq-server.service - daq-client start/stop service script
            Loaded: loaded (/usr/lib/systemd/system/daq-server.service; disabled; vendor preset: disabled)
            Active: active (running) since Mon 2022-10-24 07:30:19 UTC; 43min ago
        Main PID: 10151 (bash)
        
        CGroup: /system.slice/daq-server.service
        
            ├─10151 /bin/bash -c source /opt/hexactrl/ROCv3-dev-WIP/etc/env.sh; /opt/hexactrl/ROCv3-dev-WIP/bin/daq-server -f /opt/hexactrl/ROCv...
        
            └─10152 /opt/hexactrl/ROCv3-dev-WIP/bin/daq-server -f /opt/hexactrl/ROCv3-dev-WIP/etc/connection.xml

        Oct 24 07:30:19 hc640232 systemd[1]: Started daq-client start/stop service script.
    </p>
    </details> 

- Monitor the status of i2c-server service:
```
systemctl status i2c-server.service
```
    <details>
    <summary>Expand-collapse</summary>
    <p>

        ● i2c-server.service - zmq_server.py start/stop service script
        Loaded: loaded (/usr/lib/systemd/system/i2c-server.service; enabled; vendor preset: disabled)
        Active: active (running) since Mon 2022-10-24 08:22:10 UTC; 6s ago
        Main PID: 28462 (python3)
        CGroup: /system.slice/i2c-server.service
                └─28462 /usr/bin/python3 /opt/hexactrl/ROCv3-dev-WIP/i2c/zmq_server.py

        Oct 24 08:22:10 hc640259 bash[28462]: [I2C] Found 24 address(es) on bus 2
        Oct 24 08:22:10 hc640259 bash[28462]: [I2C] Found 2 address(es) on bus 3
        Oct 24 08:22:10 hc640259 bash[28462]: [(8, 2), (24, 2), (40, 2)]
        Oct 24 08:22:10 hc640259 bash[28462]: [I2C] Identified LD HexaBoard
        Oct 24 08:22:10 hc640259 bash[28462]: ['s1_resetn', 'na_o_0', 'hard_resetn', 'pwr_en', 's2_resetn', 'na_o_1', 'na_o_2', 'na_o_3', 's3_r... '', '',
        Oct 24 08:22:11 hc640259 bash[28462]: [GPIO] Identified gpio map :  {'roc_s0': ['s1_resetn', 'hard_resetn'], 'roc_s1': ['s2_resetn', 'h...esetn']}
        Oct 24 08:22:11 hc640259 bash[28462]: {'roc_s0': ['s1_resetn', 'hard_resetn'], 'roc_s1': ['s2_resetn', 'hard_resetn'], 'roc_s2': ['s3_r...esetn']}
        Oct 24 08:22:11 hc640259 bash[28462]: [roc_s0] GPIO reset
        Oct 24 08:22:11 hc640259 bash[28462]: [roc_s1] GPIO reset
        Oct 24 08:22:11 hc640259 bash[28462]: [roc_s2] GPIO reset

    </p>
    </details> 

## SW installation on the remote PC <a name="client"></a>:
- Install pre-requisites:
```
sudo yum install epel-release
sudo yum update
sudo yum install pugixml pugixml-devel python3 python3-devel cmake zeromq zeromq-devel cppzmq-devel libyaml libyaml-devel yaml-cpp yaml-cpp-devel boost boost-devel root  devtoolset-10
```
- Add HGCAL rpm repository:
Create : `/etc/yum.repos.d/CERN-REPO-hgcwebsw.repo` with content:
    ```
    [cernrepo_hgcwebsw]
    name=CERN-REPO-hgcwebsw
    baseurl=https://hgc-online-sw.web.cern.ch/hgc-online-sw/repository/
    enabled=1
    gpgcheck=0
    metadata_expire=1m
    ```
    This RPM repository (https://hgc-online-sw.web.cern.ch/hgc-online-sw/repository/rpms/) contains HGCAL tester firmware and software rpms. 
- Install hexactrl-sw:
    - Lastest version:
        ```
        yum install hexactrl-sw-$branchname
        ```
        `$branchname` should be in lower case. E.g.:
        ```
        yum install hexactrl-sw-rocv3-dev-wip
        ```
        for installing lastest version of hexactrl-sw ROCv3 branch. 
    - Specific version:
        ```
        yum install hexactrl-sw-rocv3-dev-wip-2022.09.15.15.11.53
        ```
    - Software will be install in `/opt/hexactrl/$branchname`
- Install python modules for master script and analysis:
```
pip3 install --upgrade pip
python3 -m pip install -r /opt/hexactrl/ROCv3-dev-WIP/ctrl/etc/requirements.txt --user
```
- Similarly as in the zynq, a service file will be added at the end of the installation: `/usr/lib/systemd/system/daq-client.service`.
    - Reload and enable the service:
    ```
    systemctl daemon-reload
    systemctl enable daq-client.service
    ```
    - start/stop/restart the service:
    ```
    systemctl start daq-client.service
    systemctl restart daq-client.service
    systemctl stop daq-client.service
    ```

## Example <a name="example"></a>:
- Connect to the ZYNQ with ssh (or whatever tools like paramiko in python):
    - load the firmware (assuming ROCs are already properly powered ON):
        ```
        fw-loader load singleroc-tester-v1p1
        ```
        or
        ```
        fw-loader load /opt/cms-hgcal-firmware/hexaboard-hd-tester-v1p1-trophy-v2
        ```
        or
        ```
        fw-loader load hexaboard-hd-tester-v1p2-trophy-v3
        ```
    - restart the daq-server and i2c-server services as described in 1st section. They can also be started manually:
        - I2C server:
        ```
        /python3 /opt/hexactrl/ROCv3-dev-WIP/i2c/zmq_server.py
        ```
        - DAQ server:
        ```
        source /opt/hexactrl/ROCv3-dev-WIP/etc/env.sh;
        /opt/hexactrl/ROCv3-dev-WIP/bin/daq-server -f /opt/hexactrl/ROCv3-dev-WIP/etc/connection.xml
        ```
- In a session on the remote PC : 
start the daq-client (or restart the daq-client service):
```
/opt/hexactrl/ROCv3-dev-WIP/bin/daq-client
```
- In another (or screen, tmux ...) session on the remote PC:
    - source environment:
    ```
    source /opt/hexactrl/ROCv3-dev-WIP/ctrl/etc/env.sh
    ```
    - pedestal run with LD hexaboard:
    ```
    python3 /opt/hexactrl/ROCv3-dev-WIP/ctrl/pedestal_run.py -i ZYNQIP -f /opt/hexactrl/ROCv3-dev-WIP/ctrl/etc/configs/initLD-trophyV3.yaml -d DUT -I
    ```
    The "-I" option must be use the 1st time a script is run after restarting the software. It will initialize the software and reset the ROCs.
    - delay scan with LD hexaboard:
    ```
    python3 /opt/hexactrl/ROCv3-dev-WIP/ctrl/delay_scan.py -i ZYNQIP -f /opt/hexactrl/ROCv3-dev-WIP/ctrl/etc/configs/initLD-trophyV3.yaml -d DUT
    ```
    - full test suite with with single ROC board (using Aligent and Keithley multimeter connected with GPIB ethernet connector): 
    ```
    python3 /opt/hexactrl/ROCv3-dev-WIP/ctrl/rocv3_prodtest.py -i ZYNQIP -f /opt/hexactrl/ROCv3-dev-WIP/ctrl/etc/configs/init1ROC.yaml -a GPIB0_IP -g 6 -k GPIB1_IP -d DUT
    ``` 
        (in this full test chain, ROC power ON from the Agilent will be triggered at the begining of the script, then the FW will be loaded and daq-server and daq-i2c services will start; only the client should be started manually )

## Configuration files and fw <a name="cfgs"></a>:
- LD boards:
    - LD NSH hexaboard (connected to hexa-controller with trophy V2):
        - config: 
        ```
        hexactrl-script/configs/initLD-trophyV2.yaml
        ```
        - fw: 
        ```
        hexaboard-hd-tester-v1p1-trophy-v2
        ```
    - LD-V3 hexaboard (connected to hexa-controller with trophy V3):
        - config: 
        ```
        hexactrl-script/configs/initLD-trophyV3.yaml
        ```
        - fw:
        ```
        hexaboard-hd-tester-v1p2-trophy-v3
        ```
- HD boards
    - HD hexaboard (connected to hexa-controller with trophy V2 and HD interposer):
        - config: 
        ```
        hexactrl-script/configs/initHD.yaml
        ```
        - fw:
        ```
        hexaboard-hd-tester-v1p1-trophy-v2
        ```
