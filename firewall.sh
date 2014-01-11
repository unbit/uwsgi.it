LEGION_NODES=/etc/uwsgi/legion_nodes
NODES=/etc/uwsgi/nodes

while read line
do
	echo "$line"
	echo "$line"
done < $LEGION_NODES
