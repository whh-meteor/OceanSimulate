import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from scipy.io import netcdf_file
import os

# -----------------------------
# 点潮位流速绘制函数
# ----------------------------- 
def points_tide_flow(nc_path, png_path, lon_stn=[450000, 451000], lat_stn=[4250000, 4251000], 
                     stn_name=['stn1', 'stn2'], inds=0, time_interval=None,png_name='points_tide_flow'):
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

    # 观测站点数量
    nstn = len(lon_stn)

    for i in range(nstn):
        # 计算距离并找到最近的网格点
        dist = (lon - lon_stn[i])**2 + (lat - lat_stn[i])**2
        ind = np.argmin(dist)
        print(f'Nearest point to {stn_name[i]}: {lon[ind]}, {lat[ind]} (index: {ind})')

        # 创建图形窗口并绘制三个子图
        plt.figure()

        # 绘制潮位随时间变化
        plt.subplot(3, 1, 1)
        plt.title(stn_name[i])
        end_idx = time_interval[1] if time_interval else nt
        plt.plot(time[inds:end_idx], zeta[inds:end_idx, ind], linewidth=0.5)
        plt.ylabel('Elevation (m)')
        plt.grid()

        # 绘制水平流速 ua 随时间变化
        plt.subplot(3, 1, 2)
        if ua.ndim == 3 and ind < ua.shape[2]:
            plt.plot(time[inds:end_idx], ua[inds:end_idx, 0, ind], linewidth=0.5)
            plt.ylabel('u (m/s)')
            plt.grid()
        else:
            print(f"Index {ind} is out of bounds for ua with shape {ua.shape}")

        # 绘制垂直流速 va 随时间变化
        plt.subplot(3, 1, 3)
        if va.ndim == 3 and ind < va.shape[2]:
            plt.plot(time[inds:end_idx], va[inds:end_idx, 0, ind], linewidth=0.5)
            plt.ylabel('v (m/s)')
            plt.xlabel('Days')
            plt.grid()
        else:
            print(f"Index {ind} is out of bounds for va with shape {va.shape}")

        # 保存图像到指定路径
        if not os.path.exists(png_path + 'flow_tide'):
            os.makedirs(png_path + 'flow_tide')  # 如果文件夹不存在则创建
        strfile = os.path.join(png_path, 'flow_tide', f'{stn_name[i]+png_name}.png')
        plt.savefig(strfile)
        print(f"04脚本： 点潮位流速生成完成---{strfile}")

    # 清理资源
    nf.close()

# # 示例调用
# points_tide_flow(nc_path='path_to_netcdf_file.nc', png_path='path_to_save_png/', 
#                  lon_stn=[450500, 451500], lat_stn=[4250500, 4252000], 
#                  stn_name=['station1', 'station2'], time_interval=(0, 100))
# import numpy as np
# import matplotlib
# matplotlib.use('Agg')
# from matplotlib import pyplot as plt
# from scipy.io import netcdf_file
# import numpy as np 

# # -----------------------------
# # 点潮位流速绘制函数
# # ----------------------------- 
# def points_tide_flow(nc_path,png_path):
#   #从模型输出中提取特定位置的数据。
#   #绘制时间序列图表，展示流速和潮位随时间的变化。
#   #为特定站点进行流速和潮位的分析和可视化。
#   # 读取 NetCDF 文件并获取相关变量
#   nf = netcdf_file(nc_path, 'r')  # 打开 NetCDF 文件 'pltf_0002.nc'，以只读模式
#   lon = nf.variables['x'][:]  # 读取网格点的经度信息
#   lat = nf.variables['y'][:]  # 读取网格点的纬度信息
#   ua = nf.variables['u'][:]  # 读取水平流速 u
#   va = nf.variables['v'][:]  # 读取垂直流速 v
#   time = nf.variables['time'][:]  # 读取时间变量
#   zeta = nf.variables['zeta'][:]  # 读取潮位数据
#   nele = nf.dimensions['nele']  # 读取网格单元的数量
#   node = nf.dimensions['node']  # 读取网格节点的数量
#   nt = zeta.shape[0]  # 获取时间步的数量

#   # 观测站点的经纬度和名称（可修改为多个点）
#   lon_stn = [450000,451000]  # 观测站点的经度
#   lat_stn = [4250000,4251000]  # 观测站点的纬度
#   stn_name = ['stn1','stn2']  # 观测站点的名称

#   print(f"ua shape: {ua.shape}")  # 打印 ua 数据的形状信息，用于调试

#   inds = 0  # 时间索引的初始值
#   nstn = len(lon_stn)  # 观测站点的数量

#   for i in range(nstn):  # 遍历每个观测站点
#       # 计算每个观测站点与所有网格点的距离平方
#       dist = (lon - lon_stn[i])**2 + (lat - lat_stn[i])**2
#       ind = np.argmin(dist)  # 找到距离最近的网格点索引
#       print(f'Nearest point to {stn_name[i]}: {lon[ind]}, {lat[ind]} (index: {ind})')  # 打印最近点的经纬度和索引

#       # 创建一个图形窗口并绘制三个子图
#       plt.figure()
#       plt.subplot(3, 1, 1)  # 创建第一个子图
#       plt.title(stn_name[i])  # 设置子图标题
#       plt.plot(time[inds:], zeta[inds:, ind], linewidth=0.5)  # 绘制潮位随时间变化的曲线
#       plt.ylabel('Elevation (m)')  # 设置 y 轴标签
#       plt.grid()  # 添加网格线

#       plt.subplot(3, 1, 2)  # 创建第二个子图
#       # 确保索引有效并访问 ua 的正确维度
#       if ua.ndim == 3 and ind < ua.shape[2]:
#           plt.plot(time[inds:], ua[inds:, 0, ind], linewidth=0.5)  # 绘制 ua 随时间变化的曲线（假设使用第 0 层）
#           plt.ylabel('u (m/s)')  # 设置 y 轴标签
#           plt.grid()  # 添加网格线
#       else:
#           print(f"Index {ind} is out of bounds for ua with shape {ua.shape}")  # 如果索引超出范围，打印警告信息

#       plt.subplot(3, 1, 3)  # 创建第三个子图
#       # 确保索引有效并访问 va 的正确维度
#       if va.ndim == 3 and ind < va.shape[2]:
#           plt.plot(time[inds:], va[inds:, 0, ind], linewidth=0.5)  # 绘制 va 随时间变化的曲线（假设使用第 0 层）
#           plt.ylabel('v (m/s)')  # 设置 y 轴标签
#           plt.xlabel('Days')  # 设置 x 轴标签
#           plt.grid()  # 添加网格线
#       else:
#           print(f"Index {ind} is out of bounds for va with shape {va.shape}")  # 如果索引超出范围，打印警告信息

#       strfile = png_path+f'flow_tide/{stn_name[i]}.png'  # 定义保存图像的文件名
#       plt.savefig(strfile)  # 保存图像
#       print("04脚本： 点潮位流速生成完成---"+strfile)

#   # plt.show()  # 显示所有绘制的图像

#   # 清理资源
#   ua = None
#   va = None
#   lon = None
#   lat = None
#   time = None
#   zeta = None
#   nf.close()  # 关闭 NetCDF 文件
