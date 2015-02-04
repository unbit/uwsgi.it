uwsgi.it Changelog
==================

[20150204]

* added mem.rss and mem.cache metrics

[20141116]

* added support for HTTPS/sni certificate authentication (https://github.com/unbit/uwsgi.it/blob/master/CustomerQuickstart.md#client-certificates-httpssni-authentication)

[20141115]

* updated to uWSGI 2.0.9
* added pushover (https://pushover.net/) support (alarms api)
* added alarm_freq field (alarms api)
* do not regenerate uwsgi_authorized_keys on container restart (the configurator will do it)
* added high-performance pipe mode for the http router (example usage: https://github.com/unbit/uwsgi.it/blob/master/snippets/apache.md#high-performance-mode-pipe)
