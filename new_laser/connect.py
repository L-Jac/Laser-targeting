#!/usr/bin/python3
import time
import serial
import threading

"""
lock gaun target
"""


class Lc12s(object):
    # ID number1,ID number2,flag
    # ID number1,ID number2,flag

    def __init__(self, uart_baud, set_pin, machine_idh, machine_idl, net_idh, net_idl, rf_power,
                 rf_channel, data_length):

        self.net_idl = net_idl
        self.start = None
        self.data_length = data_length  # frame length
        self.uart = serial.Serial('/dev/ttyUSB0', uart_baud, timeout=1)
        # AA 5A 00 00 FF FF 00 1E 00 04 00 14 00 01 00 12 00 4B
        self.init_order = [0xaa, 0x5a, 0x00, 0x00, 0x00, 0x0c, 0x00, 0x1E, 0x00, 0x04, 0x00, 0x14, 0x00, 0x01, 0x00,
                           0x12, 0x00, 0x59]
        self.order = bytearray(self.init_order)
        self.machineid_high = machine_idh  # 1byte
        self.machineid_low = machine_idl  # 1byte
        self.init_order[4] = net_idh  # 1byte
        self.init_order[5] = net_idl  # 1byte
        self.init_order[7] = rf_power  # 0:6dbm 1:3dbm 2:1dbm 3:-2dbm 4:-8dbm
        self.init_order[11] = rf_channel  # 0~127
        self.checksum = self.check
        self.init_order[17] = self.checksum

        # byte0:0x0b:core and gun,0x16:core and web.
        # byte1:enroll:0x00 quit: 0x01 data:10 set:11
        # byte2:direction:0x10 up 0x01 down
        # byte3 and byte4: gun_id_high and gun_id_low
        # byte5 and byte6:target_id_high and target_id_low
        # byte7:axis
        # byte8:ack
        # byte9:bullet
        # byte10 and byte11: gun nc core aix
        # byte12 ,byte13 and byte14:nc
        self.core_gun = [0x0b, 0x10, 0x10, 0x00, 0x00, 0x00, 0x00, 0x01, 0x00, 0x1E, 0x67, 0x68]
        self.core_web = [0x16, 0x10, 0x10, 0x00, 0x0c, 0x00, 0x00, 0x01, 0x00, 0x1E, 0x07, 0x08, 0x69, 0x70, 0x71]
        self.datat_gun = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.datat_web = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.data_temp = None
        # function flag
        self.receive_flag_g = False  # 是否接收到来自枪支和网络的数据
        self.receive_flag_w = False
        self.target_enroll = False  # 是否注册靶箱
        self.core_gun_flag = False  # 是否接收到来自枪支和网络的设置信息
        self.core_web_flag = False
        self.receive_enroll_flag = False  # 是否接收到注册、数据和退出事件
        self.receive_data_flag = False
        self.receive_quit_flag = False
        self.confirm_set_flag = False  # 是否确认设置
        self.send_interval = False  # 是否发送
        self.open_flag = False  # 是否打开

        # LOCK
        # threading.Lock()基本的锁定机制，用于同步多线程
        # https://www.runoob.com/python3/python3-multithreading.html
        self.target_enroll_lock = threading.Lock()
        self.receive_enroll_lock = threading.Lock()
        self.receive_quit_lock = threading.Lock()
        self.confirm_set_lock = threading.Lock()
        self.gun_data_lock = threading.Lock()
        self.web_data_lock = threading.Lock()
        self.receive_gun_lock = threading.Lock()
        self.receive_web_lock = threading.Lock()
        self.receive_data_lock = threading.Lock()
        # Send state
        self.send_flag = False
        #
        self.handlers = {
            0xaa: self.handle_aa,  # 设置信号
            0x0b: self.handle_0b,  # 枪信号
            0x16: self.handle_16,  # 靶箱信号
        }
        self.gun_handlers = {
            0: self.handle_gun_0x00,
            0x01: self.handle_gun_0x01,
            0x10: self.handle_gun_0x10,
            0x11: self.handle_gun_0x11
        }
        self.web_handlers = {
            0x00: self.handle_web_0x00,
            0x01: self.handle_web_0x01,
            0x10: self.handle_web_0x10,
            0x11: self.handle_web_0x11
        }

    # 设置
    def config(self):
        # 调用 self.uart.write 方法将 self.order 中的数据写入串口。
        self.uart.write(bytearray(self.order))
        # 调用 time.sleep 方法等待 0.5 秒
        time.sleep(0.5)
        # 调用 self.uart.flushInput 方法清空输入缓冲区。
        self.uart.flushInput()

    # check 方法用于计算校验和。
    def check(self):
        temp = 0
        for i in range(17):
            temp = self.init_order[i] + temp
        # 将 temp 与 0xff 进行按位与运算
        # 相当于将 temp 与二进制数 11111111 进行按位与运算。会保留temp 变量的低 8 位，高位清零。
        temp = (temp & 0xff)
        return temp

    # 发送消息函数
    def send(self, data_buffer):
        temp = bytearray(data_buffer)
        self.uart.write(temp)
        if self.send_interval:
            time.sleep(0.100)
        else:
            time.sleep(0.010)

    # 设置信号
    def handle_aa(self, data):
        data = self.uart.read(17)
        data = 0

    # 枪信号
    def handle_0b(self, data):
        self.gun_data_lock.acquire()
        self.datat_gun = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.datat_gun[0] = 0x0b
        data = self.uart.read(11)
        for i in range(1, len(self.datat_gun)):
            self.datat_gun[i] = int(data[i - 1])
        self.gun_data_lock.release()
        self.receive_gun_lock.acquire()
        self.receive_flag_g = True
        self.receive_gun_lock.release()

    # 靶箱信号
    def handle_16(self, data):
        self.web_data_lock.acquire()
        self.datat_web = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
        self.datat_web[0] = 0x16
        data = self.uart.read(14)
        for i in range(1, len(self.datat_web)):
            self.datat_web[i] = int(data[i - 1])
        self.web_data_lock.release()
        self.receive_web_lock.acquire()
        self.receive_flag_w = True
        self.receive_web_lock.release()

    # 接收消息
    def recv(self):
        self.start = time.time()
        uart_temp = ''
        # 如果串口有数据就先读一个字节的数据
        if self.uart.inWaiting():
            uart_temp = self.uart.read(1)
        if len(uart_temp) > 0:
            head = int(uart_temp[0])
            handler = self.handlers.get(head)
            if handler:
                handler(self, uart_temp)

    def handle_gun_0x00(self):
        self.receive_enroll_lock.acquire()
        self.receive_enroll_flag = True
        self.receive_enroll_lock.release()
        self.receive_quit_lock.acquire()
        self.receive_quit_flag = False
        self.receive_quit_lock.release()
        self.core_gun[3] = self.datat_gun[3]
        self.core_gun[4] = self.datat_gun[4]

    def handle_gun_0x01(self):
        self.receive_enroll_lock.acquire()
        self.receive_enroll_flag = False
        self.receive_enroll_lock.release()
        self.receive_quit_lock.acquire()
        self.receive_quit_flag = True
        self.receive_quit_lock.release()
        self.core_gun[3] = 0xff
        self.core_gun[4] = 0xff

    def handle_gun_0x10(self):
        self.receive_data_lock.acquire()
        self.receive_data_flag = True
        self.receive_data_lock.release()

    def handle_gun_0x11(self):
        self.confirm_set_flag = True

    def handle_web_0x00(self):
        if self.datat_web[8] == 0x99:
            print("确认注册")
            self.target_enroll_lock.acquire()
            self.target_enroll = True
            self.target_enroll_lock.release()

    def handle_web_0x01(self):
        if self.datat_web[8] == 0x99:
            print("quit confirm")

    def handle_web_0x10(self):
        if self.datat_web[8] == 0x99:
            print("data confirm")

    def handle_web_0x11(self):
        print("收到设置")
        self.core_gun_flag = True

    def handle_message(self):
        if self.receive_flag_g:
            self.receive_gun_lock.acquire()
            self.receive_flag_g = False
            self.receive_gun_lock.release()
            if self.datat_gun[0] == 11 and self.datat_gun[2] == 16:
                self.gun_data_lock.acquire()
                temp = self.datat_gun
                self.gun_data_lock.release()
                temp[8] = 153
                temp[2] = 0x01
                self.send_interval = True
                self.send(temp)
                self.send_interval = False
                msg_type = self.datat_gun[1]
                handler = self.gun_handlers.get(msg_type)
                if handler:
                    handler(self)
        elif self.receive_flag_w:
            self.receive_web_lock.acquire()
            self.receive_flag_w = False
            self.receive_web_lock.release()
            if self.datat_web[0] == 0x16 and self.datat_web[2] == 0x01:
                msg_type = self.datat_web[1]
                handler = self.web_handlers.get(msg_type)
                if handler:
                    handler(self)
        else:
            self.gun_data_lock.acquire()
            self.datat_web = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            self.gun_data_lock.release()
            self.web_data_lock.acquire()
            self.datat_gun = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            self.web_data_lock.release()

    def enroll(self):
        # 注册
        self.core_web[0] = 0x16
        self.core_web[1] = 0x00
        self.core_web[2] = 0x10
        self.core_web[8] = 0x00
        self.send_interval = True
        self.send(self.core_web)
        self.send_interval = False

    # 射击成绩传送
    def hit(self, flag, aim_ring, shoot_ring, shake, shake_v,
            shoot_shake, shoot_shake_v, axis_x, axis_y):
        self.core_web[0] = 0x16
        self.core_web[1] = 0x10
        self.core_web[2] = 0x10
        self.core_web[3] = flag  # 击中靶子
        self.core_web[4] = aim_ring
        self.core_web[5] = shoot_ring
        self.core_web[6] = shake
        self.core_web[7] = shake_v
        self.core_web[8] = shoot_shake
        self.core_web[9] = shoot_shake_v
        axis_xh = int(axis_x / 480.0 * 100)
        axis_xl = int((axis_x / 480.0 * 100 - axis_xh)) * 100
        axis_yh = int(axis_y / 480.0 * 100)
        axis_yl = int((axis_y / 480.0 * 100) - axis_yh) * 100
        self.core_web[10] = axis_xh  # 取出高位
        self.core_web[11] = axis_xl  # 取出低位
        self.core_web[12] = axis_yh  # 取出高位
        self.core_web[13] = axis_yl  # 取出低位
        print("坐标为", axis_x, axis_y)
        self.send_interval = False
        self.send(self.core_web)
        self.send_interval = True
        # confirm to recv
