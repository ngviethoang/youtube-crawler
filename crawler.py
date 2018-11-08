# -*- coding: utf-8 -*-
import requests
from googleapiclient.errors import HttpError
from unidecode import unidecode
from apiclient.discovery import build

from xml.etree import ElementTree
import re
from HTMLParser import HTMLParser
from mongo_db import get_mongo_db
import os

mongo_db = get_mongo_db()

htmlParser = HTMLParser()

YOUTUBE_DEVELOPER_KEY = "AIzaSyACCj3LAKVJva3wG8QOczho-spqORzyK_E"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


class YoutubeAPI:

    def __init__(self):
        self.api = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=YOUTUBE_DEVELOPER_KEY)

    def get_channel_id(self, user_name):
        response = self.api.channels().list(forUsername=user_name, part='id').execute()
        if len(response['items']):
            return response['items'][0]['id']
        return None

    def get_videos_from_channel(self, channel_id, max_results=None):
        videos = []

        response = self.api.search() \
            .list(order='date', part='snippet', regionCode='US',
                  channelId=channel_id, maxResults=50, type='video') \
            .execute()

        responses_all = [response]

        totalResults = response['pageInfo']['totalResults']

        videos += response['items']

        while len(videos) < totalResults and 'nextPageToken' in response:
            page_token = response['nextPageToken']

            response = self.api.search() \
                .list(order='date', part='snippet', regionCode='US',
                      channelId=channel_id, maxResults=50, type='video', pageToken=page_token) \
                .execute()

            responses_all.append(response)

            videos += response['items']

            if max_results is not None and len(videos) > max_results:
                return videos[:max_results]

        return videos

    @staticmethod
    def get_subtitles(video_id, language):
        r = requests.get('http://video.google.com/timedtext?lang={}&v={}'.format(language, video_id))
        subtitles = []

        try:
            root = ElementTree.fromstring(r.content)
            for child in root._children:
                subtitles.append(child.text)
        except ElementTree.ParseError:
            return None

        subtitles = list(filter(lambda c: c is not None, subtitles))
        subtitles = ' '.join(subtitles)
        subtitles = re.sub(r'\n', ' ', subtitles)
        subtitles = htmlParser.unescape(subtitles)
        subtitles = subtitles.encode('utf-8')

        return subtitles


if __name__ == "__main__":
    channel_names = [
        'TEDtalksDirector',
        'TEDEducation'
    ]

    youtubeAPI = YoutubeAPI()

    for channel_name in channel_names:
        channel_id = youtubeAPI.get_channel_id(channel_name)
        print('Get channel id {} from {}'.format(channel_id, channel_name))
        if channel_id is not None:
            videos = youtubeAPI.get_videos_from_channel(channel_id, max_results=None)
            print('Get {} videos'.format(len(videos)))

            print('Downloading subtitles...')

            videos = list(map(lambda v: dict(
                id=v['id']['videoId'],
                title=v['snippet']['title'],
                channel_name=channel_name,
                subtitle=YoutubeAPI.get_subtitles(v['id']['videoId'], 'en'),
            ), videos))

            subtitle_videos = list(filter(lambda v: v['subtitle'] is not None, videos))
            print('Get {} videos with english subtitles'.format(len(subtitle_videos)))

            print('Inserting to db...')
            mongo_db.insert_many(videos)
