使用dw1000的uwb模块上层软件开发包。


设备定义：
client_id: 设备的编号，格式:{group_id}-{type_id}-{client_no}是一个字符串.eg:1-2-4.
           其中:group_id: 现在是1.
		        type_id:  1--主基站(中枢基站). 2--次基站，固定位置的定位基站。 3 --标签，被定位设备
				client_no: 设备号，从0开始.

测距代码:
```
from pyuwb import uwb
h=uwb()
#连接串口设备
h.connect()
# 设置设备列表
h.set_device(tag_no_list=[1], anchor_no_list=[0])
# 获取距离
dist_meter = h.get_distance('1-3-1', '1-2-0')
print('distance between 1-3-1 & 1-2-0', dist_meter,'meter')
```

定位代码:
```
from pyuwb import uwb
h=uwb()
#连接串口
h.connect(com_port="COM3") #set to None will auto-detect the port
# 设置设备
h.set_device(tag_no_list=[1,2], anchor_no_list=[0,1,2,3])
# 定位基站位置
anchor_pos_list = h.locate_anchor()
#显示基站位置
print(anchor_pos_list)
# 开始标签的定位
located_tag_pos = h.start_locate_once()
print('located_tag_pos:', located_tag_pos)
```

定位代码2-回调函数：
```
from pyuwb import uwb
h=uwb()
# 连接串口
h.connect(com_port="COM3") #set to None will auto-detect the port
# 自动检测周围存在的设备
h.detect_device()
# 设置基站位置
anchor_pos_list = [{'client_id': '1-2-0', 'pos': {'x': 0, 'y': 5.5, 'z': 0.5}},
                       {'client_id': '1-2-1', 'pos': {'x': 0, 'y': 0, 'z': 1.1}},
                       {'client_id': '1-2-2', 'pos': {'x': 2.67, 'y': -0.33, 'z': 0.5}},
                       {'client_id': '1-2-3', 'pos': {'x': 4.03, 'y': 5.47, 'z': 1.1},
                       }]
h.set_anchor_location(anchor_pos_list)

def function_to_call(tag_no,dist, pos):
	# 每次定位成功一次，会调用一次这个函数
	print('定位：function_to_call', tag_no,pos, dist)
# 设置回调函数
h.set_pos_callback(function_to_call)

# 定位一次10秒钟
h.set_to_start()
t1=time.time()

while time.time()-t1<10:
	h.locate_loop()

h.stop_measure_h()
```

[详细说明](doc/pyuwb_api.md)

