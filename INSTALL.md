Step by step guide for installing a uwsgi.it node
-------------------------------------------------

This procedure assumes an x86_64 Ubuntu 13.10 server (ubuntu-minimal) with ext4 filesystem.

Note: you can set /etc/hostname to whatever you want, each container will have its own...

/etc/default/grub
-----------------

First step is ensuring the kernel io scheduler (elevator) is set to cfq (ubuntu enforces it to deadline).

Before you ask, being "fair" at the price of a bit of performance is the best approach (imho) for hosting environments. In addition to this, CFQ will avoid a single user to steal all of your storage I/O throughput

open `/etc/default/grub` and change

```sh
GRUB_CMDLINE_LINUX_DEFAULT="nomodeset"
```

to

```sh
GRUB_CMDLINE_LINUX_DEFAULT="nomodeset elevator=cfq"
```

and run (as root)

```sh
dpkg-reconfigure grub-pc
```

/etc/fstab
----------

We need a working (and customizable) cgroup setup and a filesystem with uid quota support.

Let's edit /etc/fstab

First step is finding the line on which the rootfs (or more general where /containers, the home of our containers) will be stored. Once found add quota support:

```sh
...
/dev/md/2 / ext4 defaults,usrjquota=aquota.user,jqfmt=vfsv1 0 0
...
```

in this example /dev/md2 will store customer's file so we add `usrjquota=aquota.user,jqfmt=vfsv1` to its options

Finally the cgroup line:

```sh
...
/dev/md/2 / ext4 defaults,usrjquota=aquota.user,jqfmt=vfsv1 0 0
none /sys/fs/cgroup cgroup blkio,cpuacct,cpu,memory,devices 0 0
...
```

Now you are ready to reboot your server. If it reboots correctly just move to the next step

Configuring ssh (/etc/ssh/sshd_config)
--------------------------------------

Find the line with 

```sh
#AuthorizedKeysFile     %h/.ssh/authorized_keys
```

and change to

```sh
AuthorizedKeysFile %h/.ssh/authorized_keys %h/.ssh/uwsgi_authorized_keys
```

Then find 

```sh
#PasswordAuthentication yes
```

and change to

```sh
PasswordAuthentication no
```

Finally turn off X11Forwarding

```sh
X11Forwarding no
```

Optional (for better user experience):

```sh
ClientAliveInterval 30
```

Now be ABSOLUTELY sure to set your .ssh/authorized_keys in the account you are currently using to log-in (otherwise you will not be able to log-in back via ssh).

test if you can login with your key and then restart your ssh service:

```sh
service ssh restart
```

apt-installing packages
-----------------------

```sh
apt-get install git make build-essential libpam-dev ntp libcurl4-openssl-dev quota
```

As we are going to use secured subscription subsystem (that includes anti-replay-attacks mesaures) we need synchronized-clocks (that is why ntp daemon is installed)

/etc/nsswitch.conf and /etc/pam.d/ssh
-------------------------------------

we need to extend our uid/gid mappings (and the pam subsystem) to support the container-based setup.

First step is /etc/nsswitch.conf

```sh
git clone https://github.com/unbit/nss-unbit
cd nss-unbit
# run make as root or with sudo
make
```

now edit /etc/nsswitch.conf and update passwd, group and shadow to use the 'unbit' engine

```sh
passwd:         compat unbit
group:          compat unbit
shadow:         compat unbit
...
```

Now it's the pam time:

```sh
git clone https://github.com/unbit/pam-unbit
cd pam-unbit
# run make as root or with sudo
make
```

then edit /etc/pam.d/sshd and below the

```sh
session    required     pam_env.so user_readenv=1 envfile=/etc/default/locale
```

line, add


```sh
session    required     pam_unbit.so
```


Preparing the filesystem
------------------------

now we need to create a set of directories (as root)

```sh
# used for containers homes
mkdir /containers
# used for storing various distributions rootfs
mkdir /distros
# fake mountpoint for namespaces
mkdir /ns
# uwsgi tree
mkdir -p /opt/unbit/uwsgi/plugins
# uwsgi configuration
mkdir /etc/uwsgi
mkdir /etc/uwsgi/vassals
mkdir /etc/uwsgi/domains
mkdir /etc/uwsgi/ssl

# for logging
mkdir /var/log/uwsgi
```

Building uwsgi.it
-----------------

```sh
git clone https://github.com/unbit/uwsgi.it
cd uwsgi.it
cp emperor.conf /etc/init
cp -R services /etc/uwsgi
cp collector.pl configurator.pl dominator.pl /etc/uwsgi/
```

Configuring /etc/uwsgi/local.ini
--------------------------------

```ini
[uwsgi]
public_ip = x.x.x.x
api_domain = example.com
; additional options
env = LANG=en_US.UTF-8
```

Building uWSGI
--------------



The first distro
----------------

The first vassal
----------------

The firewall
------------

udp port 999 is the tuntap remote gateway, its access must be allowed only from the infrastrcture nodes and from port 999 (it is a privileged port so it should be a pretty good protection)

node1 = 1.1.1.1
node2 = 2.2.2.2
node3 = 3.3.3.3

on node1:

```sh
iptables -A INPUT -d 1.1.1.1 -p udp --dport 999 --sport 999 -s 2.2.2.2 -J ACCEPT
iptables -A INPUT -d 1.1.1.1 -p udp --dport 999 --sport 999 -s 3.3.3.3 -J ACCEPT
iptables -A INPUT -d 1.1.1.1 -p udp --dport 999 -J DROP
```

ports 22, 80 and 443 are for public access, there is no need to protect them in a particular way

port udp 123 is for ntp services, default ubuntu policies already protect them at the application level.

port 998 is the fastrouter one it binds itself to udp port 2000 for forwarding subscription to the legion-based http routers (for clustering). As for the tuntp router we can protect legion's subscription server to accept requests only from source port 2000.

The legion subsystem is used for clustering, as tuntap and subscriptions we only need to ensure that udp packets have source port == to the destination one (each legion should get a port >= 2100)

Last port to protect is 998 TCP used by the fastrouter. This things are a bit more complex:

we need to avoid containers to access it

we need to avoid external networks to access it

we need to allow ONLY legion-based http routers to access it

Install the api server - Only for the API node -
------------------------------------------------

The API server runs in a container as all of the other apps. It is a simple django app answering requests from emperor daemons (configurator, collector and dominator) and from customers.

Data of customers and containers (as well as servers and their topology) can be stored in a SQL database. (we strongly suggest postgresql for it).

You can run the app on one of the nodes or on an external ones. You can eventually distribute it.

SSL certificates
----------------

We will generate SSL certificates in the /etc/uwsgi/ssl directory


Clustering
----------

