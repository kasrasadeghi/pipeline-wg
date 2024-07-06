SUBNET = 10.23.23
SERVER_IP = 5.78.88.129
SSH_REMOTE = hpt

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

load:
	python vpn_setup.py --load \
		--server-ip $(SERVER_IP) \
		--ssh-remote $(SSH_REMOTE)
