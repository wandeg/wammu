import wx
import wx.html
import gammu
import sys
import datetime
import Wammu
import Wammu.Events
import Wammu.Displayer
import Wammu.Browser
from Wammu.Paths import *
import threading
import copy

def SortDataKeys(a, b):
    if a == 'info':
        return -1
    elif b == 'info':
        return 1
    else:
        return cmp(a,b)
        
def SortDataSubKeys(a, b):
    if a == '  ':
        return -1
    elif b == '  ':
        return 1
    else:
        return cmp(a,b)

displaydata = {}
displaydata['info'] = {}
displaydata['call'] = {}
displaydata['memory'] = {}
displaydata['message'] = {}
displaydata['todo'] = {}

#information
displaydata['info']['  '] = ('', _('Phone'), _('Phone Information'), 'phone', [[_('Wammu version'), Wammu.__version__], [_('Gammu version'), gammu.Version()[0]], [_('python-gammu version'), gammu.Version()[1]]])

# calls
displaydata['call']['  '] = ('info', _('Calls'), _('All Calls'), 'call', [])
displaydata['call']['RC'] = ('call', _('Received'), _('Received Calls'), 'call-received', [])
displaydata['call']['MC'] = ('call', _('Missed'), _('Missed Calls'), 'call-missed', [])
displaydata['call']['DC'] = ('call', _('Outgoing'), _('Outgoing Calls'), 'call-outgoing', [])

# contacts
displaydata['memory']['  '] = ('info', _('Contacts'), _('All Contacts'), 'contact', [])
displaydata['memory']['SM'] = ('memory', _('SIM'), _('SIM Contacts'), 'contact-sim', [])
displaydata['memory']['ME'] = ('memory', _('Phone'), _('Phone Contacts'), 'contact-phone', [])

# contacts
displaydata['message']['  '] = ('info', _('Messages'), _('All Messages'), 'message', [])
displaydata['message'][' R'] = ('message', _('Read'), _('Read Messages'), 'message-read', [])
displaydata['message']['UR'] = ('message', _('Unread'), _('Unread Messages'), 'message-unread', [])
displaydata['message'][' S'] = ('message', _('Sent'), _('Sent Messages'), 'message-sent', [])
displaydata['message']['US'] = ('message', _('Unsent'), _('Unsent Messages'), 'message-unsent', [])

#todos
displaydata['todo']['  '] = ('info', _('Todos'), _('All Todos'), 'todo', [])


