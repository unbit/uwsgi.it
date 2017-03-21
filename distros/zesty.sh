set -u
set -e
debootstrap --components=main,universe,multiverse --include=vim,build-essential,git,redis-server,lua5.1,postgresql,libpq-dev,python-dev,python3-dev,memcached,mongodb,libperl-dev,ruby,ruby-dev,wget,language-pack-en,libcurl4-openssl-dev,mysql-server,libyajl-dev,beanstalkd,ssh,rsync,libluajit-5.1-dev,curl,ipython,liblocal-lib-perl,python-virtualenv,python-pip,libpcre3-dev,libjansson-dev,quota,gawk,libreadline-dev,libyaml-dev,libsqlite3-dev,sqlite3,autoconf,libgdbm-dev,libncurses5-dev,automake,libtool,bison,libffi-dev,libphp7.0-embed,php7.0-json,php7.0-mysql,php7.0-gd,php7.0-pgsql,php7.0-dev,libxml2-dev,libdb-dev,libbz2-dev,libjpeg-dev,libpng-dev,ruby-rack,postgresql-contrib,postgis,libxslt1-dev,sphinxsearch,libmysqlclient-dev,imagemagick,libgraphicsmagick1-dev,libgraphicsmagick++1-dev,libmagick++-dev,libmagickcore-dev,libmagickwand-dev,libreoffice,tesseract-ocr,tesseract-ocr-ita,pdftk,wkhtmltopdf,graphicsmagick,poppler-utils,ghostscript,language-pack-it,language-pack-de,language-pack-es,language-pack-pt,language-pack-pl,nullmailer,nodejs,nano,htop,emacs,mercurial,screen,apache2-utils,unzip,erlang-nox,libdatetime-perl,libmemcached-dev,libapache2-mod-svn,libapache2-mod-gnutls,libapache2-mod-xsendfile,libapache2-mod-php7.0,php-pear,libcap2-bin,libcap-dev,libode-dev,gettext,libreoffice-style-galaxy,libapache2-mod-rpaf,graphviz,strace,e2fslibs-dev,bind9-host,php7.0-curl,bc,pastebinit,tmux,php7.0-mcrypt,php7.0-intl,php7.0-imap,mc,zip,xmlsec1,libxmlsec1-dev,attr,acl,libssh2-1-dev,libkrb5-dev,python3-virtualenv,libgeo-ip-perl,virtualenv,subversion,ftp,libgeoip-dev,libattr1-dev,telnet,npm,golang,couchdb,erlang,ffmpeg,unoconv,libfl-dev,libzmq3-dev,php7.0-xsl,libdbd-pg-perl,libdbd-mysql-perl,openjdk-8-jdk,node-clean-css,node-less,apache2,apache2-dev,php-mbstring,virtualenvwrapper,python-setuptools,postgresql-9.6-postgis,net-tools,python3.6-dev,python3.6-venv zesty /distros/zesty
chroot /distros/zesty /bin/bash -x <<'EOF'
set -u
set -e
dpkg-reconfigure tzdata
echo "exit 101" > /usr/sbin/policy-rc.d
chmod 755 /usr/sbin/policy-rc.d
mkdir /.old_root
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
cp nsswitch.conf /distros/zesty/etc/nsswitch.conf
cp shortcuts.ini /distros/zesty/opt/unbit/uwsgi/shortcuts.ini
