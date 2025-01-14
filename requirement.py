import subprocess
from types import SimpleNamespace
from typing import Optional

def local(cmd, dry_run):
  if dry_run:
    print(f'$ {cmd}  # dry run')
    return SimpleNamespace(returncode=1, output=None)
  else:
    p = subprocess.Popen(cmd, shell=True, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    print(f"$ {cmd}")
    for line in iter(p.stdout.readline, b''):
      print(line.decode('utf-8'), end='')
    p.communicate()
    print(f"-> error code '{p.returncode}'")
    return p

def remote(cmd, ssh_remote, dry_run):
  if dry_run:
    print(f'$ {cmd}  # dry run')
    return SimpleNamespace(returncode=1, output=None)
  else:
    p = subprocess.Popen(['ssh', ssh_remote, cmd], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    print(f"$ {cmd}")
    for line in iter(p.stdout.readline, b''):
      print(line.decode('utf-8'), end='')
    p.communicate()
    print(f"-> error code '{p.returncode}'")
    return p

class Requirement:
  ssh_remote = None
  dry_run = None

  def __init__(self, desc: str, setup: str, check: str, remote: bool, path: Optional[str] = None, content: Optional[str] = None):
    self.desc = desc
    self.setup = setup
    self.check = check
    self.remote = remote
    self.path = path
    self.content = content
  
  @classmethod
  def configure(cls, ssh_remote_val, dry_run_val):
    cls.ssh_remote = ssh_remote_val
    cls.dry_run = dry_run_val

  def ensure(self):
    assert Requirement.ssh_remote is not None, 'ssh_remote must be set'
    assert Requirement.dry_run is not None, 'dry_run must be set'
    run = (lambda cmd: remote(cmd, Requirement.ssh_remote, Requirement.dry_run) if self.remote else
           lambda cmd: local(cmd, Requirement.dry_run))

    def check():
      r = run(self.check)
      return True if r.returncode == 0 else False

    def send():
      if self.path is not None:
        run('printf "' + self.content + '" | sudo tee ' + self.path)

    def setup():
      run(self.setup)

    if not check():
      send()
      setup()
