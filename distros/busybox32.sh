set -u
set -e
wget -O busybox-i686 http://www.busybox.net/downloads/binaries/latest/busybox-i686
mkdir -p /distros/busybox32/bin
cp busybox-i686 /distros/busybox32/bin/busybox
chmod 755 /distros/busybox32/bin/busybox
mkdir /distros/busybox32/.old_root
mkdir /distros/busybox32/containers
mkdir -p /distros/busybox32/etc/security
touch /distros/busybox32/etc/security/pam_env.conf
touch /distros/busybox32/etc/security/limits.conf
mkdir /distros/busybox32/proc
mkdir /distros/busybox32/run
mkdir /distros/busybox32/tmp
mkdir /distros/busybox32/dev
mkdir -p /distros/busybox32/usr/local
mkdir /distros/busybox32/var
mkdir /distros/busybox32/var/log
mkdir /distros/busybox32/var/spool
mkdir /distros/busybox32/var/tmp

chroot /distros/busybox32 /bin/busybox sh <<'EOF'
/bin/busybox --install -s /bin
echo "#!/bin/sh" > /bin/bash
echo "/bin/ash \$@" >> /bin/bash
chmod 755 /bin/bash
EOF
