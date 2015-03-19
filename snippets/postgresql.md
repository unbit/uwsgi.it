Running PostgreSQL
------------------

For Saucy Salamander:

```sh
/usr/lib/postgresql/9.1/bin/initdb -A md5 -U postgres -W -D db.pg -E UTF-8
mkdir /run/postgresql
```

For Trusty:

```sh
/usr/lib/postgresql/9.3/bin/initdb -A md5 -U postgres -W -D db.pg -E UTF-8
mkdir /run/postgresql
```


create vassals/pg.ini (change 9.1 to 9.3 on trusty)

```ini
[uwsgi]
pg = $(HOME)/db.pg
smart-attach-daemon = %(pg)/postmaster.pid /usr/lib/postgresql/9.1/bin/postgres -D %(pg)
```

check logs/emperor.log, if all goes well your postgresql instance should be started and you can use it normally

Bonus: auto-backup
------------------

use the cron facilities to run automatic dump of your db.

The following example will create a dump every day of the month (be sure to create a backup directory in your home):

(as before, remember to change 9.1 to 9.3 for trusty)

```ini
[uwsgi]
pg = $(HOME)/db.pg
smart-attach-daemon = %(pg)/postmaster.pid /usr/lib/postgresql/9.1/bin/postgres -D %(pg)

; backup
env = PGPASSWORD=XXX
cron = 59 3 -1 -1 -1  pg_dump -U ZZZ YYY |bzip2 -9 > $(HOME)/backup/YYY_`date +"%%d"`.sql.bz2
```

change XXX with your db password, ZZZ with the username and YYY with the db name

Super Bonus: master-slave replication
-------------------------------------

Requirements: two linked containers (hey, do not forget to 'link' them, if you do not know what linking is, check the customer quickstart, but technically linking is simply allowing network access between containers)

On the master container:

postgresql.conf

```

```

creating the replica role (from the psql shell)


```sql
CREATE USER replicator REPLICATION LOGIN ENCRYPTED PASSWORD 'foobar';
```

rsync data directory

restarting the master

On the slave container:

postgresql.conf

recovery.conf

start the slave

###### electing the slave as master

If your master goes down (for whatever reason) you may want your slave (that is readonly, remember) to became the new master (with write capability). To force a slave to became a master, you just need to 'create' the 'trigger file'.



