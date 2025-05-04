import subprocess
from wg.session import Session

session = Session.load("ssh")
if not session:
  print("ERROR: no session found, run ssh.py first")
  exit(1)

network = session.networks["10.50.50"]
device = network.create_device(name="phone")

session.output()
network.upload_beacon_config()

print("ALERT: phone config is not current, scan qrcode")
subprocess.run(["qrencode", "-t", "PNG", "-o", "output/phone.png", "-r", "output/phone.conf"])
subprocess.run(["open", "output/phone.png"])
