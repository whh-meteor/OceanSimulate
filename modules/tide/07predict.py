import numpy as np
from datetime import datetime, timedelta
import constituent
from tide import Tide

# 读取调和常数数据
def read_harmonic_constants(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()[1:]  # 跳过第一行
    harmonic_constants = []
    for line in lines:
        values = line.split()
        harmonic_constants.append({
            'lon': float(values[0]),
            'lat': float(values[1]),
            'M2_amp': float(values[2]), 'S2_amp': float(values[3]), 
            'K1_amp': float(values[4]), 'N2_amp': float(values[5]),
            'P1_amp': float(values[6]), 'O1_amp': float(values[7]), 
            'K2_amp': float(values[8]), 'Q1_amp': float(values[9]), 
            'M4_amp': float(values[10]),
            'M2_phase': float(values[11]), 'S2_phase': float(values[12]), 
            'K1_phase': float(values[13]), 'N2_phase': float(values[14]), 
            'P1_phase': float(values[15]), 'O1_phase': float(values[16]), 
            'K2_phase': float(values[17]), 'Q1_phase': float(values[18]), 
            'M4_phase': float(values[19]),
        })
    return harmonic_constants

# 读取点数据
def read_points(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()[1:]  # 跳过第一行
    points = []
    for line in lines:
        values = line.split()
        points.append({
            'lat': float(values[0]),
            'lon': float(values[1]),
            'yy': int(values[2]),
            'mm': int(values[3]),
            'dd': int(values[4]),
            'hh': int(values[5]),
            'mi': int(values[6]),
            'sec': int(values[7]),
            'dt(min)': int(values[8]),
            'TSLength': int(values[9]),
        })
    return points

# 预测潮位
def predict_tide(harmonic_constants, points):
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
        start_time = datetime(point['yy'], point['mm'], point['dd'],
                              point['hh'], point['mi'], point['sec'])
        hours = np.arange(0, point['TSLength']) * point['dt(min)'] // 60
        times = [start_time + timedelta(hours=int(h)) for h in hours]

        # 计算潮汐时间序列
        predicted_heights = model.at(times)
        results.append(predicted_heights)

    return results

# 主程序
harmonic_constants = read_harmonic_constants('调和常数.dat')
points = read_points('lat_lon')

predicted_results = predict_tide(harmonic_constants, points)

# 写入结果到1.dat文件
with open('1.dat', 'w') as file:
    # 先写入每个点的潮位预测
    for heights in zip(*predicted_results):  # 转置，使每列对应一个点
        file.write(' '.join(f"{height:>10.4f}" for height in heights) + '\n')

print("潮位预测完成，结果已保存到1.dat文件。")
