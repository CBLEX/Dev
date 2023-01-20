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
# It will also extract youtube captions if they are available for that video (note that availability may depend on user's permissions)
# output will be echoed to the screen and stored in OUTPUTFILENAME+videoid.txt

#last modified KKeogh k.keogh@federation.edu.au August 2022

#the purpose of this program is to extract Youtube video captions, meta data and transcripts in english and save these to files

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
OUTPUTFILENAME="Transcripts/Video"
OUTPUTDIR="Transcripts/"
tracefile=open("Transcripts/logfiletrace180820221330","w",encoding='utf-8')
videoTitleDict = dict()

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

#This function will get a public video caption if it is available on the youtube video (uncommented for now)
#It will also retrieve meta data about the video
def getvideocaption(youtube, vid):
    failed=0
    try:
        title=' '
        ofile=open(OUTPUTFILENAME+vid+"Captions.txt", 'a', encoding='utf-8')
        ofilemeta=open(OUTPUTFILENAME+vid+"MetaData","a", encoding='utf-8')

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
##        print(' the videoid is ')
##        print(theid)
##        print(' the video id passed in url was ')
##        print(vid)
##        print(' the title is ')
##        print(title)
##        print(' the channel title is ')
##        print(channeltitle)

        #get the captions list from youtube 
##uncomment this section if you think you have authorisation to access captions on the videos directly, otherwise, don't waste request quota
##        request2 = youtube.captions().list(
##            part="id,snippet",
##            videoId=youtubevideoid
##        )
##        response2 = request2.execute()
##                
##        captionslist=response2.get('items')
        #print (captionslist)  #saved to file below
        

       # now create a file where the downloaded content should be written.
        fh = io.FileIO(OUTPUTFILENAME+theid+".json", "wb")

        #first save the videos().list response
        download = MediaIoBaseDownload(fh, request)
        complete = False
        while not complete:
          status, complete = download.next_chunk()

        #now save the youtube.captions().list response
##uncomment this section if you think you have authorisation to directly access captions on the videos, otherwise, don't bother
##        download = MediaIoBaseDownload(fh, request2)
##        complete = False
##        while not complete:
##          status, complete = download.next_chunk()

        fh.close()

        #now look in more detail at the captions
##uncomment this section if you think you have authorisation to directly access captions on the videos, otherwise, don't bother
       
##        captionresponse=[]
##        for captionidreturned in captionslist:
##            captionid=captionidreturned.get('id')
####            print("captionid is ")
####            print(captionid)
##            ofile.write("\n{\t\"captionid\": "+captionid+",")
##            captiontrackKind = captionidreturned.get('snippet').get('trackKind')
##            ofile.write("\n\t\"trackType\": "+captiontrackKind+", (Note: asr means Automatic Speech Recognition) ")
###            print("caption trackType is (Note: asr means Automatic Speech Recognition) "+ captiontrackKind)
##            
##
##            #https://developers.google.com/youtube/v3/docs/captions/download
##            requestcaption= youtube.captions().download(
##                id=captionid,
##                tfmt='srt',  
##                prettyPrint=True
##            )
##            caption_response_item = requestcaption.execute().decode('utf-8')
##            caption_data = caption_response_item.split('\n\n')
##            ofile.write("\n\t\"caption\": {\n")
##            captiononly=""
##            #echo the captions to the screen output/ save to file 
##            for line in caption_data:
##                if line.count('\n') > 1:
##                    i, timecode, caption = line.split('\n', 2)
##                    captiononly=captiononly+caption+" "
##                    caption_line="\"time\": " +timecode + ", \n\t\t \"text\": \""+ ' '.join(caption.split())
##                    #one line at a time to save to file
##                    ofile.write("\n\t\t{" +caption_line+"\"")
##                    #echo the captions to the screen output
##                    #print('%02d) [%s] %s' % (
##                            #int(i), timecode, ' '.join(caption.split())))
##                #print
##                ofile.write("\n\t\t}")
##            
##        
##        if not captionslist: #captionlist is empty
##            ofile.write("\n{\t\"caption\": { No captions available} \n")
##            ofile.close()
##            ofilemeta.close()
##            #print("No captions available")
##            failed=1
##        else:           
##            ofile.write("\n}\n\n")
##            ofile.write("{\"rawcaption\": "+captiononly+"}\n")
##            ofile.close()
##            ofilemeta.close()
##            ofile=open(OUTPUTFILENAME+vid+"RawCaptions.txt", 'a', encoding='utf-8')
##            ofile.write(captiononly)
##            failed=0

    except Exception as err:
        ofile=open(OUTPUTFILENAME+vid+".txt", 'a', encoding='utf-8')
        ofilemeta=open(OUTPUTFILENAME+vid+"metaData","a", encoding='utf-8')

        ofile.write("\n{\t\"caption\": { No captions available or exception occurred} }\n")
        ofilemeta.write("\n{\t\"caption\": { No captions available or exception occurred} }\n")
        
        #print("Exception {0}".format(err), " occurred with "+str(vid))
        tracefile.write("Exception {0}".format(err))
        tracefile.write(" occurred with ")
        tracefile.write(vid)
        #print("failed on first attempt to get captions for ",vid)
        tracefile.write("\nfailed on first attempt to get captions for "+vid)
        failed=1
        ofile.close()
        ofilemeta.close()
        ofile=open(OUTPUTFILENAME+vid+"Exception.txt", 'a', encoding='utf-8')
        ofile.write("\nException {0}".format(err))
        ofile.write(" occurred with ")
        ofile.write(vid)
        ofile.close()
              
    return failed  # return 1 or 0 to indicate if it failed or not (0 means success)

