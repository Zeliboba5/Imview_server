import os
import traceback
from hashlib import md5
from random import randint
from shutdown import shutdown_server

from app import app
from app import models, db
from bcrypt import gensalt
from flask import request, make_response, Response
from flask.ext.login import LoginManager, login_user, login_required, current_user
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.utils import secure_filename
from passlib.apps import custom_app_context as passlib

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

lm = LoginManager()
lm.init_app(app)


@lm.user_loader
def load_user(user_id):
    return models.User.query.filter_by(id=user_id).first()


@app.route('/shutdown', methods=['POST'])
@login_required
def shutdown():
    if current_user.id == 1:
        shutdown_server()
    else:
        return Response(status=401)


@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    user = models.User.query.filter_by(name=username).first()
    if user and passlib.verify(password, user.password):
        login_user(user, remember=True)
        resp_dict = user.as_dict()
        del resp_dict["password"]
        return make_response(str(resp_dict))
    else:
        response = make_response(str({"error": "wrong username or password"}))
        response.status_code = 401
        return response


@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['username']
    password = request.form['password']

    try:
        password = passlib.encrypt(password)
        user = models.User(username, password)
        db.session.add(user)
        db.session.commit()
    except IntegrityError:
        traceback.print_exc()
        response = make_response(str({"error": "username already in use"}))
        response.set_status = 400
        response.mimetype = 'application/json'
        return response

    login_user(user, remember=True)
    resp_dict = user.as_dict()
    del resp_dict["password"]
    response = make_response(str(resp_dict))
    response.mimetype = 'application/json'
    return response


@app.route('/', methods=['GET'])
def get_api_page():
    return "hello"


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def hash_filename(filename):
    arr = filename.rsplit('.', 1)
    arr[0] += str(gensalt())
    return md5(str(arr[0]).encode()).hexdigest() + '.' + arr[1]


@app.route('/image/new', methods=['POST'])
@login_required
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


@app.route('/image/list', methods=['GET'])
def get_featured_list():
    is_featured = request.args.get('is_featured')
    try:
        image_set = models.Image.query.filter_by(is_featured=is_featured).all()
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


@app.route('/comment/new', methods=['POST'])
@login_required
def create_comment():
    text = request.form['text']
    image_id = request.form['image_id']

    comment = models.Comment(text, current_user.id, image_id)

    db.session.add(comment)
    try:
        db.session.commit()
    except IntegrityError:
        traceback.print_exc()
        return Response(status=400)

    return make_response(str(comment.as_dict()))


@app.route('/comment/get', methods=['GET'])
def get_comments():
    image_id = request.args.get('image_id')
    comment_list = []
    for comment in models.Comment.query.filter_by(image_id=image_id).all():
        comment_list.append(comment.as_dict())

    return make_response(str(comment_list))

# @app.route('/image/vote', methods=['POST']):
# login_required()
# def image_vote():
