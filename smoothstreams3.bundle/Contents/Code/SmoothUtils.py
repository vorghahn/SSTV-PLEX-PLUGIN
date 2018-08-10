# -*- coding: utf-8 -*-
###################################################################################################
#
#	Smoothstreams plugin for Plex
#	Copyright (C) 2016 Smoothstreams
#
###################################################################################################
import datetime
import re
import htmlentitydefs
import gzip
import urllib2
import io
import time
import requests
import xml.etree.ElementTree
from m3u_parser import LoadPlaylist
import xmltv_parser
from locale_patch import L, SetAvailableLanguages
from threading import Thread

THUMB_URL = 'https://guide.smoothstreams.tv/assets/images/channels/150.png'
GUIDE_CACHE_MINUTES = 10

sports_list = ["martial sports",'nba','sports','motorsport','americanfootball',"nfl","national football league",'ice hockey',"nhl","national hockey league",'nascar',"hockey","college football","cfb","ncaaf","rugby","fifa","uefa","epl","soccer","premier league","bundesliga","football","nba","wnba","mlb","baseball","pga",'golf',"ufc",'fight',"boxing","mma","wwe","wrestling","curling","darts","snooker","tennis/squash","cricket","basketball"]

def SportsList():
	return  sports_list

def fix_text(text):
	def fixup(m):
		text = m.group(0)
		if text[:2] == "&#":
			# character reference
			try:
				if text[:3] == "&#x":
					return unichr(int(text[3:-1], 16))
				else:
					return unichr(int(text[2:-1]))
			except ValueError:
				pass
		else:
			# named entity
			try:
				text = unichr(htmlentitydefs.name2codepoint[text[1:-1]])
			except KeyError:
				pass
		return text # leave as is
	return re.sub("&#?\w+;", fixup, text)

def GetServerUrlByName(serverLocation=None):
	if Prefs["customServer"] is not None and len(Prefs['customServer']) > 0 and ":" in Prefs['customServer'] > 0:
		Dict['server'] = Prefs['customServer'].split(":")[0]
	elif serverLocation == 'EU Random':
		Dict['server'] = "deu.SmoothStreams.tv"
	elif serverLocation == 'EU DE-Frankfurt':
		Dict['server'] = "deu-de.SmoothStreams.tv"
	elif serverLocation == 'EU NL-3':
		Dict['server'] = "deu-nl3.SmoothStreams.tv"
	elif serverLocation == 'EU NL-2':
		Dict['server'] = "deu-nl2.SmoothStreams.tv"
	elif serverLocation == 'EU NL-1':
		Dict['server'] = "deu-nl1.SmoothStreams.tv"
	elif serverLocation == 'EU NL':
		Dict['server'] = "deu-nl.SmoothStreams.tv"
	elif serverLocation == 'EU UK-Random':
		Dict['server'] = "deu-uk.SmoothStreams.tv"
	elif serverLocation == 'EU UK-London1':
		Dict['server'] = "deu-uk1.SmoothStreams.tv"
	elif serverLocation == 'EU UK-London2':
		Dict['server'] = "deu-uk2.SmoothStreams.tv"
	elif serverLocation == 'US All':
		Dict['server'] = "dna.SmoothStreams.tv"
	elif serverLocation == 'US East':
		Dict['server'] = "dnae.SmoothStreams.tv"
	elif serverLocation == 'US West':
		Dict['server'] = "dnaw.SmoothStreams.tv"
	elif serverLocation == 'US West-PHX':
		Dict['server'] = "dnaw1.SmoothStreams.tv"
	elif serverLocation == 'US West-LA':
		Dict['server'] = "dnaw2.SmoothStreams.tv"
	elif serverLocation == 'US West-SJ':
		Dict['server'] = "dnaw3.SmoothStreams.tv"
	elif serverLocation == 'US Chi':
		Dict['server'] = "dnaw4.SmoothStreams.tv"
	elif serverLocation == 'US East-NJ':
		Dict['server'] = "dnae1.SmoothStreams.tv"
	elif serverLocation == 'US East-VA':
		Dict['server'] = "dnae2.SmoothStreams.tv"
	elif serverLocation == 'US East-CAN':
		Dict['server'] = "dnae3.SmoothStreams.tv"
	elif serverLocation == 'US East-CAN2':
		Dict['server'] = "dnae4.SmoothStreams.tv"
	elif serverLocation == 'US East-NY':
		Dict['server'] = "dnae6.SmoothStreams.tv"
	elif serverLocation == 'Asia':
		Dict['server'] = "dap.SmoothStreams.tv"
	elif serverLocation == 'Asia Old':
		Dict['server'] = "dsg.SmoothStreams.tv"
	else:
		Log.Error('Invalid serverName passed to GetServerUrlByName ' + serverLocation)
		Dict['server'] = None
	Dict.Save()

