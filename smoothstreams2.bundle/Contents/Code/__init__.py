# -*- coding: utf-8 -*-
###################################################################################################
#
#	Smoothstreams plugin for XBMC
#	Copyright (C) 2016 Smoothstreams
#
###################################################################################################
import sys
import os
import dateutil.parser
import datetime
import urllib2
import SmoothUtils
import SmoothAuth
import traceback
import operator
import bisect
import time
import calendar
import shlex

Smoothstreams_URL = 'http://www.Smoothstreams.com'
Smoothstreams_URL1 = 'http://a.video.Smoothstreams.com/'
BASE_URL = 'http://www.Smoothstreams.com/videos'

MIN_CHAN = 1 # probably a given
MAX_CHAN = 150 # changed this to a preference

VIDEO_PREFIX = ''
NAME = 'Smoothstreams'
PREFIX = '/video/' + NAME.replace(" ", "+") + 'videos'
PLUGIN_VERSION = ''
PLUGIN_VERSION_LATEST = ''
source = ''

ART  = 'art-default.png'
ICON = 'icon-default.png'
####################################################################################################

def Start():
	getLatestVersion()
	Log.Info("***{0} starting Python Version {1} TimeZone {2} PluginVersion {3}".format(NAME, sys.version, time.timezone, PLUGIN_VERSION))
	loginResult = SmoothAuth.login()
	scheduleResult = SmoothUtils.GetScheduleJson()
	if Dict['SPassW'] is None:
		Log.Info('Bad login here, need to display it')
		ObjectContainer.title1 = NAME + " - Enter Login Details ->"
		ObjectContainer.art = R(ART)
	else:
		ObjectContainer.title1 = NAME
		ObjectContainer.art = R(ART)
		DirectoryObject.thumb = R("Smoothstreams-network.png")
		HTTP.Headers['User-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.8; rv:22.0) Gecko/20100101 Firefox/22.0'

####################################################################################################

def sourceType():
	#Standard default setting
	source = Prefs['sourcetype']
	#Client videotype overide
	hlsClients = []
	rtmpClients = []
	if not Prefs['hlsClient'] is None and len(Prefs['hlsClient']) > 2:
		for client in Prefs['hlsClient'].split(";"):
			hlsClients.append(client)
	if not Prefs['rtmpClient'] is None and len(Prefs['rtmpClient']) > 2:
		for client in Prefs['rtmpClient'].split(";"):
			rtmpClients.append(client)
	if str(Client.Platform) in hlsClients:
		source = "HLS"
		Log.Debug('Forcing HLS stream based on detected platform ' + str(Client.Platform))
	elif str(Client.Platform) in rtmpClients:
		source = "RTMP"
		Log.Debug('Forcing RTMP stream based on detected platform ' + str(Client.Platform))
	else:
		Log.Debug('Using user settings for client: ' + str(Client.Platform))
		Log.Debug('Source is ' + str(source))
	return source

###################################################################################################

@route(PREFIX + '/ValidatePrefs')
def ValidatePrefs():
	Log.Info("***{0} ValidatePrefs Python Version {1} TimeZone {2} PluginVersion {3}".format(NAME, sys.version, time.timezone, PLUGIN_VERSION))
	# Do we need to reset the extentions?
	loginResult = SmoothAuth.login()
	if Prefs['simple'] != 'Yes (No EPG)':
		scheduleResult = SmoothUtils.GetScheduleJson()
	Log.Info(repr(loginResult))
	return loginResult

#################################################################################################
@handler(PREFIX, NAME, thumb = ICON, art = ART)
def VideoMainMenu():
	Log.Info(PLUGIN_VERSION + ' VideoMainMenu called: ')
	MAX_CHAN = int(Prefs['numChannels'])
	oc = ObjectContainer()
	source = sourceType()

	if PLUGIN_VERSION_LATEST > PLUGIN_VERSION:
		updateAvailable = " - plugin update available"
	else:
		updateAvailable = ""


	if Prefs['simple'] == 'Yes':
		return SimpleStreams()
	elif Prefs['simple'] == 'Yes (No EPG)':
		return SimpleStreamsNoEPG()
	else:
		if (Dict['currentGuide'] == "Sports" and Prefs['sportsOnly']) or (Dict['currentGuide'] == "All" and not Prefs['sportsOnly']):
			scheduleResult = SmoothUtils.GetScheduleJson()
		if Dict['SPassW'] is None or Prefs['serverLocation'] is None or Prefs['username'] is None or Prefs['service'] is None:
			Log.Info('No password yet')
			ObjectContainer.title1 = NAME + updateAvailable + ' - Enter Login Details and Server Preferences then Refresh ->'
			oc.add(PrefsObject(title = "Preferences", thumb = R("icon-prefs.png")))
		else:
			ObjectContainer.title1 = NAME + updateAvailable
			oc.add(DirectoryObject(key = Callback(LiveMenu), title = "Live", thumb = SmoothUtils.GetChannelThumb(chanName = "Live"), summary = "Live shows"))
			oc.add(DirectoryObject(key = Callback(ChannelsMenu), title = "Channels", thumb = SmoothUtils.GetChannelThumb(chanName = "Channels"), summary = "Channel List"))
			oc.add(DirectoryObject(key = Callback(CategoriesMenu), title = "Categories", thumb = SmoothUtils.GetChannelThumb(chanName = "Categories"), summary = "Category List"))
			oc.add(DirectoryObject(key = Callback(ScheduleListMenu), title = "Schedule", thumb = SmoothUtils.GetChannelThumb(chanName = "Schedule"), summary = "Schedule List"))

			# TODO: add custom categories
			if not Prefs['mySearch'] is None and len(Prefs['mySearch']) > 2:
				for mySearch in Prefs['mySearch'].split(";"):
					if ":" in mySearch:
						title = mySearch.split(":")[0].strip()
						searchString = mySearch.split(":")[1].strip()
					else:
						title = mySearch
						searchString = mySearch
					thumb = SmoothUtils.GetChannelThumb(category = title.replace(" HD", "").replace(" NOW", "").replace(" NEXT", "").replace(" BEST", ""), large = False)
					oc.add(DirectoryObject(key = Callback(SearchShows, query = searchString), title = title, thumb = thumb))

			oc.add(InputDirectoryObject(key = Callback(SearchShows), title = "Search Shows", prompt = 'Enter show title'))

			# Preferences
			oc.add(PrefsObject(title = "Preferences", thumb = R("icon-prefs.png")))

	return oc
###################################################################################################
@route(PREFIX + '/simple')
def SimpleStreams(url = None):
	oc = ObjectContainer()
	source = sourceType()
	Log.Debug('Channels menu: Source is ' + str(source))
	#oc = ObjectContainer(title2 = "Channels")
	Log.Info(PLUGIN_VERSION + ' ChannelsMenu')
	channelsDict = Dict['channelsDict']
	channelText = ''
	currentTime = SmoothUtils.getCurrentTimeNative()

	for i in range(1, 5):
		if not channelsDict is None:
			break
		Log.Info('sleeping 500ms for async schedule details to return')
		Thread.Sleep(0.5)

	for channelNum in range(1, MAX_CHAN + 1):
		if not channelsDict is None and str(channelNum) in channelsDict:
			channelItem = channelsDict[str(channelNum)]
			channelName = channelItem.name.replace("720P", "HD")
			nowPlaying = channelItem.NowPlaying()
			upcoming = channelItem.Upcoming()
			if not upcoming is None and len(upcoming) > 0:
				upcoming = upcoming[0]

			if nowPlaying is None:
				titleText = formatShowText(channelItem, nowPlaying, currentTime, "#{ch} {chname}")
				category = ""
				tagLine = ""
			else:
				titleText = formatShowText(channelItem, nowPlaying, currentTime, "#{ch} {chname} {title} {qual} {lang} {time} ({cat})")
				category = nowPlaying['category']
				tagLine = nowPlaying['description']

			if upcoming is None or len(upcoming) == 0:
				summaryText = ""
			else:
				summaryText = formatShowText(channelItem, upcoming, currentTime, "{when} {title} {qual} {lang} {time} ({cat})")

			thumb = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = category, large = False) #, chanFirst = True

			if Prefs['channelDetails']:
				channelUrl = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)
				oc.add(DirectoryObject(key = Callback(PlayMenu, url = channelUrl, channelNum = channelNum), title = SmoothUtils.fix_text(titleText), thumb = thumb))
			else:
				thumbV = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = category, large = True) #, chanFirst = True
				oc.add(VideoClipObject(
					key = Callback(CreateVideoClipObject,
						url = HTTPLiveStreamURL(SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)),
						title = SmoothUtils.fix_text(titleText),
						tagline = SmoothUtils.fix_text(tagLine),
						summary = SmoothUtils.fix_text(summaryText),
						thumb = thumbV,
						studio = channelName,
						quotes = "",
						container = True),
					url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source),
					title = SmoothUtils.fix_text(titleText),
					tagline = SmoothUtils.fix_text(tagLine),
					summary = SmoothUtils.fix_text(summaryText),
					studio = channelName,
					quotes = "",
					thumb = thumbV,
					items = [
						MediaObject(
							parts = [ PartObject(key = HTTPLiveStreamURL(url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)), duration = 1000) ],
							optimized_for_streaming = True
						)
					]
					))
	return oc

