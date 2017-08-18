# -*- coding: utf-8 -*-
###################################################################################################
#
#	Smoothstreams plugin for XBMC
#	Copyright (C) 2016 Smoothstreams
#
###################################################################################################
import time
import calendar
import dateutil.parser
import datetime
import urllib
import SmoothAuth
import re
import htmlentitydefs
from dateutil.tz import tzlocal
import json
import os

THUMB_URL = 'http://smoothstreams.tv/schedule/includes/images/uploads/'
GUIDE_CACHE_MINUTES = 10

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

def getCurrentTimeNative():
	return datetime.datetime.now(tzlocal())

def GetDateTimeNative(strTime):
	try:
		parser = dateutil.parser()
		is_dst = time.daylight and time.localtime().tm_isdst > 0
		utc_offset = - (time.altzone if is_dst else time.timezone)
		return (parser.parse(strTime) - datetime.timedelta(hours=Dict['ScheduleUtcOffset'])).replace(tzinfo=dateutil.tz.tzutc()).astimezone(dateutil.tz.tzlocal())
	except:
		Log.Error("GetDateTimeNative " + strTime)

def IsDST():
    dt = datetime.datetime.utcnow()
    if dt.year < 2007:
        raise ValueError()
    dst_start = datetime.datetime(dt.year, 3, 8, 2, 0)
    dst_start += datetime.timedelta(6 - dst_start.weekday())
    dst_end = datetime.datetime(dt.year, 11, 1, 2, 0)
    dst_end += datetime.timedelta(6 - dst_end.weekday())
    return dst_start <= dt < dst_end

def IsScheduleInDst():
	#In the northern parts of the time zone, during the second Sunday in March, at 2:00 a.m. EST, clocks are advanced to 3:00 a.m. EDT
	# leaving a one hour "gap". During the first Sunday in November, at 2:00 a.m. EDT, clocks are moved back to 1:00 a.m. EST, thus "duplicating" one hour.
	Log.Error("not yet implemented, don't call this")
	return 0

def GetDstEnd():
	nowdate = datetime.datetime.now()
	novFirstDate = datetime.date(nowdate.year, nowdate.month, 1)
	delta = (6 - novFirstDate.weekday())
	return datetime.datetime(nowdate.year, nowdate.month, delta,2,0,0,0)

def GetDstStart():
	nowdate = datetime.datetime.now()
	marDate = datetime.date(nowdate.year, 11, 1)
	delta = (13 - marDate.weekday())
	return datetime.datetime(nowdate.year, nowdate.month, delta,2,0,0,0)

def GetServerUrlByName(serverLocation=None):
	if serverLocation == 'EU Random':
		return "deu.SmoothStreams.tv"
	elif serverLocation == 'EU DE-Frankfurt':
		return "deu.de1.SmoothStreams.tv"
	elif serverLocation == 'EU NL-EVO':
		return "deu.nl2.SmoothStreams.tv"
	elif serverLocation == 'EU NL-i3d':
		return "deu.nl1.SmoothStreams.tv"
	elif serverLocation == 'EU UK Random':
		return "deu.uk.SmoothStreams.tv"
	elif serverLocation == 'EU UK-London1':
		return "deu.uk1.SmoothStreams.tv"
	elif serverLocation == 'EU UK-London2':
		return "deu.uk2.SmoothStreams.tv"
	elif serverLocation == 'US All':
		return "dna.SmoothStreams.tv"
	elif serverLocation == 'US East':
		return "dnae.SmoothStreams.tv"
	elif serverLocation == 'US West':
		return "dnaw.SmoothStreams.tv"
	elif serverLocation == 'US East-NJ':
		return "dnae1.SmoothStreams.tv"
	elif serverLocation == 'US East-VA':
		return "dnae2.SmoothStreams.tv"
	elif serverLocation == 'US East-CAN':
		return "dnae3.SmoothStreams.tv"
	elif serverLocation == 'US East-CAN2':
		return "dnae4.SmoothStreams.tv"
	elif serverLocation == 'Asia':
		return "dsg.SmoothStreams.tv"
	else:
		Log.Error('Invalid serverName passed to GetServerUrlByName ' + serverLocation)
		return None

