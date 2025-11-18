import subprocess
from wg.session import Session
import argparse

argparser = argparse.ArgumentParser()
argparser.add_argument("--name", type=str, default="client")
argparser.add_argument("--prefix", type=str)
argparser.add_argument("--qrcode", action="store_true")
args = argparser.parse_args()

session = Session.load("ssh")
if not session:
  print("ERROR: no session found, run ssh.py first")
  exit(1)

network = session.networks[args.prefix]
created, device = network.get_or_create_device(name=args.name)
if not created:
  print("WARNING: device already exists, just showing qrcode")

session.output()
network.upload_beacon_config()

if args.qrcode:
  subprocess.run(["qrencode", "-t", "PNG", "-o", "output/" + device.name + ".png", "-r", "output/" + device.name + ".conf"])
  subprocess.run(["open", "output/" + device.name + ".png"])
