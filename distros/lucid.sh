set -u
set -e
debootstrap --components=main,universe,multiverse --include=build-essential,git-core,redis-server,lua5.1,postgresql,libpq-dev,python-dev,python3-dev,memcached,mongodb,libperl-dev,ruby,wget,ruby-dev,language-pack-en,libcurl4-openssl-dev,mysql-server,libyajl-dev,beanstalkd,ssh,rsync,libluajit-5.1-dev,curl,irb,ruby1.9-dev,ipython,liblocal-lib-perl,python-virtualenv,python-pip,libpcre3-dev,mercurial lucid /distros/lucid
chroot /distros/lucid /bin/bash -x <<'EOF'
mkdir /.old_root
mkdir /containers
mkdir -p /opt/unbit/uwsgi/plugins
cd /root
git clone https://github.com/unbit/uwsgi
cd uwsgi
UWSGI_PROFILE_OVERRIDE='json=yajl' make uwsgi.it
cp uwsgi /opt/unbit/uwsgi/uwsgi
EOF
