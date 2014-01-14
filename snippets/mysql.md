Running MySQL
-------------

For Saucy Salamander:

create ~/.my.cnf (substitute XXXXX with your container uid)
```
[mysqld]
pid-file        = /containers/XXXXX/db.mysql/mysqld.pid
socket          = /containers/XXXXX/db.mysql/mysqld.sock
datadir         = /containers/XXXXX/db.mysql
character-set-server=utf8

[client]
socket          = /containers/XXXXX/db.mysql/mysqld.sock
```

run

```
mysql_install_db --defaults-file=.my.cnf
```

create vassals/mysql.ini

```
[uwsgi]
smart-attach-daemon = $(HOME)/db.mysql/mysqld.pid mysqld --defaults-file=$(HOME)/.my.cnf
```

Check logs/emperor.log, if all goes well you can start using mysql normally (remember to assign a root password)
