# coding=utf-8
from __future__ import absolute_import

import octoprint.plugin

class CncPlugin(octoprint.plugin.StartupPlugin,
		octoprint.plugin.TemplatePlugin,
		octoprint.plugin.SettingsPlugin):

	def on_after_startup(self):
		self._logger.info("CNC Plugin (%s)" % self._settings.get(["url"]))

	def get_settings_defaults(self):
		return dict(url="http://www.skippingrock.com")

	def get_template_configs(self):
    		return [
        		#dict(type="navbar", custom_bindings=False),
        		dict(type="settings", custom_bindings=False)
    		]


__plugin_implementations__ = [CncPlugin()]
