set -u
set -e
rm -rf uwsgi
git clone https://github.com/unbit/uwsgi
cd uwsgi
make uwsgi.it
cp uwsgi /opt/unbit/uwsgi/uwsgi

/opt/unbit/uwsgi/uwsgi --build-plugin plugins/corerouter
/opt/unbit/uwsgi/uwsgi --build-plugin plugins/http
/opt/unbit/uwsgi/uwsgi --build-plugin plugins/fastrouter
/opt/unbit/uwsgi/uwsgi --build-plugin plugins/tuntap

cp corerouter_plugin.so http_plugin.so fastrouter_plugin.so tuntap_plugin.so /opt/unbit/uwsgi/plugins

/opt/unbit/uwsgi/uwsgi --build-plugin ../calc_ip.c
cp calc_ip_plugin.so /opt/unbit/uwsgi/plugins

git clone https://github.com/unbit/uwsgi-alarm-chain
/opt/unbit/uwsgi/uwsgi --build-plugin uwsgi-alarm-chain
cp alarm_chain_plugin.so /opt/unbit/uwsgi/plugins

git clone https://github.com/unbit/uwsgi-console-broadcast
/opt/unbit/uwsgi/uwsgi --build-plugin uwsgi-console-broadcast
cp console_broadcast_plugin.so /opt/unbit/uwsgi/plugins

git clone https://github.com/unbit/uwsgi-eventfd
/opt/unbit/uwsgi/uwsgi --build-plugin uwsgi-eventfd
cp eventfd_plugin.so /opt/unbit/uwsgi/plugins

git clone https://github.com/unbit/uwsgi-hetzner
/opt/unbit/uwsgi/uwsgi --build-plugin uwsgi-hetzner
cp hetzner_plugin.so /opt/unbit/uwsgi/plugins

git clone https://github.com/unbit/uwsgi-quota
/opt/unbit/uwsgi/uwsgi --build-plugin uwsgi-quota
cp quota_plugin.so /opt/unbit/uwsgi/plugins
