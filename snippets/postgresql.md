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
