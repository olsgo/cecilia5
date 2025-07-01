# encoding: utf-8
"""
Copyright 2019 iACT, Universite de Montreal,
Jean Piche, Olivier Belanger, Jean-Michel Dumas

This file is part of Cecilia 5.

Cecilia 5 is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Cecilia 5 is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Cecilia 5.  If not, see <http://www.gnu.org/licenses/>.
"""

import os, sys, wx, time, math, copy, codecs, shutil
import unicodedata
from subprocess import Popen
from .constants import *
from .API_interface import *
import Resources.Variables as vars
import wx.lib.agw.supertooltip as STT
import xmlrpc.client as xmlrpclib

if sys.version_info[0] < 3:
    unicode_t = unicode
else:
    unicode_t = str

def buildFileTree():
    root = MODULES_PATH
    directories = []
    files = {}
    for dir in sorted(os.listdir(MODULES_PATH)):
        if not dir.startswith('.'):
            directories.append(dir)
            files[dir] = []
            for f in sorted(os.listdir(os.path.join(root, dir))):
                if not f.startswith('.'):
                    files[dir].append(f)
    return root, directories, files

def setVar(var, value):
    vars.CeciliaVar[var] = value

def getVar(var, unicode=False):
    if unicode:
        return ensureNFD(vars.CeciliaVar[var])
    else:
        return vars.CeciliaVar[var]

def setJackParams(client=None, inPortName=None, outPortName=None):
    if client is not None:
        vars.CeciliaVar['jack']['client'] = client
    if inPortName is not None:
        vars.CeciliaVar['jack']['inPortName'] = inPortName
    if outPortName is not None:
        vars.CeciliaVar['jack']['outPortName'] = outPortName

def setPlugins(x, pos):
    vars.CeciliaVar['plugins'][pos] = x

def getControlPanel():
    return getVar('interface').getControlPanel()

def writeVarToDisk():
    vars.writeCeciliaPrefsToFile()

def chooseColour(i, numlines):
    def clip(x):
        val = int(x * 255)
        if val < 0: val = 0
        elif val > 255: val = 255
        else: val = val
        return val

    def colour(i, numlines, sat, bright):
        hue = (i / numlines) * 315
        segment = math.floor(hue / 60) % 6
        fraction = hue / 60 - segment
        t1 = bright * (1 - sat)
        t2 = bright * (1 - (sat * fraction))
        t3 = bright * (1 - (sat * (1 - fraction)))
        if segment == 0:
            r, g, b = bright, t3, t1
        elif segment == 1:
            r, g, b = t2, bright, t1
        elif segment == 2:
            r, g, b = t1, bright, t3
        elif segment == 3:
            r, g, b = t1, t2, bright
        elif segment == 4:
            r, g, b = t3, t1, bright
        elif segment == 5:
            r, g, b = bright, t1, t2
        return wx.Colour(clip(r), clip(g), clip(b))

    lineColour = colour(i, numlines, 1, 1)
    midColour = colour(i, numlines, .5, .5)
    knobColour = colour(i, numlines, .8, .5)
    sliderColour = colour(i, numlines, .5, .75)

    return [lineColour, midColour, knobColour, sliderColour]

def chooseColourFromName(name):
    def clip(x):
        val = int(x * 255)
        if val < 0: val = 0
        elif val > 255: val = 255
        else: val = val
        return val

    def colour(name):
        vals = COLOUR_CLASSES[name]
        hue = vals[0]
        bright = vals[1]
        sat = vals[2]
        segment = int(math.floor(hue / 60))
        fraction = hue / 60 - segment
        t1 = bright * (1 - sat)
        t2 = bright * (1 - (sat * fraction))
        t3 = bright * (1 - (sat * (1 - fraction)))
        if segment == 0:
            r, g, b = bright, t3, t1
        elif segment == 1:
            r, g, b = t2, bright, t1
        elif segment == 2:
            r, g, b = t1, bright, t3
        elif segment == 3:
            r, g, b = t1, t2, bright
        elif segment == 4:
            r, g, b = t3, t1, bright
        elif segment == 5:
            r, g, b = bright, t1, t2
        return wx.Colour(clip(r), clip(g), clip(b))

    lineColour = colour(name)
    midColour = colour(name)
    knobColour = colour(name)
    sliderColour = colour(name)

    return [lineColour, midColour, knobColour, sliderColour]

