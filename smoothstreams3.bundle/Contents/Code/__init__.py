# -*- coding: utf-8 -*-
###################################################################################################
#
#	Smoothstreams plugin for PLEX
#	Copyright (C) 2016 Smoothstreams
#
###################################################################################################
import sys
import os, urllib, zipfile, shutil
import SmoothUtils
import SmoothAuth
import time
import calendar
import ssl
import copy
import platform
from locale_patch import L, SetAvailableLanguages
from threading import Thread
import requests

Smoothstreams_URL = 'http://www.Smoothstreams.com'
Smoothstreams_URL1 = 'http://a.video.Smoothstreams.com/'
BASE_URL = 'http://www.Smoothstreams.com/videos'

VIDEO_PREFIX = ''
NAME = 'SmoothStreamsTV'
PREFIX = '/video/' + NAME.replace(" ", "+") + 'videos'
PLUGIN_VERSION = 0.51
PLUGIN_VERSION_LATEST = 0.1
source = ''

# Changelist
# 0.51 - Tidying
# 0.5 - Autoupdate of plugin and bug fixes
# 0.47 - Autoupdate playlist fix
# 0.46 - Change thread.sleep to time.sleep, 5 min between relaod checks
# 0.45 - Force playlist reload on start
# 0.44 - Bugfix
# 0.43 - Updated FOG Urls
# 0.42 - Options adjusted, removed mystreams and worldfootball
# 0.41 - Typo in UK-Random server fixed
# 0.40 - Categories Enabled, SimpleStreams menu changed, Test menu added (update requires restart)
# 0.36 - Correction of EPG times and filters
# 0.35 - Incorporate images saved in resources to override m3u8 sourced icon
# 0.34 - Added channel numbers to standard list
# 0.33 - Change to Requests Module
# 0.32 - Change to ssl auth
# 0.31 - Addition of extra fallbacks for EPG, reenabled sportsOnly EPG
# 0.3 - First attempt at EPG fix.
# 0.2 - Addition of schedule menu items
# 0.1 - Initial

ART  = 'art-default.png'
ICON = 'Icon-Default.png'

# sports_list = ["martial sports",'nba','basketball','sports','motorsport','american football',"nfl","national football league",'ice hockey',"nhl","national hockey league",'nascar',"hockey","college football","cfb","ncaaf","rugby","fifa","uefa","epl","soccer","premier league","bundesliga","football","nba","wnba","mlb","baseball","pga",'golf',"ufc",'fight',"boxing","mma","wwe","wrestling","curling","darts","snooker","tennis/squash"]
sports_list = SmoothUtils.SportsList()
####################################################################################################

def Start():
	getLatestVersion()
	Log.Info("***{0} starting Python Version {1} TimeZone {2} PluginVersion {3} SSL Version {4}".format(NAME, sys.version, time.timezone, str(PLUGIN_VERSION),ssl.OPENSSL_VERSION))
	loginResult = SmoothAuth.login()
	SetAvailableLanguages({'en', 'fr', 'ru'})
	if Dict['SPassW'] is None:
		Log.Info('Bad login here, need to display it')
		ObjectContainer.title1 = NAME + " - Enter Login Details ->"
		ObjectContainer.art = R(ART)
	else:
		ObjectContainer.title1 = NAME
		DirectoryObject.thumb = R("Smoothstreams-network.png")
		InputDirectoryObject.thumb = R('icon-search.png')
		InputDirectoryObject.art = R('art-default.jpg')
		ObjectContainer.art = R('art-default.jpg')
		InputDirectoryObject.thumb = R('icon-search.png')
		InputDirectoryObject.art = R('art-default.jpg')
		VideoClipObject.thumb = R('icon-tv.png')
		VideoClipObject.art = R('art-default.jpg')
		Dict['playlist_loading_in_progress'] = False
		Dict['guide_loading_in_progress'] = False
		HTTP.Headers['User-agent'] = 'YAP4PLEX - %s - %s - %s' % (sys.argv[0], platform.system(), str(PLUGIN_VERSION))

####################################################################################################

def sourceType():
	#Standard default setting
	source = Prefs['sourcetype'].lower()
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
		source = 'hls'
		Log.Debug('Forcing HLS stream based on detected platform ' + str(Client.Platform))
	elif str(Client.Platform) in rtmpClients:
		source = 'rtmp'
		Log.Debug('Forcing RTMP stream based on detected platform ' + str(Client.Platform))
	else:
		Log.Debug('Using user settings for client: ' + str(Client.Platform))
		Log.Debug('Source is ' + str(source))
	if source == 'hls':
		Dict['source'] = 'https'
		Dict['port'] = 443
		Dict['sourceext'] = '/playlist.m3u8'
	else:
		Dict['source'] = 'rtmp'
		Dict['port'] = 3625
		Dict['sourceext'] = ''
	Dict.Save()
	return

