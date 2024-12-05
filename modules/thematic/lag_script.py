import numpy as np
import matplotlib.tri as tri
import matplotlib
from xarray import Dataset
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from scipy.io import netcdf_file
import numpy as np   
import os
# -----------------------------
# 绘制拉格朗日粒子追踪函数v3  自选点
# -----------------------------
def lag_script_v3(nc_path,costaline_path,png_path,lag_index=[0, 50, 100]  ,png_name='lagtrack'):

    # 打开 NetCDF 文件
    file_path =  nc_path # 替换为您的文件路径
    nf = netcdf_file(file_path, 'r', mmap=False)

    # 读取变量
    lon = nf.variables['x'][:]
    lat = nf.variables['y'][:]
    z = nf.variables['z'][:]
    time = nf.variables['time'][:]
    nlag = nf.dimensions['nlag']
    nt = time.shape[0]
    nf.close()

    # 去掉重复的经度和纬度
    sz = []
    slon = []
    slat = []
    stime = []
    for i in range(nlag):
        tmp = (lon[:, i] - lon[0, i]) ** 2 + (lat[:, i] - lat[0, i]) ** 2
        tind = np.nonzero(np.diff(tmp))
        indfirst = 0
        indlast = 0
        if len(tind[0]) > 0:
            indfirst = max(0, tind[0][0] - 1)  # 确保索引不为负数
            indlast = min(len(lon[:, i]) - 1, tind[0][-1] + 1)  # 确保索引不超出数组长度
        sz.append(z[indfirst:indlast + 1, i])
        slon.append(lon[indfirst:indlast + 1, i])
        slat.append(lat[indfirst:indlast + 1, i])
        stime.append(time[indfirst:indlast + 1])

    # 读取岸线数据
    coast = np.load(costaline_path)
    coastx = coast['coastx']
    coasty = coast['coasty']

    # 创建lagtrack目录
    if not os.path.isdir('lagtrack'):
        os.mkdir('lagtrack')

        # 选择多个粒子
    particles = lag_index # 选择粒子索引，可以修改为所需的多个粒子索引

    # 计算所有粒子的轨迹范围
    min_lon = min([min(slon[i]) for i in particles])  # 所有粒子的最小经度
    max_lon = max([max(slon[i]) for i in particles])  # 所有粒子的最大经度
    min_lat = min([min(slat[i]) for i in particles])  # 所有粒子的最小纬度
    max_lat = max([max(slat[i]) for i in particles])  # 所有粒子的最大纬度

    # 设置坐标轴范围
    xlim = [min_lon-100, max_lon+100]  # 根据所有粒子的经度范围设置x轴
    ylim = [min_lat-100, max_lat+100]  # 根据所有粒子的纬度范围设置y轴

    # 绘制2D图
    fig2d = plt.figure()
    ax2d = plt.subplot(111)
    ax2d.plot(coastx, coasty, 'k', label='Coastline')  # 绘制岸线

    # 绘制多个粒子的轨迹
    for i in particles:
        ax2d.plot(slon[i], slat[i], '.-', label=f'Trajectory of Particle({i+1})')  # 绘制粒子的轨迹
        ax2d.plot(slon[i][0:1], slat[i][0:1], 'ro')  # 标记起始点

    ax2d.grid()
    ax2d.set_aspect('equal')
    ax2d.set_xlim(xlim)  # 应用x轴范围
    ax2d.set_ylim(ylim)  # 应用y轴范围
    ax2d.set_xlabel('Longitude (degrees)')
    ax2d.set_ylabel('Latitude (degrees)')
    ax2d.set_title('Trajectories of Multiple Particles')
    ax2d.legend()
    plt.savefig(png_path+f'lagtrack/{png_name}_2D.png')  # 保存2D图像图像

    # 绘制3D图
    fig3d = plt.figure()
    ax3d = plt.subplot(111, projection='3d')

    # 绘制多个粒子的3D轨迹
    for i in particles:
        ax3d.plot(slon[i], slat[i], sz[i], '.-', label=f'3D Trajectory of Particle({i+1})')  # 绘制粒子的3D轨迹
        ax3d.plot(slon[i][0:1], slat[i][0:1], sz[i][0:1], 'ro')  # 标记起始点

    ax3d.set_aspect('auto')  # 使用'auto'以避免3D视图中的异常
    ax3d.set_xlabel('Longitude (degrees)')
    ax3d.set_ylabel('Latitude (degrees)')
    ax3d.set_zlabel('Depth (m)')
    ax3d.set_title('3D Trajectories of Multiple Particles')
    ax3d.legend()
    plt.savefig(png_path+f'lagtrack/{png_name}_3D.png')  # 保存3D图像图像

    plt.show()  # 显示图像

    # 清理变量和关闭文件
    sz = None
    slon = None
    slat = None
    stime = None
    coast = None
    coastx = None
    coasty = None
    nf = None

