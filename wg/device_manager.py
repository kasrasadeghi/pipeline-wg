# ================ ARCHIVED =====================================================================

class DeviceManager:
  def __init__(self, subnet: str, ssh_remote: str, public_ip: str, server_name: str, local_device: str, non_local_devices: List[str]):
    self.public_ip = public_ip
    self.ssh_remote = ssh_remote
    self.subnet = subnet
    if server_name == local_device:
      self.local_device = None
      self.server_device = Device(local_device, f'{subnet}.2')
      self.non_local_devices = [Device(name, f'{subnet}.{i+3}') for i, name in enumerate(non_local_devices)]
    else:
      self.server_device = Device(server_name, f'{subnet}.1')
      self.local_device = Device(local_device, f'{subnet}.2')
      self.non_local_devices = [Device(name, f'{subnet}.{i+3}') for i, name in enumerate(non_local_devices)]
  
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
      print(f'loading from {load_folder}devices.json...')
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

    if not os.path.exists(save_folder):
      os.makedirs(save_folder)
    with open(os.path.join(save_folder, 'devices.json'), 'w') as f:
      json.dump(data, f, indent=2)