### Tooltips ###
class CECTooltip(STT.SuperToolTip):
    def __init__(self, tip):
        STT.SuperToolTip.__init__(self, tip)
        self.SetStartDelay(1.5)
        if getVar("useTooltips"):
            self.EnableTip(True)
        else:
            self.EnableTip(False)
        self.ApplyStyle("Gray")

    def OnMouseEvents(self, evt):
        if evt.ButtonDown() or evt.ButtonDClick():
            self.DoHideNow()
        evt.Skip()

    def update(self):
        if getVar("useTooltips"):
            self.EnableTip(True)
        else:
            self.EnableTip(False)

def setToolTip(obj, tip):
    if "\n" in tip:
        pos = tip.find("\n")
        header = tip[:pos]
        body = tip[pos+1:]
    else:
        header = "Documentation"
        body = tip
    tooltip = CECTooltip(body)
    tooltip.SetHeader(header)
    tooltip.SetTarget(obj)
    tooltip.SetDrawHeaderLine(True)
    getVar("tooltips").append(tooltip)
    obj.Bind(wx.EVT_MOUSE_EVENTS, tooltip.OnMouseEvents)

def updateTooltips():
    for tooltip in getVar("tooltips"):
        tooltip.update()

###### Start / Stop / Drivers ######
def startCeciliaSound(timer=True, rec=False):
    # Check if soundfile is loaded
    for key in getVar("userInputs").keys():
        if 'mode' not in getVar("userInputs")[key]:
            getVar("userInputs")[key]['mode'] = 0
        if getVar("userInputs")[key]['mode'] == 0:
            if not os.path.isfile(getVar("userInputs")[key]['path']):
                showErrorDialog('No input sound file!',
                                'In/Out panel, "%s" has no input sound file, please load one...' % getControlPanel().getCfileinFromName(key).label)
                ret = getControlPanel().getCfileinFromName(key).onLoadFile()
                if not ret:
                    resetControls()
                    getVar("grapher").toolbar.loadingMsg.SetForegroundColour(TITLE_BACK_COLOUR)
                    wx.CallAfter(getVar("grapher").toolbar.loadingMsg.Refresh)
                    return
    getControlPanel().resetMeter()
    getVar("audioServer").shutdown()
    getVar("audioServer").reinit()
    getVar("audioServer").boot()
    if getVar("currentModuleRef") is not None:
        if not getVar("audioServer").loadModule(getVar("currentModuleRef")):
            return
    else:
        showErrorDialog("Wow...!", "No module to load.")
        return
    getVar("grapher").toolbar.convertSlider.Hide()
    getVar("presetPanel").presetChoice.setEnable(False)
    getControlPanel().durationSlider.Disable()
    getVar("audioServer").start(timer=timer, rec=rec)
    if getVar('showSpectrum'):
        getVar('mainFrame').openSpectrumWindow()
    getVar("grapher").toolbar.loadingMsg.SetForegroundColour(TITLE_BACK_COLOUR)
    wx.CallAfter(getVar("grapher").toolbar.loadingMsg.Refresh)

def stopCeciliaSound():
    if getVar('spectrumFrame') is not None:
        try:
            getVar('spectrumFrame').onClose()
        except:
            getVar('interface').menubar.spectrumSwitch(False)
            setVar('showSpectrum', 0)
        finally:
            setVar('spectrumFrame', None)
    if getVar("audioServer").isAudioServerRunning():
        getVar("audioServer").stop()
        time.sleep(.25)
        if getVar("currentModule") is not None:
            getVar("audioServer").checkForAutomation()
            getVar("currentModule")._checkForAutomation()
            getVar("grapher").checkForAutomation()
    resetControls()

def resetControls():
    if getVar('interface') is not None:
        getControlPanel().transportButtons.setPlay(False)
        getControlPanel().transportButtons.setRecord(False)
        getVar("presetPanel").presetChoice.setEnable(True)
        getControlPanel().durationSlider.Enable()
        if getControlPanel().tmpTotalTime != getVar("totalTime"):
            getControlPanel().setTotalTime(getControlPanel().tmpTotalTime, True)
        wx.CallAfter(getControlPanel().vuMeter.reset)

