class KalmanFilterXYZ:
    def __init__(self,Q=3.0, R=10.0):
        self.kx=KalmanFilter(Q, R)
        self.ky=KalmanFilter(Q, R)
        self.kz=KalmanFilter(Q, R)
    def set_x(self,x):
        return self.kx.set_val(x)
    def set_y(self, y):
        return self.ky.set_val(y)
    def set_z(self, z):
        return self.kz.set_val(z)
class KalmanFilter:
    def __init__(self, Q=3.0, R=10.0):
        self.p_last = 0
        self.ProcessNiose_Q = Q
        self.MeasureNoise_R=R
        self.val_last = None
    def set_val(self, val):
        if self.val_last is None:
            self.val_last=val
        # 卡尔曼滤波 基于下一时刻位置不变模型
        p_mid = self.p_last + self.ProcessNiose_Q
        # 预测本次误差
        kg = p_mid / (p_mid + self.MeasureNoise_R)
        # 更新本次卡尔曼增益
        data_now = self.val_last + kg * (val - self.val_last)
        # 根据本次观测值预测本次输出
        p_now = (1 - kg) * p_mid
        # 更新误差
        self.p_last = p_now
        self.val_last = data_now
        return data_now


def Filter_Kalman(data_now, data_last, p_last, ProcessNiose_Q, MeasureNoise_R):
    """

    :param data_now: 数值 x/y/z
    :param data_last:  上一次的数值
    :param p_last:
    :param ProcessNiose_Q: 3
    :param MeasureNoise_R: 10
    :return:
    """
    # 卡尔曼滤波 基于下一时刻位置不变模型
    result = [[], []]
    p_mid = p_last + ProcessNiose_Q
    # 预测本次误差
    kg = p_mid / (p_mid + MeasureNoise_R)
    # 更新本次卡尔曼增益
    data_now = data_last + kg * (data_now - data_last)
    # 根据本次观测值预测本次输出
    p_now = (1 - kg) * p_mid
    # 更新误差
    p_last = p_now
    result[0] = data_now
    result[1] = p_last
    return result

def test_kf1():
    x=[1,2,1,2,1]
    p_last = 0
    x_dn=[]
    last_val = 1.0
    for i in range(len(x)):
        ret= Filter_Kalman(x[i],last_val, p_last, 3, 10)
        p_last = ret[1]
        print('ret:',i, ret[0])
        last_val = ret[0]
        x_dn.append(ret[0])

    assert x_dn[0]==1.0
    assert x_dn[1]==1.3467336683417086
    assert x_dn[2]==1.2105584375953615
    assert x_dn[3]==1.5336301851417857
    assert x_dn[4]==1.3122030348062983


def test_kf2():
    x=[1,2,1,2,1]
    kf2 = KalmanFilter()
    x_dn=[]
    for i in range(len(x)):
        curr_val = kf2.set_val(x[i])
        print('ret:',curr_val)
        x_dn.append(curr_val)

    assert x_dn[0]==1.0
    assert x_dn[1]==1.3467336683417086
    assert x_dn[2]==1.2105584375953615
    assert x_dn[3]==1.5336301851417857
    assert x_dn[4]==1.3122030348062983

if __name__=='__main__':
    test_kf1()
    test_kf2()


