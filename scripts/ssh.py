from wg.session import Session

# open ssh session
# create a network in the session
# create a client device in the network
# the session auto-saves

session = Session.load("ssh")
if not session:
  session = Session("ssh")
  network = session.create_network(prefix="10.50.50", public_ip="5.78.42.196")
  beacon = network.create_beacon(name="beacon", ssh_remote="h")
  client = network.create_device(name="admin")
else:
  network = session.networks["10.50.50"]
  beacon = network.beacon
  client = network.devices[1]
  assert client.name == "admin"

session.output()

if not network.is_beacon_current():
  print("ALERT: beacon config is not current, uploading new config")
  network.upload_beacon_config()
