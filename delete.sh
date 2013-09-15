#! /bin/bash

. conf.sh

if [ $# -eq 0 ]; then
	param="targz bucket upload keypair_out keypair_pem"
else
	param=$*
fi

echo "delete: $param"

echo $param | grep -q -w keypair_pem
if [ $? -eq 0 ]; then
	rm -f $keypair_pem
fi

echo $param | grep -q -w keypair_out
if [ $? -eq 0 ]; then
	rm -f $keypair_out
fi

echo $param | grep -q -w upload
if [ $? -eq 0 ]; then
	# nothing to do, we delete all files in S3 when delete bucket
	:
fi
echo $param | grep -q -w bucket
if [ $? -eq 0 ]; then
	aws s3 rb s3://$bucket_name --force
fi

echo $param | grep -q -w targz
if [ $? -eq 0 ]; then
	rm -f $src.tar.gz
fi
