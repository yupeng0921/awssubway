#! /bin/bash

dir_name=$1
table_name=$2
link_prefix=$3
bucket_name=$4
region=$5
google_map_api_id=$6
log_directory=$7


function dump_param
{
	echo "dir_name: $dir_name"
	echo "table_name: $table_name"
	echo "link_prefix: $link_prefix"
	echo "bucket_name: $bucket_name"
	echo "region: $region"
	echo "google_map_api_id: $google_map_api_id"
	echo "log_directory: $log_directory"
}

function error_exit()
{
    echo $1 1>&2
    exit 1
}

logfile=/tmp/1.log

dump_param >> $logfile

echo "[BACKEND]" > /opt/$dir_name/bs.conf
echo "DIR_NAME = $dir_name" >> /opt/$dir_name/bs.conf
echo "TABLE_NAME = $table_name" >> /opt/$dir_name/bs.conf
echo "LINK_PREFIX = $link_prefix" >> /opt/$dir_name/bs.conf
echo "BUCKET_NAME = $bucket_name" >> /opt/$dir_name/bs.conf
echo "REGION = $region" >> /opt/$dir_name/bs.conf
echo "[FRONTEND]" >> /opt/$dir_name/bs.conf
echo "GOOGLE_MAP_API_ID = $google_map_api_id" >> /opt/$dir_name/bs.conf
echo "[CONTROLLER]" >> /opt/$dir_name/bs.conf
echo "LOG_DIRECTORY = $log_directory" >> /opt/$dir_name/bs.conf

cat /etc/nginx/nginx.conf | awk 'BEGIN{mask=0}{if (mask && $1=="}")mask=0; if(!mask) {print $0};if($1=="location" && $2=="/" && $3=="{"){mask=1;printf("\t\t\tinclude uwsgi_params;\n\t\t\tuwsgi_pass 127.0.0.1:3031;\n")} }' > /tmp/nginx.conf

mv /tmp/nginx.conf /etc/nginx/nginx.conf

service nginx restart > /dev/null

useradd -M -s /sbin/nologin uwsgi > /dev/null

mkdir $log_directory
chown -R uwsgi:uwsgi $log_directory
chown -R uwsgi:uwsgi /opt/$dir_name

uwsgi_uid=`awk 'BEGIN {FS=":"} {if($1=="uwsgi")print $3}' /etc/passwd`
uwsgi_command="cd /opt/$dir_name ; uwsgi --socket 127.0.0.1:3031 --wsgi-file /opt/$dir_name/controller.py --callable app --processes 4 --threads 2 --stats 127.0.0.1:9191 --uid $uwsgi_uid -d $log_directory/uwsgi.log"

echo $uwsgi_command >> /etc/rc.local
$uwsgi_command
