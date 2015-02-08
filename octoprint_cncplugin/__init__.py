# coding=utf-8
from __future__ import absolute_import


import octoprint.plugin
import octoprint.printer
import octoprint.util
import re

from octoprint.events import eventManager, Events
import octoprint.settings


# singleton
_instance = None
class CncPlugin(
                octoprint.plugin.StartupPlugin,
                octoprint.plugin.TemplatePlugin,
                octoprint.plugin.SettingsPlugin,
                octoprint.plugin.AssetPlugin,
                octoprint.plugin.Plugin,
                ):
    __instance = None

    def __new__(cls):
        if CncPlugin.__instance is None:
            CncPlugin.__instance = object.__new__(cls)
            CncPlugin.__instance._isGrbl = None
            CncPlugin.__instance._needPosUpdate = True
            CncPlugin.__instance._lastPos = dict(MPos='',WPos='')
            CncPlugin.__instance._isCommsInitializing = None
        return CncPlugin.__instance

    def isInitialized(self):
        return self._printer is not None

    def initialize(self):
        eventManager().subscribe(Events.PRINT_STARTED, self.onPrintStarted)
        _instance = self;
        controls = octoprint.settings.settings().get(["controls"])
        if any(c['name'] == 'Position Monitor' for c in controls):
            del controls[next(index for (index, c) in enumerate(controls) if c['name'] == 'Position Monitor')]
        poscontrols = dict(name="Position Monitor", type="section", children=[])
        poscontrols["children"].append(dict(name="Machine Position", type="feedback",
                                            regex=".*(MPos:[+-]?[0-9.]+,[+-]?[0-9.]+,[+-]?[0-9.]+).*",
                                            template="{0}"))
        poscontrols["children"].append(dict(name="Work Position", type="feedback",
                                            regex=".*(WPos:[+-]?[0-9.]+,[+-]?[0-9.]+,[+-]?[0-9.]+)",
                                            template="{0}"))
        controls.append(poscontrols)
        octoprint.settings.settings().set(["controls"],controls)
        self._printer.registerCallback(self)

    def on_after_startup(self):
        # update the extensions allowed by the file manager
        octoprint.filemanager.extensions['machinecode']['gcode'].extend(['nc'])
        octoprint.filemanager.all_extensions = octoprint.filemanager.get_all_extensions()
        self._logger.info("CNC Plugin initialized")


    def sendFeedbackCommandOutput(self, name, output):
        pieces = output.split(':')
        if len(pieces) == 2:
            if pieces[0] == 'WPos':
                self._needPosUpdate = self._lastPos['WPos'] != pieces[1]
                if self._needPosUpdate: self._lastPos['WPos'] = pieces[1]
            elif pieces[0] == 'MPos':
                self._needPosUpdate = self._lastPos['MPos'] != pieces[1]
                if self._needPosUpdate: self._lastPos['MPos'] = pieces[1]

    def addLog(self, data):
        pass

    def addMessage(self, data):
        pass

    def onPrintStarted(self, event, payload):
        profile = self._printer_profile_manager
        if self._printer_profile_manager is None:
            return

    def sendCurrentData(self,data):
        if data is None or data['state'] is None or data['state']['text'] is None:
            return

        # note that these strings are hard coded and therefore brittle
        if self._isCommsInitializing:
            cpp = self._printer_profile_manager.get_current_or_default()
            
            # can use name, model, or id. Going to use model for now
            if cpp is not None and '(grbl)' in cpp['model']:
                self._isGrbl = True
            else:
                self._isGrbl = False

    def addTemperature(self,data):
        pass

    def sendHistoryData(self,data):
        pass

    def get_assets(self):
        return dict(
            js=['js/cncposition.js']
        )

    def get_settings_defaults(self):
        return dict(float_precision=3,
                    trim_floats=True)

    def get_template_configs(self):
        return [
            dict(type="sidebar"),
            dict(type="tab", custom_bindings=False),
            dict(type="settings")
        ]

def roundAllFloats(line, precision):
    for token in line.split():
        m = re.search(r"\b([A-Z])(-?\d+\.\d{3,})\b", token)
        if m:
            rounded = round(float(m.group(2)), precision)
            newtoken="%s%s" % (m.group(1),rounded)
            line = re.sub(token, newtoken, line)
    return(line)


def output_hook(comm,line,sendChecksum):
    cnc = CncPlugin()
    if not cnc.isInitialized():
        return line,sendChecksum

    if not cnc._isGrbl:
        return line, sendChecksum
    
    return line, False
    
def input_hook(comm,line):
    cnc = CncPlugin()
    if not cnc.isInitialized():
        return line
    
    cnc._isCommsInitializing = comm.isInitializing()
    
    if not cnc._isGrbl:
        return line
    
    # this part here is deeply tied to current implementation
    if comm.isInitializing():
        if '$$' in line:
            comm._state = comm.STATE_CONNECTING
            return 'ok T:0'
    
    # The easiest way to deal with all the extra commands for extruders and whatnot
    if line.startswith('error: '):
        return 'ok'
    
    return line
    
def gcode_hook(comm,cmd):
    cnc = CncPlugin()
    if not cnc.isInitialized():
        return cmd

    cnc._isCommsInitializing = comm.isInitializing()
    
    if not cnc._isGrbl:
        return cmd

    if cmd == 'M105':
        if comm.isOperational():
            # this is annoying. I want it to noop, but if I send None or '' it ends up sending the original cmd
            return '?' if cnc._needPosUpdate else None
        else:
            return '$'

    if cnc._settings.get(['trim_floats']):
        cmd = roundAllFloats(cmd,cnc._settings.getInt(['float_precision']))
    
    return cmd

__plugin_implementations__ = [CncPlugin()]
__plugin_hooks__ = {'octoprint.comm.protocol.gcode' : gcode_hook, 
                    'octoprint.comm.protocol.input' : input_hook,
                    'octoprint.comm.protocol.output' : output_hook}