def queryAudioMidiDrivers():
    inputs, inputIndexes, defaultInput, outputs, outputIndexes, \
    defaultOutput, midiInputs, midiInputIndexes, defaultMidiInput = getVar("audioServer").getAvailableAudioMidiDrivers()
    setVar("availableAudioOutputs", outputs)
    setVar("availableAudioOutputIndexes", outputIndexes)
    if getVar("audioOutput") not in outputIndexes:
        try:
            setVar("audioOutput", outputIndexes[outputs.index(defaultOutput)])
        except:
            setVar("audioOutput", 0)

    setVar("availableAudioInputs", inputs)
    setVar("availableAudioInputIndexes", inputIndexes)
    if getVar("audioInput") not in inputIndexes:
        try:
            setVar("audioInput", inputIndexes[inputs.index(defaultInput)])
        except:
            setVar("audioInput", 0)

    if midiInputs == []:
        setVar("useMidi", 0)
    else:
        setVar("useMidi", 1)
    setVar("availableMidiInputs", midiInputs)
    setVar("availableMidiInputIndexes", midiInputIndexes)
    if getVar("midiDeviceIn") not in midiInputIndexes:
        try:
            setVar("midiDeviceIn", midiInputIndexes[midiInputs.index(defaultMidiInput)])
        except:
            setVar("midiDeviceIn", 0)

def openAudioFileDialog(parent, wildcard, type='open', defaultPath=os.path.expanduser('~')):
    setVar("canGrabFocus", False)
    openDialog = wx.FileDialog(parent, message='Choose a file to %s' % type,
                                defaultDir=defaultPath, wildcard=wildcard,
                                style=wx.FD_OPEN | wx.FD_PREVIEW)
    if openDialog.ShowModal() == wx.ID_OK:
        filePath = ensureNFD(openDialog.GetPath())
        setVar("openAudioFilePath", os.path.split(filePath)[0])
    else:
        filePath = None
    openDialog.Destroy()
    setVar("canGrabFocus", True)
    return filePath

def saveFileDialog(parent, wildcard, type='Save'):
    if type == 'Save audio':
        defaultPath = getVar("saveAudioFilePath", unicode=True)
        ext = "." + getVar("audioFileType")
    else:
        defaultPath = getVar("saveFilePath", unicode=True)
        ext = ".c5"

    setVar("canGrabFocus", False)
    defaultFile = os.path.split(getVar("currentCeciliaFile", unicode=True))[1].split(".")[0]
    saveAsDialog = wx.FileDialog(parent, message="%s file as ..." % type,
                                 defaultDir=defaultPath, defaultFile=defaultFile + ext,
                                 wildcard=wildcard, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT)
    if saveAsDialog.ShowModal() == wx.ID_OK:
        filePath = ensureNFD(saveAsDialog.GetPath())
        if type == 'Save audio':
            setVar("saveAudioFilePath", os.path.split(filePath)[0])
        else:
            setVar("saveFilePath", os.path.split(filePath)[0])
    else:
        filePath = None
    saveAsDialog.Destroy()
    setVar("canGrabFocus", True)
    return filePath

def showErrorDialog(title, msg):
    setVar("canGrabFocus", False)
    if getVar("mainFrame") is not None:
        dlg = wx.MessageDialog(getVar("mainFrame"), msg, title, wx.OK)
    else:
        dlg = wx.MessageDialog(None, msg, title, wx.OK)
    dlg.ShowModal()
    dlg.Destroy()
    setVar("canGrabFocus", True)

###### External app calls ######
def loadPlayerEditor(app_type):
    if getVar("systemPlatform") == 'win32':
        wildcard = "Executable files (*.exe)|*.exe|"     \
                    "All files|*"
    elif getVar("systemPlatform") == 'darwin':
        wildcard = "Application files (*.app)|*.app|"     \
                    "All files|*"
    else:
        wildcard = "All files|*"

    setVar("canGrabFocus", False)
    path = ''
    dlg = wx.FileDialog(None, message="Choose a %s..." % app_type,
                        defaultDir=ensureNFD(os.path.expanduser('~')),
                        wildcard=wildcard, style=wx.FD_OPEN)

    if dlg.ShowModal() == wx.ID_OK:
        path = dlg.GetPath()
    dlg.Destroy()
    setVar("canGrabFocus", True)

    if path:
        if app_type == 'soundfile player':
            setVar("soundfilePlayer", path)
        elif app_type == 'soundfile editor':
            setVar("soundfileEditor", path)
        elif app_type == 'text editor':
            setVar("textEditor", path)

def listenSoundfile(soundfile):
    if getVar("soundfilePlayer") == '':
        showErrorDialog("Preferences not set", "Choose a soundfile player first.")
        loadPlayerEditor('soundfile player')
    if os.path.isfile(soundfile):
        app = getVar("soundfilePlayer")
        if getVar("systemPlatform") == 'darwin':
            cmd = 'open -a "%s" "%s"' % (app, soundfile)
            Popen(cmd, shell=True)
        elif getVar("systemPlatform") == 'win32':
            try:
                Popen([app, soundfile], shell=False)
            except (OSError, OSError2):
                print('Unable to open desired software:\n' + app)
        else:
            cmd = '"%s" "%s"' % (app, soundfile)
            try:
                Popen(cmd, shell=True)
            except (OSError, OSError2):
                print('Unable to open desired software:\n' + app)