###################################################################################################

@route(PREFIX + '/ValidatePrefs')
def ValidatePrefs():
	Log.Info("***{0} ValidatePrefs Python Version {1} TimeZone {2} PluginVersion {3}".format(NAME, sys.version, time.timezone, str(PLUGIN_VERSION)))
	# Do we need to reset the extentions?
	loginResult = SmoothAuth.login()
	Log.Info(repr(loginResult))

	return loginResult

#################################################################################################
@handler(PREFIX, NAME, thumb = ICON, art = ART)
def VideoMainMenu():
	Log.Info(str(PLUGIN_VERSION) + ' VideoMainMenu called: ')
	oc = ObjectContainer()
	loginResult = SmoothAuth.login()
	if PLUGIN_VERSION_LATEST > PLUGIN_VERSION:
		updateAvailable = " - plugin update available"
	else:
		updateAvailable = ""
	sourceType()
	SmoothUtils.GetServerUrlByName(Prefs["serverLocation"])


	Log.Info(Dict['last_playlist_load_datetime'])
	if SmoothUtils.update_required(Dict['last_playlist_load_datetime']):
		SmoothUtils.PlaylistReload()
		SmoothUtils.GuideReload()

	Thread(target=SmoothUtils.PlaylistReloader).start()
	Thread(target=SmoothUtils.GuideReloader).start()
	if Dict['SPassW'] is None or Prefs['serverLocation'] is None or Prefs['username'] is None or Prefs[
		'service'] is None:
		Log.Info('No password yet')
		ObjectContainer.title1 = NAME + updateAvailable + ' - Enter Login Details and Server Preferences then Refresh ->'
		oc.add(PrefsObject(title="Preferences", thumb=R("icon-prefs.png")))


	else:
		ObjectContainer.title1 = NAME + updateAvailable
		if Prefs['simple'] == 'Test':
			return test()
		elif Prefs['simple'] == 'SimpleStreams (No EPG)':
			return SimpleStreamsNoEPG()
		elif Prefs['simple'] == 'SimpleStreams':
			return ListItems()
		else:


			if not Dict['groups']:
				ReloadPlaylist()
				if not Dict['groups']:
					return ObjectContainer(
						title1=unicode(L('Error')),
						header=unicode(L('Error')),
						message=unicode(L(
							'Provided playlist files are invalid, missing or empty, check the log file for more information'))
					)

			groups = Dict['groups']
			groups_list = groups.values()

			use_groups = False
			for group in groups_list:
				if group['title'] not in [unicode('All'), unicode('No category'), unicode('SSTV')]:
					use_groups = True
					break

			if use_groups:
				groups_list.sort(key=lambda d: d['order'])
				oc = ObjectContainer(title1=unicode(L(NAME)) + updateAvailable)
				oc.add(
					DirectoryObject(
						key=Callback(ListItems, group=unicode('All')),
						title=unicode(L('All'))
					)
				)
				for group in groups_list:
					if group['title'] not in [unicode('All'), unicode('No category')]:
						thumb = GetImage(group['thumb'], default='icon-folder.png', title=group['title'])
						art = GetImage(group['art'], default='art-default.png')
						oc.add(
							DirectoryObject(
								key=Callback(ListItems, group=group['title']),
								title=group['title'],
								thumb=thumb,
								art=art
							)
						)
				if unicode('No category') in groups.keys():
					oc.add(
						DirectoryObject(
							key=Callback(ListItems, group=unicode('No category')),
							title=unicode(L('No category'))
						)
					)
			else:
				oc.add(DirectoryObject(key=Callback(ListItems), title="Channels",
				                       thumb=R('Icon-Default.png'), summary="Channel List"))




			oc.add(DirectoryObject(key = Callback(CategoriesMenu), title = "Categories", thumb = SmoothUtils.GetChannelThumb(chanName = "Categories"), summary = "Category List"))
			oc.add(DirectoryObject(key = Callback(SearchListItems, query = 'schedule'), title = "Schedule Sports", thumb = SmoothUtils.GetChannelThumb(chanName = "Schedule"), summary = "Schedule List"))
			# oc.add(DirectoryObject(key = Callback(SearchListItems, query = 'live'), title = "Live Sports", thumb = SmoothUtils.GetChannelThumb(chanName = "Live Sports"), summary = "Schedule List"))

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
					oc.add(DirectoryObject(key = Callback(SearchListItems, query = searchString), title = title, thumb = thumb))

			oc.add(InputDirectoryObject(key = Callback(ListItems), title = "Find Channel", prompt = 'Enter show title'))

			# Reload buttons
			oc.add(
				DirectoryObject(
					key=Callback(ReloadPlaylist),
					title=unicode(L('Reload playlist')),
					thumb=R('icon-reload.png')
				)
			)

			oc.add(
				DirectoryObject(
					key=Callback(ReloadGuide),
					title=unicode(L('Reload program guide')),
					thumb=R('icon-reload.png')
				)
			)
			# Preferences
			oc.add(PrefsObject(title = "Preferences", thumb = R("icon-prefs.png")))

	return oc
