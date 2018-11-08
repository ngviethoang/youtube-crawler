# -*- coding: utf-8 -*-
import pymongo
import os


def get_mongo_db():
    MONGO_URI = "mongodb://localhost:27017"
    MONGO_DATABASE = "youtube"
    MONGO_COLLECTION = "subtitles"

    mongo_db = pymongo.MongoClient(MONGO_URI)[MONGO_DATABASE]

    return mongo_db[MONGO_COLLECTION]
