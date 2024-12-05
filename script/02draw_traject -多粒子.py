#!/bin/env python
#coding=utf-8
import os
import numpy as np
import mpl_toolkits.mplot3d
import matplotlib.pyplot as plt
from scipy.io import netcdf_file

# 打开 NetCDF 文件
file_path = 'F:/Desktop/OceanSimulate/static/pltf/lagnc_lagtra.nc'  # 替换为您的文件路径
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
for i in range(0 , 5):
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
coast = np.load('F:/Desktop/OceanSimulate/tempfile/jhhhkkllmnhhuoolmmnbv/coastline.npz')
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
for i in range(0,5):
    ax2d.plot(slon[i], slat[i], '.', label=f'Particle {i+1}')  # 每个粒子的轨迹

ax2d.grid()
ax2d.set_aspect('equal')
#ax2d.set_xlim(xlim)  # 应用x轴范围
#ax2d.set_ylim(ylim)  # 应用y轴范围
ax2d.set_xlabel('Longitude (degrees)')
ax2d.set_ylabel('Latitude (degrees)')
ax2d.set_title('Trajectory of All Particles')
ax2d.legend(loc='upper left', fontsize=8)
plt.savefig('lagtrack/trajectory_2D_all_particles.png')  # 保存2D图像
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
plt.savefig('lagtrack/trajectory_3D_all_particles.png')  # 保存3D图像
#plt.close(fig3d)  # 关闭当前图表，避免图形叠加

plt.show()  # 显示图像
