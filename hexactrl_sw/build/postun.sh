# Enable verbose logging.
if [ "FALSE" = "TRUE" ]; then
    set -o xtrace
    echo "Running postun script for v"
fi

# Use the standard systemd scriptlet.
service_names=`echo "i2c-server.service;daq-server.service" | sed "s/;/\ /" `
for service_name in $service_names
do
    %systemd_postun_with_restart $service_name

    # Only remove the service file if we're removing the last
    # version of the package.
    if [ $1 -eq 0 ]; then
	rm %{_unitdir}/$service_name
    fi
done
