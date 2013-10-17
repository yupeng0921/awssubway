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
		echo "$stack_name $status"
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
[ $? -eq 0 ] || error_exit "extract pem failed, $keypair_out, $kekypair_pem" "$resource"
chmod 600 $keypair_pem

resource="$resource"" keypair_pem"

aws dynamodb create-table --table-name $dynamodb_name --attribute-definitions AttributeName="station",AttributeType="S" AttributeName="title",AttributeType="S" AttributeName="timestamp",AttributeType="S" --key-schema AttributeName="station",KeyType="HASH" AttributeName="title",KeyType="RANGE" --provisioned-throughput ReadCapacityUnits=$read_throughput,WriteCapacityUnits=$write_throughput --local-secondary-indexes "[{\"IndexName\":\"timestamp-index\",\"KeySchema\":[{\"AttributeName\":\"station\",\"KeyType\":\"HASH\"},{\"AttributeName\":\"timestamp\",\"KeyType\":\"RANGE\"}],\"Projection\":{\"ProjectionType\":\"ALL\"}}]" --region $region
[ $? -eq 0 ] || error_exit "create dynamodb failed" "$resource"

resource="$resource"" dynamodb"

aws cloudformation create-stack --stack-name $stage1_name --template-body file://stage1.json --parameters ParameterKey="KeyName",ParameterValue="$key_name" ParameterKey="S3Bucket",ParameterValue="$bucket_name" ParameterKey="S3Link",ParameterValue="$s3_link" ParameterKey="SourceCodeDir",ParameterValue="$src" ParameterKey="GoogleMapApiId",ParameterValue="$google_map_api_id" ParameterKey="DynamoDb",ParameterValue="$dynamodb_name" --region $region

[ $? -eq 0 ] || error_exit "create stack failed, $stage1_name" "$resource"

resource="$resource"" stage1"

wait_stack $stage1_name
if [ $? -ne 0 ]; then
	# aws cloudformation describe-stack-events --stack-name $stage1_name --region $region
	error_exit "create stack failed, $stack_name" "$resource"
fi


result=`aws cloudformation describe-stacks --stack-name $stage1_name --region $region | egrep OutputValue`
instance_id=""
for item in $result; do
	[ $item == "\"OutputValue\":" ] && continue
	item=`echo $item | awk '{print substr($0,2,length($0)-2)}'`
	echo $item | egrep -q '^i-[0-9,a-f]{8}$'
	[ $? -eq 0 ] && instance_id=$item
done

[ "$instance_id" == "" ] && error_exit "no instance_id $result" "$resource"

echo $instance_id

echo "$resource"
exit 0

aws ec2 create-image --instance-id $instance_id --name $image_name --description "$image_description" --region $region
[ $? -eq 0 ] || error_exit "create image failed, $instance_id, $snapshot_name" "$resource"

resource="$resource"" image"

image_id=`aws ec2 describe-images --owners self --filters Name=name,Values=$image_name --region $region | awk '{if($1=="\"ImageId\":") print substr($2,2,length($2)-3)}'`
echo $image_id | egrep -q '^ami-[0-9,a-f]{8}$'
[ $? -eq 0 ] || error_exit "invalid image_id, $image_id" "$resource"

echo $image_id

while true; do
	sleep 5
	state=`aws ec2 describe-images --owners self --filters Name=name,Values=$image_name --region $region | awk '{if($1=="\"State\":") print substr($2,2,length($2)-3)}'`
	echo "$state"
	if [ "$state" == "available" ]; then
		break
	fi
done

aws cloudformation create-stack --stack-name $stage2_name --template-body file://stage2.json --parameters ParameterKey="KeyName",ParameterValue="$key_name" ParameterKey="ImageId",ParameterValue="$image_id" ParameterKey="InstanceType",ParameterValue="$instance_type" ParameterKey="DynamoDb",ParameterValue="$dynamodb_name" ParameterKey="MinSize",ParameterValue="$min_size" ParameterKey="MaxSize",ParameterValue="$max_size" --region $region

[ $? -eq 0 ] || error_exit "create stack failed, $stage2_name" "$resource"

resource="$resource"" stage2"

wait_stack $stage2_name
if [ $? -ne 0 ]; then
	# aws cloudformation describe-stack-events --stack-name $stage2_name --region $region
	error_exit "create stack failed, $stack_name" "$resource"
fi

aws cloudformation describe-stacks --stack-name $stage2_name --region $region | egrep OutputValue
