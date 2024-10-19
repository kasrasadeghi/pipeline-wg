# USAGE: 
# python vpn-setup.py --dry-run \
#     --subnet 10.50.50 \
#     --server-ip 5.78.42.196 \
#     --remote am \
#     --server lightsail \
#     --local arkaz \ 
#     --clients kaz3080 phone tabs6 tabs8u kaztop

# generate the scripts for the server and the clients
# send the server config to the server
# setup the server
# - setup packet forwarding
# - install wireguard and enable wireguard systemd service

import subprocess
from typing import List
import argparse
import json
import os

# TODO make the defaults None and then provide a defaults SimpleNamespace to use if they're not available

parser = argparse.ArgumentParser(description='Setup VPN on remote host.')
parser.add_argument('--dry-run', action='store_true')
parser.add_argument('--ssh-remote')
parser.add_argument('--subnet', help='required if not loading')
parser.add_argument('--public-ip', help='required if not loading')
parser.add_argument('--server', help='the name of the remote server')
parser.add_argument('--local', help='the name of the local client, if the current machine is the not the server')
parser.add_argument('--clients', nargs='+', help="the non-local clients")
parser.add_argument('--load', action='store_true', help='load from a json file')
parser.add_argument('--input', help='the path to the folder that contains the json file to load from', default='output/devices.json')
parser.add_argument('--output', help='the path to the folder that will contain the json file to save to', default='output/devices.json')
parser.add_argument('--local-is-server', action='store_true')

args = parser.parse_args()

if not args.local_is_server:
  from requirement import Requirement

# === requirements ==========================================

  packet_forwarding = Requirement(
    desc='packet forwarding',
    setup='sudo sysctl -p /etc/sysctl.d/70-wireguard-routing.conf -w',
    check="(sudo sysctl -a | grep 'net.ipv4.ip_forward = 1') && (sudo sysctl -a | grep 'net.ipv4.conf.all.proxy_arp = 1')",
    remote=True,
    path='/etc/sysctl.d/70-wireguard-routing.conf',
    content='net.ipv4.ip_forward = 1\nnet.ipv4.conf.all.proxy_arp = 1\n',
  )

  package_install = Requirement(
    desc='install prereqs',
    setup='sudo apt-get update && sudo apt-get install wireguard-tools file -y',
    check="dpkg -l | grep wireguard-tools && dpkg -l | grep 'ii  file'",
    remote=True,
  )

# === devices and device management ==========================================

class Device:
  def __init__(self, name: str, ip: str):
    global next_ip
    self.name = name
    self.ip = ip

    # if 'wg' doesn't work, use import curve25519
    try:
      self.private, self.public = Device.gen_keys()
    except:
      import curve25519
      self.private, self.public = curve25519.generate_keypair()

  def to_dict(self):
    return {
      'name': self.name,
      'ip': self.ip,
      'private': self.private,
      'public': self.public,
    }

  def subnet(self):  # 10.0.0.5 -> 10.0.0
    return self.ip.rsplit('.', 1)[0]

  @staticmethod
  def gen_keys():
    private_key = subprocess.run(['wg', 'genkey'], stdout=subprocess.PIPE, check=True).stdout
    public_key = subprocess.run(['wg', 'pubkey'], stdout=subprocess.PIPE, check=True, input=private_key).stdout
    return private_key.decode('utf-8').removesuffix('\n'), public_key.decode('utf-8').removesuffix('\n')


class DeviceManager:
  def __init__(self, subnet: str, ssh_remote: str, public_ip: str, server_name: str, local_device: str, non_local_devices: List[str]):
    self.public_ip = public_ip
    self.ssh_remote = ssh_remote
    self.subnet = subnet
    if server_name == local_device:
      self.local_device = None
      self.server_device = Device(local_device, f'{args.subnet}.2')
      self.non_local_devices = [Device(name, f'{args.subnet}.{i+3}') for i, name in enumerate(non_local_devices)]
    else:
      self.server_device = Device(server_name, f'{args.subnet}.1')
      self.local_device = Device(local_device, f'{args.subnet}.2')
      self.non_local_devices = [Device(name, f'{args.subnet}.{i+3}') for i, name in enumerate(non_local_devices)]
  
  def server(self) -> Device:
    return self.server_device
  
  def clients(self) -> List[Device]:
    if self.local_device:
      return [self.local_device, *self.non_local_devices]
    else:
      return self.non_local_devices
  
  @staticmethod
  def validate_names(subnet: str, ssh_remote: str, public_ip: str, server_name: str, local_device: str, non_local_devices: List[str]):
    assert server_name not in non_local_devices, f"Cannot name a client the same name as the server '{server_name}'"
    assert local_device not in non_local_devices, f"Cannot name a client the same as '{local_device}'"
    assert len(non_local_devices) == len(set(non_local_devices)), "Duplicate client names"

  @staticmethod
  def load(load_folder):
    with open(os.path.join(load_folder, 'devices.json'), 'r') as f:
      data = json.load(f)
      
      def load_device(d, name):
        d.private = data[name]['private']
        d.public = data[name]['public']
        d.ip = data[name]['ip']

      DeviceManager.validate_names(**data['args'])
      x = DeviceManager(**data['args'])
      load_device(x.server_device, data['args']['server_name'])
      load_device(x.local_device, data['args']['local_device'])
      for client in x.non_local_devices:
        load_device(client, client.name)

      return x
  
  def save(self, save_folder):
    data = {
      'args': {
        'public_ip': self.public_ip,
        'ssh_remote': self.ssh_remote,
        'subnet': self.server_device.subnet(),

        'server_name': self.server_device.name,
        'local_device': self.local_device.name if self.local_device else None,
        'non_local_devices': [c.name for c in self.non_local_devices],
      },
      self.server_device.name: self.server_device.to_dict(),
    }
    if self.local_device:
      data[self.local_device.name] = self.local_device.to_dict()
    for client in self.non_local_devices:
      data[client.name] = client.to_dict()
    with open(os.path.join(save_folder, 'devices.json'), 'w') as f:
      json.dump(data, f, indent=2)