def GetServicePort(serviceName=None):
	#Currently redundent
	# Gets the port for HTML5 streaming
	if serviceName is None:
		Log.Error('No serviceName specified')
		port = "80" # this will at least let ss server op log it if debugging on that end
	elif serviceName == 'StreamTVNow':
		port = "443" #"9100"
	elif serviceName == 'StarStreams':
		port = "443" #"9100"
	elif serviceName == 'Live247':
		port = "443" #"9100" #deu.smoothstreams.tv:12935
	elif serviceName == 'MyStreams':
		port = "443" #"9100"
	elif serviceName == "MMA-TV/MyShout":
		port = "443" #"9100"
	elif serviceName == "MMA SR+":
		port = "443" #"9100"
	else:
		Log.Error('Invalid service name supplied to GetServicePort')
	return port

# def GetScheduleJson(OnlyGetNowPlaying=False, IgnorePast=False):
# 	if "guideValidUntil" in Dict and Dict['guideValidUntil'] > datetime.datetime.now():
# 		Log.Info('Guide load not needed')
# 		return
#
# 	Log.Info('Starting GetScheduleJson')
#
# 	currentTime = getCurrentTimeNative()
#
# 	if IsDST():
# 		Dict['ScheduleUtcOffset'] = -4
# 	else:
# 		Dict['ScheduleUtcOffset'] = -5
#
# 	parser = dateutil.parser()
#
# 	if Prefs['secureEPG']:
# 		secureEPG = 'https'
# 	else:
# 		secureEPG = 'http'
# 	Log.Info('HTTP type is ' + secureEPG)
#
# 	if Prefs['sportsOnly']:
# 		Log.Info('Sports only')
# 		scheduleFeedURL = secureEPG + '://iptvguide.netlify.com/iptv.json'
# 		Dict['currentGuide'] = "Sports"
# 		cacheSeconds = 1800 # cache for 30 minutes
# 	else:
# 		Log.Info('Not Sports only')
# 		if Prefs['epg'] == 'iptv':
# 			scheduleFeedURL = secureEPG + '://iptvguide.netlify.com/tv.json'
# 		elif Prefs['epg'] == 'fogs':
# 			scheduleFeedURL = 'https://fast-guide.smoothstreams.tv/altepg/feedall1.json.gz'
# 		else:
# 			scheduleFeedURL = secureEPG + '://speed.guide.smoothstreams.tv/feed.json'
# 		Dict['currentGuide'] = "All"
# 		cacheSeconds = 21600 # cache for 6 hours because this guide is not updated often
# 	if Prefs['epg'] == 'fogs':
# 		inmemory = StringIO(urllib.urlopen(scheduleFeedURL).read())
# 		thetarfile = gzip.GzipFile(fileobj=inmemory, mode='rb')
# 		result = JSON.ObjectFromString(thetarfile.read().decode("utf-8"))
# 	else:
# 		result = JSON.ObjectFromURL(scheduleFeedURL, cacheTime = cacheSeconds)
# 	Log.Info("Getting guide from " + scheduleFeedURL)
#
# 	# these are going to get cached for future lookups
# 	channelsDict = {}
# 	showsList = []
# 	categoryDict = {}
#
# 	for channelId in result:
# 		channel = result[channelId]
#
# 		if 'items' in result[channelId]:
# 			myItems = result[channelId]['items']
# 		else:
# 			myItems = None
#
# 		channelsDict[channelId] = SsChannel(channel['channel_id'], channel['name'], myItems)
# 		channelName = channel['name']
#
# 		if not myItems is None:
# 			for show in myItems:
# 				endTime = GetDateTimeNative(show['end_time'])
# 				if endTime >= currentTime:
# 					startTime = GetDateTimeNative(show['time'])
#
# 					# clean up the categories
# 					if " " in show['category']:
# 						show['category'] = show['category'].replace(" ", "")
# 					if show['category'].lower() in ['', 'tv', 'generaltv', 'americanfootball'] and (show['name'].find("NFL") > -1 or show['description'].find("NFL") > -1 or show['description'].find("National Football League") > -1):
# 						show['category'] = u"NFL"
# 					elif show['category'].lower() in ['', 'tv', 'generaltv', 'icehockey'] and (show['name'].find("NHL") > -1 or show['description'].find("NHL") > -1 or show['description'].find("National Hockey League") > -1 or channelName[:3] == 'NHL'):
# 						show['category'] = u"NHL"
# 					elif show['category'].lower() == 'nascar':
# 						show['category'] = u"NASCAR"
# 					elif show['category'].lower() in ['', 'tv', 'generaltv', 'othersports']:
# 						if show['name'].find("NHL") > -1 or show['description'].find("NHL") > -1 or show['name'].find("Hockey") > -1:
# 							show['category'] = u"IceHockey"
# 						elif show['name'].find("NFL") > -1 or show['description'].find("NFL") > -1:
# 							show['category'] = u"NFL"
# 						elif show['name'].find("College Football") > -1 or show['name'].find("CFB") > -1:
# 							show['category'] = u"NCAAF"
# 						elif show['name'].find("Rugby") > -1 or show['description'].find("Rugby") > -1:
# 							show['category'] = u"Rugby"
# 						elif show['name'].find("FIFA") > -1 or show['name'].find("UEFA") > -1 or show['name'].find("EPL") > -1 or show['description'].find("FIFA") > -1 or show['name'].find("Soccer") > -1 or show['name'].find("Premier League") > -1 or show['description'].find("Premier League") > -1 or show['name'].find("Bundesliga") > -1 or show['description'].find("Bundesliga") > -1:
# 							show['category'] = u"WorldFootball"
# 						elif (show['name'].find("NBA") > -1 or show['description'].find("NBA") > -1 or channelName[:3] == 'NBA') and (show['name'].find("WNBA") == -1 or show['description'].find("WNBA") == -1):
# 							show['category'] = u"NBA"
# 						elif show['name'].find("MLB") > -1 or channelName[:3] == 'MLB':
# 							show['category'] = u"Baseball"
# 						elif show['name'].find("PGA") > -1 or channelName[:4] == 'Golf':
# 							show['category'] = u"Golf"
# 						elif show['name'].find("UFC") > -1 or show['description'].find("UFC") > -1 or channelName[:3] == 'UFC' or channelName[:5] == 'Fight':
# 							show['category'] = u"Boxing+MMA"
# 						elif show['name'].find("NASCAR") > -1 or show['description'].find("NASCAR") > -1:
# 							show['category'] = u"NASCAR"
# 						elif show['name'].find("WWE") > -1 or channelName[:3] == 'WWE':
# 							show['category'] = u"Wrestling"
# 						elif show['name'].find("Curling") > -1 or show['description'].find("Curling") > -1:
# 							show['category'] = u"Curling"
# 						elif show['name'].find("Darts") > -1 or show['description'].find("Darts") > -1:
# 							show['category'] = u"Darts"
# 						elif show['name'].find("Snooker") > -1 or show['description'].find("Snooker") > -1:
# 							show['category'] = u"Snooker"
# 						elif show['name'].find("News") > -1 or show['description'].lower().find("news") > -1 or channelName[:3] == 'CNN' or channelName[:4] == 'CNBC' or channelName == 'Fox News':
# 							show['category'] = u"News"
# 						elif ('runtime' in show and int(show['runtime']) > 70) and (channelName[:3] == 'HBO' or channelName[:7] == 'Cinemax' or channelName[:9] == 'Actionmax' or channelName[:8] == 'Showtime' or channelName[:3] == 'AMC' or channelName[:5] == 'Starz'):
# 							show['category'] = u"Movies"
# 						else:
# 							show['category'] = u"GeneralTV"
#
# 					if not show['category'] in categoryDict:
# 						categoryDict[show['category']] = []
# 					categoryDict[show['category']].append(show)
#
# 					if (channel['name'].upper().endswith("720P") or channel['name'].endswith("HD")) and show['quality'].lower() in ['', 'hqlq']:
# 						show['quality'] = "720p"
#
# 					if show['name'].startswith("Test Cricket"):
# 						show['name'] = show['name'][5:]
# 					if show['description'] == "No description":
# 						show['description'] = ""
#
# 					#if startTime < currentTime < endTime:
# 					#	nowPlayingDict.append(show)
# 					showsList.append(show)
#
# 	# Display and cache the dictionary info
# 	#Dict['nowPlayingDict'] = nowPlayingDict
# 	Dict['categoryDict'] = categoryDict
# 	Dict['channelsDict'] = channelsDict
# 	Dict['showsList'] = showsList
# 	Dict['guideValidUntil'] = datetime.datetime.now() + datetime.timedelta(minutes = GUIDE_CACHE_MINUTES)
# 	Dict.Save()
# 	Log.Info('Saved GetScheduleJson results')

