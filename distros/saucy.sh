set -u
set -e
debootstrap --components=main,universe,multiverse --include=vim,build-essential,git,redis-server,lua5.1,postgresql,libpq-dev,python-dev,python3-dev,memcached,mongodb,libperl-dev,ruby2.0,ruby2.0-dev,wget,language-pack-en,libcurl4-openssl-dev,mysql-server,libyajl-dev,beanstalkd,ssh,rsync,libluajit-5.1-dev,curl,ipython,liblocal-lib-perl,python-virtualenv,python-pip,libpcre3-dev,libjansson-dev,quota,gawk,libreadline6-dev,libyaml-dev,libsqlite3-dev,sqlite3,autoconf,libgdbm-dev,libncurses5-dev,automake,libtool,bison,libffi-dev,libphp5-embed,php5-memcached,php5-memcache,php5-json,php5-mysql,php5-gd,php5-pgsql,php5-dev,libxml2-dev,libdb-dev,libbz2-dev,libjpeg-dev,libpng12-dev,ruby-rack,postgresql-contrib,postgis,libxslt-dev,libsphinxclient-dev,sphinxsearch,libmysqlclient-dev,imagemagick,libgraphicsmagick1-dev,libgraphicsmagick++1-dev,libmagick++-dev,libmagickcore-dev,libmagickwand-dev,libreoffice,tesseract-ocr,tesseract-ocr-ita,pdftk,wkhtmltopdf,graphicsmagick,poppler-utils,ghostscript,language-pack-it,language-pack-de,language-pack-es,language-pack-pt,language-pack-pl,nullmailer,nodejs,nano,htop,emacs,mercurial,screen,apache2-utils,unzip,erlang-nox,libdatetime-perl,libmemcached-dev,libapache2-svn,libapache2-mod-gnutls,apache2-mpm-prefork,libapache2-mod-xsendfile,libapache2-mod-php5,php-pear,db5.1-util,libcap2-bin,libcap2-dev,libode-dev,gettext,libapache2-mod-rpaf,graphviz,ffmpeg,postgresql-9.1-postgis,proj-bin,e2fslibs-dev,bind9-host,php5-curl,bc,openjdk-7-jdk,openjdk-6-jdk,tmux,php5-mcrypt,php5-intl,php5-xcache,php5-imap,php5-sqlite,mc,zip,xmlsec1,libxmlsec1-dev saucy /distros/saucy
chroot /distros/saucy /bin/bash -x <<'EOF'
set -u
set -e
echo "exit 101" > /usr/sbin/policy-rc.d
chmod 755 /usr/sbin/policy-rc.d
mkdir /.old_root
rm /etc/mtab
ln -s /proc/self/mounts /etc/mtab
mkdir /containers
mkdir -p /opt/unbit/uwsgi/plugins
rm /etc/hosts /etc/hostname
ln -s /run/resolvconf/hostname /etc/hostname
ln -s /run/resolvconf/hosts /etc/hosts
cd /root
git clone https://github.com/unbit/nss-unbit
cd nss-unbit
make
EOF
cp nsswitch.conf /distros/saucy/etc/nsswitch.conf
cp shortcuts.ini /distros/saucy/opt/unbit/uwsgi/shortcuts.ini
