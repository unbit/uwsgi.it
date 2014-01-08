set -u
set -e
debootstrap --components=main,universe,multiverse --include=vim,build-essential,git,redis-server,lua5.1,postgresql,libpq-dev,python-dev,python3-dev,memcached,mongodb,libperl-dev,ruby,wget,ruby-dev,language-pack-en,libcurl4-openssl-dev,mysql-server,libyajl-dev,beanstalkd,ssh,rsync,libluajit-5.1-dev,curl,ipython,liblocal-lib-perl,python-virtualenv,python-pip,libpcre3-dev,libjansson-dev precise /distros/precise
chroot /distros/precise /bin/bash -x <<'EOF'
set -u
set -e
mkdir /.old_root
mkdir /containers
mkdir -p /opt/unbit/uwsgi/plugins
cp shortcuts.ini /opt/unbit/uwsgi/shortcuts.ini
rm /etc/hosts /etc/hostname
ln -s /run/resolvconf/hostname /etc/hostname
ln -s /run/resolvconf/hosts /etc/hosts
cd /root
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
EOF
cp nsswitch.conf /distros/precise/etc/nsswitch.conf
