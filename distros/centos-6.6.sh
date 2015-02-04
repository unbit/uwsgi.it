set -u
set -e
rinse --mirror http://mirror.centos.org/centos/6.6/os/x86_64/Packages/ --directory /distros/centos-6.6 --distribution centos-6.6 --pkgs-dir ./distros --arch amd64
chroot /distros/centos-6.6 /bin/bash -x <<'EOF'
set -u
set -e
yum update
yum install -y openssl-devel gcc make git curl ruby strace pcre-devel yajl-devel
mkdir -p /.old_root
mkdir -p /containers
mkdir -p /opt/unbit/uwsgi/plugins
cd /root
git clone --branch uwsgi-2.0 https://github.com/unbit/uwsgi
cd uwsgi
UWSGI_PROFILE_OVERRIDE="json=yajl" make uwsgi.it
cp uwsgi /opt/unbit/uwsgi/uwsgi
EOF
