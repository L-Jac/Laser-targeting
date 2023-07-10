#!/usr/bin/python3
import time
import cv2
from threading import Thread  # 用于实现多线程处理的库。https://www.runoob.com/python/python-multithreading.html
from scores import Score


class Detector(object):

    def __init__(self,
                 open_flag: any,
                 k_size: int = 5,
                 framerate: int = 15,
                 size_w: int = 480,
                 size_h: int = 480) -> None:

        self.open_flag = open_flag
        self.framerate = framerate
        self.k_size = k_size
        self.framerate_w = framerate
        self.size = (size_w, size_h)
        # camera init
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.videoWriter = cv2.VideoWriter('output.avi', fourcc, 30.0, self.size)
        self.center_list = []
        self.center = []
        self.center_x = 0
        self.center_y = 0
        self.frame_cnt = 1
        self.det_flag = 0
        # record 创建带有时间戳的文件夹和一个 CSV 文件，用于记录数据
        # 用 time.strftime 函数获取当前时间，并将其格式化为字符串，格式为“日_时-分-秒”
        self.dt = time.strftime("%d_%H-%M-%S", time.localtime())
        # 存储在 self.path
        self.path = self.dt + '/'
        # 用 open 函数以写入模式打开一个 CSV 文件，文件名为“centers_时间戳.csv”，
        self.lfp = open('centers_{}.csv'.format(self.dt), mode='w')
        # 在 CSV 文件的第一行写入标题“time, x, y”。
        self.lfp.write('time, x, y\n')
        # 记录处理的帧数
        self.frame_cnt = 0
        # score
        self.score = Score()
        self.aim_xlist = []
        self.aim_ylist = []
        self.shoot_xlist = []
        self.shoot_ylist = []
        self.aim_ring = 0
        self.shoot_ring = 0
        self.shake = 0
        self.shake_v = 0
        self.shoot_shake = 0
        self.shoot_shake_v = 0
        self.update_flag = 0

    # 所有点绘制轨迹
    def line(self, frame: any) -> None:
        for i in range(1, len(self.center_list)):
            if self.center_list[i - 1] is None or self.center_list[i] is None:
                continue
            # thickness = int(np.sqrt(64 / float(i + 1)) * 2.5)
            cv2.line(frame, self.center_list[i - 1], self.center_list[i], (0, 0, 255), 1, cv2.LINE_AA)

    # 每15个点绘制轨迹
    def short_line(self, frame: any) -> None:
        if 2 < len(self.center_list) < 15:
            for i in range(len(self.center_list) - 1):
                cv2.line(frame, self.center_list[i - 1], self.center_list[i], (0, 255, 0), 1, cv2.LINE_AA)
        elif len(self.center_list) > 15:
            for i in range(len(self.center_list) - 16, len(self.center_list) - 1):
                cv2.line(frame, self.center_list[i - 1], self.center_list[i], (0, 255, 0), 1, cv2.LINE_AA)

    # 追踪激光点
    def highlight(self, frame: any) -> None:
        if self.open_flag:
            self.frame_cnt = +1
            # 在帧的左上角添加文本，显示当前帧的编号。
            cv2.putText(frame, 'frame:{}'.format(self.frame_cnt), (0, 20), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 255, 255))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (7, 7), 0)
            thresh = cv2.threshold(gray, 170, 255, cv2.THRESH_BINARY)[1]
            cents = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 图像、轮廓和层次结构
            # 如果长度为 2，则表示使用的是 OpenCV 4，因此 cents[0] 包含轮廓信息。否则，表示使用的是 OpenCV 3，因此 cents[1] 包含轮廓信息。
            cents = cents[0] if len(cents) == 2 else cents[1]
            # 历找到的每个轮廓，大于10的表示检测到了物体self.det_flag 变量设置为 1，
            # 计算轮廓的几何中心，添加到 self.center_list 列表中，将中心坐标存储在 self.center 变量中
            for c in cents:
                if cv2.contourArea(c) > 10:
                    self.det_flag = 1
                    m = cv2.moments(c)
                    if m["m00"] != 0:
                        cx = int(m["m10"] / m["m00"])
                        cy = int(m["m01"] / m["m00"])
                        self.center_list.append((cx, cy))
                        self.center = [cx, cy]
                    else:
                        self.det_flag = 0
                else:
                    self.det_flag = 0

    # 获取有效中心坐标
    def get_center(self, frame: any) -> list | None:
        self.highlight(frame)
        if self.det_flag:
            return self.center
        else:
            return None

    def mask(self, flag: any, frame: any) -> None:
        self.highlight(frame)
        if self.det_flag:
            # 重置self.det_flag
            self.det_flag = 0
            # 储存中心坐标
            self.aim_xlist.append(self.center[0])
            self.aim_ylist.append(self.center[1])
            self.shoot_xlist.append(self.center[0])
            self.shoot_ylist.append(self.center[1])
            self.center_x = self.center[0]
            self.center_y = self.center[1]
            # 清空列表
            self.center = []

            # 计算一些得分(调用 self.score.aim_ring、self.score.shake 和 self.score.shake_v)
            self.aim_ring = self.score.aim_ring(self.aim_xlist, self.aim_ylist)
            self.shake = self.score.shake(self.aim_xlist, self.aim_ylist)
            self.shake_v = self.score.shake_v(self.aim_xlist, self.aim_ylist)
            # 如果识别为没脱靶，进一步计算其他分数
            if flag:
                self.shoot_ring = self.score.shoot_ring(self.center_x, self.center_y)
                self.shoot_shake = self.score.shoot_shake(self.shoot_xlist, self.shoot_ylist, self.center_x,
                                                          self.center_y)
                self.shoot_shake_v = self.score.shoot_shake_v(self.shoot_xlist, self.shoot_ylist, self.center_x,
                                                              self.center_y)
                self.shoot_xlist = []
                self.shoot_ylist = []
            # 处理的帧数超过 34，则清空 self.aim_xlist 和 self.aim_ylist 列表，并将帧计数器重置为 0。
            if self.frame_cnt > 34:
                self.aim_xlist = []
                self.aim_ylist = []
                self.frame_cnt = 0
            # self.shoot_xlist 列表的长度超过 100，则清空该列表和 self.shoot_ylist 列表
            if len(self.shoot_xlist) > 100:
                self.shoot_xlist = []
                self.shoot_ylist = []
            #
            self.update_flag = 1

    def update(self, flag: any) -> tuple[int, int, int, int, int, int, int, int]:
        if self.update_flag:
            # self.update_flag = 0
            # print(self.update_flag)
            # 返回成绩
            if flag:
                return self.aim_ring, self.shoot_ring, self.shake, self.shake_v, self.shoot_shake, self.shoot_shake_v, self.center_x, self.center_y
            else:
                return self.aim_ring, 0, self.shake, self.shake_v, 0, 0, self.center_x, self.center_y
        else:
            pass