def editSoundfile(soundfile):
    if getVar("soundfileEditor") == '':
        showErrorDialog("Preferences not set", "Choose a soundfile editor first.")
        loadPlayerEditor('soundfile editor')
    if os.path.isfile(soundfile):
        app = getVar("soundfileEditor")
        if getVar("systemPlatform") == 'darwin':
            cmd = 'open -a "%s" "%s"' % (app, soundfile)
            Popen(cmd, shell=True)
        elif getVar("systemPlatform") == 'win32':
            try:
                Popen([app, soundfile], shell=False)
            except (OSError, OSError2):
                print('Unable to open desired software:\n' + app)
        else:
            cmd = '%s %s' % (app, soundfile)
            try:
                Popen(cmd, shell=True)
            except (OSError, OSError2):
                print('Unable to open desired software:\n' + app)

def openCurrentFileAsText(curfile):
    if getVar("textEditor") == '':
        showErrorDialog("Preferences not set", "Choose a text editor first.")
        loadPlayerEditor('text editor')
    if os.path.isfile(curfile):
        app = getVar("textEditor")
        if getVar("systemPlatform") == 'darwin':
            cmd = 'open -a "%s" "%s"' % (app, os.path.join(os.getcwd(), curfile))
            Popen(cmd, shell=True, cwd=os.path.expanduser("~"))
        elif getVar("systemPlatform") == 'win32':
            try:
                Popen([app, curfile], shell=False)
            except (OSError, OSError2):
                print('Unable to open desired software:\n' + app)
        else:
            cmd = '%s %s' % (app, curfile)
            try:
                Popen(cmd, shell=True)
            except (OSError, OSError2):
                print('Unable to open desired software:\n' + app)

###### Preset functions ######
def loadPresetFromFile(preset):
    presetFile = os.path.join(PRESETS_PATH, getVar("currentModuleName"), preset)

    presetData = None
    if preset == "init":
        presetData = getVar("initPreset")
    elif os.path.isfile(presetFile):
        with open(presetFile, 'r') as f:
            try:
                result, method = xmlrpclib.loads(f.read())
                presetData = result[0]
            except:
                showErrorDialog("Preset corrupted...", "Failed to load preset '%s', reloading 'init'..." % preset)
                preset = "init"
                presetData = getVar("initPreset")

    if presetData is not None:
        currentModule = getVar("currentModule")
        setVar("currentModule", None)

        for data in presetData.keys():
            if data == 'userInputs':
                if presetData[data] == {}:
                    continue
                ok = True
                prekeys = presetData[data].keys()
                for key in prekeys:
                    if not os.path.isfile(presetData[data][key]['path']):
                        ok = False
                        break
                if not getVar("rememberedSound"):
                    if ok:
                        setVar("userInputs", copy.deepcopy(presetData[data]))
                        updateInputsFromDict()
                    else:
                        for input in getVar("userInputs"):
                            cfilein = getControlPanel().getCfileinFromName(input)
                            cfilein.reset()
                            cfilein.reinitSamplerFrame()
                else:
                    if ok:
                        setVar("userInputs", copy.deepcopy(presetData[data]))
                        updateInputsFromDict()
                    else:
                        for input in getVar("userInputs"):
                            cfilein = getControlPanel().getCfileinFromName(input)
                            cfilein.reinitSamplerFrame()
            elif data == 'userSliders':
                slidersDict = presetData[data]
                for slider in getVar("userSliders"):
                    if slider.getName() in slidersDict:
                        slider.setState(slidersDict[slider.getName()])
                del slidersDict
            elif data == 'plugins':
                pluginsDict = deepCopy(presetData[data])
                wx.CallAfter(getControlPanel().setPlugins, pluginsDict)
                del pluginsDict
            elif data == 'userTogglePopups':
                togDict = presetData[data]
                for widget in getVar("userTogglePopups"):
                    if widget.getName() in togDict and hasattr(widget, "setValue"):
                        widget.setValue(togDict[widget.getName()], True)
                del togDict
            else:
                continue
        if preset == "init":
            for line in getVar("grapher").getPlotter().getData():
                try:
                    line.reinit()
                except:
                    pass
        elif 'userGraph' in presetData:
            graphDict = deepCopy(presetData['userGraph'])
            ends = ['min', 'max']
            for line in graphDict:
                for i, graphLine in enumerate(getVar("grapher").getPlotter().getData()):
                    if line == graphLine.getName():
                        graphLine.setLineState(graphDict[line])
                        break
                    else:
                        for end in ends:
                            if graphLine.getLabel().endswith(end) and line.endswith(end) and line.startswith(graphLine.getName()):
                                graphLine.setLineState(graphDict[line])
                                break
            del graphDict

        setVar("totalTime", presetData["totalTime"])
        getControlPanel().updateDurationSlider()
        setVar("nchnls", presetData["nchnls"])
        updateNchnlsDevices()
        getVar("gainSlider").SetValue(presetData["gainSlider"])
        getVar("presetPanel").setLabel(preset)
        getVar("grapher").getPlotter().draw()
        setVar("currentModule", currentModule)
        getVar("grapher").setTotalTime(getVar("totalTime"))

        wx.CallAfter(againForPluginKnobs, presetData)