###################################################################################################
@route(PREFIX + '/simplenoepg')
def SimpleStreamsNoEPG(url = None):
	oc = ObjectContainer()
	source = sourceType()
	Log.Debug('Channels menu: Source is ' + str(source))
	#oc = ObjectContainer(title2 = "Channels")
	Log.Info(PLUGIN_VERSION + ' ChannelsMenu')
	channelsDict = Dict['channelsDict']
	channelText = ''
	currentTime = SmoothUtils.getCurrentTimeNative()

	# for i in range(1, 5):
	# 	if not channelsDict is None:
	# 		break
	# 	Log.Info('sleeping 500ms for async schedule details to return')
	# 	Thread.Sleep(0.5)

	for channelNum in range(1, MAX_CHAN + 1):
		# if not channelsDict is None and str(channelNum) in channelsDict:
		summaryText = ""

		thumb = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = "", category = "", large = False) #, chanFirst = True
		thumbV = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = "", category = "", large = True) #, chanFirst = True
		oc.add(VideoClipObject(
			key = Callback(CreateVideoClipObject,
				url = HTTPLiveStreamURL(SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)),
				title = channelNum,
				tagline = "",
				summary = "",
				thumb = thumbV,
				studio = "",
				quotes = "",
				container = True),
			url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source),
			title = channelNum,
			tagline = "",
			summary = "",
			studio = channelNum,
			quotes = "",
			thumb = thumbV,
			items = [
				MediaObject(
					parts = [ PartObject(key = HTTPLiveStreamURL(url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)), duration = 1000) ],
					optimized_for_streaming = True
				)
			]
			))
	return oc

