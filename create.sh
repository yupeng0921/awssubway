#! /bin/bash

. conf.sh

function error_exit()
{
	echo $1 1>&2
	./delete.sh $2
	exit 1
}

resource="targz"

tar zcf $src.tar.gz $src
[ $? -eq 0 ] || error_exit "create $src.tar.gz failed" "$resource"

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

resource="$resource"" keypair_pem"
