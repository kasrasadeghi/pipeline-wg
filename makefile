# SUBNET = 10.23.23
# SERVER_IP = 5.78.88.129
# SSH_REMOTE = hpt

SUBNET = 10.50.50
SERVER_IP = 5.78.42.196
SSH_REMOTE = h

ssh:
	python scripts/ssh.py

phone:
	python scripts/add_phone.py

send:
	python scripts/config_send.py --file output/kaz3080.conf --port 9000 --code-length 6

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
