# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
from octoprint.server import user_permission
from octoprint.util import RepeatedTimer
from octoprint.events import eventManager, Events
import time

class AutomaticshutdownPlugin(octoprint.plugin.TemplatePlugin,
							  octoprint.plugin.AssetPlugin,
							  octoprint.plugin.SimpleApiPlugin,
							  octoprint.plugin.EventHandlerPlugin,
							  octoprint.plugin.SettingsPlugin,
							  octoprint.plugin.StartupPlugin):

	def __init__(self):
                self.abortTimeout = 0
                self.rememberCheckBox = False
                self.lastCheckBoxValue = False
		self._automatic_shutdown_enabled = False
		self._timeout_value = None
		self._timer = None
                self._renderingQueue = []

        def initialize(self):
                self.abortTimeout = self._settings.get_int(["abortTimeout"])
                self._logger.debug("abortTimeout: %s" % self.abortTimeout)

                self.rememberCheckBox = self._settings.get_boolean(["rememberCheckBox"])
                self._logger.debug("rememberCheckBox: %s" % self.rememberCheckBox)

                self.lastCheckBoxValue = self._settings.get_boolean(["lastCheckBoxValue"])
                self._logger.debug("lastCheckBoxValue: %s" % self.lastCheckBoxValue)
                if self.rememberCheckBox:
                        self._automatic_shutdown_enabled = self.lastCheckBoxValue
                
	def get_assets(self):
		return dict(js=["js/automaticshutdown.js"])

	def get_template_configs(self):
		return [dict(type="sidebar",
			name="Automatic Shutdown",
			custom_bindings=False,
			icon="power-off"),
                        dict(type="settings", custom_bindings=False)]
            

	def get_api_commands(self):
		return dict(enable=[],
			disable=[],
			abort=[])

	def on_api_command(self, command, data):
                if not user_permission.can():
                        return make_response("Insufficient rights", 403)

		if command == "enable":
			self._automatic_shutdown_enabled = True
		elif command == "disable":
			self._automatic_shutdown_enabled = False
		elif command == "abort":
			if self._timer is not None:
				self._timer.cancel()
				self._timer = None
			self._timeout_value = None
			self._logger.info("Shutdown aborted.")
                
                if command == "enable" or command == "disable":
                        self.lastCheckBoxValue = self._automatic_shutdown_enabled
                        if self.rememberCheckBox:
                                self._settings.set_boolean(["lastCheckBoxValue"], self.lastCheckBoxValue)
                                self._settings.save()
                                eventManager().fire(Events.SETTINGS_UPDATED)
                        
                self._plugin_manager.send_plugin_message(self._identifier, dict(automaticShutdownEnabled=self._automatic_shutdown_enabled, type="timeout", timeout_value=self._timeout_value))

	def on_event(self, event, payload):
		if event == Events.CLIENT_OPENED:
			self._plugin_manager.send_plugin_message(self._identifier, dict(automaticShutdownEnabled=self._automatic_shutdown_enabled, type="timeout", timeout_value=self._timeout_value))
			return
                
		if event == Events.MOVIE_RENDERING:
			self._logger.debug("Adding %s to the rendering queue." % payload["movie_basename"])
			self._renderingQueue.append(payload["movie_basename"])
			return
                
		if event in [Events.MOVIE_DONE, Events.MOVIE_FAILED]:
			self._logger.debug("Removing %s from the rendering queue." % payload["movie_basename"])
			try:
				self._renderingQueue.remove(payload["movie_basename"])
			except ValueError:
				pass
                
		if not self._automatic_shutdown_enabled:
                        return
                
                if not self._settings.global_get(["server", "commands", "systemShutdownCommand"]):
                        self._logger.warning("systemShutdownCommand is not defined. Aborting shutdown...")
 			return
                
		if event not in [Events.PRINT_DONE, Events.MOVIE_DONE, Events.MOVIE_FAILED]:
			return

                if self._printer.is_printing() or self._printer.is_paused():
                        self._logger.info("Printer is currently printing/paused. No shutdown action will be preformed.")
                        return

                if (len(self._renderingQueue) > 0):
                        self._logger.info("Waiting for %s timelapse(s) to finish rendering before starting shutdown timer..." % len(self._renderingQueue))
                        return

		if event in [Events.MOVIE_DONE, Events.MOVIE_FAILED]:
			self._timer_start()
			return
                
		if event == Events.PRINT_DONE:
			webcam_config = self._settings.global_get(["webcam", "timelapse"], merged=True)
			timelapse_type = webcam_config["type"]
			if (timelapse_type is not None and timelapse_type != "off"):
				return
                        else:
				self._timer_start()
				return

	def _timer_start(self):
		if self._timer is not None:
			return
                
                self._logger.info("Starting abort shutdown timer.")
		
		self._timeout_value = self.abortTimeout
		self._timer = RepeatedTimer(1, self._timer_task)
		self._timer.start()

	def _timer_task(self):
		if self._timeout_value is None:
			return

		self._timeout_value -= 1
		self._plugin_manager.send_plugin_message(self._identifier, dict(automaticShutdownEnabled=self._automatic_shutdown_enabled, type="timeout", timeout_value=self._timeout_value))
		if self._timeout_value <= 0:
			self._timer.cancel()
			self._timer = None
			self._shutdown_system()

	def _shutdown_system(self):
		shutdown_command = self._settings.global_get(["server", "commands", "systemShutdownCommand"])
		self._logger.info("Shutting down system with command: {command}".format(command=shutdown_command))
		try:
			import sarge
			p = sarge.run(shutdown_command, async=True)
		except Exception as e:
			self._logger.exception("Error when shutting down: {error}".format(error=e))
			return

        def get_settings_defaults(self):
                return dict(
                        abortTimeout = 30,
                        rememberCheckBox = False,
                        lastCheckBoxValue = False
                )

        def on_settings_save(self, data):
                octoprint.plugin.SettingsPlugin.on_settings_save(self, data)
        
                self.abortTimeout = self._settings.get_int(["abortTimeout"])
                self.rememberCheckBox = self._settings.get_boolean(["rememberCheckBox"])
                self.lastCheckBoxValue = self._settings.get_boolean(["lastCheckBoxValue"])

        def get_update_information(self):
                return dict(
                        automaticshutdown=dict(
                        displayName="Automatic Shutdown",
                        displayVersion=self._plugin_version,

                        # version check: github repository
                        type="github_release",
                        user="OctoPrint",
                        repo="OctoPrint-AutomaticShutdown",
                        current=self._plugin_version,

                        # update method: pip w/ dependency links
                        pip="https://github.com/OctoPrint/OctoPrint-AutomaticShutdown/archive/{target_version}.zip"
                )
        )

__plugin_name__ = "Automatic Shutdown"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = AutomaticshutdownPlugin()

	global __plugin_hooks__
	__plugin_hooks__ = {
		"octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.get_update_information
	}