### This is a hack to ensure that plugin knob automations are drawn in the grapher.
### Called within a wx.CallAfter to be executed after wx.CallAfter(getControlPanel().setPlugins).
def againForPluginKnobs(presetData):
    if 'userGraph' in presetData:
        graphDict = presetData['userGraph']
        for line in graphDict:
            for i, graphLine in enumerate(getVar("grapher").getPlotter().getData()):
                if line == graphLine.getName():
                    graphLine.setLineState(graphDict[line])
                    break
        del graphDict
        getVar("grapher").getPlotter().draw()
        getVar("grapher").setTotalTime(getVar("totalTime"))

def savePresetToFile(presetName):
    presetDict = dict()
    presetDict['nchnls'] = getVar("nchnls")
    presetDict['totalTime'] = getVar("totalTime")
    presetDict['gainSlider'] = getVar("gainSlider").GetValue()
    if getVar("interface"):
        presetDict['userInputs'] = completeUserInputsDict()

        sliderDict = dict()
        for slider in getVar("userSliders"):
            sliderDict[slider.getName()] = slider.getState()
        presetDict['userSliders'] = copy.deepcopy(sliderDict)
        del sliderDict

        widgetDict = dict()
        plugins = getVar("plugins")
        for i, plugin in enumerate(plugins):
            if plugin is None:
                widgetDict[str(i)] = ['None', [0, 0, 0, 0], [[0, 0, None], [0, 0, None], [0, 0, None]]]
            else:
                widgetDict[str(i)] = [plugin.getName(), plugin.getParams(), plugin.getStates()]
        presetDict['plugins'] = copy.deepcopy(widgetDict)
        del widgetDict

        widgetDict = dict()
        for widget in getVar("userTogglePopups"):
            widgetDict[widget.getName()] = widget.getValue()
        presetDict['userTogglePopups'] = copy.deepcopy(widgetDict)
        del widgetDict

        graphDict = dict()
        for line in getVar("grapher").getPlotter().getData():
            if line.slider is None:
                graphDict[line.getName()] = line.getLineState()
            else:
                outvalue = line.slider.getValue()
                if line.slider.widget_type in ["slider", "plugin_knob"]:
                    graphDict[line.getName()] = line.getLineState()
                elif line.slider.widget_type == "range":
                    ends = ['min', 'max']
                    for i in range(len(outvalue)):
                        if line.getLabel().endswith(ends[i]):
                            graphDict[line.getName() + ends[i]] = line.getLineState()
                            break
                elif line.slider.widget_type == "splitter":
                    for i in range(len(outvalue)):
                        if line.getLabel().endswith("%d" % i):
                            graphDict[line.getName() + "_%d" % i] = line.getLineState()
                            break
        presetDict['userGraph'] = copy.deepcopy(graphDict)
        del graphDict

        if presetName == "init":
            setVar("initPreset", deepCopy(presetDict))
        else:
            with open(os.path.join(PRESETS_PATH, getVar('currentModuleName'), presetName), "w") as presetFile:        
                msg = xmlrpclib.dumps((presetDict, ), allow_none=True)
                presetFile.write(msg)