def GetServicePort(serviceName=None):
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
	else:
		Log.Error('Invalid service name supplied to GetServicePort')
	return port

def GetScheduleJson(OnlyGetNowPlaying=False, IgnorePast=False):
	if "guideValidUntil" in Dict and Dict['guideValidUntil'] > datetime.datetime.now():
		Log.Info('Guide load not needed')
		return

	Log.Info('Starting GetScheduleJson')

	currentTime = getCurrentTimeNative()

	if IsDST():
		Dict['ScheduleUtcOffset'] = -4
	else:
		Dict['ScheduleUtcOffset'] = -5

	parser = dateutil.parser()
	if Prefs['secureEPG']:
		secureEPG = 'https'
	else:
		secureEPG = 'http'
	if Prefs['sportsOnly']:
		scheduleFeedURL = secureEPG + '://iptvguide.netlify.com/iptv.json'
		Dict['currentGuide'] = "Sports"
		cacheSeconds = 1800 # cache for 30 minutes
	else:
		if Prefs['epg'] == 'iptv':
			scheduleFeedURL = secureEPG + '://iptvguide.netlify.com/tv.json'
		elif Prefs['epg'] == 'fogs':
			scheduleFeedURL = secureEPG + '://sstv.fog.pt/feedall1.json '
		else:
			scheduleFeedURL = secureEPG + '://speed.guide.smoothstreams.tv/feed.json'
		Dict['currentGuide'] = "All"
		cacheSeconds = 21600 # cache for 6 hours because this guide is not updated often
	result = JSON.ObjectFromURL(scheduleFeedURL, cacheTime = cacheSeconds)
	Log.Info("Getting guide from " + scheduleFeedURL)
	
	# these are going to get cached for future lookups
	channelsDict = {}
	showsList = []
	categoryDict = {}
	
	for channelId in result:
		channel = result[channelId]
		
		if 'items' in result[channelId]:
			myItems = result[channelId]['items']
		else:
			myItems = None

		channelsDict[channelId] = SsChannel(channel['channel_id'], channel['name'], myItems)
		channelName = channel['name']

		if not myItems is None:
			for show in myItems:
				endTime = GetDateTimeNative(show['end_time'])
				if endTime >= currentTime:
					startTime = GetDateTimeNative(show['time'])

					# clean up the categories
					if " " in show['category']:
						show['category'] = show['category'].replace(" ", "")
					if show['category'].lower() in ['', 'tv', 'generaltv', 'americanfootball'] and (show['name'].find("NFL") > -1 or show['description'].find("NFL") > -1 or show['description'].find("National Football League") > -1):
						show['category'] = u"NFL"
					elif show['category'].lower() in ['', 'tv', 'generaltv', 'icehockey'] and (show['name'].find("NHL") > -1 or show['description'].find("NHL") > -1 or show['description'].find("National Hockey League") > -1 or channelName[:3] == 'NHL'):
						show['category'] = u"NHL"
					elif show['category'].lower() == 'nascar':
						show['category'] = u"NASCAR"
					elif show['category'].lower() in ['', 'tv', 'generaltv', 'othersports']:
						if show['name'].find("NHL") > -1 or show['description'].find("NHL") > -1 or show['name'].find("Hockey") > -1:
							show['category'] = u"IceHockey"
						elif show['name'].find("NFL") > -1 or show['description'].find("NFL") > -1:
							show['category'] = u"NFL"
						elif show['name'].find("College Football") > -1 or show['name'].find("CFB") > -1:
							show['category'] = u"NCAAF"
						elif show['name'].find("Rugby") > -1 or show['description'].find("Rugby") > -1:
							show['category'] = u"Rugby"
						elif show['name'].find("FIFA") > -1 or show['name'].find("UEFA") > -1 or show['name'].find("EPL") > -1 or show['description'].find("FIFA") > -1 or show['name'].find("Soccer") > -1 or show['name'].find("Premier League") > -1 or show['description'].find("Premier League") > -1 or show['name'].find("Bundesliga") > -1 or show['description'].find("Bundesliga") > -1:
							show['category'] = u"WorldFootball"
						elif (show['name'].find("NBA") > -1 or show['description'].find("NBA") > -1 or channelName[:3] == 'NBA') and (show['name'].find("WNBA") == -1 or show['description'].find("WNBA") == -1):
							show['category'] = u"NBA"
						elif show['name'].find("MLB") > -1 or channelName[:3] == 'MLB':
							show['category'] = u"Baseball"
						elif show['name'].find("PGA") > -1 or channelName[:4] == 'Golf':
							show['category'] = u"Golf"
						elif show['name'].find("UFC") > -1 or show['description'].find("UFC") > -1 or channelName[:3] == 'UFC' or channelName[:5] == 'Fight':
							show['category'] = u"Boxing+MMA"
						elif show['name'].find("NASCAR") > -1 or show['description'].find("NASCAR") > -1:
							show['category'] = u"NASCAR"
						elif show['name'].find("WWE") > -1 or channelName[:3] == 'WWE':
							show['category'] = u"Wrestling"
						elif show['name'].find("Curling") > -1 or show['description'].find("Curling") > -1:
							show['category'] = u"Curling"
						elif show['name'].find("Darts") > -1 or show['description'].find("Darts") > -1:
							show['category'] = u"Darts"
						elif show['name'].find("Snooker") > -1 or show['description'].find("Snooker") > -1:
							show['category'] = u"Snooker"
						elif show['name'].find("News") > -1 or show['description'].lower().find("news") > -1 or channelName[:3] == 'CNN' or channelName[:4] == 'CNBC' or channelName == 'Fox News':
							show['category'] = u"News"
						elif ('runtime' in show and int(show['runtime']) > 70) and (channelName[:3] == 'HBO' or channelName[:7] == 'Cinemax' or channelName[:9] == 'Actionmax' or channelName[:8] == 'Showtime' or channelName[:3] == 'AMC' or channelName[:5] == 'Starz'):
							show['category'] = u"Movies"
						else:
							show['category'] = u"GeneralTV"

					if not show['category'] in categoryDict:
						categoryDict[show['category']] = []
					categoryDict[show['category']].append(show)

					if (channel['name'].upper().endswith("720P") or channel['name'].endswith("HD")) and show['quality'].lower() in ['', 'hqlq']:
						show['quality'] = "720p"

					if show['name'].startswith("Test Cricket"):
						show['name'] = show['name'][5:]
					if show['description'] == "No description":
						show['description'] = ""

					#if startTime < currentTime < endTime:
					#	nowPlayingDict.append(show)
					showsList.append(show)

	# Display and cache the dictionary info
	#Dict['nowPlayingDict'] = nowPlayingDict
	Dict['categoryDict'] = categoryDict
	Dict['channelsDict'] = channelsDict
	Dict['showsList'] = showsList
	Dict['guideValidUntil'] = datetime.datetime.now() + datetime.timedelta(minutes = GUIDE_CACHE_MINUTES)
	Dict.Save()
	Log.Info('Saved GetScheduleJson results')

