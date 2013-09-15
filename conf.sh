#! /bin/bash

export region=us-west-1
export prefix=Subway1
export bucket=sourcecode
export src=web

export bucket_name=`echo $prefix | tr "[:upper:]" "[:lower:]"`$bucket
export key_name="$prefix""Keypair"
export keypair_out="$prefix""Keypair.out"
export keypair_pem="$prefix""Keypair.pem"
