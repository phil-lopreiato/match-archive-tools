#!/usr/bin/python

import httplib
import httplib2
import os
import random
import sys
import time
import re
import csv
import argparse

from apiclient.discovery import build
from apiclient.errors import HttpError
from apiclient.http import MediaFileUpload
from oauth2client.client import flow_from_clientsecrets
from oauth2client.file import Storage
from oauth2client.tools import argparser, run_flow
from subprocess import call


# Explicitly tell the underlying HTTP transport library not to retry, since
# we are handling retry logic ourselves.
httplib2.RETRIES = 1

# Maximum number of times to retry before giving up.
MAX_RETRIES = 10

# Always retry when these exceptions are raised.
RETRIABLE_EXCEPTIONS = (httplib2.HttpLib2Error, IOError, httplib.NotConnected,
  httplib.IncompleteRead, httplib.ImproperConnectionState,
  httplib.CannotSendRequest, httplib.CannotSendHeader,
  httplib.ResponseNotReady, httplib.BadStatusLine)

# Always retry when an apiclient.errors.HttpError with one of these status
# codes is raised.
RETRIABLE_STATUS_CODES = [500, 502, 503, 504]

# The CLIENT_SECRETS_FILE variable specifies the name of a file that contains
# the OAuth 2.0 information for this application, including its client_id and
# client_secret. You can acquire an OAuth 2.0 client ID and client secret from
# the {{ Google Cloud Console }} at
# {{ https://cloud.google.com/console }}.
# Please ensure that you have enabled the YouTube Data API for your project.
# For more information about using OAuth2 to access the YouTube Data API, see:
#   https://developers.google.com/youtube/v3/guides/authentication
# For more information about the client_secrets.json file format, see:
#   https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
CLIENT_SECRETS_FILE = "../client-secret-match_splitter.json"

# This OAuth 2.0 access scope allows an application to upload files to the
# authenticated user's YouTube channel, but doesn't allow other types of access.
YOUTUBE_UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# This variable defines a message to display if the CLIENT_SECRETS_FILE is
# missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
WARNING: Please configure OAuth 2.0

To make this sample run you will need to populate the client_secrets.json file
found at:

   %s