# wireguard configs

def make_server_requirement(server: Device, clients: List[Device]):
  content = make_server_config(server, clients)
  interface_name = server.name
  path = f'/etc/wireguard/{interface_name}.conf'
  return Requirement(
    desc=f"'{interface_name}' wireguard config",
    setup=(f'sleep 1 && sudo systemctl enable wg-quick@{interface_name} '
            f'&& sudo systemctl restart wg-quick@{interface_name}'),
    check=f"sudo wg && ( ip addr | grep '{interface_name}' ) && sudo file '{path}' && [[ $(sudo cat '{path}') == '{content}' ]]",
    remote=True,
    path=path,
    content=content,
  )

def make_server_config(server: Device, clients: List[Device]):
  content = (
f"""[Interface]
# {server.name}
Address = {server.ip}/24
ListenPort = 51820
PrivateKey = {server.private}
""")
  for client in clients:
    content += (
f"""
[Peer]
# {client.name}
PublicKey = {client.public}
AllowedIps = {client.ip}/32
""")
  return content


def make_client_requirement(client: Device, server: Device, public_ip: str):
  content = make_client_config(client, server)

  interface_name = client['name']
  path = f'/etc/wireguard/{interface_name}.conf'
  return Requirement(
    name=interface_name,
    desc=f"client '{interface_name}' wireguard config",
    setup=(f'sleep 1 && sudo systemctl enable wg-quick@{interface_name} '
           f'&& sudo systemctl restart wg-quick@{interface_name}'),
    check=f"sudo wg && ( ip addr | grep '{interface_name}' ) && sudo file '{path}' && [[ $(sudo cat '{path}') == '{content}' ]]",
    path=path,
    content=content,
    remote=False,
  )

def make_client_config(client: Device, server: Device, public_ip: str):
  return (
f"""[Interface]
# {client.name}
Address = {client.ip}/32
PrivateKey = {client.private}

[Peer]
# server
Endpoint = {public_ip}:51820
PublicKey = {server.public}
AllowedIPs = {server.subnet()}.0/24
PersistentKeepalive = 25
""")


def main():
  if not args.load:
    assert args.output

  if args.load:
    mgr = DeviceManager.load(args.input)
  else:
    DeviceManager.validate_names(server_name=args.server, local_device=args.local, non_local_devices=args.clients, public_ip=args.public_ip,
      ssh_remote=args.ssh_remote,
      subnet=args.subnet)

    mgr = DeviceManager(
      server_name=args.server,
      local_device=args.local,
      non_local_devices=args.clients,
      public_ip=args.public_ip,
      ssh_remote=args.ssh_remote,
      subnet=args.subnet
    )
  
  mgr.save(args.output)

  # we need a remote and a real run in order to install packages and config a system
  if args.local_is_server:
    assert args.dry_run and mgr.local_device is None, f"{args.dry_run=} {mgr.local_device.to_dict()=}"
  else:
    Requirement.configure(mgr.ssh_remote, args.dry_run)

    packet_forwarding.ensure()
    package_install.ensure()
    
    server_config = make_server_requirement(mgr.server(), mgr.clients())
    server_config.ensure()

  if mgr.local_device:
    with open(os.path.join(args.output, mgr.local_device.name + '.conf'), "w+") as f:
      f.write(make_client_config(mgr.local_device, mgr.server_device, mgr.public_ip))
  
  with open(os.path.join(args.output, mgr.server_device.name + '.conf'), "w+") as f:
    f.write(make_server_config(mgr.server_device, mgr.clients()))

  for client in mgr.clients():
    with open(os.path.join(args.output, client.name + '.conf'), "w+") as f:
      f.write(make_client_config(client, mgr.server_device, mgr.public_ip))

if __name__ == '__main__':
  main()
