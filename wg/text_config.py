from wg.device import Device
from typing import List
import textwrap

def make_server_config(server: Device, clients: List[Device]):
  content = textwrap.dedent(
    f"""
    [Interface]
    # {server.name}
    Address = {server.ip}/24
    ListenPort = 51820
    PrivateKey = {server.private}
    """)
  for client in clients:
    content += textwrap.dedent(
      f"""
      [Peer]
      # {client.name}
      PublicKey = {client.public}
      AllowedIps = {client.ip}/32
      """)
  return content


def make_client_config(client: Device, server: Device, public_ip: str):
  return textwrap.dedent(
    f"""
    [Interface]
    # {client.name}
    Address = {client.ip}/32
    PrivateKey = {client.private}

    [Peer]
    # server
    Endpoint = {public_ip}:51820
    PublicKey = {server.public}
    AllowedIPs = {server.subnet()}.0/24
    PersistentKeepalive = 25
    """)

# [Interface]
# PrivateKey = <YOUR_PRIVATE_KEY>
# Address = 10.200.200.1/24
# ListenPort = 51820

# [Peer]
# PublicKey = <YOUR_PUBLIC_KEY>
# AllowedIPs = 10.50.50.2/32
# Endpoint = 127.0.0.1:51820
