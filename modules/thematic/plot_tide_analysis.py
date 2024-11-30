
import numpy as np
import matplotlib.tri as tri
import matplotlib
matplotlib.use('Agg')
from matplotlib import pyplot as plt
import numpy as np 
# -----------------------------
# 绘制振幅和相位等制图函数
# ----------------------------- 

def plot_tide_analysis(tide_path,
                       costaline_path,
                       pngpath,
                        lon_min=None, 
                        lon_max=None, 
                        lat_min=None, 
                        lat_max=None,
                        dpi=300,
                        png_name='tideAnalysis'
                       ):
    
  # 加载调和常数数据
  hc = np.load(tide_path)  # 从文件中加载数据
  tide_name = hc['tide_name']  # 提取潮汐名称
#   lonc = hc['xc']  # 读取网格中心点的经度
#   latc = hc['yc']  # 读取网格中心点的纬度
  lon = hc['lon']  # 提取经度数据
  lat = hc['lat']  # 提取纬度数据
  amp = hc['amp'] * 100  # 提取并放大振幅数据
  phase = hc['phase']  # 提取相位数据
  nv = hc['nv']  # 三角形网格节点信息
  ntide = tide_name.shape[0]  # 获取潮汐成分数量
  lon.shape = -1  # 将经度数据展平
  lat.shape = -1  # 将纬度数据展平
  tide_name.shape = -1  # 将潮汐名称展平

  # 加载岸线数据
  coastline = np.load(costaline_path)  # 加载岸线数据
  coastx = coastline['coastx']  # 提取岸线的 x 坐标
  coasty = coastline['coasty']  # 提取岸线的 y 坐标
  xlim = [lon.min(), lon.max()]  # 设置 x 轴范围
  ylim = [lat.min(), lat.max()]  # 设置 y 轴范围
  # 定义绘图参数
  amp_fr = [10, 5, 2, 2]  # 振幅起始值列表
  amp_int = [10, 5, 2, 2]  # 振幅等值线间隔
  phase_int = [30, 30, 30, 30]  # 相位等值线间隔
  tide_ind = [0, 1, 2, 3]  # 要绘制的潮汐成分索引

  # 构建三角网格
  faces = nv.transpose().copy() - 1  # 将节点信息转置并减去 1（从 0 开始索引）
  triang = tri.Triangulation(lon, lat, faces)  # 创建三角网格对象

  # 遍历每个指定的潮汐成分进行绘图
  for n in tide_ind:
      tamp = amp[:, n]  # 提取指定潮汐成分的振幅
      tphase = phase[:, n]  # 提取指定潮汐成分的相位

      # 检查和处理非有限值
      if not np.all(np.isfinite(tphase)):  # 检查 tphase 中是否有非有限值
          print(f"Non-finite values found in tphase for tide index {n}, handling them.")
          tphase = np.where(np.isfinite(tphase), tphase, np.nanmean(tphase))  # 用均值替换非有限值

      # 定义振幅和相位等值线的间隔
      levs_amp = np.arange(amp_fr[n], 150, amp_int[n])  # 振幅等值线水平
      levs_phase = np.arange(30, 350, phase_int[n])  # 相位等值线水平

      # 创建图形
      fig = plt.figure()
      ax = fig.add_subplot(111)  # 创建一个子图
      ax.set_aspect('equal')  # 设置轴比例为相等
              # 如果lon_min, lon_max, lat_min, lat_max都有值，则设置坐标轴范围
      if lon_min is not None and lon_max is not None and lat_min is not None and lat_max is not None:
        ax.set_xlim(lon_min, lon_max)
        ax.set_ylim(lat_min, lat_max)
      else:
        ax.set_xlim(xlim[0], xlim[1])
        ax.set_ylim(ylim[0], ylim[1])
      plt.xlabel('Longitude (m)')  # 设置 x 轴标签
      plt.ylabel('Latitude (m)')  # 设置 y 轴标签
      plt.plot(coastx, coasty, color='k', linewidth=1)  # 绘制岸线

      # 绘制振幅和相位等值线图
      ca = plt.tricontour(triang, tamp, levs_amp, colors='k', linestyles='dashed')  # 绘制振幅等值线
      cp = plt.tricontour(triang, tphase, levs_phase, colors='k')  # 绘制相位等值线

      # 设置等值线标签格式
      strfmt = '%.0f'
      if amp_int[n] < 1:
          strfmt = '%.1f'

      # 添加等值线标签
      plt.clabel(ca, levs_amp[0::1], inline=0, fmt=strfmt, fontsize=12, colors='r')  # 标注振幅等值线
      plt.clabel(cp, levs_phase[0::1], inline=0, fmt='%.0f', fontsize=12, colors='b')  # 标注相位等值线
        
      # 设置图形标题和保存文件
      strtide = tide_name[n]  # 获取当前潮汐成分的名称
      strtitle = 'cotidal map: %s (cm)' % strtide  # 设置图形标题
      plt.title(strtitle)  # 添加图形标题
      strname = pngpath+'amplitude/'+strtide+'_'+png_name+'.png'  # 设置保存的文件名
      plt.savefig(strname ,dpi =dpi)  # 保存图形为 PNG 文件
      print("03脚本：振幅和相位等值线生成完成---"+strname)
