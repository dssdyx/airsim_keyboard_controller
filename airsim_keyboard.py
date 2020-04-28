import curses
import math
import time
import airsim


class TextWindow():

    _screen = None
    _window = None
    _num_lines = None

    def __init__(self, stdscr, lines=10):
        self._screen = stdscr
        self._screen.nodelay(True)
        curses.curs_set(0)

        self._num_lines = lines

    def read_key(self):
        keycode = self._screen.getch()
        return keycode if keycode != -1 else None

    def clear(self):
        self._screen.clear()

    def write_line(self, lineno, message):
        if lineno < 0 or lineno >= self._num_lines:
            raise ValueError, 'lineno out of bounds'
        height, width = self._screen.getmaxyx()
        y = (height / self._num_lines) * lineno
        x = 10
        for text in message.split('\n'):
            text = text.ljust(width)
            self._screen.addstr(y, x, text)
            y += 1

    def refresh(self):
        self._screen.refresh()

    def beep(self):
        curses.flash()

class SimpleKeyTeleop():
    def __init__(self, interface):
        self._interface = interface

        self._last_pressed = {}
        self._client =  airsim.MultirotorClient()
        self._client.confirmConnection()
        self._client.enableApiControl(True)
        self._px4_cmd= 'undo'

    movement_bindings = {
        curses.KEY_UP:'Forward',
        curses.KEY_DOWN:'Backward',
        curses.KEY_LEFT:'Left',
        curses.KEY_RIGHT:'Right',
        ord('s'):'Down',
        ord(' '):'Up',
        ord('a'):'Arm',
        ord('t'):'Takeoff',
        ord('l'):'Land',
        ord('z'):'TurnLeft',
        ord('c'):'TurnRight',
        ord('x'):'Hover',
    }

    def run(self):
        self._running = True
        while self._running:
            while True:
                keycode = self._interface.read_key()
                if keycode is None:
                    break
                self._key_pressed(keycode)
            self._set_velocity()
            self._publish()       


    def _key_pressed(self, keycode):
        if keycode == ord('q'):
            self._running = False
        elif keycode in self.movement_bindings:
            self._last_pressed[keycode] = time.time()


    def _set_velocity(self):
        now = time.time()
        keys = []
        for a in self._last_pressed:
            if now - self._last_pressed[a] < 0.4:
                keys.append(a)
        linear = 0.0
        angular = 0.0
        #self._px4_cmd = 'undo'
        self.pos = self._client.getMultirotorState().kinematics_estimated.position
        if self._px4_cmd == 'undo':
           self.origin_h =self.pos.z_val
        self.pitch, self.roll, self.yaw  = airsim.to_eularian_angles(self._client.getMultirotorState().kinematics_estimated.orientation)
        ##
        
        self.forward = (math.cos(self.yaw),math.sin(self.yaw)) 
        self.right = (-self.forward[1],self.forward[0])
        speed = 1
        for k in keys:
           self._px4_cmd = self.movement_bindings[k]
           ##
           if self._px4_cmd == 'Forward':
              self._client.moveByVelocityAsync(speed*self.forward[0],speed*self.forward[1],0,0.1,airsim.DrivetrainType.ForwardOnly,airsim.YawMode(True,0)).join()
           if self._px4_cmd == 'Backward':
              self._client.moveByVelocityAsync(-speed*self.forward[0],-speed*self.forward[1],0,0.1,airsim.DrivetrainType.ForwardOnly,airsim.YawMode(True,0)).join()
           if self._px4_cmd == 'Left':
              self._client.moveByVelocityAsync(-self.right[0],-self.right[1],0,0.1,airsim.DrivetrainType.ForwardOnly,airsim.YawMode(True,0)).join()
           if self._px4_cmd == 'Right':
              self._client.moveByVelocityAsync(self.right[0],self.right[1],0,0.1,airsim.DrivetrainType.ForwardOnly,airsim.YawMode(True,0)).join()
           if self._px4_cmd == 'Down':
              self._client.moveByVelocityAsync(0,0,0.3,0.1,airsim.DrivetrainType.ForwardOnly,airsim.YawMode(True,0)).join()
           if self._px4_cmd == 'Up':
              self._client.moveByVelocityAsync(0,0,-0.3,0.1,airsim.DrivetrainType.ForwardOnly,airsim.YawMode(True,0)).join()
           if self._px4_cmd == 'Arm':
              self._client.armDisarm(True)
           if self._px4_cmd == 'Takeoff':
              self._client.takeoffAsync().join()
           if self._px4_cmd == 'Land':
              self._client.landAsync().join()
           if self._px4_cmd == 'TurnLeft':
              self._client.rotateByYawRateAsync(-12,0.1).join()
           if self._px4_cmd == 'TurnRight':
              self._client.rotateByYawRateAsync(12,0.1).join()
           if self._px4_cmd == 'Hover':
              self._client.hoverAsync().join()
       
           
    def _publish(self):
        self._interface.write_line(2, 'cmd : %s' % (self._px4_cmd)) 
        self._interface.write_line(4, 'pos x : %f' % (self.pos.x_val))      
        self._interface.write_line(5, 'pox y : %f' % (self.pos.y_val)) 
        self._interface.write_line(6, 'pox z : %f' % (self.origin_h-self.pos.z_val))           
        self._interface.write_line(7, 'yaw : %f' % (self.yaw*180/math.pi))                                                                    





def main(stdscr):
    app = SimpleKeyTeleop(TextWindow(stdscr))
    app.run()

if __name__ == '__main__':
        curses.wrapper(main)

