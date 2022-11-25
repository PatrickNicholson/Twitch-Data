import requests
import urllib
import json
import time
import datetime
import backoff
import pandas as pd

#having trouble using the new API. My bucket and id keep getting rejected. I have no idea how to wrap the header correctly, it makes no sense
@backoff.on_exception(backoff.expo,requests.exceptions.RequestException,max_time=1000)
def getData(url, client):
    headers = {'Client-ID': client}
    resp = requests.get(url, headers=headers)
    if(resp.status_code != 200):
        print(resp.status_code)
        print(resp)
        print(resp.headers)
    json_array = resp.json()
    return json_array

def getInfo(name, client):
    name = urllib.parse.quote(name)
    url = 'https://api.twitch.tv/helix/users?login=' + str(name)
    data = getData(url,client).pop('data')
    data.append(data[0].pop('id'))
    del data[0]
    url2 = 'https://api.twitch.tv/helix/users/follows?first=1&to_id=' + str(data[0])
    data.append(getData(url2,client).pop('total'))
    url3 = 'https://api.twitch.tv/helix/users/follows?first=1&from_id=' + str(data[0])
    print(data)
    data.append(getData(url3,client).pop('total'))
    return data

def getFollowers(ID,page,limit,client):
    name = urllib.parse.quote(ID)
    if (page != ''):
        url = 'https://api.twitch.tv/helix/users/follows?first=' + str(limit) + '&to_id=' + str(name) + '&after=' + str(page)
    else:
        url = 'https://api.twitch.tv/helix/users/follows?first=' + str(limit) + '&to_id=' + str(name)
    data = getData(url,client)
    return data

def getFollows(ID,page,limit,client):
    name = urllib.parse.quote(ID)
    if (page != ''):
        url = 'https://api.twitch.tv/helix/users/follows?first=' + str(limit) + '&from_id=' + str(name) + '&after=' + str(page)
    else:
        url = 'https://api.twitch.tv/helix/users/follows?first=' + str(limit) + '&from_id=' + str(name)
    data = getData(url,client)
    return data

def parseFollowers(name,client):
    streamer_data = getInfo(name, client)
    ID = streamer_data[0]
    total_followers = streamer_data[1]
    page = ''
    followers = []
    while(total_followers > 0):
        if(total_followers < 100):
            limit = total_followers
        else:
            limit = 100
        
        json = getFollowers(ID,page,limit,client)

        total_followers -= limit
        page = json.pop('pagination').pop('cursor')
        data = json.pop('data')
        for i in range(0,limit):
            followers.append(data[i].pop('from_name'))
    
    return followers

def parseFollows(followers,client):
    for i in range(0, len(followers)):
        print(i)
        streamer_data = getInfo(followers[i], client)
        ID = streamer_data[0]
        total_follows = streamer_data[2]

        page = ''
        follows = []
        while(total_follows > 0):
            if(total_follows < 100):
                limit = total_follows
            else:
                limit = 100
        
            json = getFollows(ID,page,limit,client)

            total_follows -= limit
            
            page = json.pop('pagination').pop('cursor')
            data = json.pop('data')
            for i in range(0,limit):
                follows.append(data[i].pop('to_name'))
    return follows

if(__name__ == '__main__'):
    CLIENT = '' 
    NAME = ''
    followers = parseFollowers(NAME,CLIENT)
    print(followers)
    print(parseFollows(followers,CLIENT))