def completeUserInputsDict():
    for i in getVar("userInputs"):
        try:
            getVar("userInputs")[i]['mode'] = 0
            if getVar("userInputs")[i]['type'] == 'csampler':
                cfilein = getControlPanel().getCfileinFromName(i)
                getVar("userInputs")[i]['off' + cfilein.getName()] = cfilein.getOffset()
                getVar("userInputs")[i]['loopMode'] = cfilein.getSamplerInfo()['loopMode']
                getVar("userInputs")[i]['startFromLoop'] = cfilein.getSamplerInfo()['startFromLoop']
                getVar("userInputs")[i]['loopX'] = cfilein.getSamplerInfo()['loopX']
                getVar("userInputs")[i]['loopIn'] = cfilein.getSamplerInfo()['loopIn']
                getVar("userInputs")[i]['loopOut'] = cfilein.getSamplerInfo()['loopOut']
                getVar("userInputs")[i]['gain'] = cfilein.getSamplerInfo()['gain']
                getVar("userInputs")[i]['transp'] = cfilein.getSamplerInfo()['transp']
            elif getVar("userInputs")[i]['type'] == 'cfilein':
                cfilein = getControlPanel().getCfileinFromName(i)
                getVar("userInputs")[i]['off' + cfilein.getName()] = cfilein.getOffset()
        except:
            pass
    return copy.deepcopy(getVar("userInputs"))

def updateInputsFromDict():
    for input in getVar("userInputs"):
        cfilein = getControlPanel().getCfileinFromName(input)
        if cfilein and os.path.isfile(getVar("userInputs")[input]['path']):
            inputDict = getVar("userInputs")[input]
            cfilein.updateMenuFromPath(inputDict['path'])
            for k in inputDict:
                if k == 'loopMode':
                    cfilein.getSamplerFrame().setLoopMode(inputDict[k])
                elif k == 'loopX':
                    cfilein.getSamplerFrame().setLoopX(inputDict[k])
                elif k == 'loopIn':
                    cfilein.getSamplerFrame().setLoopIn(inputDict[k])
                elif k == 'loopOut':
                    cfilein.getSamplerFrame().setLoopOut(inputDict[k])
                elif k == 'gain':
                    cfilein.getSamplerFrame().setGain(inputDict[k])
                elif k == 'transp':
                    cfilein.getSamplerFrame().setTransp(inputDict[k])
                elif k == 'startFromLoop':
                    cfilein.getSamplerFrame().setStartFromLoop(inputDict[k])
                elif k == ('off' + input):
                    cfilein.setOffset(inputDict[k])
                elif k == 'path':
                    pass

###### Open / Save / Close ######
def saveCompileBackupFile(cecFilePath):
    with open(cecFilePath, "r") as f:
        _module = f.read()
    with open(MODULE_COMPILE_BACKUP_PATH, "w") as f:
        f.write(_module)

def saveRuntimeBackupFile(cecFilePath):
    with open(cecFilePath, "r") as f:
        _module = f.read()
    with open(MODULE_RUNTIME_BACKUP_PATH, "w") as f:
        f.write(_module)

def saveCeciliaFile(parent):
    wildcard = "Cecilia file (*.%s)|*.%s" % (FILE_EXTENSION, FILE_EXTENSION)
    fileToSave = saveFileDialog(parent, wildcard, 'Save')
    if not fileToSave:
        return
    else:
        if not fileToSave.endswith(FILE_EXTENSION):
            fileToSave = "%s.%s" % (fileToSave, FILE_EXTENSION)

    savePresetToFile("last save")

    curfile = codecs.open(getVar("currentCeciliaFile", unicode=True), "r", encoding="utf-8")
    curtext = curfile.read()
    curfile.close()

    try:
        file = codecs.open(fileToSave, "w", encoding="utf-8")
    except IOError:
        setVar("canGrabFocus", False)
        dlg = wx.MessageDialog(parent, 'Please verify permissions and write access on the file and try again.',
                            '"%s" could not be opened for writing' % (fileToSave), wx.OK | wx.ICON_EXCLAMATION)
        if dlg.ShowModal() == wx.ID_OK:
            dlg.Destroy()
            setVar("canGrabFocus", True)
            return

    file.write(curtext.rstrip())
    file.close()

    oldModuleName = os.path.split(getVar("currentCeciliaFile"))[1]
    oldModuleName = os.path.splitext(oldModuleName)[0]
    newModuleName = os.path.split(fileToSave)[1]
    newModuleName = os.path.splitext(newModuleName)[0]
    if not os.path.isdir(os.path.join(PRESETS_PATH, newModuleName)):
        os.mkdir(os.path.join(PRESETS_PATH, newModuleName))
    for f in os.listdir(os.path.join(PRESETS_PATH, oldModuleName)):
        shutil.copyfile(os.path.join(PRESETS_PATH, oldModuleName, f), os.path.join(PRESETS_PATH, newModuleName, f))

    setVar("builtinModule", False)
    setVar('currentModuleName', newModuleName)
    setVar("currentCeciliaFile", fileToSave)
    setVar("lastCeciliaFile", fileToSave)

    if getVar("mainFrame") is not None:
        getVar("mainFrame").newRecent(fileToSave)

    saveCompileBackupFile(fileToSave)

