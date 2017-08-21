#Forked from sstvProxy:
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

import time
import os
import requests
from gevent.pywsgi import WSGIServer
from flask import Flask, Response, request, jsonify, abort

app = Flask(__name__)

config = {
    'bindAddr': os.environ.get('SSTV_BINDADDR') or '',
    'sstvProxyURL': os.environ.get('SSTV_PROXY_URL') or 'http://localhost',
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
    lineup = []

    lineup.append({'GuideNumber': "1",
                           'GuideName': "ESPNEWS",
                           'URL':"http://dnaw1.smoothstreams.tv:9100/viewms/ch01q1.stream/playlist.m3u8?wmsAuthSign=c2VydmVyX3RpbWU9OC8yMC8yMDE3IDc6NDU6MDIgUE0maGFzaF92YWx1ZT1FanNiNVFmeEFNb211cVN6Zkl3c3JBPT0mdmFsaWRtaW51dGVzZpZD12aWV3bXMtMTUzNTk==="
                           })

    return jsonify(lineup)


@app.route('/lineup.post')
def lineup_post():
    return ''


if __name__ == '__main__':
    http = WSGIServer((config['bindAddr'], 5004), app.wsgi_app)
    http.serve_forever()
