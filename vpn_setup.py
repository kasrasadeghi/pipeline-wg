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

parser = argparse.ArgumentParser(description='Setup VPN on remote host.')
parser.add_argument('--dry-run', action='store_true')
parser.add_argument('--ssh-remote', required=True)
parser.add_argument('--subnet', help='required if not loading')
parser.add_argument('--server-ip', help='required if not loading')
parser.add_argument('--server', help='the name of the remote server')
parser.add_argument('--local', help='the name of the local client, if the current machine is the not the server')
parser.add_argument('--clients', nargs='+', help="the non-local clients")
parser.add_argument('--load', action='store_true', help='load from a json file')
parser.add_argument('--config', help='the path to the json file to load from', default='output/devices.json')

args = parser.parse_args()

from requirement import Requirement
Requirement.configure(args.ssh_remote, args.dry_run)

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
  check="dpkg -l | grep wireguard-tools",
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
  next_ip = 0
  def __init__(self, server_name: str, local_device: str, non_local_devices: List[str]):
    self.server_device = Device(server_name, f'{args.subnet}.1')
    self.local_device = Device(local_device, f'{args.subnet}.2')
    self.non_local_devices = [Device(name, f'{args.subnet}.{i+3}') for i, name in enumerate(non_local_devices)]
  
  def server(self) -> Device:
    return self.server_device
  
  def clients(self) -> List[Device]:
    return [self.local_device, *self.non_local_devices]
  
  @staticmethod
  def validate_names(server_name: str, local_device: str, non_local_devices: List[str]):
    assert server_name not in non_local_devices, f"Cannot name a client the same name as the server '{server_name}'"
    assert local_device not in non_local_devices, f"Cannot name a client the same as '{local_device}'"
    assert len(non_local_devices) == len(set(non_local_devices)), "Duplicate client names"

  @staticmethod
  def load(filename):
    with open(filename, 'r') as f:
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
  
  def save(self, filename):
    data = {
      'args': {
        'server_name': self.server_device.name,
        'local_device': self.local_device.name,
        'non_local_devices': [c.name for c in self.non_local_devices],
      },
      self.server_device.name: self.server_device.to_dict(),
      self.local_device.name: self.local_device.to_dict(),
    }
    for client in self.non_local_devices:
      data[client.name] = {'private': client.private, 'public': client.public}
    with open(filename, 'w') as f:
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


def make_client_requirement(client: Device, server: Device):
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

def make_client_config(client: Device, server: Device):
  return (
f"""[Interface]
# {client.name}
Address = {client.ip}/32
PrivateKey = {client.private}

[Peer]
# server
Endpoint = {args.server_ip}:51820
PublicKey = {server.public}
AllowedIPs = {server.subnet()}.0/24
PersistentKeepalive = 25
""")


def main():
  if args.load:
    print(args)
    assert args.ssh_remote
  else:
    assert args.subnet
    assert args.ssh_remote
    assert args.server_ip

  packet_forwarding.ensure()
  package_install.ensure()

  print('clients:', args.clients)

  if args.load:
    mgr = DeviceManager.load(args.config)
  else:
    DeviceManager.validate_names(args.server, args.local, args.clients)

    mgr = DeviceManager(
      server_name='server',
      local_device=args.local,
      non_local_devices=args.clients,
    )
    mgr.save(args.config)
  
  server_config = make_server_requirement(mgr.server(), mgr.clients())
  server_config.ensure()

  with open('output/' + mgr.local_device.name + '.conf', "w+") as f:
    f.write(make_client_config(mgr.local_device, mgr.server_device))
  
  with open('output/' + mgr.server_device.name + '.conf', "w+") as f:
    f.write(make_server_config(mgr.server_device, mgr.clients()))

  for client in mgr.clients():
    with open('output/' + client.name + '.conf', "w+") as f:
      f.write(make_client_config(client, mgr.server_device))

if __name__ == '__main__':
  main()
