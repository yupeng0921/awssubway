#! /usr/bin/env python

import cgi
import boto
import boto.dynamodb2
from boto.dynamodb2.table import Table
import time

print "Content-type:text/html\r\n\r\n"

form = cgi.FieldStorage()
try:
    station = form['insert_station'].value
    description = form['insert_description'].value
    timestamp = time.ctime()

    conn = boto.dynamodb2.connect_to_region('us-west-1')
    table = Table('SubwayStage1-DynamoDb-1HDONOMYE3WDE', connection=conn)
    table.put_item(data={'station':station, 'timestamp':timestamp, 'description':description})

    print station
    print timestamp
    print description
except Exception, e:
    print e
