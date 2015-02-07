# coding=utf-8
from __future__ import absolute_import


import octoprint.plugin
import octoprint.printer
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

        # can use name, model, or id. Going to use model for now
        stext = data['state']['text']

        # note that these strings are hard coded and therefore brittle
        if (stext == "Detecting baudrate"
            or stext == "Opening Serial Port"
            or stext == "Detecting Serial Port"):
            cpp = self._printer_profile_manager.get_current_or_default()
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


def line_hook(comm,line):
    cnc = CncPlugin()
    if not cnc.isInitialized():
        return line
    
    if not cnc._isGrbl:
        return line
    
    # this part here is deeply tied to current implementation
    if comm._state == comm.STATE_DETECT_BAUDRATE \
            or comm._state == comm.STATE_CONNECTING:
        if '$$' in line:
            comm._state = comm.STATE_CONNECTING
            return 'ok T:0'
    
    return line
    
def gcode_hook(comm,cmd):
    cnc = CncPlugin()
    if not cnc.isInitialized():
        return cmd

    if not cnc._isGrbl:
        return cmd

    if cmd == 'M105':
        if comm.isOperational():
            # this is annoying. I want it to noop, but if I send None or '' it ends up sending the original cmd
            return '?' if cnc._needPosUpdate else ' '
        else:
            return '$'

    if cnc._settings.get(['trim_floats']):
        cmd = roundAllFloats(cmd,cnc._settings.getInt(['float_precision']))

__plugin_implementations__ = [CncPlugin()]
__plugin_hooks__ = {'octoprint.comm.protocol.gcode' : gcode_hook, 'octoprint.comm.protocol.input' : line_hook}

'''
looks like I should be able to try to manage the M105 / ? thing here.
It looks like the best thing to do would be to look at some printer profile setting
and do the m105/? thing based on a "GCode Flavor" setting

I could make it decoupled from that and just make it a manual setting somewhere. I could probably
add it into the sidebar or something.

the biggest issue is that I need a chance to see what the responses are and those just are not available.
it is possible that I could do a matcher, but then I'd have to figure out how to suppress it since all
i really care about is during the board connection.

also looks like I can access the _xxx properties from both comm and the CncPlugin so I can probably dive
in pretty deeply.

getting sucked in here....

ooh - I could just use a string in the printer profile name like (grbl) to do the overrides?

'''
