
import wx
import comm
import wii

import numpy as np
from matplotlib import pyplot as pp

EVT_NXT_SAMPLE_type = wx.NewEventType()
EVT_NXT_SAMPLE = wx.PyEventBinder(EVT_NXT_SAMPLE_type, 0)

EVT_NXT_STATUS_type = wx.NewEventType()
EVT_NXT_STATUS = wx.PyEventBinder(EVT_NXT_STATUS_type, 0)

class NxtWxDataEvent(wx.PyCommandEvent):
  def __init__(self, etype, data):
    super(NxtWxDataEvent,self).__init__(etype)
    self.data = data

class NxtSlamFrame(wx.Frame):
  def __init__(self, *args, **kwargs):
    super(NxtSlamFrame, self).__init__(*args, **kwargs)
    self.create_controls()
    self._create_new_comm_thread()
    self.wii = wii.WiiNxtController(self.comm_thread)

  def create_controls(self):
    v_sizer = wx.BoxSizer(wx.VERTICAL)

    #setup menu
    filemenu= wx.Menu()

    # wx.ID_ABOUT and wx.ID_EXIT are standard IDs provided by wxWidgets.
    self.menu_nxt_connect = filemenu.Append(100,"Nxt &Connect"," Connect to a brick")
    self.Bind(wx.EVT_MENU, self.OnMenuNxtConnect, self.menu_nxt_connect)

    self.menu_nxt_disconnect = filemenu.Append(101,"Nxt &Disconnect"," Disconnect from a brick")
    self.menu_nxt_disconnect.Enable(False)
    self.Bind(wx.EVT_MENU, self.OnMenuNxtDisconnect, self.menu_nxt_disconnect)

    menuexit = filemenu.Append(wx.ID_EXIT,"E&xit"," Terminate the program")
    self.Bind(wx.EVT_MENU, self.OnMenuExit, menuexit)

    #wii menu
    wiimenu = wx.Menu()
    self.menu_wii_connect = wiimenu.Append(200,"Wii &Connect"," Connect to a wii")
    self.Bind(wx.EVT_MENU, self.OnMenuWiiConnect, self.menu_wii_connect)

    self.menu_wii_disconnect = wiimenu.Append(201,"Wii &Disconnect"," Disconnect from a brick")
    self.menu_wii_disconnect.Enable(False)
    self.Bind(wx.EVT_MENU, self.OnMenuWiiDisconnect, self.menu_wii_disconnect)

    # Creating the menubar.
    menuBar = wx.MenuBar()
    menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
    menuBar.Append(wiimenu,"&Wii") # Adding the "filemenu" to the MenuBar
    self.SetMenuBar(menuBar)  # Adding th

    # create status bar
    self.sb = self.CreateStatusBar()

    #create main panel
    self.main_panel = wx.Panel(self)
    self.main_panel.SetSizer(v_sizer)

    #set up heading meter
    row_sizer = wx.BoxSizer(wx.HORIZONTAL)
    self._heading_label = wx.StaticText(self.main_panel,
                                        label="Heading:   ",
                                        style=wx.ALIGN_CENTRE)
    self._heading_meter = wx.StaticText(self.main_panel, label="0")
    row_sizer.Add(self._heading_label,1,)
    row_sizer.Add(self._heading_meter,1)
    v_sizer.Add(row_sizer)


    #set up distance meter
    row_sizer = wx.BoxSizer(wx.HORIZONTAL)
    self._distance_label = wx.StaticText(self.main_panel,
                                         label="US Distance:   ",
                                         style=wx.ALIGN_CENTRE)
    self._distance_meter = wx.StaticText(self.main_panel, label="0")
    row_sizer.Add(self._distance_label,1,)
    row_sizer.Add(self._distance_meter,1)
    v_sizer.Add(row_sizer)

    #set up color meter
    row_sizer = wx.BoxSizer(wx.HORIZONTAL)
    self._color_label = wx.StaticText(self.main_panel,
                                      label="Color:   ",
                                      style=wx.ALIGN_CENTRE)
    self._color_meter = wx.StaticText(self.main_panel, label="0")
    row_sizer.Add(self._color_label,1,)
    row_sizer.Add(self._color_meter,1)
    v_sizer.Add(row_sizer)

    #set up color meter
    row_sizer = wx.BoxSizer(wx.HORIZONTAL)
    self._left_tacho_label = wx.StaticText(self.main_panel,
                                           label="Left Tacho:   ",
                                           style=wx.ALIGN_CENTRE)
    self._left_tacho_meter = wx.StaticText(self.main_panel, label="0")
    row_sizer.Add(self._left_tacho_label,1,)
    row_sizer.Add(self._left_tacho_meter,1)
    v_sizer.Add(row_sizer)

    #set up color meter
    row_sizer = wx.BoxSizer(wx.HORIZONTAL)
    self._right_tacho_label = wx.StaticText(self.main_panel,
                                            label="Right Tacho:   ",
                                            style=wx.ALIGN_CENTRE)
    self._right_tacho_meter = wx.StaticText(self.main_panel, label="0")
    row_sizer.Add(self._right_tacho_label,1,)
    row_sizer.Add(self._right_tacho_meter,1)
    v_sizer.Add(row_sizer)

    #set up log filer picker
    row_sizer = wx.BoxSizer(wx.HORIZONTAL)
    self._log_file_picker_label = wx.StaticText(self.main_panel, label="Log file:   ")
    self._log_file_picker = wx.FilePickerCtrl(self.main_panel, 
                                              path="samples.pk",
                                              style=wx.FLP_SAVE | wx.FLP_USE_TEXTCTRL)
    self._start_logging_toggle = wx.ToggleButton(self.main_panel, label="Start Logging")
    self._start_logging_toggle.Enable(False)
    self.Bind(wx.EVT_TOGGLEBUTTON, self.OnStartLoggingToggle)
    row_sizer.Add(self._log_file_picker_label,1)
    row_sizer.Add(self._log_file_picker,1)
    row_sizer.Add(self._start_logging_toggle,1)
    v_sizer.Add(row_sizer)

    #setup nxt msg handlers
    self.Bind(EVT_NXT_SAMPLE, self.OnNxtSample)
    self.Bind(EVT_NXT_STATUS, self.OnNxtStatus)
    self.Bind(wx.EVT_CLOSE, self.OnClose)


  def OnMenuExit(self,evt):
    self.Close()

  def OnClose(self, evt):
    if self.comm_thread:
      try:
        self.comm_thread.disconnect()
      except:
        pass
      try:
        self.wii.disconnect()
      finally:
        self.comm_thread.join()
        self.Destroy()

  def OnMenuNxtConnect(self, evt):
    if not self.comm_thread.connected:
      self._create_new_comm_thread()

  def _create_new_comm_thread(self):
    self.comm_thread = comm.NxtSlamCommListenerThread(
      self.FireNxtSample, self.FireNxtStatus)
    self.comm_thread.start()
    self.sb.SetStatusText("Connecting...")
    self.menu_nxt_connect.Enable(False)
    try:
      self.wii.comm = self.comm_thread
    except: 
      pass

  def OnMenuNxtDisconnect(self, evt):
    if self.comm_thread.connected:
      try:
        self.comm_thread.disconnect()
      finally:
        self.comm_thread.join()

  def OnNxtStatus(self, evt):
    self.sb.SetStatusText(evt.data)
    if self.comm_thread.connected:
      self.menu_nxt_disconnect.Enable()
      self.menu_nxt_connect.Enable(False)
      self._start_logging_toggle.Enable()
    else:
      self.comm_thread.join()
      self.menu_nxt_disconnect.Enable(False)
      self.menu_nxt_connect.Enable()
      self._start_logging_toggle.Enable(False)

    if self.wii.connected:
      self.menu_wii_disconnect.Enable()
    else:
      self.menu_wii_connect.Enable()

  def OnNxtSample(self, evt):
    self._left_tacho_meter.SetLabel(str(evt.data[0]))
    self._right_tacho_meter.SetLabel(str(evt.data[1]))
    self._distance_meter.SetLabel(str(evt.data[2]))
    self._heading_meter.SetLabel(str(evt.data[3]))
    self._color_meter.SetLabel(str(evt.data[4]))

  def OnStartLoggingToggle(self, evt):
    if self.comm_thread.logging:
      self.comm_thread.stop_logging(filename = self._log_file_picker.GetPath())
      self._start_logging_toggle.SetLabel("Start Logging")
    else:
      self.comm_thread.start_logging()
      self._start_logging_toggle.SetLabel("Stop Logging")

  def OnMenuWiiConnect(self, evt):
    if not self.wii.connected:
      self.wii.connect_nonblocking(self.FireNxtStatus)
      self.menu_wii_connect.Enable(False)

  def OnMenuWiiDisconnect(self, evt):
    if self.wii.connected:
      try:
        self.wii.disconnect()
      finally:
        self.menu_wii_disconnect.Enable(False)

  def FireNxtSample(self, data):
    """Thread safe method to lauch a sample update"""
    evt = NxtWxDataEvent(EVT_NXT_SAMPLE_type, data)
    wx.PostEvent(self,evt)

  def FireNxtStatus(self, msg):
    """Thread safe method to lauch a status update"""
    evt = NxtWxDataEvent(EVT_NXT_STATUS_type, msg)
    wx.PostEvent(self,evt)

class NxtSlamGUI(wx.App):

  def OnInit(self):
    frame = NxtSlamFrame(None, title="Nxt Slam Gui")
    self.SetTopWindow(frame)
    frame.Show()
    return True

def draw_map(pf):
  """Draws a map using pyplot"""
  #TODO: integrate into main gui
  US = sum([np.exp(m)/(np.exp(m)+1) for m in pf.us_map_particles]) 

  RP = np.array([
    (p.x,p.y) for p in pf.pose_particles
  ]) 
  RN = np.array([ 
    p.norm_vector() for p in pf.pose_particles 
  ])
  
  pp.clf()
  pp.imshow(np.transpose(US), 
            cmap = pp.cm.gray, 
            origin='lower',
            #interpolation = 'nearest'
            )

  pp.quiver(RP[:,0],RP[:,1],RN[:,0],RN[:,1], color=[1.0,0,0] )
  pp.draw()

if __name__ == "__main__":
  app = NxtSlamGUI()
  app.MainLoop()
