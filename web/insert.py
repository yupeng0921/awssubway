#! /usr/bin/env python

import cgi

print "Content-type:text/html\r\n\r\n"

form = cgi.FieldStorage()
station = form['insert_station'].value
description = form['insert_description'].value

print station
print description
