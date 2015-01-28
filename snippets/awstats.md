Awstats
=======

ensure your app/domain logs in the apache format:


http://uwsgi-docs.readthedocs.org/en/latest/LogFormat.html#apache-style-combined-request-logging


This will run awstats under /awstats (it assumes awstats is untar'ed under $(HOME)/awstats/awstats-7.3)

```ini
plugin = router_basicauth, cgi
; map static resources
static-map = /awstats/icon=$(HOME)/awstats/awstats-7.3/wwwroot/icon
; authentication
route = ^/awstats basicauth:awstats,test:test
; map /awstats as cgi script
cgi = /awstats=$(HOME)/awstats/awstats-7.3/wwwroot/cgi-bin/awstats.pl
; force requests to /awstats to be managed by the cgi plugin (modifier 9)
route = ^/awstats setmodifier1:9

; update stats every hour (remember to create a config for 'domain')
cron = 59 -1 -1 -1 -1 $(HOME)/awstats/awstats-7.3/wwwroot/cgi-bin/awstats.pl -config=domain -update

```

