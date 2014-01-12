LEGION_NODES=/etc/uwsgi/legion_nodes
NODES=/etc/uwsgi/nodes

if [ ! -f $NODES ]; then
exit 0
fi

# tuntap firewall
iptables -F tuntap
while read line
do
	iptables -A tuntap -s $line -p udp --sport 999 -j ACCEPT
done < $NODES
iptables -A tuntap -j DROP

if [ ! -f $LEGION_NODES ]; then
exit 0
fi

# legion firewall
iptables -F legion
while read line
do
        iptables -A legion -s $line -p udp --sport 2000 -j ACCEPT
done < $NODES
iptables -A legion -j DROP

#while read line
#do
#	echo "$line"
#	echo "$line"
#done < $LEGION_NODES