###################################################################################################

@route(PREFIX + '/searchShows')
def SearchShows(query):
	source = sourceType()
	channelsDict = Dict['channelsDict']
	showsListAll = Dict['showsList']
	oc = ObjectContainer(title2 = "Search Results for {0}".format(query))
	for i in range(1, 5):
		if not channelsDict is None and not showsListAll is None:
			break
		Log.Info('sleeping 500ms for async schedule details to return')
		Thread.Sleep(0.5)

	currentTime = SmoothUtils.getCurrentTimeNative()
	summaryText = ''

	query = [x.strip().upper() for x in shlex.split(query)]
	hdOnly = Prefs['hdOnly'] #or "HD" in query or "SD" in query DISABLED CURRENTLY
	nowOnly = "NOW" in query
	nextOnly = "NEXT" in query
	bestOnly = "BEST" in query
	#if hdOnly == "HD only": query.remove("HD") DISABLED CURRENTLY
	#if hdOnly == "SD only": query.remove("SD") DISABLED CURRENTLY
	if nowOnly: query.remove("NOW")
	if nextOnly: query.remove("NEXT")
	if bestOnly: query.remove("BEST")
	if nowOnly and nextOnly:
		nextOnly = False

	showsList = []
	for show in showsListAll:
		keepShow = False
		showName = show['name'].upper()
		showCat = show['category'].replace(" ", "").upper()
		showDesc = show['description'].upper()
		startTime = SmoothUtils.GetDateTimeNative(show['time'])
		endTime = SmoothUtils.GetDateTimeNative(show['end_time'])
		if endTime >= currentTime and (not nowOnly or startTime <= currentTime):
			if len(show['quality']) == 0:
				show['quality'] = 'unk'
			if startTime <= currentTime:
				show['SORTER'] = "A" + show['name'] + show['time'] + show['quality']
			else:
				show['SORTER'] = "B" + show['time'] + show['name'] + show['quality']
			if not nextOnly or (startTime > currentTime and startTime <= currentTime + datetime.timedelta(minutes = 90)):
				if hdOnly == "SD only" and not (show['quality'].lower() == '720p' or show['quality'].lower() == '1080i'):
					if len(query) == 0:
						keepShow = True
					else:
						for searchString in query:
							if len(searchString) > 0 and (showCat == searchString or showName.find(searchString) > -1 or showDesc.find(searchString) > -1):
								keepShow = True
								break
				if hdOnly == "HD only" and (show['quality'].lower() == '720p' or show['quality'].lower() == '1080i'):
					if len(query) == 0:
						keepShow = True
					else:
						for searchString in query:
							if len(searchString) > 0 and (showCat == searchString or showName.find(searchString) > -1 or showDesc.find(searchString) > -1):
								keepShow = True
								break
				if hdOnly == "Both":
					if len(query) == 0:
						keepShow = True
					else:
						for searchString in query:
							if len(searchString) > 0 and (showCat == searchString or showName.find(searchString) > -1 or showDesc.find(searchString) > -1):
								keepShow = True
								break
		if keepShow:
			showsList += [show]

	showsList.sort(key = lambda x: (x['SORTER']))

	showCount = 0
	lastShow = ""
	for show in showsList:
		channelNum = str(show['channel'])
		channelItem = channelsDict[str(channelNum)]
		channelName = channelItem.name.replace("720P", "HD")
		titleText = formatShowText(channelItem, show, currentTime, "{when} {title} {qual} {lang} {time} ({cat}) {chname} #{ch}")
		channelUrl = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)
		thumb = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = "", large = False)
		showCount += 1

		if not bestOnly or lastShow != show['time'] + show['name']:
			if Prefs['channelDetails']:
				oc.add(DirectoryObject(key = Callback(PlayMenu, url = channelUrl, channelNum = channelNum), title = titleText, tagline = SmoothUtils.fix_text(show['description']), thumb = thumb))
			elif SmoothUtils.GetDateTimeNative(show['time']) < currentTime:
				thumbV = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = "", large = True)
				oc.add(VideoClipObject(
					key = Callback(CreateVideoClipObject,
						url = HTTPLiveStreamURL(SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)),
						title = SmoothUtils.fix_text(titleText),
						tagline = SmoothUtils.fix_text(show['description']),
						summary = "",
						thumb = thumbV,
						container = True),
					url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source),
					title = SmoothUtils.fix_text(titleText),
					tagline = SmoothUtils.fix_text(show['description']),
					summary = "",
					thumb = thumbV,
					items = [
						MediaObject(
							parts = [ PartObject(key = HTTPLiveStreamURL(url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)), duration = 1000) ],
							optimized_for_streaming = True
						)
					]
					))
			else:
				thumbV = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = show['category'], large = True)
				oc.add(CreateVideoClipObject(
					url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source) + "&" + show['id'] + "&tm=" + str(show['time']).replace(" ", ""),
					title = SmoothUtils.fix_text(titleText),
					tagline = SmoothUtils.fix_text(show['description']),
					summary = "",
					thumb = thumbV
				))
		lastShow = show['time'] + show['name']

		if showCount == 100:
			Log.Info('MAX SHOWS REACHED')
			break

	return oc

