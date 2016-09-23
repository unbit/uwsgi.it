Step by step guide for installing a uwsgi.it node
-------------------------------------------------

This procedure assumes an x86_64 Ubuntu 14.04 server (ubuntu-minimal) with ext4 filesystem or an x86_64 Ubuntu 16.04 server (ubuntu-minimal)

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

If you do not plan to use ipv6, it is better to fully disable it

```sh
GRUB_CMDLINE_LINUX_DEFAULT="nomodeset elevator=cfq ipv6.disable=1"
```

and re-run

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
/dev/md/2 / ext4 defaults,noatime,usrjquota=aquota.user,jqfmt=vfsv1 0 0
...
```

in this example /dev/md2 will store customer's file so we add `noatime,usrjquota=aquota.user,jqfmt=vfsv1` to its options

Finally add the cgroup line if you are on Trusty (not required for Xenial):

```sh
...
/dev/md/2 / ext4 defaults,noatime,usrjquota=aquota.user,jqfmt=vfsv1 0 0
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
AuthorizedKeysFile %h/.ssh/authorized_keys %h/.ssh/uwsgi_authorized_keys %h/.ssh/authorized_keys2
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

Eventually fix ssh keys with 

```sh
ssh-keygen -A
```

apt-installing packages
-----------------------

```sh
apt-get install git make build-essential libpam-dev ntp libcurl4-openssl-dev quota libpcre3-dev libjansson-dev uuid-dev libexpat-dev libwww-perl libjson-perl libconfig-inifiles-perl libquota-perl telnet automake libcap2-dev libcap2-bin libtool tmux libssl-dev python pkg-config
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

then edit /etc/pam.d/sshd and below the line

```sh
session [success=ok ignore=ignore module_unknown=ignore default=bad]        pam_selinux.so close
```

add


```sh
session    requisite     pam_unbit.so
```

and comment (prefixing with a sharp) this three lines

```sh
session    optional     pam_motd.so  motd=/run/motd.dynamic noupdate
```

and

```sh
session    optional     pam_mail.so standard noenv # [1]
```

and

```sh
session    required     pam_env.so user_readenv=1 envfile=/etc/default/locale
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
# directory for subscription sockets
mkdir /subscribe
chown www-data:www-data /subscribe
# uwsgi tree
mkdir -p /opt/unbit/uwsgi/plugins
# uwsgi configuration
mkdir /etc/uwsgi
mkdir /etc/uwsgi/vassals
mkdir /etc/uwsgi/domains
chown www-data:www-data /etc/uwsgi/domains
mkdir /etc/uwsgi/ssl
# temprary store for dynamic ssl certificates
mkdir /etc/uwsgi/tmp_ssl
chown www-data:www-data /etc/uwsgi/tmp_ssl
chmod 700 /etc/uwsgi/tmp_ssl
# alarms store
mkdir /etc/uwsgi/alarms
chmod 777 /etc/uwsgi/alarms

# for logging
mkdir /var/log/uwsgi
chown root:www-data /var/log/uwsgi
chmod 770 /var/log/uwsgi
```

Building uwsgi.it
-----------------

```sh
git clone https://github.com/unbit/uwsgi.it
cd uwsgi.it
cp emperor.conf /etc/init
cp emperor.ini /etc/uwsgi
cp -R services /etc/uwsgi
mkdir /etc/uwsgi/custom_services
cp firewall.sh collector.pl configurator.pl dominator.pl loopboxer.pl /etc/uwsgi/
gcc -o /etc/uwsgi/loopbox loopbox.c
```

Configuring /etc/uwsgi/local.ini
--------------------------------

```ini
[uwsgi]
public_ip = x.x.x.x
api_domain = example.com
api_client_key_file = /etc/uwsgi/ssl/client.key
api_client_cert_file = /etc/uwsgi/ssl/client.crt

legion_key = XXXX
node_weight = 9999

; additional options
env = LANG=en_US.UTF-8
```

Building uWSGI
--------------

```sh
bash -x build_uwsgi.sh
```

SSL certificates
----------------

We will generate SSL certificates in the /etc/uwsgi/ssl directory, if you already have a valid key and a cert, copy them in /etc/uwsgi/ssl as uwsgi.it.key and uwsgi.it.crt. They will be used as the default ssl context for the https server.

Then you need a key/cert pair for authenticating with the api server.

Distros
-------

TODO


The firewall
------------

the firewall.sh script is automatically executes whenever a changes involving network security is made

Check the PORTS.md file to understand which ports are opened to the world and how they are proctected

Install the api server - Only for the API node -
------------------------------------------------

The API server is a simple django app answering requests from emperor daemons (configurator, collector and dominator) and from customers.

Data of customers and containers (as well as servers and their topology) can be stored in a SQL database. (we strongly suggest postgresql for it).

You can run the app on one of the nodes or on an external ones. You can eventually distribute it.