###################################################################################################
@route(PREFIX + '/simple')
def SimpleStreams():
	oc = ObjectContainer()
	Log.Debug('SimpleStreams menu: Source is ' + str(Dict['source']))
	#oc = ObjectContainer(title2 = "Channels")
	Log.Info(str(PLUGIN_VERSION) + ' SimpleStreams')
	channelsDict = Dict['channelsDict']
	currentTime = SmoothUtils.getCurrentTimeNative()

	for i in range(1, 5):
		if not channelsDict is None:
			break
		Log.Info('sleeping 500ms for async schedule details to return')
		Thread.Sleep(0.5)

	for channelNum in range(1, int(Prefs['numChannels']) + 1):
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

			thumbV = SmoothUtils.GetChannelThumb(chanNum = int(channelNum), chanName = channelName, category = category, large = True) #, chanFirst = True
			oc.add(
				CreateVideoClipObject(
				url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum),
				title = SmoothUtils.fix_text(titleText),
				tagline = SmoothUtils.fix_text(tagLine),
				summary = SmoothUtils.fix_text(summaryText),
				studio = channelName,
				thumb = thumbV,
				optimized_for_streaming=True,
				include_container=False #True before though...
				)
			)
			# Preferences
	oc.add(PrefsObject(title="Preferences", thumb=R("icon-prefs.png")))
	return oc

###################################################################################################
@route(PREFIX + '/simplenoepg')
def SimpleStreamsNoEPG():
	oc = ObjectContainer()
	Log.Debug('SimpleStreamsNoEPG menu: Source is ' + str(Dict['source']))
	Log.Info(str(PLUGIN_VERSION) + ' SimpleStreamsNoEPG')

	for channelNum in range(1,int(Prefs['numChannels']) + 1):
		oc.add(
			CreateVideoClipObject(
				url=SmoothUtils.GetFullUrlFromChannelNumber(channelNum),
				title="Channel %s" % str(channelNum),
				thumb='https://guide.smoothstreams.tv/assets/images/channels/150.png',
				optimized_for_streaming=True,
				include_container=False #True before though...
			)
		)
		# Preferences
	oc.add(PrefsObject(title="Preferences", thumb=R("icon-prefs.png")))
	return oc