###################################################################################################
@route(PREFIX + '/channels')
def ChannelsMenu(url = None):
	source = sourceType()
	Log.Debug('Channels menu: Source is ' + str(source))
	oc = ObjectContainer(title2 = "Channels")
	Log.Info(PLUGIN_VERSION + ' ChannelsMenu')
	channelsDict = Dict['channelsDict']
	channelText = ''
	currentTime = SmoothUtils.getCurrentTimeNative()
	hdOnly = Prefs['hdOnly']

	for i in range(1, 5):
		if not channelsDict is None:
			break
		Log.Info('sleeping 500ms for async schedule details to return')
		Thread.Sleep(0.5)

	for channelNum in range(1, MAX_CHAN + 1):
		if not channelsDict is None and str(channelNum) in channelsDict:
			channelItem = channelsDict[str(channelNum)]
			channelName = channelItem.name.replace("720P", "HD")
			nowPlaying = channelItem.NowPlaying()
			upcoming = channelItem.Upcoming()
			# if hdOnly == "SD only" and not(channelName.find("720p") == -1 and channelName.find("720P") == -1 and channelName.find("1080i") == -1 and channelName.find("HD") == -1):
			# 	nowPlaying = None
			# elif hdOnly == "HD only" and (channelName.find("720p") == -1 and channelName.find("720P") == -1 and channelName.find("1080i") == -1 and channelName.find("HD") == -1):
			# 	nowPlaying = None
			if not upcoming is None and len(upcoming) > 0:
				upcoming = upcoming[0]

			if nowPlaying is None:
				# if hdOnly == "SD only":
				# 	titleText = formatShowText(channelItem, nowPlaying, currentTime, "#{ch}")
				# 	category = ""
				# 	tagLine = ""
				# else:
				titleText = formatShowText(channelItem, nowPlaying, currentTime, "#{ch} {chname}")
				category = ""
				tagLine = ""
			else:
				titleText = formatShowText(channelItem, nowPlaying, currentTime, "#{ch} {chname} {title} {qual} {lang} {time} ({cat})")

				category = nowPlaying['category']
				tagLine = nowPlaying['description']

			if upcoming is None or len(upcoming) == 0:
				summaryText = ""
			else:
				summaryText = formatShowText(channelItem, upcoming, currentTime, "{when} {title} {qual} {lang} {time} ({cat})")

			thumb = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = category, large = False) #, chanFirst = True

			if Prefs['channelDetails']:
				channelUrl = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)
				oc.add(DirectoryObject(key = Callback(PlayMenu, url = channelUrl, channelNum = channelNum), title = SmoothUtils.fix_text(titleText), thumb = thumb))
			else:
				thumbV = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = category, large = True) #, chanFirst = True
				oc.add(VideoClipObject(
					key = Callback(CreateVideoClipObject,
						url = HTTPLiveStreamURL(SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)),
						title = SmoothUtils.fix_text(titleText),
						tagline = SmoothUtils.fix_text(tagLine),
						summary = SmoothUtils.fix_text(summaryText),
						thumb = thumbV,
						studio = channelName,
						quotes = "",
						container = True),
					url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source),
					title = SmoothUtils.fix_text(titleText),
					tagline = SmoothUtils.fix_text(tagLine),
					summary = SmoothUtils.fix_text(summaryText),
					studio = channelName,
					quotes = "",
					thumb = thumbV,
					items = [
						MediaObject(
							parts = [ PartObject(key = HTTPLiveStreamURL(url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)), duration = 1000) ],
							optimized_for_streaming = True
						)
					]
					))
	return oc