# -----------------------------
# 绘制拉格朗日粒子追踪函数v2 多粒子
# -----------------------------
def lag_script_v2(nc_path,costaline_path,png_path,lag_index=(0 , 5) ,png_name='lagtrack'):
    nf = netcdf_file(nc_path, 'r', mmap=False)

    # 读取变量
    lon = nf.variables['x'][:]
    lat = nf.variables['y'][:]
    z = nf.variables['z'][:]
    time = nf.variables['time'][:]
    nlag = nf.dimensions['nlag']
    nt = time.shape[0]
    nf.close()

    # 去掉重复的经度和纬度
    sz = []
    slon = []
    slat = []
    stime = []
    
    for i in lag_index:
        tmp = (lon[:, i] - lon[0, i]) ** 2 + (lat[:, i] - lat[0, i]) ** 2
        tind = np.nonzero(np.diff(tmp))
        indfirst = 0
        indlast = 0
        if len(tind[0]) > 0:
            indfirst = max(0, tind[0][0] - 1)  # 确保索引不为负数
            indlast = min(len(lon[:, i]) - 1, tind[0][-1] + 1)  # 确保索引不超出数组长度
        sz.append(z[indfirst:indlast + 1, i])
        slon.append(lon[indfirst:indlast + 1, i])
        slat.append(lat[indfirst:indlast + 1, i])
    stime.append(time[indfirst:indlast + 1])

    # 读取岸线数据
    coast = np.load(costaline_path)
    coastx = coast['coastx']
    coasty = coast['coasty']

    # 创建lagtrack目录
    if not os.path.isdir('lagtrack'):
        os.mkdir('lagtrack')

    # 设定坐标轴范围
    #xlim = [min([min(slon[i]) for i in range(0,5)]), max([max(slon[i]) for i in range(0,5)])]  # 设置x轴范围
    #ylim = [min([min(slat[i]) for i in range(0,5)]), max([max(slat[i]) for i in range(0,5)])]  # 设置y轴范围

    # 绘制2D图
    fig2d = plt.figure()
    ax2d = plt.subplot(111)
    ax2d.plot(coastx, coasty, 'k', label='Coastline')  # 绘制岸线

    # 在2D图上绘制所有粒子的轨迹
    for i in lag_index:
        ax2d.plot(slon[i], slat[i], '.', label=f'Particle {i+1}')  # 每个粒子的轨迹

    ax2d.grid()
    ax2d.set_aspect('equal')
    #ax2d.set_xlim(xlim)  # 应用x轴范围
    #ax2d.set_ylim(ylim)  # 应用y轴范围
    ax2d.set_xlabel('Longitude (degrees)')
    ax2d.set_ylabel('Latitude (degrees)')
    ax2d.set_title('Trajectory of All Particles')
    ax2d.legend(loc='upper left', fontsize=8)
    plt.savefig(png_path+f'lagtrack/{png_name}_2D.png')  # 保存2D图像
    #plt.close(fig2d)  # 关闭当前图表，避免图形叠加

    # 绘制3D图
    fig3d = plt.figure()
    ax3d = fig3d.add_subplot(111, projection='3d')

    # 在3D图上绘制所有粒子的轨迹
    for i in range(0,5):
        ax3d.plot(slon[i], slat[i], sz[i], '.', label=f'Particle {i+1}')  # 每个粒子的轨迹

    ax3d.set_aspect('auto')  # 使用'auto'以避免3D视图中的异常
    ax3d.set_xlabel('Longitude (degrees)')
    ax3d.set_ylabel('Latitude (degrees)')
    ax3d.set_zlabel('Depth (m)')
    ax3d.set_title('3D Trajectory of All Particles')
    ax3d.legend(loc='upper left', fontsize=8)
    plt.savefig(png_path+f'lagtrack/{png_name}_3D.png')  # 保存3D图像

