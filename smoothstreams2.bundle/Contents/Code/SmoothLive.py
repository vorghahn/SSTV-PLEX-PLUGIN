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
# import dateutil.parser
# import datetime
# import urllib2
# import SmoothUtils
# import SmoothAuth
# import traceback
# import operator
# import bisect
# import time
# import calendar
# import shlex
# import requests
from gevent.pywsgi import WSGIServer
from flask import Flask, Response, request, jsonify, abort
# import SmoothUtils
# import SmoothAuth
# import SmoothPlaylist #requires python 3

app = Flask(__name__)


# config = {
#     'bindAddr': os.environ.get('SSTV_BINDADDR') or '',
#     'sstvProxyURL': os.environ.get('SSTV_PROXY_URL') or 'http://localhost',
#     'tunerCount': os.environ.get('SSTV_TUNER_COUNT') or 6,  # number of tuners to use for sstv
# }
#
#
# @app.route('/discover.json')
# def discover():
#     return jsonify({
#         'FriendlyName': 'sstvProxy',
#         'ModelNumber': 'HDTC-2US',
#         'FirmwareName': 'hdhomeruntc_atsc',
#         'TunerCount': int(config['tunerCount']),
#         'FirmwareVersion': '20150826',
#         'DeviceID': '12345678',
#         'DeviceAuth': 'test1234',
#         'BaseURL': '%s' % config['sstvProxyURL'],
#         'LineupURL': '%s/lineup.json' % config['sstvProxyURL']
#     })
#
#
# @app.route('/lineup_status.json')
# def status():
#     return jsonify({
#         'ScanInProgress': 0,
#         'ScanPossible': 1,
#         'Source': "Cable",
#         'SourceList': ['Cable']
#     })


@app.route('/lineup.json')
def lineup():
    #check if m3u8 is less than a day old
    if os.path.localtime() > (os.path.getmtime("SmoothStreamsTV-xml.m3u8") + 86400):
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
    file = open("SmoothStreamsTV-xml.m3u8", 'r')
    file.readline()
    lineup = []
    
    for channelNum in range(1,151):
        #example m3u8 line
        #Line 1 #EXTINF:-1 tvg-id="tv.9" tvg-logo="http://www.freeviewnz.tv/nonumbracoimages/ChannelsOpg/TVNZ11280x1280.png",TVNZ 1
        #Line 2 https://tvnzioslive04-i.akamaihd.net/hls/live/267188/1924997895001/channel1/master.m3u8|X-Forwarded-For=219.88.222.91
        
        # #EXTINF:-1 tvg-id="133" tvg-logo="https:https://guide.smoothstreams.tv/assets/images/channels/110.png" tvg-name="BT Sport 3 HD" tvg-num="110",BT Sport 3 HD
        # pipe://#PATH# 110
        header = file.readline()
        url = file.readline()
        header = header.split(",")
        metadata = header[0]
        metadata = metadata.split(" ")
        channelName = header[1]
        for item in metadata:
            if item == "#EXTINF:-1":
                metadata.remove("#EXTINF:-1")
            elif "tvg-id" in item:
                channelId = item[8:-1]
            elif "tvg-logo" in item:
                channelLogo = item[10:-1]
            elif "tvg-name" in item:
                channelName = item[10:-1]
            elif "tvg-num" in item:
                channelNum = item[9:-1]
        print (channelName)
        print (url)
        #random web pipe
        #ffmpeg -i url -vcodec rawvideo -pix_fmt yuv420p -f rawvideo - | x264 --crf 18 -o test.mp4 --fps 25.0 - 640x352
        #jobriens ffmpeg pipe
        pipeUrl = "ffmpeg -i url -codec copy -loglevel info -bsf:v h264_mp4toannexb -f mpegts -tune zerolatency pipe:1"
        lineup.append({'GuideNumber': channelNum,
                           'GuideName': str(channelNum) + " " + channelName,
                           'URL': pipeUrl
                           })
        # print ({'GuideNumber': channelNum,
        #                    'GuideName': str(channelNum) + channelName,
        #                    'URL': url
        #                    })

    #lineup.append({'GuideNumber': "1",
    #                       'GuideName': "ESPNEWS",
    #                       'URL':"http://dnaw1.smoothstreams.tv:9100/viewms/ch01q1.stream/playlist.m3u8?wmsAuthSign=c2VydmVyX3RpbWU9OC8yMC8yMDE3IDc6NDU6MDIgUE0maGFzaF92YWx1ZT1FanNiNVFmeEFNb211cVN6Zkl3c3JBPT0mdmFsaWRtaW51dGVzZpZD12aWV3bXMtMTUzNTk==="
    #                       })

    # return jsonify(lineup)


# @app.route('/lineup.post')
# def lineup_post():
#     return ''
#
#
# if __name__ == '__main__':
#     http = WSGIServer((config['bindAddr'], 5004), app.wsgi_app)
#     http.serve_forever()

lineup()