###################################################################################################
@route(PREFIX + '/live')
def LiveMenu(url = None):
	source = sourceType()
	oc = ObjectContainer(title2 = "Live")
	Log.Info(PLUGIN_VERSION + ' LiveMenu')
	channelsDict = Dict['channelsDict']
	showsListAll = Dict['showsList']
	currentTime = SmoothUtils.getCurrentTimeNative()

	for i in range(1, 5):
		if not channelsDict is None and not showsListAll is None:
			break
		Log.Info('sleeping 500ms for async schedule details to return')
		Thread.Sleep(0.5)

	showsList = [i for i in showsListAll if SmoothUtils.GetDateTimeNative(i['time']) <= currentTime and SmoothUtils.GetDateTimeNative(i['end_time']) >= currentTime]
	showsList.sort(key = lambda x: (x['category'], x['name'], x['quality'], x['time']))

	for i in range(0, len(showsList)):
		show = showsList[i]
		showName = None
		channelNum = str(show['channel'])
		if show['category'].lower().replace(" ", "") in ["", "tv", "generaltv"]:
			thumbText = '%02d'%int(channelNum)
			show['category'] = ""
		else:
			thumbText = show['category']
		channelItem = channelsDict[str(channelNum)]
		channelName = channelItem.name.replace("720P", "HD")
		channelText2 = channelItem.GetStatusText2()

		titleText = formatShowText(channelItem, show, currentTime, "{cat} {title} {qual} {lang} {time} {chname} #{ch}")

		artUrl = 'http://smoothstreams.tv/schedule/includes/images/uploads/8ce52ab224906731eaed8497eb1e8cb4.png'
		channelUrl = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)
		thumb = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = show['category'], large = False)

		if Prefs['channelDetails']:
			oc.add(DirectoryObject(key = Callback(PlayMenu, url = channelUrl, channelNum = channelNum), title = titleText, thumb = thumb))
		else:
			thumbV = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = show['category'], large = True)
			oc.add(VideoClipObject(
				key = Callback(CreateVideoClipObject,
					url = HTTPLiveStreamURL(SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)),
					title = SmoothUtils.fix_text(titleText),
					tagline = SmoothUtils.fix_text(show['description']),
					summary = "",
					studio = channelName,
					thumb = thumbV,
					container = True),
				url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source),
				title = SmoothUtils.fix_text(titleText),
				tagline = SmoothUtils.fix_text(show['description']),
				summary = "",
				studio = channelName,
				thumb = thumbV,
				items = [
					MediaObject(
						parts = [ PartObject(key = HTTPLiveStreamURL(url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)), duration = 1000) ],
						optimized_for_streaming = True
					)
				]
			))

	return oc
#################################################################################################
@route(PREFIX + '/categories')
def CategoriesMenu():
	source = sourceType()
	Log.Info(PLUGIN_VERSION + " CategoriesMenu")
	oc = ObjectContainer(title2 = "Categories")
	Log.Info('Categories')
	channelsDict = Dict['channelsDict']
	categoryDict = Dict['categoryDict']
	channelText = ''

	for i in range(1, 5):
		Log.Info('sleeping 500ms for async schedule details to return')
		Thread.Sleep(0.5)
		if not channelsDict is None and not categoryDict is None:
			break

	for category in sorted(categoryDict):
		thumb = SmoothUtils.GetChannelThumb(category = category, large = False)
		oc.add(DirectoryObject(key = Callback(CategoryMenu, url = category), title = category, thumb = thumb))

	return oc
#################################################################################################
@route(PREFIX + '/category')
def CategoryMenu(url = None):
	source = sourceType()
	Log.Info(PLUGIN_VERSION + " CategoryMenu " + url)
	if url is None:
		oc = ObjectContainer(title2 = "Categories")
	else:
		oc = ObjectContainer(title2 = url)
	channelsDict = Dict['channelsDict']
	categoryDict = Dict['categoryDict']
	channelText = ''
	currentTime = SmoothUtils.getCurrentTimeNative()

	for i in range(1, 5):
		if not channelsDict is None and not channelsDict is None:
			break
		Log.Info('sleeping 500ms for async schedule details to return')
		Thread.Sleep(0.5)

	# filter and sort the shows for the category by start time
	if url in categoryDict:
		showsList = sorted([i for i in categoryDict[url] if SmoothUtils.GetDateTimeNative(i['end_time']) >= currentTime], key = lambda x: (x['time'], x['name'], x['quality']))
	else:
		showsList = []

	showCount = 0
	for show in showsList:
		showCount += 1
		showName = None
		channelNum = str(show['channel'])
		thumbText = '%02d'%int(channelNum)
		channelItem = channelsDict[str(channelNum)]
		channelName = channelItem.name.replace("720P", "HD")
		titleText = formatShowText(channelItem, show, currentTime, "{when} {title} {qual} {lang} {time} {chname} #{ch}")
		artUrl = 'http://smoothstreams.tv/schedule/includes/images/uploads/8ce52ab224906731eaed8497eb1e8cb4.png'
		channelUrl = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)
		thumb = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = "", large = False)

		if Prefs['channelDetails']:
			oc.add(DirectoryObject(key = Callback(PlayMenu, url = channelUrl, channelNum = channelNum), title = titleText, tagline = SmoothUtils.fix_text(show['description']), thumb = thumb))
		elif SmoothUtils.GetDateTimeNative(show['time']) < currentTime:
			thumbV = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = "", large = True)
			oc.add(VideoClipObject(
				key = Callback(CreateVideoClipObject,
					url = HTTPLiveStreamURL(SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)),
					title = SmoothUtils.fix_text(titleText),
					tagline = SmoothUtils.fix_text(show['description']),
					summary = "",
					thumb = thumbV,
					container = True),
				url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source),
				title = SmoothUtils.fix_text(titleText),
				tagline = SmoothUtils.fix_text(show['description']),
				summary = "",
				thumb = thumbV,
				items = [
					MediaObject(
						parts = [ PartObject(key = HTTPLiveStreamURL(url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)), duration = 1000) ],
						optimized_for_streaming = True
					)
				]
				))
		else:
			thumbV = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = "", large = True)
			oc.add(CreateVideoClipObject(
				url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source) + "&" + show['id'] + "&tm=" + str(show['time']).replace(" ", ""),
				title = SmoothUtils.fix_text(titleText),
				tagline = SmoothUtils.fix_text(show['description']),
				thumb = thumbV
			))

		if showCount == 100:
			Log.Info('MAX SHOWS REACHED')
			break

	return oc
