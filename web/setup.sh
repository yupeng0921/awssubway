#! /bin/bash

dir_name=$1
table_name=$2

function dump_param
{
	echo "dir_name: $dir_name"
	echo "table_name: $table_name"
}

function error_exit()
{
    echo $1 1>&2
    exit 1
}

logfile=/tmp/1.log

dump_param >> $logfile

cp /tmp/$dir_name/*.sh /var/www/html/
[ $? -eq 0 ] || error_exit "cp sh failed"
cp /tmp/$dir_name/*.js /var/www/html/
[ $? -eq 0 ] || error_exit "cp js failed"
cp /tmp/$dir_name/*.py /var/www/cgi-bin/
[ $? -eq 0 ] || error_exit "cp py failed"
