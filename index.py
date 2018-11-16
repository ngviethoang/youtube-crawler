# -*- coding: utf-8 -*-
from flask import Flask, render_template, jsonify, request
from mongo_db import get_mongo_db

mongo_db = get_mongo_db()


class CustomFlask(Flask):
    jinja_options = Flask.jinja_options.copy()
    jinja_options.update(dict(
        variable_start_string='%%',  # Default is '{{', I'm changing this because Vue.js uses '{{' / '}}'
        variable_end_string='%%',
    ))


app = CustomFlask(__name__)  # This replaces your existing "app = Flask(__name__)"


@app.route('/')
def main():
    return render_template('index.html')


@app.route('/videos')
def get_videos():
    args = request.args

    nPerPage = int(args['limit'])
    pageNumber = int(args['page'])
    order = int(args['order'])
    vocab_num = args['vocab_num']

    res_videos = mongo_db.find({'subtitle': {'$ne': None}})\
        .sort('stats.{}.new_words_pnt'.format(vocab_num), order)\
        .skip((pageNumber - 1) * nPerPage if pageNumber > 0 else 0)\
        .limit(nPerPage)

    videos = []

    for res_video in res_videos:
        video = dict(
            id=res_video['id'],
            title=res_video['title'],
            channelTitle=res_video['snippet']['channelTitle'],
            description=res_video['snippet']['description'],
            thumbnail=res_video['snippet']['thumbnails']['medium']['url'],
            stats=res_video['stats'][vocab_num],
            subtitle=res_video['subtitle'],
            subtitle_words=res_video['subtitle_words'],
        )
        videos.append(video)

    return jsonify(dict(
        videos=videos
    ))


if __name__ == '__main__':
    app.run(port='5000', debug=True)
