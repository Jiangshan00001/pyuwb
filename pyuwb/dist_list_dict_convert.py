from .client_id_utils import client_id_get_no, pack_client_id, DEVICE_TYPE_ANCHORZ, DEVICE_TYPE_ANCHOR


def dist_dict2list():
    pass

def dist_list2dict(dist_list, group_id=1):
    """
    将 距离列表 转换成 距离字典
    :param dist_list:[1,2,3,4,5,6,7,8]
    :param group_id:3
    :return:{1-2-0:1, 1-2-1:2, 1-2-2:3,...}
    """
    if not isinstance(dist_list, list):
        # 如果dist_list 不是列表，则不作处理
        return dist_list
    dist_dict = {}
    for n in range(len(dist_list)):
        one_client_id = pack_client_id(group_id, DEVICE_TYPE_ANCHOR, n)
        dist_dict[one_client_id] = dist_list[n]
    return dist_dict


if __name__ == '__main__':
    ret = dist_list2dict([1, 2, -1, 4, 5, 6, 7, 8], 1)
    # ret = dist_list2dict('1-2-0', {}, 1)
    print(ret)




