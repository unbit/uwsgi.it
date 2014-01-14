Running PostgreSQL
------------------

For Saucy Salamander:

```sh
/usr/lib/postgresql/9.1/bin/initdb -A md5 -U postgres -W -D db.pg -E UTF-8
mkdir /run/postgresql
```

create vassals/pg.ini

```ini
[uwsgi]
pg = $(HOME)/db.pg
smart-attach-daemon = %(pg)/postmaster.pid /usr/lib/postgresql/9.1/bin/postgres -D %(pg)
```

check logs/emperor.log, if all goes well your postgresql instance should be started and you can use it normally