def GetFullUrlFromChannelNumber(channelNum):
	url_template = '{0}://{1}:{2}/{3}/ch{4}q{5}.stream{6}?wmsAuthSign={7}'
	# rtmp_template = '{0}://{1}:{2}/{3}?wmsAuthSign={6}/ch{4}q{5}.stream'

	if Prefs['quality'] == 'LQ':
		quality = 3
	elif Prefs['quality'] == 'HQ':
		quality = 2
	else:
		quality = 1
	if int(channelNum) > int(Prefs['numQuality']):
		quality = 1
	return url_template.format(Dict['source'],Dict['server'],Dict['port'],Dict['service'],'%02d' % int(channelNum), quality, Dict['sourceext'], Dict['SPassW'])


def GetChannelThumb(chanNum = 0, chanName = "", category = "", large = False, chanFirst = False, fallBack = ""):
	if False: #Prefs['showThumbs'] == False:
		return None
	else:
		chanName = chanName.split('- ', 1)[-1].replace(" ", "").replace("720p", "")
		if chanNum == 0:
			sChanNum = ""
		else:
			sChanNum = str(chanNum)
		if large:
			chanAdd = "v"
		else:
			chanAdd = ""
		if not fallBack:
			fallBack = "https://placeholdit.imgix.net/~text?txtsize=25&bg=000000&txtclr=ffffff&w=195&h=110&fm=png&txttrack=0&txt=" + ((sChanNum + " " + chanName + " " + category).replace("  ", " ").replace(" ", "+")).strip()
		thumb = None
		if chanFirst:
			thumb = R(re.sub('[^A-Za-z0-9]+', '', chanName) + chanAdd + '.png')
			if thumb is None and "HD" in chanName:
				thumb = R(re.sub('[^A-Za-z0-9]+', '', chanName.replace("HD", "")) + chanAdd + '.png')
		if thumb is None and not category.replace(" ", "").lower() in ["", "tv", "generaltv"]:
			thumb = R(re.sub('[^A-Za-z0-9]+', '', category) + chanAdd + '.png')
		if thumb is None and not chanFirst:
			thumb = R(re.sub('[^A-Za-z0-9]+', '', chanName) + chanAdd + '.png')
		if thumb is None:
			thumb = fallBack
		return thumb

