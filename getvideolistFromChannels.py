#this file has bugs in it
# modify these values
delimiter = ','													# delimiter, e.g. ',' for CSV or '\t' for TAB
##waittime = 10														# seconds browser waits before giving up
##sleeptime = [5,15]													# random seconds range before loading next video id
headless = True
outfile="traceoutput_file180822"
logfiletrace="logfiletrace180822"
tracefile=open(logfiletrace,"w")

from youtube_transcript_api import YouTubeTranscriptApi  			# this line added kkeogh 10 08 2021
import google_auth_oauthlib.flow									# this line added kkeogh 06 09 2021
import googleapiclient.discovery									# this line added kkeogh 06 09 2021
import googleapiclient.errors										# this line added kkeogh 06 09 2021
import json
from pandas import *
import sys

from time import sleep
import csv
import random
import os.path

videodict = dict()

#based on https://www.googleapis.com/youtube/v3/channelSections
#https://developers.google.com/youtube/v3/docs/channelSections/list?apix=true&apix_params=%7B%22part%22%3A%5B%22snippet%2CcontentDetails%22%5D%2C%22channelId%22%3A%22UC_x5XG1OV2P6uZZ5FSM9Ttw%22%7D 
# Get credentials and create an API client
#following code snippet taken from help in developers.google.com/youtube/v3/docs/channels/list

def getCredentials():
	scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
  # Disable OAuthlib's HTTPS verification when running locally.
    # *DO NOT* leave this option enabled in production.
	
	os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

	api_service_name = "youtube"
	api_version = "v3"
	client_secrets_file = "clientsecretfiledesktop.json"
   # Get credentials and create an API client
	flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, scopes)
	credentials = flow.run_console()
	youtube=googleapiclient.discovery.build(api_service_name, api_version, credentials=credentials)
	return youtube

#for a given youtube video channel, get the playlist and videos associated with that channel 
def getChannelList(mychannelId,youtube):
        #scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        #next code added by Kathleen based on https://www.googleapis.com/youtube/v3/channelSections to list of videos for a channel
        try:
                request = youtube.channels().list(part="snippet,contentDetails,statistics",id=mychannelId)
                channeldetails = request.execute()
                
                request2 = youtube.playlists().list(part="id",channelId=mychannelId,maxResults=1000)
                playlist=request2.execute()
                
        except RuntimeError as err:
                print("Exception {0}".format(err), " occurred with channel ", mychannelId)
                channeldetails=[]
                newlist=[]
        else:
                playlistdict=json.loads(json.dumps(playlist))
                newlist=[]
                newplaylist=[]
                summaryfile=open("SummaryOfVideoDetails.txt","w",encoding="utf-8")
             
                for itemslist in playlistdict.get('items'):
                        returnedid=itemslist.get('id')  #get playlist id
                        newplaylist.append(returnedid)
                        print("playlist id is :")
                        print(returnedid)
                        # this returnedid is a playlist id not a video id, now request list of vidoes for this playlist
                        #request = youtube.playlistItems().list(
                        request3 = youtube.playlistItems().list(part="snippet,contentDetails",maxResults=1000,playlistId=returnedid)
                        listresponse = request3.execute()
                        videolistdict=json.loads(json.dumps(listresponse))
                        print("playlist video items returned ")
                        print(videolistdict)
                        theTitle=' '
                        for listItemPart in videolistdict.get("items"):
                                print("stepping into title ")
                                snippet=listItemPart.get("snippet")
                                theTitle=snippet.get("title")
                                print("Title ")
                                print(theTitle)
                                channelTitle= listItemPart.get("channelTitle")
                                content=listItemPart.get("contentDetails")
                                onevideoid=content.get("videoId")
                                newlist.append(onevideoid)
                                print("content ", content)
                                print("videoid ", onevideoid)
                                summaryfile.write(onevideoid)
                                summaryfile.write(" ")
                                summaryfile.write(theTitle)
                                summaryfile.write("\n")
                        #print(listresponse)
                                videodict[onevideoid]=theTitle
                        print("end of playlist video details returned ")
                        
                #save channel details to file
                cwritefilename="ChannelsDetails/channel_id_"+mychannelId+".json"
                channelfile = open(cwritefilename,"w")
                channelfile.write(json.dumps(channeldetails))
                channelfile.write(json.dumps(playlist))
                channelfile.close()
                
                #save extracted video ids in newlist to a csv file
                cwritefilename="ChannelsDetails/channel_id_videos"+mychannelId+".csv"
                channelfile = open(cwritefilename,"w",newline='')
                for videoid in newlist:
                        channelfile.write(videoid, videodict[videoid])
                        channelfile.write('\n')
                #csvwriter = csv.writer(channelfile)
                #csvwriter.writerows(newlist)
                channelfile.close()
                
                # save the playlists to a separate file
                cwritefilename="PlaylistsDetails/channel_id_playlists"+mychannelId+".csv"
                channelfile = open(cwritefilename,"w",newline='')
                for aplaylistid in newplaylist:
                        channelfile.write(aplaylistid)
                        channelfile.write('\n')
                channelfile.close()

                #print("newlist")
                #print(newlist)
                        
                return(channeldetails,newlist)


