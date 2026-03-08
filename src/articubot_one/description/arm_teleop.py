import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import sys, select, termios, tty

# กำหนดปุ่มควบคุม
msg = """
Control Your Arm!
---------------------------
Moving Base2 (Up/Down):
    w : Up (+0.01)
    s : Down (-0.01)

Moving Slides (L/R):
    a : Slide In (+0.01)
    d : Slide Out (-0.01)

space or k : Force Stop (Reset to 0)
CTRL-C to quit
"""

class ArmTeleop(Node):
    def __init__(self):
        super().__init__('arm_teleop')
        self.publisher_ = self.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)
        
        # ค่าเริ่มต้นของแต่ละ Joint
        self.base2_pos = 0.0
        self.slide_pos = 0.0
        
        # ขีดจำกัดจากไฟล์ robot_core.xacro
        self.base2_limit = [0.0, 0.2] #
        self.slide_limit = [0.0, 0.25375] #

    def send_command(self):
        trajectory_msg = JointTrajectory()
        trajectory_msg.joint_names = ['arm_base2_joint', 'arm_slide_joint_L', 'arm_slide_joint_R'] #

        point = JointTrajectoryPoint()
        # คำนวณตำแหน่ง: Slide R จะมีค่าเป็นลบเสมอตามลิมิตใน xacro (-0.235 ถึง 0)
        point.positions = [self.base2_pos, self.slide_pos, -self.slide_pos]
        point.time_from_start = Duration(sec=0, nanosec=100000000) # เคลื่อนที่เร็ว (0.1 วินาที)
        
        trajectory_msg.points.append(point)
        self.publisher_.publish(trajectory_msg)

def get_key(settings):
    tty.setraw(sys.stdin.fileno())
    select.select([sys.stdin], [], [], 0.1)
    key = sys.stdin.read(1)
    termios.tcsetattr(sys.stdin, sys.stdin.fileno(), settings)
    return key

def main():
    settings = termios.tcgetattr(sys.stdin)
    rclpy.init()
    node = ArmTeleop()
    
    print(msg)
    
    try:
        while True:
            key = get_key(settings)
            if key == 'w':
                node.base2_pos = min(node.base2_limit[1], node.base2_pos + 0.01)
            elif key == 's':
                node.base2_pos = max(node.base2_limit[0], node.base2_pos - 0.01)
            elif key == 'a':
                node.slide_pos = min(node.slide_limit[1], node.slide_pos + 0.01)
            elif key == 'd':
                node.slide_pos = max(node.slide_limit[0], node.slide_pos - 0.01)
            elif key in [' ', 'k']:
                node.base2_pos = 0.0
                node.slide_pos = 0.0
            elif key == '\x03': # CTRL-C
                break
            
            if key != '':
                node.send_command()
                print(f"Current Pos -> Base2: {node.base2_pos:.2f}, Slide: {node.slide_pos:.2f}", end='\r')

    except Exception as e:
        print(e)
    finally:
        node.destroy_node()
        rclpy.shutdown()
        termios.tcsetattr(sys.stdin, sys.stdin.fileno(), settings)

if __name__ == '__main__':
    main()