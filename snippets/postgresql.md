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



