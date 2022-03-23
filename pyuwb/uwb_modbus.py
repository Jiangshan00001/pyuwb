import copy
import time
from .calc_crc import calc_crc, check_crc
from .modbus_pkt import get_read_pkt, get_write_pkt, decode_read_return, decode_write_return, split_packet
import serial
from .mylog import logging

logger = logging.getLogger(__name__)


LABEL_NUM_ADDR = 0x29
LABEL_START_ADDR=0x37
BAUDRATE_ADDR=0x00
MODBUS_ID_ADDR=0x01
DEVICE_MODE_ADDR = 3
DEVICE_ID_ADDR = 4
DEVICE_CHANNEL_AND_SPEED_ADDR=5
DEVICE_ANTENNA_DELAY_ADDR=8
KALMAN_PARAM_ADDR=6
MEASURE_MODE_ADDR=2
CONVERT_ANCHOR_TAG_PARAM_ADDR=0x8d
CONVERT_ANCHOR_TAG_START_CMD_ADDR=0x28

class UwbModbus():
    def __init__(self):
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


    def connect(self, com_port=None):
        """连接串口"""
        try:
            self.port_name = com_port
            if self.port_name is None:
                self.port_name = self.detect_com_port()

            if self.port_name is None:
                print('找不到主基站设备')
                return 'error'

            print('端口号：', self.port_name)
            print('self.port_name：', self.port_name)

            self.port = serial.Serial(port=self.port_name, baudrate=115200, timeout=0.1)  # , timeout=0.1
            print('self.port：', self.port)
            self.port.close()
            if not self.is_port_open():
                self.port.open()
            return 'ok'
        except Exception as e:
            pass
            print('串口连接失败', e)
            return 'error'

    def _demo_write_data(self, data):
        if self.demo_inst is None:
            return
        return self.demo_inst.write(data)

    def _write_data(self, data):
        # logger.debug('write_data: %s %s', data.hex(), '123456')

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
                # logger.error('串口错误?')
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
                    # logger.error('串口错误?')
                    self.port.close()
                    self.port.open()
                    data_get += self.port.read(1024)

            # logger.debug('read_data: %s', data_get.hex())
            if byte_max > 0 and byte_max <= len(data_get):
                break

        # logger.debug('read_data_ret: %s', data_get.hex())

        return data_get

    def check_crc(self, payload: bytes):
        """

        :param payload: 带校验和的报文，最后2byte的校验和会被用于比较
        :return: 正确返回True, 否则返回false
        """
        return check_crc(payload)

    def read_modbus_h(self, add2, reg_count, id=1):
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

        to_w = get_read_pkt(add2, reg_count,id)

        self._write_data(to_w)
        to_read_len = 5 + reg_count * 2
        ret = self._read_data(1, to_read_len)

        ret2 = decode_read_return(ret,reg_count)
        return ret2


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
        # logger.debug('write_modbus_real: %s %s %s %d', add2.to_bytes(2, 'big').hex(), reg_count.to_bytes(1, 'big').hex(),
        #             dat.hex(), id)

        to_r = get_write_pkt(add2, reg_count,dat, id)

        if just_gen_pkt:
            # logger.debug("write_modbus_real just_gen_pkt=1 do not send")
            return to_r

        self._write_data(to_r)
        ret = self._read_data(1, 8)

        return decode_write_return(ret)


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
        # logger.debug('write_modbus: %s %s %s %d', add2.to_bytes(2, 'big').hex(), reg_count.to_bytes(1, 'big').hex(),
        #             dat.hex(), id)

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


    def set_label_h(self, label_no_list=[0]):
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

        self.write_modbus_h(LABEL_START_ADDR, (label_cnt + 1) // 2, label_dat)
        # 因为设置标签都是bulk模式，所以此处不需要sleep
        if not self.bulk_mode:
            time.sleep(0.5)

    def set_label_num_h(self, num: int):
        # logger.info('设置标签数：%d', num)
        num_b = num.to_bytes(2, 'big')
        self.write_modbus_h(LABEL_NUM_ADDR, 1, num_b)
        # 因为此处是bulk模式，所以此处不需要sleep
        if not self.bulk_mode:
            time.sleep(0.5)

    def set_buardrate_h(self, rate_no=7):
        """
        设备串口通讯波特率
        :param rate_no:0：4800  1：9600 2：14400 3：19200 4：38400 5：56000 6：57600 7：115200  8：128000 9：256000
        :return:
        """
        self.write_modbus_h(BAUDRATE_ADDR, 1, rate_no.to_bytes(2, 'big'))

    def set_modbus_id_h(self, id=1):
        self.write_modbus_h(MODBUS_ID_ADDR, 1, id.to_bytes(2, 'big'))

    def set_device_measure_mode_h(self, cmode=1, dmode=0):
        """
        :param cmode:测量模式   0：DS-TWR 1：高性能TWR。
        :param dmode:测距模式 1:二维模式 2：三维模式"
        :return:
        """
        self.write_modbus_h(MEASURE_MODE_ADDR, 1, cmode.to_bytes(1, 'big') + dmode.to_bytes(1, 'big'))

    def set_device_mode_h(self, mode=2):
        """

        :param mode:设备模式 0：标签 1：次基站 2：主基站
        :return:
        """
        self.write_modbus_h(DEVICE_MODE_ADDR, 1, mode.to_bytes(2, 'big'))

    def set_device_id_h(self, device_id=0):
        """
        设备ID，高8位为次基站ID，范围0~6 ，
        低8位为标签ID ，0~99
        （程序内部 标签ID为0~247  次基站ID为248~254  主基站ID为255）
        :param device_id:
        :return:
        """
        self.write_modbus_h(DEVICE_ID_ADDR, 1, device_id.to_bytes(2, 'big'))

    def set_comm_channel_and_speed_h(self, channel=1, speed=2):
        """
        byte0-空中信道，byte1-空中传输速率

        :param channel:
        :param speed:
        :return:
        """
        self.write_modbus_h(DEVICE_CHANNEL_AND_SPEED_ADDR, 1, channel.to_bytes(1, 'big') + speed.to_bytes(1, 'big'))

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
        return self.write_modbus_h(DEVICE_ANTENNA_DELAY_ADDR, 1, delay.to_bytes(2, 'big'), just_gen_pkt=just_gen_pkt)



    def set_anchor_enable_h(self, jizhan_index=0, enabled=1):
        """
        基站固定的有7个。编号为0-6. 对应 BCDEFGH
        :param jizhan_index:基站编号 0-6
        :return:
        """
        if jizhan_index > 6 or jizhan_index < 0:
            # logger.error("基站编号超过范围：%s", jizhan_index)
            return
        # logger.info('设置基站使能 %d %d', jizhan_index, enabled)
        #FIXME: 此处基站使能地址不连续???
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
        self.write_modbus_h(CONVERT_ANCHOR_TAG_START_CMD_ADDR, 1, mode.to_bytes(2, 'big'))
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
        ret = self.read_modbus_h(0x8e, 1)
        if 'crc_ok' not in ret:
            return False
        if not ret['crc_ok']:
            return False
        if ret['data'] != b'\x00\x03':
            print('is_convert_complete: ', ret['data'].hex())
            return False
        print('is_convert_complete OK')
        return True

    def convert_tag_to_anchor_once_h(self, client_id):
        """
        将标签 转化为 次基站
        """
        print('将标签 转化为 次基站: 次基站 ', client_id)
        # 将标签0改为B基站 ：  01 10 00 8d 00 02 04 00 00 00 02 A1 BB
        # 开始修改 ：  01 10 00 28 00 01 02 00 05 A1 BB
        jizhan_id = int(client_id[-1]).to_bytes(1, 'big')
        self.write_modbus_h(CONVERT_ANCHOR_TAG_PARAM_ADDR, 2, jizhan_id + b'\x00\x00\x02')
        time.sleep(0.5)
        ret = self.write_modbus_h(CONVERT_ANCHOR_TAG_START_CMD_ADDR, 1, b'\x00\x05')
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

        jizhan_id = int(client_id[-1]).to_bytes(1, 'big')
        self.write_modbus_h(CONVERT_ANCHOR_TAG_PARAM_ADDR, 2, jizhan_id + b'\x00\x00\x01')
        time.sleep(0.2)
        ret = self.write_modbus_h(CONVERT_ANCHOR_TAG_START_CMD_ADDR, 1, b'\x00\x05')
        return ret

    def convert_anchor_to_tag_h(self, client_id, loop_max_cnt=5):
        self.bulk_mode = 0
        ret=None
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
