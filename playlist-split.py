
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
CLIENT_SECRETS_FILE = "../client-secret-match_splitter.json"

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

def process_titles(titles,urls,options):
    eventKey = str(options.key)
    year = eventKey[:4]
    event = eventKey[4:]
    matchType=""
    matchNum=""
    p = re.compile("^\d")
    
    if(options.output == ""):
	#process a playlist
	dataFile = options.key+"_matches.csv"
    else:
	#dump youtube data to file
	dataFile = options.user+"_uploads.csv"

    with open(dataFile, "a") as csvfile:
        writer = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for title,url in zip(titles,urls):
            if(not options.output == ""):
		#just write all the data to a file
		writer.writerow([str(title),url])
		continue

	    #process the title and generate row for copy/paste into TBA spreadsheet
  	    expl = re.split("\s",title)
	    match = False
	    if("Q-" in title):
		matchType = "q"
		matchNum = str(expl[0])[2:]
	    if(True):
	    	print title
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
                 video_data = youtube.videos().list(part='snippet',
                                                    id=video["snippet"]["resourceId"]["videoId"]).execute()
                 for v in video_data.get("items",[]):
                     videos.append(video["snippet"]["resourceId"]["videoId"])
                     titles.append(v["snippet"]["title"])
    print "Videos:\n", "\n".join(videos), "\n"
    print "Num: ",len(videos)
    process_titles(titles,videos,options)

def get_upload_playlist(args):
    youtube = get_authenticated_service()
    channels_response = youtube.channels().list(part="contentDetails",forUsername=args.user).execute()
    for channel in channels_response["items"]:
  	# From the API response, extract the playlist ID that identifies the list
  	# of videos uploaded to the authenticated user's channel.
  	uploads_list_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
    	print uploads_list_id
    	return uploads_list_id
    

if __name__ == "__main__":
  parser = OptionParser()
  parser.add_option("--playlist", dest="playlist",help="ID of playlsit to parse")
  parser.add_option("--user",dest="user",default="",help="Username to fetch all uploads for")
  parser.add_option("--key", dest="key",help="Full TBA event key")
  parser.add_option("--output",dest="output",help="csv file to output Youtube data to")
  parser.add_option("--file",dest="file",help="csv file to use instead of querying YouTube over and over")
  (options, args) = parser.parse_args()
  
  if(not options.user == ""):
  	options.playlist = get_upload_playlist(options)

  process_playlist(options)

  
