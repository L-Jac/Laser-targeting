import numpy as np
import math
from typing import Union


class Score(object):

    def __init__(self) -> None:
        self.r = 0
        self.aim_xlist = []
        self.aim_ylist = []

        self.shoot_xlist = []
        self.shoot_ylist = []

        self.center_x = 296
        self.center_y = 264

        self.k = 500 / 480

        self.r = [0, 0, 0, 0, 0, 216, 168, 120, 72, 24, 0]

    # 更新瞄准列表
    # def update_aim(self, axis_x, axis_y):
    #     if len(axis_x) < 31:
    #         self.aim_xlist.append(axis_x)
    #         self.aim_ylist.append(axis_y)
    #     else:
    #         self.aim_xlist = []
    #         self.aim_ylist = []

    # 更新射击列表
    # def update_shoot(self, axis_x, axis_y):
    #     if len(axis_x) < 31:
    #         self.aim_xlist.append(axis_x)
    #         self.aim_ylist.append(axis_y)
    #     else:
    #         self.aim_xlist = []
    #         self.aim_ylist = []

    # 根据坐标算出环数
    def ring(self, xs: Union[int, float], ys: Union[int, float]) -> int:
        r = math.sqrt(((xs - self.center_x) ** 2) + ((ys - self.center_y) ** 2))
        # print(r)
        if r >= 0:
            if r < 24:
                ri = 10
            elif r < 72:
                ri = 9
            elif r < 120:
                ri = 8
            elif r < 168:
                ri = 7
            elif r <= 216:
                ri = 6
            else:
                return 0
        else:
            return 0
        # print(ri)
        rd = ((r - self.r[ri]) / 48)
        return int(10 * (ri + (1 - rd)))

    # 计算瞄准环值
    def aim_ring(self, aim_xlist, aim_ylist):
        aim_x, aim_y = self.aim_axis(aim_xlist, aim_ylist)
        ring = self.ring(aim_x, aim_y)
        return ring

    # 计算击中环值
    def shoot_ring(self, shoot_x, shoot_y):
        ring = self.ring(shoot_x, shoot_y)
        return ring

    # 计算瞄准平均坐标
    def aim_axis(self, aim_xlist, aim_ylist):
        if len(aim_xlist) > 0 and len(aim_ylist) > 0:
            return np.mean(aim_xlist), np.mean(aim_ylist)
        else:
            return None, None

    # 计算持枪晃动
    def shake(self, aim_xlist, aim_ylist):
        aim_x, aim_y = self.aim_axis(aim_xlist, aim_ylist)
        shake = int(np.mean(np.sqrt(
            ((np.array(aim_xlist) - np.array(aim_x)) ** 2) + ((np.array(aim_ylist) - np.array(aim_y)) ** 2))) * self.k)
        if shake < 255:
            return shake
        else:
            return 255

    # 计算晃动速率
    def shake_v(self, aim_xlist, aim_ylist):
        shake_v = int(np.sum(np.sqrt(((np.array(aim_xlist) - np.array(self.center_x)) ** 2) + (
                (np.array(aim_ylist) - np.array(self.center_y)) ** 2))) * self.k)
        if shake_v < 255:
            return shake_v
        else:
            return 255

    # 计算击发晃动量
    def shoot_shake(self, aim_xlist, aim_ylist, shoot_x, shoot_y):
        aim_xlist = np.array(aim_xlist)
        aim_ylist = np.array(aim_ylist)
        shoot_x = np.array(shoot_x)
        shoot_y = np.array(shoot_y)
        shoot_shake = int(np.max(np.sqrt((((aim_xlist - shoot_x) ** 2) + ((aim_ylist - shoot_y) ** 2)))) * self.k)
        if shoot_shake < 255:
            return shoot_shake
        else:
            return 255

    # 计算击发速率
    def shoot_shake_v(self, aim_xlist, aim_ylist, shoot_x, shoot_y):
        aim_xlist = np.array(aim_xlist)
        aim_ylist = np.array(aim_ylist)
        shoot_x = np.array(shoot_x)
        shoot_y = np.array(shoot_y)
        shoot_shake_v = int(np.sum(np.sqrt(((aim_xlist - shoot_x) ** 2) + ((aim_ylist - shoot_y) ** 2))) * self.k)
        if shoot_shake_v < 255:
            return shoot_shake_v
        else:
            return 255
