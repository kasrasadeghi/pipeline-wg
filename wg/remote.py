import subprocess
from types import SimpleNamespace

# def local(cmd, dry_run):
#   if dry_run:
#     print(f'$ {cmd}  # dry run')
#     return SimpleNamespace(returncode=1, output=None)
#   else:
#     p = subprocess.Popen(cmd, shell=True, executable='/bin/bash', stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
#     print(f"$ {cmd}")
#     for line in iter(p.stdout.readline, b''):
#       print(line.decode('utf-8'), end='')
#     p.communicate()
#     print(f"-> error code '{p.returncode}'")
#     return p

def remote(cmd, ssh_remote, dry_run):
  if dry_run:
    print(f'$ {cmd}  # dry run')
    return SimpleNamespace(returncode=1, output=None)
  else:
    p = subprocess.Popen(['ssh', ssh_remote, cmd], stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    print(f"$ {cmd}")
    output = ''
    for line in iter(p.stdout.readline, b''):
      curr_line = line.decode('utf-8')
      print(curr_line, end='')
      output += curr_line
    p.communicate()
    print(f"-> error code '{p.returncode}'")
    return SimpleNamespace(returncode=p.returncode, output=output)