def GetFullUrlFromChannelNumber(channelNum, source, checkQuality = False):
	#Log.Debug('HELP,Source is ' + str(source))
	if checkQuality:
		return GetChannelUrlByQuality(channelNum, True)
	if Prefs['quality'] == 'LQ':
		quality = 3
	elif Prefs['quality'] == 'HQ':
		quality = 2
	else:
		quality = 1
	numQuality = Prefs['numQuality']
	if int(channelNum) > int(numQuality):
		quality = 1
	if Prefs["customServer"] is not None and len(Prefs['customServer']) > 0 and ":" in Prefs['customServer'] > 0:
		server = Prefs['customServer'].split(":")[0]
		servicePort = Prefs['customServer'].split(":")[1]
	else:
		server = GetServerUrlByName(Prefs["serverLocation"])
		servicePort = GetServicePort(Prefs['service'])
	if source == "HLS":
		try:
				channelUrl = 'https://%s:%s/%s/ch%sq%s.stream/playlist.m3u8?wmsAuthSign=%s' % (server, servicePort, SmoothAuth.getLoginSite(),'%02d' % int(channelNum), quality, Dict['SPassW'])
		except:
				servicePort = 3625
				channelUrl = 'rtmp://%s:%s/%s?wmsAuthSign=%s/ch%sq%s.stream' % (server, servicePort, SmoothAuth.getLoginSite(), Dict['SPassW'],'%02d' % int(channelNum), quality)
	
	else:
		try:
				servicePort = 3625
				channelUrl = 'rtmp://%s:%s/%s?wmsAuthSign=%s/ch%sq%s.stream' % (server, servicePort, SmoothAuth.getLoginSite(), Dict['SPassW'],'%02d' % int(channelNum), quality)
		except:
				channelUrl = 'https://%s:%s/%s/ch%sq%s.stream/playlist.m3u8?wmsAuthSign=%s' % (server, servicePort, SmoothAuth.getLoginSite(),'%02d' % int(channelNum), quality, Dict['SPassW'])
				servicePort = GetServicePort(Prefs['service'])
	return channelUrl

