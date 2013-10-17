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
			echo $result | grep -q 'does not exist$'
			[ $? -eq 0 ] && break 2
			status=`echo $result | awk 'BEGIN {RS=","} {if($1=="\"StackStatus\":") print substr($2,2,length($2)-2)}'`
			echo "$stack_name $status"
			[ $status == "DELETE_FAILED" ] && break
		done
	done
}
			
if [ $# -eq 0 ]; then
	param="targz bucket upload keypair_out keypair_pem dynamodb stage1 image stage2"
else
	param=$*
fi

echo "delete param: $param"

echo $param | grep -q -w stage2
if [ $? -eq 0 ]; then
	delete_stack $stage2_name
fi

echo $param | grep -q -w image
if [ $? -eq 0 ]; then
	image_id=`aws ec2 describe-images --owners self --filters Name=name,Values=$image_name --region $region | awk '{if($1=="\"ImageId\":") print substr($2,2,length($2)-3)}'`
	run_until_success aws ec2 deregister-image --image-id $image_id --region $region
fi

echo $param | grep -q -w stage1
if [ $? -eq 0 ]; then
	delete_stack $stage1_name
fi

echo $param | grep -q -w dynamodb
if [ $? -eq 0 ]; then
	while true; do
		status=`aws dynamodb describe-table --table-name $dynamodb_name --region us-west-1 | awk '{if($1=="\"TableStatus\":") print substr($2,2,length($2)-3)}'`
		if [ "$status" == "" ]; then
			break
		elif [ "$status" == "ACTIVE" ]; then
			aws dynamodb delete-table --table-name $dynamodb_name --region $region
			break
		fi
		sleep 5
	done
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