# main program code is below 	
if __name__ == "__main__":
        # prepare log file
        logwrite = open('transcriptlogfile','w',newline='\n')
        logwriter = csv.DictWriter(logwrite, fieldnames=['id','msg'])
        logwriter.writeheader()

        #authenticate with youtube using google credentials - will prompt for verification
        myyoutube=getCredentials()

        #after credentials have been sought, from now on, redirect output to a txt file out.txt
        orig_stdout = sys.stdout
        f = open('out.txt', 'w',encoding="utf-8")
        sys.stdout = f

        # read csv file of channels to explore
        #channelsfile = open('channelList.csv','r', newline='\n')
        channelsfile = open('ChannelsDetails/channelListEXTENDED.csv','r', newline='\n')
        channelreader = csv.DictReader(channelsfile)
        channelcount = len(open('ChannelsDetails/channelListEXTENDED.csv').readlines())


        #print("test channel UCbqmj1hzxuAXsjk08k-KP6w")
        #aChannel = "UCbqmj1hzxuAXsjk08k-KP6w"
        #print("about to get channel list for test channel")
        # for channel - aChannel get list of videos in that channel

        allids=["videoIds"]
        allchannels=[{"channels"}]

        #for each youtube video channel, get the playlist and videos associated with that channel 
        for row in channelreader:
                print("opening channel", row['channel'], row['url'])
                ans,ids=getChannelList(row['channel'],myyoutube)
                print("channel list for ", row['channel'], "follows: ")
                print(ans)
                allchannels.append(ans)
                print("videolist for ", row['channel'], "follows: " )
                print(ids)
                for itemid in ids:
                        allids.append(itemid)
                #allids contains all the videos found for that channel's playlist
                

        #now store all found channel playlists to a file named channelListDetailsAllExtended
        idfile = open('ChannelsDetails/channelListsDetailsExtended','a',newline='\n')
        #idfilewriter = csv.DictWriter(idfile, ans)
        for eachChannel in allchannels:
                #addict = json.loads(json.dumps(eachChannel))
                for value in list(eachChannel):
                        idfile.write(str(value))
                #idfile.write(list(eachChannel))
                idfile.write('\n')
        idfile.close()

        #write videos in list ids to a csv file with column name 'videoIds'
        videofile = open('AllChannelsSourcedVideoListsExtended.csv','w',newline='')
        #videofilewriter=csv.writer(videofile,dialect='excel')
        #videofilewriter.writerow("videoIds")
        #videofilewriter.writerows(allids)

        for avideo in allids:
                videofile.write(avideo)
                videofile.write(" ")
                videofile.write(videodict[avideo])
                videofile.write('\n')
        videofile.close()
        #print(allids)

        #clean up - redirect system output back to screen
        sys.stdout = orig_stdout
        f.close()
        print("done")


