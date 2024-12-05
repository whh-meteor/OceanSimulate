import numpy as np
import matplotlib.pyplot as plt
from scipy.io import netcdf_file

# 打开 NetCDF 文件并读取变量
nf = netcdf_file('F:/Desktop/OceanSimulate/static/pltf/pltf_0002.nc', 'r')
lon = nf.variables['x'][:]  # 节点经度
lat = nf.variables['y'][:]  # 节点纬度
ua = nf.variables['u'][:]  # 水平流速 u，维度为 (time, siglay, nele)
va = nf.variables['v'][:]  # 垂直流速 v，维度为 (time, siglay, nele)
time = nf.variables['time'][:]  # 时间
zeta = nf.variables['zeta'][:]  # 潮位，维度为 (time, node)
triangles = nf.variables['nv'][:] - 1  # 网格单元的节点索引（减1转换为从0开始的索引）

nt = zeta.shape[0]  # 时间步数

# 创建一个函数来返回观测站点的经纬度和名称
def get_station_data():
    lon_stn = [681870.630, 704213.096, 723780.267, 739805.394, 761503.899, 782302.112]  # 观测站点经度
    lat_stn = [4230899.155, 4195606.376, 4164818.144, 4269220.307, 4236269.782, 4203486.651]  # 观测站点纬度
    stn_name = ['H1', 'H2', 'H3', 'H4', 'H5', 'H6']  # 观测站点名称
    return lon_stn, lat_stn, stn_name

# 从函数中获取观测站点数据
lon_stn, lat_stn, stn_name = get_station_data()

# 遍历每个观测站点，创建每个站点的单独图
for i in range(len(lon_stn)):
    # 找到距离站点最近的节点
    dist_node = (lon - lon_stn[i])**2 + (lat - lat_stn[i])**2
    closest_node = np.argmin(dist_node)  # 最近的节点索引

    # 找到包含站点的三角形网格
    element_found = False
    for ele_index, triangle in enumerate(triangles.T):
        x1, y1 = lon[triangle[0]], lat[triangle[0]]
        x2, y2 = lon[triangle[1]], lat[triangle[1]]
        x3, y3 = lon[triangle[2]], lat[triangle[2]]

        # 使用重心法检查点是否在三角形内
        denom = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        a = ((y2 - y3) * (lon_stn[i] - x3) + (x3 - x2) * (lat_stn[i] - y3)) / denom
        b = ((y3 - y1) * (lon_stn[i] - x3) + (x1 - x3) * (lat_stn[i] - y3)) / denom
        c = 1 - a - b

        if 0 <= a <= 1 and 0 <= b <= 1 and 0 <= c <= 1:
            closest_element = ele_index
            element_found = True
            break

    if not element_found:
        print(f"Warning: Station {stn_name[i]} is not inside any element. Skipping.")
        continue

    # 计算网格单元的中心坐标
    x1, y1 = lon[triangles[0, closest_element]], lat[triangles[0, closest_element]]
    x2, y2 = lon[triangles[1, closest_element]], lat[triangles[1, closest_element]]
    x3, y3 = lon[triangles[2, closest_element]], lat[triangles[2, closest_element]]

    # 计算三角形网格的中心（几何中心）
    center_lon = (x1 + x2 + x3) / 3
    center_lat = (y1 + y2 + y3) / 3

    # 提取该站点的潮位、流速和流向数据
    elevation = zeta[:, closest_node]  # 潮位数据
    u = ua[:, 0, closest_element]  # 水平流速
    v = va[:, 0, closest_element]  # 垂直流速

    speed = np.sqrt(u**2 + v**2)  # 总流速
    direction = (np.arctan2(v, u) * 180 / np.pi) % 360  # 流向（角度）

    # 创建一个新的绘图窗口
    plt.figure(figsize=(10, 8))

    # 绘制潮位、u速度、v速度、流向随时间的变化
    plt.subplot(2, 2, 1)
    plt.plot(time, elevation, label=f"Elevation at {stn_name[i]}")
    plt.title(f"Elevation at {stn_name[i]}")
    plt.xlabel('Time (days)')
    plt.ylabel('Elevation (m)')
    plt.grid(True)

    plt.subplot(2, 2, 2)
    plt.plot(time, u, label=f"U velocity at {stn_name[i]}")
    plt.title(f"U velocity at {stn_name[i]}")
    plt.xlabel('Time (days)')
    plt.ylabel('U velocity (m/s)')
    plt.grid(True)

    plt.subplot(2, 2, 3)
    plt.plot(time, v, label=f"V velocity at {stn_name[i]}")
    plt.title(f"V velocity at {stn_name[i]}")
    plt.xlabel('Time (days)')
    plt.ylabel('V velocity (m/s)')
    plt.grid(True)

    plt.subplot(2, 2, 4)
    plt.plot(time, direction, label=f"Direction at {stn_name[i]}")
    plt.title(f"Direction at {stn_name[i]}")
    plt.xlabel('Time (days)')
    plt.ylabel('Direction (degrees)')
    plt.grid(True)

    # 调整布局
    plt.tight_layout()

    # 显示每个站点的图
    plt.show()