def openCeciliaFile(parent, openfile=None, builtin=False):
    if not openfile:
        setVar("canGrabFocus", False)
        wildcard = "Cecilia file (*.%s)|*.%s" % (FILE_EXTENSION, FILE_EXTENSION)
        defaultPath = getVar("openFilePath", unicode=True)
        openDialog = wx.FileDialog(parent, message='Choose a Cecilia file to open...',
                                    defaultDir=defaultPath, wildcard=wildcard, style=wx.FD_OPEN)
        if openDialog.ShowModal() == wx.ID_OK:
            cecFilePath = openDialog.GetPath()
            setVar("openFilePath", (os.path.split(cecFilePath)[0]))
        else:
            cecFilePath = None
        openDialog.Destroy()
        setVar("canGrabFocus", True)

        if cecFilePath is None:
            return
    else:
        cecFilePath = openfile

    if getVar("audioServer").isAudioServerRunning():
        stopCeciliaSound()

    snds = []
    if getVar("rememberedSound") and getVar("interfaceWidgets") and getVar("userInputs"):
        try:
            names = [d['name'] for d in getVar("interfaceWidgets")]
            keys = getVar("userInputs").keys()
            sortlist = list(zip([names.index(k) for k in keys], keys))
            sortlist.sort()
            index, keys = list(zip(*sortlist))
            for key in keys:
                if getVar("userInputs")[key]['path'] != '':
                    snds.append(getVar("userInputs")[key]['path'])
        except:
            pass

    if getVar("currentCeciliaFile"):
        closeCeciliaFile(parent)

    moduleName = os.path.split(cecFilePath)[1]
    moduleName = os.path.splitext(moduleName)[0]
    setVar('currentModuleName', moduleName)
    if not os.path.isdir(os.path.join(PRESETS_PATH, moduleName)):
        os.mkdir(os.path.join(PRESETS_PATH, moduleName))

    getVar("mainFrame").Hide()

    if not getVar("audioServer").openCecFile(cecFilePath):
        return

    setVar("builtinModule", builtin)
    setVar("currentCeciliaFile", cecFilePath)
    setVar("lastCeciliaFile", cecFilePath)

    if getVar("mainFrame") is not None:
        getVar("mainFrame").newRecent(cecFilePath)

    saveCompileBackupFile(cecFilePath)

    if getVar("interface"):
        for i, cfilein in enumerate(getControlPanel().getCfileinList()):
            if i >= len(snds):
                break
            cfilein.onLoadFile(snds[i])

    savePresetToFile("init")

    if os.path.isfile(os.path.join(PRESETS_PATH, moduleName, "last save")):
        setVar("presetToLoad", "last save")

    getVar("mainFrame").updateTitle()

    getVar("interface").Raise()

def closeCeciliaFile(parent):
    savePresetToFile("last save")
    getVar("mainFrame").closeInterface()
    setVar("currentCeciliaFile", '')

###### Interface creation utilities ######
def resetWidgetVariables():
    setVar("gainSlider", None)
    setVar("plugins", [None] * NUM_OF_PLUGINS)
    setVar("userInputs", {})
    for slider in getVar("userSliders"):
        slider.cleanup()
    setVar("userSliders", [])
    setVar("userSamplers", [])
    setVar("userTogglePopups", [])
    setVar("samplerSliders", [])
    setVar("samplerTogglePopup", [])
    getVar("presetPanel").cleanup()
    getVar("presetPanel").parent = None
    setVar("presetPanel", None)
    getVar("grapher").parent = None
    setVar("grapher", None)
    setVar("tooltips", [])

def parseInterfaceText():
    interfaceWidgets = getVar("interfaceWidgets")
    return interfaceWidgets

def updateNchnlsDevices():
    try:
        getVar("interface").updateNchnls()
    except:
        pass

def deepCopy(ori):
    if type(ori) is dict:
        new = {}
        for key in ori:
            new[key] = deepCopy(ori[key])
        return new
    elif type(ori) is list:
        new = []
        for data in ori:
            new.append(deepCopy(data))
        return new
    elif type(ori) is tuple:
        new = []
        for data in ori:
            new.append(deepCopy(data))
        return tuple(new)
    else:
        return ori