###################################################################################################
@route(PREFIX + '/test')
def test():
	oc = ObjectContainer()
	Log.Debug('SimpleStreamsNoEPG menu: Source is ' + str(Dict['source']))
	Log.Info(str(PLUGIN_VERSION) + ' Test Streams')

	def GetVideoURL(url, live=True):
		if url.startswith('rtmp') and False:
			Log.Debug('*' * 80)
			Log.Debug('* url before processing: %s' % url)
			Log.Debug('* url after processing: %s' % RTMPVideoURL(url=url, live=live))
			Log.Debug('*' * 80)
			return RTMPVideoURL(url=url, live=live)
		elif url.startswith('mms') and False:
			return WindowsMediaVideoURL(url=url)
		else:
			return HTTPLiveStreamURL(url=url)

	@route(PREFIX + '/createvideoclipobject2')
	def CreateVideoClipObject2(url, title, thumb=None, tagline=None, summary=None, studio=None, quotes=None,
	                          container=False, art=ART, **kwargs):
		vco = VideoClipObject(
			key=Callback(CreateVideoClipObject, url=url, title=SmoothUtils.fix_text(title), summary=summary,
			             tagline=tagline, studio=studio, quotes=quotes, thumb=thumb, art=ART, container=True),
			# rating_key = url,
			url=url,
			title=SmoothUtils.fix_text(title),
			summary=summary,
			tagline=tagline,
			studio=studio,
			quotes=quotes,
			thumb=thumb,
			items=[
				MediaObject(
					container=Container.MP4,  # MP4, MKV, MOV, AVI
					bitrate=bitrate,
					video_codec=VideoCodec.H264,  # H264
					video_resolution=video_resolution,
					audio_codec=AudioCodec.AAC,  # ACC, MP3
					audio_channels=2,  # 2, 6
					parts=[PartObject(key=GetVideoURL(url=url), duration=1000)],
					optimized_for_streaming=True) for video_resolution, bitrate, version_id in
				[(1080, 5000, 'hd1080'), (720, 3000, 'hd720'), (576, 1500, 'sd1500'), (576, 1200, 'sd1200'),
				 (360, 900, 'sd900'), (360, 600, 'basic600')]
			]
		)

		if container:
			return ObjectContainer(objects=[vco])
		else:
			return vco

	for channelNum in range(1,2):
		oc.add(
			CreateVideoClipObject(
				url=SmoothUtils.GetFullUrlFromChannelNumber(channelNum),
				title="Channel %s" % str(channelNum),
				thumb='https://guide.smoothstreams.tv/assets/images/channels/150.png',
				optimized_for_streaming=True,
				include_container=False #True before though...
			)
		)
		oc.add(VideoClipObject(
			key = Callback(CreateVideoClipObject,
				url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum) + "&tm=a",
				title = str(channelNum)+'a',
				thumb = 'https://guide.smoothstreams.tv/assets/images/channels/150.png',
				container = True),
			url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum) + "&tm=a",
			title = str(channelNum)+'a',
			studio = channelNum,
			thumb = 'https://guide.smoothstreams.tv/assets/images/channels/150.png',
			items = [
				MediaObject(
					parts = [ PartObject(key = SmoothUtils.GetFullUrlFromChannelNumber(channelNum), duration = 1000) ],
					optimized_for_streaming = True
				)
			]
			))
		oc.add(VideoClipObject(
			key = Callback(CreateVideoClipObject,
				url = GetVideoURL(SmoothUtils.GetFullUrlFromChannelNumber(channelNum)) + "&tm=b",
				title = str(channelNum)+'b',
				thumb = 'https://guide.smoothstreams.tv/assets/images/channels/150.png',
				container = True),
			url = SmoothUtils.GetFullUrlFromChannelNumber(channelNum) + "&tm=b",
			title = str(channelNum)+'b',
			studio = channelNum,
			thumb = 'https://guide.smoothstreams.tv/assets/images/channels/150.png',
			items = [
				MediaObject(
					parts = [ PartObject(key = GetVideoURL(SmoothUtils.GetFullUrlFromChannelNumber(channelNum)), duration = 1000) ],
					optimized_for_streaming = True
				)
			]
			))
		oc.add(
			CreateVideoClipObject(
				url=GetVideoURL(SmoothUtils.GetFullUrlFromChannelNumber(channelNum)) + "&tm=c",
				title=str(channelNum)+'c',
				thumb='https://guide.smoothstreams.tv/assets/images/channels/150.png',
				optimized_for_streaming=True,
				include_container=False #True before though...
			)
		)
		oc.add(
			CreateVideoClipObject2(
				url=SmoothUtils.GetFullUrlFromChannelNumber(channelNum) + "&tm=d",
				title=str(channelNum)+'d',
				thumb='https://guide.smoothstreams.tv/assets/images/channels/150.png',
			)
		)
		oc.add(
			CreateVideoClipObject2(
				url=GetVideoURL(SmoothUtils.GetFullUrlFromChannelNumber(channelNum)) + "&tm=e",
				title=str(channelNum)+'e',
				thumb='https://guide.smoothstreams.tv/assets/images/channels/150.png',
			)
		)
		# Preferences
	oc.add(PrefsObject(title="Preferences", thumb=R("icon-prefs.png")))
	return oc

#################################################################################################
@route(PREFIX + '/categories')
def CategoriesMenu():
	Log.Info(str(PLUGIN_VERSION) + " CategoriesMenu")
	oc = ObjectContainer(title2 = "Categories")
	Log.Info('Categories')
	categoryDict = Dict['genres']['sports']

	for i in range(1, 5):
		if not categoryDict is None and not categoryDict is None:
			break
		Log.Info('sleeping 500ms for async schedule details to return')
		Thread.Sleep(0.5)
	Log.Info(categoryDict)
	for category in sorted(categoryDict):
		thumb = SmoothUtils.GetChannelThumb(category = category, large = False)
		oc.add(DirectoryObject(key=Callback(SearchListItems, query="genre,%s" % category), title=category, thumb=thumb))

	return oc

###############################################################################################

