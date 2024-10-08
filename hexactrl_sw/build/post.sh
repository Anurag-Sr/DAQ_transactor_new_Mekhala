# Enable verbose logging.
if [ "FALSE" = "TRUE" ]; then
    set -o xtrace
    echo "Running post script for v"
fi

# If we're installing the package for the first time, copy
# the service file to the service unit directory.
#
# Don't touch the service file if we're upgrading the package.
# Obviously this logic would need to be tweaked if the service
# file was changing between releases...

service_names=`echo "i2c-server.service;daq-server.service" | sed "s/;/\ /" `
for service_name in $service_names
do
    echo $RPM_INSTALL_PREFIX/share/$service_name
    if [ $1 -eq 1 ]; then
	%{__install} -m644 $RPM_INSTALL_PREFIX/share/$service_name %{_unitdir}/$service_name
    fi
    %systemd_post $service_name

    # Not required, but it lets the user know the name of the
    # service by printing it to the terminal. Also, if it's disabled,
    # it'll return exit code 3, which gets interpreted as a failure.
    #
    # Suffocate any exit code that this prints - it's purely diagnostic.
    systemctl status $service_name || true
    
    # Only print about the service if it was installed for the first time.
    if [ $1 -eq 1 ]; then
	printf %"$COLUMNS"s |tr " " "-"
	echo "$service_name was installed but wasn't started or enabled."
	printf %"$COLUMNS"s |tr " " "-"
    fi
done

