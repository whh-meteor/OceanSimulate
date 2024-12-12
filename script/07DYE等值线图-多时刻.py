import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
from netCDF4 import Dataset
import matplotlib.tri as tri
import matplotlib.colors as mcolors
import ezdxf

# 文件名
filename = "F:\\Desktop\\OceanSimulate\\script\\范围.txt"

# 读取文件
with open(filename, 'r') as file:
    lines = file.readlines()

# 解析数据
first_line = lines[0].strip().split()
second_line = lines[1].strip().split()

# 将每个数字转换为整数
a, b = int(first_line[0]), int(first_line[1])
c, d = int(second_line[0]), int(second_line[1])

# 读取第三行中的数值作为等值线的水平
levels = list(map(float, lines[2].strip().split()))  # 将第三行的数值转为浮点数

xlim = [a, b]  # 根据经度数据设置 x 轴范围
ylim = [c, d]  # 根据纬度数据设置 y 轴范围

# 创建保存图像的文件夹
output_dir = 'kuosan'
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# 读取 NetCDF 文件
file_path = "F:\\Desktop\\ZIZHI-DYE-01.nc"  # 替换为你的 nc 文件路径
nc = Dataset(file_path, 'r')

# 假设变量名为 'DYE'（请根据实际文件修改）
lon = nc.variables['x'][:]  # 网格点经度
lat = nc.variables['y'][:]  # 网格点纬度
nv = nc.variables['nv'][:] - 1  # 将网格连接信息转换为 0 基索引
dye = nc.variables['DYE'][:]  # 替换为你的污染物浓度变量名
time_steps = dye.shape[0]  # 获取时间步长数量

# 设置绘图的时间段 (例如，时间步 10 到 20)
start_time = 0  # 起始时间步索引（从 0 开始）
end_time = 48    # 结束时间步索引（从 0 开始）

# 遍历指定时间段内的时间步
for time_index in range(start_time, end_time + 1):
    dye_at_time = dye[time_index, 0, :]  # 选择第 0 层的数据，视情况修改
    dye_at_time[dye_at_time < 0] = 0
    
    # 创建三角剖分
    triang = tri.Triangulation(lon, lat, nv.T)

    # 使用自定义的颜色映射，增强颜色变化
    cmap = plt.get_cmap('viridis_r')
    norm = mcolors.Normalize(vmin=0, vmax=1)

    # 绘制等值线图和等值线
    plt.figure(figsize=(10, 8))
    ax = plt.gca()
    # ax.set_xlim(xlim[0], xlim[1])
    # ax.set_ylim(ylim[0], ylim[1])
    ax.set_aspect('equal')
    # 绘制填充的等值线图
    contourf = plt.tricontourf(triang, dye_at_time, levels=levels, cmap=cmap, norm=norm)
    # 绘制等值线
    contour = plt.tricontour(triang, dye_at_time, levels=levels, colors='k', linewidths=0.5)

    # 显示等值线标签
    plt.clabel(contour, inline=True, fontsize=8, fmt='%.2f')  # 显示等值线标签
    plt.colorbar(contourf, label='Dye Concentration')  # 添加颜色条
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.title(f'Dye Concentration Contour at Time Step {time_index + 1}')

    # 保存图像到 kuosan 文件夹
    output_path = os.path.join(output_dir, f'dye_concentration_{time_index + 1}.png')
    plt.savefig(output_path, dpi=1000)  # 设置图像分辨率为 1000 DPI
    plt.close()

    # 将等值线保存为 DXF 文件
    # 创建 DXF 文档
    doc = ezdxf.new(dxfversion='AC1027')
    msp = doc.modelspace()

    # 使用 contour.allsegs 替代 contour.collections
    for level_segments in contour.allsegs:
        for segment in level_segments:
            if len(segment) > 1:  # 忽略太短的路径
                # 将等值线坐标添加为多段线到 DXF 文件中
                points = segment
                msp.add_lwpolyline(points, close=True)  # 添加为多段线，close=False 表示不封闭

    # 保存 DXF 文件
    dxf_output_path = os.path.join(output_dir, f'dye_concentration_{time_index + 1}.dxf')
    doc.saveas(dxf_output_path)

# 关闭 NetCDF 文件
nc.close()

print("图像和DXF文件已生成！")
