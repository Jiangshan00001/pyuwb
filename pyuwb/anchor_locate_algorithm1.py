from .locate_base import AnchorLocateBase
from .dingwei import Dingwei


class AnchorLocateAlgorithm1(AnchorLocateBase):
    """
    根据基站的距离信息，生成位置信息
    """

    def __init__(self):
        super().__init__()

    def calc(self):
        """
        self.anchor_list [
        {
            client_id:'1-2-3',
            dist:{'1-2-1':10.5,... },
            direction_point:'N'
        },
        ...
          ]

        :return:
        """
        # 次基站定位
        anchor_pos_list = Dingwei().calc_anchor_pos(self.anchor_list)
        ret = []
        for i in anchor_pos_list:
            d = {}
            d['client_id'] = i['client_id']
            d['pos'] = i['pos']
            ret.append(d)
        print('基站坐标：', ret)
        return ret


def get_dist(xy1,xy2):
    return ((xy1['x']-xy2['x'])**2+(xy1['y']-xy2['y'])**2)**0.5

def test_rect1():
    """
    基站在10x30长方形4个顶点：
    :return:
    """
    a = AnchorLocateAlgorithm1()
    anchor_and_dist = [
        {'client_id': '1-2-0', 'direction_point': 'N',
         'dist': {'1-2-0': 0, '1-2-1': 30, '1-2-2': 10 * (10 ** 0.5), '1-2-3': 10}, 'height': 0.5},
        {'client_id': '1-2-1', 'direction_point': 'S',
         'dist': {'1-2-0': 30, '1-2-1': 0, '1-2-2': 10, '1-2-3': 10 * (10 ** 0.5)}, 'height': 1.1},
        {'client_id': '1-2-2', 'direction_point': 'E',
         'dist': {'1-2-0': 10 * (10 ** 0.5), '1-2-1': 10, '1-2-2': 0, '1-2-3': 30}, 'height': 0.5},
        {'client_id': '1-2-3', 'direction_point': None,
         'dist': {'1-2-0': 10, '1-2-1': 10 * (10 ** 0.5), '1-2-2': 30, '1-2-3': 0}, 'height': 1.1}
    ]

    a.set_anchor_info(anchor_and_dist)
    a.calc()
    l = a.get_anchor_pos()
    assert (get_dist(l[0]['pos'], {'x': 0, 'y':30})<0.1)
    assert (get_dist(l[1]['pos'], {'x': 0, 'y':0})<0.1)
    assert (get_dist(l[2]['pos'], {'x': 10, 'y':0})<0.1)
    assert (get_dist(l[3]['pos'], {'x': 10, 'y':30})<0.1)


if __name__ == '__main__':
    test_rect1()
