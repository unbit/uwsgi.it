List of ports used by the uwsgi.it infrastructure
-------------------------------------------------


tcp 0.0.0.0:80

tcp 0.0.0.0:443

tcp public_ip:3022 fastrouter (requires firewall protection)

udp public_ip:3022 the dgram router bind on this address to forward packets to the http router

udp public_ip:3026 the dgram router accepts requests on this address from fastrouters (requires firewall protection)



127.0.0.1:5000 -> container Emperor stats

127.0.0.1:5001 -> tuntap stats server

127.0.0.1:5002 -> http stats server

127.0.0.1:5003 -> fastrouter stats server

udp public_ip:3000 legion packets (requires firewall protection)

udp public_ip:999 tuntap router (requires firewall protection)
