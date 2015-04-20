#!/usb/bin/env python

import cwiid
import math
from threading import Thread

from time import time, sleep

class WiiNxtController(object):

  BTN_EVENTS = {
    0: { 
      'stop': ()
    },
    cwiid.BTN_UP: { 
      'drive_reg': (70,0)
    },
    cwiid.BTN_DOWN: { 
      'drive_reg': (-70,0)
    },
    cwiid.BTN_LEFT: { 
      'drive_reg': (70,67)
    },
    cwiid.BTN_RIGHT: { 
      'drive_reg': (70,-67)
    },
    cwiid.BTN_A: {
      'toggle_acc': ()
    },
    cwiid.BTN_B: {
      'quit': ()
    },
  }




  def __init__(self, nxt_comm):
    self.comm = nxt_comm

    self.last_motor_command = time()
    self.last_roll = 0
    self.last_pitch = 0
    self.connected = False


  def handle(self,msg_list,timestamp):
    for msg in msg_list:
      type, data = msg
      if type == 1 and data in self.BTN_EVENTS:
        actions = self.BTN_EVENTS[data]
        # for each function name and arguments
        for act,args in actions.iteritems():
          try:
            print "Executing %s with %s" %(act,repr(args))
            getattr(self,act)(*args)
          except Exception as e:
            print "Could not execute %s with %s" %(act,repr(args))
            print e
      elif type == 2:
        if ((time()-self.last_motor_command) > 0.05):
          roll,pitch = self.get_roll_pitch(data)

          diff_r = abs(self.last_roll - roll)
          diff_p = abs(self.last_pitch - pitch)

          if (diff_r > 0.2 or diff_p > 0.2):
            self.last_roll,self.last_pitch = roll, pitch
            power = roll/(math.pi/2)*40
            turn_ratio = max(-40,min(40,(pitch/(math.pi/2)*40)))

            left = power - turn_ratio
            right = power + turn_ratio

            if (left < 5):
              left = 0
            else:
              left = max(-100,min(100,(left + 60) *(left > 0)))

            if (right < 5):
              right = 0
            else:
              right = max(-100,min(100,(right + 60) *(right > 0)))

            self.drive_unreg((left,right))
            self.last_motor_command = time()

  def connect(self):
    self.disconnect()

    # do some setup
    self.wii = cwiid.Wiimote()
    self.wii.mesg_callback = self.handle
    self.call_zero,self.call_one = self.wii.get_acc_cal(cwiid.EXT_NONE)
    self.wii.rpt_mode = cwiid.RPT_BTN
    self.wii.enable(cwiid.FLAG_MESG_IFC)
    self.connected = True

  def connect_nonblocking(self, callback):
    Thread(target = lambda: self._connect_with_callback(callback)).start()

  def _connect_with_callback(self, callback):
    try:
      self.connect()
      callback("Connected to Wiimote")
    except Exception as e:
      callback(repr(e))

  def disconnect(self):
    try:
      if self.connected:
        self.wii.close()
    finally:
      self.connected = False

  def quit(self):
    try:
      self.comm.stop_motors()
      self.comm.disconnect()
    finally:
      self.disconnect()

  def toggle_acc(self):
    rpt_mode = self.wii.state['rpt_mode']
    self.wii.rpt_mode = rpt_mode ^ cwiid.RPT_ACC

  def get_roll_pitch(self,data):
    x,y,z = data
    #normalize acc data
    a_x = float(x - self.call_zero[0])/(self.call_one[0] - self.call_zero[0])
    a_y = float(y - self.call_zero[1])/(self.call_one[1] - self.call_zero[1])
    a_z = float(z - self.call_zero[2])/(self.call_one[2] - self.call_zero[2])

    if (a_z != 0):
      roll = math.atan(float(a_x)/a_z)
    else:
      roll = math.pi/2

    if (a_z <= 0):
      roll += math.pi * math.copysign(1,a_x)

    if (a_z != 0):
      pitch = math.atan(float(a_y)/a_z)
    else:
      pitch = math.pi/2

    if (a_z <= 0):
      pitch += math.pi * math.copysign(1,a_y)

    return roll,pitch

  def drive_unreg(self, motor_power):
    self.comm.drive_unreg(motor_power)

  def drive_reg(self, power, turn_ratio):
    self.comm.drive_reg(power, turn_ratio)

  def stop(self):
    self.comm.stop_motors()

