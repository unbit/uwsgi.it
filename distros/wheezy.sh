set -u
set -e
debootstrap --components=main --include=vim,build-essential,git,redis-server,lua5.1,postgresql,libpq-dev,python-dev,python3-dev,memcached,mongodb,libperl-dev,wget,libcurl4-openssl-dev,mysql-server,libyajl-dev,beanstalkd,ssh,rsync,curl,ipython,liblocal-lib-perl,python-virtualenv,python-pip,libpcre3-dev,libjansson-dev,quota,gawk,libreadline6-dev,libyaml-dev,libsqlite3-dev,sqlite3,autoconf,libgdbm-dev,libncurses5-dev,automake,libtool,bison,libffi-dev,libphp5-embed,php5-memcached,php5-memcache,php5-mysql,php5-pgsql,php5-dev,libxml2-dev,libdb-dev,libbz2-dev,libjpeg8-dev,libpng12-dev,ruby-rack,postgresql-contrib,postgis,libxslt1-dev,libmysqlclient-dev,imagemagick,libgraphicsmagick1-dev,libgraphicsmagick++1-dev,libmagick++-dev,libmagickcore-dev,libmagickwand-dev,tesseract-ocr,tesseract-ocr-ita,pdftk,wkhtmltopdf,graphicsmagick,poppler-utils,ghostscript,nullmailer,nano,htop,emacs,ruby1.9.1-dev,libqdbm-dev,libonig-dev,mercurial,screen,apache2-utils,unzip,erlang-nox,libdatetime-perl,telnet,libmemcached-dev,libapache2-svn,libapache2-mod-gnutls,apache2-mpm-prefork,libapache2-mod-xsendfile,libapache2-mod-php5,php-pear,db5.1-util,libcap2-bin,libcap2-dev,libode-dev,gettext,libapache2-mod-rpaf,graphviz,ffmpeg,postgresql-9.1-postgis,proj-bin,e2fslibs-dev,bind9-host wheezy /distros/wheezy
chroot /distros/wheezy /bin/bash -x <<'EOF'
set -u
set -e
mkdir /.old_root
mkdir /containers
mkdir -p /opt/unbit/uwsgi/plugins
rm /etc/hosts /etc/hostname
ln -s /run/resolvconf/hostname /etc/hostname
ln -s /run/resolvconf/hosts /etc/hosts
cd /root
GIT_SSL_NO_VERIFY=1 git clone https://github.com/unbit/nss-unbit
cd nss-unbit
make
cd ..
EOF
cp nsswitch.conf /distros/wheezy/etc/nsswitch.conf
cp shortcuts.ini /distros/wheezy/opt/unbit/uwsgi/shortcuts.ini
