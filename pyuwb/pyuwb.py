import copy
import serial
import serial.tools.list_ports
import time
import math
from numpy import short
from .calc_crc import calc_crc
from .anchor_locate_algorithm1 import AnchorLocateAlgorithm1
from .tag_locate_algorithm1 import TagLocateAlgorithm1
from .uwb_modbus import UwbModbus, split_packet
from .detect_com_port import is_anchor0
from .client_id_utils import client_id_get_no, client_id_get_type, pack_client_id, client_id_remove_group
from .dist_list_dict_convert import dist_list2dict

from .mylog import logging

logger = logging.getLogger(__name__)


def get_cali_param_all():
    return {
        '2-0': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '2-1': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '2-2': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '2-3': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '2-4': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '2-5': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '3-1': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '3-2': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '3-3': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '3-4': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '3-20': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '3-21': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
    }


class uwb_zrzn(UwbModbus):

    def set_pos_callback(self, callback_func):
        self.pos_callback = callback_func

    # 检测周围所有设备
    def detect_device(self, tag_no_list=None, anchor_no_list=None):
        """
        如果是空列表，则基站会检测：0,1,2,3,4,5,6,7存在不存在，标签会检测：1-10存在不存在
        :param tag_no_list:  如果是空标签会检测：1-10存在不存在
        :param anchor_no_list:
        :return:
        """
        if tag_no_list is None or tag_no_list == []:
            tag_no_list = [i+1 for i in range(10)]
        if anchor_no_list is None or anchor_no_list == []:
            anchor_no_list = [i for i in range(8)]

        tag_client_list = [pack_client_id(self.group_id, 3, i) for i in tag_no_list]
        anchor_client_list = [pack_client_id(self.group_id, 2, i)for i in anchor_no_list]

        """检测设备是否存在"""
        # 避免上次通讯错误，导致0标签的存在
        self.bulk_mode = 0
        self.convert_tag_to_anchor_h('0-0-0', 3)
        for i in anchor_client_list.copy():
            client_id = i
            if self.is_demo_mode:
                loop_max = 1
            else:
                loop_max = 3
            if self.if_jizhan_exist(client_id, loop_max):
                pass
            else:
                print('基站' + client_id + '测试通讯失败.去除此设备')
                anchor_client_list.remove(client_id)

        time.sleep(1)
        self.if_biaoqian_exist('1-3-1')
        time.sleep(1)

        for i in tag_client_list.copy():
            client_id = i
            if self.is_demo_mode:
                loop_max = 1
            else:
                loop_max = 5
            if self.if_biaoqian_exist(client_id, loop_max):
                pass
            else:
                print('标签' + client_id + '测试通讯失败.去除此设备')
                tag_client_list.remove(client_id)

        tag_no_list= [ client_id_get_no(i) for i in tag_client_list]
        anchor_no_list = [ client_id_get_no(i) for i in anchor_client_list]
        self.set_device(tag_no_list, anchor_no_list)

    # 显示当前所有设备及相关测距信息
    def device_list(self):
        # print('所有使用的设备信息：', self.all_device_list)
        ret = []
        for i in self.all_device_list:
            d = {}
            d['client_id'] = i['client_id']
            d['pos'] = i['pos']
            ret.append(d)
        return ret

    def tag_no_list(self):
        used_tag_no_list = []
        for i in self.all_device_list:
            tag_type = client_id_get_type(i['client_id'])
            tag_no = client_id_get_no(i['client_id'])
            if tag_type == 3:
                used_tag_no_list.append(tag_no)
        return used_tag_no_list

    def anchor_no_list(self):
        used_anchor_no_list = []
        for i in self.all_device_list:
            tag_type = client_id_get_type(i['client_id'])
            tag_no = client_id_get_no(i['client_id'])
            if tag_type == 2:
                used_anchor_no_list.append(tag_no)
        return used_anchor_no_list

    def set_device(self, tag_no_list, anchor_no_list, using_master=0):
        """
        如果不需要检测设备，直接指定设备列表也可以 (tag_no_list：标签列表，anchor_no_list：次基站列表，using_master：是否使用主基站测距【1代表使用，0代表不使用】)
        """
        self.all_device_list = []
        for i in tag_no_list:
            tag_client_id = pack_client_id(self.group_id, 3, i)
            self.all_device_list.append({'client_id': tag_client_id, 'dist': [], 'pos': []})
        for i in anchor_no_list:
            anchor_client_id = pack_client_id(self.group_id, 2, i)
            self.all_device_list.append({'client_id': anchor_client_id, 'dist': [], 'pos': []})

        self.all_device_dict = {i['client_id']: i for i in self.all_device_list}

        # 使能设备
        for i in self.anchor_used_dict.copy():
            if i not in anchor_no_list:
                self.anchor_used_dict[i] = 0
            else:
                self.anchor_used_dict[i] = 1
            print('当前启动的基站列表', self.anchor_used_dict)

    def locate_anchor(self, height_list=[0.5, 1.1, 0.5, 1.1], direction_point=['N', 'S', 'E'], measure_ready_cnt=40):
        """
        对基站坐标进行定位：
        1 测距：各基站到其他基站的距离：
        2 计算位置：根据距离和高度参数，以及顺序位置，建立坐标系
        :param height_list:高度列表，需要和设备数一致
        :param measure_ready_cnt:测距次数，多次测量取均值，用于提高测距精度，进而提高定位精度
        :return:
        """
        # 定位次基站
        anchor_list, tag_info = self.get_jizhan_and_biaoqian_info()

        # 次基站之间测距
        anchor_list = self.anchor_zidong_ceju(anchor_list, measure_ready_cnt)

        for i in range(len(anchor_list)):
            if i<len(direction_point):
                anchor_list[i]['direction_point'] = direction_point[i]
            else:
                anchor_list[i]['direction_point'] = None
            if i<len(height_list):
                anchor_list[i]['height'] = height_list[i]
            else:
                anchor_list[i]['height'] = None


        self.anchor_locate_algorithm.set_anchor_info(anchor_list)
        self.anchor_locate_algorithm.calc()
        anchor_pos_list = self.anchor_locate_algorithm.get_anchor_pos()

        # FIXME:此处调用set_anchor_location 进行位置设置-2022.3.23
        self.set_anchor_location(anchor_pos_list)

        return anchor_pos_list

    def set_anchor_location(self, anchor_pos, using_master=0):
        """

        :param anchor_pos:[{client_id:'1-2-0', pos:{x:, y:, z:}} ]
        :param using_master:False/True
        :return:
        """
        # 如果不检测定位基站，或者上次已经检测的定位过，则可以直接设置基站的坐标位置
        anchor_pos_list = anchor_pos
        # 将基站位置同步到内存 self.all_device_list
        for i in range(len(self.all_device_list)):
            for j in anchor_pos_list:
                if self.all_device_list[i]['client_id'] == j['client_id']:
                    self.all_device_list[i]['pos'] = j['pos']
        # 显示基站位置

    def start_locate(self):
        pass

    # 定位一次 标签
    def start_locate_once(self):
        anchor_client_list, tag_client_list = self.get_jizhan_and_biaoqian_info()
        # 标签与次基站之间的距离
        self.biaoqian_zidong_ceju(tag_client_list)

        ret_tag_dict = {}
        # FIXME: 此处获取各标签位置，传入 定位算法函数，获取返回值-2022.3.23
        # 各标签列表：[{client_id:, dist:{1-2-0:50,1-2-1:30},...},...]
        for i in tag_client_list:
            tag_client_id = i['client_id']
            tag_dist = self.tag_list[client_id_get_no(tag_client_id)]['dist']
            ret = self.tag_locate_algorithm.calc(tag_dist, tag_client_id, anchor_client_list)
            self.all_device_dict[tag_client_id]['pos'] = ret
            ret_tag_dict[tag_client_id] = ret

        # 结束
        return ret_tag_dict

    def get_distance(self, client_id1, client_id2):
        """
        测量获取距离
        :param client_id1:
        :param client_id2:
        :return: 两个设备间的距离，单位m
        """
        # 测 次基站和次基站之间的距离 或 次基站和标签之间的距离
        if client_id_get_type(client_id1) == 3 or client_id_get_type(client_id2) == 3:
            # 存在 标签
            if client_id_get_type(client_id1) == 3 and client_id_get_type(client_id2) == 3:
                print('get_distance error：不能输入两个标签')
                return
            if client_id_get_type(client_id1) == 3:
                tag_client_id = client_id1
                anchor_client_id = client_id2
            else:# client_id_get_type(client_id2) == 3:
                tag_client_id = client_id2
                anchor_client_id = client_id2

            # 标签和基站之间测距
            dist = self.biaoqian_zidong_ceju(tag_client_list=[{'client_id': tag_client_id, 'dist': {}}],
                                      anchor_client_list=[{'client_id': anchor_client_id, 'dist': {}}])
            return dist[0][anchor_client_id]
            #for i in self.all_device_list:
            #    if i['client_id'] == tag_client_id:
            #        return i['dist'][client_id_get_no(anchor_client_id)]
        else:
            # 两个次基站 测距
            self.anchor_zidong_ceju([{'client_id': client_id1, 'dist': {}}, {'client_id': client_id2, 'dist': {}}])
            for i in self.all_device_list:
                if i['client_id'] == client_id1:
                    return i['dist_list'][client_id_get_no(client_id2)]
                elif i['client_id'] == client_id2:
                    return i['dist_list'][client_id_get_no(client_id1)]

        print('打印get_distance=================', self.all_device_list)

    # ==================================
    # ==================================
    # ==================================
    # ==================================
    def __init__(self):
        super(uwb_zrzn, self).__init__()

        self.EMPTY_DIST_VAL = -1  # 空的距离位置值
        self.anchor_used_dict = {0: 1, 1: 1, 2: 1, 3: 1, 4: 1, 5: 1, 6: 0}  # 当前启动的基站列表，默认是6个
        self.all_device_list = []
        self.all_device_dict = {}
        self.curr_anchor_to_measure = None  # 当前正在测距的次基站
        self.battery_anchor = [255, 255, 255, 255, 255, 255, 255, 255]
        self.battery_tag = {20: 255, 21: 255, 22: 255, 23: 255, 24: 255, 25: 255, 1: 255, 2: 255, 3: 255, 4: 255,
                            5: 255, 6: 255}
        self.measure_mode = 0  # mode=3,4时，才会接收并处理数据
        self.curr_used_anchor = []
        self.set_cache_data_to_default()
        self.cali_param = get_cali_param_all()

        self.anchor_locate_algorithm = AnchorLocateAlgorithm1()
        self.tag_locate_algorithm = TagLocateAlgorithm1()
        self.group_id = 1  # device group
        self.pos_callback = None

    def get_jizhan_and_biaoqian_info(self):
        """

        :return: [{client_id:, pos:{x:,y:,z:}}], [{client_id:, pos:{x:,y:,z:}}]
        """
        # 从内存self.all_device_list中获取 基站 和 标签信息
        tag_client_list = []
        anchor_client_list = []
        for i in self.all_device_list:
            if client_id_get_type(i['client_id']) == 2:
                anchor_client_list.append(i)
            elif client_id_get_type(i['client_id']) == 3:
                tag_client_list.append(i)
        return anchor_client_list, tag_client_list



    def anchor_zidong_ceju(self, anchor_client_list, measure_ready_cnt=40):
        """
        基站的测距：
        :param anchor_client_list: [ {client_id:'1-2-3', }]
        :return:
        """
        all_anchor_client_id_list = [i['client_id'] for i in anchor_client_list]
        ret = []
        for i in all_anchor_client_id_list:
            reti = {'client_id': i}
            reti['dist'] = self.measure_one_anchor_dist(i, measure_ready_cnt)
            ret.append(reti)
        print("基站自动测距结束")
        return ret

    def set_to_start(self, tag_no_list=None, ready_cnt=30, start_cmd=6):

        if tag_no_list is None:
            tag_no_list = self.tag_no_list()
        self.set_basic_info(tag_no_list)  # self.uwb.set_cache_data_to_default()内部会调用此函数

        self.tag_list_cache_ready_cnt = ready_cnt
        self.start_measure_h(start_cmd)

    def locate_loop(self, tag_no_list=None, wait_for_finish=0, timeout=10.0):
        """
        测量循环
        :param tag_no_list:
        :param wait_for_finish:
        :param timeout:
        :return:
        """
        # 多次测量取平均值

        if tag_no_list is None:
            tag_no_list = self.tag_no_list()
        cijizhan_no_list = self.anchor_no_list()

        self.measure_read()
        if not wait_for_finish:
            return

        time_start = time.time()
        unfinished_tag = copy.deepcopy(tag_no_list)

        while time.time() - time_start < timeout:
            self.measure_read()
            if wait_for_finish:
                ready_tag = []
                if len(unfinished_tag) == 0:
                    break
                for i in unfinished_tag:
                    nz_cnt = 0
                    for j in self.tag_list[i]['dist']:
                        if j != self.EMPTY_DIST_VAL:
                            nz_cnt += 1
                    if nz_cnt >= len(cijizhan_no_list):
                        ready_tag.append(i)

                for i in ready_tag:
                    unfinished_tag.remove(i)
                ready_tag.clear()

        if wait_for_finish:
            if len(unfinished_tag) > 0:
                print('测量标签位置失败 1-3-', unfinished_tag)
            else:
                print('测量标签位置完成 1-3-', tag_no_list)

    def biaoqian_zidong_ceju(self, tag_client_list, anchor_client_list=None):
        """

        :param tag_client_list:[{client_id:,}, ...]
        :param anchor_client_list:[{client_id:,}, ...]
        :return:
        """
        tag_client_id_list = [i['client_id'] for i in tag_client_list]
        tag_no_list = [client_id_get_no(i) for i in tag_client_id_list]

        if anchor_client_list is None:
            anchor_client_list, tinfo = self.get_jizhan_and_biaoqian_info()

        cijizhan_no_list = [client_id_get_no(i['client_id']) for i in anchor_client_list]
        self.set_to_start(tag_no_list)
        self.locate_loop(tag_no_list, 1, 10)

        self.stop_measure_h()
        self.tag_list_cache_ready_cnt = 10


        for tt in self.all_device_list:
            tag_no = client_id_get_no(tt['client_id'])
            if tag_no in tag_no_list:
                tt['dist'] = dist_list2dict(self.tag_list[tag_no]['dist'])

        dist_all=[]
        for i in tag_client_list:
            dist_all.append(dist_list2dict(self.tag_list[ client_id_get_no(i['client_id'])]['dist'], self.group_id))

        return dist_all
    def start_anchor_dist_measure(self, client_id, ready_cnt=40):
        self.curr_anchor_to_measure = client_id  # FIXME: client_id[2:]
        self.bulk_mode = 0
        print("基站自动定位测距：", client_id)

        self.bulk_mode = 0
        # 基站转标签
        is_ok, ret = self.convert_anchor_to_tag_h(client_id)
        if not is_ok:
            return is_ok
        time.sleep(0.25)

        # 设置基站和标签参数
        except_list = [client_id_get_no(client_id)]
        except_list = list(set(except_list))
        self.set_basic_info([0], except_list)

        # 启动测量
        self.tag_list_cache_ready_cnt = ready_cnt
        self.start_measure_h(6)
        return True

    def tag_a_process(self, tag_id, acce_x, acce_y, acce_z):
        """向tag_a_xyz中添加 标签20 21 的加速度"""
        if tag_id not in self.tag_a_xyz_cache_count:
            self.tag_a_xyz_cache_count[tag_id] = 0
        self.tag_a_xyz_cache_count[tag_id] += 1
        if acce_x != '':
            self.tag_a_xyz_cache[tag_id]['x'].append(short(int.from_bytes(acce_x, 'big')) * 16 / 32768)
        if acce_y != '':
            self.tag_a_xyz_cache[tag_id]['y'].append(short(int.from_bytes(acce_y, 'big')) * 16 / 32768)
        if acce_z != '':
            self.tag_a_xyz_cache[tag_id]['z'].append(short(int.from_bytes(acce_z, 'big')) * 16 / 32768)
        if self.tag_a_xyz_cache_count[tag_id] > self.tag_list_cache_ready_cnt:
            # print('self.tag_a_xyz_cache: ', self.tag_a_xyz_cache)
            x_sum = 0
            for j1 in range(len(self.tag_a_xyz_cache[tag_id]['x'])):
                x_sum += self.tag_a_xyz_cache[tag_id]['x'][j1]
            if len(self.tag_a_xyz_cache[tag_id]['x']) > 0:
                x_avg = x_sum / len(self.tag_a_xyz_cache[tag_id]['x'])
                self.tag_a_xyz[tag_id]['x'] = x_avg
            y_sum = 0
            for j1 in range(len(self.tag_a_xyz_cache[tag_id]['y'])):
                y_sum += self.tag_a_xyz_cache[tag_id]['y'][j1]
            if len(self.tag_a_xyz_cache[tag_id]['y']) > 0:
                y_avg = y_sum / len(self.tag_a_xyz_cache[tag_id]['y'])
                self.tag_a_xyz[tag_id]['y'] = y_avg
            z_sum = 0
            for j1 in range(len(self.tag_a_xyz_cache[tag_id]['z'])):
                z_sum += self.tag_a_xyz_cache[tag_id]['z'][j1]
            if len(self.tag_a_xyz_cache[tag_id]['z']) > 0:
                z_avg = z_sum / len(self.tag_a_xyz_cache[tag_id]['z'])
                self.tag_a_xyz[tag_id]['z'] = z_avg

            self.tag_a_xyz_cache_count[tag_id] = 0
            self.tag_a_xyz_cache[tag_id] = {'x': [], 'y': [], 'z': []}

    def decode_measure_payload(self, payload63: bytes, pkt_has_height=1):
        """
        解码报文
        :param payload63:
        :param pkt_has_height:
        :return:
        """
        tag_id, dista, battery_tag, battery_anchor, acce_x, acce_y, acce_z, status, noise_param = self.decode_measure(
            payload63, pkt_has_height)
        for i in range(len(self.battery_anchor)):
            if battery_anchor[i] == 255:
                continue
            self.battery_anchor[i] = battery_anchor[i]

        for i in list(battery_tag.keys()):
            if battery_tag[i] == 255:
                del battery_tag[i]
        self.battery_tag.update(battery_tag)

        self.tag_a_process(tag_id, acce_x, acce_y, acce_z)
        self.tag_dist_process(tag_id, dista, status)
        self.count_for_payload_func(tag_id, dista, status, acce_x, acce_y, acce_z)
        return

    def count_for_payload_func(self, tag_id, dista, status, acce_x, acce_y, acce_z):
        """
        测试 运行速度
        :return:
        """

        for i in range(1, 8):
            # 错误统计
            tag_en = ((status & (1 << i)) >> i)
            tag_dist = (dista[i] / 100.0)
            if tag_en and (tag_dist != 0.0):
                self.biaoqian_jizhan_error[tag_id][i - 1][0] += 1
            self.biaoqian_jizhan_error[tag_id][i - 1][1] += 1

        self.count_for_payload += 1
        ctime = time.time()
        if ctime - self.count_for_payload_timer > 3.0:
            self.count_for_payload_pps = round(self.count_for_payload / (ctime - self.count_for_payload_timer), 1)
            print('count_for_payload: %s', self.count_for_payload_pps)
            print('error_status: %s', self.biaoqian_jizhan_error)
            self.count_for_payload = 0
            self.count_for_payload_timer = ctime

    def avg_dist_data(self, data_list, last_data):
        """
            距离数据的平均滤波。避免跳动太大
        :param data_list:
        :param last_data:
        :return:
        """
        print('avg_dist_data 输入 %s %s', data_list, last_data)
        if len(data_list) == 0:
            print('avg_dist_data result:', last_data)
            return last_data, 0
        elif len(data_list) == 1 and last_data == self.EMPTY_DIST_VAL:
            # 针对第一个测距数据可能不对的问题，如果之前没有测距值，现在只有1个测距值，则不使用，等待有多个测距值再用
            return last_data, 0

        if len(data_list) > 5:
            data_list.sort()
            data_list = data_list[2:-2]
        elif len(data_list) > 3:
            data_list.sort()
            data_list = data_list[1:-1]

        dlen = len(data_list)
        dist_avg = sum(data_list) / len(data_list)
        print('avg_dist_data result: %s', dist_avg)
        if (math.fabs(dist_avg - last_data) > 1) and (last_data != self.EMPTY_DIST_VAL):
            print('距离跳跃太大：%s %s %s', data_list, dist_avg, last_data)
        return dist_avg, 1

    def tag_dist_cache_to_one(self, tag_id):
        """
        标签的距离，采用多次测量取平均值的方式
        :return:
        """
        currdist_list = self.tag_list_cache[tag_id]['dist']
        print('tag_id= %s 距离测距次数:%s', tag_id, self.dist_decode_cnt[tag_id])
        print('距离测距数值:%s', currdist_list)

        for i in range(len(currdist_list)):
            anchor_index = i
            anchor_dist = currdist_list[i]

            ###统计基站测距次数和成功次数

            ###

            if len(anchor_dist) > 0:
                curr_val, curr_val_en = self.avg_dist_data(anchor_dist, self.tag_list[tag_id]['dist'][i])
                if tag_id == 0:
                    # 某一个次基站（0标签）正在测距
                    tag_id_c = self.curr_anchor_to_measure  # 1-2-0
                else:
                    # 某一个标签正在测距 20、21、1、2、3、4
                    tag_id_c = pack_client_id(self.group_id, 3, tag_id)
                #  tag_id：2-4或3-20，anchor_id：0-5之间的一个数字，curr_val：距离，cali_param：计算参数
                curr_val = self.data_cali_v2(client_id=tag_id_c, anchor_id_n=i, curr_val=curr_val,
                                             cali_param=self.cali_param)
                if i > 5:
                    break

                self.tag_list[tag_id]['dist'][i] = curr_val
                self.tag_list[tag_id]['dist_en'][i] = curr_val_en
                self.tag_list[tag_id]['dist_cache'][i] = currdist_list[i]

            self.tag_list_cache[tag_id]['dist'][i] = []

        self.one_tag_dist_got(tag_id)

    def one_tag_dist_got(self, tag_id):
        """
        每次接收到1次设备发来的标签距离信息，则会调用此函数
        :param tag_id:
        :return:
        """

        ainfo, tinfo = self.get_jizhan_and_biaoqian_info()
        dist = dist_list2dict(self.tag_list[tag_id]['dist'], self.group_id)
        if tag_id!=0:
            pos = self.tag_locate_algorithm.calc(dist, pack_client_id(self.group_id, 3, tag_id), ainfo)
        else:
            pos={'x':0, 'y':0, 'z':0}
        if self.pos_callback is not None:
            self.pos_callback(tag_id, dist, pos)

    def tag_dist_process(self, tag_id, dista, status):
        """
        处理距离
        :param dista:
        :param status:
        :param tag_id:
        :return:
        """
        if tag_id not in self.tag_list:
            print('tag_id not in self.tag_list:', tag_id, self.tag_list)
            raise ValueError('tag_id不在tag_list中' + str(tag_id))

        """向tag_list中添加对应标签到各次基站的距离"""
        for i in range(0, 8):
            tag_en = ((status & (1 << i)) >> i)
            tag_dist = (dista[i] / 100.0)
            if tag_en and (tag_dist != 0.0):
                self.tag_list_cache[tag_id]['dist'][i].append(tag_dist)
        # logger.info('打印标签到各基站的距离列表多次： %s %s ', tag_id, self.tag_list_cache[tag_id]['dist'])

        if tag_id not in self.dist_decode_cnt:
            self.dist_decode_cnt[tag_id] = 0
        self.dist_decode_cnt[tag_id] += 1

        if self.dist_decode_cnt[tag_id] > self.tag_list_cache_ready_cnt:
            # 转实际值
            self.tag_dist_cache_to_one(tag_id)
            self.dist_decode_cnt[tag_id] = 0

    def data_cali_v2(self, client_id, anchor_id_n, curr_val, cali_param):
        """

        """
        client_id2 = client_id_remove_group(client_id)
        anchor_id = str(anchor_id_n)
        if (client_id2 in cali_param) and (anchor_id in cali_param[client_id2]):
            curr_val *= cali_param[client_id2][anchor_id]
        print('data_cali: %s %s %s', client_id2, anchor_id_n, curr_val)
        print('输出: %s ', curr_val)
        return curr_val

    def measure_read(self, pkt_has_height=1):
        """
        读取串口数据并解码，用于主基站主动发数据的模式
        :param pkt_has_height:
        :return: 此次处理的报文数，此次处理的字节数
        """
        if self.measure_mode != 3 and self.measure_mode != 4 and self.measure_mode != 6:
            return 0, 0
        # 只有3，4模式是主动发送，需要处理报文
        self.read_buf += self._read_data(0.1)
        print('measure_read: ', len(self.read_buf), self.read_error_cnt, self.read_ok_cnt)
        print('measure_read: ', self.read_error_stat)

        pkt_length = 63
        if pkt_has_height == 0:
            pkt_length = 63 - 16

        pkt_list, self.read_buf, read_error_cnt, ret_pkt_process, ret_byte_process = split_packet(self.read_buf,
                                                                                                  pkt_length,
                                                                                                  self.read_error_stat)
        for i in pkt_list:
            self.decode_measure_payload(i, pkt_has_height)

        return ret_pkt_process, ret_byte_process

    def check_anchor_dist_measure_finish(self):
        """
        读取串口测距报文，处理后，查看哪些测距已经完成
        :return:is_finish, 100
        """
        self.measure_read()

        anchor_len = len(self.curr_used_anchor)
        if anchor_len <= 0:
            print('anchor_len: ', anchor_len, self.anchor_used_dict)
            return True, 100

        nz_cnt = 0
        for i in self.tag_list[0]['dist']:
            if i != self.EMPTY_DIST_VAL:
                nz_cnt += 1

        if nz_cnt >= anchor_len:
            print(':测距完成：', self.tag_list[0]['dist'], nz_cnt, anchor_len)
            return True, 100
        if 0 not in self.dist_decode_cnt:
            return False, 0
        return False, [len(i) for i in self.tag_list_cache[0]['dist']]

    def stop_anchor_dist_measure(self, client_id):

        self.stop_measure_h()
        # 转换标签到基站
        ret = self.convert_tag_to_anchor_h(client_id)
        self.tag_list_cache_ready_cnt = 10
        dist_ret = copy.deepcopy(self.tag_list[0]['dist'])
        print('stop_jizhan_dist_measure: ', dist_ret)
        return dist_ret

    def measure_one_anchor_dist(self, client_id, measure_ready_cnt=40, remove_error_device=True):
        """
        测量某个基站到其他基站的距离
        :param client_id:当前要测量的次基站client_id       次基站的id：eg: 1-2-1
        :param all_measure_anchor_client_id:所有使用的次基站client_id ['1-2-1','1-2-2']
        :return:
        """
        # 每个次基站，进行测距

        print('次基站' + client_id + '正在测距中')

        start_ok = self.start_anchor_dist_measure(client_id, measure_ready_cnt)
        if (not start_ok) and remove_error_device:
            print("次基站连接失败 ： 改为不启用，即删除该基站信息", client_id)
            for i in self.all_device_list.copy():
                if i['client_id'] == client_id:
                    self.all_device_list.remove(i)
                    break

        cnt = 0
        while start_ok:
            cnt += 1
            is_finish, percent = self.check_anchor_dist_measure_finish()
            if is_finish:
                break

            print("次基站测距中 client_id： percent----", client_id, percent)

            time.sleep(0.1)
            if cnt > 100:  # 10秒种
                print("基站测距超时失败 ", client_id)
                time.sleep(0.1)
                break

        dist = self.stop_anchor_dist_measure(client_id)

        # dist的list->dict
        # 基站：client_id 到其它基站的距离在dist中，需要写入self.all_device_list
        for i in self.all_device_list:
            if i['client_id'] == client_id:
                i['dist'] = dist_list2dict(dist, self.group_id)
                break
        print('次基站' + client_id + '测距成功, dist:', dist)
        return dist_list2dict(dist, self.group_id)

    def calc_crc(self, payload: bytes):
        """
        :param payload:不校验和的报文
        :return: 返回2byte的校验和
        """
        return calc_crc(payload)

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
            print("The Serial port can't find!")
            return ret

        for i in list(port_list):
            port_name = i[0]
            if is_anchor0(port_name):
                ret = port_name
                print('端口号存在')

        return ret

    def if_jizhan_exist(self, client_id, loop_max=3):
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

    def set_cache_data_to_default(self):
        """标签20 21 到各次基站的距离"""
        # 每个标签的距离
        v = self.EMPTY_DIST_VAL
        self.tag_list = {20: {'dist': [v, v, v, v, v, v, v, v], 'dist_en': [0, 0, 0, 0, 0, 0, 0, 0],
                              'dist_cache': [[], [], [], [], [], [], [], []]},
                         21: {'dist': [v, v, v, v, v, v, v, v], 'dist_en': [0, 0, 0, 0, 0, 0, 0, 0],
                              'dist_cache': [[], [], [], [], [], [], [], []]},
                         22: {'dist': [v, v, v, v, v, v, v, v], 'dist_en': [0, 0, 0, 0, 0, 0, 0, 0],
                              'dist_cache': [[], [], [], [], [], [], [], []]},
                         23: {'dist': [v, v, v, v, v, v, v, v], 'dist_en': [0, 0, 0, 0, 0, 0, 0, 0],
                              'dist_cache': [[], [], [], [], [], [], [], []]},
                         24: {'dist': [v, v, v, v, v, v, v, v], 'dist_en': [0, 0, 0, 0, 0, 0, 0, 0],
                              'dist_cache': [[], [], [], [], [], [], [], []]},
                         25: {'dist': [v, v, v, v, v, v, v, v], 'dist_en': [0, 0, 0, 0, 0, 0, 0, 0],
                              'dist_cache': [[], [], [], [], [], [], [], []]},
                         0: {'dist': [v, v, v, v, v, v, v, v], 'dist_en': [0, 0, 0, 0, 0, 0, 0, 0],
                             'dist_cache': [[], [], [], [], [], [], [], []]},
                         1: {'dist': [v, v, v, v, v, v, v, v], 'dist_en': [0, 0, 0, 0, 0, 0, 0, 0],
                             'dist_cache': [[], [], [], [], [], [], [], []]},
                         2: {'dist': [v, v, v, v, v, v, v, v], 'dist_en': [0, 0, 0, 0, 0, 0, 0, 0],
                             'dist_cache': [[], [], [], [], [], [], [], []]},
                         3: {'dist': [v, v, v, v, v, v, v, v], 'dist_en': [0, 0, 0, 0, 0, 0, 0, 0],
                             'dist_cache': [[], [], [], [], [], [], [], []]},
                         4: {'dist': [v, v, v, v, v, v, v, v], 'dist_en': [0, 0, 0, 0, 0, 0, 0, 0],
                             'dist_cache': [[], [], [], [], [], [], [], []]},
                         5: {'dist': [v, v, v, v, v, v, v, v], 'dist_en': [0, 0, 0, 0, 0, 0, 0, 0],
                             'dist_cache': [[], [], [], [], [], [], [], []]},
                         6: {'dist': [v, v, v, v, v, v, v, v], 'dist_en': [0, 0, 0, 0, 0, 0, 0, 0],
                             'dist_cache': [[], [], [], [], [], [], [], []]},
                         }
        # 每个标签的距离缓存，每秒钟会有总共约48个距离，取平均后放入tag_list
        self.tag_list_cache = {20: {'dist': [[], [], [], [], [], [], [], []]},
                               21: {'dist': [[], [], [], [], [], [], [], []]},
                               22: {'dist': [[], [], [], [], [], [], [], []]},
                               23: {'dist': [[], [], [], [], [], [], [], []]},
                               24: {'dist': [[], [], [], [], [], [], [], []]},
                               25: {'dist': [[], [], [], [], [], [], [], []]},
                               0: {'dist': [[], [], [], [], [], [], [], []]},
                               1: {'dist': [[], [], [], [], [], [], [], []]},
                               2: {'dist': [[], [], [], [], [], [], [], []]},
                               3: {'dist': [[], [], [], [], [], [], [], []]},
                               4: {'dist': [[], [], [], [], [], [], [], []]},
                               5: {'dist': [[], [], [], [], [], [], [], []]},
                               6: {'dist': [[], [], [], [], [], [], [], []]},
                               }

        self.tag_list_cache_ready_cnt = 10  # 用于缓存几个数据，就可以进行平均放入tag_list中的设置。默认10各数据。

        self.dist_decode_cnt = {0: 0, 1: 0, 20: 0, 21: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}

        """标签20 21 的加速度"""
        # 标签20 21 加速度
        self.tag_a_xyz = {20: {'x': 0, 'y': 0, 'z': 1},
                          21: {'x': 0, 'y': 0, 'z': 1},
                          22: {'x': 0, 'y': 0, 'z': 1},
                          23: {'x': 0, 'y': 0, 'z': 1},
                          24: {'x': 0, 'y': 0, 'z': 1},
                          25: {'x': 0, 'y': 0, 'z': 1},
                          0: {'x': 0, 'y': 0, 'z': 1},
                          1: {'x': 0, 'y': 0, 'z': 1},
                          2: {'x': 0, 'y': 0, 'z': 1},
                          3: {'x': 0, 'y': 0, 'z': 1},
                          4: {'x': 0, 'y': 0, 'z': 1},
                          5: {'x': 0, 'y': 0, 'z': 1},
                          6: {'x': 0, 'y': 0, 'z': 1},
                          }
        # 标签20 21 缓存加速度，多个加速度求平均值后，添加到 tag_a_xyz
        self.tag_a_xyz_cache = {20: {'x': [], 'y': [], 'z': []},
                                21: {'x': [], 'y': [], 'z': []},
                                22: {'x': [], 'y': [], 'z': []},
                                23: {'x': [], 'y': [], 'z': []},
                                24: {'x': [], 'y': [], 'z': []},
                                25: {'x': [], 'y': [], 'z': []},
                                0: {'x': [], 'y': [], 'z': []},
                                1: {'x': [], 'y': [], 'z': []},
                                2: {'x': [], 'y': [], 'z': []},
                                3: {'x': [], 'y': [], 'z': []},
                                4: {'x': [], 'y': [], 'z': []},
                                5: {'x': [], 'y': [], 'z': []},
                                6: {'x': [], 'y': [], 'z': []},

                                }
        self.tag_a_xyz_cache_count = {}

        # 标签测距错误数、测距总次数
        self.biaoqian_jizhan_error = {20: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                                      21: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                                      22: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                                      23: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                                      24: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                                      25: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                                      0: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                                      1: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                                      2: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                                      3: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                                      4: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                                      5: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                                      6: [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]],
                                      }
        # 标签位置
        self.tag_pos = {20: {'pos_x': 0, 'pos_x_max': 0, }}
        # 标签位置的最大值，最小值
        self.tag_pos_error = {20: {'x': [0, 0], 'y': [0, 0], 'z': [0, 0]},
                              21: {'x': [0, 0], 'y': [0, 0], 'z': [0, 0]},
                              22: {'x': [0, 0], 'y': [0, 0], 'z': [0, 0]},
                              23: {'x': [0, 0], 'y': [0, 0], 'z': [0, 0]},
                              24: {'x': [0, 0], 'y': [0, 0], 'z': [0, 0]},
                              25: {'x': [0, 0], 'y': [0, 0], 'z': [0, 0]},
                              0: {'x': [0, 0], 'y': [0, 0], 'z': [0, 0]},
                              1: {'x': [0, 0], 'y': [0, 0], 'z': [0, 0]},
                              2: {'x': [0, 0], 'y': [0, 0], 'z': [0, 0]},
                              3: {'x': [0, 0], 'y': [0, 0], 'z': [0, 0]},
                              4: {'x': [0, 0], 'y': [0, 0], 'z': [0, 0]},
                              5: {'x': [0, 0], 'y': [0, 0], 'z': [0, 0]},
                              6: {'x': [0, 0], 'y': [0, 0], 'z': [0, 0]},
                              }

    def set_basic_info(self, label_list, except_jizhan_list=None):
        """
        设置测距的基本信息。会通过bulk模式发送
        :param label_list:[20,21,22,23,24]
        :param except_jizhan_list: 默认的是6各基站:0 1,2,3,4,5.对应基站：1-2-0,1-2-5.
        :return:
        """
        self.set_cache_data_to_default()

        self.bulk_mode = 1
        # 基站: B H :14379
        # 基本设置
        self.set_buardrate_h()
        self.set_modbus_id_h()
        self.set_device_measure_mode_h()
        self.set_device_mode_h()
        self.set_device_id_h()
        self.set_comm_channel_and_speed_h(2, 2)
        self.set_kalman_h()
        self.set_recv_delay_h()
        self.clear_measure1_reg()

        # 使能基站
        if except_jizhan_list is None:
            except_jizhan_list = []
        except_jizhan_list.extend([i for i in self.anchor_used_dict if not self.anchor_used_dict[i]])
        self.curr_used_anchor = []
        for i in range(7):
            if except_jizhan_list is not None:
                if i in except_jizhan_list:
                    self.set_anchor_enable_h(i, 0)
                    continue
            self.set_anchor_enable_h(i, 1)
            self.curr_used_anchor.append(i)

        self.curr_anchor_stat = {i: {'cnt': 0, 'success': 0} for i in self.curr_used_anchor}
        self.set_label_h(label_list)  # 使用标签
        self.set_label_num_h(len(label_list))  # 标签数量 1

        self.bulk_send()
        self.bulk_mode = 0
        time.sleep(0.5)

    def clear_measure1_reg(self):
        """
        清除寄存器0x2f->0x36 8个寄存器
        :return:
        """
        ret = self.write_modbus_h(0x2f, 8, b'\x00' * 16)

    def get_dist_of_biaoqian_once(self):
        """
            获取某个标签的距离:
            测量3次，取平均值
        """
        # logger.debug('get_dist_of_biaoqian_once: start')
        self.start_measure_h(1)
        time.sleep(1)
        ret = self.read_modbus_h(0x30, 7)

        dist_b = [self.EMPTY_DIST_VAL for i in range(8)]
        if 'data' in ret:
            dist_b[0] = (ret['data'][0] * 256 + ret['data'][1]) / 100.0
            dist_b[1] = (ret['data'][2] * 256 + ret['data'][3]) / 100.0
            dist_b[2] = (ret['data'][4] * 256 + ret['data'][5]) / 100.0
            dist_b[3] = (ret['data'][6] * 256 + ret['data'][7]) / 100.0
            dist_b[4] = (ret['data'][8] * 256 + ret['data'][9]) / 100.0
            dist_b[5] = (ret['data'][10] * 256 + ret['data'][11]) / 100.0
            dist_b[6] = (ret['data'][12] * 256 + ret['data'][13]) / 100.0

        self.stop_measure_h()
        # time.sleep(0.5)
        print('标签到各基站距离: %s', dist_b)
        return 0, 0, dist_b

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

        # for i in dist_list:
        #     logger.debug('i %s', i)
        # logger.debug('d_dict %s', d_dict)
        return d_dict

    def get_pos_of_biaoqian_once(self, loop_mean_cnt=20):
        """
        获取标签距离，默认平均20次
        """
        dist_all = []
        dist_list = []

        for i in range(loop_mean_cnt):
            x, y, dist_b = self.get_dist_of_biaoqian_once()
            dist_list.append(dist_b)
            # print(str(i)+'-次数---------: ', dist_b)
        # 求多次测距平均值
        d_dict = self.convert_mean(dist_list)
        # print('平均值: ', d_dict)
        return 0, 0, d_dict

    def if_biaoqian_exist(self, client_id, loop_max=5):
        client_no = client_id_get_no(client_id)
        self.set_basic_info([client_no], [1, 2, 3, 4, 5, 6])
        for i in range(loop_max):
            x, y, dist = self.get_pos_of_biaoqian_once(1)
            for d in dist:
                if d != 0 and d != 0.0:
                    return True
            # if dist[0] != 0 and dist[0] != 0.0:
            #     return True

        return False