@route(PREFIX + '/searchlistitems')
def SearchListItems(group = unicode('All'), query = ''):
	if not Dict['streams']:
		Log.Info(Dict['streams'])
		return ObjectContainer(
					title1 = unicode(L('Error')),
					header = unicode(L('Error')),
					message = unicode(L('Provided playlist files are invalid, missing or empty, check the log file for more information'))
				)
	if not Dict['guide']:
		Log.Info(Dict['guide'])
		return ObjectContainer(
					title1 = unicode(L('Error')),
					header = unicode(L('Error')),
					message = unicode(L('Provided guide files are invalid, missing or empty, check the log file for more information'))
				)
	schedule = False
	genre = None
	if query == 'schedule':
		query = ''
		schedule = True
		oc = ObjectContainer(title1=unicode(L('Sports Schedule')))
	elif "genre," in query:

		genre = query.split(",")[1]
		query = ""
		Log.Info("Genre requested %s" % genre)
		oc = ObjectContainer(title1=unicode(L(genre)))
	else:
		oc = ObjectContainer(title1=unicode(L(query)))
	channels_list = Dict['streams'].get(group, dict()).values()
	guide = Dict['guide']

	current_datetime = Datetime.Now()

	now = []
	next = []
	later = []
	Log.Info(query)
	Log.Info(schedule)
	Log.Info(genre)


	for channel in channels_list:
		key = None
		id = channel['id']
		name = channel['name']
		title = channel['title']
		if id:
			if id in guide.keys():
				key = id
		if not key:
			channels = Dict['channels']
			if channels:
				if name:
					if name in channels.keys():
						id = channels[name]
						if id in guide.keys():
							key = id
				if not key:
					if title:
						if title in channels.keys():
							id = channels[title]
							if id in guide.keys():
								key = id
		if key:
			items_list = guide[key].values()
			if items_list:
				try:
					guide_hours = int(Prefs['guide_hours'])
				except:
					guide_hours = 8
				time_filtered_list = [program for program in items_list if
									  program['start'] <= current_datetime + Datetime.Delta(hours=guide_hours) and
									  program['stop'] > current_datetime]
				time_filtered_list.sort(key=lambda x: (x['start']))

				# if time_filtered_list[0]['genre']:
				# 	Log.Info(title)
				# 	Log.Info(time_filtered_list[0]['title'])
				# 	Log.Info(time_filtered_list[0]['genre'])
				# 	Log.Info(genre)
				for program in time_filtered_list:
					if program['title'] and (
									(schedule == True and program['genre'] and program['genre'].lower() in sports_list) or
						                         (schedule == False and genre == None and query.lower() in program['title'].lower()) or
						                         (genre and program['genre'] and program['genre'].lower() == genre.lower())
					):
						# Log.Info("Pass 1")

						new_chan = copy.deepcopy(channel)
						new_chan['title'] = program['title']
						new_chan['time'] = program['start']
						new_chan['usertime'] = program['start'].strftime('%H:%M')
						if time_filtered_list.index(program) == 0:
							new_chan['title'] = 'NOW ' +  program['title'] +  program['title'] + ' (' + channel['id'] + ')'
							now.append(new_chan)
							# Log.Info("Now")
							# Log.Info(title)
							# Log.Info(new_chan['title'])
							# Log.Info(new_chan['genre'])
							# Log.Info(genre)
						elif time_filtered_list.index(program) == 1:
							# Log.Info("Next")
							new_chan['title'] = 'NEXT ' + new_chan['usertime'] + ' (' + channel['id'] + ')'
							now.append(new_chan)
							# Log.Info(title)
							# Log.Info(new_chan['title'])
							# Log.Info(new_chan['genre'])
							# Log.Info(genre)
						else:
							# Log.Info("Later")
							when = ''
							if program['start'].date() == current_datetime.date():
								when = "LATER"
							else:
								when = calendar.day_name[program['start'].weekday()][:3].upper()
							new_chan['title'] = when + " " + new_chan['usertime'] + ' ' + program['title'] + ' (' + channel['id'] + ')'
							now.append(new_chan)
							# Log.Info(title)
							# Log.Info(new_chan['title'])
							# Log.Info(new_chan['genre'])
							# Log.Info(genre)
	now.sort(key = lambda x: (x['time']))

	count = 0
	for item in now:
		count+=1
		oc.add(
			CreateVideoClipObject(
				url=item['url'] + "&tm=" + str(item['time']).replace(" ", ""),
				title=item['title'],
				thumb=GetImage(item['thumb'], default='icon-tv.png', id=item['id'], name=item['name'],
							   title=item['title']),
				art=GetImage(item['art'], default='art-default.jpg'),
				summary=GetSummary(item['id'], item['name'], item['title'], unicode(L('No description available'))),
				c_audio_codec=item['audio_codec'] if item['audio_codec'] else None,
				c_video_codec=item['video_codec'] if item['video_codec'] else None,
				c_container=item['container'] if item['container'] else None,
				c_protocol=item['protocol'] if item['protocol'] else None,
				optimized_for_streaming=item['optimized_for_streaming'] in ['y', 'yes', 't', 'true', 'on', '1'] if
				item['optimized_for_streaming'] else 'No',
				include_container=False
			)
		)
	# next.sort(key=lambda x: (x['time']))
	# for item in next:
	# 	count += 1
	# 	oc.add(
	# 		CreateVideoClipObject(
	# 			url=item['url'] + "&tm=" + str(item['time']).replace(" ", ""),
	# 			title=item['title'],
	# 			thumb=GetImage(item['thumb'], default='icon-tv.png', id=item['id'], name=item['name'],
	# 			               title=item['title']),
	# 			art=GetImage(item['art'], default='art-default.jpg'),
	# 			summary=GetSummary(item['id'], item['name'], item['title'], unicode(L('No description available'))),
	# 			c_audio_codec=item['audio_codec'] if item['audio_codec'] else None,
	# 			c_video_codec=item['video_codec'] if item['video_codec'] else None,
	# 			c_container=item['container'] if item['container'] else None,
	# 			c_protocol=item['protocol'] if item['protocol'] else None,
	# 			optimized_for_streaming=item['optimized_for_streaming'] in ['y', 'yes', 't', 'true', 'on', '1'] if
	# 			item['optimized_for_streaming'] else 'No',
	# 			include_container=False
	# 		)
	# 	)
	# later.sort(key=lambda x: (x['time']))
	# for item in later:
	# 	new_chan['time'] = program['start'].strftime('%H:%M')
	# 	count += 1
	# 	oc.add(
	# 		CreateVideoClipObject(
	# 			url=item['url'] + "&tm=" + str(item['time']).replace(" ", ""),
	# 			title=item['title'],
	# 			thumb=GetImage(item['thumb'], default='icon-tv.png', id=item['id'], name=item['name'],
	# 			               title=item['title']),
	# 			art=GetImage(item['art'], default='art-default.jpg'),
	# 			summary=GetSummary(item['id'], item['name'], item['title'], unicode(L('No description available'))),
	# 			c_audio_codec=item['audio_codec'] if item['audio_codec'] else None,
	# 			c_video_codec=item['video_codec'] if item['video_codec'] else None,
	# 			c_container=item['container'] if item['container'] else None,
	# 			c_protocol=item['protocol'] if item['protocol'] else None,
	# 			optimized_for_streaming=item['optimized_for_streaming'] in ['y', 'yes', 't', 'true', 'on', '1'] if
	# 			item['optimized_for_streaming'] else 'No',
	# 			include_container=False
	# 		)
	# 	)

	return oc

