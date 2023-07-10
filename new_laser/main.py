#!/usr/bin/python3

# 导入相关库
from connect import Lc12s
from catch import Detector
import cv2
from enum import Enum
# https://zhuanlan.zhihu.com/p/494394714 枚举模块enum
from catch import WebcamStream


# 枚举处理端状态
class Status(Enum):
    IDLE = 0  # 空闲态
    ENROLL_WEB = 1  # 注册网关
    GUN_ENROLL = 2  # 枪抢占
    QUIT = 4  # 退出
    CONFIRM_QUIT = 5  # 确认退出态\


# 枚举事件
class Event(Enum):
    NULL = 0  # 无事件
    ENROLL = 1  # 注册事件
    GUN_ENROLL = 2
    QUIT = 3  # 关闭摄像头
    SEND_CURVE = 4  # 发送轨迹信息
    SEND_POINT = 5  # 发送击中坐标信息


class Core(object):
    def __init__(self,
                 wireless: any,
                 detect: any,
                 status: any,
                 event: any) -> None:
        self.wireless = wireless
        self.detect = detect
        self.framerate = 40
        self.size = (480, 480)

        self.status = status
        self.event = event
        self.count = 0
        self.dis_10 = 100
        self.dis_9 = 160
        self.dis_8 = 200
        self.dis_7 = 224
        self.dis_6 = 240
        self.webcam_stream = WebcamStream(stream_id=0)  # stream_id = 0 is for primary camera

    def get_action(self) -> None:
        # 接收信息
        self.wireless.recv()
        # 处理信息
        self.wireless.handle_message()

    # 有限状态机
    def recv_fsm(self) -> None:
        self.get_action()
        while 1:
            # print(self.status)
            # 当状态为 空闲态时
            if self.status == Status.IDLE:
                # 如果已注册靶箱，则将其设置为假，将状态更改为注册网关，将事件更改为无事件，并将计数器重置为0。
                if self.wireless.target_enroll:
                    self.wireless.target_enroll = False
                    self.status = Status.ENROLL_WEB
                    self.event = Event.NULL
                    self.count = 0
                    print("confirm target enroll")
                # 否则，状态保持为 空闲态，事件保持为无事件，并且计数器递增。
                else:
                    self.status = Status.IDLE
                    self.event = Event.NULL
                    self.count = self.count + 1
                    # 如果计数器能被5整除，则调用无线对象的enroll方法(注册)。
                    if self.count % 5 == 0:
                        print("target enroll")
                        self.status = Status.IDLE
                        self.event = Event.NULL
                        self.count = 0
                        self.wireless.enroll()
                break
            # 当状态为注册网关时
            if self.status == Status.ENROLL_WEB:
                # 如果接收到枪注册，则将状态更改为枪注册，将事件更改为枪注册，并将计数器重置为0。
                if self.wireless.receive_enroll_flag:  # enroll ack
                    # 否则，状态保持为注册网关，事件保持为无事件，并且计数器递增。
                    self.status = Status.GUN_ENROLL  # gun enroll
                    self.event = Event.GUN_ENROLL
                    self.count = 0
                else:
                    # print("wait for gun")
                    self.status = Status.ENROLL_WEB
                    self.event = Event.NULL
                    self.count = self.count + 1
                    if self.count > 600:
                        # 如果计数器大于600，则打印“超时”。
                        print("timeout ")
                    self.count = 0
                break
            # 当状态为 枪注册 时
            if self.status == Status.GUN_ENROLL:
                # gun enroll
                # print("gun enroll")
                if self.wireless.receive_data_flag:
                    # 如果接收到数据,
                    # 则确认收到来自网络的设置信息, 并将 receive_data_flag（收到数据）设置为假
                    self.wireless.core_web_flag = True
                    self.wireless.receive_data_flag = False
                if self.wireless.receive_quit_flag:
                    # 如果退出, 则打印 “gun quit request”, 将其设置为假,
                    # 将状态更改为 注册网关, 将事件更改为 退出, 并将计数器重置为0
                    print("gun quit request")
                    self.wireless.receive_quit_flag = False
                    self.status = Status.ENROLL_WEB
                    self.event = Event.QUIT
                    self.count = 0
                    break
                if self.wireless.core_web_flag and self.detect.open_flag:
                    # 如果收到来自网络的设置信息和检测对象的 open_flag 都为真, 则状态保持不变, 事件更改为 发送轨迹信息,
                    # 并将core_web_flag（收到来自网络的设置信息） 设置为假
                    self.status = Status.GUN_ENROLL
                    self.event = Event.SEND_POINT
                    self.wireless.core_web_flag = False
                elif self.detect.open_flag:
                    # 检测对象的 open_flag 为真, 则状态保持不变, 事件更改为 发送击中坐标信息, 并将计数器重置为0.
                    if self.detect.open_flag:
                        self.status = Status.GUN_ENROLL
                        self.event = Event.SEND_CURVE
                        self.count = 0
                # enroll
                break
            else:
                break

    # 调用有限状态机来更新状态和事件实例变量
    # 如果事件不是上述任何一种，则将事件更改为 无事件
    def event_handle(self) -> None:
        self.recv_fsm()
        # print(self.event)
        while 1:
            if self.event == Event.GUN_ENROLL:
                # 当事件为枪注册时，将open_flag设置为真，将事件更改为无事件，并打印“open camera”。
                self.detect.open_flag = True
                self.event = Event.NULL
                print("open camera")
                break
            if self.event == Event.QUIT:
                # 当事件为退出时，将open_flag属性设置为假，将receive_quit_flag和receive_enroll_flag（退出和注册）属性设置为假，
                # 关闭所有OpenCV窗口，停止网络摄像头流，将事件更改为无事件，并打印“close camera”。
                self.wireless.open_flag = False
                self.wireless.receive_quit_flag = False
                self.wireless.receive_enroll_flag = False
                cv2.destroyAllWindows()
                self.webcam_stream.stop()  # stop the webcam stream
                # self.webcam_stream.vcap.release()
                self.event = Event.NULL
                print("close camera")
                break
            if self.event == Event.SEND_CURVE:
                # 当事件为 发送轨迹信息 时, 如果网络摄像头流已停止, 则退出循环.
                if self.webcam_stream.stopped is True:
                    break
                else:
                    # 否则, 从网络摄像头流中读取一帧图像, 并使用mask 方法处理图像. 然后更新检测结果
                    frame = self.webcam_stream.read()
                self.detect.mask(0x00, frame)
                mes = self.detect.update(0x00)
                if self.detect.update_flag:
                    # 如果已更新, 则将其设置为假, 调用hit发送击中信息, 并将事件更改为 无事件.
                    self.detect.update_flag = 0
                    self.wireless.hit(0x00, mes[0], mes[1], mes[2], mes[3], mes[4], mes[5], mes[6], mes[7])
                    self.event = Event.NULL
                break
            elif self.event == Event.SEND_POINT:
                # 当事件为 发送击中点  时, 如果网络摄像头流已停止, 则退出循环
                if self.webcam_stream.stopped is True:
                    break
                else:
                    # 否则, 从网络摄像头流中读取一帧图像, 并使用mask 方法处理图像. 然后更新检测结果
                    frame = self.webcam_stream.read()
                self.detect.mask(0x01, frame)
                mes = self.detect.update(0x01)
                if self.detect.update_flag:
                    # 如果已更新, 则将其设置为假, 调用 hit 发送击中信息, 并将事件更改为 无事件
                    self.detect.update_flag = 0
                    self.wireless.hit(0x01, mes[0], mes[1], mes[2], mes[3], mes[4], mes[5], mes[6], mes[7])
                    self.event = Event.NULL
                break
            else:
                self.event = Event.NULL
                break


lc12s = Lc12s(9600, 25, 0x01, 0xc8, 0x00, 0x0C, 0x1E, 0x14, 0X12)
camera = Detector(False)
axis = []


def main() -> None:
    core = Core(lc12s, camera, Status.IDLE, Event.NULL)
    core.webcam_stream.start()
    # processing frames in input stream
    while True:
        core.event_handle()


# 主程序部分
if __name__ == '__main__':
    main()