###################################################################################################
@route(PREFIX + '/channels/schedulelist')
def ScheduleListMenu(startIndex = 0):
	source = sourceType()
	pageCount = int(Prefs['pageCount'])
	endIndex = int(startIndex) + pageCount

	oc = ObjectContainer(title2 = "Schedule List")
	Log.Info(PLUGIN_VERSION + ' ScheduleListMenu %s %s %s' % (startIndex, endIndex, pageCount))
	channelsDict = Dict['channelsDict']
	showsList = Dict['showsList']
	channelText = ''

	for i in range(1, 5):
		if not channelsDict is None and not showsList is None:
			break
		Log.Info('sleeping 500ms for async schedule details to return')
		Thread.Sleep(0.5)

	parser = dateutil.parser()
	currentTime = SmoothUtils.getCurrentTimeNative()

	showsList = [i for i in showsList if SmoothUtils.GetDateTimeNative(i['end_time']) >= currentTime]
	showsList.sort(key = lambda x: (x['time'], x['name'], x['quality']))

	if endIndex > len(showsList):
		endIndex = len(showsList)

	for i in range(int(startIndex), int(endIndex)):
		show = showsList[i]
		channelSeparator = ' - '

		if SmoothUtils.GetDateTimeNative(show['end_time']) <= currentTime:
			channelSeparator = ' * '
		channelItem = None
		channelText = u''
		channelNum = str(show['channel'])
		channelUrl = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)

		if SmoothUtils.GetDateTimeNative(show['time']) > currentTime:
			channelUrl += "&" + show['id']

		if show['category'].lower().replace(" ", "") in ["", "tv", "generaltv"]:
			show['category'] = ""

		if not channelsDict is None and not channelsDict[channelNum] is None:
			channelItem = channelsDict[channelNum]
			channelName = channelItem.name.replace("720P", "HD")
			channelText = channelItem.GetStatusText()
			channelText = formatShowText(channelItem, show, currentTime, "{when} {time} #{ch} {chname} {title} {qual} {lang} ({cat})")
		else:
			channelText = '%02d {0} ' % (channelNum, channelSeparator)
			channelText = formatShowText(channelItem, show, currentTime, "")

		# CHECK PREFS for Scheduled Channel Details
		if Prefs['channelDetails']:
			thumb = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = show['category'], large = False)
			oc.add(DirectoryObject(key = Callback(PlayMenu, url = channelUrl, channelNum = channelNum), title = SmoothUtils.fix_text(channelText), tagline = SmoothUtils.fix_text(show['description']), thumb = thumb))
		else:
			thumbV = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = show['category'], large = True)
			oc.add(VideoClipObject(
				key = Callback(CreateVideoClipObject,
					url = HTTPLiveStreamURL(SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)),
					title = SmoothUtils.fix_text(channelText),
					tagline = SmoothUtils.fix_text(show['description']),
					summary = "",
					thumb = thumbV,
					container = True),
				url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source),
				title = SmoothUtils.fix_text(channelText),
				tagline = SmoothUtils.fix_text(show['description']),
				summary = "",
				thumb = thumbV,
				items = [
					MediaObject(
						parts = [ PartObject(key = HTTPLiveStreamURL(url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)), duration = 1000) ],
						optimized_for_streaming = True
					)
				]
			))

	Log.Info('endInd %s'.format(endIndex))
	endIndex = int(endIndex)
	Log.Info(' vs %s'.format(len(showsList)))

	if int(endIndex) < len(showsList):
		oc.add(NextPageObject(key = Callback(ScheduleListMenu, startIndex = int(endIndex)), title = "Next Page", thumb = 'more.png'))

	return oc
