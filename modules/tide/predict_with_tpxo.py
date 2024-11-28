from datetime import datetime

import numpy as np

from . import constituent
from .tide import Tide
from .tpxo1 import get_tpxo
import pandas as pd


def predict_tide(points, times):

    harmonic_constants = get_tpxo(points)

    results = []

    for index, point in enumerate(points):
        # 提取潮汐成分、振幅和相位
        tides = ['M2', 'S2', 'K1', 'N2', 'P1', 'O1', 'K2', 'Q1', 'M4']
        amplitudes = [harmonic_constants[index][f'{tide}_amp'] for tide in tides]
        phases = [harmonic_constants[index][f'{tide}_phase'] for tide in tides]

        # 获取潮汐成分的对象
        constituents = [getattr(constituent, f"_{tide}") for tide in tides]

        # 初始化潮汐模型
        model = Tide(constituents=constituents, amplitudes=amplitudes, phases=phases)

        # 定义预测时间
        # start_time = datetime(point['yy'], point['mm'], point['dd'],
        #                       point['hh'], point['mi'], point['sec'])
        # hours = np.arange(0, point['TSLength']) * point['dt(min)'] // 60
        # times = [start_time + timedelta(hours=int(h)) for h in hours]

        # 计算潮汐时间序列
        predicted_heights = model.at(times)
        results.append(predicted_heights)
    return np.array(results)


if __name__ == '__main__':
    lat_lon_file = "lat_lon"  # 修改为你的实际文件路径
    data = pd.read_csv(lat_lon_file, sep=r'\s+', skiprows=1, header=None,
                       names=['lat', 'lon', 'year', 'month', 'day', 'hour', 'minute', 'second', 'dt', 'TSLength'])
    # 获取所有点的经纬度
    lat_lon_points = [(row['lat'], row['lon']) for _, row in data.iterrows()]

    times = [datetime(2006, 1, 1, 0, 0), datetime(2006, 1, 1, 1, 0), datetime(2006, 1, 1, 2, 0), datetime(2006, 1, 1, 3, 0)]
    predicted_results = predict_tide(points=lat_lon_points, times=times)

    # 写入结果到1.dat文件
    with open('1.dat', 'w') as file:
        # 先写入每个点的潮位预测
        for heights in zip(*predicted_results):  # 转置，使每列对应一个点
            file.write(' '.join(f"{height:>10.4f}" for height in heights) + '\n')

    print("潮位预测完成，结果已保存到2.dat文件。")

