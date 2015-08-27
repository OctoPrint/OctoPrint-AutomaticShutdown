# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin
from octoprint.util import RepeatedTimer

class AutomaticshutdownPlugin(octoprint.plugin.TemplatePlugin,
							  octoprint.plugin.AssetPlugin,
							  octoprint.plugin.SimpleApiPlugin,
							  octoprint.plugin.EventHandlerPlugin,
							  octoprint.plugin.SettingsPlugin,
							  octoprint.plugin.StartupPlugin):

	def on_after_startup(self):
		self.automatic_shutdown_enabled = False

	def get_assets(self):
		return dict(js=["js/automaticshutdown.js"])

	def get_template_configs(self):
		return [dict(type="sidebar",
					name="Automatic Shutdown",
					custom_bindings=False,
					icon="power-off")]

	def get_api_commands(self):
		return dict(automatic_shutdown=["value"],
					abort_shutdown=["value"])

	def on_api_command(self, command, data):
		import flask
		if command == "automatic_shutdown":
			self.automatic_shutdown_enabled = data["value"]
		elif command == "abort_shutdown":
			self._timer.finish()
			if data["value"]:
				self._logger.info("Shutdown aborted.")

	def on_event(self, event, payload):
		if event == "PrintDone":
			if self.automatic_shutdown_enabled and self._settings.global_get(["server", "commands", "systemShutdownCommand"]) and not hasattr(self, "timer"):
				self.timeout_value = 10
				self._timer = RepeatedTimer(1, self._timer_task)
				self._timer.start()
				self._plugin_manager.send_plugin_message(self._identifier, dict(type="timeout", timeout_value=self.timeout_value))

	def _timer_task(self):
		self.timeout_value -= 1
		self._plugin_manager.send_plugin_message(self._identifier, dict(type="timeout", timeout_value=self.timeout_value))
		if self.timeout_value <= 0:
			self._timer.finish()
			del(self._timer)
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