def find_between(s, first, last):
	try:
		start = s.index(first) + len(first)
		end = s.index(last, start)
		return s[start:end]
	except ValueError:
		return ""

def gather_codecs(url):
	codecs = {}
	try:
		url = GetFullUrlFromChannelNumber(url)
		session = requests.Session()
		result = session.get(url)
		data = result.text
		data = find_between(data, "INF:", "chunks")
		data = data.split(",")
		data2 = find_between(data, '"', '"')
		data2 = data2.split(",")
		for i in data:
			a = i.split("=")
			codecs[a[0]] = a[1]
		codecs["AUDIO"] = data2[0]
		codecs["VIDEO"] = data2[1]
	except:
		return {"BANDWIDTH":u'',"RESOLUTION":u'',"VIDEO":u'', "AUDIO":u''}

def build_channel_map():
	Dict['groups'] = {u'SSTV': {'order': 1, 'art': u'art-default.jpg', 'thumb': u'Icon-Default.png', 'title': u'SSTV'}}
	streams = {}
	thumb = "http://speed.guide.smoothstreams.tv/assets/images/channels/{0}.png"
	group_title=u'SSTV'
	Log.Info("Starting process for SSTV.")

	try:
		Log.Info("Fogs channel list succeded.")
		url = 'https://fast-guide.smoothstreams.tv/altepg/channels.json'
		jsonChanList = JSON.ObjectFromURL(url, encoding = 'utf-8')

		for item in jsonChanList:
			oChannel = jsonChanList[item]
			channum = oChannel["channum"]
			channel = int(oChannel["channum"])
			channame = oChannel["channame"].replace(" - ", "").strip()
			if channame == 'Empty':
				channame = channum
			codecs = gather_codecs(channel)
			stream = {
				'url': u'%s' % GetFullUrlFromChannelNumber(channel),
				'title': u'%s' % channame,
				'id': u'%s' % oChannel["xmltvid"],
				'name': u'%s' % channame,
				'thumb': u'%s' % thumb.format(channel),
				'art': u'', # % GetChannelThumb(channel, channame),
				'audio_codec': u'%s' % codecs["AUDIO"],
				'video_codec': u'%s' % codecs["VIDEO"],
				'container': u'',
				'protocol': u'%s' % 'hls' if Prefs["source"] == "https" else 'rtmp',
				'optimized_for_streaming': u'',
				'order': channel
			}
			streams.setdefault(unicode('All'), {})[channel] = stream
			streams.setdefault(unicode('SSTV'), {})[channel] = stream
	except:
		Log.Info("Fogs channel list failed, using SSTV.")
		url = 'https://speed.guide.smoothstreams.tv/feed-new.json'
		jsonEPG = JSON.ObjectFromURL(url, encoding='utf-8')
		jsonChanList = jsonEPG['data']

		for item in jsonChanList:

			oChannel = jsonChanList[item]
			channum = oChannel["number"]
			channel = int(oChannel["number"])
			channame = oChannel["name"].replace(" - ", "").strip()
			if channame == 'Empty':
				channame = channum

			stream = {
				'url': u'%s' % GetFullUrlFromChannelNumber(channel),
				'title': u'%s' % channame,
				'id': u'%s' % oChannel["number"],
				'name': u'%s' % channame,
				'thumb': u'%s' % thumb.format(channel),
				'art': u'',  # % GetChannelThumb(channel, channame),
				'audio_codec': u'',
				'video_codec': u'',
				'container': u'',
				'protocol': u'',
				'optimized_for_streaming': u'',
				'order': channel
			}
			streams.setdefault(unicode('All'), {})[channel] = stream
			streams.setdefault(unicode('SSTV'), {})[channel] = stream

	Dict['streams'] = streams
	Dict['last_playlist_load_datetime'] = datetime.datetime.utcnow()
	Dict['last_playlist_load_prefs'] = url
	Dict['last_playlist_load_filename_groups'] = False
	Dict['playlist_loading_in_progress'] = False
	Dict.Save()

	# {'No category': {1: {'art': u'', 'thumb': u'http://speed.guide.smoothstreams.tv/assets/images/channels/1.png',
	#                      'title': u'ESPNNews', 'url': u'https://fast-guide.smoothstreams.tv/altepg/channels.json',
	#                      'optimized_for_streaming': u'', 'protocol': u'', 'order': u'1', 'container': u'',
	#                      'audio_codec': u'', 'video_codec': u'', 'id': u'I59976.labs.zap2it.com', 'name': u'ESPNNews'},
	# {u'No category': {1: {'art': u'', 'thumb': u'http://192.168.1.3:80/sstv/1.png',
	#                       'title': u'ESPNNews','url': 'http://192.168.1.3:80/sstv/playlist.m3u8?ch=1&strm=hls&qual=1',
	# 	                     'optimized_for_streaming': u'', 'protocol': u'', 'order': 1, 'container': u'',
	# 	                     'audio_codec': u'', 'video_codec': u'', 'id': u'1', 'name': u'ESPNNews'},
####################################################################################################
def LoadXMLTV():

	Dict['guide_loading_in_progress'] = True
	channels = {}
	icons = {}
	guide = {}
	genres = {}
	genres['sports']  = []
	genres['all'] = []
	full_xmltv = 'https://fast-guide.smoothstreams.tv/altepg/xmltv3.xml.gz'
	fallback = 'https://fast-guide.smoothstreams.tv/altepg/xmltv1.xml.gz'
	fallback1 = 'http://ca.epgrepo.download/xmltv1.xml'
	fallback2 = 'http://eu.epgrepo.download/xmltv1.xml'
	sports_xmltv = 'https://fast-guide.smoothstreams.tv/feed.xml'



	def open_xmltv(xmltv_file):
		if xmltv_file.startswith('http://') or xmltv_file.startswith('https://'):
			# Plex can't handle compressed files, using standard Python methods instead
			if xmltv_file.endswith('.gz') or xmltv_file.endswith('.gz?raw=1'):
				f = io.BytesIO(urllib2.urlopen(xmltv_file).read())
				try:
					g = gzip.GzipFile(fileobj = f)
					xmltv = g.read()
				except:
					Log.Error('Provided file %s is not a valid GZIP file' % xmltv_file)
					xmltv = None
			else:
				xmltv = HTTP.Request(xmltv_file).content
		else:
			# Local compressed files are not supported at the moment
			xmltv = Resource.Load(xmltv_file, binary = True)
		return xmltv


	def process_xmltv(xmltv_file):
		xmltv = open_xmltv(xmltv_file)
		try:
			#root = XML.ElementFromString(xmltv, encoding = None)
			root = xml.etree.ElementTree.fromstring(xmltv)
		except:
			Log.Error('Provided file %s is not a valid XML file' % xmltv_file)
			root = None
		if root:
			for channel_elem in root.findall('./channel'):
				id = channel_elem.get('id')
				if id:
					for name in channel_elem.findall('display-name'):
						try:
							key = unicode(name.text, errors = 'replace')
						except TypeError:
							try:
								key = name.text.decode('utf-8')
							except:
								key = None
						if key:
							channels[key] = id
					icon_elem = channel_elem.find('icon')
					if icon_elem != None: # if icon_elem: does not work
						src_attr = icon_elem.get('src')
						if src_attr:
							icons[key] = src_attr
			count = 0
			current_datetime = datetime.datetime.now()
			for programme_elem in root.findall('./programme'):
				channel_attr = programme_elem.get('channel')
				try:
					channel = unicode(channel_attr, errors = 'replace')
				except TypeError:
					channel = channel_attr.decode('utf-8')
				start = StringToLocalDatetime(programme_elem.get('start'))
				stop = StringToLocalDatetime(programme_elem.get('stop'))
				if stop >= current_datetime:
					title_text = programme_elem.find('title').text
					if title_text:
						try:
							title = unicode(title_text, errors = 'replace')
						except TypeError:
							title = title_text.decode('utf-8')
					else:
						title = None
					if programme_elem.find('desc'):
						desc_text = programme_elem.find('desc').text
						if desc_text:
							try:
								desc = unicode(desc_text, errors = 'replace')
							except TypeError:
								desc = desc_text.decode('utf-8')
						else:
							desc = None
					else:
						desc = None
					if programme_elem.find('category'):
						genre_text = programme_elem.find('category').text
						if genre_text:
							try:
								genre = unicode(desc_text, errors = 'replace')
							except TypeError:
								genre = desc_text.decode('utf-8')
						else:
							genre = None
					else:
						genre = ''
					if genre.lower() == 'sports' or genre == '':
						if 'nba' in title.lower() or 'wnba' in title.lower() or 'ncaam' in title.lower()or 'basketball' in title.lower():
							genre = "Basketball"
						elif 'nfl' in title.lower() or 'american football' in title.lower() or 'ncaaf' in title.lower() or 'cfb' in title.lower():
							genre = "AmericanFootball"
						elif 'epl:' in title.lower() or 'efl:' in title.lower() or 'soccer' in title.lower() or 'ucl' in title.lower() or 'mls' in title.lower() or 'uefa' in title.lower() or 'fifa' in title.lower() or 'la liga' in title.lower() or 'serie a' in title.lower() or 'wcq' in title.lower():
							genre = "Soccer"
						elif 'rugby' in title.lower() or 'nrl' in title.lower() or 'afl' in title.lower() or 'sevens' in title.lower():
							genre = "Rugby"
						elif 'cricket' in title.lower() or 't20' in title.lower():
							genre = "Cricket"
						elif 'tennis' in title.lower() or 'squash' in title.lower() or 'atp' in title.lower():
							genre = "Tennis/Squash"
						elif 'f1' in title.lower() or 'nascar' in title.lower() or 'motogp' in title.lower() or 'racing' in title.lower():
							genre = "MotorSport"
						elif 'golf' in title.lower() or 'pga' in title.lower():
							genre = "Golf"
						elif 'boxing' in title.lower() or 'mma' in title.lower() or 'ufc' in title.lower() or 'wrestling' in title.lower() or 'wwe' in title.lower():
							genre = "Martial Sports"
						elif 'hockey' in title.lower() or 'nhl' in title.lower() or 'ice hockey' in title.lower():
							genre = "Ice Hockey"
						elif 'baseball' in title.lower() or 'mlb' in title.lower() or 'beisbol' in title.lower() or 'minor league' in title.lower():
							genre = "Baseball"
						else:
							genre = None
					if genre and not genre in genres['all']:
						genres['all'].append(genre)
						if genre.lower() in sports_list:
							genres['sports'].append(genre)
					count = count + 1
					item = {
						'start': start,
						'stop': stop,
						'title': title,
						'desc': desc,
						'genre': genre,
						'order': count
					}
					guide.setdefault(channel, {})[count] = item

	Log.Info("Starting process for SSTV EPG.")
	if Prefs['sportsOnly']:
		try:
			Log.Info("Sports EPG passed.")
			xmltv = open_xmltv(sports_xmltv)
			xmltv_file = sports_xmltv
		except:
			Log.Info("Sports EPG failed, trying Full.")
			xmltv = open_xmltv(full_xmltv)
			xmltv_file = full_xmltv
	else:
		try:
			Log.Info("Fogs 3day EPG passed.")
			xmltv = open_xmltv(full_xmltv)
			xmltv_file = full_xmltv
		except:
			try:
				Log.Info("Fogs 1day EPG passed.")
				xmltv = open_xmltv(fallback)
				xmltv_file = fallback
			except:
				Log.Info("Fogs EPG failed.")
				try:
					Log.Info("CA mirror EPG passed.")
					xmltv = open_xmltv(fallback1)
					xmltv_file = fallback1
				except:
					try:
						Log.Info("EU mirror EPG passed.")
						xmltv = open_xmltv(fallback2)
						xmltv_file = fallback2
					except:
						Log.Info("Full EPG failed, trying SSTV.")
						xmltv = open_xmltv(sports_xmltv)
						xmltv_file = sports_xmltv
	process_xmltv(xmltv_file)

	if Prefs['xmltv']:
		xmltv_files = Prefs['xmltv'].split(';')

		for xmltv_file in xmltv_files:
			Log.Info("Starting process for %s." % xmltv_file)
			process_xmltv(xmltv_file)

	Dict['genres'] = genres
	Dict['channels'] = channels
	Dict['icons'] = icons
	Dict['guide'] = guide
	Dict['last_guide_load_datetime'] = datetime.datetime.utcnow()
	Dict['last_guide_load_prefs'] = xmltv_file
	Dict['guide_loading_in_progress'] = False
	Dict.Save()

