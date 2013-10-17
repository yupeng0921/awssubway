#! /usr/bin/env python

import os
import time
from flask import Flask, request, redirect, url_for, render_template
from werkzeug import secure_filename
from backend_engin import backend, TitleExistError

app = Flask(__name__)

UPLOAD_FOLDER = 'upload'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])
MAX_CONTENT_LENGTH = 2 * 1024 * 1024

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def remove_local_files(path, files):
    if path[-1] != '/':
        path = path + '/'
    for f in files:
        if f != 'empty':
            os.remove(path+f)

stations = [
    { 'name' : 'Gucheng', 'x' : '39.907299', 'y' : '116.190765' },
    { 'name' : 'Babaoshan', 'x' : '39.907440', 'y' : '116.235741' },
    { 'name' : 'Yuquanlu', 'x' : '39.907413', 'y' : '116.252991' },
    { 'name' : 'Wukesong', 'x' : '39.907413', 'y' : '116.273941' },
    { 'name' : 'Wanshoulu', 'x' : '39.907497', 'y' : '116.295067' }
    ]

valid_station = []
for station in stations:
    valid_station.append(station['name'])

@app.route('/')
def index():
    return render_template('index.html', stations=stations)

@app.route('/<station>', methods=['GET', 'POST'])
def show_station(station=None):
    if not station in valid_station:
        return render_template('404.html')
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        timestamp = str(time.time())
        files = []
        file0 = request.files['imageInput0']
        filename0 = 'empty'
        if file0 and allowed_file(file0.filename):
            name = secure_filename(file0.filename).rsplit('.', 1)
            filename0 = name[0] + timestamp + '0.' + name[1]
            file0.save(os.path.join(app.config['UPLOAD_FOLDER'], filename0))
            files.append(filename0)
        file1 = request.files['imageInput1']
        filename1 = 'empty'
        if file1 and allowed_file(file1.filename):
            name = secure_filename(file1.filename)
            filename1 = name[0] + timestamp + '1.' + name[1]
            file1.save(os.path.join(app.config['UPLOAD_FOLDER'], filename1))
            files.append(filename1)
        file2 = request.files['imageInput2']
        filename2 = 'empty'
        if file2 and allowed_file(file2.filename):
            name = secure_filename(file2.filename)
            filename2 = name[0] + timestamp + '2.' + name[1]
            file2.save(os.path.join(app.config['UPLOAD_FOLDER'], filename2))
            files.append(filename2)
        if not title:
            return 'should specific a title'
        title = title.replace(' ', '-')
        try:
            backend.write_to_backend(station, title, timestamp, description,
                                     os.path.join(app.config['UPLOAD_FOLDER']), files)
            remove_local_files(os.path.join(app.config['UPLOAD_FOLDER']), files)
        except TitleExistError, e:
            remove_local_files(os.path.join(app.config['UPLOAD_FOLDER']), files)
            return 'title exist, try another one'
    page_num = request.args.get('num')
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
    return render_template('station.html', station=station, items=items, prev=prev, next=next)

@app.route('/<station>/<title>', methods=['GET', 'POST'])
def show_item(station=None, title=None):
    if not station in valid_station:
        return render_template('404.html')
    if request.method == 'POST':
        action = request.args.get('action')
        if action == 'update':
            description = request.form['description']
            timestamp = str(time.time())
            files = []
            file0 = request.files['imageInput0']
            if file0 and allowed_file(file0.filename):
                name = secure_filename(file0.filename).rsplit('.', 1)
                filename0 = name[0] + timestamp + '0.' + name[1]
                file0.save(os.path.join(app.config['UPLOAD_FOLDER'], filename0))
                files.append(filename0)
            file1 = request.files['imageInput1']
            if file1 and allowed_file(file1.filename):
                name = secure_filename(file1.filename).rsplit('.', 1)
                filename1 = name[0] + timestamp + '1.' + name[1]
                file1.save(os.path.join(app.config['UPLOAD_FOLDER'], filename1))
                files.append(filename1)
            file2 = request.files['imageInput2']
            if file2 and allowed_file(file2.filename):
                name = secure_filename(file2.filename).rsplit('.', 1)
                filename2 = name[0] + timestamp + '2.' + name[1]
                file2.save(os.path.join(app.config['UPLOAD_FOLDER'], filename2))
                files.append(filename2)

            backend.update_description_and_append_files(station, title, timestamp, description,
                                                        os.path.join(app.config['UPLOAD_FOLDER']), files)
            remove_local_files(os.path.join(app.config['UPLOAD_FOLDER']), files)
            return redirect(url_for('show_item', station=station, title=title))
        elif action == 'deletefile':
            f = request.args.get('f')
            backend.delete_file(station, title, f)
            return redirect(url_for('show_item', station=station, title=title))
        elif action == 'deleteitem':
            backend.delete_item(station, title)
            return redirect(url_for('show_station', station=station))
        else:
            return 'unknown action %s' % action
    item = backend.get_item(station, title)
    if not item:
        return 'not find item: %s %s' % (station, title)
    return render_template('item.html', station=station, item=item)

@app.errorhandler(404)
def handler_404(error):
    return render_template('404.html')

if __name__ == "__main__":
    app.debug = True
    app.run(host='0.0.0.0', port=80)
