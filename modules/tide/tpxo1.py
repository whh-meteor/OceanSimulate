import os.path

import pandas as pd
import numpy as np
import xarray as xr
from scipy.interpolate import griddata

# 获取当前文件的绝对路径
current_dir = os.path.dirname(os.path.abspath(__file__))

# 构建 TPXO 文件的完整路径
tpxo_path = os.path.join(current_dir, '..', '..', 'static', 'TPXO.8')
# tpxo_path = os.path.join(current_dir, 'F:\Desktop\【LTGK】海洋一所\240531084643LTX\1开发域-2022\3编码实现\后端\Python-Flask\static\TPXO.8\Clip')

print(tpxo_path)

print(tpxo_path,'tpxo_path')

# NetCDF 文件路径
tpxo_files = {
    'M2': "M2.nc",
    'S2': "S2.nc",
    'K1': "K1.nc",
    'N2': "N2.nc",
    'P1': "P1.nc",
    'O1': "O1.nc",
    'K2': "K2.nc",
    'Q1': "Q1.nc",
    'M4': "M4.nc"
}


def get_tpxo(points):
    '''
    获取调和常数
    :param points:
    :return:
    '''
    # 初始化存储所有点的调和常数
    all_constants = {const: {} for const in tpxo_files}

    # 用户可以选择插值方法
    chosen_method = 'nearest'  # 插值方法可选 'linear', 'nearest', 'cubic'
    fallback_method = 'nearest'  # 备用插值方法

    # 对每个 NetCDF 文件进行插值以提取调和常数
    for const, file in tpxo_files.items():
        all_constants[const] = interpolate_constants_in_range(os.path.join(tpxo_path, file), points, method=chosen_method, fallback_method=fallback_method)

    # 初始化存储调和常数的列表
    output_constants = []

    result = []

    # 整理数据并保存到文件
    for index, (lat, lon) in enumerate(points):
        point_constant = {}
        constants = [f"{lon:.10f}", f"{lat:.10f}"]  # 经度在前，纬度在后
        amplitudes = []
        phases = []
        for const in tpxo_files.keys():
            amplitude, phase = all_constants[const].get(index, (np.nan, np.nan))

            # 如果相位是负值，则加 360 度
            if phase < 0:
                phase += 360
            point_constant[f"{const}_amp"] = f"{amplitude:.6f}"
            point_constant[f"{const}_phase"] = f"{phase:.6f}"
            amplitudes.append(f"{amplitude:.6f}")
            phases.append(f"{phase:.6f}")

        # 放到字典
        result.append(point_constant)

        constants.extend(amplitudes + phases)  # 先振幅后相位
        output_constants.append(constants)

    # 将结果保存到 dat 文件中
    output_file = "../../tempfile/调和常数1.dat"
    header = "lon lat " + " ".join([f"{const}_amp" for const in tpxo_files.keys()]) + " " + " ".join(
        [f"{const}_phase" for const in tpxo_files.keys()])
    np.savetxt(output_file, output_constants, fmt='%s', header=header, comments='')

    print(f"调和常数已成功写入 {output_file} 文件。")
    return result






# 修正后的插值函数
def interpolate_constants_in_range(file, points, method='linear',
                                   fallback_method='nearest'):
    # 提取经度和纬度
    lats, lons = zip(*points)

    # 计算最小值和最大值
    min_lat = min(lats) - 0.5
    max_lat = max(lats) + 0.5
    min_lon = min(lons) - 0.5
    max_lon = max(lons) + 0.5

    constants = {}
    try:
        # 打开 NetCDF 文件并提取子网格
        ds = xr.open_dataset(file)

        # 假设纬度和经度分别是 'lat' 和 'lon'，如有不同需要手动调整
        lat_name, lon_name = 'lat', 'lon'

        lat_tpxo = ds[lat_name].values
        lon_tpxo = ds[lon_name].values

        # 提取在指定范围内的经纬度数据
        lat_mask = (lat_tpxo >= min_lat) & (lat_tpxo <= max_lat)
        lon_mask = (lon_tpxo >= min_lon) & (lon_tpxo <= max_lon)

        lat_tpxo_sub = lat_tpxo[lat_mask]
        lon_tpxo_sub = lon_tpxo[lon_mask]

        if lat_tpxo_sub.size == 0 or lon_tpxo_sub.size == 0:
            raise ValueError(f"子网格提取为空，经纬度范围: [{min_lat}, {max_lat}], [{min_lon}, {max_lon}]")

        # 提取对应区域的振幅和相位数据
        ha_sub = ds['Ha'].values[np.ix_(lat_mask, lon_mask)]
        hg_sub = ds['Hg'].values[np.ix_(lat_mask, lon_mask)]

        # 网格点：使用 np.meshgrid 来生成网格点坐标
        lon_grid, lat_grid = np.meshgrid(lon_tpxo_sub, lat_tpxo_sub)
        points = np.vstack([lat_grid.ravel(), lon_grid.ravel()]).T

        # 对每个点进行插值
        for index, (lat, lon) in enumerate(points):
            amplitude = griddata(points, ha_sub.ravel(), (lat, lon), method=method)
            phase = griddata(points, hg_sub.ravel(), (lat, lon), method=method)

            # 如果线性插值返回 NaN，则使用指定的备用插值方法
            if np.isnan(amplitude) or np.isnan(phase):
                amplitude = griddata(points, ha_sub.ravel(), (lat, lon), method=fallback_method)
                phase = griddata(points, hg_sub.ravel(), (lat, lon), method=fallback_method)

            # 如果仍然是 NaN，填充默认值
            if np.isnan(amplitude) or np.isnan(phase):
                amplitude, phase = 0.0, 0.0  # 填充默认值

            # 如果相位是负值，则加 360 度
            if phase < 0:
                phase += 360

            constants[index] = (amplitude, phase)

    except Exception as e:
        print(f"读取文件 {file} 时出错: {e}")

    return constants


if __name__ == '__main__':
    lat_lon_file = "lat_lon"  # 修改为你的实际文件路径
    data = pd.read_csv(lat_lon_file, sep=r'\s+', skiprows=1, header=None,
                       names=['lat', 'lon', 'year', 'month', 'day', 'hour', 'minute', 'second', 'dt', 'TSLength'])
    # 获取所有点的经纬度
    lat_lon_points = [(row['lat'], row['lon']) for _, row in data.iterrows()]

    get_tpxo(lat_lon_points)

