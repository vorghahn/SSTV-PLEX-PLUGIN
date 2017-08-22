#
# Forked from sstvProxy:
#
#sstvProxy Development Lead
#````````````````
#- bjzy <bjzybjzy@gmail.com>
#
#tvhProxy Developer (majority of code, thanks!)
#````````````````
#- Joel Kaaberg <joel.kaberg@gmail.com>
#
#Patches and Suggestions
#```````````````````````
#
#- Nikhil Choudhary

from gevent import monkey; monkey.patch_all()

import subprocess
import sys
import os
import datetime
import time
from gevent.pywsgi import WSGIServer
from flask import Flask, Response, request, jsonify, abort

app = Flask(__name__)

cdict = {}
config = {
    'bindAddr': os.environ.get('SSTV_BINDADDR') or '',
    'sstvProxyURL': os.environ.get('SSTV_PROXY_URL') or 'http://192.168.1.23',
    'tunerCount': os.environ.get('SSTV_TUNER_COUNT') or 6,  # number of tuners to use for sstv
}


@app.route('/discover.json')
def discover():
    return jsonify({
        'FriendlyName': 'sstvProxy',
        'ModelNumber': 'HDTC-2US',
        'FirmwareName': 'hdhomeruntc_atsc',
        'TunerCount': int(config['tunerCount']),
        'FirmwareVersion': '20150826',
        'DeviceID': '12345678',
        'DeviceAuth': 'test1234',
        'BaseURL': '%s' % config['sstvProxyURL'],
        'LineupURL': '%s/lineup.json' % config['sstvProxyURL']
    })


@app.route('/lineup_status.json')
def status():
    return jsonify({
        'ScanInProgress': 0,
        'ScanPossible': 1,
        'Source': "Cable",
        'SourceList': ['Cable']
    })


@app.route('/lineup.json')
def lineup():
    #check if m3u8 is less than a day old
    if time.localtime() > (os.path.getmtime("SmoothStreamsTV-xml.m3u8") + 86400):
        print ("updating m3u8")
        #Python 3
        # scheduleResult = SmoothPlaylist.main()

        #Python 2 compatible
        child = subprocess.Popen("python SmoothPlaylist.py", shell=True, stderr=subprocess.PIPE)
        while True:
            out = child.stderr.read(1)
            if out == '' and child.poll() != None:
                break
            if out != '':
                sys.stdout.write(out)
                sys.stdout.flush()
    print (time.localtime(), (os.path.getmtime("SmoothStreamsTV-xml.m3u8")))
    file = open("SmoothStreamsTV-xml.m3u8", 'r')
    file.readline()
    lineup = []
    
    for channelNum in range(1,151):
        cdict[channelNum] = {}
        #example m3u8 line
        #Line 1 #EXTINF:-1 tvg-id="tv.9" tvg-logo="http://www.freeviewnz.tv/nonumbracoimages/ChannelsOpg/TVNZ11280x1280.png",TVNZ 1
        #Line 2 https://tvnzioslive04-i.akamaihd.net/hls/live/267188/1924997895001/channel1/master.m3u8|X-Forwarded-For=219.88.222.91
        
        # #EXTINF:-1 tvg-id="133" tvg-logo="https:https://guide.smoothstreams.tv/assets/images/channels/110.png" tvg-name="BT Sport 3 HD" tvg-num="110",BT Sport 3 HD
        # pipe://#PATH# 110
        header = file.readline()
        if header:
            cdict[channelNum]['url'] = file.readline()
            header = header.split(",")
            metadata = header[0]
            metadata = metadata.split(" ")
            cdict[channelNum]['channelName'] = header[1]
            for item in metadata:
                if item == "#EXTINF:-1":
                    metadata.remove("#EXTINF:-1")
                elif "tvg-id" in item:
                    cdict[channelNum]['channelId'] = item[8:-1]
                elif "tvg-logo" in item:
                    cdict[channelNum]['channelLogo'] = item[10:-1]
                elif "tvg-name" in item:
                    cdict[channelNum]['channelName'] = item[10:-1]
                elif "tvg-num" in item:
                    cdict[channelNum]['channelNum'] = item[9:-1]
                elif "epg-id" in item:
                    cdict[channelNum]['channelEPGID'] = item[8:-1]
                elif "url-epg" in item:
                    cdict[channelNum]['channelEPG'] = item[9:-1]
            print (cdict[channelNum]['channelName'])
            print (cdict[channelNum]['url'])
            lineup.append({'GuideNumber': channelNum,
                               'GuideName': str(channelNum) + " " + cdict[channelNum]['channelName'],
                               'URL': '%s/auto/v%s' % (config['sstvProxyURL'], str(channelNum))
                               })

        # print ({'GuideNumber': channelNum,
        #                    'GuideName': str(channelNum) + channelName,
        #                    'URL': url
        #                    })
    file.close()
    return jsonify(lineup)

@app.route('/auto/v<channelNum>')
def channelProxy(channelNum):
    auth()
    url = "http://%s.SmoothStreams.tv:9100/%s/ch%sq1.stream/playlist.m3u8?wmsAuthSign=%s==" % ('dsg', 'viewstvn', str(channelNum), str(cdict['hash']))
    pipeUrl = 'ffmpeg -i $s -codec copy -loglevel error -f mpegts pipe:1' % str(url)
    return pipeUrl

def auth():
    LOGIN_TIMEOUT_MINUTES = 60
    postdata = {"username": 'uname', "password": 'pword', "site": 'viewstvn'}
    result = JSON.ObjectFromURL('http://auth.smoothstreams.tv/hash_api.php', values = postdata, encoding = 'utf-8', cacheTime = LOGIN_TIMEOUT_MINUTES * 100)
    cdict["code"] = result["code"]
    cdict["hash"] = result["hash"]
    cdict["validUntil"] = datetime.datetime.now() + datetime.timedelta(minutes = LOGIN_TIMEOUT_MINUTES)

@app.route('/lineup.post')
def lineup_post():
    return ''


if __name__ == '__main__':
    http = WSGIServer((config['bindAddr'], 5004), app.wsgi_app)
    http.serve_forever()

# lineup()

