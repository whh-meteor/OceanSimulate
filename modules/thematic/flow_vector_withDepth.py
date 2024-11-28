import os
import numpy as np
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
from scipy.io import netcdf_file
from matplotlib.ticker import MaxNLocator
import matplotlib.tri as tri
# -----------------------------
# 绘制流场矢量图（含水深）函数
# -----------------------------
def flow_vector_withDepth(nc_path, costline_path, png_path, inter=10, time_range=None,siglay_step = 0, speed=2, scale=20, width=0.002, 
                        quiverkey_pos=(0.12, -0.1), compass_pos=(0.95, 0.95), title_prefix="Flow Vector", dpi=300, 
                        coast_color='black', coast_linewidth=1, quiver_color='black',lon_min=None, lon_max=None, lat_min=None, lat_max=None):
    """
    绘制流场矢量图，并保存为 PNG 文件。

    :param nc_path: NetCDF 文件路径
    :param costline_path: 岸线数据路径（.npz 格式）
    :param png_path: 保存图片的目录
    :param inter: 采样间隔（默认为10）
    :param time_range: 时间步长范围，形如 (start, end)，默认为最后5个时间步
    :param speed: 流速（默认值为2）
    :param scale: 矢量图标定的比例尺（默认值为20）
    :param width: 矢量的线宽（默认值为0.002）
    :param quiverkey_pos: 流速比例尺的位置，默认为 (0.12, -0.1)
    :param compass_pos: 指北针的位置，默认为 (0.95, 0.95)
    :param title_prefix: 图表标题前缀，默认为 "Flow Vector"
    :param dpi: 保存图片的分辨率，默认为 300
    :param coast_color: 岸线的颜色，默认为 'black'
    :param coast_linewidth: 岸线的线宽，默认为 1
    :param quiver_color: 矢量图的颜色，默认为 'black'
    """
    
    # 打开 NetCDF 文件并读取变量
    nf = netcdf_file(nc_path, 'r', mmap=True)
    lonc = nf.variables['xc'][:]  # 读取网格中心点的经度
    latc = nf.variables['yc'][:]  # 读取网格中心点的纬度
    lon = nf.variables['x'][:]  # 网格点经度
    lat = nf.variables['y'][:]  # 网格点纬度
    nv = nf.variables['nv'][:]  # 读取网格连接信息
    ua = nf.variables['u'][:]  # 读取 u 方向速度分量
    va = nf.variables['v'][:]  # 读取 v 方向速度分量
    nele = nf.dimensions['nele']  # 网格单元数
    node = nf.dimensions['node']  # 网格节点数
    nt = ua.shape[0]  # 时间步长数
    h = nf.variables['h'][:]  # 水深数据

    # 加载岸线数据
    coastline = np.load(costline_path)  # 从文件中加载岸线数据
    coastx = coastline['coastx']
    coasty = coastline['coasty']
    triang = tri.Triangulation(lon, lat, nv.transpose() - 1)
    # 设置时间范围，如果没有指定则默认取最后5个时间步
    if time_range is None:
        time_range = (nt - 5, nt)
    
    # 设定经纬度的采样间隔
    tlon = lonc[siglay_step::inter]  # 抽取经度点
    tlat = latc[siglay_step::inter]  # 抽取纬度点
    xlim = [lonc.min(), lonc.max()]  # 设置 x 轴范围
    ylim = [latc.min(), latc.max()]  # 设置 y 轴范围

    # 创建输出目录
    if not os.path.exists(png_path):
        os.makedirs(png_path)

    # 遍历指定的时间步长范围
    for tind in range(*time_range):  # 使用指定的时间范围
        print(f"Processing time step {tind}")

        plt.figure()  # 创建新的图形
        ax = plt.gca()  # 获取当前坐标轴

        # 绘制水深颜色图
        plt.tripcolor(triang, h)  # 绘制水深颜色图
        # 选择指定时间步的数据并按间隔采样
        tua = ua[tind, siglay_step, :][siglay_step::inter]  # 选择 u 方向速度
        tva = va[tind, siglay_step, :][siglay_step::inter]  # 选择 v 方向速度

        # 确保 tua 和 tva 的大小与 tlon 和 tlat 匹配
        tua = tua[:len(tlon)]
        tva = tva[:len(tlat)]

        # 打印检查大小
        print(f"tlon size: {len(tlon)}, tlat size: {len(tlat)}")
        print(f"tua size: {len(tua)}, tva size: {len(tva)}")

        # 添加指北针
        plt.text(compass_pos[0], compass_pos[1], 'N', fontsize=12, ha='center', transform=ax.transAxes)
        plt.arrow(compass_pos[0], compass_pos[1] - 0.07, 0, 0.05, head_width=0.02, head_length=0.02, fc='k', ec='k', transform=ax.transAxes)

        # 绘制流场矢量图
        plt.quiver(tlon, tlat, tua, tva, scale=scale, width=width, color=quiver_color)
        
        # 添加流速比例尺
        plt.quiverkey(plt.quiver(tlon, tlat, tua, tva, scale=scale, width=width), *quiverkey_pos, speed, f'{speed:.2f} m/s', labelpos='E', coordinates='axes')

        # 绘制岸线
        plt.plot(coastx, coasty, color=coast_color, linewidth=coast_linewidth)

        # 设置图形属性
        ax.set_aspect('equal')
        # 如果lon_min, lon_max, lat_min, lat_max都有值，则设置坐标轴范围
        if lon_min is not None and lon_max is not None and lat_min is not None and lat_max is not None:
            ax.set_xlim(lon_min, lon_max)
            ax.set_ylim(lat_min, lat_max)
        else:
          ax.set_xlim(xlim[0], xlim[1])
          ax.set_ylim(ylim[0], ylim[1])
        plt.xlabel('Longitude (m)')
        plt.ylabel('Latitude (m)')
        plt.title(f"{title_prefix} at Time Step {tind}")

        
        # 自动计算刻度，限制最大刻度数量
        ax.xaxis.set_major_locator(MaxNLocator(integer=True, prune=None, nbins=5))  # nbins 控制最多显示的刻度数量
 
        # 保存为 PNG 文件
        strfile = os.path.join(png_path, f"flow/flow_{tind:04d}.png")
        plt.savefig(strfile, dpi=dpi)
        plt.close()  # 关闭图形，避免内存占用过多
        print(f"Flow vector plot saved: {strfile}")

    # 清理变量和关闭文件
    nf.close()  # 关闭 NetCDF 文件
    print("Finished processing flow vector plots.")

 
