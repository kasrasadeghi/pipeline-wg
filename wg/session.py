import json
import os
from typing import List, Optional
from wg.device import Device
from wg.remote import remote
from wg.text_config import make_server_config, make_client_config

class Session:
  def __init__(self, name):
    self.name = name
    self.networks = {}  # map prefix -> Network
  
  def create_network(self, prefix, public_ip):
    """prefix is something like '10.0.0' and public_ip is something like '127.0.0.1' for local testing and something like '42.100.50.50' for remote testing"""
    network = Network(self, prefix, public_ip)
    self.networks[prefix] = network
    self.save()
    return network
  
  def to_dict(self):
    return {
      "name": self.name,
      "networks": {name: network.to_dict() for name, network in self.networks.items()}
    }

  @staticmethod
  def from_dict(data):
    session = Session(data['name'])
    for name, net_data in data['networks'].items():
      session.networks[name] = Network.from_dict(session, net_data)
    return session

  def save(self):
    with open(f"sessions/{self.name}.session", "w+") as f:
      json.dump(self.to_dict(), f, indent=2)
    
  @staticmethod
  def load(name):
    if not os.path.exists(f"sessions/{name}.session"):
      return None
    with open(f"sessions/{name}.session", "r") as f:
      data = json.load(f)
      return Session.from_dict(data)
  
  def output(self):
    network = list(self.networks.values())[0]
    for device in network.devices:
      if device.ssh_remote is None:
        with open(f"output/{device.name}.conf", "w") as f:
          f.write(network.client_config(device.name))
      else:
        with open(f"output/{device.name}.conf", "w") as f:
          f.write(network.beacon_config())
      

class Network:
  def __init__(self, parent_session, prefix, public_ip):
    self.parent_session = parent_session
    self.prefix = prefix
    self.public_ip = public_ip
    self.devices: List[Device] = []
    self.beacon_name: Optional[str] = None

  def beacon(self):
    return next(device for device in self.devices if device.name == self.beacon_name)

  def next_device_number(self):
    device_numbers = [int(device.ip.rsplit(".", 1)[1]) for device in self.devices]
    device_numbers.sort()
    prior = None
    for num in device_numbers:
      if prior is None:
        prior = num
        continue
      if num != prior + 1:
        return prior + 1
      prior = num
    # If no devices exist, start with 1, otherwise return the next number after the last device
    return 1 if prior is None else prior + 1
  
  def create_device(self, name):
    assert name not in [dev.name for dev in self.devices], f"device with name '{name}' already created"
    device = Device(name, self.prefix + "." + str(self.next_device_number()))
    self.devices.append(device)
    self.parent_session.save()
    return device

  # returns (created, device)
  def get_or_create_device(self, name) -> (bool, Device):
    for device in self.devices:
      if device.name == name:
        return False, device
    return True, self.create_device(name)
  
  def remove_device(self, name):
    assert name in [dev.name for dev in self.devices], f"device with name '{name}' not found"
    i, device = next((i, device) for i, device in enumerate(self.devices) if device.name == name)
    self.devices.pop(i)
    self.parent_session.save()
    return device
  
  def create_beacon(self, name, ssh_remote):
    device = self.create_device(name)
    self.beacon_name = device.name
    device.set_ssh_remote(ssh_remote)
    self.parent_session.save()
    return device

  def to_dict(self):
    return {
      "prefix": self.prefix,
      "public_ip": self.public_ip,
      "devices": [device.to_dict() for device in self.devices],
      "beacon_name": self.beacon_name if self.beacon_name else ''
    }

  @staticmethod
  def from_dict(session, data):
    network = Network(session, data['prefix'], data['public_ip'])
    for device in data['devices']:
      network.devices.append(Device.from_dict(device))
    network.beacon_name = data['beacon_name']
    return network

  def beacon_config(self):
    server = self.beacon()
    clients = [device for device in self.devices if device.name != server.name]
    return make_server_config(server, clients)
  
  def client_config(self, device_name):
    # TODO check that there is only one server
    device = next(device for device in self.devices if device.name == device_name)
    server = next(device for device in self.devices if device.name != device_name)
    return make_client_config(device, server, self.public_ip)

  def upload_beacon_config(self):
    remote('sudo systemctl stop wg-quick@*.service', self.beacon().ssh_remote, False)
    remote('sudo rm /etc/wireguard/*.conf', self.beacon().ssh_remote, False)
    config = self.beacon_config()
    path = f'/etc/wireguard/{self.beacon_name}.conf'

    cmd = 'printf "' + config + '" | sudo tee "' + path + '" > /dev/null'
    remote(cmd, self.beacon().ssh_remote, False)
    remote('sudo systemctl restart wg-quick@' + self.beacon_name, self.beacon().ssh_remote, False)
  
  def is_beacon_current(self):
    path = f'/etc/wireguard/{self.beacon_name}.conf'
    is_active = remote('sudo systemctl is-active --quiet wg-quick@' + self.beacon_name, self.beacon().ssh_remote, False).returncode == 0
    if not is_active:
      print("WARNING: beacon config is not active")
    
    remote_conf = remote('cat "' + path + '"', self.beacon().ssh_remote, False).output
    config = self.beacon_config()
    if remote_conf != config:
      print("WARNING: beacon config is not current")
    
    return is_active and remote_conf == config

class RemoteBeacon:
  def __init__(self, name, ssh_remote):
    self.name = name
    self.ssh_remote = ssh_remote

  def check_dmesg(self):
    # TODO somehow send a request and figure out if it's getting blocked or getting through
    return remote('dmesg -T', self.ssh_remote, False).output

  def check_wg_show(self):
    # TODO check that the connections are working
    return remote('wg show', self.ssh_remote, False).output

  def check_ping(self):
    # TODO check that beacon and local are accessible on wg network
    return remote('ping -c 4 ' + self.name, self.ssh_remote, False).output

  def check_ssh(self):
    # TODO check that beacon and local are accessible on wg network
    return remote('ssh ' + self.name, self.ssh_remote, False).output

"""
troubleshooting

ssh dmesg -T, check that ufw isn't blocking something (!)
ssh wg show, check that the connections are working
ping, check that beacon and local are accessible on wg network
ssh ping, check that beacon and local are accessible on wg network from the beacon
"""