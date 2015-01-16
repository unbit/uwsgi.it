Running Redis
-------------


Simple mode
-----------

```ini
[uwsgi]
attach-daemon = redis-server
```


this will simply bind redis to 127.0.0.1:6379


Smart mode
----------

```sh
cp /etc/redis/redis.conf $HOME/etc/redis.conf
```

Open `$HOME/etc/redis.conf` with your preferred editor. Replace the following lines:

```
pidfile /var/run/redis/redis-server.pid
logfile /var/log/redis/redis-server.log
dir     /var/lib/redis
```

with (replace `[HOME]` with your home path)

```
pidfile [HOME]/run/redis-server.pid
logfile [HOME]/logs/redis-server.log
dir     [HOME]
```

Create vassals/redis.ini

```ini
[uwsgi]
smart-attach-daemon = $(HOME)/run/redis-server.pid /usr/bin/redis-server $(HOME)/etc/redis.conf
```

check logs/emperor.log, if all goes well your redis instance should be started and you can use it normally