## Create a new frame class, derived from the wxPython Frame.
class WammuFrame(wx.Frame):

    def __init__(self, parent, id):
        wx.Frame.__init__(self, parent, id, 'Wammu', wx.DefaultPosition, wx.Size(640,480), wx.DEFAULT_FRAME_STYLE)
        self.CreateStatusBar(2)
        self.SetStatusWidths([-1,100])

        # Associate some events with methods of this class
        wx.EVT_CLOSE(self, self.CloseWindow)
        Wammu.Events.EVT_PROGRESS(self, self.OnProgress)
        Wammu.Events.EVT_SHOW_MESSAGE(self, self.OnShowMessage)
        Wammu.Events.EVT_LINK(self, self.OnLink)
        Wammu.Events.EVT_DATA(self, self.OnData)
        Wammu.Events.EVT_SHOW(self, self.OnShow)
        Wammu.Events.EVT_EDIT(self, self.OnEdit)
        Wammu.Events.EVT_DELETE(self, self.OnDelete)

        self.splitter = wx.SplitterWindow(self, -1)
        il = wx.ImageList(16, 16)

        self.tree = wx.TreeCtrl(self.splitter)
        self.tree.AssignImageList(il)

        self.treei = {}
        self.values = {}

        keys = displaydata.keys()
        keys.sort(SortDataKeys)
        for type in keys:
            self.treei[type] = {}
            self.values[type] = {}
            subkeys = displaydata[type].keys()
            subkeys.sort(SortDataSubKeys)
            for subtype in subkeys:
                self.values[type][subtype] = displaydata[type][subtype][4]
                if displaydata[type][subtype][0] == '':
                    self.treei[type][subtype] = self.tree.AddRoot(
                        displaydata[type][subtype][1], 
                        il.Add(wx.Bitmap(IconPath(displaydata[type][subtype][3]))))
                else:
                    self.treei[type][subtype] = self.tree.AddRoot(
                        displaydata[type][subtype][1], 
                        il.Add(wx.Bitmap(IconPath(displaydata[type][subtype][3]))))
                    self.treei[type][subtype] = self.tree.AppendItem(
                        self.treei[displaydata[type][subtype][0]]['  '], 
                        displaydata[type][subtype][1], 
                        il.Add(wx.Bitmap(IconPath(displaydata[type][subtype][3]))))

        for type in keys:
            self.tree.Expand(self.treei[type]['  '])

        wx.EVT_TREE_SEL_CHANGED(self, self.tree.GetId(), self.OnTreeSel)
        

        # right frame
        self.rightsplitter = wx.SplitterWindow(self.splitter, -1)
        self.rightwin = wx.Panel(self.rightsplitter, -1)
        self.rightwin.sizer = wx.BoxSizer(wx.VERTICAL)
        
        # title text
        self.label = wx.StaticText(self.rightwin, -1, 'Wammu')
        self.rightwin.sizer.Add(self.label, 0, wx.LEFT|wx.ALL, 2)

        # line
        self.rightwin.sizer.Add(wx.StaticLine(self.rightwin, -1), 0 , wx.EXPAND)

        # item browser
        self.browser = Wammu.Browser.Browser(self.rightwin, self)
        self.rightwin.sizer.Add(self.browser, 1, wx.EXPAND)
        self.rightwin.SetSizer(self.rightwin.sizer)

        # values displayer
        self.content = Wammu.Displayer.Displayer(self.rightsplitter, self)
        self.rightsplitter.SplitHorizontally(self.rightwin, self.content, -200)

        self.splitter.SplitVertically(self.tree, self.rightsplitter, 160)

        # initial content
        self.content.SetPage('<body><html><font size=+1><b>' + _('Welcome to Wammu') + ' ' + Wammu.__version__ + '</b></font><br><a href="memory://ME/1">Mem 1</a></html></body>')

        # Prepare the menu bar
        self.menuBar = wx.MenuBar()

        # 1st menu from left
        menu1 = wx.Menu()
