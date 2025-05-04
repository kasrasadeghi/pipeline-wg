from wg.session import Session

session = Session.load("ssh")
if not session:
  print("ERROR: no session found, run ssh.py first")
  exit(1)

network = session.networks["10.50.50"]

session.output()
network.upload_beacon_config()
