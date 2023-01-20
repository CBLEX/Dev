# -*- coding: utf-8 -*-

# This code is based on sample Python code for youtube.captions.download API https://developers.google.com/youtube/v3/docs/captions/download
# This code also uses the youtube_transcript_api API https://github.com/jdepoix/youtube-transcript-api/blob/master/youtube_transcript_api/_api.py

# NOTE: To use this code, you must run it locally using your own google API credentials.
# See instructions for running code locally using your own API credentials:
# https://developers.google.com/explorer-help/code-samples#python
# TODO : edit file to insert your credentials in client_secrets_file (line 59)

# Usage: py getcaptions.py [videoid]    // for a single video 
# Usage: py getcaptions.py [csvfilename] [colname]   // for multiple videos provided in a csv file:csvfilename in column : colname
# This python program will extract all the metadata available in Youtube for the provided videoid

#last modified by KKeogh k.keogh@federation.edu.au August 2022

#the purpose of this program is to extract Youtube video meta data for provided youtube video urls save the title of each video to a spreadsheet

import io
import os
import google_auth_oauthlib.flow
import googleapiclient.errors
import json
import csv

from google.auth.transport.requests import Request
from google.oauth2 import credentials
from google_auth_oauthlib.flow import InstalledAppFlow

from googleapiclient import discovery
from googleapiclient.http import MediaIoBaseDownload
from google.auth.transport.requests import Request

from youtube_transcript_api import YouTubeTranscriptApi  			# this line added kkeogh 10 08 2021
from youtube_transcript_api.formatters import Formatter
from youtube_transcript_api.formatters import JSONFormatter

from pandas import read_csv


SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]
#scopes = ["https://www.googleapis.com/auth/youtube.readonly"]  # need stronger scope as given in line above

#modify next line to name the output file prefix - output will be stored in OUTPUTFILENAME+videoid.txt
OUTPUTFILENAME="VideoMetaData/Video"
OUTPUTDIR="VideoMetaData/"
tracefile=open("VideoMetaData_logfile","w",encoding='utf-8')
videoTitleDict = {"video_url":"video title"}

def getcredentials():
    # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    api_service_name = "youtube"
    api_version = "v3"
    #TODO Change this file to point to your credentials for Google API
    client_secrets_file = "clientsecretfiledesktop.json"
    creds= None
    
    try:
        #authorise youtube access by using localhost request redirection
        TOKENS = 'storage.json'
        if os.path.exists(TOKENS):
            creds = credentials.Credentials.from_authorized_user_file(TOKENS)
        if not (creds and creds.valid):  #credentials have expired get new credentials
            flow = InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
            creds = flow.run_local_server()
        #store credentials in TOKENS file for next time
        with open(TOKENS, 'w') as token:
            token.write(creds.to_json())
        myyoutube=discovery.build(api_service_name, api_version, credentials=creds)
    except Exception as err:
        tracefile.write("\nException {0}".format(err)+ " occurred getting credentials to acccess youtube, trying again.")
        # try again to use secret file to get authorisation of youtube request
        # Get credentials and create an API client
        flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(client_secrets_file, SCOPES)
        creds = flow.run_console()
        myyoutube = googleapiclient.discovery.build(api_service_name, api_version, credentials=creds)
        
    return myyoutube

#This function will get a public video caption if it is available on the youtube video It will also retrieve meta data about the video
def getvideodetails(youtube, vid):
    try:
        title=' '
        ofilemeta=open(OUTPUTFILENAME+vid+"MetaData.txt","a", encoding='utf-8')

        youtubevideoid=vid
        request = youtube.videos().list(
            part="snippet,contentDetails,status,statistics",
            id=youtubevideoid
        )
        video_metadataresponse = request.execute()
##        print('video list (metadata for the video): ')
##        print(video_metadataresponse)
        formatter=JSONFormatter()
        json_formatted= formatter.format_transcript(video_metadataresponse)
        ofilemeta.write(json_formatted)
        

        videodict=json.loads(json.dumps(video_metadataresponse))
        videodetail = videodict.get('items')
