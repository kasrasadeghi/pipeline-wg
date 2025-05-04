from requirement import remote

# ping the server
remote('ping -c 1 10.50.50.1', 'h', False)

# ask the server for the status of the network
remote('wg', 'h', False)