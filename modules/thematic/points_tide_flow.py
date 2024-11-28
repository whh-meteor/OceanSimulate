import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from scipy.io import netcdf_file
import numpy as np 

# -----------------------------
# 点潮位流速绘制函数
# ----------------------------- 
def points_tide_flow(nc_path,png_path):
  #从模型输出中提取特定位置的数据。
  #绘制时间序列图表，展示流速和潮位随时间的变化。
  #为特定站点进行流速和潮位的分析和可视化。
  # 读取 NetCDF 文件并获取相关变量
  nf = netcdf_file(nc_path, 'r')  # 打开 NetCDF 文件 'pltf_0002.nc'，以只读模式
  lon = nf.variables['x'][:]  # 读取网格点的经度信息
  lat = nf.variables['y'][:]  # 读取网格点的纬度信息
  ua = nf.variables['u'][:]  # 读取水平流速 u
  va = nf.variables['v'][:]  # 读取垂直流速 v
  time = nf.variables['time'][:]  # 读取时间变量
  zeta = nf.variables['zeta'][:]  # 读取潮位数据
  nele = nf.dimensions['nele']  # 读取网格单元的数量
  node = nf.dimensions['node']  # 读取网格节点的数量
  nt = zeta.shape[0]  # 获取时间步的数量

  # 观测站点的经纬度和名称（可修改为多个点）
  lon_stn = [450000,451000]  # 观测站点的经度
  lat_stn = [4250000,4251000]  # 观测站点的纬度
  stn_name = ['stn1','stn2']  # 观测站点的名称

  print(f"ua shape: {ua.shape}")  # 打印 ua 数据的形状信息，用于调试

  inds = 0  # 时间索引的初始值
  nstn = len(lon_stn)  # 观测站点的数量

  for i in range(nstn):  # 遍历每个观测站点
      # 计算每个观测站点与所有网格点的距离平方
      dist = (lon - lon_stn[i])**2 + (lat - lat_stn[i])**2
      ind = np.argmin(dist)  # 找到距离最近的网格点索引
      print(f'Nearest point to {stn_name[i]}: {lon[ind]}, {lat[ind]} (index: {ind})')  # 打印最近点的经纬度和索引

      # 创建一个图形窗口并绘制三个子图
      plt.figure()
      plt.subplot(3, 1, 1)  # 创建第一个子图
      plt.title(stn_name[i])  # 设置子图标题
      plt.plot(time[inds:], zeta[inds:, ind], linewidth=0.5)  # 绘制潮位随时间变化的曲线
      plt.ylabel('Elevation (m)')  # 设置 y 轴标签
      plt.grid()  # 添加网格线

      plt.subplot(3, 1, 2)  # 创建第二个子图
      # 确保索引有效并访问 ua 的正确维度
      if ua.ndim == 3 and ind < ua.shape[2]:
          plt.plot(time[inds:], ua[inds:, 0, ind], linewidth=0.5)  # 绘制 ua 随时间变化的曲线（假设使用第 0 层）
          plt.ylabel('u (m/s)')  # 设置 y 轴标签
          plt.grid()  # 添加网格线
      else:
          print(f"Index {ind} is out of bounds for ua with shape {ua.shape}")  # 如果索引超出范围，打印警告信息

      plt.subplot(3, 1, 3)  # 创建第三个子图
      # 确保索引有效并访问 va 的正确维度
      if va.ndim == 3 and ind < va.shape[2]:
          plt.plot(time[inds:], va[inds:, 0, ind], linewidth=0.5)  # 绘制 va 随时间变化的曲线（假设使用第 0 层）
          plt.ylabel('v (m/s)')  # 设置 y 轴标签
          plt.xlabel('Days')  # 设置 x 轴标签
          plt.grid()  # 添加网格线
      else:
          print(f"Index {ind} is out of bounds for va with shape {va.shape}")  # 如果索引超出范围，打印警告信息

      strfile = png_path+f'flow_tide/{stn_name[i]}.png'  # 定义保存图像的文件名
      plt.savefig(strfile)  # 保存图像
      print("04脚本： 点潮位流速生成完成---"+strfile)

  # plt.show()  # 显示所有绘制的图像

  # 清理资源
  ua = None
  va = None
  lon = None
  lat = None
  time = None
  zeta = None
  nf.close()  # 关闭 NetCDF 文件
