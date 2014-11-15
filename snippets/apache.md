Running apache instances
========================

Distributions: precise,saucy,wheezy,trusty

In some (really rare) case you may need to install an apache instance (heavily .htaccess based instances, mod_svn, mod_php ...)

Installation
============

Ensure your $(HOME)/etc/hosts has an entry for your server name

```sh
cp -R /etc/apache2 $HOME/etc
mkdir /var/log/apache2
mkdir -p /run/lock/apache2
```

Configuration
=============

Edit $HOME/etc/apache2/ports.conf to bind on unprivileged ports (like 8080) and remove ssl/gnutls modules from mods-enabled directory (if any)

Edit $HOME/etc/apache2/sites-enabled/000-default to set your DocumentRoot

Running it
==========

Use this vassal as your base configuration (for precise and wheezy)

```ini
[uwsgi]
; register the domains you need
domain = example.com
domain = example2.com
domain = .foo.bar

; load the http proxy router
plugins = router_http
offload-threads = 2
; forward requests to apache
route-run = http:127.0.0.1:8080
; monitor the apache instance
smart-attach-daemon = /run/apache2.pid apache2ctl -k start -d $(HOME)/etc/apache2
```

and this one for saucy or trusty

```ini
[uwsgi]
; register the domains you need
domain = example.com
domain = example2.com
domain = .foo.bar

; load the http proxy router
plugins = router_http
offload-threads = 2
; forward requests to apache
route-run = http:127.0.0.1:8080
; monitor the apache instance
env = APACHE_CONFDIR=$(HOME)/etc/apache2
smart-attach-daemon = /run/apache2/apache2.pid apache2ctl -k start
```

to reload the instance on precise and wheezy

```sh
apache2ctl -k restart -d $HOME/etc/apache2
```

on saucy and trusty

```sh
APACHE_CONFDIR=$HOME/etc/apache2 apache2ctl -k restart
```

High performance mode (pipe)
============================

As apache is a fully featured webserver, you can configure the proxy to be less smart about data received, and to
blindly forward everything it receives. This will give you a performance boost as true keep-alive will be accomplished. To enable this mode you need to change the router from http to 'httpdumb' (it will not transform the request to an HTTP/1.0) and subscribe domains with the special/magic code 123 (when the http router sees it it put itself in raw mode):

```ini
[uwsgi]
; register the domains you need
domain = example.com
domain = example2.com
domain = .foo.bar

; load the http proxy router
plugins = router_http
offload-threads = 2

; instruct the http router to go in raw mode

subscribe-with-modifier1 = 123

; forward requests to apache in dumb mode
route-run = httpdumb:127.0.0.1:8080
; monitor the apache instance
env = APACHE_CONFDIR=$(HOME)/etc/apache2
smart-attach-daemon = /run/apache2/apache2.pid apache2ctl -k start
```

Logrotate
=========

```sh
/var/log/apache2/*.log {
        weekly
        missingok
        rotate 52
        compress
        delaycompress
        notifempty
        create 640
        sharedscripts
        postrotate
                APACHE_CONFDIR=$HOME/etc/apache2 apache2ctl -k restart
        endscript
}
```

```ini
cron = 59 5 -1 -1 -1 logrotate -s /run/logrotate.state $(HOME)/etc/apache2.logrotate.conf
```

Common pitfalls
===============

Your configurations like in $HOME/etc/apache2 NOT /etc/apache2 !!! (if you get permission errors, very probably you are in the wrong dir)

If you need to install untrusted apps with an high vulnerability potential, consider installing apache instances in dedicated containers linked to the one working as proxy (and registering domains). In such a case you only need to set the http backend address to the 10.x.x.x one
