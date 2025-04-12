# SUBNET = 10.23.23
# SERVER_IP = 5.78.88.129
# SSH_REMOTE = hpt

SUBNET = 10.50.50
SERVER_IP = 5.78.42.196
SSH_REMOTE = h

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


# web: kazhttp.py
# 	python wireguard_manager.py 9123

# .PHONY: kazhttp.py
# kazhttp.py:
# 	cp ../pipeline-js/kazhttp.py kazhttp.py

# dry:
# 	python vpn_setup.py --dry-run \
# 		--subnet $(SUBNET) \
# 		--public-ip $(SERVER_IP) \
# 		--ssh-remote $(SSH_REMOTE) \
# 		--clients bigmac phone

# test:
# 	python vpn_setup.py \
# 		--subnet $(SUBNET) \
# 		--public-ip $(SERVER_IP) \
# 		--ssh-remote $(SSH_REMOTE) \
# 		--server server \
# 		--local bigmac \
# 		--clients phone

# dry_load:
# 	python vpn_setup.py --dry-run --load \
# 		--input archive/devices.json \
# 		--output output/devices.json

# load:
# 	python vpn_setup.py --load \
# 		--input archive/ \
# 		--output output/

# hotspot:
# 	python vpn_setup.py \
# 	    --dry-run \
# 		--subnet $(SUBNET) \
# 		--public-ip 192.168.177.174 \
# 		--server flightmac \
# 		--local flightmac \
# 		--clients mobile \
# 		--local-is-server \
# 		--output hotspot-output/

# install:
# 	python vpn_setup.py \
# 	    --load \
# 		--input output/ \
# 		--local kaz3080 \
# 		--local-install-only