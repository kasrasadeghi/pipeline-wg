dry:
	python vpn_setup.py --dry-run \
		--subnet 10.23.23 \
		--server-ip 5.78.88.129 \
		--ssh-remote hpt \
		--clients bigmac phone

test:
	python vpn_setup.py \
		--subnet 10.23.23 \
		--server-ip 5.78.88.129 \
		--ssh-remote hpt \
		--clients bigmac phone

load:
	python vpn_setup.py --load \
		--server-ip 5.78.88.129 \
		--ssh-remote hpt