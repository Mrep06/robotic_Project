import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration

class ArmControlNode(Node):
    def __init__(self):
        super().__init__('arm_test_control')
        # สร้าง publisher ไปยัง topic ของ controller ที่ตั้งไว้ใน my_controllers.yaml
        self.publisher_ = self.create_publisher(JointTrajectory, '/arm_controller/joint_trajectory', 10)
        self.timer = self.create_timer(2.0, self.move_arm)
        self.state = 0

    def move_arm(self):
        msg = JointTrajectory()
        # รายชื่อ Joint ต้องตรงกับใน my_controllers.yaml
        msg.joint_names = ['arm_base2_joint', 'arm_slide_joint_L', 'arm_slide_joint_R']

        point = JointTrajectoryPoint()
        
        if self.state == 0:
            # ยืดแขนออก (อ้างอิง limit จาก robot_core.xacro)
            point.positions = [0.08, 0.2, -0.2] 
            self.get_logger().info('Moving Arm Out...')
            self.state = 1
        else:
            # หดแขนกลับเข้าหาศูนย์กลาง
            point.positions = [0.0, 0.0, 0.0]
            self.get_logger().info('Moving Arm to Home...')
            self.state = 0

        point.time_from_start = Duration(sec=2, nanosec=0)
        msg.points.append(point)
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = ArmControlNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.init()

if __name__ == '__main__':
    main()