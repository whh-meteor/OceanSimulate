
import numpy as np
import matplotlib.tri as tri
import matplotlib
from matplotlib import pyplot as plt
from scipy.io import netcdf_file
from xarray import Dataset
matplotlib.use('Agg')
from modules.thematic.common import harmonic
# -----------------------------
# 潮汐调和分析函数
# -----------------------------
def gen_tide_analysis(filepath='pltf_0002.nc', tide_path='tide_analysis.npz'):
    """
    执行潮汐调和分析并保存结果。
    :param filepath: NetCDF 网格文件路径
    :param tide_path: 输出潮汐调和分析结果文件路径 (.npz)
    """
    # 打开 NetCDF 文件
    nf = netcdf_file(filepath, 'r', mmap=True)
    lon = nf.variables['x'][:]
    lat = nf.variables['y'][:]
    nv = nf.variables['nv'][:]
    time = nf.variables['time'][:]
    zeta = nf.variables['zeta'][:]
    node = nf.dimensions['node']

    # 潮汐成分及周期
    tide_name = ['m2', 's2', 'k1', 'o1']
    period = np.array([44712, 43200, 86164, 92950])  # 周期 (秒)
    tide_freq = 2 * np.pi / period
    time_secs = time * 86400

    # 初始化振幅和相位数组
    amp = np.zeros([node, len(tide_name)])
    phase = np.zeros([node, len(tide_name)])
    amp0 = np.zeros([node, 1])

    # 调和分析 (最后 4 天的数据)
    nhours = 4 * 24
    for i in range(node):
        [amp[i, :], phase[i, :], amp0[i]] = harmonic(
            time_secs[-nhours:], zeta[-nhours:, i], tide_freq
        )

    # 保存结果到 .npz 文件
    np.savez(tide_path, amp=amp, phase=phase, amp0=amp0, lon=lon, lat=lat, nv=nv, tide_name=tide_name)
    nf.close()
    print("潮位调和分析完成，结果保存为:", tide_path)


# -----------------------------
# 主函数：处理岸线和网格并生成分析图
# -----------------------------
def get_coastline_from_npz(
    water_nc_path,
    pollutant_nc_path,
    lag_nc_path,
    costaline,
    tidenpz,
    png_path
):
    """
    基于输入的网格文件和其他数据文件生成分析图。
    :param water_nc_path: NetCDF 网格文件路径
    :param pollutant_nc_path: 污染物扩散文件路径
    :param lag_nc_path: 拉格朗日粒子追踪文件路径
    :param costaline: 输出岸线文件路径
    :param tidenpz: 输出潮汐调和分析结果文件路径 (.npz)
    :param png_path: 图形输出目录
    """
    # 岸线生成
    from modules.thematic.mesh_costline import mesh_costline
    mesh_costline(
        filepath=water_nc_path,
        costline_path=costaline,
        png_path=png_path,
        tri_linewidth = 0.05,# 三角网格线宽
        costa_linewidth = 1.0,# 岸线宽度
        lon_min=400000,  # 经度最小值
        lon_max=500000,  # 经度最大值
        lat_min=4150000, # 纬度最小值
        lat_max=4200000, # 纬度最大值
        dpi=300,  # 输出分辨率

    )
    gen_tide_analysis(water_nc_path, tidenpz)  # 潮汐调和分析
    # 绘制潮位调和分析图
    from modules.thematic.plot_tide_analysis import plot_tide_analysis
    plot_tide_analysis(tidenpz, costaline, png_path ,                 
                  lon_min=400000, 
                  lon_max=500000, 
                  lat_min=4150000, 
                  lat_max=4200000,
                  dpi=1000)  # 绘制振幅和相位等值线图
    # 绘制水深分布图
    from modules.thematic.plot_depth import plot_depth
    plot_depth(water_nc_path, 
                  costaline, 
                  png_path, 
                  tri_linewidth=0.3, 
                  lon_min=400000, 
                  lon_max=500000, 
                  lat_min=4150000, 
                  lat_max=4200000,
                  dpi=1000)

    from modules.thematic.points_tide_flow import points_tide_flow
    points_tide_flow(water_nc_path, png_path)  # 绘制点潮位流速图
    # 矢量流场（无水深）
    from modules.thematic.flow_vector_noDepth import flow_vector_noDepth
    flow_vector_noDepth(
        nc_path=water_nc_path,
        costline_path=costaline,
        png_path=png_path,
        inter=10,  # 采样间隔
        time_range=(0, 10),  # 时间步范围
        siglay_step = 1,  # 层数间隔
        speed=3,  # 流速
        scale=15,  # 矢量图比例尺
        width=0.003,  # 矢量宽度
        quiverkey_pos=(0.1, -0.1),  # 流速比例尺位置
        compass_pos=(0.95, 0.95),  # 指北针位置
        title_prefix="Ocean Flow",  # 标题前缀
        dpi=600,  # 图片分辨率
        coast_color='blue',  # 岸线颜色
        coast_linewidth=2,  # 岸线宽度
        quiver_color='red' , # 矢量颜色
        lon_min=400000, 
        lon_max=500000, 
        lat_min=4150000, 
        lat_max=4200000
    )
    # 矢量流场（带水深）
    from modules.thematic.flow_vector_withDepth import flow_vector_withDepth
    flow_vector_withDepth(
        nc_path=water_nc_path,
        costline_path=costaline,
        png_path=png_path,
        inter=10,  # 采样间隔
        time_range=(0, 10),  # 时间步范围
        siglay_step = 1,  # 层数间隔
        speed=3,  # 流速
        scale=15,  # 矢量图比例尺
        width=0.003,  # 矢量宽度
        quiverkey_pos=(0.1, -0.1),  # 流速比例尺位置
        compass_pos=(0.95, 0.95),  # 指北针位置
        title_prefix="Ocean Flow",  # 标题前缀
        dpi=600,  # 图片分辨率
        coast_color='blue',  # 岸线颜色
        coast_linewidth=2,  # 岸线宽度
        quiver_color='red',  # 矢量颜色
        lon_min=None, 
        lon_max=None, 
        lat_min=None, 
        lat_max=None
    )
     # 拉格朗日粒子追踪图
    from modules.thematic.lag_script import lag_script
    lag_script(lag_nc_path, costaline, png_path) 
    # 污染物扩散图
    from modules.thematic.pollutantDispersion import pollutantDispersion
    pollutantDispersion(pollutant_nc_path, 
                        png_path, 
                        lon_min=806500, 
                        lon_max=811000, 
                        lat_min=4410250, 
                        lat_max=4413750,
                        dlon=740000,# 工程中心点经度
                        dlat=4285750, # 工程中心点纬度
                        time_index=88,
                        siglay_index= 2)  

    return costaline, tidenpz


# -----------------------------
# main()
# -----------------------------
if __name__ == "__main__":
    get_coastline_from_npz()
