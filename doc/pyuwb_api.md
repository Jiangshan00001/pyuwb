# Table of Contents

* [pyuwb](#pyuwb)
  * [uwb\_zrzn](#pyuwb.uwb_zrzn)
    * [set\_pos\_callback](#pyuwb.uwb_zrzn.set_pos_callback)
    * [detect\_device](#pyuwb.uwb_zrzn.detect_device)
    * [device\_pos\_list](#pyuwb.uwb_zrzn.device_pos_list)
    * [tag\_no\_list](#pyuwb.uwb_zrzn.tag_no_list)
    * [anchor\_no\_list](#pyuwb.uwb_zrzn.anchor_no_list)
    * [set\_device](#pyuwb.uwb_zrzn.set_device)
    * [locate\_anchor](#pyuwb.uwb_zrzn.locate_anchor)
    * [set\_anchor\_location](#pyuwb.uwb_zrzn.set_anchor_location)
    * [measure\_distance](#pyuwb.uwb_zrzn.measure_distance)
    * [locate\_loop](#pyuwb.uwb_zrzn.locate_loop)
* [uwb\_modbus](#uwb_modbus)
  * [UwbModbus](#uwb_modbus.UwbModbus)
    * [detect\_com\_port](#uwb_modbus.UwbModbus.detect_com_port)
    * [connect](#uwb_modbus.UwbModbus.connect)
    * [check\_crc](#uwb_modbus.UwbModbus.check_crc)
    * [read\_modbus\_h](#uwb_modbus.UwbModbus.read_modbus_h)
    * [write\_modbus\_h](#uwb_modbus.UwbModbus.write_modbus_h)
    * [set\_label\_h](#uwb_modbus.UwbModbus.set_label_h)
    * [set\_buardrate\_h](#uwb_modbus.UwbModbus.set_buardrate_h)
    * [set\_device\_measure\_mode\_h](#uwb_modbus.UwbModbus.set_device_measure_mode_h)
    * [set\_device\_mode\_h](#uwb_modbus.UwbModbus.set_device_mode_h)
    * [set\_modbus\_id\_h](#uwb_modbus.UwbModbus.set_modbus_id_h)
    * [set\_device\_id\_h](#uwb_modbus.UwbModbus.set_device_id_h)
    * [set\_comm\_channel\_and\_speed\_h](#uwb_modbus.UwbModbus.set_comm_channel_and_speed_h)
    * [set\_kalman\_h](#uwb_modbus.UwbModbus.set_kalman_h)
    * [set\_recv\_delay\_h](#uwb_modbus.UwbModbus.set_recv_delay_h)
    * [set\_anchor\_enable\_h](#uwb_modbus.UwbModbus.set_anchor_enable_h)
    * [start\_measure\_h](#uwb_modbus.UwbModbus.start_measure_h)
    * [convert\_tag\_to\_anchor\_once\_h](#uwb_modbus.UwbModbus.convert_tag_to_anchor_once_h)
    * [convert\_anchor\_to\_tag\_once\_h](#uwb_modbus.UwbModbus.convert_anchor_to_tag_once_h)
    * [get\_dist\_of\_tag\_once\_inner\_h](#uwb_modbus.UwbModbus.get_dist_of_tag_once_inner_h)
    * [set\_cache\_data\_to\_default](#uwb_modbus.UwbModbus.set_cache_data_to_default)
    * [clear\_measure1\_reg](#uwb_modbus.UwbModbus.clear_measure1_reg)
    * [set\_basic\_info\_h](#uwb_modbus.UwbModbus.set_basic_info_h)
    * [get\_dist\_of\_tag\_once](#uwb_modbus.UwbModbus.get_dist_of_tag_once)
    * [convert\_mean](#uwb_modbus.UwbModbus.convert_mean)

<a id="pyuwb"></a>

# pyuwb

<a id="pyuwb.uwb_zrzn"></a>

## uwb\_zrzn Objects

```python
class uwb_zrzn(UwbModbus)
```

<a id="pyuwb.uwb_zrzn.set_pos_callback"></a>

#### set\_pos\_callback

```python
def set_pos_callback(callback_func)
```

set the callback function when dist and pos is successfully measured

**Arguments**:

- `callback_func`: def function_to_call(tag_id:int, dist:dict, pos:dict) pos:{x:1,y:2,z:3}

<a id="pyuwb.uwb_zrzn.detect_device"></a>

#### detect\_device

```python
def detect_device(tag_no_list=None, anchor_no_list=None)
```

detect if device exist

如果是空列表，则基站会检测：0,1,2,3,4,5,6,7存在不存在，标签会检测：1-10存在不存在

**Arguments**:

- `tag_no_list`: tag_no will be detected. will detect 1-10 tag is exist or not if None or empty.  如果是空标签会检测：1-10号标签是否存在
- `anchor_no_list`: anchor_no will be detected. will detect 0-7 anchor is exist or not if None or empty. 如果为空，则会检测0-7号基站是否存在

**Returns**:

exist tag_no_list, exist anchor_no_list

<a id="pyuwb.uwb_zrzn.device_pos_list"></a>

#### device\_pos\_list

```python
def device_pos_list()
```

get all device current pos

**Returns**:

[{'client_id':'1-2-3', pos:{x:,y:,z:}},...]

<a id="pyuwb.uwb_zrzn.tag_no_list"></a>

#### tag\_no\_list

```python
def tag_no_list()
```

get current tag no list

**Returns**:

[1,2,3,...]

<a id="pyuwb.uwb_zrzn.anchor_no_list"></a>

#### anchor\_no\_list

```python
def anchor_no_list()
```

get current anchor no list

**Returns**:

[0,1,2,3,...]

<a id="pyuwb.uwb_zrzn.set_device"></a>

#### set\_device

```python
def set_device(tag_no_list, anchor_no_list, using_master=0)
```

set device to use.

this function will auto called when  you call detect_device.
如果不需要检测设备，直接指定设备列表也可以 (tag_no_list：标签列表，anchor_no_list：次基站列表，using_master：是否使用主基站测距【1代表使用，0代表不使用】)
暂不支持通过master进行定位

**Arguments**:

- `tag_no_list`: tag no in the system. eg:[1,2,3,...]
- `anchor_no_list`: anchor no in the system eg: [0,1,2,3]
- `using_master`: 0

**Returns**:

None

<a id="pyuwb.uwb_zrzn.locate_anchor"></a>

#### locate\_anchor

```python
def locate_anchor(height_list=(0.5, 1.1, 0.5, 1.1),
                  direction_point=('N', 'S', 'E'),
                  measure_ready_cnt=40)
```

对基站坐标进行定位：

1 测距：各基站到其他基站的距离：
2 计算位置：根据距离和高度参数，以及顺序位置，建立坐标系

**Arguments**:

- `height_list`: 高度列表，需要和设备数一致
- `measure_ready_cnt`: 测距次数，多次测量取均值，用于提高测距精度，进而提高定位精度

<a id="pyuwb.uwb_zrzn.set_anchor_location"></a>

#### set\_anchor\_location

```python
def set_anchor_location(anchor_pos, using_master=0)
```

**Arguments**:

- `anchor_pos`: [{client_id:'1-2-0', pos:{x:, y:, z:}} ]
- `using_master`: False/True

<a id="pyuwb.uwb_zrzn.measure_distance"></a>

#### measure\_distance

```python
def measure_distance(client_id1, client_id2)
```

测量获取距离

**Arguments**:

- `client_id1`: 
- `client_id2`: 

**Returns**:

两个设备间的距离，单位m

<a id="pyuwb.uwb_zrzn.locate_loop"></a>

#### locate\_loop

```python
def locate_loop(tag_no_list=None, wait_for_finish=0, timeout=10.0)
```

测量循环

**Arguments**:

- `tag_no_list`: 
- `wait_for_finish`: 
- `timeout`: 

<a id="uwb_modbus"></a>

# uwb\_modbus

<a id="uwb_modbus.UwbModbus"></a>

## UwbModbus Objects

```python
class UwbModbus()
```

<a id="uwb_modbus.UwbModbus.detect_com_port"></a>

#### detect\_com\_port

```python
def detect_com_port()
```

检测串口：

**Returns**:

'COM3'  对应uwb的主基站串口
没有相应设备时，为None

<a id="uwb_modbus.UwbModbus.connect"></a>

#### connect

```python
def connect(com_port=None)
```

连接串口

<a id="uwb_modbus.UwbModbus.check_crc"></a>

#### check\_crc

```python
def check_crc(payload: bytes)
```

**Arguments**:

- `payload`: 带校验和的报文，最后2byte的校验和会被用于比较

**Returns**:

正确返回True, 否则返回false

<a id="uwb_modbus.UwbModbus.read_modbus_h"></a>

#### read\_modbus\_h

```python
def read_modbus_h(reg_start_addr, reg_count, addr=1)
```

**Arguments**:

- `reg_start_addr`: 
- `reg_count`: 
- `addr`: 

**Returns**:

is_ok, ilist, bytes_data

<a id="uwb_modbus.UwbModbus.write_modbus_h"></a>

#### write\_modbus\_h

```python
def write_modbus_h(add2, reg_count, dat, id=1, just_gen_pkt=0)
```

例子：开始测距 01 10 00 28 00 01 02 00 04 A1 BB

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

**Arguments**:

- `id`: 
- `add2`: 
- `reg_count`: 
- `dat`: 

<a id="uwb_modbus.UwbModbus.set_label_h"></a>

#### set\_label\_h

```python
def set_label_h(label_no_list=(0, ))
```

如果label_no_list=[1] 则发送数据为 00 01

如果label_no_list=[1,2] 则发送数据为 02 01
如果label_no_list=[1,2,3] 则发送数据为 02 01 00 03

**Arguments**:

- `label_no_list`: 

<a id="uwb_modbus.UwbModbus.set_buardrate_h"></a>

#### set\_buardrate\_h

```python
def set_buardrate_h(rate_no=7)
```

设备串口通讯波特率

**Arguments**:

- `rate_no`: 0：4800  1：9600 2：14400 3：19200 4：38400 5：56000 6：57600 7：115200  8：128000 9：256000

<a id="uwb_modbus.UwbModbus.set_device_measure_mode_h"></a>

#### set\_device\_measure\_mode\_h

```python
def set_device_measure_mode_h(cmode=1, dmode=0)
```

**Arguments**:

- `cmode`: 测量模式   0：DS-TWR 1：高性能TWR。
- `dmode`: 测距模式 1:二维模式 2：三维模式"

<a id="uwb_modbus.UwbModbus.set_device_mode_h"></a>

#### set\_device\_mode\_h

```python
def set_device_mode_h(mode=2)
```

**Arguments**:

- `mode`: 设备模式 0：tag 1：anchor 2：anchorz

<a id="uwb_modbus.UwbModbus.set_modbus_id_h"></a>

#### set\_modbus\_id\_h

```python
def set_modbus_id_h(mid)
```

**Arguments**:

- `mid`: modbus_id/addr to set.

<a id="uwb_modbus.UwbModbus.set_device_id_h"></a>

#### set\_device\_id\_h

```python
def set_device_id_h(device_id=0)
```

设备ID，高8位为次基站ID，范围0~6 ，

低8位为标签ID ，0~99
（程序内部 标签ID为0~247  次基站ID为248~254  主基站ID为255）

**Arguments**:

- `device_id`: 

<a id="uwb_modbus.UwbModbus.set_comm_channel_and_speed_h"></a>

#### set\_comm\_channel\_and\_speed\_h

```python
def set_comm_channel_and_speed_h(channel=1, speed=2)
```

byte0-空中信道，byte1-空中传输速率

**Arguments**:

- `channel`: 
- `speed`: 

<a id="uwb_modbus.UwbModbus.set_kalman_h"></a>

#### set\_kalman\_h

```python
def set_kalman_h(param_q=3, param_r=0x0a)
```

**Arguments**:

- `param_q`: 
- `param_r`: 

<a id="uwb_modbus.UwbModbus.set_recv_delay_h"></a>

#### set\_recv\_delay\_h

```python
def set_recv_delay_h(delay=0x80CF, just_gen_pkt=0)
```

**Arguments**:

- `delay`: 

<a id="uwb_modbus.UwbModbus.set_anchor_enable_h"></a>

#### set\_anchor\_enable\_h

```python
def set_anchor_enable_h(jizhan_index=0, enabled=1)
```

基站固定的有7个。编号为0-6. 对应 BCDEFGH

**Arguments**:

- `jizhan_index`: 基站编号 0-6
- `enabled`: 0--disable. 1--enable it

<a id="uwb_modbus.UwbModbus.start_measure_h"></a>

#### start\_measure\_h

```python
def start_measure_h(mode=6)
```

**Arguments**:

- `mode`: 0x04：持续测量，主动发送，不写入寄存器
0x03：单次测量，主动发送，写入寄存器
0x02：持续测量，不发送，写入寄存器
0x01：单次测量，不发送，写入寄存器
0x00: 停止测量"

<a id="uwb_modbus.UwbModbus.convert_tag_to_anchor_once_h"></a>

#### convert\_tag\_to\_anchor\_once\_h

```python
def convert_tag_to_anchor_once_h(client_id)
```

将标签 转化为 次基站

<a id="uwb_modbus.UwbModbus.convert_anchor_to_tag_once_h"></a>

#### convert\_anchor\_to\_tag\_once\_h

```python
def convert_anchor_to_tag_once_h(client_id)
```

将次基站 转化为 标签0

<a id="uwb_modbus.UwbModbus.get_dist_of_tag_once_inner_h"></a>

#### get\_dist\_of\_tag\_once\_inner\_h

```python
def get_dist_of_tag_once_inner_h()
```

获取某个标签的距离:
测量3次，取平均值

<a id="uwb_modbus.UwbModbus.set_cache_data_to_default"></a>

#### set\_cache\_data\_to\_default

```python
def set_cache_data_to_default()
```

标签20 21 到各次基站的距离

<a id="uwb_modbus.UwbModbus.clear_measure1_reg"></a>

#### clear\_measure1\_reg

```python
def clear_measure1_reg()
```

清除寄存器0x2f->0x36 8个寄存器


<a id="uwb_modbus.UwbModbus.set_basic_info_h"></a>

#### set\_basic\_info\_h

```python
def set_basic_info_h(tag_no_list, except_anchor_list=None)
```

设置测距的基本信息。会通过bulk模式发送

**Arguments**:

- `tag_no_list`: [20,21,22,23,24] tag_no_list that will be used
- `except_anchor_list`: anchor that will be excluded. 默认的是空。

<a id="uwb_modbus.UwbModbus.get_dist_of_tag_once"></a>

#### get\_dist\_of\_tag\_once

```python
def get_dist_of_tag_once(loop_mean_cnt=20)
```

获取标签距离，默认平均20次

<a id="uwb_modbus.UwbModbus.convert_mean"></a>

#### convert\_mean

```python
def convert_mean(dist_list)
```

求均值函数

**Arguments**:

- `dist_list`: 