#        menu1.Append(101, _('&SearchPhone'), _('Search for phone'))
#        menu1.AppendSeparator()
        menu1.Append(150, _('&Settings'), _('Change Wammu settings'))
        menu1.AppendSeparator()
        menu1.Append(199, _('E&xit'), _('Exit Wammu'))
        # Add menu to the menu bar
        self.menuBar.Append(menu1, _('&Wammu'))
        
        # 2st menu from left
        menu2 = wx.Menu()
        menu2.Append(201, _('&Connect'), _('Connect the device'))
        menu2.Append(202, _('&Disconnect'), _('Disconnect the device'))
        menu2.AppendSeparator()
        menu2.Append(210, _('&Synchronise time'), _('Synchronises time in mobile with PC'))
        # Add menu to the menu bar
        self.menuBar.Append(menu2, _('&Phone'))

        # 2st menu from left
        menu3 = wx.Menu()
        menu3.Append(301, _('&Info'), _('Get phone information'))
        menu3.AppendSeparator()
        menu3.Append(310, _('Contacts (&SIM)'), _('Contacts from SIM'))
        menu3.Append(311, _('Contacts (&phone)'), _('Contacts from phone memory'))
        menu3.Append(312, _('&Contacts (All)'), _('Contacts from phone and SIM memory'))
        menu3.AppendSeparator()
        menu3.Append(320, _('C&alls'), _('Calls'))
        menu3.AppendSeparator()
        menu3.Append(330, _('&Messages'), _('Messages'))
        menu3.AppendSeparator()
        menu3.Append(340, _('&Todos'), _('Todos'))
        # Add menu to the menu bar
        self.menuBar.Append(menu3, _('&Retrieve'))

        # 2st menu from left
        menu4 = wx.Menu()
        menu4.Append(401, _('&Contact'), _('Crates new contact'))
        # Add menu to the menu bar
        self.menuBar.Append(menu4, _('&New'))

        # Set menu bar
        self.SetMenuBar(self.menuBar)

        # menu events
        wx.EVT_MENU(self, 150, self.Settings)
        wx.EVT_MENU(self, 199, self.CloseWindow)
        
        wx.EVT_MENU(self, 201, self.PhoneConnect)
        wx.EVT_MENU(self, 202, self.PhoneDisconnect)
        wx.EVT_MENU(self, 210, self.SyncTime)

        wx.EVT_MENU(self, 301, self.ShowInfo)
        wx.EVT_MENU(self, 310, self.ShowContactsSM)
        wx.EVT_MENU(self, 311, self.ShowContactsME)
        wx.EVT_MENU(self, 312, self.ShowContacts)
        wx.EVT_MENU(self, 320, self.ShowCalls)
        wx.EVT_MENU(self, 330, self.ShowMessages)
        wx.EVT_MENU(self, 340, self.ShowTodos)
        
        wx.EVT_MENU(self, 401, self.NewContact)


        self.TogglePhoneMenus(False)

        self.type = ['info','  ']
        self.ActivateView('info', '  ')
        
        # create state machine
        self.sm = gammu.StateMachine()


    def PostInit(self):
        # things that need window opened
        self.cfg = wx.Config(style = wx.CONFIG_USE_LOCAL_FILE)

        if not self.cfg.HasGroup('/Gammu'):
            try:
                self.sm.ReadConfig()
                config = self.sm.GetConfig()

                wx.MessageDialog(self, 
                    _('Wammu configuration was not found. Gammu settings were read and will be used as defaults. You will now be taken to configuration dialog to check configuration.'),
                    _('Configuration not found'),
                    wx.OK | wx.ICON_INFORMATION).ShowModal()
            except:
                wx.MessageDialog(self, 
                    _('Wammu configuration was not found. Gammu settings couldn\'t be read. You will now be taken to configuration dialog to confige Wammu.'),
                    _('Configuration not found'),
                    wx.OK | wx.ICON_WARNING).ShowModal()
                    
            # make some defaults
            if config['Model'] == None:
                config['Model'] = Wammu.Models[0]
            if config['Connection'] == None:
                config['Connection'] = Wammu.Connections[0]
            if config['Device'] == None:
                config['Device'] = Wammu.Devices[0]
            if not config['SyncTime'] == 'yes':
                config['SyncTime'] = 'no'
            if not config['LockDevice'] == 'yes':
                config['LockDevice'] = 'no'
            if not config['StartInfo'] == 'yes':
                config['StartInfo'] = 'no'

            self.cfg.Write('/Gammu/Model', config['Model'])
            self.cfg.Write('/Gammu/Device', config['Device'])
            self.cfg.Write('/Gammu/Connection', config['Connection'])
            self.cfg.Write('/Gammu/SyncTime', config['SyncTime'])
            self.cfg.Write('/Gammu/LockDevice', config['LockDevice'])
            self.cfg.Write('/Gammu/StartInfo', config['StartInfo'])

            self.Settings()

    def TogglePhoneMenus(self, enable):
        self.connected = enable
        if enable:
            self.SetStatusText(_('Connected'), 1)
        else:
            self.SetStatusText(_('Disconnected'), 1)
        mb = self.menuBar

        mb.Enable(201, not enable);
        mb.Enable(202, enable);
        
        mb.Enable(210, enable);

        mb.Enable(301, enable);

        mb.Enable(310, enable);
        mb.Enable(311, enable);
        mb.Enable(312, enable);
        
        mb.Enable(320, enable);
        
        mb.Enable(330, enable);
        
        mb.Enable(340, enable);
        
        mb.Enable(401, enable);

    def ActivateView(self, k1, k2):
        self.tree.SelectItem(self.treei[k1][k2])
        self.ChangeView(k1, k2)

    def ChangeView(self, k1, k2):
        self.ChangeBrowser(k1, k2)
        self.label.SetLabel(displaydata[k1][k2][2])

    def ChangeBrowser(self, k1, k2):
        self.type = [k1, k2]
        if k2 == '  ':
            data = []
            for k3, v3 in self.values[k1].iteritems():
                if k3 != '__':
                    data = data + v3
            self.values[k1]['__'] = data
            self.browser.Change(k1, data)
        else:
            self.browser.Change(k1, self.values[k1][k2])

    def OnTreeSel(self, event):
        item = event.GetItem()
        for k1, v1 in self.treei.iteritems():
            for k2, v2 in v1.iteritems():
                if v2 == item:
                    self.ChangeView(k1, k2)

    def Settings(self, event = None):
        import Wammu.Settings
        if Wammu.Settings.Settings(self, self.cfg).ShowModal() == wx.ID_OK and self.connected:
            wx.MessageDialog(self, 
                _('If you changed parameters affecting phone connection, they will be used next time you connect to phone.'),
                _('Notice'),
                wx.OK | wx.ICON_INFORMATION).ShowModal()

    def CloseWindow(self, event):
        # tell the window to kill itself
        self.Destroy()

    def ShowError(self, info):
        evt = Wammu.Events.ShowMessageEvent(
            message = _('Got error from phone:\n%s\nIn:%s\nError code: %d') % (info['Text'], info['Where'], info['Code']),
            title = _('Error Occured'),
            type = wx.ICON_ERROR)
        wx.PostEvent(self, evt)

    def ShowProgress(self, text):
        self.progress = wx.ProgressDialog(
                        _('Operation in progress'),
                        text,
                        100,
                        self,
                        wx.PD_CAN_ABORT | wx.PD_APP_MODAL | wx.PD_AUTO_HIDE | wx.PD_ELAPSED_TIME | wx.PD_REMAINING_TIME | wx.PD_ESTIMATED_TIME)

    def OnData(self, evt):
        self.values[evt.type[0]][evt.type[1]] = evt.data
        if evt.last and hasattr(self, 'nextfun'):
            f = self.nextfun
            a = self.nextarg
            del self.nextfun
            del self.nextarg
            f (*a)

    def ShowData(self, data):
        text = ''
        for d in data:
            if len(d) == 2:
                text = text + ('<b>%s</b>: %s<br>' % (d[0], d[1]))
            else:
                text = text + ('<br>%s' % d[0])
        self.content.SetPage('<body><html>%s</html></body>' % text)
        
            
    def OnShow(self, evt): 
        if self.type == ['info','  ']:
            data = [self.values['info']['__'][evt.index]]
        elif self.type[0] == 'memory' or self.type[0] == 'call':
            if self.type[1] == '  ':
                t = '__'
            else:
                t = self.type[1]
            v = self.values[self.type[0]][t][evt.index]
            data = [
                (_('Location'), str(v['Location'])),
                (_('Memory type'), v['MemoryType'])]
            for i in v['Values']:
                data.append((i['Type'], str(i['Value'])))
        elif self.type[0] == 'message':
            text = ''
            if self.type[1] == '  ':
                t = '__'
            else:
                t = self.type[1]
            v = self.values[self.type[0]][t][evt.index]
            data = [
                (_('Number'), str(v['Number'])),
                (_('Date'), str(v['DateTime'])),
                (_('Location'), str(v['Location'])),
                (_('Folder'), str(v['Folder'])),
                (_('Memory'), v['Memory']),
                (_('SMSC'), v['SMSCNumber']),
                (_('State'), v['State']),
                (v['Text'],)]
        elif self.type[0] == 'todo':
            if self.type[1] == '  ':
                t = '__'
            else:
                t = self.type[1]
            v = self.values[self.type[0]][t][evt.index]
            data = [
                (_('Location'), str(v['Location'])),
                (_('Priority'), v['Priority'])]
            for i in v['Values']:
                data.append((i['Type'], str(i['Value'])))
        else:
            data = [('Show not yet implemented! (id = %d)' % evt.index,)]
        self.ShowData(data)

    def NewContact(self, evt):
        import Wammu.Editor
        v = {}
        if Wammu.Editor.ContactEditor(self, self.sm, v).ShowModal() == wx.ID_OK:
            busy = wx.BusyInfo(_('Creating memory entry...'))
            # do the change
            try:
                v['Location'] = self.sm.AddMemory(v)

                # reread entry (it doesn't have to contain exactly same data as entered, it depends on phone features)
                v = self.sm.GetMemory(v['MemoryType'], v['Location'])
                Wammu.Utils.ParseMemoryEntry(v)
                self.values['memory'][v['MemoryType']].append(v)
                
            except gammu.GSMError, val:
                self.ShowError(val[0])
                
            self.ActivateView('memory', v['MemoryType'])

    def OnEdit(self, evt): 
        if self.type[0] == 'memory':
            import Wammu.Editor
            if self.type[1] == '  ':
                t = '__'
            else:
                t = self.type[1]
            v = self.values[self.type[0]][t][evt.index]
            backup = copy.deepcopy(v)
            if Wammu.Editor.ContactEditor(self, self.sm, v).ShowModal() == wx.ID_OK:
                busy = wx.BusyInfo(_('Updating memory entry...'))
                # do the change
                try:
                    if v['MemoryType'] != backup['MemoryType']:
                        self.sm.DeleteMemory(backup['MemoryType'], backup['Location'])
                        v['Location'] = self.sm.AddMemory(v)
                        # delete item from current list:
                        if backup['MemoryType'] == t:
                            del self.values[self.type[0]][t][evt.index]
                        else:
                            # we are showing merged list, delete just from the original
                            for idx in self.values[self.type[0]][backup['MemoryType']].keys():
                                if self.values[self.type[0]][backup['MemoryType']][idx] == v:
                                    del self.values[self.type[0]][backup['MemoryType']][idx]
                                    break
                        self.values[self.type[0]][v['MemoryType']].append(v)
                        t = v['MemoryType']
                    else:
                        v['Location'] = self.sm.SetMemory(v)

                    # reread entry (it doesn't have to contain exactly same data as entered, it depends on phone features)
                    v = self.sm.GetMemory(v['MemoryType'], v['Location'])
                    Wammu.Utils.GetMemoryEntryName(v)
                    Wammu.Utils.GetMemoryEntryNumber(v)
                except gammu.GSMError, val:
                    v = backup
                    self.ShowError(val[0])
                    
                if t == '__':
                    t = '  '
                    
                self.ActivateView('memory', t)
        else: 
            print 'Edit not yet implemented!'
            print evt.index

    def OnDelete(self, evt): 
        # FIXME: add here confirmation?
        if self.type[0] == 'memory' or self.type[0] == 'call':
            if self.type[1] == '  ':
                t = '__'
            else:
                t = self.type[1]
            v = self.values[self.type[0]][t][evt.index]
            try:
                self.sm.DeleteMemory(v['MemoryType'], v['Location'])
                if v['MemoryType'] == t:
                    del self.values[self.type[0]][t][evt.index]
                else:
                    # we are showing merged list, delete just from the original
                    for idx in range(len(self.values[self.type[0]][v['MemoryType']])):
                        if self.values[self.type[0]][v['MemoryType']][idx] == v:
                            del self.values[self.type[0]][v['MemoryType']][idx]
                            break
            except gammu.GSMError, val:
                self.ShowError(val[0])

            if t == '__':
                t = '  '
            self.ActivateView(self.type[0], t)
        elif self.type[0] == 'message':
            if self.type[1] == '  ':
                t = '__'
            else:
                t = self.type[1]
            v = self.values[self.type[0]][t][evt.index]
            try:
                # FIXME: 0 folder is safe for AT, but I'm not sure with others
                self.sm.DeleteSMS(0, v['Location'])
                if v['S'] == t:
                    del self.values[self.type[0]][t][evt.index]
                else:
                    # we are showing merged list, delete just from the original
                    for idx in range(len(self.values[self.type[0]][v['S']])):
                        if self.values[self.type[0]][v['S']][idx] == v:
                            del self.values[self.type[0]][v['S']][idx]
                            break
            except gammu.GSMError, val:
                self.ShowError(val[0])

            if t == '__':
                t = '  '
            self.ActivateView(self.type[0], t)
        elif self.type[0] == 'todo':
            if self.type[1] == '  ':
                t = '__'
            else:
                t = self.type[1]
            v = self.values[self.type[0]][t][evt.index]
            try:
                self.sm.DeleteToDo(v['Location'])
                if '  ' == t:
                    del self.values[self.type[0]][t][evt.index]
                else:
                    # we are showing merged list, delete just from the original
                    for idx in range(len(self.values[self.type[0]]['  '])):
                        if self.values[self.type[0]]['  '][idx] == v:
                            del self.values[self.type[0]]['  '][idx]
                            break
            except gammu.GSMError, val:
                self.ShowError(val[0])

            if t == '__':
                t = '  '
            self.ActivateView(self.type[0], t)
        else: 
            print 'Delete not yet implemented!'
            print evt.index

    def OnLink(self, evt): 
        print 'Links not yet implemented!'
        print evt.link

    def OnProgress(self, evt): 
        if not self.progress.Update(evt.progress):
            try:
                evt.cancel()
            except:
                pass
        if (evt.progress == 100):
            self.progress.Destroy()
        try:
            evt.lock.release()
        except AttributeError:
            pass

    def OnShowMessage(self, evt): 
        try:
            if self.progress.IsShown():
                parent = self.progress
            else:
                parent = self
        except:
            parent = self

        dlg = wx.MessageDialog(self, 
            evt.message,
            evt.title,
            wx.OK | evt.type).ShowModal()
        try:
            evt.lock.release()
        except AttributeError:
            pass

    def ShowInfo(self, event):
        self.ShowProgress(_('Reading phone information'))
        import Wammu.Info
        Wammu.Info.GetInfo(self, self.sm).start()
        self.nextfun = self.ActivateView
        self.nextarg = ('info', '  ')
       
    #
    # Calls
    #
   
    def ShowCalls(self, event):
        self.GetCallsType('MC')
        self.nextfun = self.ShowCalls2
        self.nextarg = ()
        
    def ShowCalls2(self):
        self.GetCallsType('DC')
        self.nextfun = self.ShowCalls3
        self.nextarg = ()
        
    def ShowCalls3(self):
        self.GetCallsType('RC')
        self.nextfun = self.ActivateView
        self.nextarg = ('call', '  ')
        
    def GetCallsType(self, type):
        self.ShowProgress(_('Reading calls of type %s') % type)
        import Wammu.Memory
        Wammu.Memory.GetMemory(self, self.sm, 'call', type).start()
        
    #
    # Contacts
    #

    def ShowContacts(self, event):
        self.GetContactsType('SM')
        self.nextfun = self.ShowContacts2
        self.nextarg = ()
        
    def ShowContacts2(self):
        self.GetContactsType('ME')
        self.nextfun = self.ActivateView
        self.nextarg = ('memory', '  ')

    def ShowContactsME(self, event):
        self.GetContactsType('ME')
        self.nextfun = self.ActivateView
        self.nextarg = ('memory', 'ME')
        
    def ShowContactsSM(self, event):
        self.GetContactsType('SM')
        self.nextfun = self.ActivateView
        self.nextarg = ('memory', 'SM')
        
    def GetContactsType(self, type):
        self.ShowProgress(_('Reading contacts from %s') % type)
        import Wammu.Memory
        Wammu.Memory.GetMemory(self, self.sm, 'memory', type).start()
        
    #
    # Messages
    #

    def ShowMessages(self, event):
        self.ShowProgress(_('Reading messages'))
        import Wammu.Message
        Wammu.Message.GetMessage(self, self.sm).start()
        self.nextfun = self.ActivateView
        self.nextarg = ('message', '  ')
        
    #
    # Todos
    #

    def ShowTodos(self, event):
        self.ShowProgress(_('Reading todos'))
        import Wammu.Todo
        Wammu.Todo.GetTodo(self, self.sm).start()
        self.nextfun = self.ActivateView
        self.nextarg = ('todo', '  ')
        
    #
    # Time
    #

    def SyncTime(self, event):
        busy = wx.BusyInfo(_('Setting time in phone...'))
        try:
            self.sm.SetDateTime(datetime.datetime.now())
        except gammu.GSMError, val:
            del busy
            self.ShowError(val[0])
    
    #
    # Connecting / Disconneting
    #

    def PhoneConnect(self, event):
        busy = wx.BusyInfo(_('One moment please, connecting to phone...'))
        cfg = {
            'StartInfo': self.cfg.Read('/Gammu/StartInfo', 'no'), 
            'UseGlobalDebugFile': 1, 
            'DebugFile': '/tmp/gammu.log', #FIXME
            'SyncTime': self.cfg.Read('/Gammu/SyncTime', 'no'), 
            'Connection': self.cfg.Read('/Gammu/Connection', Wammu.Connections[0]), 
            'LockDevice': self.cfg.Read('/Gammu/LockDevice', 'no'), 
            'DebugLevel': 'textall', #FIXME
            'Device': self.cfg.Read('/Gammu/Device', Wammu.Devices[0]), 
            'Localize': None,  #FIXME
            'Model': self.cfg.Read('/Gammu/Model', Wammu.Models[0])
            }
        self.sm.SetConfig(0, cfg)
        try:
            self.sm.Init()
            self.TogglePhoneMenus(True)
        except gammu.GSMError, val:
            del busy
            self.ShowError(val[0])
            try:
                self.sm.Terminate()
            except gammu.GSMError, val:
                pass
        
    def PhoneDisconnect(self, event):
        busy = wx.BusyInfo(_('One moment please, disconnecting from phone...'))
        try:
            self.sm.Terminate()
        except gammu.GSMError, val:
            del busy
            self.ShowError(val[0])
        self.TogglePhoneMenus(False)

