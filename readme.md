# Plex Plugin for SmoothStreamsTV

## About

Forked from https://bitbucket.org/stankness/sstv-plex-plugin/overview on 25 MAR 2017
Rewritten based of Cigaras IPTV Bundle in DEC 2017

This is a Plex plugin to access your SmoothStreamsTV account.

## Installation

- Unzip the downloaded file and place the smoothstreams3.bundle folder in the correct location for your Plex Media Server platform � see here for details: https://support.plex.tv/hc/en-us/articles/201106098-How-do-Ifind-the-Plug-Ins-folder-
- Using a web browser open Plex Web (http://PLEXSEVERIP:32400/web/index.html) and select Channels
- SmoothstreamsTV should be in the Channels list now. Hover over the Smoothstreams channel and click on the cog to configure.
- You should then be able to open the Smoothstreams channel and start watching the streams

## Options
Set your username, password and service according to your provider.

### Simple
Useful for faultfinding or for a simpler interface.
- No: Normal mode
- Yes: Channels only mode
- Yes (no EPG): Channels only mode with zero epg data
- Test: Has 6 different methods for launching channel 1 to help identify client issues.

### My Search
This is an area where you can setup custom entries for the plugin's home page. This will do a search based on the terms. You can use any strings to match the title, description or category in the guide. Items are separated by a semicolon (;) so that you can make multiple entries.

#### Example
```
US Sports:NFL NHL NBA Baseball;Devils:"New Jersey Devils";NBA;NFL
```

Would make six entries.

- All shows in the NHL category and any other shows with the term 'NHL' in the title or description. This will get a custom title of 'LiveNHL'
- All shows in the NFL category and shows with the term 'NFL' in the title or description
- All shows matching the words: NFL NHL NBA and Baseball with a custom title of 'US Sports'
- All shows matching the exact string "New Jersey Devils". This will get a custom title of 'Devils'

### HLS or RTMP
Selection of video stream type. HLS is smoother but has a 15 sec delay compared to RTMP. If your client is only able to accept one type then you can enter it into the lists below. For a list of the correct terms to use refer client-platform in: https://forums.plex.tv/discussion/190573/list-of-current-client-product-and-client-platform

### Stream Quality (Select channels only)
Selection of Either Low Quality, High Quality or High Definition video streams

### Number of Channels that carry multiple qualities
Set to 60 as currently only 60 channels respond to the above stream quality selections.

### Sports Only?
- On: Use the default, official guide which only shows live sporting events.
- Off: Use the extended guide (thanks fog) which shows content for all channels. This will make the plugin slower because of the larger guide information.

## Updates
From version 0.5 the plugin will autoupdate, if this happens you may notice the plugin being slow or refreshing.

## Uninstall
- Delete the smoothstreams2.bundle folder from your plugins folder location - https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-thePlug-Ins-folder-
- Delete com.plexapp.plugins.smoothstreams3 - use this link to find the location depending on platform- https://support.plex.tv/hc/enus/articles/202967376-Clearing-Plugin-Channel-Agent-HTTP-Caches
- Delete com.plexapp.plugins.smoothstreams3 from the Data folder. Use the above link and change Caches for Data on the end of the string to find the location. Change %LOCALAPPDATA%\Plex Media Server\Plug-in Support\Caches\ to %LOCALAPPDATA%\Plex Media Server\Plug-in Support\Data

## Issues
Report issues preferably on SSTV forums. If possible share the most recent log file from PLEXHOMEDIR/Logs/PMS Plugins Logs/com.plexapp.plugins.smoothstreamstv.log

## Troubleshooting

Issue: "Not enough bandwidth for any playback of this item. Cannot convert to below minimum bandwidth of 77kbps"
Possible Causes: Upload limit set on server. Remote/Internet Quality not set to 'Original' on Client. Exhibited on PMS versions since ~Jun 2017.

Issue: Streams stop every XX minutes.
Possible Cause: Regional Server issues, try a different one.
