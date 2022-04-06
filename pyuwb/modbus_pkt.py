from .calc_crc import calc_crc,check_crc
import copy
"""
生成和解码modbus报文
"""

def get_read_pkt(start_reg, reg_count, addr=1):
    """
    生成读报文
    :param start_reg:
    :param reg_count:
    :param addr:
    :return:
    """
    # print('read_modbus: ', add2.to_bytes(2, 'big').hex(), reg_count.to_bytes(1, 'big').hex(), id)
    to_w = addr.to_bytes(1, byteorder='big', signed=False) + b'\x03' + start_reg.to_bytes(2, byteorder='big',
                                                                                   signed=False) + reg_count.to_bytes(
        2, byteorder='big', signed=False)

    to_w_crc = calc_crc(to_w)
    to_w = to_w + to_w_crc
    return to_w

def get_write_pkt( start_reg, reg_count, dat_to_write:bytes, addr=1):
    """
    生成写报文
    :param start_reg:
    :param reg_count:
    :param dat_to_write:
    :param addr:
    :return:
    """
    to_r = addr.to_bytes(1, byteorder='big', signed=False) + b'\x10' + start_reg.to_bytes(2, byteorder='big',
                                                                                   signed=False) + reg_count.to_bytes(
        2, byteorder='big', signed=False) + \
           len(dat_to_write).to_bytes(1, byteorder='big', signed=False) + dat_to_write
    to_r_crc = calc_crc(to_r)
    to_r = to_r + to_r_crc
    return to_r



def decode_read_return(payload:bytes, to_read_reg_count):
    ret=payload
    to_read_len = 5 + to_read_reg_count * 2
    if len(payload) == to_read_len:
        if check_crc(ret):
            check_crc_ok = 1
        else:
            check_crc_ok = 0
        ret2 = {'id': int(ret[0]), 'cmd': int(ret[1]), 'byte_cnt': int(ret[2]),
                'data': ret[3:-2], 'crc': ret[-2:], 'raw_data': ret, 'crc_ok': check_crc_ok}
        ret3 = copy.deepcopy(ret2)
        ret3['raw_data'] = ret3['raw_data'].hex()
        ret3['data'] = ret3['data'].hex()
        ret3['crc'] = ret3['crc'].hex()
    else:
        ret2 = {'raw_data': ret, 'crc_ok': 0}
        ret3 = copy.deepcopy(ret2)
        ret3['raw_data'] = ret3['raw_data'].hex()

    return ret2

def decode_write_return(payload:bytes):
    ret=payload
    if len(payload) == 8:
        if check_crc(payload):
            check_crc_ok = 1
        else:
            check_crc_ok = 0
        ret2 = {'id': int(ret[0]), 'cmd': int(ret[1]), 'start': int(ret[2]) * 256 + int(ret[3]),
                'byte_cnt': 2 * (int(ret[4]) * 256 + int(ret[5])),
                'crc': ret[-2:], 'raw_data': ret, 'crc_ok': check_crc_ok}
        ret3 = copy.deepcopy(ret2)
        ret3['raw_data'] = ret3['raw_data'].hex()
        ret3['crc'] = ret3['crc'].hex()
    else:
        ret2 = {'raw_data': ret, 'crc_ok': 0}
        ret3 = copy.deepcopy(ret2)
        ret3['raw_data'] = ret3['raw_data'].hex()

    return ret2

def split_packet(buf: bytes, pkt_length, read_error_stat):
    read_error_cnt = 0
    ret_pkt_process = 0
    ret_byte_process = 0
    pkt_list = []
    read_ok_cnt = 0

    while True:
        if len(buf) < pkt_length:
            # 报文不够长
            read_error_cnt += 1
            if 'less' not in read_error_stat:
                read_error_stat['less'] = 0
            read_error_stat['less'] += 1
            break
        if buf[0] != 1:
            # 报文头不对
            buf = buf[1:]
            read_error_cnt += 1
            ret_byte_process += 1

            if 'start' not in read_error_stat:
                read_error_stat['start'] = 0
            read_error_stat['start'] += 1
            continue
        if buf[1] != 3:
            # 报文头不对 01 03
            buf = buf[1:]
            read_error_cnt += 1
            ret_byte_process += 1

            if 'read' not in read_error_stat:
                read_error_stat['read'] = 0
            read_error_stat['read'] += 1
            continue
        if buf[2] != 0x2A:
            # 报文头不对 01 03 2A
            buf = buf[1:]
            ret_byte_process += 1
            read_error_cnt += 1

            if 'len' not in read_error_stat:
                read_error_stat['len'] = 0
            read_error_stat['len'] += 1
            continue

        if not check_crc(buf[:pkt_length]):
            print('crc error. ', buf[:pkt_length].hex(),
                  calc_crc(buf[:pkt_length - 2]).hex())
            buf = buf[1:]
            read_error_cnt += 1
            ret_byte_process += 1

            if 'crc' not in read_error_stat:
                read_error_stat['crc'] = 0
            read_error_stat['crc'] += 1
            continue

        read_ok_cnt += 1
        ret_pkt_process += 1
        ret_byte_process += pkt_length
        pkt_list.append(buf[0:pkt_length])
        if len(buf) > pkt_length:
            buf = buf[pkt_length:]
        else:
            buf = b''

    return pkt_list, buf, read_error_cnt, ret_pkt_process, ret_byte_process


def test_read_pkt1():
    pass


def test_write_pkt1():
    pass

if __name__=='__main__':
    pass


