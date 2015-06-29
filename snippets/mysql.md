Running MySQL
-------------

For Saucy, Trusty and Utopic:

create ~/.my.cnf (substitute XXXXX with your container uid)
```ini
[mysqld]
pid-file        = /containers/XXXXX/db.mysql/mysqld.pid
socket          = /containers/XXXXX/db.mysql/mysqld.sock
datadir         = /containers/XXXXX/db.mysql
character-set-server=utf8

[client]
socket          = /containers/XXXXX/db.mysql/mysqld.sock
```

Note: if you need to import dumps with very large column values add the following line in the [mysqld] section:

```ini
max_allowed_packet = 16M
```

run

```sh
mysql_install_db --defaults-file=.my.cnf
```

and (for allowing transparent compatibility with debian/ubuntu mysql environment)

```
ln -s $HOME/db.mysql /var/run/mysqld
```

create vassals/mysql.ini

```ini
[uwsgi]
smart-attach-daemon = $(HOME)/db.mysql/mysqld.pid,180 mysqld --defaults-file=$(HOME)/.my.cnf
```

Check logs/emperor.log, if all goes well you can start using mysql normally (remember to assign a root password)

What is that '180' after the pidfile ?
--------------------------------------

By default the daemons manager ensures up to 10 times that the external process daemonized. (this is about 10 seconds of retries). Unfortunately if you have corruptions, the amount of time required for a repair could be way bigger. That '180' instructs the master to retries up to 180 times (about 3 minutes) before giving up.

Backup
------

```perl
#!/usr/bin/env perl

use strict;
use warnings;
use DBI ;
use DateTime ;

######### Configure here
#
my %cfg = (
        username  => 'root',                             # user (generally 'root')
        password  => 'XXXX',                  # Password
        backupDir => $ENV{HOME}.'/backup_mysql',        # where to store backups
);

######### DO NOT CHANGE BELOW !!!

umask 0027;

mkdir $cfg{'backupDir'} unless -d $cfg{'backupDir'};

my $dbh = DBI->connect( "dbi:mysql:database=mysql", $cfg{'username'}, $cfg{'password'} );
my $sth = $dbh->prepare( "SHOW DATABASES" );

if ( $sth->execute >=1 ) {
        my $dt = DateTime->now;
        my $day =  $dt->day_of_month;
        while( my $row = $sth->fetchrow_hashref ) {
                my $db = $row->{Database};
                next if $db eq 'information_schema';
                next if $db eq 'performance_schema';
                mkdir $cfg{'backupDir'} . '/' . $db unless -d $cfg{'backupDir'} . '/'. $db;
                my $cmd = "mysqldump --defaults-file=" .$ENV{HOME}. "/.my.cnf -u " . $cfg{'username'} . " -p". $cfg{'password'} . " " . $db . " | bzip2 -9 > " . $cfg{'backupDir'} . '/'. $db . "/" . $day . ".bz2";
                system ( $cmd );
        }
}
```

save it as `mysql_backup.pl` and run it via uWSGI cron:

```ini
[uwsgi]
smart-attach-daemon = $(HOME)/db.mysql/mysqld.pid mysqld --defaults-file=$(HOME)/.my.cnf
cron = 59 3 -1 -1 -1 perl $(HOME)/mysql_backup.pl
```
