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

Objectives
----------

- each customer has a pool of containers
- each container has an associated disk quota, a cpu share and a fixed amount of memory
- each container has an associated Emperor
- best possibile isolation between containers
- each container can be mapped to a different distribution
- each container has its dedicated firewall based on the tuntap router plugin
- ssh access is governed by the container emperor using the pam-unbit project
- uid/gid mapping is managed using nss-unbit project
- each container runs with its uid/gid
- each container has its /etc/hosts and /etc/resolv.conf
- each vassal in the container subscribe to a central http router with a specific key (domain)
- containers Emperors configure alarms by default for: disk quota, oom, memory thresholds, restarts
- gather metrics and generate graphs
- SNI is the only https/spdy supported approach
- cron and external processes (like dbs) are managed as vassals


TODO
----

- we still need to find the silver bullet for secure subscriptions (we need to avoid unallowed containers to subscribe to specific domains, but we need multiple containers [on multiple machines too] to subscribe for the same domain)