#################################################################################################
@route(PREFIX + '/channels/playmenu')
def PlayMenu(url = None, channelNum = None):
	source = sourceType()
	### This is the detailed PLAY menu after a channel has been selected which shows NOW PLAYING, and then the shows that will be on later
	Log.Info(PLUGIN_VERSION + ' PlayMenu with Url ' + url)
	oc = ObjectContainer(title1 = 'Channel ' + channelNum)
	title = channelNum
	addedItems = False
	channelsDict = Dict['channelsDict']
	currentTime = SmoothUtils.getCurrentTimeNative()

	if not channelsDict is None and not channelsDict[str(channelNum)] is None:
		channel = channelsDict[str(channelNum)]
		title = channel.name
		upcomingShows = channel.Upcoming()
		oc.title1 = title
		channelItem = channelsDict[str(channelNum)]
		channelName = channelItem.name.replace("720P", "HD")
		channelText = SmoothUtils.fix_text(channelItem.GetStatusText())
		channelText1 = SmoothUtils.fix_text(channelItem.GetStatusText1())
		channelText2 = SmoothUtils.fix_text(channelItem.GetStatusText2())
		channelText3 = SmoothUtils.fix_text(channelItem.GetStatusText3())
		if not upcomingShows is None and len(upcomingShows) > 0:
			nowPlaying = channel.NowPlaying()
			if nowPlaying is None:
					thumbV = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = "", large = True)
					oc.add(VideoClipObject(
					key = Callback(CreateVideoClipObject,
						url = HTTPLiveStreamURL(SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)),
						title = SmoothUtils.fix_text(channelText),
						thumb = thumbV,
						container = True),
					url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source),
					title = formatShowText(channelItem, None, currentTime, "{ch} {chname}"),
					thumb = thumbV,
					items = [
						MediaObject(
							parts = [ PartObject( key = HTTPLiveStreamURL(url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)), duration = 1000) ],
							optimized_for_streaming = True
						)
					]
					))
			else:
				# we only get here if we couldn't get any schedule info
				thumbV = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = nowPlaying['category'], large = True)
				oc.add(CreateVideoClipObject(
					url = HTTPLiveStreamURL(SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source)),
					title = formatShowText(channelItem, nowPlaying, currentTime, "{title} {lang} ({qual}) {time}"),
					tagline = SmoothUtils.fix_text(nowPlaying['description']),
					summary = "",
					thumb = thumbV
				))
			for show in upcomingShows:
				thumbV = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = show['category'], large = True)
				oc.add(CreateVideoClipObject(
					url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source) + "&" + show['id'],
					title = formatShowText(channelItem, show, currentTime, "{when}: {title} {lang} ({qual}) {time}"),
					tagline = SmoothUtils.fix_text(show['description']),
					summary = "",
					thumb = thumbV
				))

			addedItems = True

	if not addedItems:
		oc.title1 = title
		oc.add(CreateVideoClipObject(
				url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum, source),
				title = SmoothUtils.fix_text(('WATCH: ' + title).encode("iso-8859-1")),
				thumb = None
			))
	try:
		# add browse options for Next/Prev channel
		prevChan = int(channelNum) - 1
		if prevChan < MIN_CHAN:
			prevChan = MAX_CHAN
		channelUrl = SmoothUtils.GetFullUrlFromChannelNumber(prevChan, source)
		oc.add(DirectoryObject(key = Callback(PlayMenu, url = channelUrl, channelNum = prevChan), title = ('/\\ ' + channelsDict[str(prevChan)].GetStatusText()).encode("iso-8859-1")))

		nextChan = int(channelNum) + 1
		if nextChan > MAX_CHAN:
			nextChan = MIN_CHAN
		channelUrl = SmoothUtils.GetFullUrlFromChannelNumber(nextChan, source)
		oc.add(DirectoryObject(key = Callback(PlayMenu, url = channelUrl, channelNum = nextChan), title = ('\\/ ' + channelsDict[str(nextChan)].GetStatusText()), thumb = R(channelText2 + '.png')))
	except Exception, e:
		Log.Error('Could not add next/prev chan browse options')
		Log.Error(str(e))
		Log.Error(traceback.print_exc())

	return oc
###############################################################################################

#####https://github.com/Cigaras/IPTV.bundle/blob/master/Contents/Code/__init__.py
@route(PREFIX + '/listitems', items_dict = dict)
def ListItems(items_dict, group):
	source = sourceType()
	oc = ObjectContainer(title1 = L(group))
	items_list = []
	for i in items_dict:
		if items_dict[i]['group'] == group or group == 'All':
			items_list.append(items_dict[i])
	for item in items_list:
		# Simply adding VideoClipObject does not work on some clients (like LG SmartTV),
		# so there is an endless recursion - function CreateVideoClipObject calling itself -
		# and I have no idea why and how it works...
		oc.add(CreateVideoClipObject(
			url = item['url'],
			title = item['title'],
			thumb = item['thumb']
		))
	return oc

