# -*- coding: utf-8 -*-
import spacy

from spacy.lang.en import English

import nltk
from nltk.stem.wordnet import WordNetLemmatizer
from nltk.corpus import wordnet as wn

from gensim import corpora
import pickle

import gensim

from mongo_db import get_mongo_db

mongo_db = get_mongo_db()

spacy.load('en')
parser = English()


def tokenize(text):
    lda_tokens = []
    tokens = parser(text)
    for token in tokens:
        if token.orth_.isspace():
            continue
        elif token.like_url:
            lda_tokens.append('URL')
        elif token.orth_.startswith('@'):
            lda_tokens.append('SCREEN_NAME')
        else:
            lda_tokens.append(token.lower_)
    return lda_tokens


nltk.download('wordnet')


def get_lemma(word):
    lemma = wn.morphy(word)
    if lemma is None:
        return word
    else:
        return lemma


def get_lemma2(word):
    return WordNetLemmatizer().lemmatize(word)


nltk.download('stopwords')
en_stop = set(nltk.corpus.stopwords.words('english'))


def prepare_text_for_lda(text):
    tokens = tokenize(text)
    tokens = [token for token in tokens if len(token) > 4]
    tokens = [token for token in tokens if token not in en_stop]
    tokens = [get_lemma(token) for token in tokens]
    return tokens


if __name__ == "__main__":
    res_videos = mongo_db.find({'subtitle': {'$ne': None}})
    print(res_videos.count())

    videos = []
    for video in res_videos:
        tokens = prepare_text_for_lda(video['subtitle'])
        video['tokens'] = tokens
        videos.append(video)

    # train data
    train_videos = videos[:800]
    test_videos = videos[800:]

    text_data = []
    for video in train_videos:
        text_data.append(video['tokens'])

    dictionary = corpora.Dictionary(text_data)
    corpus = [dictionary.doc2bow(text) for text in text_data]

    pickle.dump(corpus, open('corpus.pkl', 'wb'))
    dictionary.save('dictionary.gensim')

    # get topics
    NUM_TOPICS = 64
    ldamodel = gensim.models.ldamodel.LdaModel(corpus, num_topics=NUM_TOPICS, id2word=dictionary, passes=15)
    ldamodel.save('model5.gensim')
    topics = ldamodel.print_topics(num_words=4)
    for topic in topics:
        print(topic)

    for video in test_videos:
        doc_bow = dictionary.doc2bow(video['tokens'])
        doc_topics = ldamodel.get_document_topics(doc_bow)

        pass

    print(1)