###### Conversion functions #######
def interpFloat(t, v1, v2):
    "interpolator for a single value; interprets t in [0-1] between v1 and v2"
    return (v2 - v1) * t + v1

def tFromValue(value, v1, v2):
    "returns a t (in range 0-1) given a value in the range v1 to v2"
    return (value - v1) / (v2 - v1)

def clamp(v, minv, maxv):
    "clamps a value within a range"
    if v < minv: v = minv
    if v > maxv: v = maxv
    return v

def toLog(t, v1, v2):
    v1 = float(v1)
    return math.log10(t / v1) / math.log10(v2 / v1)

def toExp(t, v1, v2):
    return math.pow(10, t * (math.log10(v2) - math.log10(v1)) + math.log10(v1))

###### Utility functions #######
def autoRename(path, index=0, wrap=False):
    if os.path.exists(path):
        file = ensureNFD(os.path.split(path)[1])
        if wrap:
            name = ensureNFD(file.rsplit('.', 1)[0])[:-4]
        else:
            name = ensureNFD(file.rsplit('.', 1)[0])
        ext = file.rsplit('.', 1)[1]

        if len(name) >= 5:
            if name[-4] == '_' and name[-3:].isdigit():
                name = name[:-4]
        root = os.path.split(path)[0]
        filelist = os.listdir(root)
        num = index
        for f in filelist:
            f = ensureNFD(f)
            if name in f and ext in f:
                num += 1
        newName = name + '_%03d' % num + '.' + ext
        newPath = os.path.join(root, newName)
        return autoRename(newPath, index + 1, True)
    else:
        newPath = path
    return newPath

def shortenName(name, maxChar):
    name = ensureNFD(name)
    if len(name) > maxChar:
        shortenChar = '...'
        addSpace = 0
        charSpace = (maxChar - len(shortenChar)) // 2
        if (maxChar - 5) % 2 != 0:
            addSpace = 1
        name = name[:charSpace + addSpace] + shortenChar + name[len(name) - charSpace:]
    return name

def ensureNFD(unistr):
    if getVar("systemPlatform").startswith('linux') or sys.platform == 'win32':
        encodings = [DEFAULT_ENCODING, ENCODING,
                     'cp1252', 'iso-8859-1', 'utf-16']
        format = 'NFC'
    else:
        encodings = [DEFAULT_ENCODING, ENCODING,
                     'macroman', 'iso-8859-1', 'utf-16']
        format = 'NFC'
    decstr = unistr
    if type(decstr) != unicode_t:
        for encoding in encodings:
            try:
                decstr = decstr.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
            except:
                decstr = "UnableToDecodeString"
                print("Unicode encoding not in a recognized format...")
                break
    if decstr == "UnableToDecodeString":
        return unistr
    else:
        return unicodedata.normalize(format, decstr)

def checkForPresetsInCeciliaFile(filepath):
    PRESETS_DELIMITER = "####################################\n" \
                        "##### Cecilia reserved section #####\n" \
                        "#### Presets saved from the app ####\n" \
                        "####################################\n"

    mylocals = {}
    rewrite = False

    with open(filepath, "r") as f:
        text = f.read()
        if PRESETS_DELIMITER in text:
            rewrite = True
            newtext = text[:text.find(PRESETS_DELIMITER) - 1]
            text = text[text.find(PRESETS_DELIMITER) + len(PRESETS_DELIMITER) + 1:]
            if text.strip() != "":
                exec(text, globals(), mylocals)

                presetsDir = os.path.join(PRESETS_PATH, getVar("currentModuleName")) 
                if not os.path.isdir(presetsDir):
                    os.mkdir(presetsDir)

                for preset in mylocals["CECILIA_PRESETS"]:
                    for key in list(mylocals["CECILIA_PRESETS"][preset]["plugins"]):
                        mylocals["CECILIA_PRESETS"][preset]["plugins"][str(key)] = mylocals["CECILIA_PRESETS"][preset]["plugins"][key]
                        del mylocals["CECILIA_PRESETS"][preset]["plugins"][key]
                    msg = xmlrpclib.dumps((mylocals["CECILIA_PRESETS"][preset], ), allow_none=True)
                    with open(os.path.join(presetsDir, preset), "w") as fw:
                        fw.write(msg)
    if rewrite:
        with open(filepath, "w") as f:
            f.write(newtext)
