import argparse
import subprocess
from wg.session import Session

argparser = argparse.ArgumentParser()
argparser.add_argument("--prefix", type=str)
args = argparser.parse_args()

session = Session.load("ssh")
if not session:
  print("ERROR: no session found, run ssh.py first")
  exit(1)

network = session.networks[args.prefix]

i = None
for i, device in enumerate(network.devices):
  if device.name == "phone":
    device = network.devices[i]
    break

if i is None:
  device = network.create_device(name="phone")
else:
  print("WARNING: phone device not found, creating new device")
  device = network.devices[i]

session.output()
network.upload_beacon_config()

print("ALERT: phone config is not current, scan qrcode")
subprocess.run(["qrencode", "-t", "PNG", "-o", "output/phone.png", "-r", "output/phone.conf"])
subprocess.run(["open", "output/phone.png"])
