set -u
set -e
rm -f centos-release-6-5.el6.centos.11.1.x86_64.rpm
mkdir -p /distros/centos-6.5/var/lib/rpm
rpm --rebuilddb --root=/distros/centos-6.5
wget http://mirror.centos.org/centos/6.5/os/x86_64/Packages/centos-release-6-5.el6.centos.11.1.x86_64.rpm
rpm -i --root=/distros/centos-6.5 --nodeps centos-release-6-5.el6.centos.11.1.x86_64.rpm
yum --nogpgcheck --installroot=/distros/centos-6.5 install -y rpm-build yum vim gcc ruby-devel python-devel git yajl-devel pcre-devel openssl-devel expat-devel ruby python perl perl-devel perl-ExtUtils-Embed
echo nameserver 8.8.8.8 > /distros/centos-6.5/etc/resolv.conf
chroot /distros/centos-6.5 /bin/bash -x <<'EOF'
set -u
set -e
mkdir -p /.old_root
mkdir -p /containers
mkdir -p /opt/unbit/uwsgi/plugins
cd /root
git clone https://github.com/unbit/uwsgi
cd uwsgi
make uwsgi.it
cp uwsgi /opt/unbit/uwsgi/uwsgi
EOF