def GetChannelSummaryText(channelInfo=None):
	if Prefs['showThumbs']==False:
		return None
	else:
		return channelInfo

def GetChannelThumb(chanNum = 0, chanName = "", category = "", large = False, chanFirst = False):
	if Prefs['showThumbs'] == False:
		return None
	else:
		chanName = chanName.replace(" ", "").replace("720p", "")
		if chanNum == 0:
			sChanNum = ""
		else:
			sChanNum = str(chanNum)
		if large:
			chanAdd = "v"
			fallBack = "https://placeholdit.imgix.net/~text?txtsize=25&bg=000000&txtclr=ffffff&w=195&h=110&fm=png&txttrack=0&txt=" + ((sChanNum + " " + chanName + " " + category).replace("  ", " ").replace(" ", "+")).strip()
		else:
			chanAdd = ""
			fallBack = "https://placeholdit.imgix.net/~text?txtsize=25&bg=000000&txtclr=ffffff&w=120&h=120&fm=png&txttrack=0&txt=" + ((sChanNum + " " + chanName + " " + category).replace("  ", " ").replace(" ", "+")).strip()

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

def GetShowTimeText(show):
	timeString = u''

	parser = dateutil.parser()
	startTime = GetDateTimeNative(show['time'])
	endTime = GetDateTimeNative(show['end_time'])

	timeString += str(int(startTime.strftime('%I'))) + startTime.strftime(':%M').replace(":00", "")
	if (startTime.hour <= 12 and endTime.hour > 11) or (startTime.hour > 12 and endTime.hour <= 12):
		timeString += startTime.strftime('%p')[:1]

	timeString += "-" + str(int(endTime.strftime('%I'))) + endTime.strftime(':%M').replace(":00", "") + endTime.strftime('%p')[:1]

	return timeString

def IsShowNowPlaying(show):
	try:
		parser = dateutil.parser()
		currentTime = getCurrentTimeNative()
		endTime = GetDateTimeNative(show['end_time'])
		startTime = GetDateTimeNative(show['time'])
		return startTime <= currentTime <= endTime
	except:
		return False

