Quickstart for Customers owning a whole uwsgi.it server
=======================================================

Please read the CustomerQuickstart before this !!!

If your uwsgi.it supplier supports mapping customer to one (ore more) server, you are able to create containers on your dedicated machines.

The system constantly checks that you are not overselling.

You are not supposed to delete containers (you can remap, reconfigure and retag them easily) as a delete should be followed by a complete removal of the container's home from the server, so if you need to destroy a container (for a good reason), contact your supplier.


Getting the list of available servers
=====================================

```sh
curl https://kratos:deimos@api.uwsgi.it/api/me
```

the 'servers' attribute is an array of the servers you have rights on (generally it is an empty array).

The servers are showed as a list of ipv4 addresses. You have to use this address to select on which server you want to create a container.


Creating a container
====================

You need to specify the 'server' (obviously) a 'name' (it does not need to be unique) a 'memory' value (in MB) and a 'storage' one (again in MB).

To create the container 'hydra' on machine '1.2.3.4' with 1GB of memory and 20GB of storage you just send

```sh
curl -X POST -d '{"server":"1.2.3.4", "name":"hydra", "memory":1000, "storage":20000}' https://kratos:deimos@api.uwsgi.it/api/containers
```

Port mapping
============

Owners of dedicated servers can map public unprivileged (>1024) udp and tcp ports of the machine to specific private ports in containers.

As an example you can set a server to forward all requests to its port 8080 to the port 9000 of the container XYZ.

Private ports must be bound on network 10.x.x.x, this rule protects you from exposing services on 127.0.0.1.

The api is pretty minimal

```sh
curl -X GET https://kratos:deimos@api.uwsgi.it/api/portmappings/ip
```

will return the current mappings for the server (specified by its public ip address)

```sh
curl -X POST -d '{"container": 30001, "proto":"tcp", "public_port": 9000, "private_port": 8000}' https://kratos:deimos@api.uwsgi.it/api/portmappings/ip
```

will create a mapping from public tcp port 9000 to private port 8000 on the container 3001 on the nwtwork 10.x.x.x

finally

```sh
curl -X DELETE -d '{"id": xyz}' https://kratos:deimos@api.uwsgi.it/api/portmappings/ip
```

will delete the mapping with the specified id