def saveTranscriptFiles(videoid, mytranscript):
    textonly=''
    atranscriptdict=json.loads(json.dumps(mytranscript))
    #print (atranscriptdict)
    for field in mytranscript:
            thetext = field["text"]
            textonly+=thetext+" " 
    
    writefilename = OUTPUTDIR+'transcript_text_for_video' + str(videoid)+ '.json'
    mywritefile=open(writefilename,"a", encoding='utf-8')
    mywritefile.write(textonly)
    mywritefile.close()

    mywritefilename=OUTPUTDIR+'transcript_with_timing_for_'+str(videoid)+'.json'
    formatter=JSONFormatter()
    json_formatted= formatter.format_transcript(mytranscript)
    with open(mywritefilename, 'w',encoding='utf-8') as json_file:
        json_file.write(json_formatted)  

    return

def getmultipletranscriptsindividually(videoids):
                #get transcripts one by one 
##        mytranscript_list=[]
##        print("trialing getting transcript for b-at2RUpCH0 ")
##        mytranscript=YouTubeTranscriptApi.get_transcript("b-at2RUpCH0")
##        print(mytranscript)
##        mytranscript_list.append(mytranscript)

        alltranscripts=[]
        for videoid in videoids:
                try:
                        #print("about to get transcript for ", videoid)
                        tracefile.write("\nabout to get individual transcript for "+videoid)
                        mytranscript=YouTubeTranscriptApi.get_transcript(videoid)
                        
                        if (mytranscript is None):
                                #print("failed to get transcript for ",videoid)
                                tracefile.write("\nreturned null on first attempt to get individual transcript for"+videoid)
                        else:
                                alltranscripts.append(mytranscript)
                                saveTranscriptFiles(videoid, mytranscript)
                                
                except Exception as err:
                        #print("Exception {0}".format(err), " occurred with "+str(videoid))
                        tracefile.write("\nException {0}".format(err))
                        tracefile.write(" occurred with ")
                        tracefile.write(videoid)
                        #print("\nException occurred on first attempt to get transcript for ",videoid)
                        tracefile.write("\nFailed on first attempt to get transcript for "+videoid)
                        try:
                                # based on https://pypi.org/project/youtube-transcript-api/  trying a different method
                                # get a list of transcripts available
                                transcript_list=YouTubeTranscriptApi.list_transcripts(videoid)
                                # find the english language transcripts
                                if (transcript_list is not None):
                                        transcript = transcript_list.find_transcript(['en'])
##                                        print(
##                                                transcript.video_id,
##                                                transcript.language,
##                                                transcript.language_code,
##                                                # whether it has been manually created or generated by YouTube
##                                                transcript.is_generated,
##                                                # whether this transcript can be translated or not
##                                                transcript.is_translatable,
##                                                # a list of languages the transcript can be translated to
##                                                transcript.translation_languages,
##                                                )
                                        #fetch the transcript contents using fetch request
                                        ans = transcript.fetch()
                                        #save to a json file using the api formatter provided by youtube-transcript-api
                                        tracefile.write("\nfetched transcript for "+transcript.video_id+" on next attempt")
                                        if (ans is not None):
                                            saveTranscriptFiles(transcript.video_id, ans)
                                            alltranscripts.append(ans)
                                        
                                        continue
                                        
                                else:
                                        tracefile.write("\ntranscript list is empty, failed to get transcript information for video"+videoid)
                                        continue
                        except Exception as err:
                                try:
                                        #print("Exception {0}".format(err), " occurred with "+str(videoid))
                                        tracefile.write("\nException {0}".format(err)+ " occurred with "+str(videoid))
                                        mywritefilename='Transcripts/error_transcript_for_'+str(transcript.video_id)+'.json'
                                        mywriter=open(mywritefilename, 'w', encoding='utf-8')
                                        mywriter.write("\nException {0}".format(err)+ " occurred with "+str(videoid))
                                        continue
                                except:
                                        continue
                                   
        
        tracefile.write("\nhave retrieved and fetched each of the transcripts individually where possible")
        return alltranscripts

    