class SsChannel:
	''' Exposes features useful for a specific channel and its shows '''
	def __init__(self, id, name, items):
		self.channel_id = id
		self.name = name
		self.items = items

	def NowPlaying(self):
		parser = dateutil.parser()
		currentTime = getCurrentTimeNative()

		if not self.items is None:
			for item in self.items:
				endTime = GetDateTimeNative(item['end_time'])
				startTime = GetDateTimeNative(item['time'])
			
				if startTime <= currentTime <= endTime:
					return item

	def Upcoming(self):
		parser = dateutil.parser()
		currentTime = getCurrentTimeNative()

		if not self.items is None:
			results = []
			for item in self.items:
				endTime = GetDateTimeNative(item['end_time'])
				startTime = GetDateTimeNative(item['time'])
				if startTime >= currentTime and endTime > currentTime:
					results.append(item)

			results.sort(key = lambda x: (x['time']))
			return results

	def GetChannel(self):
		try:
			if self.NowPlaying() is None:
				return self.name
			else:
				nowPlaying = self.NowPlaying()
				if "language" in nowPlaying and nowPlaying['language'].upper() != "US":
					language = ' ' + nowPlaying['language'].upper()
				return self.name + ': ' + nowPlaying['name'] + ' ' + nowPlaying['quality'] + language + ' ' + GetShowTimeText(nowPlaying) + u' (' + nowPlaying['category'] + u')'
		except:
			return ""

	def GetStatusText(self):
		#returns status of either what's currently playing or what's next
		language = ""

		try:
			if self.NowPlaying() is None:
				if self.Upcoming() is None or len(self.Upcoming())==0:
					return self.name
				else:
					upcoming = self.Upcoming()[0]
					if "language" in upcoming and upcoming['language'].upper() != "US":
						language = ' ' + upcoming['language'].upper()
					#return self.name
					return "NEXT " + self.name + ': ' + upcoming['name'] + ' ' + upcoming['quality'] + language + ' ' + GetShowTimeText(upcoming) + u' (' + upcoming['category'] + u')'
			else:
				nowPlaying = self.NowPlaying()
				if "language" in nowPlaying and nowPlaying['language'].upper() != "US":
					language = ' ' + nowPlaying['language'].upper()
				return "LIVE " + self.name + ': ' + nowPlaying['name'] + ' ' + nowPlaying['quality'] + language + ' ' + GetShowTimeText(nowPlaying) + u' (' + nowPlaying['category'] + u')'
		except:
			return ""

	def GetStatusText1(self):
		#returns status of either what's currently playing or what's next
		language = ""

		try:
			if self.NowPlaying() is None:
				if self.Upcoming() is None or len(self.Upcoming())==0:
					return self.name
				else:
					upcoming = self.Upcoming()[0]
					if "language" in upcoming and upcoming['language'].upper() != "US":
						language = ' ' + upcoming['language'].upper()
					return "NEXT " + upcoming['network'] + ': ' + upcoming['name'] + ' ' + upcoming['quality'] + language + GetShowTimeText(upcoming)
			else:
				nowPlaying = self.NowPlaying()
				if "language" in nowPlaying and nowPlaying['language'].upper() != "US":
					language = ' ' + nowPlaying['language'].upper()
				return "LIVE " + (u'%02d ' % int(self.channel_id)) + ' ' + nowPlaying['name'] + ' ' + nowPlaying['quality'] + language + GetShowTimeText(nowPlaying) + u' (' + nowPlaying['category'] + u')'
		except:
			return ""

	def GetStatusText2(self):
		#returns status of either what's currently playing or what's next
		if self.NowPlaying() is None:
			if self.Upcoming() is None or len(self.Upcoming())==0:
				return "C" + (u'%02d' % int(self.channel_id))
			else:
				upcoming = self.Upcoming()[0]
				return "C" + (u'%02d' % int(self.channel_id))
		else:
			nowPlaying = self.NowPlaying()
			return "C" + (u'%02d' % int(self.channel_id))

	def GetStatusText3(self):
		#returns status of either what's currently playing or what's next
		language = ""

		try:
			if self.NowPlaying() is None:
				if self.Upcoming() is None or len(self.Upcoming())==0:
					return fix_text(self.name)
				else:
					upcoming = self.Upcoming()[0]
					if "language" in upcoming and upcoming['language'].upper() != "US":
						language = ' ' + upcoming['language'].upper()
					return 'NEXT: ' + fix_text(GetShowTimeText(upcoming) + ' ' + upcoming['name'] + ' ' + upcoming['quality'] + language)
			else:
				nowPlaying = self.NowPlaying()
				if "language" in nowPlaying and nowPlaying['language'].upper() != "US":
					language = ' ' + nowPlaying['language'].upper()
				return "LIVE " + fix_text((u'%02d ' % int(self.channel_id)) + ' ' + nowPlaying['name'] + ' ' + nowPlaying['quality'] + language + GetShowTimeText(nowPlaying) + u' (' + nowPlaying['category'] + u')')
		except:
			return ""

	def GetStatusText4(self):
		#returns status of either what's currently playing or what's next
		if self.NowPlaying() is None:
			return "E " + fix_text(self.name)
		#else:
		#	nowPlaying = self.NowPlaying()
		#	return fix_text((u'%02d ' % int(self.channel_id)) + '- ' + nowPlaying['name'] + ' ' + nowPlaying['quality'] + GetShowTimeText(nowPlaying) + u' (' + nowPlaying['category'] + u')')
