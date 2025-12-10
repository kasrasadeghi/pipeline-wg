# SUBNET = 10.23.23
# SERVER_IP = 5.78.88.129
# SSH_REMOTE = hpt

SUBNET = 10.50.50
SERVER_IP = 5.78.42.196
SSH_REMOTE = h
SESSION_NAME = ssh

list:
	python -m scripts.list_session --session $(SESSION_NAME)

ssh:
	python -m scripts.ssh --public_ip $(SERVER_IP) --ssh_remote $(SSH_REMOTE) --prefix $(SUBNET) --session $(SESSION_NAME)

phone:
	python -m scripts.add_device --name phone --prefix $(SUBNET) --qrcode --session $(SESSION_NAME)

device:
	python -m scripts.add_device --name kaz5090 --prefix $(SUBNET) --session $(SESSION_NAME)

send:
	python -m scripts.config_send --file output/kaz3080.conf --port 9000 --code-length 6 --session $(SESSION_NAME)

load-and-upload:
	python -m scripts.load_and_upload --prefix $(SUBNET) --session $(SESSION_NAME)

inspect-beacon:
	ssh $(SSH_REMOTE) "cat /etc/wireguard/beacon.conf" --session $(SESSION_NAME)

qr:
	qrencode -t ANSIUTF8 -r output/phone.conf
