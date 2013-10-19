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
    def __init__(self, region, link_prefix, bucket_name, table_name):
        if link_prefix[-1] != u'/':
            link_prefix += u'/'
        self.link_prefix = link_prefix
        conn = boto.s3.connect_to_region(region)
        self.bucket = conn.get_bucket(bucket_name)
        conn = boto.dynamodb2.connect_to_region(region)
        self.table = Table(table_name, connection=conn)
    def write_to_backend(self, station, title, timestamp, description, files_path, files):
        if self._get_item(station, title):
            msg = u'%s %s' % (station, title)
            raise TitleExistError(msg)

        if files_path and files:
            if files_path[-1] != u'/':
                files_path = files_path + u'/'
            files_with_path = []
            for f in files:
                k = Key(self.bucket)
                k.key = u''.join([station, u'_', title, u'_', f])
                k.set_contents_from_filename(files_path+f)
                k.set_acl(u'public-read')
                files_with_path.append(self.link_prefix+k.key)
            files_str = u' '.join(files_with_path)
        else:
            files_str = u'empty'
        self.table.put_item(data={u'station':station, u'title':title, \
                                      u'timestamp':timestamp, u'description': description, u'files':files_str})
        return True

    def update_description_and_append_files(self, station, title, timestamp, description, files_path, files):
        if files_path and files:
            if files_path[-1] != u'/':
                files_path = files_path + u'/'
            files_with_path = []
            for f in files:
                k = Key(self.bucket)
                k.key = u''.join([station, u'_', title, u'_', f])
                k.set_contents_from_filename(files_path+f)
                k.set_acl(u'public-read')
                files_with_path.append(self.link_prefix+k.key)
            new_files_str = u' '.join(files_with_path)
        else:
            new_files_str = u'empty'
        item = self._get_item(station, title)
        if not item:
            return False
        old_files_str = unicode(item[u'files'])
        if old_files_str == u'empty':
            files_str = new_files_str
        elif new_files_str == u'empty':
            files_str = old_files_str
        else:
            files_str = u''.join([old_files_str, u' ', new_files_str])
        item[u'files'] = files_str
        item[u'description'] = description
        item.partial_save()
        return True

    def delete_item(self, station, title):
        item = self._get_item(station, title)
        if not item:
            return False
        files_str = unicode(item[u'files'])
        if files_str == u'empty':
            files = []
        elif not files_str:
            files = []
        else:
            files = files_str.split(u' ')
        self.table.delete_item(station=station, title=title)
        for f in files:
            k = Key(self.bucket)
            k.key = f[len(self.link_prefix):]
            k.delete()
        return True

    def delete_file(self, station, title, f):
        item = self._get_item(station, title)
        files = unicode(item[u'files']).split(u' ')
        if f in files:
            files.remove(f)
            if files:
                files_str = u' '.join(files)
            else:
                files_str = u'empty'
            item[u'files'] = files_str
            item.partial_save()
            k =Key(self.bucket)
            k.key = f[len(self.link_prefix):]
            k.delete()
            return True
        return False

    def get_page(self, station, page_num, page_size):
        items = self.table.query(station__eq=station, index=u'timestamp-index', reverse=False)
        i = 0
        skip = page_num * page_size
        ret = []
        for item in items:
            if i < skip:
                pass
            elif i < skip + page_size:
                r = {}
                r[u'title'] = unicode(item[u'title'])
                r[u'timestamp'] = unicode(item[u'timestamp'])
                r[u'description'] = unicode(item[u'description'])
                r[u'files'] = unicode(item[u'files']).split(u' ')
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
        r[u'title'] = unicode(item[u'title'])
        r[u'timestamp'] = unicode(item[u'timestamp'])
        r[u'description'] = unicode(item[u'description'])
        r[u'files'] = unicode(item[u'files']).split(u' ')
        return r

    def _get_item(self, station, title):
        items = self.table.query(station__eq=station, title__eq=title)
        for item in items:
            return item
        return None
