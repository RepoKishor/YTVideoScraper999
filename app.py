from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
from googleapiclient.discovery import build
import mysql.connector as connection
import pandas as pd
import pytube
from pytube import YouTube
import csv

app = Flask(__name__)

@app.route('/',methods=['GET'])  # route to display the home page
@cross_origin()
def homePage():
    return render_template("index.html")

@app.route('/ytdetails',methods=['POST','GET']) # route to show the review comments in a web UI
@cross_origin()
def index():
    #if request.method == 'POST':
        try:
            api_key ='AIzaSyCBlB5WuqPX2Q4KKrZF-vWZ-xH0KfYsw_4'
            channel_id = 'UCjWY5hREA6FFYrthD0rZNIw'
            youtube = build('youtube', 'v3', developerKey=api_key)
            request = youtube.channels().list(
                part='snippet, contentDetails, statistics', id=channel_id)
            response = request.execute()
            data = dict(Channel_name=response['items'][0]['snippet']['title'],
                        subscribers=response['items'][0]['statistics']['subscriberCount'],
                        viewCount=response['items'][0]['statistics']['viewCount'],
                        videoCount=response['items'][0]['statistics']['videoCount'],
                        playlist_id=response['items'][0]['contentDetails']['relatedPlaylists']['uploads'])

            playlist_id = data['playlist_id']

            # fetching the 50 video ids from the channel
            request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50)
            response = request.execute()
            video_ids = []
            for i in range(len(response['items'])):
                video_ids.append(response['items'][i]['contentDetails']['videoId'])
            print("video_ids", len(video_ids))
            # fetching all the video details of the above 50 videos
            all_video_stats = []
            request = youtube.videos().list(
                part="snippet,contentDetails,statistics",
                id=','.join(video_ids))
            response = request.execute()
            for video in response['items']:
                video_stats = dict(title=video['snippet']['title'],
                                   publishedDate=video['snippet']['publishedAt'],
                                   thumbnail=video['snippet']['thumbnails']['default']['url'],
                                   views=video['statistics']['viewCount'],
                                   likes=video['statistics']['likeCount'],
                                   comments=video['statistics']['commentCount'], )
            
                all_video_stats.append(video_stats)
            # creating a csv file of all the details
            video_data = pd.DataFrame(all_video_stats)
            video_data.to_csv("ytdetails.csv")
            # Saving to the MySQL database
            dbAction(all_video_stats)
            # Download the videos
            #videoDownload(video_ids)
            #reviews = []
            #reviews.append(mydict)
            return render_template('results.html', videoDetails=all_video_stats[0:(len(all_video_stats)-1)])
        except Exception as e:
            print('The Exception message is: ',e)
            return 'something is wrong'

def dbAction(all_video_stats):
    try:
        mydb = connection.connect(host="localhost", user="root", passwd="mysql", use_pure=True)
        cursor = mydb.cursor()
        cursor.execute("create database if not exists youtubeTask")
        cursor.execute("create table if not exists youtubeTask.ytdetails (title varchar(100), publishedDate varchar(25), thumbnail varchar(60), views varchar(20), likes varchar(20), comments varchar(20))")
        for i in range(len(all_video_stats)):
            myDict = all_video_stats[i]
            placeholders = ', '.join(['%s'] * len(myDict))
            columns = ', '.join(myDict.keys())
            sql = "INSERT INTO youtubeTask.ytdetails ( %s ) VALUES ( %s )" % (columns, placeholders)
            cursor.execute(sql, list(myDict.values()))
        mydb.commit()
        print("All the yt video details are inserted....")
        mydb.close()
    except Exception as e:
        mydb.close()
        print(str(e))

@app.route('/ytvideodownload',methods=['POST','GET'])
@cross_origin()
def videoDownload():
    try:
        print("METHOD CALLED TO DOWNLOAD VIDEOS..............")
        api_key = 'AIzaSyCBlB5WuqPX2Q4KKrZF-vWZ-xH0KfYsw_4'
        channel_id = 'UCjWY5hREA6FFYrthD0rZNIw'
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.channels().list(
            part='snippet, contentDetails, statistics', id=channel_id)
        response = request.execute()
        data = dict(Channel_name=response['items'][0]['snippet']['title'],
                    subscribers=response['items'][0]['statistics']['subscriberCount'],
                    viewCount=response['items'][0]['statistics']['viewCount'],
                    videoCount=response['items'][0]['statistics']['videoCount'],
                    playlist_id=response['items'][0]['contentDetails']['relatedPlaylists']['uploads'])

        playlist_id = data['playlist_id']
        request = youtube.playlistItems().list(
                part='contentDetails',
                playlistId=playlist_id,
                maxResults=50)
        response = request.execute()
        video_ids = []
        for i in range(len(response['items'])):
            video_ids.append(response['items'][i]['contentDetails']['videoId'])

        yt = "https://www.youtube.com/watch?v="
        downloadpath = 'E:/Personal/iNeuron/YTVideos/'
        for i in range(0, 50):
            youtube = pytube.YouTube(yt + video_ids[i])
            video = youtube.streams.first()
            video.download(downloadpath)
        return render_template('resultsdownload.html')
    except Exception as e:
        print('The Exception message is: ', e)
        return 'something is wrong'

if __name__ == "__main__":
    #app.run(host='127.0.0.1', port=8001, debug=True)
	app.run(debug=True)
