from Tkinter import *
from map_canvas import *
import rpyc
from nxtslam.state import Odometry, Pose
from nxtslam.models import MotionModel
from nxtslam.particle_filter import NxtSlamParticleFilter
import math
import numpy as np
import itertools
NUM_PARTICLES = 50
particles = []
particle_obj = []
#class Particle:
#    def __init__(self, pose, odometry):
#        self.pose =

for i in range(NUM_PARTICLES):
    particles.append(Pose(0, 0, -3.14159/2))

map_mat = np.zeros((100, 100))
pose = Pose(0, 0, -3.14159/2)
particle_filter = NxtSlamParticleFilter(100, initial_pose=pose)
odometry = Odometry(0, 0)
#motionModel = MotionModel(wheel_circ=0.55*3.14, base_circ=1.2)
#motionModel = MotionModel(wheel_circ=0.055*100, base_circ=0.12*100)
motionModel = MotionModel(wheel_circ=.055/2.0, base_circ=.12)

root = Tk()
conn = rpyc.classic.connect('192.168.137.3')
ev3 = conn.modules.ev3
UltrasonicSensor = ev3.lego.UltrasonicSensor

Motor = ev3.ev3dev.Motor
right = Motor(Motor.PORT.A)
left = Motor(Motor.PORT.B)
sensor = conn.modules.test

previousAngle = sensor.get_angle()


left.position = 0
right.position = 0
left.regulation_mode = True
right.regulation_mode = True
SPEED = 250

def key(event):
    if event.char == '2':
        update_position()
    if event.char == '7':
        left.run_forever(speed_sp=SPEED)
    if event.char == '4':
        left.run_forever(speed_sp=-SPEED)
    if event.char == '9':
        right.run_forever(speed_sp=SPEED)
    if event.char == '6':
        right.run_forever(speed_sp=-SPEED)

    print "pressed", repr(event.char)
rectangle = None

def update_position():
    global map, rectangle, pose, odometry, previousAngle
    oldpose = pose
    newOdometry = Odometry(left.position*3.14159/180, right.position*3.14159/180)
    dist = sensor.get_dist()/1000.0
    angle = sensor.get_angle()
    print(dist)
    dOdometry = newOdometry - odometry
    if not(dOdometry.left == 0 and dOdometry.right == 0):
        #print("Position", (left.position, ' ', right.position))
        print('Before:' + repr(pose))
        for i, particle in enumerate(particles):
           map.canvas.coords(particle_obj[i], 400 - particle.y * 100, 600 - 100 + particle.x * 100, 400 - particle.y * 100 + 2, 600 - 100 + particle.x * 100 + 2)

        pose = motionModel.compute_motion(pose, newOdometry - odometry)
        for i in range(NUM_PARTICLES):
            dpose = motionModel.sample_given_odo(particles[i], newOdometry - odometry)
            particles[i] = dpose
        for i in range(NUM_PARTICLES):
            print(particles[i])

        #d_theta = angle - previousAngle
        #previousAngle = angle

        #pose.theta = (angle) % (2*3.14159)
        odometry = newOdometry
    global rectangle
    if not rectangle:
        rectangle = map.canvas.create_rectangle(400 - pose.y * 100, 600 - 100 + pose.x * 100, 400 - pose.y * 100 + 25, 600 - 100 + pose.x * 100 + 25, fill='red')
        for particle in particles:
            particle_obj.append(map.canvas.create_rectangle(400 - pose.y * 100, 600 - 100 + pose.x * 100, 400 - pose.y * 100 + 2, 600 - 100 + pose.x * 100 + 2, fill='yellow'))
        print(rectangle)
    else:
        #map.canvas.create_oval(400 - pose.y * 100 + 10.5, 600 - 100 + pose.x * 100 +10.5, 400 - pose.y * 100 + 13.5, 600 - 100 + pose.x * 100 +13.5, fill='red')
        #particle_filter.project_given_odometry(dOdometry)
        map.canvas.create_line(400 - oldpose.y * 100 + 2.5, 600 - 100 + oldpose.x * 100 + 2.5, 400 - pose.y * 100 + 2.5, 600 - 100 + pose.x * 100 + 2.5, fill='blue', dash=(2,2))

        map.canvas.coords(rectangle, (400 - pose.y * 100 - 5, 600 - 100 + pose.x * 100 - 5, 400 - pose.y * 100 + 5, 600 - 100 + pose.x * 100 + 5))
        if (dist > 0.07 and dist < 0.60):
            #particle_filter.update_given_obs(dist)
            dx = dist*math.cos(pose.theta)
            dy = dist*math.sin(pose.theta)
            x,y = (400 - (pose.y+dy) * 100 - 5, 600 - 100 + (pose.x + dx) * 100 - 5)
            map_mat[y//8, x//86] = 1
            map.canvas.create_rectangle((x//8)*8, y//8*8, x//8*8 + 8,  y//8*8 + 8, fill='gray')
            #map.canvas.create_rectangle((400 - (pose.y+dy) * 100 - 5, 600 - 100 + (pose.x + dx) * 100 - 5, 400 - (pose.y + dy) * 100 + 5, 600 - 100 + (pose.x + dx) * 100 + 5), fill='gray')

    root.after(100, update_position)

def up(event):
    if event.char == '8':
        sensor.move()
    if event.char == '2':
        sensor.move(forward=False)
    if event.char in '74':
        left.run_forever(speed_sp=0)

    if event.char in '96':
        right.run_forever(speed_sp=0)

def callback(event):
    frame.focus_set()
    print "clicked at", event.x, event.y

frame = Frame(root, width=800, height=600)
map = MapCanvas(frame)

for k in '7946':
    root.bind(k, key)
frame.bind("<Button-1>", callback)
frame.pack()
root.bind(k, key)
root.bind('<KeyRelease>', up)
if __name__ == "__main__":
    update_position()
    root.mainloop()
