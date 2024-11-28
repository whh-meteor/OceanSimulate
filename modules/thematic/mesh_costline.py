
import numpy as np
import matplotlib.tri as tri
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from scipy.io import netcdf_file
import numpy as np  

from modules.thematic.common import *
# -----------------------------
# 解析nc数据，提取岸线和网格函数
# -----------------------------
def mesh_costline(filepath, costline_path, png_path,tri_linewidth=0.05,costa_linewidth=1.0,lon_min=None, lon_max=None, lat_min=None, lat_max=None, dpi=300):
    """
    解析 NetCDF 数据，提取岸线和网格，并生成三角网格图形。

    :param filepath: NetCDF 文件路径
    :param costline_path: 保存岸线数据的路径 (.npz 格式)
    :param png_path: 保存图片的路径
    :param tri_linewidth: 网格线宽度（默认 0.05）
    :param costa_linewidth: 岸线宽度（默认 1.0）
    :param lon_min: 经度最小值（可选，默认 None）
    :param lon_max: 经度最大值（可选，默认 None）
    :param lat_min: 纬度最小值（可选，默认 None）
    :param lat_max: 纬度最大值（可选，默认 None）
    :param dpi: 输出图像的分辨率（默认为 300）
    :param xlim: 经度范围（可选，默认为 None）
    :param ylim: 纬度范围（可选，默认为 None）
    """
  
    # 打开 NetCDF 文件并读取变量
    nf = netcdf_file(filepath, 'r', mmap=True)
    lonc = nf.variables['xc'][:]  # 读取网格中心点的经度
    latc = nf.variables['yc'][:]  # 读取网格中心点的纬度
    lon = nf.variables['x'][:]
    lat = nf.variables['y'][:]
    nv = nf.variables['nv'][:]
    h = nf.variables['h'][:]
    nele = nf.dimensions['nele']
    node = nf.dimensions['node']
    
    xlim = [lonc.min(), lonc.max()]  # 设置 x 轴范围
    ylim = [latc.min(), latc.max()]  # 设置 y 轴范围

    # 获取岸线数据
    nvp = nv.transpose() - 1
    coastx, coasty = get_coastline(lon, lat, nvp)
    np.savez(costline_path, coastx=coastx, coasty=coasty)

    # 创建图形
    fig = plt.figure()
    triang = tri.Triangulation(lon, lat, nvp)
    
    # 绘制三角网格和岸线
    plt.triplot(triang, color='k', linewidth=tri_linewidth)
    plt.plot(coastx, coasty, color='b', linewidth=costa_linewidth)
    
    # 获取坐标轴对象
    ax = plt.gca()
    ax.set_aspect('equal')
    
    # 设置轴标签
    plt.xlabel('Longitude (m)')
    plt.ylabel('Latitude (m)')

    # 设置坐标轴范围
    if lon_min is not None and lon_max is not None and lat_min is not None and lat_max is not None:
        ax.set_xlim(lon_min, lon_max)
        ax.set_ylim(lat_min, lat_max)
    elif xlim is not None and ylim is not None:
        ax.set_xlim(xlim[0], xlim[1])
        ax.set_ylim(ylim[0], ylim[1])

    # 保存图像为 PNG 文件
    plt.savefig(png_path + '/mesh_coastline/grid_coastline.png', format='png', dpi=dpi, bbox_inches='tight')
    
    # 关闭文件和清理变量
    nf.close()
 
    
    lon = None
    lat = None
    nv = None
    h = None
    nf.close()
    print("01脚本：coastline.npz岸线提取完成")