###############################################################################################

#####https://github.com/Cigaras/IPTV.bundle/blob/master/Contents/Code/__init__.py
@route(PREFIX + '/listitems', page = int)
def ListItems(group = unicode('All'), query = '', page = 1):

	if not Dict['streams']:
		Log.Info(Dict['streams'])
		return ObjectContainer(
					title1 = unicode(L('Error')),
					header = unicode(L('Error')),
					message = unicode(L('Provided playlist files are invalid, missing or empty, check the log file for more information'))
				)

	group = unicode(group) # Plex loses unicode formating when passing string between @route procedures if string is not a part of a @route

	items_list = Dict['streams'].get(group, dict()).values()
	Log.Info("List items started")


	# Filter
	if query:
		items_list = filter(lambda d: query.lower() in d['title'].lower(), items_list)

	# Sort
	# if Prefs['sort_lists']:
	# 	# Natural sort (http://stackoverflow.com/a/16090640)
	# 	items_list.sort(key = lambda d: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', d['title'].lower())])
	# else:
	items_list.sort(key = lambda d: d['order'])

	# Number of items per page
	try:
		items_per_page = int(Prefs['pageCount'])
	except:
		items_per_page = 40

	items_list_range = items_list[page * items_per_page - items_per_page : page * items_per_page]

	oc = ObjectContainer(title1 = unicode(L('Search')) if query else group)

	for item in items_list_range:
		oc.add(
			CreateVideoClipObject(
				url = item['url'],
				title = str(item['order']) + " " + item['title'],
				# Change to using icons form resources, backup is urls.
				#thumb = GetImage(item['thumb'], default = 'icon-tv.png', id = item['id'], name = item['name'], title = item['title']),
				thumb = SmoothUtils.GetChannelThumb(chanNum = item['order'], chanName = item['title'], category = "", large = False, fallBack = GetImage(item['thumb'], default = 'icon-tv.png', id = item['id'], name = item['name'], title = item['title'])),
				art = GetImage(item['art'], default = 'art-default.jpg'),
				summary = GetSummary(item['id'], item['name'], item['title'], unicode(L('No description available'))),
				c_audio_codec = item['audio_codec'] if item['audio_codec'] else None,
				c_video_codec = item['video_codec'] if item['video_codec'] else None,
				c_container = item['container'] if item['container'] else None,
				c_protocol = item['protocol'] if item['protocol'] else None,
				optimized_for_streaming = item['optimized_for_streaming'] in ['y', 'yes', 't', 'true', 'on', '1'] if item['optimized_for_streaming'] else 'No',
				include_container = False
			)
		)

	if len(items_list) > page * items_per_page:
		oc.add(
			NextPageObject(
				key = Callback(ListItems, group = group, query = query, page = page + 1),
				thumb = R('icon-next.png')
			)
		)

	if len(oc) > 0:
		return oc
	else:
		return ObjectContainer(
					title1 = unicode(L('Search')),
					header = unicode(L('Search')),
					message = unicode(L('No items were found'))
				)


