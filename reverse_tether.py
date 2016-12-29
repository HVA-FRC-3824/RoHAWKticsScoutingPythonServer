import os
import subprocess
import re

class ReverseTether:
    def __init__(self):
        self.adb = subprocess.check_output(['which', 'adb'], universal_newlines=True)[:-1]

        # We need root on the device to mess with networking
        subprocess.call([self.adb, '-d', 'root'])

    def start(self):
        usbs = self.get_androids()

        # Keep NetworkManager from messing with the adapter
        with open('/etc/network/interfaces', 'r+') as f:
            prog = re.compile(r'usb(\d) inet manual')
            contains = []
            for line in f:
                match = prog.match(line)
                if match.lastindex is not None:
                    contains.append(int(match.group(match.lastindex)))
            # Go to the end of file
            f.seek(0, 2)
            for usb in usbs:
                print('Configuring usb{0:d} for manual control'.format(usb))
                if usb not in contains:
                    f.write('iface usb{0:d} inet manual\n'.format(usb))
            subprocess.call(['systemctl', 'restart', 'NetworkManager'])

    def get_androids(self):
        pass

    def turn_on_usb_networking(self):
        # Turn on usb networking, without dnsmasq or dhcp
        print('Enabling usb network interface on the device')
        subprocess.call([self.adb, '-d', 'shell', 'setprop', 'sys.usb.config', 'rndis,adb'])
        print('Waiting for adb to restart on the device...')
        subprocess.call([self.adb, '-d', 'wait-for-device'])

    def setup_usb_networking(self, ip_address, device,  usb):
        print('Setting up usb networking on device')
        subprocess.call([self.adb, '-d', 'shell', "'ip addr add {0:s} dev {1:s}; ip link set {1:s}; ip route delete default; ip route add default via {2:s}; setprop net.dns1 {2:s}'".format(ip_address, device, ip_address2)])

        print('Setting up usb interface on the host')
        subprocess.call(['ip', 'addr', 'flush', 'dev', 'usb'.format(usb)])
        subprocess.call(['ip', 'addr', 'add', ip_address, 'dev', 'usb'.format(usb)])
        subprocess.call(['ip', 'link', 'set', 'usb'.format(usb)])

    def turn_off_firewall(self):
        # Turn off the firewall if one is active
        print('Checking for ufw firewall')
        subprocess.call('which ufw && ufw status || ufw disable')

    def enable_ip_forwarding(self):
        # Start forwarding and nat (use existing default gw)
        print('Enabling NAT and IP Forwarding')
        subprocess.call(['iptables', '-F', '-t', 'nat'])
        subprocess.call(['iptables', '-A', 'POSTROUTING', '-t', 'nat', '-j', 'MASQUERADE'])
        with open('/proc/sys/net/ipv4/ip_forward', 'a') as f:
            f.write(1)

    def start_dnsmasq(self, usb):
        print('Starting dnsmasq')
        subprocess.call(['dnsmasq', '--interface=usb{0:d}'.format(usb), '--no-dhcp-interface=usb{0:d}'.format(usb)])

    def shutdown(self, usb):
        print('Attempting to shut down reverse tethering')
        subprocess.call('killall', 'dnsmasq')
        for usb in usbs:
            subprocess.call('ip', 'link', 'set', 'usb{0:d}'.format(usb),'down')
        subprocess.call(['iptables', '-F', '-t', 'nat'])
        with open('/proc/sys/net/ipv4/ip_forward', 'a') as f:
            f.write(0)

        print('Disabling usb networking on host')
        subprocess.call([self.adb, '-d', 'shell', 'setprop', 'sys.usb.config', 'adb'])
        subprocess.call([self.adb, 'wait-for-device'])
        subprocess.call([self.adb, 'shell', 'ip', 'route', 'delete', 'default'])

if __name__ == "__main__":

    # We need root on the host to mess with networking
    if os.getuid() != 0:
        print("ReverseTether needs to be run with sudo")
        exit()

    rt = ReverseTether()
    rt.start()
