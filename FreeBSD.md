FreeBSD status
--------------

What is missing ?


pam-unbit
---------

in the Linux version, this module connect to a unix socket to get the list of namespace file descriptors to call setns() on.

On FreeBSD it will be simpler, as we only need to get the jid (jail_id) of the container. We can get it over a unix socket, to avoid race conditions and to be sure to not enter
dead jails (read:jails without Emperor)


tuntap router
-------------

this is the core of networking (all in user space).

The only requirement is mapping a jail to a tun device. Is it possible with FreeBSD ?

First step will be porting the uWSGI tuntap plugin to FreeBSD


Distros
-------

We need to build rootfs for the various FreeBSD versions and for kFreeBSD

Memory limits
-------------

We need to add support for https://wiki.freebsd.org/Hierarchical_Resource_Limits in uWSGI core. This will be useful even outside of the uwsgi.it project
