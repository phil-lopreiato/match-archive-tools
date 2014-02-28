
#!/usr/bin/python

import httplib2
import os
import random
import sys
import time
import csv
import re

from apiclient.discovery import build
from apiclient.errors import HttpError
from oauth2client.file import Storage
from oauth2client.client import flow_from_clientsecrets
from oauth2client.tools import run
from optparse import OptionParser


# CLIENT_SECRETS_FILE, name of a file containing the OAuth 2.0 information for
# this application, including client_id and client_secret. You can acquire an
# ID/secret pair from the API Access tab on the Google APIs Console
#   http://code.google.com/apis/console#access
# For more information about using OAuth2 to access Google APIs, please visit:
#   https://developers.google.com/accounts/docs/OAuth2
# For more information about the client_secrets.json file format, please visit:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
# Please ensure that you have enabled the YouTube Data API for your project.
CLIENT_SECRETS_FILE = "../client_secrets.json"

# An OAuth 2 access scope that allows for full read/write access.
YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Helpful message to display if the CLIENT_SECRETS_FILE is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the APIs Console
https://code.google.com/apis/console#access

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

def get_authenticated_service():
  flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE, scope=YOUTUBE_SCOPE,
    message=MISSING_CLIENT_SECRETS_MESSAGE)

  storage = Storage("%s-oauth2.json" % sys.argv[0])
  credentials = storage.get()

  if credentials is None or credentials.invalid:
    credentials = run(flow, storage)

  return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    http=credentials.authorize(httplib2.Http()))


def youtube_search(options):
  youtube = get_authenticated_service()

  search_response = youtube.search().list(
    q="meow",
    part="id,snippet",
    maxResults=3
  ).execute()

  videos = []
  channels = []
  playlists = []

  for search_result in search_response.get("items", []):
    if search_result["id"]["kind"] == "youtube#video":
      videos.append("%s (%s)" % (search_result["snippet"]["title"],
                                 search_result["id"]["videoId"]))
    elif search_result["id"]["kind"] == "youtube#channel":
      channels.append("%s (%s)" % (search_result["snippet"]["title"],
                                   search_result["id"]["channelId"]))
    elif search_result["id"]["kind"] == "youtube#playlist":
      playlists.append("%s (%s)" % (search_result["snippet"]["title"],
                                    search_result["id"]["playlistId"]))

  print "Videos:\n", "\n".join(videos), "\n"
  print "Channels:\n", "\n".join(channels), "\n"
  print "Playlists:\n", "\n".join(playlists), "\n"
    
def process_titles(titles,urls,options):
    eventKey = str(options.key)
    year = eventKey[:4]
    event = eventKey[4:]
    matchType=""
    matchNum=""
    p = re.compile("^\d")
    
    with open('matches.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=' ',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for title,url in zip(titles,urls):
            print title
            expl = re.split("\s",title)
            '''if expl[0]==eventKey:
                valid=False
                if(p.match(expl[1])):
                    #qual match
                    matchType="q"
                    matchNum=expl[1]
                    valid=True
                else:
                    matchType=str(expl[1]).lower()+str(expl[2])[:1]
                    matchNum=str(expl[2])[2:]
                    valid=True'''
            matchType="q"
            matchNum=expl[5]
            valid=True
            if(valid):
                writer.writerow([year,event,matchType,matchNum,"http://www.youtube.com/watch?v="+url])

def process_playlist(options):
    youtube = get_authenticated_service()
    videos = []
    titles = []
    page=""
    stop=False
    while not stop: 
        if not 'page' in locals():
            break
        
        playlist = youtube.playlistItems().list(
                                                playlistId=options.playlist,
                                                part="id,snippet",
                                                maxResults=50,
                                                pageToken=page
                                                ).execute()
        if "nextPageToken" in playlist:
                page = playlist["nextPageToken"]
        else:
                stop=True       
        for video in playlist.get("items", []):
            if video["kind"] == "youtube#playlistItem" and video["snippet"]["resourceId"]["kind"] == "youtube#video":
                 video_data = youtube.videos().list(
                                                    part='snippet',
                                                    id=video["snippet"]["resourceId"]["videoId"]).execute()
                 for v in video_data.get("items",[]):
                     videos.append(video["snippet"]["resourceId"]["videoId"])
                     titles.append(v["snippet"]["title"])
    print "Videos:\n", "\n".join(videos), "\n"
    print "Num: ",len(videos)
    process_titles(titles,videos,options)

if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("--playlist", dest="playlist",
    help="ID of playlsit to parse")
  parser.add_option("--key", dest="key",
    help="Full TBA event key")
  (options, args) = parser.parse_args()
  
  process_playlist(options)
  # youtube_search(options)
  
