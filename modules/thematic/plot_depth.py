import numpy as np
import matplotlib.tri as tri
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from scipy.io import netcdf_file
import numpy as np

# -----------------------------
# 绘制网格水深函数
# ----------------------------- 
def plot_depth(nc_path, costaline_path, png_path, tri_linewidth=0.3, lon_min=None, lon_max=None, lat_min=None, lat_max=None, dpi=300,png_name='griddepth'):
    """
    绘制网格和水深图，并保存为 PNG 文件。

    :param nc_path: NetCDF 文件路径
    :param costaline_path: 岸线数据文件路径 (.npz 格式)
    :param png_path: 保存图像的路径
    :param lon_min: 经度最小值（可选，默认 None）
    :param lon_max: 经度最大值（可选，默认 None）
    :param lat_min: 纬度最小值（可选，默认 None）
    :param lat_max: 纬度最大值（可选，默认 None）
    :param dpi: 输出图像的分辨率（默认为 300）
    """
    nf = netcdf_file(nc_path, 'r', mmap=True)
    lonc = nf.variables['xc'][:]  # 读取网格中心点的经度
    latc = nf.variables['yc'][:]  # 读取网格中心点的纬度
    lon = nf.variables['x'][:]
    lat = nf.variables['y'][:]
    nv = nf.variables['nv'][:]
    h  = nf.variables['h'][:]
    nele = nf.dimensions['nele']
    node = nf.dimensions['node']

    triang = tri.Triangulation(lon,lat,nv.transpose()-1)
    xlim = [lonc.min(), lonc.max()]  # 设置 x 轴范围
    ylim = [latc.min(), latc.max()]  # 设置 y 轴范围
    # 读取岸线数据
    coastline = np.load(costaline_path)
    coastx = coastline['coastx']
    coasty = coastline['coasty']

    fig1 = plt.figure()
    plt.triplot(triang, color='k', linewidth=tri_linewidth)
    ax = plt.gca()
    ax.set_aspect('equal')
    plt.xlabel('Longitude (m)')
    plt.ylabel('Latitude (m)')
    plt.title('grid')
 

    fig2 = plt.figure()
    #plt.triplot(triang, color='k', linewidth=0.3)
    plt.tripcolor(triang, h, )
    plt.plot(coastx, coasty, color='k')


    ax = plt.gca()
    ax.set_aspect('equal')

    # 设置坐标轴范围
    if lon_min is not None and lon_max is not None and lat_min is not None and lat_max is not None:
        ax.set_xlim(lon_min, lon_max)
        ax.set_ylim(lat_min, lat_max)
    else:
        ax.set_xlim(xlim[0], xlim[1])
        ax.set_ylim(ylim[0], ylim[1])

    plt.xlabel('Longitude (m)')
    plt.ylabel('Latitude (m)')
    plt.colorbar()
    plt.title('depth (m)')
 

    plt.savefig(png_path+'/griddepth/'+png_name+'.png',dpi=dpi)

    # plt.show()

    h = None
    lon = None
    lat = None
    nv = None
    nf.close()
