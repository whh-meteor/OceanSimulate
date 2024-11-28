import numpy as np
import matplotlib.tri as tri
import matplotlib
from xarray import Dataset
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from scipy.io import netcdf_file
import numpy as np   

# -----------------------------
# 绘制拉格朗日粒子追踪函数
# -----------------------------

def lag_script(nc_path,costaline_path,png_path):
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
  i = 0  # 选择第一个粒子

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
  plt.savefig(png_path+'lagtrack/trajectory_2D.png')  # 保存2D图像

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
  plt.savefig(png_path+'lagtrack/trajectory_3D.png')  # 保存3D图像

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
