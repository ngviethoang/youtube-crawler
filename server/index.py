# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_mongoengine import MongoEngine
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Email, Length, InputRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json

from processor.mongo_db import get_mongo_db

mongo_db = get_mongo_db()

# app = Flask(__name__)


class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        variable_start_string='%%',  # Default is '{{', I'm changing this because Vue.js uses '{{' / '}}'
        variable_end_string='%%',
    ))


app = CustomFlask(__name__)  # This replaces your existing "app = Flask(__name__)"


db = MongoEngine(app)
app.config['SECRET_KEY'] = '1\x0c\xf6\xbf\xaa\xb9\xd0\xe7\xae\xdc\x07\xe6\xb7\xe3\xd3\x90\xd3\x13bG\xb5(\xfa\xc9'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

words_separator = ', '


class User(UserMixin, db.Document):
    email = db.StringField(max_length=30)
    password = db.StringField()


@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()


class RegForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=30)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=20)])


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegForm()
    if request.method == 'POST':
        # if form.validate():
        email = form.email.data
        existing_user = User.objects(email=email).first()
        if existing_user is None:
            hashpass = generate_password_hash(form.password.data, method='sha256')
            hey = User(form.email.data, hashpass).save()
            login_user(hey)

            # Create user's info in db
            mongo_db['users'].replace_one(
                {'email': email},
                {'email': email, 'vocabulary': '', 'suitable_videos': [], 'watched_videos': []},
                upsert=True
            )

            return redirect(url_for('home'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegForm()
    if request.method == 'POST':
        # if form.validate():
        email = form.email.data
        check_user = User.objects(email=email).first()
        if check_user:
            if check_password_hash(check_user['password'], form.password.data):
                login_user(check_user)

                return redirect(url_for('home'))
    return render_template('login.html', form=form)


@app.route('/logout', methods=['GET'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@app.route('/home')
@login_required
def home():
    return render_template('index.html')


@app.route('/vocabulary', methods=['GET', 'POST'])
@login_required
def vocabulary():
    vocabulary = ''
    # Update vocabulary from file and form
    if request.method == 'POST':
        vocabulary = request.form['vocabulary']
        vocabulary = vocabulary.split(words_separator)
        update_suitable_videos(vocabulary)

        vocabulary = words_separator.join(sorted(vocabulary))
    # Get user's vocabulary
    elif request.method == 'GET':
        vocabulary = mongo_db['users'].find_one({'email': current_user.email})['vocabulary']

    return jsonify(dict(
        vocabulary=vocabulary
    ))


# Update watched videos for user
@app.route('/videos/watch', methods=['GET'])
@login_required
def watch_videos():
    video_ids = request.args.get('video_ids', '').split(words_separator)

    # Get user's watched videos
    watched_videos = mongo_db['users'].find_one({'email': current_user.email})['watched_videos']
    watched_videos = list(set(watched_videos + video_ids))

    # Update watched videos
    mongo_db['users'].update_one(
        {'email': current_user.email},
        {'$set': {'watched_videos': watched_videos}}
    )

    # Update user's vocabulary based on watched videos
    vocabulary = mongo_db['users'].find_one({'email': current_user.email})['vocabulary']
    vocabulary = set(vocabulary.split(words_separator))
    print('before add videos: {}'.format(len(vocabulary)))

    # Get subtitles and merge to vocabulary
    res_get_videos = mongo_db['subtitles'].find({'id': {'$in': video_ids}})
    for res_get_video in res_get_videos:
        subtitle_tokens = set(res_get_video['subtitle']['tokens'].split(words_separator))
        vocabulary = vocabulary.union(subtitle_tokens)

    print('after add videos: {}'.format(len(vocabulary)))

    update_suitable_videos(vocabulary)

    return jsonify(dict(
        status=200
    ))


@app.route('/videos', methods=['GET'])
@login_required
def videos():
    args = request.args

    nPerPage = int(args.get('limit', 10))
    pageNumber = int(args.get('page', 0))

    # Get user's recommended videos
    user_videos = mongo_db['users'].find_one({'email': current_user.email})['suitable_videos']

    # Pagination
    startIndex = (pageNumber - 1) * nPerPage if pageNumber > 0 else 0
    endIndex = startIndex + nPerPage

    user_videos = user_videos[startIndex:endIndex]
    video_ids = [video['id'] for video in user_videos]

    # Get videos' info
    res_videos = []
    res_get_videos = mongo_db['subtitles'].find({'id': {'$in': video_ids}})
    for res_get_video in res_get_videos:
        res_videos.append(res_get_video)

    videos = []

    for user_video in user_videos:
        res_video = filter(lambda x: x['id'] == user_video['id'], res_videos)[0]

        videos.append(dict(
            id=res_video['id'],
            title=res_video['title'],
            channelTitle=res_video['snippet']['channelTitle'],
            description=res_video['snippet']['description'],
            thumbnail=res_video['snippet']['thumbnails']['medium']['url'],
            subtitle=res_video['subtitle'],
            new_words=user_video['new_words'],
            new_words_pnt=user_video['new_words_pnt'],
        ))

    return jsonify(dict(
        videos=videos
    ))


@app.route('/api/search')
@login_required
def search():
    query = request.args.get('q', None)

    user = mongo_db['users'].find_one({'email': current_user.email})
    # Get user's recommended videos
    user_videos = user['suitable_videos']

    # Get user's watched videos
    watched_videos = user['watched_videos']

    # Search by query
    videos = []

    res_videos = mongo_db['subtitles'].find({'subtitle.sentences.text': {"$regex": ' {} '.format(query)}})

    for res_video in res_videos:
        new_words_stats = filter(lambda x: x['id'] == res_video['id'], user_videos)
        if len(new_words_stats):
            new_words_stats = new_words_stats[0]
        else:
            new_words_stats = None

        video = dict(
            id=res_video['id'],
            title=res_video['title'],
            channelTitle=res_video['snippet']['channelTitle'],
            description=res_video['snippet']['description'],
            thumbnail=res_video['snippet']['thumbnails']['medium']['url'],
            subtitle=res_video['subtitle'],
            isWatched=res_video['id'] in watched_videos,
            new_words_stats=new_words_stats
        )
        videos.append(video)

    return jsonify(dict(
        len=len(videos),
        videos=videos
    ))


@app.route('/search')
@login_required
def search_page():
    query = request.args.get('q', None)
    return render_template('search.html', query=query)


def update_suitable_videos(vocabulary):
    suitable_videos = []

    # Get user's watched videos
    watched_videos = mongo_db['users'].find_one({'email': current_user.email})['watched_videos']

    # Get videos from DB (except watched videos)
    videos = mongo_db['subtitles'].find({
        'subtitle': {'$ne': None},
        'id': {'$nin': watched_videos}
    })
    for video in videos:
        subtitle_tokens = set(video['subtitle']['tokens'].split(words_separator))

        # Get new words from subtitle
        new_words = subtitle_tokens - set(vocabulary)
        new_words_pnt = round(float(len(new_words)) / len(subtitle_tokens) * 100, 2)

        # Save videos for user
        if new_words_pnt < 50:
            suitable_videos.append(dict(
                id=video['id'],
                new_words=words_separator.join(sorted(new_words)),
                new_words_pnt=new_words_pnt
            ))

    # Sort suitable videos by new words point
    suitable_videos = sorted(suitable_videos, key=lambda x: x['new_words_pnt'])

    # Save result to DB
    mongo_db['users'].replace_one(
        {'email': current_user.email},
        {
            'email': current_user.email,
            'vocabulary': words_separator.join(sorted(vocabulary)),
            'suitable_videos': suitable_videos,
            'watched_videos': watched_videos
        },
        upsert=True
    )


if __name__ == '__main__':
    app.run(port=5000, debug=True)
