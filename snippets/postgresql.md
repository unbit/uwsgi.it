Running PostgreSQL
------------------

From Precise Pangolin (Ubuntu 12.04 LTS) to Saucy Salamander (Ubuntu 13.10):

```sh
/usr/lib/postgresql/9.1/bin/initdb -A md5 -U postgres -W -D db.pg -E UTF-8
mkdir /run/postgresql
```

From Trusty Tahr (Ubuntu 14.04 LTS) to Wily Werewolf (Ubuntu 15.10):

```sh
/usr/lib/postgresql/9.3/bin/initdb -A md5 -U postgres -W -D db.pg -E UTF-8
mkdir /run/postgresql
```
For Xenial Xerus (Ubuntu 16.04 LTS):

```sh
/usr/lib/postgresql/9.5/bin/initdb -A md5 -U postgres -W -D db.pg -E UTF-8
mkdir /run/postgresql
```

create `vassals/pg.ini` (change 9.1, 9.3 or 9.5)

```ini
[uwsgi]
pg = $(HOME)/db.pg
smart-attach-daemon = %(pg)/postmaster.pid /usr/lib/postgresql/9.5/bin/postgres -D %(pg)
```

check `logs/emperor.log`, if all goes well your postgresql instance should be started and you can use it normally

Bonus: auto-backup
------------------

use the cron facilities to run automatic dump of your db.

The following example will create a dump every day of the month (be sure to create a backup directory in your home):

(as before, remember to change 9.1, 9.3 or 9.5)

```ini
[uwsgi]
pg = $(HOME)/db.pg
smart-attach-daemon = %(pg)/postmaster.pid /usr/lib/postgresql/9.5/bin/postgres -D %(pg)

; backup
env = PGPASSWORD=XXX
cron = 59 3 -1 -1 -1  pg_dump -U ZZZ YYY |bzip2 -9 > $(HOME)/backup/YYY_`date +"%%d"`.sql.bz2
```

change XXX with your db password, ZZZ with the username and YYY with the db name

Super Bonus: master-slave replication
-------------------------------------

Requirements: two linked containers (hey, do not forget to 'link' them, if you do not know what linking is, check the customer quickstart, but technically linking is simply allowing network access between containers).

The slave container MUST NOT be configured with postgres (read: the db.pg directory or the vassal file must not be created, see below).

###### on the master container:

edit db.pg/postgresql.conf (adapt listen_address directive with the internal ip address of your container, and ensure the other options are set)

```
listen_addresses = 'localhost,10.X.X.X'
max_wal_senders = 3
checkpoint_segments = 8
wal_keep_segments = 8
wal_level = hot_standby
```

create the replica role (from the psql shell)


```sql
CREATE USER replicator REPLICATION LOGIN ENCRYPTED PASSWORD 'foobar';
```

(change 'foobar' to whatever you want)

and add a rule for it in the pg_hba.conf

```
host	replication	replicator	10.Y.Y.Y/32		md5
```

(change 10.Y.Y.Y with the address of the slave container)

now you can restart the master (but soon after ensure no process will write to it, as we need the first sync with the slave):

```sh
mv vassals/pg.ini vassals/pg.off
/usr/lib/postgresql/9.3/bin/pg_ctl stop -D db.pg
mv vassals/pg.off vassals/pg.ini
```

###### on the slave container

the first step is making a 1:1 copy of the master in the db.pg directory (using the previously created replicator user)

```sh
pg_basebackup -h 10.X.X.X -D db.pg -U replicator -P -v -x
```

( change 10.X.X.X with the master container ip).

After few seconds you should end with an exact copy of the master's db.pg in the slave server.

Now edit db.pg/postgresql.conf and change listen_address to bind to the slave address, and the following line:

```
hot_standby = on
```

Change db.pg/pg_hba.conf line for the replicator user with the master's ip address. and finally create a db.pg/recovery.conf file:

```
standby_mode = 'on'
primary_conninfo = 'host=10.X.X.X port=5432 user=replicator password=YYY'
trigger_file = '/run/postgresql.trigger'
```

change 10.X.X.X with the master ip and YYY with the replicator password.

Now you can start the slave (you can use the same vassals/pg.ini of the master an copy it in the slave vassal's dir)

Check its logs, if all goes well you should see something like this:

```
LOG:  started streaming WAL from primary at XXXX
```

###### electing the slave as master

If your master goes down (for whatever reason) you may want your slave (that is readonly, remember) to became the new master (with write capability). To force a slave to became a master, you just need to 'create' the 'trigger file'.

```sh
touch /run/postgresql.trigger
```

this will put the slave in "writable" mode, and will rename recovery.done (renaming it will allow the slave to continue to be writable/master even if the slave is rebooted). Now ensure your apps start pointing to the slave address.

###### ... when the master is back

... do not suddenly revert your app to point to the master !!! your master is very probbaly out of sync (read: the slave has newer data)

Make a copy of the whole db.pg (well, technically you only need to copy db.pg/postgresql.conf and db.pg/pg_hba.conf, but backups are always good), remove it and resync from the master:

* ensure postgresql is off

```
mv vassals/pg.ini vassals/pg.off
/usr/lib/postgresql/9.3/bin/pg_ctl stop -D db.pg
```

* make a copy of db.pg

```sh
cp -R db.pg db.pg.backup
```

* remove db.pg

```sh
rm -rf db.pg
```

and resync with the slave

```sh
pg_basebackup -h 10.Y.Y.Y -D db.pg -U replicator -P -v -x
```

(change 10.Y.Y.Y with slave address)

put back postgresql.conf and pg_hba.conf

```sh
cp db.pg.backup/postgresql.conf db.pg/
cp db.pg.backup/ph_hba.conf db.pg/
```

and restart postgresql:

```sh
mv vassals/pg.off vassals/pg.ini
```

Now your master is ready again, but we need to set back the slave as a replica (it is still in writable state):

```
mv db.pg/recovery.done db.pg/recovery.conf
mv vassals/pg.ini vassals/pg.off
/usr/lib/postgresql/9.3/bin/pg_ctl stop -D db.pg
mv vassals/pg.off vassals/pg.ini
```

Congratulations, all is fine again, you can start pointing your apps back to the master.

Note: it could happen that the slave updates its data while you bring up the old master. In such a case the master will not be able to synchronize spitting out an error like:

```
FATAL:  highest timeline X of the primary is behind recovery timeline Y
```

to fix it, just resync-back the slave with the master (read: run pg_basebackup on the slave)