####################################################################################################
def StringToLocalDatetime(arg_string):
	# changes to remove seconds diff, currently getting differences in milliseconds which is causing times such as 14:59 for a start time, suspect due to program running time
	arg_string_split = arg_string.split(' ')
	arg_datetime = Datetime.ParseDate(arg_string_split[0])
	if len(arg_string_split) > 1:
		arg_offset_str = arg_string_split[1]
		arg_offset_hours = int(arg_offset_str[0:3])
		arg_offset_minutes = int(arg_offset_str[3:5])
		arg_offset_seconds = (arg_offset_hours * 60 * 60) + (arg_offset_minutes * 60)
		utc_datetime = arg_datetime - Datetime.Delta(seconds = arg_offset_seconds)
	else:
		utc_datetime = arg_datetime
	loc_offset_seconds = (datetime.datetime.now().replace(microsecond=0, second=0) - datetime.datetime.utcnow().replace(microsecond=0, second=0)).total_seconds()
	loc_datetime = utc_datetime + Datetime.Delta(seconds = loc_offset_seconds)
	return loc_datetime

####################################################################################################
def GuideReload():
	try:
		LoadXMLTV()
	except:
		Log.Info('Error loading xmltv.')


def GuideReloader():
	while True:
		time.sleep(300)
		if update_required(Dict['last_guide_load_datetime']):
			GuideReload()


def PlaylistReload():
	build_channel_map()
	try:
		LoadPlaylist(Dict['groups'], Dict['streams'])
	except:
		Log.Info('No other playlists provided.')

def PlaylistReloader():
	while True:
		time.sleep(300)
		if update_required(Dict['last_playlist_load_datetime']):
			PlaylistReload()

def update_required(input_time):
	try:
		current_datetime = datetime.datetime.utcnow()
		cur_utc_hr = datetime.datetime.utcnow().replace(microsecond=0, second=0, minute=0).hour
		target_utc_hr = (cur_utc_hr // 4) * 4
		target_utc_datetime = datetime.datetime.utcnow().replace(microsecond=0, second=0, minute=0, hour=target_utc_hr)
		Log.Info('Seeing if playlist update is required, latest update was %s and current time is %s' % (input_time, current_datetime))
		if current_datetime > target_utc_datetime and target_utc_datetime > input_time:
			return True
		else:
			return False
	except:
		return True