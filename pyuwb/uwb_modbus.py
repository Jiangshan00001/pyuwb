import traceback
import copy
import time
from .calc_crc import check_crc
from .client_id_utils import client_id_get_no
from .modbus_pkt import get_read_pkt, get_write_pkt, decode_read_return, decode_write_return
import serial
from .mylog import logging
#from .detect_com_port import is_anchor0

import serial.tools.list_ports


logger = logging.getLogger(__name__)

#主基站编号，固定为0
ANCHORZ_NO=0

# old reg addr
REG_TAG_NUM = 0x29
REG_TAG_LIST = 0x37
REG_BAUD_RATE = 0x00
REG_MODBUS_ID = 0x01
REG_DEVICE_MODE = 3
REG_DEVICE_ID = 4
REG_CHANNEL_DATARAT = 5
REG_ANT_DLY = 8
KALMAN_PARAM_ADDR = 6
REG_MEASURE_MODE_ADDR = 2
REG_CHANGE_ANC_ID = 0x8d
REG_CALCULATE_EN = 0x28
REG_CHANGE_FLAG=0x8e


#new reg addr
REG_TEST=0
REG_FIRMWARE_VERSION=1
REG_BAUD_RATE=2
REG_MODBUS_ID=3
REG_MEASURE_MODE_ADDR=4
REG_DEVICE_MODE=5
REG_DEVICE_ID=6
REG_CHANNEL_DATARAT=7
REG_ANT_DLY=8
REG_ANC_ENABLED=9
#Calculate_EN：
REG_CALCULATE_EN=10
REG_TAG_NUM=11
#可用标签列表(依次为C寄存器byte0、C寄存器byte1、D寄存器byte0、D寄存器byte1......)
REG_TAG_LIST=12
REG_TAG_ID_NOW=62
REG_CALCULATE_FLAG=63
REG_DIST_A=64#=//主基站测距
REG_DIST_B=65
REG_DIST_C=66
REG_DIST_D=67
REG_DIST_E=68
REG_DIST_F=69
REG_DIST_G=70
REG_DIST_H=71
REG_ACCX_GET=72
REG_ACCY_GET=73
REG_ACCZ_GET=74
REG_ACCX_OWN=75
REG_ACCY_OWN=76
REG_ACCZ_OWN=77
REG_CHANGE_ANC_ID=78
#1为将基站改为标签，2-标签改基站。 3-设置完成. 4-设置失败 5--等待中
REG_CHANGE_FLAG=79
REG_GROUP_ID=80
REG_IAP_RESET=100# //复位重启寄存器



