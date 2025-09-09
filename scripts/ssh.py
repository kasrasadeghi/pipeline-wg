import argparse
from wg.session import Session

# open ssh session
# create a network in the session
# create a client device in the network
# the session auto-saves

argparser = argparse.ArgumentParser()
argparser.add_argument("--public_ip", required=True)
argparser.add_argument("--ssh_remote", required=True)
argparser.add_argument("--prefix", required=True)
args = argparser.parse_args()

session = Session.load("ssh")
if not session:
  session = Session("ssh")
  network = session.create_network(prefix=args.prefix, public_ip=args.public_ip)
  beacon = network.create_beacon(name="beacon", ssh_remote=args.ssh_remote)
  client = network.create_device(name="admin")
else:
  network = session.networks[args.prefix]
  beacon = network.beacon
  client = network.devices[1]
  assert client.name == "admin"

session.output()

if not network.is_beacon_current():
  print("ALERT: beacon config is not current, uploading new config")
  network.upload_beacon_config()
