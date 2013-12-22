uwsgi.it
========

The next-generation Unbit hosting platform

Intro
-----

contrary to the current unbit.it hosting platform, the next generation one will be:

- fully open source (currently at least 60% of the unbit.it kernel patches are not released to the public)
- can be installed on vanilla kernels
- everyone can build it on his/her systems (and eventually buy commercial support from unbit.com ;)
- will not rely on apache (so .htaccess will not be supported, unless you install apache in your container and proxy it via uWSGI routing)

Goals
-----

- each customer has a pool of containers
- each container has an associated disk quota, a cpu share and a fixed amount of memory
- each container has an associated Emperor
- best possible isolation between containers
- each container can be mapped to a different distribution
- each container has its dedicated firewall based on the tuntap router plugin
- ssh access is governed by the container emperor using the pam-unbit project
- uid/gid mapping is managed using nss-unbit project
- each container runs with its own uid/gid
- each container has its own /etc/hosts and /etc/resolv.conf
- each vassal in the container subscribes to a central http router with a specific key (domain)
- containers' Emperor by default configure alarms for: disk quota, oom, memory thresholds, restarts
- gather metrics and generate graphs
- SNI is the only https/spdy supported approach
- cron and external processes (like dbs) are managed as vassals
- 

How it works
------------

On server startup the emperor.ini is run. This Emperor manage vassals in /etc/uwsgi/vassals

Each vassal is spawned in a new Linux namespace and cgroup (all is native, no lxc is involved)

Each vassal spawns a sub-Emperor with uid and gid > 30000, the user (the owner of the container) can now use
this sub-Emperor to spawn its vassals.




TODO
----

- fastrouter-only implementation for nginx integration
