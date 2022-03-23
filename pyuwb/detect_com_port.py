__author__ = "songjiangshan"
__copyright__ = "Copyright (C) 2021 songjiangshan \n All Rights Reserved."
__license__ = ""
__version__ = "1.0"

import serial
import string
import binascii
import time
from .calc_crc import calc_crc
import serial.tools.list_ports
from .mylog import logging
logger = logging.getLogger(__name__)


def is_anchor0(port_name):
    logger.debug('is_anchor0:%s', port_name)
    time.sleep(0.1)
    try:
        s = serial.Serial(port_name, 115200)  # 基站
    except Exception as e:
        # print('open port error', port_name, e)
        return False

    time.sleep(0.1)
    count = s.inWaiting()  # 获取串口缓冲区数据
    if count != 0:
        #串口有数据，说明正在通讯？
        d1 = bytes.fromhex('01 10 00 28 00 01 02 00 00')
        d1_crc = calc_crc(d1)
        d1 = d1+d1_crc
        s.write(d1)
        time.sleep(0.5)
        count = s.inWaiting()
        s.read(count)
        count = s.inWaiting()
        s.read(count)



    d1 = bytes.fromhex('01 03 00 03 00 01')
    d1_crc = calc_crc(d1)
    d1 = d1 + d1_crc
    s.write(d1)
    time.sleep(0.1)
    count = s.inWaiting()  # 获取串口缓冲区数据
    if count != 0:
        n = s.read(s.in_waiting)
        logger.debug('%s', n.hex())
        time.sleep(0.02)
        if n == b"\x01\x03\x02\x00\x029\x85":
            s.close()
            logger.debug('OK')
            return True

    s.close()
    logger.debug('NO DETECTED')
    return False


def is_print(port_name):
    logger.debug('is_print:%s', port_name)
    time.sleep(0.1)
    try:
        s = serial.Serial(port_name, 256000)  # 基站
    except Exception as e:
        # print('open port error', port_name, e)
        return False

    time.sleep(0.1)
    count = s.inWaiting()  # 获取串口缓冲区数据
    if count != 0:
        #串口有数据，说明正在通讯？
        d1 = bytes.fromhex('01 10 00 28 00 01 02 00 00')
        d1_crc = calc_crc(d1)
        d1 = d1+d1_crc
        s.write(d1)
        time.sleep(0.5)
        count = s.inWaiting()
        s.read(count)
        count = s.inWaiting()
        s.read(count)



    d1 = bytes.fromhex('01 03 00 03 00 01')
    d1_crc = calc_crc(d1)
    d1 = d1 + d1_crc
    s.write(d1)
    time.sleep(0.1)
    count = s.inWaiting()  # 获取串口缓冲区数据
    if count != 0:
        n = s.read(s.in_waiting)
        logger.debug('%s', n.hex())
        time.sleep(0.02)
        # 01 03
        # 02 （长度）
        # 00 03 （3为打印工具）
        # F8 45 （crc）
        if n == b"\x01\x03\x02\x00\x03\xF8\x45":
            s.close()
            logger.debug('OK')
            return True

    s.close()
    logger.debug('NO DETECTED')
    return False

def is_alert_light(port_name):
    logger.debug('is_alert_light:%s', port_name)
    time.sleep(0.1)
    try:
        s = serial.Serial(port_name, 9600)  # 基站
    except Exception as e:
        logger.info('open port error %s %s', port_name, e)
        return False
    d1 = bytes.fromhex('21242528')# stop beep &RGB color light
    s.write(d1)
    s.close()
    time.sleep(0.5)

    s = serial.Serial(port_name, 9600)  # 基站

    d1 = bytes.fromhex('21')
    s.write(d1)
    time.sleep(0.1)
    count = s.inWaiting()  # 获取串口缓冲区数据
    if count != 0:
        logger.info('got data count:%d', count)
        time.sleep(0.02)
        n = s.read(s.in_waiting)
        logger.info('got data: %s', n.hex())
        if n == b"!\x00" or n == b'!\x01':
            s.close()
            return True


    logger.info('no got expected data')
    s.close()
    return False


def detect_com_port():
    """
    检测串口：
    :return: ['COM3', 'COM4'] 对应uwb的主基站串口，报警灯串口。
            [None, 'COM4'] ['COM3', None] [None, None] 没有相应设备时，为None
    """
    ret = [None, None, None]
    port_list = list(serial.tools.list_ports.comports())
    if len(port_list) <= 0:
        # print("The Serial port can't find!")
        return ret

    for i in list(port_list):
        port_name = i[0]
        if is_anchor0(port_name):
            ret[0] = port_name
        elif is_alert_light(port_name):
            ret[1] = port_name
        elif is_print(port_name):
            ret[2] = port_name

    logger.info('com port detect result:%s', ret)
    return ret


if __name__ == '__main__':
    print(detect_com_port())


