Running MongoDB
---------------

For Saucy Salamander

```sh
mkdir db.mongo
```

create vassals/mongodb.ini

```ini
[uwsgi]
mongopath = $(HOME)/db.mongo
smart-attach-daemon = %(mongopath)/mongod.pid mongod --dbpath %(mongopath)
```

check logs/emperor.log for mongod startup logs