# -----------------------------
# 绘制拉格朗日粒子追踪函数v1
# -----------------------------

def lag_script(nc_path,costaline_path,png_path,lag_index=0,png_name='lagtrack'):
    # 打开 NetCDF 文件
  file_path = nc_path  # 替换为您的文件路径
  nf = netcdf_file(file_path, 'r', mmap=False)

  # 读取变量
  lon = nf.variables['x'][:]
  lat = nf.variables['y'][:]
  z = nf.variables['z'][:]
  time = nf.variables['time'][:]
  nlag = nf.dimensions['nlag']
  nt = time.shape[0]
  nf.close()

  # 去掉重复的经度和纬度
  sz = []
  slon = []
  slat = []
  stime = []
  for i in range(nlag):
      tmp = (lon[:, i] - lon[0, i]) ** 2 + (lat[:, i] - lat[0, i]) ** 2
      tind = np.nonzero(np.diff(tmp))
      indfirst = 0
      indlast = 0
      if len(tind[0]) > 0:
          indfirst = max(0, tind[0][0] - 1)  # 确保索引不为负数
          indlast = min(len(lon[:, i]) - 1, tind[0][-1] + 1)  # 确保索引不超出数组长度
      sz.append(z[indfirst:indlast + 1, i])
      slon.append(lon[indfirst:indlast + 1, i])
      slat.append(lat[indfirst:indlast + 1, i])
      stime.append(time[indfirst:indlast + 1])

  # 读取岸线数据
  coast = np.load(costaline_path)
  coastx = coast['coastx']
  coasty = coast['coasty']

  # 创建lagtrack目录
  # if not os.path.isdir('lagtrack'):
  #     os.mkdir('lagtrack')

  # 选择第一个粒子的轨迹
  i = lag_index  # 选择第一个粒子

  # 设定坐标轴范围
  xlim = [min(slon[i]), max(slon[i])]  # 设置x轴范围
  ylim = [min(slat[i]), max(slat[i])]  # 设置y轴范围

  # 绘制2D图
  fig2d = plt.figure()
  ax2d = plt.subplot(111)
  ax2d.plot(coastx, coasty, 'k', label='Coastline')  # 绘制岸线
  ax2d.plot(slon[i], slat[i], '.-', label='Trajectory')  # 绘制粒子的轨迹
  ax2d.plot(slon[i][0:1], slat[i][0:1], 'ro', label='Start Point')  # 标记起始点
  ax2d.grid()
  ax2d.set_aspect('equal')
  ax2d.set_xlim(xlim)  # 应用x轴范围
  ax2d.set_ylim(ylim)  # 应用y轴范围
  ax2d.set_xlabel('Longitude (degrees)')
  ax2d.set_ylabel('Latitude (degrees)')
  ax2d.set_title('Trajectory of Particle 1')
  ax2d.legend()
  plt.savefig(png_path+f'lagtrack/{png_name}_2D.png')  # 保存2D图像

  # 绘制3D图
  fig3d = plt.figure()
  ax3d = plt.subplot(111, projection='3d')
  ax3d.plot(slon[i], slat[i], sz[i], '.-', label='3D Trajectory')  # 绘制粒子的3D轨迹
  ax3d.plot(slon[i][0:1], slat[i][0:1], sz[i][0:1], 'ro', label='Start Point')  # 标记起始点
  ax3d.set_aspect('auto')  # 使用'auto'以避免3D视图中的异常
  ax3d.set_xlabel('Longitude (degrees)')
  ax3d.set_ylabel('Latitude (degrees)')
  ax3d.set_zlabel('Depth (m)')
  ax3d.set_title('3D Trajectory of Particle 1')
  ax3d.legend()
  plt.savefig(png_path+f'lagtrack/{png_name}_3D.png')  # 保存3D图像

  # plt.show()  # 显示图像

  # 清理变量和关闭文件
  sz = None
  slon = None
  slat = None
  stime = None
  coast = None
  coastx = None
  coasty = None
  nf = None