# 实现多线程处理视频流可以用来在单独的线程中从视频流中读取帧，以便在主程序中进行实时处理。
class WebcamStream:

    def __init__(self, stream_id: int = 0) -> None:
        self.stream_id = stream_id  # stream_id=0使用计算机的主摄像头

        # opening video capture stream
        self.vcap = cv2.VideoCapture(self.stream_id)
        self.vcap.set(3, 640)  # 视频流的帧宽度设置为 640 像素。
        self.vcap.set(4, 480)  # 视频流的帧高度设置为 480 像素。
        self.vcap.set(cv2.CAP_PROP_FPS, 30)  # 频流的帧率设置为 30 帧/秒。
        # 检查视频流是否成功打开
        if self.vcap.isOpened() is False:
            print("[Exiting]: Error accessing webcam stream.")
            exit(0)
        # 使用 get 方法获取视频流的帧率，并将其打印出来
        fps_input_stream = int(self.vcap.get(5))
        print("FPS of webcam hardware/input stream: {}".format(fps_input_stream))

        # 读取一帧图像，并检查是否成功读取
        self.grabbed, self.frame = self.vcap.read()
        if self.grabbed is False:
            print('[Exiting] No more frames to read')
            exit(0)

        # 将 self.stopped 变量设置为 True，表示当前未从视频流中读取帧
        self.stopped = True

        # 创建一个线程来读取下一个可用的帧，并将其设置为守护线程。守护线程会在后台运行，即使主程序正在执行也不会阻止程序退出。
        self.t = Thread(target=self.update, args=())
        self.t.daemon = True

    # 用于启动读取帧的线程。它将 self.stopped 变量设置为 False，表示正在从视频流中读取帧，并启动线程。
    def start(self) -> None:
        self.stopped = False
        self.t.start()

    # 在单独的线程中运行，不断从视频流中读取下一个可用的帧存储在 self.frame 变量中。
    def update(self) -> None:
        while True:
            if self.stopped is True:
                break
            self.grabbed, self.frame = self.vcap.read()
            if self.grabbed is False:
                print('[Exiting] No more frames to read')
                self.stopped = True
                break
        self.vcap.release()

    # 返回最新读取的帧。
    def read(self) -> any:
        return self.frame

    # 停止读取帧。它将 self.stopped 变量设置为 True，表示不再从视频流中读取帧。
    def stop(self) -> None:
        self.stopped = True
