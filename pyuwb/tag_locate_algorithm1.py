from .dingwei import Dingwei

class TagLocateAlgorithm1(Dingwei):
    def __init__(self):
        super().__init__()

    def calc(self, tag_dist, tag_client_id, anchor_pos=None, using_kalman= None):

        """
        传递基站位置信息和标签与基站的距离信息，返回标签位置
        :param anchor_pos:[{client_id:1-2-3, pos:{x:,y:,z:}}...]
        :param tag_dist: {1-2-3:10.4, 1-2-0:5,...}
        :return:{x:,y:， z:}
        """
        jizhan_pos_param = anchor_pos

        tag_pos_dict = {}

        # {'client_id': '1-3-1', 'dist': {'1-2-0': 5 * (10 ** 0.5), '1-2-1': 5 * (10 ** 0.5), '1-2-2': 5 * (10 ** 0.5), '1-2-3': 5 * (10 ** 0.5)，...}, ...}
        tag_dict = {'dist': tag_dist, 'client_id': tag_client_id}
        tag_pos_one_list = self.dingwei_biaoqian_dist_to_pos(jizhan_pos_param, [tag_dict], using_kalman=None)
        print('tag_pos_one_list', tag_pos_one_list)
        return tag_pos_one_list[0]['pos']



def test_demo1():
    anchor_pos = [
        {'client_id': '1-2-0', 'pos': {'x': 0, 'y': 30, 'z': 0.5}},
        {'client_id': '1-2-1', 'pos': {'x': 0, 'y': 0, 'z': 1.1}},
        {'client_id': '1-2-2', 'pos': {'x': 10, 'y': 0, 'z': 0.5}},
        {'client_id': '1-2-3', 'pos': {'x': 10, 'y': 30, 'z': 1.1}}
    ]
    tag_dist = {'1-2-0': 5 * (10 ** 0.5), '1-2-1': 5 * (10 ** 0.5), '1-2-2': 5 * (10 ** 0.5), '1-2-3': 5 * (10 ** 0.5)}
    t = TagLocateAlgorithm1()
    t.calc(tag_dist, '1-3-1', anchor_pos)


if __name__ == '__main__':
    test_demo1()