class UwbModbus:
    def __init__(self):

        self.EMPTY_DIST_VAL = -1  # 空的距离位置值
        self.verbose = 0  # --0 不打印，1--打印调试信息
        self.demo_inst = None
        self.port = None
        self.port_name = None  # COM4
        self.bulk_mode = 0  # 是否直接发送
        self.is_demo_mode = 0  # 演示模式
        self.mbus_register = bytearray(106 * 2)
        self.tag_list_cache_ready_cnt = 10  # 用于缓存几个数据，就可以进行平均放入tag_list中的设置。默认10各数据。
        self.read_error_cnt = 0
        self.read_error_stat = {}
        self.read_ok_cnt = 0
        self.read_buf = b''  # 报文接收缓冲区
        self.count_for_payload = 0
        self.count_for_payload_timer = time.time()
        self.count_for_payload_pps = 0  # packet per second

        self.anchor_used_dict = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 1}  # 当前启动的基站列表，默认是6个
        self.curr_used_anchor_no = [] #当前使用的基站号列表
        self.curr_used_tag_no=[] #当前使用的标签号列表
        self.set_cache_data_to_default()

    def is_anchorz(self, port_name):
        logger.debug('is_anchorz:%s', port_name)
        time.sleep(0.1)
        is_ok = self.connect(port_name)
        if not is_ok:
            return False
        time.sleep(0.1)

        count = self.port.inWaiting()
        if count != 0:
            #正在测量？上次未关闭设备?
            self.start_measure_h(0)
            time.sleep(0.5)
            count = self.port.inWaiting()
            self.port.read(count)
            count = self.port.inWaiting()
            self.port.read(count)

        is_ok, ret = self.modbus_test_read()
        if not is_ok:
            return False
        is_ok, ilist,bdat = self.read_modbus_h(REG_DEVICE_MODE,1)
        if not is_ok:
            return False

        device_mode = ilist[0]
        logger.debug('device mode:%s(%d)\n',self.device_model_to_str(device_mode), device_mode)

        self.disconnect()
        return True

    def device_model_to_str(self, mode_int):
        #设备模式 0：标签 1：次基站 2：主基站
        if mode_int==0:
            return 'tag'
        elif mode_int==1:
            return 'anchor'
        elif mode_int==2:
            return 'anchorz'

    def detect_com_port(self):
        """
        检测串口：
        :return: 'COM3'  对应uwb的主基站串口
                没有相应设备时，为None
        """
        ret = None
        port_list = list(serial.tools.list_ports.comports())
        if len(port_list) <= 0:
            # print("The Serial port can't find!")
            logger.warning("have no  Serial port find!")
            return ret

        for i in list(port_list):
            port_name = i[0]
            if self.is_anchorz(port_name):
                ret = port_name
                logger.debug('port find')

        return ret

    def disconnect(self):
        # 关闭串口
        if self.is_port_open():
            self.port.close()
            logger.debug('port disconnect')

    def modbus_test_write(self, dat=0):
        self.write_modbus_h(REG_TEST, 1,dat.to_bytes(2, byteorder='big', signed=False))

    def modbus_test_read(self):
        is_ok, ilist, bdat= self.read_modbus_h(REG_TEST, 1)
        if not is_ok:
            return False, None

        return is_ok, ilist[0]


    def connect(self, com_port=None):
        """连接串口"""
        try:
            self.port_name = com_port
            if self.port_name is None:
                self.port_name = self.detect_com_port()

            if self.port_name is None:
                print('could not find device')
                return False

            #print('port: ', self.port_name)
            #print('self.port_name：', self.port_name)

            self.port = serial.Serial(port=self.port_name, baudrate=115200, timeout=0.1)  # , timeout=0.1
            #print('self.port：', self.port)
            self.port.close()
            if not self.is_port_open():
                self.port.open()
            return True
        except Exception as e:
            print('connect failed', e)
            traceback.print_exc()
            return False

    def _demo_write_data(self, data):
        if self.demo_inst is None:
            return
        return self.demo_inst.write(data)

    def _write_data(self, data):
        logger.debug('write_data: %s', data.hex())

        if self.is_demo_mode:
            self._demo_write_data(data)
            return

        if self.port is None or (not self.is_port_open()):
            pass
            print('self.port is None or (not self.is_port_open())')
            # logger.error('send error. not open')
        else:
            try:
                self.port.write(data)
            except Exception as e:
                logger.error('串口错误? %s', e)
                self.port.close()
                self.port.open()
                self.port.write(data)

    def _demo_read_data(self, timeout, byte_max):
        if self.demo_inst is None:
            return
        # time.sleep(timeout)
        return self.demo_inst.read(timeout, byte_max)

    def _read_data(self, timeout=0.001, byte_max=-1):
        """

        :param timeout:
        :return:
        """

        data_get = b''
        t1 = time.time()
        while time.time() - t1 < timeout:
            try:
                if self.is_demo_mode:
                    data_get += self._demo_read_data(timeout, byte_max)
                else:
                    data_get += self.port.read(1024)
            except Exception as e:
                if self.is_demo_mode:
                    pass
                else:
                    logger.error('串口错误? %s', e)
                    self.port.close()
                    self.port.open()
                    data_get += self.port.read(1024)

            # logger.debug('read_data: %s', data_get.hex())
            if (byte_max > 0) and (byte_max <= len(data_get)):
                break

        logger.debug('read_data_ret: %s', data_get.hex())

        return data_get

    def check_crc(self, payload: bytes):
        """

        :param payload: 带校验和的报文，最后2byte的校验和会被用于比较
        :return: 正确返回True, 否则返回false
        """
        return check_crc(payload)

    def read_modbus_h(self, reg_start_addr, reg_count, addr=1):
        """

        :param reg_start_addr:
        :param reg_count:
        :param addr:
        :return: is_ok, ilist, bytes_data
        """
        """
            指定id、地址、寄存器个数
            01 --id号： id
            03-- 读
            00 05 --起始寄存器  add2
            00 6A -- 寄存器个数  reg_count
            C5 E5 --校验位

            01 --id号： id
            03 -- 读
            02 -- 字节数
            0007 -- 数据
            f986
            寄存器是16bit的。低位在前，高位在后。
        """

        to_w = get_read_pkt(reg_start_addr, reg_count, addr)

        self._write_data(to_w)
        to_read_len = 5 + reg_count * 2
        ret = self._read_data(1, byte_max=to_read_len)

        ret2 = decode_read_return(ret, reg_count)
        is_ok=False
        dat = None
        if 'crc_ok' in ret2:
            is_ok = ret2['crc_ok']

        if is_ok:
            ilist =[]
            ll = len(ret2['data'])//2
            for i in range(ll):
                dat = int.from_bytes(ret2['data'][i*2:i*2+2], 'big', signed=False)
                ilist.append(dat)
        else:
            ilist = []
            ret2['data'] = ret

        return is_ok,ilist, ret2['data']


    def _write_modbus_real(self, add2, reg_count, dat, id=1, just_gen_pkt=0):
        """ 例子：开始测距 01 10 00 28 00 01 02 00 04 A1 BB
                    01 id号  id
                    10 写
                    00 00 起始寄存器  add2
                    00 6A 寄存器个数  reg_count
                    D4   字节数      len(dat)
                    。。。。 D4个字节  dat
                    0B 60 --校验和

                    返回值
                    00
                    10
                    006b   107
                    0001   1
                    71c4

                    01  id号  id
                    10  写
                    006b  起始寄存器
                    0001  寄存器个数
                    7015  校验位


                :param id:
                :param add2:
                :param reg_count:
                :param dat:
                :return:
                """
        logger.debug('write_modbus_real: %s %s %s %d', add2.to_bytes(2, 'big').hex(), reg_count.to_bytes(1, 'big').hex()
                     ,
                     dat.hex(), id)

        to_r = get_write_pkt(add2, reg_count, dat, id)

        if just_gen_pkt:
            # logger.debug("write_modbus_real just_gen_pkt=1 do not send")
            return to_r

        self._write_data(to_r)
        ret = self._read_data(1, 8)

        ret2= decode_write_return(ret)
        #print(ret2)
        return ret2

    def write_modbus_h(self, add2, reg_count, dat, id=1, just_gen_pkt=0):
        """ 例子：开始测距 01 10 00 28 00 01 02 00 04 A1 BB
            01 id号  id
            10 写
            00 00 起始寄存器  add2
            00 6A 寄存器个数  reg_count
            D4   字节数      len(dat)
            。。。。 D4个字节  dat
            0B 60 --校验和

            返回值
            00
            10
            006b   107
            0001   1
            71c4

            01  id号  id
            10  写
            006b  起始寄存器
            0001  寄存器个数
            7015  校验位


        :param id:
        :param add2:
        :param reg_count:
        :param dat:
        :return:
        """
        logger.debug('write_modbus: %s %s %s %d', add2.to_bytes(2, 'big').hex(), reg_count.to_bytes(1, 'big').hex(),
                    dat.hex(), id)

        if self.bulk_mode and (not just_gen_pkt):
            # logger.debug('write in bulk mode. just write to local without return data')
            # bulk mode，just write to buffer
            for i in range(reg_count * 2):
                self.mbus_register[add2 * 2 + i] = dat[i]

            return {'raw_data': b''}

        return self._write_modbus_real(add2, reg_count, dat, id, just_gen_pkt=just_gen_pkt)

    def bulk_send(self):
        # logger.debug('bulk_send')
        self._write_modbus_real(0, len(self.mbus_register) // 2, self.mbus_register)


    def read_label_h(self):
        is_ok, ret, bdata = self.read_modbus_h(REG_TAG_NUM, 51)
        if is_ok:
            label_num = ret[0]
            return is_ok, ret[1:label_num+1]
        return is_ok, ret

    def set_label_h(self, label_no_list=(0,)):
        """
        如果label_no_list=[1] 则发送数据为 00 01
        如果label_no_list=[1,2] 则发送数据为 02 01
        如果label_no_list=[1,2,3] 则发送数据为 02 01 00 03
        :param label_no_list:
        :return:
        """
        # logger.info('设置标签列表：%s', json.dumps(label_no_list))
        label_no_list = copy.deepcopy(label_no_list)
        label_cnt = len(label_no_list)

        if label_cnt % 2 == 1:
            # 标签是奇数个，则+0变为偶数个
            label_no_list.append(0)

        label_dat = b''
        for i in range(len(label_no_list) // 2):
            label_dat += label_no_list[i * 2 + 1].to_bytes(1, 'big') + label_no_list[i * 2].to_bytes(1, 'big')

        self.write_modbus_h(REG_TAG_LIST, (label_cnt + 1) // 2, label_dat)
        # 因为设置标签都是bulk模式，所以此处不需要sleep
        if not self.bulk_mode:
            time.sleep(0.5)

    def read_label_num_h(self):
        is_ok, data, bdata = self.read_modbus_h(REG_TAG_NUM, 1)
        return is_ok, data
    def set_label_num_h(self, num: int):
        # logger.info('设置标签数：%d', num)
        num_b = num.to_bytes(2, 'big')
        self.write_modbus_h(REG_TAG_NUM, 1, num_b)
        # 因为此处是bulk模式，所以此处不需要sleep
        if not self.bulk_mode:
            time.sleep(0.5)

    def set_buardrate_h(self, rate_no=7):
        """
        设备串口通讯波特率
        :param rate_no:0：4800  1：9600 2：14400 3：19200 4：38400 5：56000 6：57600 7：115200  8：128000 9：256000
        :return:
        """
        self.write_modbus_h(REG_BAUD_RATE, 1, rate_no.to_bytes(2, 'big'))

    def set_modbus_id_h(self, id=1):
        self.write_modbus_h(REG_MODBUS_ID, 1, id.to_bytes(2, 'big'))

    def read_modbus_id_h(self):
        is_ok, ret, bdata = self.read_modbus_h(REG_MODBUS_ID,1, 0xff)
        return is_ok, ret

    def set_device_measure_mode_h(self, cmode=1, dmode=0):
        """
        :param cmode:测量模式   0：DS-TWR 1：高性能TWR。
        :param dmode:测距模式 1:二维模式 2：三维模式"
        :return:
        """
        self.write_modbus_h(REG_MEASURE_MODE_ADDR, 1, cmode.to_bytes(1, 'big') + dmode.to_bytes(1, 'big'))

    def set_device_mode_h(self, mode=2):
        """

        :param mode:设备模式 0：tag 1：anchor 2：anchorz
        :return:
        """
        if mode=='tag':
            mode = 0
        elif mode=='anchor':
            mode = 1
        elif mode=='anchorz':
            mode = 2

        if mode<0 or mode>2:
            logger.error('mode not known %s', mode)

        self.write_modbus_h(REG_DEVICE_MODE, 1, mode.to_bytes(2, 'big'))
    def read_device_mode_h(self):
        is_ok, ilist, bdat = self.read_modbus_h(REG_DEVICE_MODE, 1)
        if not is_ok:
            return False, None

        return is_ok, ilist[0]

    def set_modbus_id_h(self, mid):
        """

        :param mid: modbus_id/addr to set.
        :return:
        """
        self.write_modbus_h(REG_MODBUS_ID, 1, mid.to_bytes(2, 'big'), id=0xff)


    def set_device_id_h(self, device_id=0):
        """
        设备ID，高8位为次基站ID，范围0~6 ，
        低8位为标签ID ，0~99
        （程序内部 标签ID为0~247  次基站ID为248~254  主基站ID为255）
        :param device_id:
        :return:
        """
        self.write_modbus_h(REG_DEVICE_ID, 1, device_id.to_bytes(2, 'big'))

    def read_device_id_h(self):
        is_ok, ilist, bdat = self.read_modbus_h(REG_DEVICE_ID, 1)
        if not is_ok:
            return False, None

        return is_ok, ilist[0]

    def read_comm_channel_and_speed_h(self):
        is_ok, ret, bdata = self.read_modbus_h(REG_CHANNEL_DATARAT, 1)
        return is_ok, ret
    def set_comm_channel_and_speed_h(self, channel=1, speed=2):
        """
        byte0-空中信道，byte1-空中传输速率

        :param channel:
        :param speed:
        :return:
        """
        self.write_modbus_h(REG_CHANNEL_DATARAT, 1, channel.to_bytes(1, 'big') + speed.to_bytes(1, 'big'))

    def set_kalman_h(self, param_q=3, param_r=0x0a):
        """

        :param param_q:
        :param param_r:
        :return:
        """
        self.write_modbus_h(KALMAN_PARAM_ADDR, 2, param_q.to_bytes(2, 'big') + param_r.to_bytes(2, 'big'))

    def set_recv_delay_h(self, delay=0x80CF,
                         just_gen_pkt=0):  # 天线延迟  ===================================================================
        """

        :param delay:
        :return:
        """
        return self.write_modbus_h(REG_ANT_DLY, 1, delay.to_bytes(2, 'big'), just_gen_pkt=just_gen_pkt)

    def read_anchor_enable_h(self):
        is_ok , ret, bdata = self.read_modbus_h(REG_ANC_ENABLED, 1, 1)
        ret_anchor_enabled=[]
        if is_ok:
            for i in range(1,7):
                if(ret[0]&(1<<i)):
                    ret_anchor_enabled.append(i-1)
        return is_ok, ret_anchor_enabled

    def set_anchor_enable_h(self,except_anchor_list=None):
        enable_byte=0xff
        for i in range(8):
            if except_anchor_list is not None:
                if i in except_anchor_list:
                    enable_byte &= ~(1<<(i))
        logger.debug('set anchor enable:%08x', enable_byte)
        self.write_modbus_h(REG_ANC_ENABLED, 1, enable_byte.to_bytes(2, 'big'))


    def set_anchor_enable_old_h(self, jizhan_index=0, enabled=1):
        """
        基站固定的有7个。编号为0-6. 对应 BCDEFGH
        :param jizhan_index: 基站编号 0-6
        :param enabled: 0--disable. 1--enable it
        :return:
        """
        """
        基站固定的有7个。编号为0-6. 对应 BCDEFGH
        :param jizhan_index:基站编号 0-6
        :return:
        """
        if jizhan_index > 6 or jizhan_index < 0:
            # logger.error("基站编号超过范围：%s", jizhan_index)
            return
        # logger.info('设置基站使能 %d %d', jizhan_index, enabled)
        # FIXME: 此处基站使能地址不连续???

        jizhan_enable_addr = [12, 16, 20, 24, 28, 32, 36]
        self.write_modbus_h(jizhan_enable_addr[jizhan_index], 1, enabled.to_bytes(2, 'big'))

    def start_measure_h(self, mode=6):
        """
        :param mode:   0x04：持续测量，主动发送，不写入寄存器
                    0x03：单次测量，主动发送，写入寄存器
                    0x02：持续测量，不发送，写入寄存器
                    0x01：单次测量，不发送，写入寄存器
                    0x00: 停止测量"
        :return:
        """
        # logger.info('start_measure %d', mode)
        self.measure_mode = mode
        self.write_modbus_h(REG_CALCULATE_EN, 1, mode.to_bytes(2, 'big'))
        time.sleep(0.3)

    def stop_measure_h(self):
        # 停止连续测量
        # logger.info('停止测量:')
        self.start_measure_h(0)
        data = self._read_data(1, -1)
        # logger.debug('unused pkt: %s', data.hex())

    def is_port_open(self):
        if self.is_demo_mode:
            if self.demo_inst is None:
                return False
            if self.demo_inst.is_connected():
                return True
            return False

        if self.port is None or (not self.port.isOpen()):
            return False
        return True

    def is_convert_complete_h(self):
        is_ok, ilist, bdat = self.read_modbus_h(REG_CHANGE_FLAG, 1)
        if  not is_ok:
            return False
        if ilist[0] != 0x03:
            logger.warning('is_convert_complete: %s', bdat.hex())
            return False
        logger.debug('is_convert_complete OK')
        return True

    def convert_tag_to_anchor_once_h(self, client_id):
        """
        将标签 转化为 次基站
        """
        print('将标签 转化为 次基站: 次基站 ', client_id)
        # 将标签0改为B基站 ：  01 10 00 8d 00 02 04 00 00 00 02 A1 BB
        # 开始修改 ：  01 10 00 28 00 01 02 00 05 A1 BB
        jizhan_id = int(client_id_get_no(client_id))

        #FIXME: 此处基站id=1-8. 单片机中此处参数是0-7.所以修改-1
        jizhan_id=jizhan_id-1
        jizhan_id=jizhan_id.to_bytes(1, 'big')
        self.write_modbus_h(REG_CHANGE_ANC_ID, 2, jizhan_id + b'\x00\x00\x02')
        time.sleep(0.5)
        ret = self.write_modbus_h(REG_CALCULATE_EN, 1, b'\x00\x05')
        time.sleep(0.5)
        return ret

    def convert_tag_to_anchor_h(self, client_id, loop_max_cnt=5):
        ret = {}
        for j in range(loop_max_cnt):
            ret = self.convert_tag_to_anchor_once_h(client_id)
            if not self.is_demo_mode:
                time.sleep(0.3)
            is_ok = self.is_convert_complete_h()
            if is_ok:
                # logger.debug('convert_biaoqian_to_jizhan ok 2 %s', client_id)
                return is_ok, ret

            if not self.is_demo_mode:
                time.sleep(1)

        # logger.error("convert_biaoqian_to_jizhan %s", client_id)
        return False, ret

    def convert_anchor_to_tag_once_h(self, client_id):
        """
        将次基站 转化为 标签0
        """
        # logger.info('将次基站 转化为 标签: 次基站 %s', client_id)
        #                   01 10 00 8d 00 02 04 00 00 00 01 00 00
        # 修改B基站为标签0 ：  01 10 00 8d 00 02 04 00 00 00 01 A1 BB
        #            01 10 00 28 00 01 02 00 05 00 00
        # 开始修改 ：  01 10 00 28 00 01 02 00 05 A1 BB

        jizhan_id = int(client_id_get_no(client_id) )
        #FIXME: 此处基站id=1-8. 单片机中此处参数是0-7.所以修改-1
        jizhan_id=jizhan_id-1
        jizhan_id = jizhan_id.to_bytes(1, 'big')
        self.write_modbus_h(REG_CHANGE_ANC_ID, 2, jizhan_id + b'\x00\x00\x01')
        time.sleep(0.2)
        ret = self.write_modbus_h(REG_CALCULATE_EN, 1,b'\x00\x05')
        return ret

    def convert_anchor_to_tag_h(self, client_id, loop_max_cnt=5):
        self.bulk_mode = 0
        ret = None
        for i in range(loop_max_cnt):
            ret = self.convert_anchor_to_tag_once_h(client_id)
            if not self.is_demo_mode:
                time.sleep(0.2)
            is_ok = self.is_convert_complete_h()
            if is_ok:
                # logger.debug('convert_jizhan_to_biaoqian:OK-OK')
                return is_ok, ret

            # logger.warning('convert_jizhan_to_biaoqian again:%s', client_id)
            if not self.is_demo_mode:
                time.sleep(0.1)
        # logger.error('convert_jizhan_to_biaoqian %s', client_id)
        return False, ret

    def get_dist_of_tag_once_inner_h(self):
        """
            获取某个标签的距离:
            测量3次，取平均值
        """
        # logger.debug('get_dist_of_biaoqian_once: start')
        self.start_measure_h(1)
        time.sleep(1)
        # FIXME: 此处需要确认地址是从哪个基站开始，改为从主基站开始???
        is_ok, ilist, bdat = self.read_modbus_h(REG_DIST_A, 8)

        dist_b = [self.EMPTY_DIST_VAL for i in range(8)]
        if is_ok:
            for i in range(8):
                dist_b[i] = ilist[i]/100.0

        self.stop_measure_h()
        # time.sleep(0.5)
        print('标签到各基站距离: %s', dist_b)
        return 0, 0, dist_b

    def set_cache_data_to_default(self):
        """标签20 21 到各次基站的距离"""
        # 每个标签的距离
        v = self.EMPTY_DIST_VAL
        self.tag_list_item_default={'dist': [v, v, v, v, v, v, v, v], 'dist_en': [0, 0, 0, 0, 0, 0, 0, 0],
                              'dist_cache': [[], [], [], [], [], [], [], []]}
        self.tag_list = {0:copy.deepcopy(self.tag_list_item_default),
                         }
        for i in self.curr_used_tag_no:
            self.tag_list[i] = copy.deepcopy(self.tag_list_item_default)

        self.tag_list_cache_item_default={'dist': [[], [], [], [], [], [], [], []]}
        # 每个标签的距离缓存，每秒钟会有总共约48个距离，取平均后放入tag_list
        self.tag_list_cache = {1: copy.deepcopy(self.tag_list_cache_item_default),
                               }
        for i in self.curr_used_tag_no:
            self.tag_list_cache[i] = copy.deepcopy(self.tag_list_cache_item_default)


        self.tag_list_cache_ready_cnt = 10  # 用于缓存几个数据，就可以进行平均放入tag_list中的设置。默认10各数据。

        self.dist_decode_cnt = {1: 0}

        """标签20 21 的加速度"""
        # 标签20 21 加速度
        self.tag_a_xyz_item_default = {'x': 0, 'y': 0, 'z': 1}
        self.tag_a_xyz = {1: copy.deepcopy(self.tag_a_xyz_item_default),}
        for i in self.curr_used_tag_no:
            self.tag_a_xyz[i] = copy.deepcopy(self.tag_a_xyz_item_default)



        # 标签20 21 缓存加速度，多个加速度求平均值后，添加到 tag_a_xyz
        self.tag_a_xyz_cache_item_default = {'x': [], 'y': [], 'z': []}

        self.tag_a_xyz_cache = {20: copy.deepcopy(self.tag_a_xyz_cache_item_default),                                }
        for i in self.curr_used_tag_no:
            self.tag_a_xyz_cache[i] = copy.deepcopy(self.tag_a_xyz_cache_item_default)

        self.tag_a_xyz_cache_count = {}

        # 标签测距错误数、测距总次数
        self.biaoqian_jizhan_error = {20: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                                      }
        for i in self.curr_used_tag_no:
            self.biaoqian_jizhan_error[i] = [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]


        # 标签位置
        self.tag_pos = {20: {'pos_x': 0, 'pos_x_max': 0, }}
        for i in self.curr_used_tag_no:
            self.tag_pos[i] = {'pos_x': 0, 'pos_x_max': 0, }


        # 标签位置的最大值，最小值
        self.tag_pos_error = {20: {'x': [0, 0], 'y': [0, 0], 'z': [0, 0]},
                              }
        for i in self.curr_used_tag_no:
            self.tag_pos_error[i] = {'x': [0, 0], 'y': [0, 0], 'z': [0, 0]}

    def clear_measure1_reg(self):
        """
        清除寄存器0x2f->0x36 8个寄存器
        :return:
        """
        ret = self.write_modbus_h(0x2f, 8, b'\x00' * 16)

    def set_basic_info_h(self, tag_no_list, except_anchor_list=None):
        """
        设置测距的基本信息。会通过bulk模式发送
        :param tag_no_list:[20,21,22,23,24] tag_no_list that will be used
        :param except_anchor_list: anchor that will be excluded. 默认的是空。
        :return:
        """

        self.bulk_mode = 1
        # 基站: B H :14379
        # 基本设置
        self.set_buardrate_h()
        self.set_modbus_id_h(1)
        self.set_device_measure_mode_h()
        self.set_device_mode_h()
        self.set_device_id_h()
        self.set_comm_channel_and_speed_h(2, 2)
        #self.set_kalman_h()
        self.set_recv_delay_h()
        #self.clear_measure1_reg()

        # 使能基站
        if except_anchor_list is None:
            except_anchor_list = []
        except_anchor_list.extend([i for i in self.anchor_used_dict if not self.anchor_used_dict[i]])

        self.curr_used_anchor_no = []
        for i in range(7):
            if except_anchor_list is not None:
                if i in except_anchor_list:
                    continue
            self.curr_used_anchor_no.append(i)

        self.set_anchor_enable_h(except_anchor_list)


        #self.curr_anchor_stat = {i: {'cnt': 0, 'success': 0} for i in self.curr_used_anchor}
        self.curr_used_tag_no=copy.deepcopy(tag_no_list)
        self.set_label_h(tag_no_list)  # 使用标签
        self.set_label_num_h(len(tag_no_list))  # 标签数量 1

        self.bulk_send()
        self.bulk_mode = 0

        # curr_used_tag_no curr_used_anchor_no updated up.
        self.set_cache_data_to_default()

        time.sleep(0.1)  # 0.5

    def decode_measure(self, payload63: bytes, pkt_has_height=1):
        battery_anchor = []
        battery_tag = {}
        tag_id = int.from_bytes(payload63[3:5], 'big')  # 标签id
        status_en = int.from_bytes(payload63[5:7], 'big')

        tag_xyz = payload63[7:13]
        dist_abcdefgh = payload63[13:29]
        max_noise = payload63[29:31]
        std_noise = payload63[31:33]
        path_param = payload63[33:45]
        if pkt_has_height:  # 新的 可以拿到 基站、标签电量信息
            acce_x = payload63[45:47]  # x重力加速度
            acce_y = payload63[47:49]
            acce_z = payload63[49:51]
            """
            20211221吊车实地测试问题： -----------z数据： 角度会有跳跃波动问题 ??? 有复现，已解决
                解决方法：当acce_x、acce_y、acce_z值均为b'\x00\x00'时，将角速度置为空
            """
            if acce_x == b'\x00\x00' and acce_y == b'\x00\x00' and acce_z == b'\x00\x00':
                acce_x = b''
                acce_y = b''
                acce_z = b''
            no_use_xyz = payload63[51:61]  # 电量： ABCDEFGH、当前测得标签的电量、FF占位
            crc = payload63[61:63]
        else:  # 原始代码
            acce_x = b''
            acce_y = b''
            acce_z = b''
            no_use_xyz = b''
            crc = payload63[45:47]

        # 处理 电量
        # DONE: 电量的显示
        battery_dict = {}
        if len(no_use_xyz) > 0:
            ba = []
            for i in range(8):
                battery_anchor.append(int.from_bytes(no_use_xyz[i:i + 1], 'big'))

            battery_tag[tag_id] = int.from_bytes(no_use_xyz[8:9], 'big')

        # 处理距离
        """
        dista = [0 for i in range(8)]
        dista[0] = int.from_bytes(dist_abcdefgh[0:2], 'big')
        dista[1] = int.from_bytes(dist_abcdefgh[2:4], 'big')
        dista[2] = int.from_bytes(dist_abcdefgh[4:6], 'big')
        dista[3] = int.from_bytes(dist_abcdefgh[6:8], 'big')
        dista[4] = int.from_bytes(dist_abcdefgh[8:10], 'big')
        dista[5] = int.from_bytes(dist_abcdefgh[10:12], 'big')
        dista[6] = int.from_bytes(dist_abcdefgh[12:14], 'big')
        dista[7] = int.from_bytes(dist_abcdefgh[14:16], 'big')
        """
        dista = []
        for i in range(8):
            dista.append(int.from_bytes(dist_abcdefgh[i * 2:i * 2 + 2], 'big'))
        logger.debug('tag_id=%s dista=%s en=%s battery_tag=%s battery_anchor=%s accel=%s %s %s',
                     tag_id, dista, status_en, battery_tag, battery_anchor, acce_x, acce_y, acce_z)
        return tag_id, dista, battery_tag, battery_anchor, acce_x, acce_y, acce_z, status_en, [max_noise, std_noise,
                                                                                               path_param]

    def is_anchor_exist_h(self, client_id, loop_max=3):
        self.bulk_mode = 0
        # logger.info('if_jizhan_exist: client_id=%s', client_id)
        is_ok, data_ret = self.convert_anchor_to_tag_h(client_id, loop_max)

        is_ok2, data_ret2 = self.convert_tag_to_anchor_h(client_id, loop_max)

        if is_ok or is_ok2:
            # logger.info('client_id=%s exists', client_id)
            return True
        else:
            # logger.info('client_id=%s not exists', client_id)

            return False

    def if_tag_exist_h(self, client_id, loop_max=5):
        client_no = client_id_get_no(client_id)
        self.set_basic_info_h([client_no], [1, 2, 3, 4, 5, 6])
        for i in range(loop_max):
            x, y, dist = self.get_dist_of_tag_once(1)
            for d in dist:
                if (d != 0) and (d != 0.0) and (d != self.EMPTY_DIST_VAL):
                    return True

        return False

    def get_dist_of_tag_once(self, loop_mean_cnt=20):
        """
        获取标签距离，默认平均20次
        """
        dist_all = []
        dist_list = []

        for i in range(loop_mean_cnt):
            x, y, dist_b = self.get_dist_of_tag_once_inner_h()
            dist_list.append(dist_b)
            # print(str(i)+'-次数---------: ', dist_b)
        # 求多次测距平均值
        d_dict = self.convert_mean(dist_list)
        # print('平均值: ', d_dict)
        return 0, 0, d_dict

    def convert_mean(self, dist_list):
        """
        求均值函数
        :param dist_list:
        :return:
        """
        d_dict = [[], [], [], [], [], [], [], []]

        # 将多次测量结果整合
        for i in dist_list:
            for j in range(7):
                d_dict[j].append(i[j])
        # 去掉值为0的数据
        for i in d_dict:
            new_l = []  # 存放不为0的数据
            for j in i:
                if j != 0:
                    new_l.append(j)
            i_index = d_dict.index(i)
            d_dict[i_index] = new_l
        for i in d_dict:
            i.sort()
            if len(i) >= 3:  # 列表长度大于等于3时，去掉最大最小值
                index = d_dict.index(i)
                d_dict[index] = i[1:-1]
        #  求距离 平均值
        for i in d_dict:
            if len(i) > 0:
                avg = sum(i) / len(i)
            else:
                avg = 0
            i_index = d_dict.index(i)
            d_dict[i_index] = avg

        return d_dict














