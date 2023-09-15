#!/bin/sh
sed -i 's|^DB_IP=127.0.0.1|DB_IP='"$DB_IP"'|1' /home/webapp/.env;
sed -i 's|DB_PORT=27017|DB_PORT='"$DB_PORT"'|g' /home/webapp/.env;
sed -i 's|DB_NAME=avoassure|DB_NAME='"$DB_NAME"'|g' /home/webapp/.env;
ldconfig /usr/local/lib;
/usr/bin/redis-server /etc/redis.conf --daemonize yes --supervised systemd >> /home/status.txt 2>&1;
/usr/sbin/nginx;
nohup /home/DAS/run.sh >> /home/status.txt 2>&1 &
nohup /home/webapp/run.sh >> /home/status.txt 2>&1
echo "Avo Assure server started"


