Memcached
=========

just choose the amount of memory to use (-m flag, in megabytes)

```ini
[uwsgi]
smart-attach-daemon = /run/memcached.pid memcached -m 128 -d -P /run/memcached.pid
```
