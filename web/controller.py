#! /usr/bin/env python

import os
import time
import ConfigParser
import logging
from flask import Flask, request, redirect, url_for, render_template, abort
from werkzeug import secure_filename
import backend_engine

app = Flask(__name__)

UPLOAD_FOLDER = u'upload'
ALLOWED_EXTENSIONS = set([u'png', u'jpg', u'jpeg'])
MAX_CONTENT_LENGTH = 2 * 1024 * 1024

app.config[u'UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config[u'MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

cf = ConfigParser.ConfigParser()
cf.read(u'bs.conf')
region = cf.get(u'BACKEND', 'REGION')
link_prefix = cf.get(u'BACKEND', u'LINK_PREFIX')
bucket_name = cf.get(u'BACKEND', u'BUCKET_NAME')
table_name = cf.get(u'BACKEND', u'TABLE_NAME')
backend = backend_engine.Backend(region, link_prefix, bucket_name, table_name)

google_map_api_id = cf.get(u'FRONTEND', u'GOOGLE_MAP_API_ID')

log_directory = cf.get(u'CONTROLLER', u'LOG_DIRECTORY')

if not app.debug:
    if log_directory[-1] != u'/':
        log_directory += u'/'
    file_handler = logging.FileHandler(log_directory + u'error.log')
    formatter = logging.Formatter(u'%(name)-12s %(asctime)s %(funcName)s %(message)s', u'%a, %d %b %Y %H:%M:%S',)
    file_handler.setFormatter(formatter)
    app.logger.addHandler(file_handler)

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit(u'.', 1)[1] in ALLOWED_EXTENSIONS

def remove_local_files(path, files):
    if path[-1] != u'/':
        path = path + u'/'
    for f in files:
        if f != u'empty':
            os.remove(path+f)

stations = [
    { u'name' : u'Gucheng', u'x' : u'39.907299', u'y' : u'116.190765' },
    { u'name' : u'Babaoshan', u'x' : u'39.907440', u'y' : u'116.235741' },
    { u'name' : u'Yuquanlu', u'x' : u'39.907413', u'y' : u'116.252991' },
    { u'name' : u'Wukesong', u'x' : u'39.907413', u'y' : u'116.273941' },
    { u'name' : u'Wanshoulu', u'x' : u'39.907497', u'y' : u'116.295067' }
    ]

valid_station = []
for station in stations:
    valid_station.append(station[u'name'])

@app.route(u'/')
def index():
    return render_template(u'index.html', stations=stations, google_map_api_id=google_map_api_id)

@app.route(u'/<station>', methods=[u'GET', u'POST'])
def show_station(station=None):
    try:
        if not station in valid_station:
            abort(404)
        if request.method == u'POST':
            title = request.form[u'title']
            description = request.form[u'description']
            timestamp = u'%f' % time.time()
            files = []
            file0 = request.files[u'imageInput0']
            filename0 = u'empty'
            if file0 and allowed_file(file0.filename):
                name = secure_filename(file0.filename).rsplit(u'.', 1)
                filename0 = name[0] + timestamp + u'0.' + name[1]
                file0.save(os.path.join(app.config[u'UPLOAD_FOLDER'], filename0))
                files.append(filename0)
            file1 = request.files[u'imageInput1']
            filename1 = u'empty'
            if file1 and allowed_file(file1.filename):
                name = secure_filename(file1.filename)
                filename1 = name[0] + timestamp + u'1.' + name[1]
                file1.save(os.path.join(app.config[u'UPLOAD_FOLDER'], filename1))
                files.append(filename1)
            file2 = request.files[u'imageInput2']
            filename2 = u'empty'
            if file2 and allowed_file(file2.filename):
                name = secure_filename(file2.filename)
                filename2 = name[0] + timestamp + u'2.' + name[1]
                file2.save(os.path.join(app.config[u'UPLOAD_FOLDER'], filename2))
                files.append(filename2)
            if not title:
                return u'should specific a title'
            title = title.replace(u' ', u'-')
            try:
                backend.write_to_backend(station, title, timestamp, description,
                                         os.path.join(app.config[u'UPLOAD_FOLDER']), files)
                remove_local_files(os.path.join(app.config[u'UPLOAD_FOLDER']), files)
            except backend_engine.TitleExistError, e:
                remove_local_files(os.path.join(app.config[u'UPLOAD_FOLDER']), files)
                return u'title exist, try another one'
        page_num = request.args.get(u'num')
        if not page_num:
            page_num = 0
        else:
            page_num = int(page_num)
        items = backend.get_page(station, page_num, 3)
        if page_num == 0:
            prev = 0
        else:
            prev = page_num - 1
        next = page_num + 1
        return render_template(u'station.html', station=station, items=items, prev=prev, next=next)
    except Exception, e:
        app.logger.error(e)
        abort(500)

@app.route(u'/<station>/<title>', methods=[u'GET', u'POST'])
def show_item(station=None, title=None):
    try:
        if not station in valid_station:
            abort(404)
        if request.method == u'POST':
            action = request.args.get(u'action')
            if action == u'update':
                description = request.form[u'description']
                timestamp = u'%f' % time.time()
                files = []
                file0 = request.files[u'imageInput0']
                if file0 and allowed_file(file0.filename):
                    name = secure_filename(file0.filename).rsplit(u'.', 1)
                    filename0 = name[0] + timestamp + u'0.' + name[1]
                    file0.save(os.path.join(app.config[u'UPLOAD_FOLDER'], filename0))
                    files.append(filename0)
                file1 = request.files[u'imageInput1']
                if file1 and allowed_file(file1.filename):
                    name = secure_filename(file1.filename).rsplit(u'.', 1)
                    filename1 = name[0] + timestamp + u'1.' + name[1]
                    file1.save(os.path.join(app.config[u'UPLOAD_FOLDER'], filename1))
                    files.append(filename1)
                file2 = request.files[u'imageInput2']
                if file2 and allowed_file(file2.filename):
                    name = secure_filename(file2.filename).rsplit(u'.', 1)
                    filename2 = name[0] + timestamp + u'2.' + name[1]
                    file2.save(os.path.join(app.config['UPLOAD_FOLDER'], filename2))
                    files.append(filename2)
    
                backend.update_description_and_append_files(station, title, timestamp, description,
                                                            os.path.join(app.config[u'UPLOAD_FOLDER']), files)
                remove_local_files(os.path.join(app.config[u'UPLOAD_FOLDER']), files)
                return redirect(url_for(u'show_item', station=station, title=title))
            elif action == u'deletefile':
                f = request.args.get(u'f')
                backend.delete_file(station, title, f)
                return redirect(url_for(u'show_item', station=station, title=title))
            elif action == u'deleteitem':
                backend.delete_item(station, title)
                return redirect(url_for(u'show_station', station=station))
            else:
                return u'unknown action %s' % action
        item = backend.get_item(station, title)
        if not item:
            return u'not find item: %s %s' % (station, title)
        return render_template(u'item.html', station=station, item=item)
    except Exception, e:
        app.logger.error(e)
        abort(500)

@app.errorhandler(404)
def handler_404(error):
    return render_template(u'404.html')

@app.errorhandler(500)
def handler_500(error):
    return render_template(u'500.html')

if __name__ == u"__main__":
    app.debug = True
    app.run(host=u'0.0.0.0', port=80)