####################################################################################################
@route(PREFIX + '/createvideoclipobject', include_container = bool)
def CreateVideoClipObject(url, title, thumb, art = None, summary = None,
						  c_audio_codec = None, c_video_codec = None,
						  c_container = None, c_protocol = None,
						  optimized_for_streaming = True,
						  include_container = False, *args, **kwargs):

	vco = VideoClipObject(
		key = Callback(CreateVideoClipObject,
					   url = url, title = SmoothUtils.fix_text(title), thumb = thumb, art = art, summary = summary,
					   c_audio_codec = c_audio_codec, c_video_codec = c_video_codec,
					   c_container = c_container, c_protocol = c_protocol,
					   optimized_for_streaming = optimized_for_streaming,
					   include_container = True),
		rating_key = url,
		title = SmoothUtils.fix_text(title),
		thumb = thumb,
		art = art,
		summary = summary,
		items = [
			MediaObject(
				parts = [
					PartObject(
						key = GetVideoURL(Callback(PlayVideo, url = url))
					)
				],
				audio_codec = c_audio_codec,
				video_codec = c_video_codec,
				container = c_container,
				protocol = c_protocol,
				optimized_for_streaming = optimized_for_streaming
			)
		]
	)

	if include_container:
		return ObjectContainer(objects = [vco])
	else:
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

####################################################################################################
def GetImage(file_name, default, id='', name='', title=''):
	images_path = ''
	if not file_name and title:
		file_name = title + '.png'

	if file_name:
		if file_name.startswith('http'):
			return Resource.ContentsOfURLWithFallback(file_name.replace(' ', '%20'), fallback=R(default))
		elif images_path:
			path = images_path
			if path.startswith('http'):
				file_name = path + file_name if path.endswith('/') else path + '/' + file_name
				return Resource.ContentsOfURLWithFallback(file_name.replace(' ', '%20'), fallback=R(default))
			else:
				if '/' in path and not '\\' in path:
					# must be unix system, might not work
					file_name = path + file_name if path.endswith('/') else path + '/' + file_name
				elif '\\' in path and not '/' in path:
					file_name = path + file_name if path.endswith('\\') else path + '\\' + file_name
		r = R(file_name)
		if r:
			return r

	icons = Dict['icons']
	if icons and (id or name or title):
		key = None
		if id:
			if id in icons.keys():
				key = id
		if not key:
			channels = Dict['channels']
			if channels:
				if name:
					if name in channels.keys():
						id = channels[name]
						if id in icons.keys():
							key = id
				if not key:
					if title:
						if title in channels.keys():
							id = channels[title]
							if id in icons.keys():
								key = id
		if key:
			file_name = icons[key]
			if file_name.startswith('http'):
				return Resource.ContentsOfURLWithFallback(file_name.replace(' ', '%20'), fallback=R(default))

	return R(default)

####################################################################################################
def GetSummary(id, name, title, default=''):

	summary = ''
	guide = Dict['guide']

	if guide:
		key = None
		if id:
			if id in guide.keys():
				key = id
		if not key:
			channels = Dict['channels']
			if channels:
				if name:
					if name in channels.keys():
						id = channels[name]
						if id in guide.keys():
							key = id
				if not key:
					if title:
						if title in channels.keys():
							id = channels[title]
							if id in guide.keys():
								key = id
		if key:
			items_list = guide[key].values()

			if items_list:
				current_datetime = Datetime.Now()
				try:
					guide_hours = int(Prefs['guide_hours'])
				except:
					guide_hours = 8
				items_list.sort(key=lambda x: (x['start']))
				for item in items_list:
					if item['start'] <= current_datetime + Datetime.Delta(hours=guide_hours) and item[
						'stop'] > current_datetime:
						if summary:
							summary = summary + '\n' + item['start'].strftime('%H:%M') + ' ' + item['title']
						else:
							summary = item['start'].strftime('%H:%M') + ' ' + item['title']
						if item['desc']:
							summary = summary + ' - ' + item['desc']

	if summary:
		return summary
	else:
		return default

####################################################################################################
@indirect
@route(PREFIX + '/playvideo.m3u8')
def PlayVideo(url):
	Log.Info("Playing: " + url)
	# Custom User-Agent string
	# if Prefs['user_agent']:
	# 	HTTP.Headers['User-Agent'] = Prefs['user_agent']
	if '|' in url:
		url = url.split('|')[0]
	Log.Info("Now Playing: " + url)

	return IndirectResponse(VideoClipObject, key = url)


