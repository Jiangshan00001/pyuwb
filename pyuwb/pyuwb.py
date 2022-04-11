import copy
import time
import math
#from numpy import short
from .my_short import my_short as short
from .anchor_locate_algorithm1 import AnchorLocateAlgorithm1
from .tag_locate_algorithm1 import TagLocateAlgorithm1
from .uwb_modbus import UwbModbus,ANCHORZ_NO
from .modbus_pkt import split_packet

from .client_id_utils import client_id_get_no, client_id_get_type, pack_client_id, client_id_remove_group, DEVICE_TYPE_TAG, DEVICE_TYPE_ANCHOR, DEVICE_TYPE_ANCHORZ
from .dist_list_dict_convert import dist_list2dict

from .mylog import logging

logger = logging.getLogger(__name__)


def get_cali_param_all():
    return {
        '1-0': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '1-1': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '1-2': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '1-3': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '1-4': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '1-5': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '0-1': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '0-2': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '0-3': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '0-4': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '0-5': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '0-6': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '0-20': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
        '0-21': {'0': 1.0, '1': 1.0, '2': 1.0, '3': 1.0, '4': 1.0, '5': 1.0, },
    }


class uwb_zrzn(UwbModbus):

    def __init__(self):
        super(uwb_zrzn, self).__init__()

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


    def set_pos_callback(self, callback_func):
        """
        set the callback function when dist and pos is successfully measured
        :param callback_func: def function_to_call(tag_id:int, dist:dict, pos:dict) pos:{x:1,y:2,z:3}
        :return:
        """
        self.pos_callback = callback_func

    # 检测周围所有设备
    def detect_device(self, tag_no_list=None, anchor_no_list=None):
        """
        tag_no_list: 用户认为存在的标签号 [1,2,3,11]
        anchor_no_list： 用户认为存在的基站 [0,1,2]
        """
        not_exist_anchor_no_list = []  # 不存在的基站
        for i in range(7):
            if i not in anchor_no_list:
                not_exist_anchor_no_list.append(i)
        # 标签测距
        self.set_to_start(tag_no_list, 1, 6, not_exist_anchor_no_list)
        self.locate_loop(tag_no_list, 1, 5)
        self.stop_measure_h()
        # 处理标签距离信息，获取在线设备
        tag_dict = {}
        for i in self.tag_list:
            logger.info('标签测距值(主基站、0,1,2,3...)： %s %s', i, self.tag_list[i]['dist'])
            tag_dict[i] = self.tag_list[i]['dist']
        ret = self._get_device_exist_using_dist(tag_dict)
        # 设置在线设备
        tag_no_list = ret['exist_tag']
        anchor_no_list = ret['exist_anchor']
        self.set_device(tag_no_list, anchor_no_list)
        return tag_no_list, anchor_no_list


    def _get_device_exist_using_dist(self, tag_dict):
        """
        分析哪些设备在线
        :param tag_dict: {20: [1,1,2,3,-1,-1,-1,-1],    -----------1-1-0、1-2-0、1-2-1...
                          21: [1,1,2,3,-1,-1,-1,-1],
                          22: [-1,-1,-1,-1,-1,-1,-1,-1]}
        :return: {'exist_anchor': [0, 1, 2, 3], 'exist_tag': [20, 21]}
        """
        ret = {'exist_anchor': [], 'exist_tag': [], 'is_exist_main_anchor': 1}  # is_exist_main_anchor主基站是否存在：1在
        for i in tag_dict:
            for index, val in enumerate(tag_dict[i]):
                if val != -1:
                    ret['exist_tag'].append(i)
                    if index==0:
                        #主基站不写入，因为必须存在，而不进行定位
                        continue
                    ret['exist_anchor'].append(index)

        ret['exist_tag'] = list(set(ret['exist_tag']))
        ret['exist_anchor'] = list(set(ret['exist_anchor']))
        logger.info('存在设备：%s', ret)
        return ret

    def detect_device_slow(self, tag_no_list=None, anchor_no_list=None):
        """
        detect if device exist
        如果是空列表，则基站会检测：0,1,2,3,4,5,6,7存在不存在，标签会检测：1-10存在不存在
        :param tag_no_list: tag_no will be detected. will detect 1-10 tag is exist or not if None or empty.  如果是空标签会检测：1-10号标签是否存在
        :param anchor_no_list: anchor_no will be detected. will detect 0-7 anchor is exist or not if None or empty. 如果为空，则会检测0-7号基站是否存在
        :return:exist tag_no_list, exist anchor_no_list
        """
        if tag_no_list is None or tag_no_list == []:
            tag_no_list = [i + 1 for i in range(10)]
        if anchor_no_list is None or anchor_no_list == []:
            anchor_no_list = [i for i in range(8)]

        tag_client_list = [pack_client_id(self.group_id, DEVICE_TYPE_TAG, i) for i in tag_no_list]
        anchor_client_list = [pack_client_id(self.group_id, DEVICE_TYPE_ANCHOR, i) for i in anchor_no_list]

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
            if self.is_anchor_exist_h(client_id, loop_max):
                pass
            else:
                print('基站' + client_id + '测试通讯失败.去除此设备')
                anchor_client_list.remove(client_id)

        time.sleep(1)
        self.if_tag_exist_h('1-3-1')
        time.sleep(1)

        for i in tag_client_list.copy():
            client_id = i
            if self.is_demo_mode:
                loop_max = 1
            else:
                loop_max = 5
            if self.if_tag_exist_h(client_id, loop_max):
                pass
            else:
                print('标签' + client_id + '测试通讯失败.去除此设备')
                tag_client_list.remove(client_id)

        tag_no_list = [client_id_get_no(i) for i in tag_client_list]
        anchor_no_list = [client_id_get_no(i) for i in anchor_client_list]
        self.set_device(tag_no_list, anchor_no_list)
        return tag_no_list, anchor_no_list

    # 显示当前所有设备及相关测距信息
    def device_pos_list(self):
        """
        get all device current pos
        :return:[{'client_id':'1-2-3', pos:{x:,y:,z:}},...]
        """
        # print('所有使用的设备信息：', self.all_device_list)
        ret = []
        for i in self.all_device_list:
            d = {}
            d['client_id'] = i['client_id']
            d['pos'] = i['pos']
            ret.append(d)
        return ret

    def tag_no_list(self):
        """
        get current tag no list
        :return:[1,2,3,...]
        """
        used_tag_no_list = []
        for i in self.all_device_list:
            tag_type = client_id_get_type(i['client_id'])
            tag_no = client_id_get_no(i['client_id'])
            if tag_type == DEVICE_TYPE_TAG:
                used_tag_no_list.append(tag_no)
        return used_tag_no_list

    def anchor_no_list(self):
        """
        get current anchor no list
        :return: [0,1,2,3,...]
        """
        used_anchor_no_list = []
        for i in self.all_device_list:
            tag_type = client_id_get_type(i['client_id'])
            tag_no = client_id_get_no(i['client_id'])
            if tag_type == DEVICE_TYPE_ANCHOR:
                used_anchor_no_list.append(tag_no)
        return used_anchor_no_list

    def set_device(self, tag_no_list, anchor_no_list):
        """
        set device to use.
        this function will auto called when  you call detect_device.
        如果不需要检测设备，直接指定设备列表也可以 (tag_no_list：标签列表，anchor_no_list：次基站列表，using_master：是否使用主基站测距【1代表使用，0代表不使用】)
        暂不支持通过master进行定位
        :param tag_no_list: tag no in the system. eg:[1,2,3,...]
        :param anchor_no_list: anchor no in the system eg: [0,1,2,3]
        :return:None
        """
        self.all_device_list = []
        for i in tag_no_list:
            tag_client_id = pack_client_id(self.group_id, DEVICE_TYPE_TAG, i)
            self.all_device_list.append({'client_id': tag_client_id, 'dist': [], 'pos': []})
        for i in anchor_no_list:
            anchor_client_id = pack_client_id(self.group_id, DEVICE_TYPE_ANCHOR, i)
            self.all_device_list.append({'client_id': anchor_client_id, 'dist': [], 'pos': []})

        self.all_device_dict = {i['client_id']: i for i in self.all_device_list}

        # 使能设备
        for i in self.anchor_used_dict.copy():
            if i not in anchor_no_list:
                self.anchor_used_dict[i] = 0
            else:
                self.anchor_used_dict[i] = 1
        logger.info('当前启动的基站列表: %s', self.anchor_used_dict)

        return None

    def locate_anchor(self, height_list=(0.5, 1.1, 0.5, 1.1), direction_point=('N', 'S', 'E'), measure_ready_cnt=40):
        """
        对基站坐标进行定位：
        1 测距：各基站到其他基站的距离：
        2 计算位置：根据距离和高度参数，以及顺序位置，建立坐标系
        :param height_list:高度列表，需要和设备数一致
        :param measure_ready_cnt:测距次数，多次测量取均值，用于提高测距精度，进而提高定位精度
        :return:
        """
        # 定位次基站
        anchor_list, tag_info = self._get_anchor_and_tag_info()

        # 次基站之间测距
        anchor_list = self._measure_all_anchor_dist(anchor_list, measure_ready_cnt)
        print('基站之间测距：', anchor_list)
        for i in range(len(anchor_list)):
            if i < len(direction_point):
                anchor_list[i]['direction_point'] = direction_point[i]
            else:
                anchor_list[i]['direction_point'] = None
            if i < len(height_list):
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

    # 定位一次 标签
    def start_locate_once(self):
        anchor_client_list, tag_client_list = self._get_anchor_and_tag_info()
        # 标签与次基站之间的距离
        self._measure_all_tag_dist(tag_client_list)

        #FIXME: remove anchorz. as it do not for locating

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

    def measure_distance(self, client_id1, client_id2, ready_cnt=30):
        """
        测量获取距离
        :param client_id1:
        :param client_id2:
        :param ready_cnt: 测距次数。默认测量10次取均值返回
        :return: 两个设备间的距离，单位m
        """
        if client_id_get_type(client_id2) == DEVICE_TYPE_ANCHORZ:
            #swap
            client_id1, client_id2 = client_id2, client_id1
        if (client_id_get_type(client_id1) == DEVICE_TYPE_TAG) and (client_id_get_type(client_id2) == DEVICE_TYPE_TAG):
            #两个都是标签，没法测距，返回错误
            return -1

        if client_id_get_type(client_id1) == DEVICE_TYPE_TAG:
            #swap
            client_id1, client_id2=client_id2, client_id1


        if client_id_get_type(client_id2) == DEVICE_TYPE_ANCHOR:
            # 两个次基站 测距
            anchor_dict=[{'client_id': client_id2, 'dist': {}}]
            if client_id_get_type(client_id1) != DEVICE_TYPE_ANCHORZ:
                anchor_dict.append({'client_id': client_id1, 'dist': {}})
            self._measure_all_anchor_dist(anchor_dict, ready_cnt)
            for i in self.all_device_list:
                if i['client_id'] == client_id2:
                    return i['dist_list'][client_id_get_no(client_id2)]
                elif i['client_id'] == client_id2:
                    return i['dist_list'][client_id_get_no(client_id1)]
        elif client_id_get_type(client_id2) == DEVICE_TYPE_TAG:
            tag_client_id = client_id2
            anchor_client_id = client_id1
            # 标签和基站之间测距
            dist = self._measure_all_tag_dist(tag_client_list=[{'client_id': tag_client_id, 'dist': {}}],
                                              anchor_client_list=[{'client_id': anchor_client_id, 'dist': {}}],ready_cnt=ready_cnt)
            return dist[0][anchor_client_id]

        logging.error('unknown device type: %s %s', client_id1, client_id2)
        return -1




        # 测 次基站和次基站之间的距离 或 次基站和标签之间的距离 或主基站和标签之间的距离，主基站和次基站之间的距离
        # 不能测量：标签和标签之间的距离



        if client_id_get_type(client_id1) == DEVICE_TYPE_TAG or client_id_get_type(client_id2) == DEVICE_TYPE_TAG:
            # 存在 标签
            if client_id_get_type(client_id1) == DEVICE_TYPE_TAG:
                tag_client_id = client_id1
                anchor_client_id = client_id2
            else:
                tag_client_id = client_id2
                anchor_client_id = client_id2

            # 标签和基站之间测距
            dist = self._measure_all_tag_dist(tag_client_list=[{'client_id': tag_client_id, 'dist': {}}],
                                              anchor_client_list=[{'client_id': anchor_client_id, 'dist': {}}])
            return dist[0][anchor_client_id]
            # for i in self.all_device_list:
            #    if i['client_id'] == tag_client_id:
            #        return i['dist'][client_id_get_no(anchor_client_id)]
        else:
            # 两个次基站 测距
            self._measure_all_anchor_dist([{'client_id': client_id1, 'dist': {}}, {'client_id': client_id2, 'dist': {}}])
            for i in self.all_device_list:
                if i['client_id'] == client_id1:
                    return i['dist_list'][client_id_get_no(client_id2)]
                elif i['client_id'] == client_id2:
                    return i['dist_list'][client_id_get_no(client_id1)]

        print('打印get_distance=================', self.all_device_list)

    def _get_anchor_and_tag_info(self):
        """

        :return: [{client_id:, pos:{x:,y:,z:}}], [{client_id:, pos:{x:,y:,z:}}]
        """
        # 从内存self.all_device_list中获取 基站 和 标签信息
        tag_client_list = []
        anchor_client_list = []
        for i in self.all_device_list:
            if client_id_get_type(i['client_id']) == DEVICE_TYPE_ANCHOR:
                anchor_client_list.append(i)
            elif client_id_get_type(i['client_id']) == DEVICE_TYPE_TAG:
                tag_client_list.append(i)
        return anchor_client_list, tag_client_list

    def _measure_all_anchor_dist(self, anchor_client_list, measure_ready_cnt=40):
        """
        基站的测距：
        :param anchor_client_list: [ {client_id:'1-2-3', }]
        :return:
        """
        all_anchor_client_id_list = [i['client_id'] for i in anchor_client_list]
        ret = []
        for i in all_anchor_client_id_list:
            reti = {'client_id': i}
            if client_id_get_no(i)==0:
                # 0 anchor could not change to tag and measure
                continue
            reti['dist'] = self._measure_one_anchor_dist(i, measure_ready_cnt, False)
            ret.append(reti)
        print("基站自动测距结束")
        return ret

    def set_to_start(self, tag_no_list=None, ready_cnt=30, start_cmd=6,except_anchor_list=None):

        if tag_no_list is None:
            tag_no_list = self.tag_no_list()
        self.set_basic_info_h(tag_no_list,except_anchor_list)  # self.uwb.set_cache_data_to_default()内部会调用此函数


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

        # FIXME: 此处需要次基站和主基站 两种基站的个数
        if  0 not in cijizhan_no_list:
            cijizhan_no_list.append(0)

        self._measure_read()
        if not wait_for_finish:
            return

        time_start = time.time()
        unfinished_tag = copy.deepcopy(tag_no_list)

        while time.time() - time_start < timeout:
            self._measure_read()
            if wait_for_finish:
                ready_tag = []
                if len(unfinished_tag) == 0:
                    break
                for i in unfinished_tag:
                    nz_cnt = 0
                    for j in self.tag_list[i]['dist']:
                        if j != self.EMPTY_DIST_VAL:
                            nz_cnt += 1
                    if nz_cnt >= len(cijizhan_no_list):# 因为主基站也会测距，所以此处+1 TODO: 还要其他函数需要修改通样的？
                        ready_tag.append(i)
                    else:
                        logger.debug("nz_cnt:%d < %d",nz_cnt,len(cijizhan_no_list))

                for i in ready_tag:
                    unfinished_tag.remove(i)
                ready_tag.clear()

        if wait_for_finish:
            if len(unfinished_tag) > 0:
                logger.debug('测量标签位置失败:%s', unfinished_tag)
            else:
                logger.debug('测量标签位置完成:%s', tag_no_list)

    def _measure_all_tag_dist(self, tag_client_list, anchor_client_list=None, ready_cnt=30):
        """

        :param tag_client_list:[{client_id:,}, ...]
        :param anchor_client_list:[{client_id:,}, ...]
        :return:[{'1-1-0:'1.1, '1-1-1':3.4},...] every item is a dict for every tag dist with all anchors.
        """
        tag_client_id_list = [i['client_id'] for i in tag_client_list]
        tag_no_list = [client_id_get_no(i) for i in tag_client_id_list]

        if anchor_client_list is None:
            anchor_client_list, tinfo = self._get_anchor_and_tag_info()

        self.set_to_start(tag_no_list,ready_cnt)
        self.locate_loop(tag_no_list, 1, ready_cnt*(len(tag_client_list)+1)/10.0)

        self.stop_measure_h()
        self.tag_list_cache_ready_cnt = 10

        for tt in self.all_device_list:
            tag_no = client_id_get_no(tt['client_id'])
            if tag_no in tag_no_list:
                tt['dist'] = dist_list2dict(self.tag_list[tag_no]['dist'])

        dist_all = []
        for i in tag_client_list:
            dist_all.append(dist_list2dict(self.tag_list[client_id_get_no(i['client_id'])]['dist'], self.group_id))

        return dist_all

    def _start_anchor_dist_measure(self, client_id, ready_cnt=40):
        self.curr_anchor_to_measure = client_id  # FIXME: client_id[2:]
        self.bulk_mode = 0
        logger.info("基站自动定位测距：%s", client_id)

        self.bulk_mode = 0
        # 基站转标签
        is_ok, ret = self.convert_anchor_to_tag_h(client_id)
        if not is_ok:
            return is_ok
        time.sleep(0.25)

        # 设置基站和标签参数
        except_list = [client_id_get_no(client_id)]
        except_list = list(set(except_list))
        self.set_basic_info_h([0], except_list)

        # 启动测量
        self.tag_list_cache_ready_cnt = ready_cnt
        self.start_measure_h(6)
        return True

    def _tag_a_process(self, tag_id, acce_x, acce_y, acce_z):
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

    def _decode_measure_payload(self, payload63: bytes, pkt_has_height=1):
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

        self._tag_a_process(tag_id, acce_x, acce_y, acce_z)
        self._tag_dist_process(tag_id, dista, status)
        self._count_for_payload_func(tag_id, dista, status, acce_x, acce_y, acce_z)
        return

    def _count_for_payload_func(self, tag_id, dista, status, acce_x, acce_y, acce_z):
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
            logger.debug('count_for_payload: %s', self.count_for_payload_pps)
            logger.debug('error_status: %s', self.biaoqian_jizhan_error)
            self.count_for_payload = 0
            self.count_for_payload_timer = ctime

    def _avg_dist_data(self, data_list, last_data):
        """
            距离数据的平均滤波。避免跳动太大
        :param data_list:
        :param last_data:
        :return:
        """
        logger.debug('avg_dist_data 输入 %s %s', data_list, last_data)
        if len(data_list) == 0:
            logger.debug('avg_dist_data result:', last_data)
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
        logger.debug('avg_dist_data result: %s', dist_avg)
        if (math.fabs(dist_avg - last_data) > 1) and (last_data != self.EMPTY_DIST_VAL):
            logger.debug('距离跳跃太大：%s %s %s', data_list, dist_avg, last_data)
        return dist_avg, 1

    def _tag_dist_cache_to_one(self, tag_id):
        """
        标签的距离，采用多次测量取平均值的方式
        :return:
        """
        currdist_list = self.tag_list_cache[tag_id]['dist']
        logger.debug('tag_id= %s 距离测距次数:%s', tag_id, self.dist_decode_cnt[tag_id])
        logger.debug('距离测距数值:%s', currdist_list)

        for i in range(len(currdist_list)):
            anchor_index = i
            anchor_dist = currdist_list[i]

            ###统计基站测距次数和成功次数

            ###

            if len(anchor_dist) > 0:
                curr_val, curr_val_en = self._avg_dist_data(anchor_dist, self.tag_list[tag_id]['dist'][i])
                if tag_id == 0:
                    # 某一个次基站（0标签）正在测距
                    tag_id_c = self.curr_anchor_to_measure  # 1-2-0
                else:
                    # 某一个标签正在测距 20、21、1、2、3、4
                    tag_id_c = pack_client_id(self.group_id, DEVICE_TYPE_TAG, tag_id)
                #  tag_id：2-4或3-20，anchor_id：0-5之间的一个数字，curr_val：距离，cali_param：计算参数
                curr_val = self._data_cali_v2(client_id=tag_id_c, anchor_id_n=i, curr_val=curr_val,
                                              cali_param=self.cali_param)
                if i > 5:
                    break

                self.tag_list[tag_id]['dist'][i] = curr_val
                self.tag_list[tag_id]['dist_en'][i] = curr_val_en
                self.tag_list[tag_id]['dist_cache'][i] = currdist_list[i]

            self.tag_list_cache[tag_id]['dist'][i] = []

        self._one_tag_dist_got(tag_id)

    def _one_tag_dist_got(self, tag_id):
        """
        每次接收到1次设备发来的标签距离信息，则会调用此函数
        :param tag_id:
        :return:
        """

        ainfo, tinfo = self._get_anchor_and_tag_info()
        for index, i in enumerate(ainfo.copy()):
            if client_id_get_no(i['client_id'])==ANCHORZ_NO:
                #主基站
                del ainfo[index]
                break

        dist = dist_list2dict(self.tag_list[tag_id]['dist'], self.group_id)
        if tag_id != 0:
            pos = self.tag_locate_algorithm.calc(dist, pack_client_id(self.group_id, DEVICE_TYPE_TAG, tag_id), ainfo)
        else:
            pos = {'x': 0, 'y': 0, 'z': 0}
        if self.pos_callback is not None:
            self.pos_callback(tag_id, dist, pos)

    def _tag_dist_process(self, tag_id, dista, status):
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
            self._tag_dist_cache_to_one(tag_id)
            self.dist_decode_cnt[tag_id] = 0

    def _data_cali_v2(self, client_id, anchor_id_n, curr_val, cali_param):
        """

        """
        client_id2 = client_id_remove_group(client_id)
        anchor_id = str(anchor_id_n)
        if (client_id2 in cali_param) and (anchor_id in cali_param[client_id2]):
            curr_val *= cali_param[client_id2][anchor_id]
        logger.debug('data_cali: %s %s %s', client_id2, anchor_id_n, curr_val)
        logger.debug('输出: %s ', curr_val)
        return curr_val

    def _measure_read(self, pkt_has_height=1):
        """
        读取串口数据并解码，用于主基站主动发数据的模式
        :param pkt_has_height:
        :return: 此次处理的报文数，此次处理的字节数
        """
        if self.measure_mode != 3 and self.measure_mode != 4 and self.measure_mode != 6:
            return 0, 0
        # 只有3，4模式是主动发送，需要处理报文
        self.read_buf += self._read_data(0.1)
        #print('measure_read: ', len(self.read_buf), self.read_error_cnt, self.read_ok_cnt)
        #print('measure_read: ', self.read_error_stat)

        pkt_length = 63
        if pkt_has_height == 0:
            pkt_length = 63 - 16

        pkt_list, self.read_buf, read_error_cnt, ret_pkt_process, ret_byte_process = split_packet(self.read_buf,
                                                                                                  pkt_length,
                                                                                                  self.read_error_stat)
        for i in pkt_list:
            self._decode_measure_payload(i, pkt_has_height)

        return ret_pkt_process, ret_byte_process

    def _check_anchor_dist_measure_finish(self):
        """
        读取串口测距报文，处理后，查看哪些测距已经完成
        :return:is_finish, 100
        """
        self._measure_read()

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

    def _stop_anchor_dist_measure(self, client_id):

        self.stop_measure_h()
        # 转换标签到基站
        ret = self.convert_tag_to_anchor_h(client_id)
        self.tag_list_cache_ready_cnt = 10
        dist_ret = copy.deepcopy(self.tag_list[0]['dist'])
        print('stop_jizhan_dist_measure: ', dist_ret)
        return dist_ret

    def _measure_one_anchor_dist(self, client_id, measure_ready_cnt=40, remove_error_device=True):
        """
        测量某个基站到其他基站的距离
        :param client_id:  当前要测量的次基站client_id       次基站的id：eg: 1-2-1
        :param measure_ready_cnt: 测量次数
        :param remove_error_device: False/True 如果测距失败，则从可用列表中移除此设备
        :return:
        """

        # 每个次基站，进行测距

        print('次基站' + client_id + '正在测距中')

        start_ok = self._start_anchor_dist_measure(client_id, measure_ready_cnt)
        if (not start_ok) and remove_error_device:
            print("次基站连接失败 ： 改为不启用，即删除该基站信息", client_id)
            for i in self.all_device_list.copy():
                if i['client_id'] == client_id:
                    self.all_device_list.remove(i)
                    break

        cnt = 0
        while start_ok:
            cnt += 1
            is_finish, percent = self._check_anchor_dist_measure_finish()
            if is_finish:
                break

            print("次基站测距中 client_id： percent----", client_id, percent)

            time.sleep(0.1)
            if cnt > 100:  # 10秒种
                print("基站测距超时失败 ", client_id)
                time.sleep(0.1)
                break

        dist = self._stop_anchor_dist_measure(client_id)

        # dist的list->dict
        # 基站：client_id 到其它基站的距离在dist中，需要写入self.all_device_list
        for i in self.all_device_list:
            if i['client_id'] == client_id:
                i['dist'] = dist_list2dict(dist, self.group_id)
                break
        print('次基站' + client_id + '测距成功, dist:', dist)
        return dist_list2dict(dist, self.group_id)
