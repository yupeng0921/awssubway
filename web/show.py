#! /usr/bin/env python

import cgi
import boto
import boto.dynamodb2
from boto.dynamodb2.table import Table

print "Content-type:text/html\r\n\r\n"

try:
    form = cgi.FieldStorage()
    station = form['show_station'].value
    conn = boto.dynamodb2.connect_to_region('replace_to_region')
    table = Table('replace_to_table_name', connection=conn)
    result=table.query(station__eq=station, limit=10, reverse=False)
    for item in result:
        print '<p>'
        print item['station']
        print item['description']
        print item['timestamp']
        print '</p>'
except Exception, e:
    print e