# def GetThumb(thumb):
# 	if thumb and thumb.startswith('http'):
# 		return thumb
# 	elif thumb and thumb <> '':
# 		return R(thumb)
# 	else:
# 		return None
#
# def GetAttribute(text, attribute, delimiter1 = '="', delimiter2 = '"'):
# 	x = text.find(attribute)
# 	if x > -1:
# 		y = text.find(delimiter1, x + len(attribute)) + len(delimiter1)
# 		z = text.find(delimiter2, y)
# 		if z == -1:
# 			z = len(text)
# 		return unicode(text[y:z].strip())
# 	else:
# 		return ''
#
# def getShowText(show, currentTime):
# 	language = ""
# 	if "language" in show and show['language'].upper() != "US":
# 		language = ' ' + show['language'].upper()
#
# 	showText = "Ch" + show['channel'] + " " + show['name'] + " " + show['quality'] + language + " " + SmoothUtils.GetShowTimeText(show)
# 	if SmoothUtils.utc_to_local(show['time']) > currentTime:
# 		return "LATER: " + showText
# 	else:
# 		return "LIVE: " + showText

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
		showTime = show['time']
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
	Log.Info("Checking plugin version is up to date %s" % str(PLUGIN_VERSION))
	try:
		global PLUGIN_VERSION
		global PLUGIN_VERSION_LATEST
		vers_url = "https://raw.githubusercontent.com/vorghahn/SSTV-PLEX-PLUGIN/master/smoothstreams3.bundle/Contents/version.txt"
		# Disable version checking against original project.
		PLUGIN_VERSION_LATEST = float(JSON.ObjectFromURL(vers_url, encoding = 'utf-8')['Version'])

		if PLUGIN_VERSION_LATEST > PLUGIN_VERSION:
			Log.Info("OUT OF DATE " + str(PLUGIN_VERSION) + " < " + str(PLUGIN_VERSION_LATEST))
			processLatestVersion()
		else:
			Log.Info("UP TO DATE " + str(PLUGIN_VERSION) + " >= " + str(PLUGIN_VERSION_LATEST))
	except:
		Log.Info("Version check failed")
		pass


def copytree(src, dst, symlinks=False, ignore=["Info.plist","DefaultPrefs.json"]):
	if not os.path.exists(dst):
		os.makedirs(dst)
	for item in os.listdir(src):
		s = os.path.join(src, item)
		d = os.path.join(dst, item)
		if os.path.isdir(s):
			copytree(s, d, symlinks, ignore=ignore)
		else:
			if not os.path.exists(d) or os.stat(s).st_mtime - os.stat(d).st_mtime > 1:
				shutil.copy2(s, d)

def processLatestVersion():
	Log.Info("Updating Plugin")
	cwd = os.getcwd()
	pluginPath = os.path.abspath(os.path.join(cwd, "../../..", "Plug-ins","smoothstreams3.bundle"))
	testPath = os.path.abspath(os.path.join(pluginPath,"TEST_Contents"))
	tempPath = os.path.abspath(os.path.join(pluginPath,"temp"))
	zipped = "https://github.com/vorghahn/SSTV-PLEX-PLUGIN/archive/master.zip"
	update_zip = os.path.join(pluginPath, "update.zip")
	urllib.urlretrieve(zipped, update_zip)

	with zipfile.ZipFile(update_zip, "r") as z:
		z.extractall(tempPath)

	copytree(os.path.join(tempPath, "SSTV-PLEX-PLUGIN-master", "smoothstreams3.bundle", "Contents"), os.path.join(pluginPath,"Contents"))
	shutil.rmtree(tempPath, ignore_errors=True)
	os.remove(os.path.join(pluginPath, "update.zip"))




####################################################################################################
@route(PREFIX + '/reloadplaylist')
def ReloadPlaylist():

	if Dict['playlist_loading_in_progress']:
		return ObjectContainer(
					title1 = unicode(L('Warning')),
					header = unicode(L('Warning')),
					message = unicode(L('Playlist is reloading in the background, please wait'))
				)

	SmoothUtils.PlaylistReload()

	if Dict['groups']:
		return ObjectContainer(
					title1 = unicode(L('Success')),
					header = unicode(L('Success')),
					message = unicode(L('Playlist reloaded successfully'))
				)
	else:
		return ObjectContainer(
					title1 = unicode(L('Error')),
					header = unicode(L('Error')),
					message = unicode(L('Provided playlist files are invalid, missing or empty, check the log file for more information'))
				)

####################################################################################################
@route(PREFIX + '/reloadguide')
def ReloadGuide():

	if Dict['guide_loading_in_progress']:
		return ObjectContainer(
					title1 = unicode(L('Warning')),
					header = unicode(L('Warning')),
					message = unicode(L('Program guide is reloading in the background, please wait'))
				)

	SmoothUtils.GuideReload()

	if Dict['guide']:
		return ObjectContainer(
					title1 = unicode(L('Success')),
					header = unicode(L('Success')),
					message = unicode(L('Program guide reloaded successfully'))
				)
	else:
		return ObjectContainer(
					title1 = unicode(L('Error')),
					header = unicode(L('Error')),
					message = unicode(L('Provided program guide files are invalid, missing or empty, check the log file for more information'))
)

###################################################################################################
# Notes about xpaths
# .// means any child/grandchild of the currently selected node, rather than anywhere in the document. Particularly important when dealing with loops.
# // = any child or grand-child ( you can use // so that you don't have to specify all the parents before it). Be careful to be specific enough to avoid confusion.
# / = direct child of the parent (for example of the entire page)
