import os
import traceback
from hashlib import md5
from random import randint

from app import app
from app import models, db
from flask import request, make_response, Response
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}


@app.route('/', methods=['GET'])
def get_api_page():
    return "hello"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def hash_filename(filename):
    arr = filename.rsplit('.', 1)
    arr[0] += str(randint(0, 10000))
    return md5(str(arr[0]).encode()).hexdigest() + '.' + arr[1]


@app.route('/image/new', methods=['POST'])
def add_new_image():
    try:
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = hash_filename(file.filename)
            filename = secure_filename(filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            return Response(status=400)
    except:
        traceback.print_exc()
        return Response(status=400)

    image = models.Image(filename, request.form['title'], request.form['description'], 0, True)
    db.session.add(image)
    try:
        db.session.commit()
    except SQLAlchemyError:
        traceback.print_exc()
        return Response(status=400)
    response = make_response()
    response.status_code = 200
    return response


@app.route('/image/get/', methods=['GET'])
def get_image_by_id():
    image_id = request.args.get('image_id')
    if image_id:
        try:
            response = make_response(models.Image.query.filter_by(id=image_id).first().as_disc())
        except SQLAlchemyError:
            traceback.print_exc()
            return Response(status=400)
        response.mimetype = 'application/json'
        response.status_code = 200
        return response
    else:
        return Response(status=404)


@app.route('/image/featured_list')
def get_featured_list():
    try:
        image_set = models.Image.query.filter_by(is_featured=True).all()
    except SQLAlchemyError:
        traceback.print_exc()
        return Response(status=500)

    image_list = []
    for image in image_set:
        image_list.append(image.as_dict())
    response = make_response(str(image_list))
    response.status_code = 200
    response.mimetype = 'application/json'
    return response

