# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

class AutomaticshutdownPlugin(octoprint.plugin.TemplatePlugin,
							  octoprint.plugin.AssetPlugin,
							  octoprint.plugin.SimpleApiPlugin):

	def get_assets(self):
		return dict(js=["js/automaticshutdown.js"])

	def get_api_commands(self):
		return dict(automatic_shutdown=["value"])

	def get_template_configs(self):
		return [dict(type="sidebar",
					name="Automatic Shutdown",
					custom_bindings=True,
					icon="power-off")]

	def on_api_command(self, command, data):
		import flask
		if command == "automatic_shutdown":
			self.automatic_shutdown = data["value"]




__plugin_name__ = "Automatic Shutdown Plugin"

def __plugin_load__():
	global __plugin_implementation__
	__plugin_implementation__ = AutomaticshutdownPlugin()

