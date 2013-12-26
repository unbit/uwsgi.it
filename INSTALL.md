Step by step guide for installing a uwsgi.it node
-------------------------------------------------

This procedure assumes an x86_64 Ubuntu 13.10 server system (ubuntu-minimal)

/etc/default/grub
-----------------

First step is ensuring the kernel io scheduler (elevator) is set to cfq (ubuntu enforces it to deadline):

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

