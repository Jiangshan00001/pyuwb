import copy
import math
from .KalmanFilter import KalmanFilter, KalmanFilterXYZ

class Dingwei():
    # 根据距离求坐标位置

    def __init__(self):
        super().__init__()
        self.using_kalman = 1
        self.kalman = {
            '1-3-20': KalmanFilterXYZ(),
            '1-3-21': KalmanFilterXYZ(),
            '1-3-22': KalmanFilterXYZ(),
            '1-3-23': KalmanFilterXYZ(),
            '1-3-24': KalmanFilterXYZ(),
            '1-3-25': KalmanFilterXYZ(),
            '1-3-1': KalmanFilterXYZ(),
            '1-3-2': KalmanFilterXYZ(),
            '1-3-3': KalmanFilterXYZ(),
            '1-3-4': KalmanFilterXYZ(),
            '1-3-5': KalmanFilterXYZ(),
            '1-3-6': KalmanFilterXYZ(),
        }

    def triangle_pos_xy(self, point_list, has_height_diff=1):
        """
        传入3个点，已知2个点的坐标，和三个点之间的距离，计算第三个点的坐标
        两点坐标为：（x1，y1），（x2，y2），距离为r1，r2
        is_accuracy 代表对应距离（r1，r2）是否是用户输入的

        :param point_list:[
        {
            "client_id":"1-2-1",
            "dist":{"1-2-2":4.00, "1-2-3":3.00 },
            "pos":{"x":0, "y":0},
        },
        {
            "client_id":"1-2-2",
            "dist":{"1-2-1":4.00, "1-2-3":5.00 },
            "pos":{"x":0.00, "y":4.00}
        },
        {
            client_id:"1-2-3",
            "is_accuracy":{"1-2-2":1, "1-2-1":0 }  # 新增数据 ---  1-说明是用户输入的距离，比较准确， 0-自测距离
            "dist":{"1-2-2":5.00, "1-2-1":3.00 }
        }
        ]
        :return:[{"x": x31, "y": y31, 'z': z}, {"x": x32, "y": y32, 'z': z}, ]
        """

        x1 = point_list[0]['pos']['x']
        y1 = point_list[0]['pos']['y']
        if has_height_diff == 1:
            z = point_list[2]['height']
            z1 = point_list[0]['pos']['z']
            z2 = point_list[1]['pos']['z']
        else:
            z = 0
            z1 = 0
            z2 = 0
        x2 = point_list[1]['pos']['x']
        y2 = point_list[1]['pos']['y']
        client_id1 = point_list[0]['client_id']
        client_id2 = point_list[1]['client_id']
        r1 = point_list[2]['dist'][client_id1]
        # r1_is_accuracy = point_list[2]['is_accuracy'][client_id1]  # r1 是否是用户输入的
        r2 = point_list[2]['dist'][client_id2]
        # r2_is_accuracy = point_list[2]['is_accuracy'][client_id2]  # r2 是否是用户输入的
        # TypeError: can't convert complex to float
        try:
            r3 = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
        except Exception as e:
            print('距离转位置失败: %s %s %s %s', point_list, z, z1, z2)
            point_list[2]['pos'] = [{"x": 0.1, "y": 0.1, "z": z}]
            return point_list

        if ((z - z1) * (z - z1) >= r1 * r1) or ((r2 * r2 <= (z - z2) * (z - z2))):
            point_list[2]['pos'] = [{"x": 0.1, "y": 0.1, "z": z}]
            return point_list

        r1 = math.sqrt(r1 * r1 - (z - z1) * (z - z1))
        r2 = math.sqrt(r2 * r2 - (z - z2) * (z - z2))

        if (r3 > r1 + r2) or (r2 > r3 + r1) or (r1 > r2 + r3):  # 组成不了三角形
            # ZeroDivisionError: float division by zero
            point_list[2]['pos'] = [
                {"x": x1 + (x2 - x1) * (r1 / (r1 + r2)), "y": y1 + (y2 - y1) * (r1 / (r1 + r2)), "z": z}]
            return point_list

        t = (r2 * r2 - r1 * r1 + x1 * x1 + y1 * y1 - x2 * x2 - y2 * y2)
        a = (2 * x1 - 2 * x2)
        b = (2 * y1 - 2 * y2)

        y31 = 0
        y32 = 0
        x31 = 0
        x32 = 0
        if b != 0:
            c = ((t - b * y1) / b)
            a1 = ((a * a + b * b) / b / b)
            b1 = (-(2 * x1 + 2 * a * c / b))
            c1 = x1 * x1 - r1 * r1 + c * c
            b2_4ac = ((b1 * b1 - 4 * a1 * c1))
            if b2_4ac >= 0:

                x31 = (-b1 + b2_4ac ** 0.5) / 2 / a1
                y31 = (t - a * x31) / b
                x32 = (-b1 - b2_4ac ** 0.5) / 2 / a1
                y32 = (t - a * x32) / b
            elif b2_4ac < 0:
                print('triangle_pos_xy位置计算失败: %s %s %s', r1, r2, point_list[0]['dist'][client_id2])
                x31 = 0
                y31 = 0
                x32 = 0
                y32 = 0

            # print(t, a, b, c, a1, b1, c1)
            # print("one:", x31, y31)
            # print("two:", x32, y32)
        elif a != 0:
            c = (t - a * x1) / a
            a1 = (a * a + b * b) / a / a
            b1 = -(2 * y1 + 2 * b * c / a)
            c1 = y1 * y1 - r1 * r1 + c * c
            b2_4ac = ((b1 * b1 - 4 * a1 * c1))
            if b2_4ac < 0:
                print('triangle_pos_xy位置计算失败2: %s %s %s', r1, r2, point_list[0]['dist'][client_id2])

                y31 = 0
                y32 = 0
                x31 = 0
                x32 = 0
            else:
                y31 = (-b1 + (b1 * b1 - 4 * a1 * c1) ** 0.5) / 2 / a1
                x31 = (t - b * y31) / a
                y32 = (-b1 - (b1 * b1 - 4 * a1 * c1) ** 0.5) / 2 / a1
                x32 = (t - b * y32) / a
            # print(t, a, b, c, a1, b1, c1)
            # print("one:", x31, y31)
            # print("two:", x32, y32)

        point_list[2]['pos'] = [{"x": x31, "y": y31, 'z': z}, {"x": x32, "y": y32, 'z': z}, ]
        # print('打印2 ', point_list)
        return point_list

    def calc_NSE_pos(self, jizhan_dist_list):
        N = None
        S = None
        E = None
        for i in jizhan_dist_list:
            if i['direction_point'] == 'N':
                N = i
            elif i['direction_point'] == 'S':
                S = i
            elif i['direction_point'] == 'E':
                E = i
        if (N is None) or (E is None) or (S is None):
            print('NES could not found: %s %s %s', N, E, S)
            return None, None
        N_client_id = N['client_id']
        S_client_id = S['client_id']
        # N S 先确定位置:S定位xy平面的原点
        N_y = N['dist'][S_client_id]
        # S点在原点
        # N点坐标：如果NS高度相同，则N点坐标为NS的距离
        #         如果NS高度不同，则N点坐标为NS的距离- 相应的高度差
        if (N_y * N_y - (N['height'] - S['height']) ** 2) < 0:
            print('NS之间距离太小，小于高度差，定位失败：%s %s %s %s', N_y, N['height'], S['height'], jizhan_dist_list)
            N['pos'] = {'x': 0, 'y': 0.1, 'z': N['height']}
        else:
            N['pos'] = {'x': 0, 'y': (N_y * N_y - (N['height'] - S['height']) ** 2) ** 0.5, 'z': N['height']}
        S['pos'] = {'x': 0, 'y': 0, 'z': S['height']}

        # client_110 = {
        #     'client_id': '1-1-0',
        #     'pos': {'x': - N_y / 5, 'y': 0, 'z': N['height']}
        # }

        # 确定E的位置
        point_list = [N, S, E]
        point_list = self.triangle_pos_xy(point_list)  #

        # 坐标轴 y:S->N x: S->E
        # 所以，E点x坐标应该>0.此处求出2个点，1个x<0, 1个x>0 取x>的一个
        xyz_2 = point_list[2]['pos']
        if len(xyz_2) > 1:
            if xyz_2[0]['x'] > xyz_2[1]['x']:
                point_list[2]['pos'] = xyz_2[0]
            else:
                point_list[2]['pos'] = xyz_2[1]
        elif len(xyz_2) == 1:
            point_list[2]['pos'] = xyz_2[0]
        else:
            print('E pos could not found')
        return jizhan_dist_list

    def Rtls_Cal_Pos2D(self, x1, y1, r1, x2, y2, r2, x3, y3, r3):
        A = [[0, 0], [0, 0]]
        B = [[0, 0], [0, 0]]
        C = [0, 0]
        result = [0, 0]
        A[0][0] = 2.0 * (x1 - x2)
        A[0][1] = 2.0 * (y1 - y2)
        A[1][0] = 2.0 * (x1 - x3)
        A[1][1] = 2.0 * (y1 - y3)

        det = 0
        det = A[0][0] * A[1][1] - A[1][0] * A[0][1]

        if det != 0:

            B[0][0] = A[1][1] / det
            B[0][1] = -A[0][1] / det

            B[1][0] = -A[1][0] / det
            B[1][1] = A[0][0] / det

            C[0] = r2 * r2 - r1 * r1 - x2 * x2 + x1 * x1 - y2 * y2 + y1 * y1
            C[1] = r3 * r3 - r1 * r1 - x3 * x3 + x1 * x1 - y3 * y3 + y1 * y1

            result[0] = B[0][0] * C[0] + B[0][1] * C[1]  # x的值
            result[1] = B[1][0] * C[0] + B[1][1] * C[1]  # y的值
        else:
            print('no pos found error!')
            result[0] = 0
            result[1] = 0

        return result

    def triangle_pos_xy_three_get_one(self, point_list, has_height_diff=1):
        x1 = point_list[0]['pos']['x']
        y1 = point_list[0]['pos']['y']

        x2 = point_list[1]['pos']['x']
        y2 = point_list[1]['pos']['y']

        x3 = point_list[2]['pos']['x']
        y3 = point_list[2]['pos']['y']

        h1 = point_list[0]['pos']['z']
        h2 = point_list[1]['pos']['z']
        h3 = point_list[2]['pos']['z']
        h = point_list[3]['height']

        r1_n = point_list[3]['dist'][point_list[0]['client_id']]
        r2_n = point_list[3]['dist'][point_list[1]['client_id']]
        r3_n = point_list[3]['dist'][point_list[2]['client_id']]

        r1 = (r1_n * r1_n - has_height_diff * (h - h1) * (h - h1)) ** 0.5
        r2 = (r2_n * r2_n - has_height_diff * (h - h2) * (h - h2)) ** 0.5
        r3 = (r3_n * r3_n - has_height_diff * (h - h3) * (h - h3)) ** 0.5

        xy = self.Rtls_Cal_Pos2D(x1, y1, r1, x2, y2, r2, x3, y3, r3)
        return {'x': xy[0], 'y': xy[1], 'z': h}

    def calc_anchor_pos(self, anchor_list):
        """

        :param anchor_list:
        :return:
        """
        # 次基站定位
        anchor_pos_list = self.calc_NSE_pos(anchor_list)
        print('基站NSE位置:', anchor_pos_list)
        other_jizhan_list = []
        NSE_jizhan_list = []
        for i in anchor_pos_list:
            if i['direction_point'] in ['N', 'S', 'E']:
                NSE_jizhan_list.append(i)
            elif i['direction_point'] == None:
                other_jizhan_list.append(i)
        for b in other_jizhan_list:
            sanwei_xyz_list = copy.deepcopy(NSE_jizhan_list)
            sanwei_xyz_list.append(b)
            print('已知三点坐标，通过映射求第四点坐标xyz： %s', sanwei_xyz_list)
            no_four_pos = self.triangle_pos_xy_three_get_one(sanwei_xyz_list)  # 三维 ， 返回第四个点坐标=========================
            # print('da 基站pos', no_four_pos)
            b['pos'] = no_four_pos
        return anchor_pos_list

    # tag=================
    def get_jizhan_list_to_calc_biaoqian(self, jizhan_info=None):
        """

        :param jizhan_info:[{client_id:1-2-0,},...]
        :return: [ ['1-2-0','1-2-1','1-2-2','1-2-3'],  ['1-2-0','1-2-1','1-2-2','1-2-4'],]


        """
        # jizhan_list 用于四个基站定位一个标签
        curr_jizhan_list = [i['client_id'] for i in jizhan_info]
        curr_jizhan_list.sort()
        if len(curr_jizhan_list) <= 4:
            return [curr_jizhan_list]

        jizhan_list = []
        jizhan_list1 = curr_jizhan_list[:3]
        jizhan_list2 = curr_jizhan_list[3:]
        for i in jizhan_list2:
            jizhan_list.append([*jizhan_list1, i])
        # jizhan_list = [
        #     ['1-2-0', '1-2-1', '1-2-2', '1-2-5'],
        #     ['1-2-0', '1-2-1', '1-2-3', '1-2-5'],
        #     ['1-2-0', '1-2-2', '1-2-3', '1-2-5'],
        #     ['1-2-1', '1-2-2', '1-2-3', '1-2-4'],
        # ]
        # jizhan_list = [
        #     ['1-2-0', '1-2-1', '1-2-2', '1-2-3']
        # ]
        return jizhan_list
    def triangle_pos_xyz(self, point_list):
        """
        point_list:[
        {
            "client_id":"1-2-1",
            "dist":{"1-2-2":3.00, "1-2-3":4.00 },
            "pos":{"x":0.00, "y":0.00, "z":0.00}
        },
        {
            "client_id":"1-2-2",
            "dist":{"1-2-1":3.00, "1-2-3":5.00 },
            "pos":{"x":10.00, "y":10.00, "z":0.00}
        },
        {
            client_id:"1-2-3",
            "dist":{1-2-2:5.00, 1-2-1:4.00 },
            "pos":{"x":0.00, "y":10.00, "z":0.00}
        },
        {
            client_id:"1-2-4",
            "dist":{1-2-2:5.00, 1-2-1:4.00 },
            "pos":{"x":10.00, "y":0.00, "z":10.00}
        },
        {
            client_id:"1-2-5",
            "dist":{1-2-1:10*(3**0.5), 1-2-2:10.00, 1-2-3:10*(2**0.5), 1-2-4:10.00}
        }

        ]

        传入5个点，已知4个点的坐标，和5个点之间的距离，计算第5个点的坐标

        :param point_list:[]
        :return:{x:,y:,z:}
        """
        # print(point_list)
        if len(point_list) < 4:
            # logger.error('距离转位置失败 %s', point_list)
            return {'x': 0, 'y': 0, 'z': 0}
        if ('pos' not in point_list[3]) or ('x' not in point_list[3]['pos']):
            # logger.error('距离转位置失败 %s', point_list)
            return {'x': 0, 'y': 0, 'z': 0}

        Point_xyz = [0.0, 0.0, 0.0]
        x1 = point_list[0]['pos']['x']
        y1 = point_list[0]['pos']['y']
        z1 = point_list[0]['pos']['z']
        x2 = point_list[1]['pos']['x']
        y2 = point_list[1]['pos']['y']
        z2 = point_list[1]['pos']['z']
        x3 = point_list[2]['pos']['x']
        y3 = point_list[2]['pos']['y']
        z3 = point_list[2]['pos']['z']
        x4 = point_list[3]['pos']['x']  # x4 = point_list[3]['pos']['x'] KeyError: 'pos'
        y4 = point_list[3]['pos']['y']
        z4 = point_list[3]['pos']['z']
        # print(x1, y1, z1)
        # print(x2, y2, z2)
        # print(x3, y3, z3)
        # print(x4, y4, z4)
        client_id1 = point_list[0]['client_id']
        client_id2 = point_list[1]['client_id']
        client_id3 = point_list[2]['client_id']
        client_id4 = point_list[3]['client_id']
        try:
            r1 = point_list[4]['dist'][client_id1]
            r2 = point_list[4]['dist'][client_id2]
            r3 = point_list[4]['dist'][client_id3]
            r4 = point_list[4]['dist'][client_id4]
        except Exception as e:
            # logger.error('四点求第五点 %s %s', e, point_list)
            return {'x': Point_xyz[0], 'y': Point_xyz[1], 'z': Point_xyz[2]}
        A = [[2 * (x1 - x2), 2 * (y1 - y2), 2 * (z1 - z2)],
             [2 * (x1 - x3), 2 * (y1 - y3), 2 * (z1 - z3)],
             [2 * (x1 - x4), 2 * (y1 - y4), 2 * (z1 - z4)]]
        # print('A', A)
        AT = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        for i in range(3):
            for j in range(3):
                AT[i][j] = A[j][i]
        # print('AT', AT)
        ATA = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        for i in range(3):
            for j in range(3):
                ATA[i][j] = AT[i][0] * A[0][j] + AT[i][1] * A[1][j] + AT[i][2] * A[2][j]
        # print('ATA', ATA)
        det = ATA[0][0] * ATA[1][1] * ATA[2][2] + ATA[0][1] * ATA[1][2] * ATA[2][0] + ATA[0][2] * ATA[1][0] * ATA[2][
            1] - ATA[2][0] * ATA[1][1] * ATA[0][2] - ATA[1][0] * ATA[0][1] * ATA[2][2] - ATA[0][0] * ATA[2][1] * ATA[1][
                  2]
        if det != 0:
            # print('det != 0')
            B = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
            B[0][0] = (ATA[1][1] * ATA[2][2] - ATA[1][2] * ATA[2][1]) / det
            B[0][1] = -(ATA[0][1] * ATA[2][2] - ATA[0][2] * ATA[2][1]) / det
            B[0][2] = (ATA[0][1] * ATA[1][2] - ATA[0][2] * ATA[1][1]) / det

            B[1][0] = -(ATA[1][0] * ATA[2][2] - ATA[1][2] * ATA[2][0]) / det
            B[1][1] = (ATA[0][0] * ATA[2][2] - ATA[0][2] * ATA[2][0]) / det
            B[1][2] = -(ATA[0][0] * ATA[1][2] - ATA[0][2] * ATA[1][0]) / det

            B[2][0] = (ATA[1][0] * ATA[2][1] - ATA[1][1] * ATA[2][0]) / det
            B[2][1] = -(ATA[0][0] * ATA[2][1] - ATA[0][1] * ATA[2][0]) / det
            B[2][2] = (ATA[0][0] * ATA[1][1] - ATA[0][1] * ATA[1][0]) / det

            H = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
            for i in range(3):
                for j in range(3):
                    H[i][j] = B[i][0] * AT[0][j] + B[i][1] * AT[1][j] + B[i][2] * AT[2][j]
            C = [0, 0, 0]
            C[0] = r2 * r2 - r1 * r1 - x2 * x2 + x1 * x1 - y2 * y2 + y1 * y1 - z2 * z2 + z1 * z1
            C[1] = r3 * r3 - r1 * r1 - x3 * x3 + x1 * x1 - y3 * y3 + y1 * y1 - z3 * z3 + z1 * z1
            C[2] = r4 * r4 - r1 * r1 - x4 * x4 + x1 * x1 - y4 * y4 + y1 * y1 - z4 * z4 + z1 * z1
            Point_xyz[0] = H[0][0] * C[0] + H[0][1] * C[1] + H[0][2] * C[2]
            Point_xyz[1] = H[1][0] * C[0] + H[1][1] * C[1] + H[1][2] * C[2]
            Point_xyz[2] = H[2][0] * C[0] + H[2][1] * C[1] + H[2][2] * C[2]
            # Point_xyz[0] = '{:.3f}'.format(Point_xyz[0])
            # Point_xyz[1] = '{:.3f}'.format(Point_xyz[1])
            # Point_xyz[2] = '{:.3f}'.format(Point_xyz[2])
        else:
            # logger.error('四点计算第五点坐标失败: %s', point_list)
            # print('det == 0')
            Point_xyz[0] = 0
            Point_xyz[1] = 0
            Point_xyz[2] = 0
        no_five_pos = {'x': Point_xyz[0], 'y': Point_xyz[1], 'z': Point_xyz[2]}  # 第五个点的坐标
        # print(point_list[4]['client_id'], ' 第五点坐标： ', no_five_pos)
        return no_five_pos

    def dingwei_biaoqian_dist_to_pos(self, jizhan_pos_param, biaoqian_dist, jizhan_list=None, using_kalman=None):
        """

        :param jizhan_pos_param: [
        {'client_id': '1-2-0', 'pos': {'x': 0, 'y': 30, 'z': 0.5}},
        {'client_id': '1-2-1', 'pos': {'x': 0, 'y': 0, 'z': 1.1}},
        {'client_id': '1-2-2', 'pos': {'x': 10, 'y': 0, 'z': 0.5}},
        {'client_id': '1-2-3', 'pos': {'x': 10, 'y': 30, 'z': 1.1}}
    ]
        :param biaoqian_dist: [{'client_id': '1-3-1', 'dist': {'1-2-0': 5 * (10 ** 0.5), '1-2-1': 5 * (10 ** 0.5), '1-2-2': 5 * (10 ** 0.5), '1-2-3': 5 * (10 ** 0.5)，...}, ...}]
        :param jizhan_list: ['1-2-0', '1-2-1', '1-2-2', '1-2-3', ...]  用其中四个基站定位标签---四个基站有多种方案
        :return:[
                    {
                        'client_id':'1-3-20',
                        'pos':{x:, y:, z:}
                    }
                ]
        """

        if jizhan_list is None:
            jizhan_list = self.get_jizhan_list_to_calc_biaoqian(jizhan_pos_param)

        # logger.debug('标签计算位置：%s %s', jizhan_pos_param, biaoqian_dist)
        biaoqian_pos = []
        for t in range(len(biaoqian_dist)):
            biaoqian_pos.append({'x': [], 'y': [], 'z': []})
        for jl in jizhan_list:
            # print('jl', jl)
            c_list_4 = []
            for i in jizhan_pos_param:
                if i['client_id'] in jl:
                    c_list_4.append(i)
            for b in range(len(biaoqian_dist)):
                # 每个标签，进行定位
                sanwei_xyz_5_list = copy.deepcopy(c_list_4)
                sanwei_xyz_5_list.append(biaoqian_dist[b])
                # logger.debug('求第五点坐标：%s', sanwei_xyz_5_list)
                the_five_pos = self.triangle_pos_xyz(sanwei_xyz_5_list)
                biaoqian_pos[b]['x'].append(the_five_pos['x'])
                biaoqian_pos[b]['y'].append(the_five_pos['y'])
                biaoqian_pos[b]['z'].append(the_five_pos['z'])
                # logger.debug('the_five_pos: %s %s', biaoqian_dist[b]['client_id'], the_five_pos)
        # logger.info('位置 多个位置平均前的 ： %s', biaoqian_pos)

        for bp in range(len(biaoqian_pos)):
            sum_x = 0
            sum_y = 0
            sum_z = 0
            for j in range(len(biaoqian_pos[bp]['x'])):
                sum_x += biaoqian_pos[bp]['x'][j]
                sum_y += biaoqian_pos[bp]['y'][j]
                sum_z += biaoqian_pos[bp]['z'][j]
            avg_x = sum_x / len(biaoqian_pos[bp]['x'])
            avg_y = sum_y / len(biaoqian_pos[bp]['y'])
            avg_z = sum_z / len(biaoqian_pos[bp]['z'])
            biaoqian_dist[bp]['pos'] = {'x': avg_x, 'y': avg_y, 'z': avg_z}
        # logger.info('位置 多个位置平均后的： %s', biaoqian_dist)

        if ((using_kalman is None) and self.using_kalman) or using_kalman:
            for i in biaoqian_dist:
                cid = i['client_id']
                i['pos']['x'] = self.kalman[cid].set_x(i['pos']['x'])
                i['pos']['y'] = self.kalman[cid].set_y(i['pos']['y'])
                i['pos']['z'] = self.kalman[cid].set_z(i['pos']['z'])
                # logger.debug('kalman pos：cid=%s %s', cid, i['pos'])
        else:  # not using kalmam
            for i in biaoqian_dist:
                cid = i['client_id']
                self.kalman[cid].set_x(i['pos']['x'])
                self.kalman[cid].set_y(i['pos']['y'])
                self.kalman[cid].set_z(i['pos']['z'])

        biaoqian_list = copy.copy(biaoqian_dist)
        # logger.info('位置 卡尔曼滤波后的位置： %s', biaoqian_list)
        return biaoqian_list