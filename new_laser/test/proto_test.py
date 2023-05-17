from typing import Tuple, List
import protobuf.msg_pb2 as msg

pts_origin: List[Tuple[int, int]] = [(0, 0), (1, 1), (12, 34), (56, 78)]


def convert_point(point: Tuple[int, int]) -> msg.Point:
    x, y = point
    p = msg.Point()
    p.x = x
    p.y = y
    return p


pts_converted = list(map(convert_point, pts_origin))

m = msg.Points()
m.id = 1234
pts = m.points

for p in pts_converted:
    pts.append(p)

import serial
import time

with serial.Serial("COM3", baudrate=9600) as ser:
    while True:
        m_serialized = m.SerializeToString()
        ser.write(m_serialized)
        print(len(m_serialized))
        time.sleep(0.1)
        m.id += 1
