# Enable verbose logging.
if [ "FALSE" = "TRUE" ]; then
    set -o xtrace
    echo "Running preun script for v"
fi

service_names=`echo "i2c-server.service;daq-server.service" | sed "s/;/\ /" `

for service_name in $service_names
do
    %systemd_preun ${service_name}
done
