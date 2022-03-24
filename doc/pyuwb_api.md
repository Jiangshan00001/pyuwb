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
- `measure_ready_cnt`: 测量次数
- `remove_error_device`: False/True 如果测距失败，则从可用列表中移除此设备

