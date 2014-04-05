Running apache instances
========================

Distributions: precise,saucy,wheezy

Installation
============

```sh
cp -R /etc/apache2 $HOME/etc
mkdir /var/log/apache2
```

Configuration
=============

Edit $HOME/etc/apache2/ports.conf to bind on unprivileged ports (like 8080)
