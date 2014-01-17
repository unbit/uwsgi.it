set -u
set -e
debootstrap --components=main,universe,multiverse --include=vim,build-essential,git,redis-server,lua5.1,postgresql,libpq-dev,python-dev,python3-dev,memcached,mongodb,libperl-dev,ruby2.0,ruby2.0-dev,wget,language-pack-en,libcurl4-openssl-dev,mysql-server,libyajl-dev,beanstalkd,ssh,rsync,libluajit-5.1-dev,curl,ipython,liblocal-lib-perl,python-virtualenv,python-pip,libpcre3-dev,libjansson-dev,quota,gawk,libreadline6-dev,libyaml-dev,libsqlite3-dev,sqlite3,autoconf,libgdbm-dev,libncurses5-dev,automake,libtool,bison,libffi-dev,libphp5-embed,php5-memcached,php5-memcache,php5-json,php5-mysql,php5-gd,php5-pgsql,php5-dev,libxml2-dev,libdb-dev,libbz2-dev,libjpeg-dev,libpng12-dev,ruby-rack,postgresql-contrib,postgis,libxslt-dev,libsphinxclient-dev,sphixsearch,libmysqlclient-dev,imagemagick,libgraphicsmagick1-dev,libgraphicsmagick++1-dev,libmagick++-dev,libmagickcore-dev,libmagickwand-dev saucy /distros/saucy
chroot /distros/saucy /bin/bash -x <<'EOF'
set -u
set -e
mkdir /.old_root
mkdir /containers
mkdir -p /opt/unbit/uwsgi/plugins
rm /etc/hosts /etc/hostname
ln -s /run/resolvconf/hostname /etc/hostname
ln -s /run/resolvconf/hosts /etc/hosts
cd /root
git clone https://github.com/unbit/nss-unbit
cd nss-unbit
make
cd ..
git clone https://github.com/unbit/uwsgi
cd uwsgi
make uwsgi.it
cp uwsgi /opt/unbit/uwsgi/uwsgi
/opt/unbit/uwsgi/uwsgi --build-plugin plugins/python
cp python_plugin.so /opt/unbit/uwsgi/plugins
PYTHON=python3 /opt/unbit/uwsgi/uwsgi --build-plugin "plugins/python python3"
cp python3_plugin.so /opt/unbit/uwsgi/plugins
/opt/unbit/uwsgi/uwsgi --build-plugin plugins/psgi
cp psgi_plugin.so /opt/unbit/uwsgi/plugins
/opt/unbit/uwsgi/uwsgi --build-plugin plugins/rack
cp rack_plugin.so /opt/unbit/uwsgi/plugins
/opt/unbit/uwsgi/uwsgi --build-plugin plugins/router_redirect
cp router_redirect_plugin.so /opt/unbit/uwsgi/plugins
/opt/unbit/uwsgi/uwsgi --build-plugin plugins/gevent
cp gevent_plugin.so /opt/unbit/uwsgi/plugins/
/opt/unbit/uwsgi/uwsgi --build-plugin plugins/fiber
/opt/unbit/uwsgi/uwsgi --build-plugin plugins/rbthreads
cp fiber_plugin.so rbthreads_plugin.so /opt/unbit/uwsgi/plugins/
/opt/unbit/uwsgi/uwsgi --build-plugin plugins/php
cp php_plugin.so /opt/unbit/uwsgi/plugins/
/opt/unbit/uwsgi/uwsgi --build-plugin plugins/router_basicauth
cp router_basicauth_plugin.so /opt/unbit/uwsgi/plugins/
git clone https://github.com/unbit/uwsgi-netlink
/opt/unbit/uwsgi/uwsgi --build-plugin uwsgi-netlink
cp netlink_plugin.so /opt/unbit/uwsgi/plugins/
EOF
cp nsswitch.conf /distros/saucy/etc/nsswitch.conf
cp shortcuts.ini /distros/saucy/opt/unbit/uwsgi/shortcuts.ini
