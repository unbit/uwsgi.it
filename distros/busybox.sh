set -u
set -e
wget -O busybox-x86_64 http://www.busybox.net/downloads/binaries/latest/busybox-x86_64
mkdir -p /distros/busybox/bin
cp busybox-x86_64 /distros/busybox/bin/busybox
chmod 755 /distros/busybox/bin/busybox
mkdir /distros/busybox/.old_root
mkdir /distros/busybox/containers
mkdir -p /distros/busybox/etc/security
touch /distros/busybox/etc/security/pam_env.conf
touch /distros/busybox/etc/security/limits.conf
mkdir /distros/busybox/proc
mkdir /distros/busybox/run
mkdir /distros/busybox/tmp
mkdir /distros/busybox/dev
mkdir -p /distros/busybox/usr/local
mkdir /distros/busybox/var
mkdir /distros/busybox/var/log
mkdir /distros/busybox/var/spool
mkdir /distros/busybox/var/tmp

chroot /distros/busybox /bin/busybox sh <<'EOF'
/bin/busybox --install -s /bin
echo "#!/bin/sh" > /bin/bash
echo "/bin/ash \$@" >> /bin/bash
chmod 755 /bin/bash
EOF
