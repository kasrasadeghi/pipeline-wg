import subprocess

class Device:
  def __init__(self, name: str, ip: str, keys = None):
    self.name = name
    self.ip = ip
    self.ssh_remote = None

    # if 'wg' doesn't work, use import curve25519
    if keys != None:
      self.private, self.public = keys
    else:
      try:
        self.private, self.public = Device.generate_keypair()
      except:
        import wg.curve25519 as curve25519
        print("WARNING: 'wg' command not found, using curve25519")
        self.private, self.public = curve25519.generate_keypair()

  def to_dict(self):
    return {
      'name': self.name,
      'ip': self.ip,
      'private': self.private,
      'public': self.public,
      'ssh_remote': self.ssh_remote,
    }

  def set_ssh_remote(self, ssh_remote):
    self.ssh_remote = ssh_remote

  @staticmethod
  def from_dict(data):
    device = Device(data['name'], data['ip'], keys=(data['private'], data['public']))
    device.set_ssh_remote(data['ssh_remote'])
    return device

  def subnet(self):  # 10.0.0.5 -> 10.0.0
    return self.ip.rsplit('.', 1)[0]

  @staticmethod
  def generate_keypair():
    private_key = subprocess.run(['wg', 'genkey'], stdout=subprocess.PIPE, check=True).stdout
    public_key = subprocess.run(['wg', 'pubkey'], stdout=subprocess.PIPE, check=True, input=private_key).stdout
    return private_key.decode('utf-8').removesuffix('\n'), public_key.decode('utf-8').removesuffix('\n')
