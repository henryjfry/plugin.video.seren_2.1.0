# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, unicode_literals

import sqlite3
import sys
from random import randint

import xbmc
import time,xbmcgui

from resources.lib.common import tools

if tools.is_stub():
    # noinspection PyUnresolvedReferences
    from mock_kodi import MOCK

from resources.lib.modules.globals import g

from resources.lib.modules.seren_version import do_version_change
from resources.lib.modules.serenMonitor import SerenMonitor
from resources.lib.modules.update_news import do_update_news
from resources.lib.modules.manual_timezone import validate_timezone_detected

g.init_globals(sys.argv)
do_version_change()

g.log("##################  STARTING SERVICE  ######################")
g.log("### {} {}".format(g.ADDON_ID, g.VERSION))
g.log("### PLATFORM: {}".format(g.PLATFORM))
g.log("### SQLite: {}".format(sqlite3.sqlite_version))  # pylint: disable=no-member
g.log("### Detected Kodi Version: {}".format(g.KODI_VERSION))
g.log("### Detected timezone: {}".format(repr(g.LOCAL_TIMEZONE.zone)))
g.log("#############  SERVICE ENTERED KEEP ALIVE  #################")


osAndroid = xbmc.getCondVisibility('system.platform.android')
if osAndroid:
	from pathlib import Path
	import shutil
	import os
	import xbmcvfs

	seren_path = str(Path(xbmcvfs.translatePath("special://home/addons/plugin.video.seren/resources/skins/Default/1080i")))
	seren_user_path = str(Path(xbmcvfs.translatePath("special://userdata/addon_data/plugin.video.seren/skins/SerenMod-Full/resources/skins/Default/1080i")))
	#seren_path = '/home/osmc/plugin.video.seren/resources/skins/Default/1080i'

	src_path = seren_path + '/Android_1080i'
	trg_path = seren_path

	if not os.path.exists(seren_path + '/android_update'):
		for src_file in Path(src_path).glob('*.*'):
			shutil.copy(os.path.join(src_path,src_file),trg_path)
			shutil.copy(os.path.join(src_path,src_file),seren_user_path)
			#os.remove(os.path.join(src_path,src_file))
		Path(seren_path + '/android_update').touch()

monitor = SerenMonitor()
try:
    xbmc.executebuiltin(
        'RunPlugin("plugin://plugin.video.seren/?action=longLifeServiceManager")'
    )

    do_update_news()
    validate_timezone_detected()
    try:
        g.clear_kodi_bookmarks()
    except TypeError:
        g.log(
            "Unable to clear bookmarks on service init. This is not a problem if it occurs immediately after install.",
            "warning"
        )

    # Disable the restoration of reuselanguageinvoker addon.xml based on settings value on upgrade.
    # It can still be toggled in settings although initially it will show user's last setting value
    # This is in preparation for removal of user setting/toggle.
    # maintenance.toggle_reuselanguageinvoker(
    #     True if g.get_setting("reuselanguageinvoker.status") == "Enabled" else False)

    g.wait_for_abort(30)  # Sleep for a half a minute to allow widget loads to complete.
    while not monitor.abortRequested():
        curr_time = time.time()
        Seren_LastUpdate = xbmcgui.Window(10000).getProperty('Next_EP.Seren_LastUpdate')
        if str(Seren_LastUpdate) == '':
            Seren_LastUpdate = 0
        if curr_time > float(Seren_LastUpdate) + 5*60 or Seren_LastUpdate == 0:
            xbmcgui.Window(10000).setProperty('Next_EP.Seren_LastUpdate', str(curr_time))
            xbmc.executebuiltin(
                'RunPlugin("plugin://plugin.video.seren/?action=runMaintenance")'
            )
            if not g.wait_for_abort(15):  # Sleep to make sure tokens refreshed during maintenance
                xbmc.executebuiltin(
                    'RunPlugin("plugin://plugin.video.seren/?action=syncTraktActivities")'
                )
            if not g.wait_for_abort(15):  # Sleep to make sure we don't possibly clobber settings
                xbmc.executebuiltin(
                    'RunPlugin("plugin://plugin.video.seren/?action=updateLocalTimezone")'
                )
            if g.wait_for_abort(60 * randint(57, 63)):
                break
finally:
    del monitor
    g.deinit()
