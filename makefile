# SUBNET = 10.23.23
# SERVER_IP = 5.78.88.129
# SSH_REMOTE = hpt

SUBNET = 10.50.50
SERVER_IP = 5.78.42.196
SSH_REMOTE = h

list:
	python -m scripts.list_session

ssh:
	python -m scripts.ssh --public_ip $(SERVER_IP) --ssh_remote $(SSH_REMOTE) --prefix $(SUBNET)

phone:
	python -m scripts.add_phone --prefix $(SUBNET)

device:
	python -m scripts.add_device --name kaz3080 --prefix $(SUBNET)

send:
	python -m scripts.config_send --file output/kaz3080.conf --port 9000 --code-length 6

load-and-upload:
	python -m scripts.load_and_upload --prefix $(SUBNET)

inspect-beacon:
	ssh $(SSH_REMOTE) "cat /etc/wireguard/beacon.conf"

from-scratch:
	python vpn_setup.py \
		--subnet $(SUBNET) \
		--public-ip $(SERVER_IP) \
		--ssh-remote $(SSH_REMOTE) \
		--server server \
		--local bigmac \
		--clients phone

qr:
	qrencode -t ANSIUTF8 -r output/phone.conf
