# -*- coding: utf-8 -*-
from topic_modeling import prepare_text_for_lda

from mongo_db import get_mongo_db

mongo_db = get_mongo_db()


# tokenize video's subtitle
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


# stemming of words
def stem_words(words):
    porter = PorterStemmer()
    words = set([porter.stem(word) for word in words])

    return words


def update_subtitle_words():
    print('normalizing subtitle...')

    # Get videos from DB
    videos = mongo_db.find({'subtitle': {'$ne': None}})

    for video in videos:
        subtitle_words = clean_text(video['subtitle'])
        # subtitle_words = stem_words(subtitle_words)

        mongo_db.update_one(
            {'id': video['id']},
            {
                '$set': {
                    'subtitle_words': ' '.join(set(subtitle_words)),
                }
            }
        )


if __name__ == "__main__":
    # update_subtitle_words()

    # Get common words list
    with open('common_words.txt', 'r') as f:
        common_words = f.readlines()
    common_words = [w.strip() for w in common_words]
    # common_words = stem_words(common_words)

    common_words_number_list = [3000, 6000, 10000]

    # Get videos from DB
    videos = mongo_db.find({'subtitle': {'$ne': None}})
    print(videos.count())

    for video in videos:
        subtitle_words = set(video['subtitle_words'].split())

        stats = dict()

        for common_words_number in common_words_number_list:
            new_words = subtitle_words - set(common_words[:common_words_number])
            new_words_pnt = round(float(len(new_words)) / len(subtitle_words) * 100, 2)

            stats[str(common_words_number)] = dict(
                new_words=' '.join(new_words),
                new_words_pnt=new_words_pnt
            )

        mongo_db.update_one(
            {'id': video['id']},
            {
                '$set': {
                    'stats': stats
                }
            }
        )
