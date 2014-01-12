LEGION_NODES=/etc/uwsgi/legion_nodes
NODES=/etc/uwsgi/nodes

# nodes based rules

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

# fastrouter_out firewall
iptables -F fastrouter_out
while read line
do
        iptables -A fastrouter_in -d $line -p tcp -j DROP
done < $NODES
iptables -A fastrouter_out -j ACCEPT


# legion based rules

if [ ! -f $LEGION_NODES ]; then
exit 0
fi

# legion firewall
iptables -F legion
while read line
do
        iptables -A legion -s $line -p udp --sport 2000 -j ACCEPT
done < $LEGION_NODES
iptables -A legion -j DROP


# fastrouter_in firewall
iptables -F fastrouter_in
while read line
do
        iptables -A fastrouter_in -s $line -p tcp -j ACCEPT
done < $LEGION_NODES
iptables -A fastrouter_in -j DROP

# subscription firewall
iptables -F subscription
while read line
do
        iptables -A subscription -s $line -p udp --sport 3026 -j ACCEPT
done < $LEGION_NODES
iptables -A subscription -j DROP
