__author__ = 'jason'
from Tkinter import *
class MapCanvas(object):
    def __init__(self, master):
        self.master = master
        self.canvas = Canvas(master, width=800, height=600, background='black')

        self.canvas.pack()