# import numpy as np
# import matplotlib.tri as tri
# import matplotlib
# from xarray import Dataset
# matplotlib.use('Agg')
# from matplotlib import pyplot as plt
# from scipy.io import netcdf_file
# import numpy as np  
# # -----------------------------
# # 绘制流场矢量图（含水深）函数
# # ----------------------------- 
# def flow_vector_withDepth(nc_path,costline_path,png_path):
    
#   # 打开 NetCDF 文件并读取变量
#   nf = netcdf_file(nc_path, 'r', mmap=True)
#   lon = nf.variables['x'][:]  # 网格点经度
#   lat = nf.variables['y'][:]  # 网格点纬度
#   nv = nf.variables['nv'][:]  # 网格连接信息
#   h = nf.variables['h'][:]  # 水深数据
#   ua = nf.variables['u'][:]  # u 方向速度分量
#   va = nf.variables['v'][:]  # v 方向速度分量
#   lonc = nf.variables['xc'][:]  # 网格中心经度
#   latc = nf.variables['yc'][:]  # 网格中心纬度
#   nele = nf.dimensions['nele']  # 网格单元数
#   node = nf.dimensions['node']  # 网格节点数
#   nt = ua.shape[0]  # 时间步长数

#   # 读取岸线数据
#   coastline = np.load(costline_path)
#   coastx = coastline['coastx']
#   coasty = coastline['coasty']

#   triang = tri.Triangulation(lon, lat, nv.transpose() - 1)

#   # 设置采样间隔和数据抽样
#   inter = 12  # 抽取间隔
#   tlon = lonc[0::inter]  # 抽取经度点
#   tlat = latc[0::inter]  # 抽取纬度点

#   # 创建输出目录
#   # if not os.path.isdir('流场图'): os.mkdir('流场图')  # 如果目录不存在则创建

#   # 遍历指定的时间步长范围
#   for tind in range(nt-5,nt):
#       print(f"Processing time step {tind + 1}/{nt}")
#       fig = plt.figure()
#       plt.tripcolor(triang, h)  # 绘制水深颜色图
#       plt.plot(coastx, coasty, color='k')  # 绘制岸线
#       ax = plt.gca()
#       ax.set_aspect('equal')
#       plt.xlabel('Longitude (m)')
#       plt.ylabel('Latitude (m)')
#       plt.colorbar(label='Depth (m)')
#       plt.title(f'Depth (m) with Velocity Field (Time Step {tind + 1})')

#       # 绘制流场矢量图
#       tua = ua[tind, 0, :][0::inter]  # 抽取 u 方向速度
#       tva = va[tind, 0, :][0::inter]  # 抽取 v 方向速度

#       # 确保 tua 和 tva 的大小与 tlon 和 tlat 匹配
#       tua = tua[:len(tlon)]
#       tva = tva[:len(tlat)]

#       # 控制矢量的长度和粗细
#       scale = 17  # 控制矢量长度
#       width = 0.002  # 控制矢量宽度

#       plt.quiver(tlon, tlat, tua, tva, scale=scale, width=width)  # 绘制流场矢量

#       # 保存每个时间步的图像
#       strfile = png_path+f'flow/velocity_depth_{tind + 1:04d}.png'
#       plt.savefig(strfile)  # 保存图形
#       # plt.show()  # 显示图形
#       plt.close()  # 关闭图形以释放内存
#       print("06脚本： 流场矢量图成完成---"+strfile)

#   # 清理变量和关闭文件
#   h = None
#   lon = None
#   lat = None
#   nv = None
#   ua = None
#   va = None
#   lonc = None
#   latc = None
#   tlon = None
#   tlat = None
#   tua = None
#   tva = None
#   nf.close()  # 关闭 NetCDF 文件
