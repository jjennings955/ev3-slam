from Tkinter import *
from map_canvas import *
import rpyc
from nxtslam.state import Odometry, Pose
from nxtslam.models import MotionModel

pose = Pose(0, 0, -3.14)
odometry = Odometry(0, 0)
#motionModel = MotionModel(wheel_circ=0.55*3.14, base_circ=1.2)
#motionModel = MotionModel(wheel_circ=0.055*100, base_circ=0.12*100)
motionModel = MotionModel(wheel_circ=9.0, base_circ=6.0)

root = Tk()
conn = rpyc.classic.connect('192.168.137.3')
ev3 = conn.modules.ev3
Motor = ev3.ev3dev.Motor
right = Motor(Motor.PORT.A)
left = Motor(Motor.PORT.B)
left.position = 0
right.position = 0
left.regulation_mode = True
right.regulation_mode = True
SPEED = 200
def key(event):
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
    global map, rectangle, pose, odometry

    newOdometry = Odometry(left.position/360.0, right.position/360.0)
    dOdometry = newOdometry - odometry
    if not(dOdometry.left == 0 and dOdometry.right == 0):
        print("Position", (left.position, ' ', right.position))
        print('Before:' + repr(pose))
        print(dOdometry)
        pose = motionModel.compute_motion(pose, newOdometry - odometry)
        odometry = newOdometry
    global rectangle
    if not rectangle:
        print(pose)
        rectangle = map.canvas.create_rectangle(400 - pose.y, 600 - 100 + pose.x, 400 - pose.y + 100, 600 - 100 + pose.x + 100, fill="blue")
        print(rectangle)
    else:

        map.canvas.coords(rectangle, (400 - pose.y * 100, 600 - 100 + pose.x * 100, 400 - pose.y * 100 + 100, 600 - 100 + pose.x * 100 + 100))
    root.after(1000, update_position)

def up(event):

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
