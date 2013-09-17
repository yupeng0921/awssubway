#! /bin/bash

dir_name=$1
table_name=$2
region=$3
google_map_api_id=$4


function dump_param
{
	echo "dir_name: $dir_name"
	echo "table_name: $table_name"
	echo "region: $region"
	echo "google_map_api_id: $google_map_api_id"
}

function error_exit()
{
    echo $1 1>&2
    exit 1
}

logfile=/tmp/1.log

dump_param >> $logfile

sed -i "s/replace_to_google_map_api_id/$google_map_api_id/g" /tmp/$dir_name/index.html
[ $? -eq 0 ] || error_exit "replace $google_map_api_id in index.html failed"
sed -i "s/replace_to_region/$region/g" /tmp/$dir_name/insert.py
[ $? -eq 0 ] || error_exit "replace $region in insert.py failed"
sed -i "s/replace_to_table_name/$table_name/g" /tmp/$dir_name/insert.py
[ $? -eq 0 ] || error_exit "replace $table_name in insert.py failed"
sed -i "s/replace_to_region/$region/g" /tmp/$dir_name/show.py
[ $? -eq 0 ] || error_exit "replace $region in show.py failed"
sed -i "s/replace_to_table_name/$table_name/g" /tmp/$dir_name/show.py
[ $? -eq 0 ] || error_exit "replace $table_name in show.py failed"

cp /tmp/$dir_name/*.html /var/www/html/
[ $? -eq 0 ] || error_exit "cp sh failed"
cp /tmp/$dir_name/*.js /var/www/html/
[ $? -eq 0 ] || error_exit "cp js failed"
cp /tmp/$dir_name/*.py /var/www/cgi-bin/
[ $? -eq 0 ] || error_exit "cp py failed"
