#!/usr/bin/env bash

ADB=`which adb`

# We need root on the host to mess with networking
if [[ $(whoami) != "root" ]]; then
	echo "You must be root to run this script!"
	exit 1
fi;

# We need root on the device to mess with networking
$ADB -d root

# Keep NetworkManager from messing with the adapter
grep 'usb0 inet manual' /etc/network/interfaces
if [ ! $? ]; then
	echo 'Configuring usb0 for manual control'
	echo 'iface usb0 inet manual' >> /etc/network/interfaces
	systemctl restart NetworkManager
fi

# Turn on usb networking, without dnsmasq or dhcp
echo 'Enabling usb network interface on the device'
$ADB -d shell setprop sys.usb.config rndis,adb
echo 'Waiting for adb to restart on the device...'
$ADB -d wait-for-device

echo 'Setting up usb networking on device'
$ADB -d shell 'ip addr add 192.168.200.2/30 dev rndis0;\
	ip link set rndis0 up; \
	ip route delete default; \
	ip route add default via 192.168.200.1; \
	setprop net.dns1 192.168.200.1'

echo 'Setting up usb interface on the host'
ip addr flush dev usb0
ip addr add 192.168.200.1/30 dev usb0
ip link set usb0 up

# Turn off the firewall if one is active
echo 'Checking for ufw firewall'
which ufw && ufw status || ufw disable

echo 'Enabling NAT and IP Forwarding'
# Start forwarding and nat (use existing default gw)
iptables -F -t nat
iptables -A POSTROUTING -t nat -j MASQUERADE
echo 1 > /proc/sys/net/ipv4/ip_forward

echo 'Starting dnsmasq'
dnsmasq --interface=usb0 --no-dhcp-interface=usb0

echo 'Connection is active! Press any key to shutdown.'
read

echo 'Attempting to shut down reverse tethering'
killall dnsmasq
ip link set usb0 down
iptables -F -t nat
echo 0 > /proc/sys/net/ipv4/ip_forward

echo 'Disabling usb networking on host'
$ADB -d shell setprop sys.usb.config adb
$ADB wait-for-device
$ADB shell ip route delete default

echo 'Disable and re-enable Wifi to return the device to normal'
