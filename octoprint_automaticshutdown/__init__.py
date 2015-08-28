# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
from octoprint.util import RepeatedTimer
from octoprint.events import Events

class AutomaticshutdownPlugin(octoprint.plugin.TemplatePlugin,
							  octoprint.plugin.AssetPlugin,
							  octoprint.plugin.SimpleApiPlugin,
							  octoprint.plugin.EventHandlerPlugin,
							  octoprint.plugin.SettingsPlugin,
							  octoprint.plugin.StartupPlugin):

	def __init__(self):
		self._automatic_shutdown_enabled = False
		self._timeout_value = None
		self._timer = None

	def get_assets(self):
		return dict(js=["js/automaticshutdown.js"])

	def get_template_configs(self):
		return [dict(type="sidebar",
			name="Automatic Shutdown",
			custom_bindings=False,
			icon="power-off")]

	def get_api_commands(self):
		return dict(enable=[],
			disable=[],
			abort=[])

	def on_api_command(self, command, data):
		import flask
		if command == "enable":
			self._automatic_shutdown_enabled = True
		elif command == "disable":
			self._automatic_shutdown_enabled = False
		elif command == "abort":
			self._timer.cancel()
			self._logger.info("Shutdown aborted.")

	def on_event(self, event, payload):
		if event != Events.PRINT_DONE:
			return
		if not self._automatic_shutdown_enabled or not self._settings.global_get(["server", "commands", "systemShutdownCommand"]):
			return
		if self._timer is not None:
			return

		self._timeout_value = 10
		self._timer = RepeatedTimer(1, self._timer_task)
		self._timer.start()
		self._plugin_manager.send_plugin_message(self._identifier, dict(type="timeout", timeout_value=self._timeout_value))

	def _timer_task(self):
		self._timeout_value -= 1
		self._plugin_manager.send_plugin_message(self._identifier, dict(type="timeout", timeout_value=self._timeout_value))
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


__plugin_name__ = "Automatic Shutdown"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = AutomaticshutdownPlugin()

