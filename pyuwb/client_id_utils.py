__author__ = "songjiangshan"
__copyright__ = "Copyright (C) 2021 songjiangshan \n All Rights Reserved."
__license__ = ""
__version__ = "1.0"


def client_id_remove_group(client_id):
    return str(client_id_get_type(client_id)) + '-' + str(client_id_get_no(client_id))


def client_id_get_no(client_id: str):
    """
    输入字符串，返回对应的号
    :param client_id:
    :return: int型数值
    """
    id = int(client_id.split('-')[-1])

    return id


def client_id_get_type(client_id):
    id = int(client_id.split('-')[-2])
    return id


def client_id_get_group(client_id):
    id = int(client_id.split('-')[0])
    return id


def pack_client_id(group_id=0, type_int=2, no=0):
    ret = str(group_id) + '-' + str(type_int) + '-' + str(no)
    return ret


if __name__ == '__main__':
    assert client_id_get_no('1-2-3') == 3
    assert client_id_get_no('1-2-20') == 20
    assert client_id_get_no('1-12-21') == 21
    print(client_id_get_type('1-12-21'))

    # assert client_id_get_type('1-2-3') == 2
    # assert client_id_get_group('1-2-3') == 1
    # assert client_id_get_group('2-2-3') == 2
