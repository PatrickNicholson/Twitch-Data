import requests
import urllib
import sys
import json
import time
import datetime
import statistics
import argparse
from sqlalchemy import create_engine
import pandas as pd

'''
To Do:
    -change http response error handling (litl/backoff)
    -implement an error log file
'''

def getTotalOnTwitch(token):
    url = 'https://api.twitch.tv/kraken/games/top?&limit=1'
    data = getData(url, token)
    return data.pop('_total')

def compareTopAndTotalGames(token, total_games):
    total = getTotalOnTwitch(token)
    if(total_games > total):
        total_games = total
        return total
    else:
        return total_games

def getSleepTime(step, start_prog, end_prog):
    time = step.split(':')
    sec = (int(time[0])*3600) + (int(time[1])*60)
    runtime = ((int(end_prog.hour)*3600) - (int(start_prog.hour)*3600)) + ((int(end_prog.minute)*60) - (int(start_prog.minute)*60))
    return (sec - runtime)

def getData(url, client):
    try:
        headers = {'Accept' : 'application/vnd.twitchtv.v5+json', 'Client-ID' :client}
        resp = requests.get(url, headers=headers)
        if(resp.status_code != 200):
            print(resp.status_code)
            print(resp)
            print(resp.headers)
            sys.exit()
        json_array = resp.json()
        return json_array

    except requests.exceptions.RequestException as err:
        print(str(err))
        return getData(url, client)  

def getGames(off_set, limit, token):  
    url = 'https://api.twitch.tv/kraken/games/top?' + 'offset=' + str(off_set) +'&limit=' + str(limit)
    data = getData(url, token)
    stream_data = data.pop('top')
    for i in range(0, len(stream_data)):
        stream_data[i]['name'] = (stream_data[i].pop('game')).pop('name')
    return stream_data

def getChannels(name, off, channel_limit, client):
    name = urllib.parse.quote(name)
    url = 'https://api.twitch.tv/kraken/streams/?game=' + str(name) + '&limit=' + str(channel_limit) + '&offset=' + str(off)
    data = getData(url,client)
    streams = data.pop('streams')
    for i in range(0, len(streams)):
        streams[i] = streams[i].pop('viewers')
    return streams

def getStatistics(game_data, sample_size, token):
    num_streams = []
    for i in range(0, len(game_data)):
        channels = int(game_data[i].get('channels'))
        name = game_data[i]['name']
        samples = 0
        if(channels < sample_size):
            size = channels
        else:
            size = sample_size     
        while(size > 0):
            if(size < 100):
                limit = size
            else:
                limit = 100
            num_streams.extend(getChannels(name, samples, limit, token))
            samples += limit
            size -= limit
        if(not num_streams):
            avrg = -1
            stdv = -1
        elif(len(num_streams) == 1):
            avrg = num_streams[0]
            stdv = 0
        else:
            avrg = statistics.mean(num_streams) 
            stdv = statistics.stdev(num_streams)
        if(samples < 0):
            samples = 0
        game_data[i]['total_avrg'] = int(game_data[i].get('viewers') / game_data[i].get('channels'))
        game_data[i]['sample_size'] = int(samples)
        game_data[i]['stdev_norm'] = int(stdv / samples)
        game_data[i]['stdev'] = int(stdv)
        game_data[i]['local_avrg'] = int(avrg)
        game_data[i]['time'] = time.time()
        num_streams = []
    return game_data

def getTopGames(total_games, token):
    off_set = 0
    difference = 0
    game_data = []
    while(total_games > 0):
        if(difference > 0): #there's a bug where the twitch APIv5 returns 99 games in the first loop, this gets game #100
            limit = difference
            game_data.extend(getGames(off_set, limit, token))
            limit = 0
            difference = 0
        else:
            if(total_games < 100):
                limit = total_games
            else:
                limit = 100
            game_data.extend(getGames(off_set, limit, token))
            difference = (off_set + limit) - len(game_data)
        total_games -= limit
        off_set += limit        
    return game_data

def main(total_games, token, sample_size, tbl_name, eng):
    print('starting')
    game_data = getTopGames(total_games, token)
    print('working...')
    game_data = getStatistics(game_data, sample_size, token)
    game_frame = pd.DataFrame(game_data)
    print('saving...')
    game_frame.to_sql(tbl_name, eng, if_exists='append')
    print('Saved ' + str(len(game_data)) + ' games.')

if(__name__ == '__main__'):
    CLIENT_TOKEN = 'TOKEN' #change this into an environment variable
    PASS_TOKEN = 'TOKEN'
    USER_TOKEN = 'TOKEN'
    TABLE_TOKEN = 'TOKEN'
    IP_TOKEN = 'TOKEN'
    PORT_TOKEN = 'TOKEN'


    engine = create_engine('postgresql://' + USER_TOKEN + ':' + PASS_TOKEN + '@' + IP_TOKEN + ':' + PORT_TOKEN + '/' + TABLE_TOKEN)

    TOTAL_GAMES = 3000
    SAMPLE_SIZE = 20000
    STEP = '3:00' #3 hours
    
    count = 0
    while(True):
        total_games = compareTopAndTotalGames(CLIENT_TOKEN, TOTAL_GAMES)
        count += 1
        start = datetime.datetime.now()
        main(total_games, CLIENT_TOKEN, SAMPLE_SIZE, TABLE_TOKEN, engine)
        stop = datetime.datetime.now()
        print(start)
        print('Sleeping.. zzz...zzz...')
        time.sleep(getSleepTime(STEP,start,stop))