##        print("video metaitems retrieved for "+vid)
##        print(videodetail)

        theid = videodetail[0].get("id")   #get the video id (hopefully theid is the same as vid)
        title = videodetail[0].get("snippet").get("title")
        channeltitle = videodetail[0].get("snippet").get("channelTitle")
        
        osummaryfile=open(OUTPUTFILENAME+"Summary Information"+vid+".txt", 'w', encoding='utf-8')
        osummaryfile.write("\nVideo id : "+theid)
        osummaryfile.write("\nVideo url : "+vid)
        osummaryfile.write("\nTitle : "+title)
        osummaryfile.write("\nChannel Title : "+channeltitle)
        osummaryfile.close()
        videoTitleDict[vid]=title   #save title in dictionary for later reference


       # now create a file where the downloaded content should be written.
        fh = io.FileIO(OUTPUTFILENAME+theid+".json", "wb")

        #first save the videos().list response
        download = MediaIoBaseDownload(fh, request)
        complete = False
        while not complete:
          status, complete = download.next_chunk()

        fh.close()

        #now look in more detail at the captions
        
        
        if not captionslist: #captionlist is empty
            ofilemeta.write("\n{\t\"caption\": { No captions available} \n")
            ofilemeta.close()
            #print("No captions available")
            failed=1
        else:           
            ofile.write("\n}\n\n")
            ofile.write("{\"rawcaption\": "+captiononly+"}\n")
            ofile.close()
            ofilemeta.close()
            ofile=open(OUTPUTFILENAME+vid+"RawCaptions.txt", 'a', encoding='utf-8')
            ofile.write(captiononly)
            failed=0

    except Exception as err:
        videoTitleDict[vid]="Exception occurred, title not saved"
        title=videoTitleDict[vid]
        ofilemeta=open(OUTPUTFILENAME+vid+"metaData","a", encoding='utf-8')

        ofilemeta.write("\n{\t\"caption\": { No captions available or exception occurred} }\n")
        
        #print("Exception {0}".format(err), " occurred with "+str(vid))
        tracefile.write("Exception {0}".format(err))
        tracefile.write(" occurred with ")
        tracefile.write(vid)
        #print("failed on first attempt to get captions for ",vid)
        tracefile.write("\nfailed on first attempt to get meta details "+vid)
        failed=1
        ofilemeta.close()
        ofile=open(OUTPUTFILENAME+vid+"Exception.txt", 'a', encoding='utf-8')
        ofile.write("\nException {0}".format(err))
        ofile.write(" occurred with ")
        ofile.write(vid)
        ofile.close()
              
    return failed, title  # return 1 or 0 to indicate if it failed or not (0 means success) 
      
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2: #if there is only one argument provided assume that is the video id of a youtube video.
        youtube=getcredentials()
        vid = sys.argv[1]
        fail,title=getvideodetails(youtube, vid)  #this also gets meta information about the video
        
        
    elif len(sys.argv) == 3:   # if there are two arguments provided, then assume these are filename and column name for a csv file with multiple video ids for youtube
        summaryfile=open("summary","w",encoding='utf-8')
        youtube=getcredentials()
        videofilename = sys.argv[1]
        colname = sys.argv[2]
        # read CSV file provided named in videofilename the 2rd argument expect a column name in the csv as named in 3rd argument
        csvread = open(videofilename, newline='\n')
        csvreader = read_csv(csvread)
        csvread.close()
        #create a list of youtube video ids from csvreader file in column with colname provided
        allvideos=csvreader[colname].tolist()

        csvwrite=open(videodetails+"_withtitles.csv", 'w', newline='')
        #for each video first attempt to get video captions if they are available - not likely to return many transcripts directly this way
        for videoid in allvideos:
            title=' ' #set to blank in case of failure
            fail,title = getvideodetails(youtube,videoid)
            summaryfile.write(videoid+" "+title+" "+videoTitleDict[videoid]+"\n")
        #use the Youtubetranscript API to get transcripts for multiple videos
        summaryfile.close()
        csvwrite.close()
               
    else:
        print('Usage: py getmetadata.py [videoid]  or py getmetadata.py [video_csvfilename.csv] [videoid_colname]')
