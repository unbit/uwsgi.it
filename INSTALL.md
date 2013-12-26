Step by step guide for installing a uwsgi.it node
-------------------------------------------------

This procedure assumes an x86_64 Ubuntu 13.10 server (ubuntu-minimal) with ext4 filesystem.

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

Now be ABSOLUTELY sure to set your .ssh/authorized_keys in the account you are currently using to log-in (otherwise you will not be able to log-in back via ssh).

test if you can login with your key and then restart your ssh service:

```sh
service ssh restart
```

apt-installing packages
-----------------------

```sh
apt-get install git make build-essential libpam-dev
```

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
```

SSL certificates
----------------

We will generate SSL certificates in the /etc/uwsgi/ssl directory

Building uWSGI
--------------

Building uwsgi.it
-----------------

Configuring /etc/uwsgi/local.ini
--------------------------------

The first distro
----------------

The first vassal
----------------
