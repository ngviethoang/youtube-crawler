# -*- coding: utf-8 -*-
import requests
from googleapiclient.errors import HttpError
from unidecode import unidecode
from apiclient.discovery import build

import argparse
import json
import csv
from xml.etree import ElementTree
import re
from HTMLParser import HTMLParser

htmlParser = HTMLParser()


DEVELOPER_KEY = "AIzaSyACCj3LAKVJva3wG8QOczho-spqORzyK_E"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"


class YoutubeAPI:

    def __init__(self):
        self.api = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)

    def search_videos(self, options):
        videos = []

        i = 0
        page_token = None

        while i < options.max_results:
            max_results = min(options.max_results - i, 50)
            i += max_results

            if page_token is None:
                response_search = self.api.search() \
                    .list(q=options.q, part="id,snippet", maxResults=max_results, type='video') \
                    .execute()
            else:
                response_search = self.api.search() \
                    .list(q=options.q, part="id,snippet", maxResults=max_results, type='video', pageToken=page_token) \
                    .execute()

            page_token = response_search['nextPageToken']

            for result_search in response_search.get("items", []):
                if result_search["id"]["kind"] == "youtube#video":
                    video_id = result_search["id"]["videoId"]

                    title = result_search["snippet"]["title"]
                    title = unidecode(title)

                    videos.append(dict(
                        id=video_id,
                        title=title
                    ))

        return videos

    def list_statistics(self, video_id):
        video_statistics = dict(
            commentCount=0,
            dislikeCount=0,
            favoriteCount=0,
            likeCount=0,
            viewCount=0
        )

        response_statistics = self.api.videos().list(id=video_id, part="statistics").execute()
        for result_statistics in response_statistics.get("items", []):
            statistics = result_statistics['statistics']
            for key in statistics.keys():
                video_statistics[key] = int(statistics[key])
            break  # get first item

        return video_statistics

    def list_captions(self, video_id):
        response_captions = self.api.captions().list(
            part="snippet",
            videoId=video_id
        ).execute()

        return response_captions.get('items', [])

    @staticmethod
    def download_caption(video_id, language):
        r = requests.get('http://video.google.com/timedtext?lang={}&v={}'.format(language, video_id))
        captions = []

        try:
            root = ElementTree.fromstring(r.content)
            for child in root._children:
                captions.append(child.text)
        except ElementTree.ParseError:
            return None

        captions = list(filter(lambda c: c is not None, captions))
        captions = ' '.join(captions)
        captions = re.sub(r'\n', ' ', captions)
        captions = htmlParser.unescape(captions)
        captions = captions.encode('utf-8')

        return captions


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Search on YouTube')
    parser.add_argument("--q", help="Search term", default="Google")
    parser.add_argument("--max-results", help="Max results", default=20)
    parser.add_argument("--output", help="Output Name", default="output.csv")
    args = parser.parse_args()

    args.max_results = int(args.max_results)

    youtubeAPI = YoutubeAPI()

    videos = []

    print('Search Youtube: {}, max results: {}'.format(args.q, args.max_results))
    search_videos = youtubeAPI.search_videos(args)

    for search_video in search_videos:
        print('list statistics: ' + search_video['id'])
        statistics = youtubeAPI.list_statistics(search_video['id'])
        for k in statistics.keys():
            search_video[k] = statistics[k]

        print('download captions: ' + search_video['id'])
        # video_captions = None
        # print('list captions: ' + search_video['id'])
        # list_captions = youtubeAPI.list_captions(search_video['id'])
        # for caption in list_captions:
        #     language = caption['snippet']['language']
        #     if language in ['en']:
        #         video_captions = youtubeAPI.download_caption(search_video['id'], language)

        video_captions = youtubeAPI.download_caption(search_video['id'], 'en')

        search_video['captions'] = video_captions

        videos.append(search_video)

    # Export to CSV
    with open('video_result.csv', 'w') as csvFile:
        csvWriter = csv.writer(csvFile)

        if len(videos):
            csvWriter.writerow(videos[0].keys())

            for video in videos:
                csvWriter.writerow([video[k] for k in video.keys()])
