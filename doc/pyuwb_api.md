# Table of Contents

* [pyuwb](#pyuwb)
  * [uwb\_zrzn](#pyuwb.uwb_zrzn)
    * [detect\_device](#pyuwb.uwb_zrzn.detect_device)
    * [set\_device](#pyuwb.uwb_zrzn.set_device)
    * [locate\_anchor](#pyuwb.uwb_zrzn.locate_anchor)
    * [set\_anchor\_location](#pyuwb.uwb_zrzn.set_anchor_location)
    * [get\_distance](#pyuwb.uwb_zrzn.get_distance)
    * [get\_jizhan\_and\_biaoqian\_info](#pyuwb.uwb_zrzn.get_jizhan_and_biaoqian_info)
    * [anchor\_zidong\_ceju](#pyuwb.uwb_zrzn.anchor_zidong_ceju)
    * [locate\_loop](#pyuwb.uwb_zrzn.locate_loop)
    * [biaoqian\_zidong\_ceju](#pyuwb.uwb_zrzn.biaoqian_zidong_ceju)
    * [tag\_a\_process](#pyuwb.uwb_zrzn.tag_a_process)
    * [decode\_measure\_payload](#pyuwb.uwb_zrzn.decode_measure_payload)
    * [count\_for\_payload\_func](#pyuwb.uwb_zrzn.count_for_payload_func)
    * [avg\_dist\_data](#pyuwb.uwb_zrzn.avg_dist_data)
    * [tag\_dist\_cache\_to\_one](#pyuwb.uwb_zrzn.tag_dist_cache_to_one)
    * [one\_tag\_dist\_got](#pyuwb.uwb_zrzn.one_tag_dist_got)
    * [tag\_dist\_process](#pyuwb.uwb_zrzn.tag_dist_process)
    * [data\_cali\_v2](#pyuwb.uwb_zrzn.data_cali_v2)
    * [measure\_read](#pyuwb.uwb_zrzn.measure_read)
    * [check\_anchor\_dist\_measure\_finish](#pyuwb.uwb_zrzn.check_anchor_dist_measure_finish)
    * [measure\_one\_anchor\_dist](#pyuwb.uwb_zrzn.measure_one_anchor_dist)
    * [detect\_com\_port](#pyuwb.uwb_zrzn.detect_com_port)
    * [set\_cache\_data\_to\_default](#pyuwb.uwb_zrzn.set_cache_data_to_default)
    * [set\_basic\_info](#pyuwb.uwb_zrzn.set_basic_info)
    * [clear\_measure1\_reg](#pyuwb.uwb_zrzn.clear_measure1_reg)
    * [get\_dist\_of\_biaoqian\_once](#pyuwb.uwb_zrzn.get_dist_of_biaoqian_once)
    * [convert\_mean](#pyuwb.uwb_zrzn.convert_mean)
    * [get\_pos\_of\_biaoqian\_once](#pyuwb.uwb_zrzn.get_pos_of_biaoqian_once)

<a id="pyuwb"></a>

# pyuwb

<a id="pyuwb.uwb_zrzn"></a>

## uwb\_zrzn Objects

```python
class uwb_zrzn(UwbModbus)
```

<a id="pyuwb.uwb_zrzn.detect_device"></a>

#### detect\_device

```python
def detect_device(tag_no_list=None, anchor_no_list=None)
```

如果是空列表，则基站会检测：0,1,2,3,4,5,6,7存在不存在，标签会检测：1-10存在不存在

**Arguments**:

- `tag_no_list`: 如果是空标签会检测：1-10存在不存在
- `anchor_no_list`: 

<a id="pyuwb.uwb_zrzn.set_device"></a>

#### set\_device

```python
def set_device(tag_no_list, anchor_no_list, using_master=0)
```

如果不需要检测设备，直接指定设备列表也可以 (tag_no_list：标签列表，anchor_no_list：次基站列表，using_master：是否使用主基站测距【1代表使用，0代表不使用】)

<a id="pyuwb.uwb_zrzn.locate_anchor"></a>

#### locate\_anchor

```python
def locate_anchor(height_list=[0.5, 1.1, 0.5, 1.1],
                  direction_point=['N', 'S', 'E'],
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

<a id="pyuwb.uwb_zrzn.get_distance"></a>

#### get\_distance

```python
def get_distance(client_id1, client_id2)
```

测量获取距离

**Arguments**:

- `client_id1`: 
- `client_id2`: 

**Returns**:

两个设备间的距离，单位m

<a id="pyuwb.uwb_zrzn.get_jizhan_and_biaoqian_info"></a>

#### get\_jizhan\_and\_biaoqian\_info

```python
def get_jizhan_and_biaoqian_info()
```

**Returns**:

[{client_id:, pos:{x:,y:,z:}}], [{client_id:, pos:{x:,y:,z:}}]

<a id="pyuwb.uwb_zrzn.anchor_zidong_ceju"></a>

#### anchor\_zidong\_ceju

```python
def anchor_zidong_ceju(anchor_client_list, measure_ready_cnt=40)
```

基站的测距：

**Arguments**:

- `anchor_client_list`: [ {client_id:'1-2-3', }]

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

<a id="pyuwb.uwb_zrzn.biaoqian_zidong_ceju"></a>

#### biaoqian\_zidong\_ceju

```python
def biaoqian_zidong_ceju(tag_client_list, anchor_client_list=None)
```

**Arguments**:

- `tag_client_list`: [{client_id:,}, ...]
- `anchor_client_list`: [{client_id:,}, ...]

<a id="pyuwb.uwb_zrzn.tag_a_process"></a>

#### tag\_a\_process

```python
def tag_a_process(tag_id, acce_x, acce_y, acce_z)
```

向tag_a_xyz中添加 标签20 21 的加速度

<a id="pyuwb.uwb_zrzn.decode_measure_payload"></a>

#### decode\_measure\_payload

```python
def decode_measure_payload(payload63: bytes, pkt_has_height=1)
```

解码报文

**Arguments**:

- `payload63`: 
- `pkt_has_height`: 

<a id="pyuwb.uwb_zrzn.count_for_payload_func"></a>

#### count\_for\_payload\_func

```python
def count_for_payload_func(tag_id, dista, status, acce_x, acce_y, acce_z)
```

测试 运行速度


<a id="pyuwb.uwb_zrzn.avg_dist_data"></a>

#### avg\_dist\_data

```python
def avg_dist_data(data_list, last_data)
```

距离数据的平均滤波。避免跳动太大

**Arguments**:

- `data_list`: 
- `last_data`: 

<a id="pyuwb.uwb_zrzn.tag_dist_cache_to_one"></a>

#### tag\_dist\_cache\_to\_one

```python
def tag_dist_cache_to_one(tag_id)
```

标签的距离，采用多次测量取平均值的方式


<a id="pyuwb.uwb_zrzn.one_tag_dist_got"></a>

#### one\_tag\_dist\_got

```python
def one_tag_dist_got(tag_id)
```

每次接收到1次设备发来的标签距离信息，则会调用此函数

**Arguments**:

- `tag_id`: 

<a id="pyuwb.uwb_zrzn.tag_dist_process"></a>

#### tag\_dist\_process

```python
def tag_dist_process(tag_id, dista, status)
```

处理距离

**Arguments**:

- `dista`: 
- `status`: 
- `tag_id`: 

<a id="pyuwb.uwb_zrzn.data_cali_v2"></a>

#### data\_cali\_v2

```python
def data_cali_v2(client_id, anchor_id_n, curr_val, cali_param)
```



<a id="pyuwb.uwb_zrzn.measure_read"></a>

#### measure\_read

```python
def measure_read(pkt_has_height=1)
```

读取串口数据并解码，用于主基站主动发数据的模式

**Arguments**:

- `pkt_has_height`: 

**Returns**:

此次处理的报文数，此次处理的字节数

<a id="pyuwb.uwb_zrzn.check_anchor_dist_measure_finish"></a>

#### check\_anchor\_dist\_measure\_finish

```python
def check_anchor_dist_measure_finish()
```

读取串口测距报文，处理后，查看哪些测距已经完成

**Returns**:

is_finish, 100

<a id="pyuwb.uwb_zrzn.measure_one_anchor_dist"></a>

#### measure\_one\_anchor\_dist

```python
def measure_one_anchor_dist(client_id,
                            measure_ready_cnt=40,
                            remove_error_device=True)
```

测量某个基站到其他基站的距离

**Arguments**:

- `client_id`: 当前要测量的次基站client_id       次基站的id：eg: 1-2-1
- `all_measure_anchor_client_id`: 所有使用的次基站client_id ['1-2-1','1-2-2']

<a id="pyuwb.uwb_zrzn.detect_com_port"></a>

#### detect\_com\_port

```python
def detect_com_port()
```

检测串口：

**Returns**:

'COM3'  对应uwb的主基站串口
没有相应设备时，为None

<a id="pyuwb.uwb_zrzn.set_cache_data_to_default"></a>

#### set\_cache\_data\_to\_default

```python
def set_cache_data_to_default()
```

标签20 21 到各次基站的距离

<a id="pyuwb.uwb_zrzn.set_basic_info"></a>

#### set\_basic\_info

```python
def set_basic_info(label_list, except_jizhan_list=None)
```

设置测距的基本信息。会通过bulk模式发送

**Arguments**:

- `label_list`: [20,21,22,23,24]
- `except_jizhan_list`: 默认的是6各基站:0 1,2,3,4,5.对应基站：1-2-0,1-2-5.

<a id="pyuwb.uwb_zrzn.clear_measure1_reg"></a>

#### clear\_measure1\_reg

```python
def clear_measure1_reg()
```

清除寄存器0x2f->0x36 8个寄存器


<a id="pyuwb.uwb_zrzn.get_dist_of_biaoqian_once"></a>

#### get\_dist\_of\_biaoqian\_once

```python
def get_dist_of_biaoqian_once()
```

获取某个标签的距离:
测量3次，取平均值

<a id="pyuwb.uwb_zrzn.convert_mean"></a>

#### convert\_mean

```python
def convert_mean(dist_list)
```

求均值函数

**Arguments**:

- `dist_list`: 

<a id="pyuwb.uwb_zrzn.get_pos_of_biaoqian_once"></a>

#### get\_pos\_of\_biaoqian\_once

```python
def get_pos_of_biaoqian_once(loop_mean_cnt=20)
```

获取标签距离，默认平均20次

