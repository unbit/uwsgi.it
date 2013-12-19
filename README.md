uwsgi.it
========

The next-generation Unbit hosting platform

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
