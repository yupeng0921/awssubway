#! /bin/bash

. conf.sh

function run_until_success()
{
	echo "$*"
        $*
        ret=$?
        while [ $ret -ne 0 ];
        do
                sleep 5
		echo "$*"
                $*
                ret=$?
        done
}

function delete_stack()
{
	stack_name=$1
	while true; do
		run_until_success aws cloudformation delete-stack --stack-name $stack_name --region $region
		while true; do
			sleep 5
			result=`aws cloudformation describe-stacks --stack-name $stack_name --region $region 2>&1`
			echo $result
			echo $result | grep -q 'does not exist$'
			[ $? -eq 0 ] && break 2
			status=`echo $result | awk 'BEGIN {RS=","} {if($1=="\"StackStatus\":") print substr($2,2,length($2)-2)}'`
			[ $status == "DELETE_FAILED" ] && break
		done
	done
}
			
if [ $# -eq 0 ]; then
	param="targz bucket upload keypair_out keypair_pem stage1"
else
	param=$*
fi

echo "delete param: $param"

echo $param | grep -q -w stage1
if [ $? -eq 0 ]; then
	delete_stack $stage1_name
fi

echo $param | grep -q -w keypair_pem
if [ $? -eq 0 ]; then
	rm -f $keypair_pem
fi

echo $param | grep -q -w keypair_out
if [ $? -eq 0 ]; then
	rm -f $keypair_out
	run_until_success aws ec2 delete-key-pair --key-name $key_name --region $region
fi

echo $param | grep -q -w upload
if [ $? -eq 0 ]; then
	# nothing to do, we delete all files in S3 when delete bucket
	:
fi
echo $param | grep -q -w bucket
if [ $? -eq 0 ]; then
	run_until_success aws s3 rb s3://$bucket_name --force --region $region
fi

echo $param | grep -q -w targz
if [ $? -eq 0 ]; then
	rm -f $src.tar.gz
fi