def getmultipletranscripts(videoids):

    #following 2 examaple lines shows how to get the transcript from one file
    #mytranscript = YouTubeTranscriptApi.get_transcript(videoid)
    #mytranscript = YouTubeTranscriptApi.get_transcript("PLuDTq4LBCsPTE2x2OgrBChRxxMKy213yG")
    #instead, use the api method get_transcripts  to get multiple transcripts

    # get the transcript from youtube for this videoids list
    tracefile.write("\nasking for transcripts for all videos in one request using youtube transcript api")
    for v in videoids:
        tracefile.write(v+" ")
    videoid=" "
    
    try:
        mytranscript_list=YouTubeTranscriptApi.get_transcripts(videoids,continue_after_error=True)
        #mytranscript_list[0] is the transcript data in a dictionary (.keys() lists all videos and .get(videoid) returns the data for a video
        #mytranscript_list[1] is the list of all videos that could not return a transcript
        alltranscripts=[]
        mysourcedtranscript = mytranscript_list[0]
        for thetranscriptvideo in mysourcedtranscript.keys():
            thetranscript=mysourcedtranscript.get(thetranscriptvideo)
            alltranscripts.append(thetranscript) 
            videoid=thetranscriptvideo
            tracefile.write("\nsuccessfully retreived transcript for "+videoid+" using bulk request")
            saveTranscriptFiles(videoid, thetranscript)  

##       
        # now see if can find missing transcripts using different approach - searching for each one by one using different API method
        for failure in mytranscript_list[1]:
                tracefile.write("\nUsing bulk request, failed to get transcript for"+ str(failure))
                
        #will try to get these transcripts using individual requests and fetch
        #note that this function will also save these transcripts to files as they are found
        moretranscripts = getmultipletranscriptsindividually(mytranscript_list[1])
        
        # add the newly found transcripts in moretranscripts list - found by searching individually to the alltranscripts list
        alltranscripts.extend(moretranscripts)
        
    except Exception as err:
        #print("Exception {0}".format(err), " occurred with "+str(videoid))
        tracefile.write("\nException {0}".format(err)+ " occurred with "+str(videoid))
        mywritefilename='Transcripts/error_transcript_for_'+str(videoid)+'getMultipleTranscripts.json'
        mywriter=open(mywritefilename, 'w', encoding='utf-8')
        mywriter.write("\nException {0}".format(err)+ " occurred with "+str(videoid))
                            
    return alltranscripts    
      
if __name__ == "__main__":
    import sys
    if len(sys.argv) == 2: #if there is only one argument provided assume that is the video id of a youtube video.
        youtube=getcredentials()
        vid = sys.argv[1]
        fail,title=getvideocaption(youtube, vid)  #this also gets meta information about the video
        allvideos=[]
        allvideos.append(vid)
        allthetranscripts2=getmultipletranscripts(allvideos)
        
    elif len(sys.argv) == 3:   # if there are two arguments provided, then assume these are filename and column name for a csv file with multiple video ids for youtube
        summaryfile=open("summary","w",encoding='utf-8')
        youtube=getcredentials()
        videofilename = sys.argv[1]
        colname = sys.argv[2]
        # read CSV file provided named in videofilename the 2rd argument expect a column name in the csv as named in 3rd argument
        csvread = open(videofilename, newline='\n')
        csvreader = read_csv(csvread)
        #create a list of youtube video ids from csvreader file in column with colname provided
        allvideos=csvreader[colname].tolist()
        #for each video first attempt to get video captions if they are available - not likely to return many transcripts directly this way
        for videoid in allvideos:
            fail = getvideocaption(youtube,videoid)
            if fail==0:
                summaryfile.write(videoid+" "+videoTitleDict[videoid]+"\n")
        #use the Youtubetranscript API to get transcripts for multiple videos
        summaryfile.close()
        
        allthetranscripts2=getmultipletranscripts(allvideos)
        
    else:
        print('Usage: py getcaptions.py [videoid]  or py getcaptions.py [video_csvfilename.csv] [videoid_colname]')