@route(PREFIX + '/createvideoclipobject')
def CreateVideoClipObject(url, title, thumb = None, tagline = None, summary = None, studio = None, quotes = None, container = False, art = ART, **kwargs):
	vco = VideoClipObject(
		key = Callback(CreateVideoClipObject, url = url, title = SmoothUtils.fix_text(title), summary = summary, tagline = tagline, studio = studio, quotes = quotes, thumb = thumb, art = ART, container = True),
		#rating_key = url,
		url = url,
		title = SmoothUtils.fix_text(title),
		summary = summary,
		tagline = tagline,
		studio = studio,
		quotes = quotes,
		thumb = thumb,
		items = [
			MediaObject(
				#container = Container.MP4,		# MP4, MKV, MOV, AVI
				#video_codec = VideoCodec.H264,	# H264
				#audio_codec = AudioCodec.AAC,	# ACC, MP3
				#audio_channels = 2,			# 2, 6
				parts = [ PartObject(key = GetVideoURL(url = url), duration = 1000) ],
				optimized_for_streaming = True
			)
		]
	)

	if container:
		return ObjectContainer(objects = [vco])
	else:
		return vco
	return vco

def GetVideoURL(url, live = True):
	if url.startswith('rtmp') and False:
		Log.Debug('*' * 80)
		Log.Debug('* url before processing: %s' % url)
		Log.Debug('* url after processing: %s' % RTMPVideoURL(url = url, live = live))
		Log.Debug('*' * 80)
		return RTMPVideoURL(url = url, live = live)
	elif url.startswith('mms') and False:
		return WindowsMediaVideoURL(url = url)
	else:
		return HTTPLiveStreamURL(url = url)

def GetThumb(thumb):
	if thumb and thumb.startswith('http'):
		return thumb
	elif thumb and thumb <> '':
		return R(thumb)
	else:
		return None

def GetAttribute(text, attribute, delimiter1 = '="', delimiter2 = '"'):
	x = text.find(attribute)
	if x > -1:
		y = text.find(delimiter1, x + len(attribute)) + len(delimiter1)
		z = text.find(delimiter2, y)
		if z == -1:
			z = len(text)
		return unicode(text[y:z].strip())
	else:
		return ''

def getShowText(show, currentTime):
	language = ""
	if "language" in show and show['language'].upper() != "US":
		language = ' ' + show['language'].upper()

	showText = "Ch" + show['channel'] + " " + show['name'] + " " + show['quality'] + language + " " + SmoothUtils.GetShowTimeText(show)
	if SmoothUtils.GetDateTimeNative(show['time']) > currentTime:
		return "LATER: " + showText
	else:
		return "LIVE: " + showText

def formatShowText(channel, show, currentTime, formatString):
	language = ""
	when = ""

	if " - " in channel.name:
		chanName = channel.name.split(" - ")[1]
	else:
		chanName = channel.name

	if show is None:
		retVal = formatString.replace("{ch}", channel.channel_id).replace("{chname}", chanName)
	else:
		if "language" in show and show['language'].upper() != "US":
			language = show['language'].upper()

		if "720p" in chanName.lower():
			chanName = chanName.replace(" 720P", "HD")
		showTime = SmoothUtils.GetDateTimeNative(show['time'])
		if showTime > currentTime:
			if showTime.date() == currentTime.date():
				when = "LATER"
			else:
				when = calendar.day_name[showTime.weekday()][:3].upper()

		if "category" in show and show["name"].startswith(show["category"] + ":") and show["category"] != "News":
			show["name"] = show["name"].replace(show["category"] + ":", "").strip()

		retVal = formatString.replace("{ch}", channel.channel_id).replace("{chname}", chanName).replace("{title}", show['name']).replace("{qual}", show["quality"].replace("hqlq", "").replace("unk", "")).replace("{time}", SmoothUtils.GetShowTimeText(show)).replace("{lang}", language).replace("{when}", when).replace("{cat}", show['category'])

	return retVal.replace("()", "").replace("  ", " ").strip()

def getLatestVersion():
	try:
		global PLUGIN_VERSION
		global PLUGIN_VERSION_LATEST

		# Disable version checking against original project.
		PLUGIN_VERSION =  '20170722dev' #Resource.Load("version.txt", binary = False)
		commitHash = JSON.ObjectFromURL("https://api.bitbucket.org/2.0/repositories/vorghahn/sstv-plex-plugin/commits", cacheTime = 43200)["values"][0]["hash"]
		PLUGIN_VERSION_LATEST =  '20170722dev' #str(JSON.ObjectFromURL("https://bitbucket.org/vorghahn/sstv-plex-plugin/raw/" + commitHash + "/smoothstreams2.bundle/Contents/Resources/version.txt", cacheTime = 43200))
		if PLUGIN_VERSION_LATEST > PLUGIN_VERSION:
			Log.Info("OUT OF DATE " + PLUGIN_VERSION + " < " + PLUGIN_VERSION_LATEST)
		else:
			Log.Info("UP TO DATE " + PLUGIN_VERSION + " >= " + PLUGIN_VERSION_LATEST)
	except:
		Log.Info("Version check failed")
		pass

#def processLatestVersion(response):

###################################################################################################
# Notes about xpaths
# .// means any child/grandchild of the currently selected node, rather than anywhere in the document. Particularly important when dealing with loops.
# // = any child or grand-child ( you can use // so that you don't have to specify all the parents before it). Be careful to be specific enough to avoid confusion.
# / = direct child of the parent (for example of the entire page)
