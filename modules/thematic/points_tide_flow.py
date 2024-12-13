import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from scipy.io import netcdf_file
import os

# -----------------------------
# 点潮位流速绘制函数
# ----------------------------- 
def points_tide_flow(nc_path, png_path, lon_stn=[681870.630, 704213.096, 723780.267, 739805.394, 761503.899, 782302.112], lat_stn=[4230899.155, 4195606.376, 4164818.144, 4269220.307, 4236269.782, 4203486.651], 
                     stn_name=['H1', 'H2', 'H3', 'H4', 'H5', 'H6'] , inds=0, time_interval=(10,20),png_name='points_tide_flow'):
    """
    从 NetCDF 文件中读取数据并为多个观测站点生成潮位、流速时间序列图。
    
    参数：
        nc_path: str, NetCDF 文件路径。
        png_path: str, 图像保存路径。
        lon_stn: list, 观测站点的经度。
        lat_stn: list, 观测站点的纬度。
        stn_name: list, 观测站点的名称。
        inds: int, 起始时间步索引。
        time_interval: tuple, 时间范围 (start, end)，可选，默认为 None。
    """
    # 读取 NetCDF 文件并获取相关变量
    nf = netcdf_file(nc_path, 'r')
    lon = nf.variables['x'][:]  # 经度
    lat = nf.variables['y'][:]  # 纬度
    ua = nf.variables['u'][:]  # 水平流速 u
    va = nf.variables['v'][:]  # 垂直流速 v
    time = nf.variables['time'][:]  # 时间
    zeta = nf.variables['zeta'][:]  # 潮位
    nele = nf.dimensions['nele']  # 网格单元数量
    node = nf.dimensions['node']  # 网格节点数量
    nt = zeta.shape[0]  # 时间步数量
    triangles = nf.variables['nv'][:] - 1  # 网格单元的节点索引（减1转换为从0开始的索引）


    # 观测站点数量
    nstn = len(lon_stn)
    # 设置时间段
    start_time = time_interval[0]  # 起始时间（单位：天，或根据实际数据格式调整）
    end_time = [1]   # 结束时间（单位：天，或根据实际数据格式调整）
        # 获取符合时间段的数据
    time_mask = (time >= start_time) & (time <= end_time)
    time_filtered = time[time_mask]  # 过滤后的时间
    zeta_filtered = zeta[time_mask, :]  # 过滤后的潮位数据
    ua_filtered = ua[time_mask, 0, :]  # 过滤后的u速度
    va_filtered = va[time_mask, 0, :]  # 过滤后的v速度

    # for i in range(nstn):
    #     # 计算距离并找到最近的网格点
    #     dist = (lon - lon_stn[i])**2 + (lat - lat_stn[i])**2
    #     ind = np.argmin(dist)
    #     print(f'Nearest point to {stn_name[i]}: {lon[ind]}, {lat[ind]} (index: {ind})')
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
        elevation = zeta_filtered[:, closest_node]  # 潮位数据
        u = ua_filtered[:, closest_element]  # 水平流速
        v = va_filtered[:, closest_element]  # 垂直流速


        speed = np.sqrt(u**2 + v**2)  # 总流速
        direction = (np.arctan2(v, u) * 180 / np.pi) % 360  # 流向（角度）
            # 创建一个新的绘图窗口
        plt.figure(figsize=(10, 10))

        # 绘制潮位、u速度、v速度、流向随时间的变化
        plt.subplot(2, 2, 1)
        plt.plot(time_filtered, elevation, label=f"Elevation at {stn_name[i]+png_name}")
        plt.title(f"Elevation at {stn_name[i]}")
        plt.xlabel('Time (days)')
        plt.ylabel('Elevation (m)')
        plt.grid(True)

        plt.subplot(2, 2, 2)
        plt.plot(time_filtered, u, label=f"U velocity at {stn_name[i]+png_name}")
        plt.title(f"U velocity at {stn_name[i]}")
        plt.xlabel('Time (days)')
        plt.ylabel('U velocity (m/s)')
        plt.grid(True)

        plt.subplot(2, 2, 3)
        plt.plot(time_filtered, v, label=f"V velocity at {stn_name[i]+png_name}")
        plt.title(f"V velocity at {stn_name[i]}")
        plt.xlabel('Time (days)')
        plt.ylabel('V velocity (m/s)')
        plt.grid(True)

        plt.subplot(2, 2, 4)
        plt.plot(time_filtered, direction, label=f"Direction at {stn_name[i]+png_name}")
        plt.title(f"Direction at {stn_name[i]}")
        plt.xlabel('Time (days)')
        plt.ylabel('Direction (degrees)')
        plt.grid(True)
        # 保存图片到指定路径
        if not os.path.exists(png_path + 'flow_tide'):
            os.makedirs(png_path + 'flow_tide')  # 如果文件夹不存在则创建
        # output_file = os.path.join(png_path,'flow_tide', f"{png_name}_{stn_name[i]}.png")
        output_file = os.path.join(png_path,'flow_tide', f"{png_name}")
        print("04脚本： 点潮位流速生成---" + output_file)
        plt.savefig(output_file, dpi=300)
        # 调整布局
        plt.tight_layout()
     # 关闭 NetCDF 文件
    nf.close()

        # # 创建图形窗口并绘制三个子图
        # plt.figure()

        # # 绘制潮位随时间变化
        # plt.subplot(3, 1, 1)
        # plt.title(stn_name[i])
        # end_idx = time_interval[1] if time_interval else nt
        # plt.plot(time[inds:end_idx], zeta[inds:end_idx, ind], linewidth=0.5)
        # plt.ylabel('Elevation (m)')
        # plt.grid()

        # # 绘制水平流速 ua 随时间变化
        # plt.subplot(3, 1, 2)
        # if ua.ndim == 3 and ind < ua.shape[2]:
        #     plt.plot(time[inds:end_idx], ua[inds:end_idx, 0, ind], linewidth=0.5)
        #     plt.ylabel('u (m/s)')
        #     plt.grid()
        # else:
        #     print(f"Index {ind} is out of bounds for ua with shape {ua.shape}")

        # # 绘制垂直流速 va 随时间变化
        # plt.subplot(3, 1, 3)
        # if va.ndim == 3 and ind < va.shape[2]:
        #     plt.plot(time[inds:end_idx], va[inds:end_idx, 0, ind], linewidth=0.5)
        #     plt.ylabel('v (m/s)')
        #     plt.xlabel('Days')
        #     plt.grid()
        # else:
        #     print(f"Index {ind} is out of bounds for va with shape {va.shape}")

        # # 保存图像到指定路径
        # if not os.path.exists(png_path + 'flow_tide'):
        #     os.makedirs(png_path + 'flow_tide')  # 如果文件夹不存在则创建
        # strfile = os.path.join(png_path, 'flow_tide', f'{stn_name[i]+png_name}.png')
        # plt.savefig(strfile)
        # print(f"04脚本： 点潮位流速生成完成---{strfile}")

    # # 清理资源
    # nf.close()
