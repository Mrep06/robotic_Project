import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
from linkattacher_msgs.srv import AttachLink, DetachLink 
import sys, select, termios, tty

msg = """
Control Your Robot and Arm!
---------------------------
Moving Robot (Base):        Moving Arm (Lift/Grip):
    w : Forward                 i : Arm Up (+0.01)
    s : Backward                k : Arm Down (-0.01)
    a : Left                    j : Slide In (+0.01)
    d : Right                   l : Slide Out (-0.01)

Plugin (Grasp):
    c : Attach Object (จับวัตถุ)
    v : Detach Object (ปล่อยวัตถุ)

space or x : Stop All (Robot & Arm)
CTRL-C to quit
"""

class CombinedTeleop(Node):
    def __init__(self):
        super().__init__('combined_teleop')
        self.wheel_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.arm_pub = self.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)
        
        # ยืนยันชื่อ Service ตามที่เช็คจาก ros2 service list
        self.attach_cli = self.create_client(AttachLink, '/ATTACHLINK')
        self.detach_cli = self.create_client(DetachLink, '/DETACHLINK')
        
        self.base2_pos = 0.0
        self.slide_pos = 0.0
        self.base2_limit = [0.0, 0.2]
        self.slide_limit = [0.0, 0.25375]

    def send_arm_command(self):
        trajectory_msg = JointTrajectory()
        trajectory_msg.joint_names = ['arm_base2_joint', 'arm_slide_joint_L', 'arm_slide_joint_R']
        point = JointTrajectoryPoint()
        point.positions = [self.base2_pos, self.slide_pos, -self.slide_pos]
        point.time_from_start = Duration(sec=0, nanosec=200000000) # 0.2 sec
        trajectory_msg.points.append(point)
        self.arm_pub.publish(trajectory_msg)

    def send_wheel_command(self, linear, angular):
        twist = Twist()
        twist.linear.x = linear
        twist.angular.z = angular
        self.wheel_pub.publish(twist)

    def attach_object(self):
        # เพิ่มเวลารอเป็น 5 วินาที
        if not self.attach_cli.wait_for_service(timeout_sec=5.0):
            self.get_logger().error('Service /ATTACHLINK ยังไม่ตอบสนอง!')
            return
            
        req = AttachLink.Request()
        req.model1_name = 'robot779'      
        req.link1_name = 'arm_link_L'    
        req.model2_name = 'box_final1'    
        req.link2_name = 'link' # <--- ถ้ากดแล้วไม่ติด ให้ลองแก้เป็น 'link_1' หรือเช็คใน Gazebo
        
        self.get_logger().info('Sending Attach Request...')
        self.attach_cli.call_async(req)

    def detach_object(self):
        if not self.detach_cli.wait_for_service(timeout_sec=5.0):
            self.get_logger().error('Service /DETACHLINK ยังไม่ตอบสนอง!')
            return
            
        req = DetachLink.Request()
        req.model1_name = 'robot779'
        req.link1_name = 'arm_link_L'
        req.model2_name = 'box_final1'
        req.link2_name = 'link'
        
        self.get_logger().info('Sending Detach Request...')
        self.detach_cli.call_async(req)

# --- ส่วนควบคุม Keyboard (เหมือนเดิม) ---
def get_key(settings):
    tty.setraw(sys.stdin.fileno())
    rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
    if rlist:
        key = sys.stdin.read(1)
    else:
        key = ''
    termios.tcsetattr(sys.stdin, sys.stdin.fileno(), settings)
    return key

def main():
    settings = termios.tcgetattr(sys.stdin)
    rclpy.init()
    node = CombinedTeleop()
    
    try:
        while True:
            key = get_key(settings)
            if key == 'w': node.send_wheel_command(0.5, 0.0)
            elif key == 's': node.send_wheel_command(-0.5, 0.0)
            elif key == 'a': node.send_wheel_command(0.0, 1.0)
            elif key == 'd': node.send_wheel_command(0.0, -1.0)
            elif key == 'i':
                node.base2_pos = min(node.base2_limit[1], node.base2_pos + 0.01)
                node.send_arm_command()
            elif key == 'k':
                node.base2_pos = max(node.base2_limit[0], node.base2_pos - 0.01)
                node.send_arm_command()
            elif key == 'j':
                node.slide_pos = min(node.slide_limit[1], node.slide_pos + 0.01)
                node.send_arm_command()
            elif key == 'l':
                node.slide_pos = max(node.slide_limit[0], node.slide_pos - 0.01)
                node.send_arm_command()
            elif key == 'c': node.attach_object()
            elif key == 'v': node.detach_object()
            elif key in [' ', 'x']:
                node.send_wheel_command(0.0, 0.0)
                node.send_arm_command()
            elif key == '\x03': break
            
            if key != '':
                print(f"\rPos -> Base2: {node.base2_pos:.2f}, Slide: {node.slide_pos:.2f} | Key: {key}    ", end='')

    except Exception as e:
        print(f"\nError: {e}")
    finally:
        node.destroy_node()
        rclpy.shutdown()
        termios.tcsetattr(sys.stdin, sys.stdin.fileno(), settings)

if __name__ == '__main__':
    main()