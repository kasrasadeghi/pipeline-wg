# SUBNET = 10.23.23
# SERVER_IP = 5.78.88.129
# SSH_REMOTE = hpt

SUBNET = 10.50.50
SERVER_IP = 5.78.42.196
SSH_REMOTE = h


web: kazhttp.py
	python wireguard_manager.py 9123

.PHONY: kazhttp.py
kazhttp.py:
	cp ../pipeline-js/kazhttp.py kazhttp.py

dry:
	python vpn_setup.py --dry-run \
		--subnet $(SUBNET) \
		--server-ip $(SERVER_IP) \
		--ssh-remote $(SSH_REMOTE) \
		--clients bigmac phone

test:
	python vpn_setup.py \
		--subnet $(SUBNET) \
		--server-ip $(SERVER_IP) \
		--ssh-remote $(SSH_REMOTE) \
		--server server \
		--local bigmac \
		--clients phone

dry_load:
	python vpn_setup.py --dry-run --load \
		--input archive/devices.json \
		--output output/devices.json

load:
	python vpn_setup.py --load \
		--input archive/devices.json \
		--output output/devices.json

hotspot:
	python vpn_setup.py \
	    --dry-run \
		--subnet $(SUBNET) \
		--public-ip 192.168.177.174 \
		--server flightmac \
		--local flightmac \
		--clients mobile \
		--local-is-server \
		--output hotspot-output/

qr:
	qrencode -t ANSIUTF8 -r hotspot-output/mobile.conf