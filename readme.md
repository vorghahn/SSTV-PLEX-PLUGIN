# Plex Plugin for SmoothStreamsTV (DEV ONLY)

## About

Forked from https://bitbucket.org/stankness/sstv-plex-plugin/overview on 25 MAR 2017

This is a Plex plugin to access your SmoothStreamsTV account.

## Installation

- Unzip the downloaded file and place the smoothstreams2.bundle folder in the correct location for your Plex Media Server platform – see here for details: https://support.plex.tv/hc/en-us/articles/201106098-How-do-Ifind-the-Plug-Ins-folder-
- Using a web browser open Plex Web (http://PLEXSEVERIP:32400/web/index.html) and select Channels
- Smoothstreams should be in the Channels list now. Hover over the Smoothstreams channel and click on the cog to configure.
- You should then be able to open the Smoothstreams channel and start watching the streams


## Uninstall
- Delete the smoothstreams2.bundle folder from your plugins folder location - https://support.plex.tv/hc/en-us/articles/201106098-How-do-I-find-thePlug-Ins-folder-
- Delete com.plexapp.plugins.smoothstreams2 - use this link to find the location depending on platform- https://support.plex.tv/hc/enus/articles/202967376-Clearing-Plugin-Channel-Agent-HTTP-Caches
- Delete com.plexapp.plugins.smoothstreams2 from the Data folder. Use the above link and change Caches for Data on the end of the string to find the location. Change %LOCALAPPDATA%\Plex Media Server\Plug-in Support\Caches\ to %LOCALAPPDATA%\Plex Media Server\Plug-in Support\Data

