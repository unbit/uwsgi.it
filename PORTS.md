List of ports used by the uwsgi.it infrastructure
-------------------------------------------------


tcp 0.0.0.0:80 public HTTP

tcp 0.0.0.0:443 public HTTPS

tcp public_ip:1999 fastrouter (requires firewall protection)

udp public_ip:3022 the dgram router bind on this address to forward packets to the http router

udp public_ip:3026 the dgram router accepts requests on this address from fastrouters (requires firewall protection)



127.0.0.1:5000 -> containers Master stats

127.0.0.1:5001 -> containers Emperor stats

127.0.0.1:5002 -> tuntap stats server

127.0.0.1:5003 -> http stats server

127.0.0.1:5004 -> fastrouter stats server

127.0.0.1:5005 -> legion stats server

udp public_ip:2000 legion packets (requires firewall protection)

udp public_ip:999 tuntap router (requires firewall protection)
