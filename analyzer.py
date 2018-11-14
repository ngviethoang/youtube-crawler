# -*- coding: utf-8 -*-
import pymongo

from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem.porter import PorterStemmer

from mongo_db import get_mongo_db

mongo_db = get_mongo_db()


def clean_text(text):
    if text is None:
        return []

    tokens = word_tokenize(text)

    # convert to lower case
    tokens = [w.lower() for w in tokens]

    # remove all tokens that are not alphabetic
    words = [word for word in tokens if word.isalpha()]

    words = set(words)

    # filter out stop words
    stop_words = set(stopwords.words('english'))
    words = [w for w in words if not w in stop_words]

    return words


def stem_words(words):
    # stemming of words
    porter = PorterStemmer()
    words = set([porter.stem(word) for word in words])

    return words


if __name__ == "__main__":
    # Get common words list
    with open('common_words.txt', 'r') as f:
        common_words = f.readlines()
    common_words = [w.strip() for w in common_words]
    common_words = stem_words(common_words)

    # Get videos from DB
    videos = mongo_db.find({'subtitle': {'$ne': None}})
    print(videos.count())

    for video in videos:
        subtitle = video['subtitle']
        subtitle_words = clean_text(subtitle)
        subtitle_words = stem_words(subtitle_words)

        overlap = common_words & subtitle_words
        overlap_pnt = float(len(overlap)) / len(subtitle_words) * 100

        mongo_db.update_one(
            {'id': video['id']},
            {
                '$set': {
                    'stats': {
                        'subtitle_words': list(subtitle_words),
                        'overlap': list(overlap),
                        'overlap_pnt': overlap_pnt
                    }
                }
            }
        )
