# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_mongoengine import MongoEngine, Document
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import Email, Length, InputRequired
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


# app = Flask(__name__)


class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        variable_start_string='%%',  # Default is '{{', I'm changing this because Vue.js uses '{{' / '}}'
        variable_end_string='%%',
    ))


app = CustomFlask(__name__)  # This replaces your existing "app = Flask(__name__)"

app.config['MONGODB_SETTINGS'] = {
    'db': 'mongodb://localhost:27017',
    'host': 'youtube'
}

db = MongoEngine(app)
app.config['SECRET_KEY'] = '1\x0c\xf6\xbf\xaa\xb9\xd0\xe7\xae\xdc\x07\xe6\xb7\xe3\xd3\x90\xd3\x13bG\xb5(\xfa\xc9'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin, db.Document):
    meta = {'collection': 'users'}
    name = db.StringField(max_length=30)
    email = db.StringField(max_length=30)
    password = db.StringField()


@login_manager.user_loader
def load_user(user_id):
    return User.objects(pk=user_id).first()


class RegForm(FlaskForm):
    name = StringField('name', validators=[InputRequired(), Length(min=8, max=20)])
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=30)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=20)])


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegForm()
    if request.method == 'POST':
        if form.validate():
            existing_user = User.objects(email=form.email.data).first()
            if existing_user is None:
                hashpass = generate_password_hash(form.password.data, method='sha256')
                hey = User(form.email.data, hashpass).save()
                login_user(hey)
                return redirect(url_for('dashboard'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegForm()
    if request.method == 'POST':
        if form.validate():
            check_user = User.objects(email=form.email.data).first()
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
def main():
    return render_template('index.html', user=current_user.email)


@app.route('/videos')
@login_required
def get_videos():
    args = request.args

    nPerPage = int(args['limit'])
    pageNumber = int(args['page'])
    order = int(args['order'])
    vocab_num = args['vocab_num']

    # res_videos = mongo_db.find({'subtitle': {'$ne': None}}) \
    #     .sort('stats.{}.new_words_pnt'.format(vocab_num), order) \
    #     .skip((pageNumber - 1) * nPerPage if pageNumber > 0 else 0) \
    #     .limit(nPerPage)

    videos = []

    # for res_video in res_videos:
    #     video = dict(
    #         id=res_video['id'],
    #         title=res_video['title'],
    #         channelTitle=res_video['snippet']['channelTitle'],
    #         description=res_video['snippet']['description'],
    #         thumbnail=res_video['snippet']['thumbnails']['medium']['url'],
    #         stats=res_video['stats'][vocab_num],
    #         subtitle=res_video['subtitle'],
    #         subtitle_words=res_video['subtitle_words'],
    #     )
    #     videos.append(video)

    return jsonify(dict(
        videos=videos
    ))


if __name__ == '__main__':
    app.run(port=5000, debug=True)
