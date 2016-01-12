import json
import os
import traceback
from hashlib import md5
from random import choice

from flask import request, make_response, Response, jsonify
from flask.ext.login import LoginManager, login_user, login_required, current_user
from passlib.apps import custom_app_context as passlib
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.utils import secure_filename

from app import app
from app import models, db
from shutdown import shutdown_server

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ!@#$%^&*"

lm = LoginManager()
lm.init_app(app)


def gen_salt():
    salt = []
    for i in range(0, 16):
        salt.append(choice(ALPHABET))
    "".join(salt)
    return str(salt)


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
        return make_response(jsonify(resp_dict))
    else:
        response = make_response(jsonify({"error": "wrong username or password"}))
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
        response = make_response(jsonify({"error": "username already in use"}))
        response.set_status = 400
        response.mimetype = 'application/json'
        return response

    login_user(user, remember=True)
    resp_dict = user.as_dict()
    del resp_dict["password"]
    response = make_response(jsonify(resp_dict))
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
    arr[0] += gen_salt()
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
    image = models.Image(filename, 0)
    db.session.add(image)
    try:
        db.session.commit()
    except SQLAlchemyError:
        traceback.print_exc()
        return Response(status=400)
    response = jsonify(image.as_dict())
    return make_response(response)


@app.route('/image/get/', methods=['GET'])
def get_image_by_id():
    image_id = request.args.get('image_id')
    if image_id:
        try:
            response = make_response(jsonify(models.Image.query.filter_by(id=image_id).first().as_dict()))
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
    try:
        is_featured = request.args.get('is_featured')
        if is_featured:
            import datetime
            yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
            image_set = models.Image.query.filter(models.Image.publish_date > yesterday)
        else:
            image_set = models.Image.query.all()
    except SQLAlchemyError:
        traceback.print_exc()
        return Response(status=400)
    image_list = []
    for image in image_set:
        comments_count = len(image.comments.all())
        image = image.as_dict()
        image['publish_date'] = str(image['publish_date'])
        image['comments_count'] = comments_count
        image_list.append(image)

    return Response(json.dumps(image_list), status=200, mimetype='application/json')


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

    author = comment.author.as_dict()
    del author['password']
    response = comment.as_dict()
    response['publish_date'] = str(response['publish_date'])
    response['author'] = author
    return make_response(jsonify(response))


@app.route('/comment/list', methods=['GET'])
def get_comments():
    try:
        image_id = request.args.get('image_id')
        comment_list = []
        for comment in models.Comment.query.filter_by(image_id=image_id).all():
            author = comment.author.as_dict()
            del author['password']
            comment = comment.as_dict()
            comment['publish_date'] = str(comment['publish_date'])
            comment['author'] = author
            comment_list.append(comment)

        return make_response(json.dumps(comment_list))
    except:
        traceback.print_exc()


@app.route('/image/vote', methods=['POST'])
@login_required
def image_vote():
    image_id = request.form['image_id']
    is_upvote = request.form['is_upvote']

    image = models.Image.query.filter_by(id=image_id).first()

    if current_user in image.voted_user:
        response = make_response(jsonify({'error': 'already voted', 'error_code': 0}))
        response.status_code = 405
        return response
    else:
        image.voted_user.append(current_user)
        if is_upvote == 1:
            image.rating += 1
        else:
            image.rating -= 1
        db.session.add(image)
        db.session.commit()

        return make_response(jsonify(image.as_dict()))


@app.route('/comment/vote', methods=['POST'])
@login_required
def comment_vote():
    comment_id = request.form['comment_id']
    is_upvote = request.form['is_upvote']

    comment = models.Comment.query.filter_by(id=comment_id).first()

    if current_user in comment.voted_user:
        response = make_response(jsonify({'error': 'already voted', 'error_code': 0}))
        response.status_code = 405
        return response
    else:
        comment.voted_user.append(current_user)
        if is_upvote == 1:
            comment.rating += 1
        else:
            comment.rating -= 1
        db.session.add(comment)
        db.session.commit()

        return make_response(jsonify(comment.as_dict()))
