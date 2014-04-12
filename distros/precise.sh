set -u
set -e
debootstrap --components=main,universe,multiverse --include=vim,build-essential,git,redis-server,lua5.1,postgresql,libpq-dev,python-dev,python3-dev,memcached,mongodb,libperl-dev,ruby,wget,ruby-dev,language-pack-en,libcurl4-openssl-dev,mysql-server,libyajl-dev,beanstalkd,ssh,rsync,libluajit-5.1-dev,curl,ipython,liblocal-lib-perl,python-virtualenv,python-pip,libpcre3-dev,libjansson-dev,quota,ruby1.9.1-dev,rubygems,ruby-bundler,libjpeg-dev,libpng12-dev,nullmailer,nano,htop,emacs,libxml2-dev,libxslt-dev,mercurial,language-pack-it,language-pack-de,language-pack-es,language-pack-pt,language-pack-pl,tmux,libreadline-dev,strace,libsasl2-dev,screen,apache2-utils,libtiff-dev,liblcms1-dev,e2fslibs-dev,unzip,erlang-nox,libdatetime-perl,telnet,libmemcached-dev,libapache2-svn,libapache2-mod-gnutls,apache2-mpm-prefork,libapache2-mod-xsendfile,libapache2-mod-php5,php-pear,db5.1-util,libcap2-bin,libcap2-dev,libode-dev precise /distros/precise
chroot /distros/precise /bin/bash -x <<'EOF'
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
UWSGICONFIG_RUBYPATH=/usr/bin/ruby1.9.1 /opt/unbit/uwsgi/uwsgi --build-plugin "plugins/rack rack2"
UWSGICONFIG_RUBYPATH=/usr/bin/ruby1.9.1 /opt/unbit/uwsgi/uwsgi --build-plugin plugins/fiber
UWSGICONFIG_RUBYPATH=/usr/bin/ruby1.9.1 /opt/unbit/uwsgi/uwsgi --build-plugin plugins/rbthreads
cp rack2_plugin.so fiber_plugin.so rbthreads_plugin.so /opt/unbit/uwsgi/plugins/
/opt/unbit/uwsgi/uwsgi --build-plugin plugins/router_basicauth
cp router_basicauth_plugin.so /opt/unbit/uwsgi/plugins
EOF
cp nsswitch.conf /distros/precise/etc/nsswitch.conf
cp shortcuts.ini /distros/precise/opt/unbit/uwsgi/shortcuts.ini
