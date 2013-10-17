#! /usr/bin/env python

import boto
import boto.s3
from boto.s3.key import Key
import boto.dynamodb2
from boto.dynamodb2.table import Table

class TitleExistError(Exception):
    """
    title already exist in dynamodb
    """
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return self.msg

class Backend():
    def __init__(self, region, s3_prefix, bucket_name, table_name):
        self.s3_prefix = s3_prefix
        conn = boto.s3.connect_to_region(region)
        self.bucket = conn.get_bucket(bucket_name)
        conn = boto.dynamodb2.connect_to_region(region)
        self.table = Table(table_name, connection=conn)
    def write_to_backend(self, station, title, timestamp, description, files_path, files):
        if self._get_item(station, title):
            msg = '%s %s' % (station, title)
            raise TitleExistError(msg)

        if files_path and files:
            if files_path[-1] != '/':
                files_path = files_path + '/'
            files_with_path = []
            for f in files:
                k = Key(self.bucket)
                k.key = ''.join([station, '_', title, '_', f])
                k.set_contents_from_filename(files_path+f)
                k.set_acl('public-read')
                files_with_path.append(self.s3_prefix+k.key)
            files_str = ' '.join(files_with_path)
        else:
            files_str = 'empty'
        self.table.put_item(data={'station':station, 'title':title, \
                                      'timestamp':timestamp, 'description': description, 'files':files_str})
        return True

    def update_description_and_append_files(self, station, title, timestamp, description, files_path, files):
        if files_path and files:
            if files_path[-1] != '/':
                files_path = files_path + '/'
            files_with_path = []
            for f in files:
                k = Key(self.bucket)
                k.key = ''.join([station, '_', title, '_', f])
                k.set_contents_from_filename(files_path+f)
                k.set_acl('public-read')
                files_with_path.append(self.s3_prefix+k.key)
            new_files_str = ' '.join(files_with_path)
        else:
            new_files_str = 'empty'
        item = self._get_item(station, title)
        if not item:
            return False
        old_files_str = str(item['files'])
        if old_files_str == 'empty':
            files_str = new_files_str
        elif new_files_str == 'empty':
            files_str = old_files_str
        else:
            files_str = ''.join([old_files_str, ' ', new_files_str])
        item['files'] = files_str
        item['description'] = description
        item.partial_save()
        return True

    def delete_item(self, station, title):
        item = self._get_item(station, title)
        if not item:
            return False
        files_str = str(item['files'])
        if files_str == 'empty':
            files = []
        elif not files_str:
            print 'interal error, no files, %s %S' % (station, title)
            files = []
        else:
            files = files_str.split(' ')
        self.table.delete_item(station=station, title=title)
        for f in files:
            k = Key(self.bucket)
            k.key = f[len(self.s3_prefix):]
            k.delete()
        return True

    def delete_file(self, station, title, f):
        item = self._get_item(station, title)
        files = str(item['files']).split(' ')
        if f in files:
            files.remove(f)
            if files:
                files_str = ' '.join(files)
            else:
                files_str = 'empty'
            item['files'] = files_str
            item.partial_save()
            k =Key(self.bucket)
            k.key = f[len(self.s3_prefix):]
            k.delete()
            return True
        return False

    def get_page(self, station, page_num, page_size):
        items = self.table.query(station__eq=station, index='timestamp-index', reverse=False)
        i = 0
        skip = page_num * page_size
        ret = []
        for item in items:
            if i < skip:
                pass
            elif i < skip + page_size:
                r = {}
                r['title'] = unicode(item['title'])
                r['timestamp'] = unicode(item['timestamp'])
                r['description'] = unicode(item['description'])
                r['files'] = str(item['files']).split(' ')
                ret.append(r)
            else:
                break
            i += 1
        return ret

    def get_item(self, station, title):
        item = self._get_item(station, title)
        if not item:
            return None
        r = {}
        r['title'] = unicode(item['title'])
        r['timestamp'] = unicode(item['timestamp'])
        r['description'] = unicode(item['description'])
        r['files'] = str(item['files']).split(' ')
        return r

    def _get_item(self, station, title):
        items = self.table.query(station__eq=station, title__eq=title)
        for item in items:
            return item
        return None

backend = Backend('us-west-2', 'https://s3-us-west-2.amazonaws.com/beijingsubway/', 'beijingsubway', 'subway2')