with information from the {{ Cloud Console }}
{{ https://cloud.google.com/console }}

For more information about the client_secrets.json file format, please visit:
https://developers.google.com/api-client-library/python/guide/aaa_client_secrets
""" % os.path.abspath(os.path.join(os.path.dirname(__file__),
                                   CLIENT_SECRETS_FILE))

VALID_PRIVACY_STATUSES = ("public", "private", "unlisted")


def get_authenticated_service(args):
  flow = flow_from_clientsecrets(CLIENT_SECRETS_FILE,
    scope=YOUTUBE_UPLOAD_SCOPE,
    message=MISSING_CLIENT_SECRETS_MESSAGE)

  storage = Storage("%s-oauth2.json" % sys.argv[0])
  credentials = storage.get()

  if args.reauth=="true" or credentials is None or credentials.invalid:
    credentials = run_flow(flow, storage, args)

  return build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION,
    http=credentials.authorize(httplib2.Http()))

def generate_csv(matchKeys,urls):
    with open('uploads.csv', 'wb') as csvfile:
        writer = csv.writer(csvfile, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for title,url in zip(matchKeys,urls):
            year = str(title)[:4]
            split=re.split("_",title)
            event = str(split[0])[4:]
            if "qm" in split[1]:
                matchType = "q"
                matchNum = str(split[1])[2:]
            elif "qf" in split[1] or "sf" in split[1]:
                matchType = str(split[1])[:3]
                matchNum = str(split[1])[4:]
            else:
                matchType = "f"
                matchNum = str(split[1])[3:]
            writer.writerow([year,event,matchType,matchNum,"http://www.youtube.com/watch?v="+url])
    print "Data Written to ./uploads.csv for copy/paste into TBA spreadsheet"

def initialize_upload(youtube, videos):
    keys=[]
    urls=[]
    for video in videos:
      path = "./matches/"+video
      tags = None
      vidTitle= os.path.splitext(video)[0].lower()
      tbaurl = "http://thebluealliance.com/match/"+vidTitle
      body = dict(
        snippet=dict(
          title=vidTitle,
          description=tbaurl,
          tags=tags
        ),
        status=dict(
          privacyStatus="public"
        )
      )
    
      # Call the API's videos.insert method to create and upload the video.
      insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        # The chunksize parameter specifies the size of each chunk of data, in
        # bytes, that will be uploaded at a time. Set a higher value for
        # reliable connections as fewer chunks lead to faster uploads. Set a lower
        # value for better recovery on less reliable connections.
        #
        # Setting "chunksize" equal to -1 in the code below means that the entire
        # file will be uploaded in a single HTTP request. (If the upload fails,
        # it will still be retried where it left off.) This is usually a best
        # practice, but if you're using Python older than 2.6 or if you're
        # running on App Engine, you should set the chunksize to something like
        # 1024 * 1024 (1 megabyte).
        media_body=MediaFileUpload(path, chunksize=-1, resumable=True)
      )
    
      u = resumable_upload(insert_request)
      keys.append(vidTitle)
      urls.append(u)

    generate_csv(keys,urls) 

# This method implements an exponential backoff strategy to resume a
# failed upload.
def resumable_upload(insert_request):
  response = None
  error = None
  retry = 0
  while response is None:
    try:
      print "Uploading file..."
      status, response = insert_request.next_chunk()
      if 'id' in response:
        print "Video id '%s' was successfully uploaded." % response['id']
        return response['id']
      else:
        exit("The upload failed with an unexpected response: %s" % response)
    except HttpError, e:
      if e.resp.status in RETRIABLE_STATUS_CODES:
        error = "A retriable HTTP error %d occurred:\n%s" % (e.resp.status,
                                                             e.content)
      else:
        raise
    except RETRIABLE_EXCEPTIONS, e:
      error = "A retriable error occurred: %s" % e

    if error is not None:
      print error
      retry += 1
      if retry > MAX_RETRIES:
        exit("No longer attempting to retry.")

      max_sleep = 2 ** retry
      sleep_seconds = random.random() * max_sleep
      print "Sleeping %f seconds and then retrying..." % sleep_seconds
      time.sleep(sleep_seconds)

def split_video(options):
    if not os.path.exists("./matches"): os.mkdir("./matches")
    videos = []
    ext = os.path.splitext(options.file)[-1].lower()
    over = ""
    if "overwrite" in options:
        over = " -y "
    with open(options.times, 'rb') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for time in reader:
            if(time[0].strip()==""):continue
            if re.match("\d{1,2}:\d{1,2}:\d{1,2}",time[1]):
                print "extracting match "+time[0]+", starting at "+time[1]
                call("ffmpeg "+over+"-ss "+time[1]+" -t "+options.length+" -i "+options.file+" -vcodec copy -acodec copy ./matches/"+time[0]+ext,shell=True)
                videos.append(time[0]+ext)
    return videos
    

if __name__ == '__main__':
    #argparser = argparse.ArgumentParser(description='Extract matches from an input video file and upload them to youtube')
    argparser.add_argument("-f","--file", required=True, help="Video file to split and upload")
    argparser.add_argument("-t","--times", required=True, help="CSV file of match info, one match per line - formatted tba_match_key,hh:mm:ss")
    argparser.add_argument("-l","--length",dest="length",default="00:03:00",help="Length of video to cut out after the start point. Defaults to 3 minutes")
    argparser.add_argument("--skip-upload",action="store_true",dest="skip",default="false",help="doesn't upload videos to YouTube, only extracts them")
    argparser.add_argument("--force-auth",action="store_true",dest="reauth",default="false",help="force authentication with YouTube API")
    argparser.add_argument("-y","--overwrite",action="store_true", dest="overwrite",help="Overwrite videos? Runs ffmpeg with -y flag")
    args = argparser.parse_args()

    if not os.path.exists(args.file):
        exit("Please specify a valid video file using the --file parameter.")
        
    if not os.path.exists(args.times):
        exit("Please specify a valid video data file using the --times parameter.")

    videos = split_video(args)
    if(args.skip=="false"):
        youtube = get_authenticated_service(args)
        try:
            initialize_upload(youtube, videos)
        except HttpError, e:
            print "An HTTP error %d occurred:\n%s" % (e.resp.status, e.content)

