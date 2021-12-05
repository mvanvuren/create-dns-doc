"""retrieve dns addresses from router and write to local csv file"""
import os.path
import csv;
from paramiko import SSHClient
from scp import SCPClient

router_ip = 'router.mvanvuren.local'
ip_range = '192.168.0.'
remote_hosts_file = '/tmp/etc/hosts.dnsmasq'
local_hosts_file = './hosts.dnsmasq'
remote_dnsmasq_file = '/tmp/etc/dnsmasq.conf'
local_dnsmasq_file = './dnsmasq.conf'
dns_file = './dns.csv'
field_names = ['ip', 'mac', 'name', 'comments']


def create_addresses():
    if not os.path.isfile(dns_file):
        return [{'ip' : ip_range + str(i), 'name': '', 'mac': '', 'comments': ''}
            for i in range(1, 256)]

    addresses = []
    with open(dns_file, 'r') as file:
        csv_reader = csv.DictReader(file, dialect='excel', delimiter=';')
        not_used = next(csv_reader, None)
        for address in csv_reader:
            addresses.append(address)

    return addresses
    

def get_remote_files():
    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.connect(router_ip)
    scp = SCPClient(ssh.get_transport())

    scp.get(remote_hosts_file, local_hosts_file)
    scp.get(remote_dnsmasq_file, local_dnsmasq_file)

    scp.close()


def fill_hostnames(addresses):
    with open(local_hosts_file) as file:
        for line in file:
            (ip, hostname) = line.rstrip().split()
            address = [a for a in addresses if a['ip'] == ip][0]
            address['name'] = hostname
    os.remove(local_hosts_file)


def fill_mac_addresses(addresses):
    with open(local_dnsmasq_file) as file:
        for line in file:
            if line.startswith('dhcp-host'):
                (mac, ip) = line[10:].rstrip().split(',')
                address = [a for a in addresses if a['ip'] == ip][0]
                address['mac'] = mac
    os.remove(local_dnsmasq_file)


def write_dns_doc(addresses):
    with open(dns_file, 'w', newline='') as file:
        csv_writer = csv.DictWriter(file, fieldnames=field_names, dialect='excel', delimiter=';')
        csv_writer.writeheader()
        for address in addresses:
            csv_writer.writerow(address)


def main():    
    get_remote_files()
    addresses = create_addresses()
    fill_hostnames(addresses)
    fill_mac_addresses(addresses)
    write_dns_doc(addresses)


main()