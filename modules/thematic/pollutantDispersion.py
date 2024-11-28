import os
import numpy as np
import matplotlib.pyplot as plt
from netCDF4 import Dataset
import matplotlib.tri as tri
import matplotlib.colors as mcolors
import ezdxf
# -----------------------------
# 污染物扩散等值线-CLASS
# ----------------------------- 
class DyeConcentrationPlotter:
    def __init__(self, lon_min, lon_max, lat_min, lat_max, dlon, dlat,  time_index=99,siglay_index=0, 
                 nc_file='ezwssc_0001.nc', output_dir='kuosan',levels=None, lon_col='x', lat_col='y', nv_col='nv', dye_col='ssc',
                 contour_color='k', contour_linewidth=0.5): 
                # 打印传入的参数，确保它们正确传递
        print(f"Initializing DyeConcentrationPlotter with the following parameters:")
        print(f"lon_min: {lon_min}, lon_max: {lon_max}, lat_min: {lat_min}, lat_max: {lat_max}")
        print(f"dlon: {dlon}, dlat: {dlat}, levels: {levels}, time_index: {time_index}, siglay_index: {siglay_index}")
        print(f"nc_file: {nc_file}, output_dir: {output_dir}")

        """
        初始化函数，所有参数可以通过调用时传递。
        
        :param lon_min: 经度最小值
        :param lon_max: 经度最大值
        :param lat_min: 纬度最小值
        :param lat_max: 纬度最大值
        :param dlon: 标注的经度
        :param dlat: 标注的纬度
        :param levels: 等值线的水平（可选）
        :param time_index: 时间步长索引
        :param siglay_index: 层数索引
        :param nc_file: NetCDF文件路径
        :param output_dir: 输出目录
        :param lon_col: 经度变量名
        :param lat_col: 纬度变量名
        :param nv_col: 网格连接信息变量名
        :param dye_col: 污染物浓度变量名
        :param contour_color: 等值线颜色
        :param contour_linewidth: 等值线线宽
        """
        self.lon_min = lon_min
        self.lon_max = lon_max
        self.lat_min = lat_min
        self.lat_max = lat_max
        self.dlon = dlon
        self.dlat = dlat
        self.levels = levels if levels else [0, 1, 5, 10, 20, 50, 100, 200, 500, 700, 1000]
        self.time_index = time_index
        self.siglay_index = siglay_index
        self.nc_file = nc_file
        self.output_dir = output_dir
        self.lon_col = lon_col
        self.lat_col = lat_col
        self.nv_col = nv_col
        self.dye_col = dye_col
        self.contour_color = contour_color
        self.contour_linewidth = contour_linewidth
        print('初始化完成self.nc_file = '+self.nc_file)
        print('初始化完成self.nc_file = '+self.output_dir)
        # 创建输出目录
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        # 读取NetCDF文件
        self.nc_data = self._read_nc_file()

    def _read_nc_file(self):
        """ 读取NetCDF文件并提取需要的数据 """
        nc = Dataset(self.nc_file, 'r')

        lon = nc.variables[self.lon_col][:]  # 经度
        lat = nc.variables[self.lat_col][:]  # 纬度
        nv = nc.variables[self.nv_col][:] - 1  # 网格连接信息，转换为0基索引
        dye = nc.variables[self.dye_col][:] * 1000  # 污染物浓度，单位转换为千
        return {'lon': lon, 'lat': lat, 'nv': nv, 'dye': dye, 'nc': nc}

    def _create_triangular_mesh(self, lon, lat, nv):
        """ 创建三角剖分 """
        return tri.Triangulation(lon, lat, nv.T)

    def plot(self):
        """ 绘制等值线图并保存为PNG文件和DXF文件 """
        # 提取时间步的浓度数据
        dye_at_time = self.nc_data['dye'][self.time_index, self.siglay_index, :]  # 获取指定时间步的数据
        dye_at_time[dye_at_time < 0] = 0  # 将负值设为0

        # 创建三角剖分
        triang = self._create_triangular_mesh(self.nc_data['lon'], self.nc_data['lat'], self.nc_data['nv'])

        # 创建颜色映射
        cmap = plt.get_cmap('viridis_r')
        norm = mcolors.Normalize(vmin=0, vmax=1000)

        # 绘制等值线图
        plt.figure(figsize=(10, 8))
        contourf = plt.tricontourf(triang, dye_at_time, levels=self.levels, cmap=cmap, norm=norm)
        contour = plt.tricontour(triang, dye_at_time, levels=self.levels, colors=self.contour_color, linewidths=self.contour_linewidth)

        # 显示等值线标签
        plt.clabel(contour, inline=True, fontsize=8, fmt='%.2f')
        plt.colorbar(contourf, label='Dye Concentration')
        plt.xlabel('Longitude')
        plt.ylabel('Latitude')
        plt.title(f'Dye Concentration Contour at Time Step {self.time_index+1}')

        # 添加文字标注
        plt.rcParams['font.sans-serif'] = ['SimHei']
        plt.rcParams['axes.unicode_minus'] = False
        text_label = "工程中心"
        plt.text(self.dlon, self.dlat, text_label, fontsize=10, ha='center', color='red')

        # 保存PNG文件
        # output_path = os.path.join(self.output_dir, f'dye_concentration_{self.time_index+1}.png')
        print(self.output_dir+'/pollutant.png')
        plt.savefig(self.output_dir+f'pollutant/pollutant_{self.time_index+1}.png', dpi=1000)
        # plt.savefig(output_path)
        # plt.show()

        # 保存为DXF文件
        self._save_as_dxf(contour)

        # 关闭NetCDF文件
        self.nc_data['nc'].close()

    def _save_as_dxf(self, contour):    
        """ 将等值线保存为DXF文件 """
        doc = ezdxf.new(dxfversion='AC1027')
        msp = doc.modelspace()

        # 使用contour.allsegs绘制多段线
        for level_segments in contour.allsegs:
            for segment in level_segments:
                if len(segment) > 1:  # 忽略太短的路径
                    points = segment
                    msp.add_lwpolyline(points, close=True)  # 添加为多段线，close=False 表示不封闭

        # 保存DXF文件
        dxf_output_path = os.path.join(self.output_dir, f'pollutant/dye_concentration_{self.time_index+1}.dxf')
        doc.saveas(dxf_output_path)
         


# 外部调用
def pollutantDispersion(       
        nc_file, 
        output_dir, 
        lon_min=806500, 
        lon_max=811000, 
        lat_min=4410250,
        lat_max=4413750,
        dlon=740000, 
        dlat=4285750,
        time_index=88,
        siglay_index= 2
        ):
     print("开始污染物扩散:"+nc_file)
     plotter =DyeConcentrationPlotter(lon_min, lon_max, lat_min, lat_max,dlon, dlat, time_index,siglay_index,nc_file, output_dir)
     plotter.plot()
     print("污染物扩散完成")

# if __name__ == '__main__':
#     # 直接传入参数，设置经纬度范围、标注位置等
#     plotter = DyeConcentrationPlotter(
#         lon_min=806500, 
#         lon_max=811000, 
#         lat_min=4410250, 
#         lat_max=4413750,
#         dlon=740000, 
#         dlat=4285750,
#         time_index=88,
#         siglay_index= 2,
#         nc_file='ezwssc_0001.nc', 
#         output_dir='kuosan'
#     )
#     plotter.plot()
    