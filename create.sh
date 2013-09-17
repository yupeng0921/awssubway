#! /bin/bash

. conf.sh

function error_exit()
{
	echo $1 1>&2
	#./delete.sh $2
	echo $2 1>&2
	exit 1
}

function wait_stack()
{
	stack_name=$1
	echo waiting stack $stack_name
	while true; do
		sleep 5
		status=`aws cloudformation describe-stacks --stack-name $stack_name --region $region | awk '{if($1=="\"StackStatus\":") print substr($2,2,length($2)-3)}'`
		echo $status
		[ $status == "CREATE_COMPLETE" ] && return 0
		echo $status | grep -q ROLLBACK
		[ $? -eq 0 ] && return 1
	done
}

resource="targz"

tar zcf $src.tar.gz $src
[ $? -eq 0 ] || error_exit "create $src.tar.gz failed" "$resource"

# bucket_conf="{\"LocationConstraint\":\"$region\"}"
# aws s3api create-bucket --bucket $bucket_name --create-bucket-configuration "$bucket_conf"
# region has no effect here
aws s3api create-bucket --bucket $bucket_name --region $region
[ $? -eq 0 ] || error_exit "create bucket failed, $bucket_name" "$resource"

resource="$resource"" bucket"

aws s3api put-object --body $src.tar.gz --bucket $bucket_name --key $src.tar.gz --region $region
[ $? -eq 0 ] || error_exit "upload source code failed, $src.tar.gz, $bucket_name" "$resource"

resource="$resource"" upload"

aws ec2 create-key-pair --key-name $key_name --region $region > $keypair_out
[ $? -eq 0 ] || error_exit "create keypair failed, $key_name, $keypair_out" "$resource"

resource="$resource"" keypair_out"

cat $keypair_out | awk '{if($1=="\"KeyMaterial\":") {gsub(/\\n/,"\n",$0);print substr($0,21,length($0)-23)}}' > $keypair_pem
[ $? -eq 0 ] || error_exit "exact pem failed, $keypair_out, $kekypair_pem" "$resource"
chmod 600 $keypair_pem

resource="$resource"" keypair_pem"

aws cloudformation create-stack --stack-name $stage1_name --template-body file://stage1.json --parameters ParameterKey="KeyName",ParameterValue="$key_name" ParameterKey="S3Bucket",ParameterValue="$bucket_name" ParameterKey="S3Link",ParameterValue="$s3_link" ParameterKey="SourceCodeDir",ParameterValue="$src" ParameterKey="WriteThroughput",ParameterValue="$write_throughput" ParameterKey="GoogleMapApiId",ParameterValue="$google_map_api_id" ParameterKey="ReadThroughput",ParameterValue="$read_throughput" --region $region

[ $? -eq 0 ] || error_exit "create stack failed, $stack_name" "$resource"

resource="$resource"" stage1"

wait_stack $stage1_name
if [ $? -ne 0 ]; then
	# aws cloudformation describe-stack-events --stack-name $stage1_name --region $region
	error_exit "create stack failed, $stack_name" "$resource"
fi
