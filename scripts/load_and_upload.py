from wg.session import Session
import argparse

argparser = argparse.ArgumentParser()
argparser.add_argument("--prefix", type=str)
args = argparser.parse_args()

session = Session.load("ssh")
if not session:
  print("ERROR: no session found, run ssh.py first")
  exit(1)

network = session.networks[args.prefix]

session.output()
network.upload_beacon_config()
