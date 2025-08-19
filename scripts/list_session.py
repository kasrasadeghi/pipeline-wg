import subprocess
from wg.session import Session
import argparse

argparser = argparse.ArgumentParser()
args = argparser.parse_args()

session = Session.load("ssh")
if not session:
  print("ERROR: no session found, run ssh.py first")
  exit(1)

for network in session.networks.values():
  print(network.prefix)
  for device in network.devices:
    print(f"  {device.name} @ {device.ip}")
    if device.ssh_remote:
      print(f"    ssh:{device.ssh_remote}")


