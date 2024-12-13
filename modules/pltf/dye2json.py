from netCDF4 import Dataset
import numpy as np
from scipy.interpolate import griddata
import sys
# import psycopg2
from datetime import datetime
import json
from osgeo import gdal, ogr, osr
import random
import shutil
import os
import uuid

# 考究的要素
items = ['DYE']
# 只拿这几层
# layers = [0, 1, 2]
layers = [0]
# 像素大小
pixel = [80, 80]
# 配置
config = {

    "DYE": {
        "size": [80, 80],
        "valueRange": [0, 510],
        "peak": 204,
        "point": 6
    }
}

 
def read_nc(nc_path, analog_name,time_index=50):
    nc_file = Dataset(nc_path)
     # 先打印变量信息进行调试
    # print("NecCDF 文件变量:")
    # for var_name in nc_file.variables:
    #     var = nc_file.variables[var_name]
    #     # print(f"{var_name}: {var.dimensions}, shape: {var.shape}")
        
    lon = nc_file.variables['x'][:]
    lat = nc_file.variables['y'][:]

    # 格式化nc文件的时间
    time = nc_file.variables['time']
    # data_time_byte=time[0, :]
    data_time_byte=time[:] # 获取所有元素
    # print(data_time_byte)
    a = len(data_time_byte)
    results = []
    i = time_index
    # for i in range(46,47):
        # if i>23:
            # print( "正在处理第"+str(i+1)+"个时间段")
            # break
        #  data_time_byte_char = time[i, :]
    data_time_byte_char = time[i]
    # 检查掩码数组的内容
    # print("数据内容:", data_time_byte_char.data)
    # print("掩码内容:", data_time_byte_char.mask)
    # 提取有效数据
    if data_time_byte_char.mask is not None:
        valid_data = data_time_byte_char.compressed()  # 获取有效的数据
    else:
        valid_data = data_time_byte_char.data
    # 确保有效数据是字节格式
    valid_data = np.array(valid_data, dtype=np.bytes_)
    # 解码有效数据
    try:
        data_time_char = np.char.decode(valid_data)
        # print("解码后的数据:", data_time_char)
    except Exception as e:
        print("解码失败:", e)
    #  data_time_char = np.char.decode(data_time_byte_char)[:]
    data_time = ''.join(data_time_char)
    # print( "时间:", data_time)
    #  data_time = format_string_date(data_time, '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%d %H:%M:%S')
    for item in items:
        if item in nc_file.variables:
            # print(f"开始处理{item}数据")
            variable = nc_file.variables[item]
            # 遍历每一层级
            for layer in layers:
                layer_data = np.array(variable[i, layer, :], dtype=np.float64)
                # print(f"Layer {layer} min: {np.min(layer_data)}, max: {np.max(layer_data)}")

                for i1,value in enumerate(layer_data):
                    if value<0 :
                        # print(f"发现小于0负值，将其置为0")
                        layer_data[i1] = 0
                    # if value>0 :
                            # print(f"发现>0.01正值!!!")
    
                        
                # 对DIN进行单位换算
                if item == 'DIN':
                    layer_data = [x * 14 / 1000 for x in layer_data]
                # 创建根目录文件夹
                dir_path = create_temp_dir(item, layer)
                # 指定shp文件路径
                shp_path = os.path.join(dir_path, item + '_' + str(i)+'_'+ str(layer) + '.shp')
                # 指定tiff文件路径
                tiff_path = os.path.join(dir_path, item + '_' +str(i)+'_'+ str(layer) + '.tif')
                # 创建shp文件
                point2shp(shp_path, lon, lat, layer_data, item)
                # 反距离权重插值，得到插值后的数据
                idw(tiff_path, shp_path, item)
                # 读取tiff文件数据
                dataset = gdal.Open(tiff_path)  # 打开文件
                grid_data = np.array(dataset.ReadAsArray(0, 0, pixel[0], pixel[1]), dtype=float)
                # # 读取后删除dir目录
                dataset = None
                shutil.rmtree(dir_path)
                # data_after_fli = np.flipud(grid_data)
                data_after_fli = grid_data #   因为dye数据是上下颠倒的，所以不用再翻转了
                data = data_after_fli.reshape(-1)
                grid_data_json = format_data(lon, lat, data, item)
                result = {
                    "item": item,
                    "layer": layer,
                    "json": grid_data_json,
                    "history_id": analog_name,
                    "nc_path": nc_path,
                    "datatime": data_time,
                    "avg": np.mean(grid_data).astype(np.float64)
                }
                
                # # 保存结果到json文件
                # with open( str(data_time) + '_data.json', 'w') as f:
                #     json.dump(result, f)
                    
                results.append(result)
    return results
 
# 四舍五入数据 对DIN进行处理
def round_layer_data(layer_data, item, lon, lat):
    cfg = config[item]
    point = cfg['point']
    rounded_data = np.round(layer_data, point).tolist()
    # 将lon和lat保留6位小数并转换为列表
    rounded_lon = [round(x, 6) for x in lon.tolist()]
    rounded_lat = [round(x, 6) for x in lat.tolist()]
    return rounded_data, rounded_lon, rounded_lat






# 反距离权重插值
def idw(output_file, point_file, item):
    # 确定参数
    opts = gdal.GridOptions(format="GTiff", outputType=gdal.GDT_Float32, width=pixel[0], height=pixel[1],
                            # algorithm="invdist:power=3.5:smothing=0.0:radius=1.0:max_points=12:min_points=0:nodata=0.0",
                            algorithm="invdist:power=3.5:smoothing=0.0:max_points=12:min_points=0:nodata=0.0",
                            zfield=item)
    gdal.Grid(destName=output_file, srcDS=point_file, options=opts)


# 获取时间戳+一个随机数组成一个文件名
def get_random_file_name():
    return "temp_" + str(int(datetime.now().timestamp())) + "_" + str(random.randint(0, 10000))


# 创建临时目录，用于存储临时文件，结束后会全部删除
def create_temp_dir(item, layer):
    dir_path = os.path.join(os.path.abspath(os.getcwd()), get_random_file_name() + '_' + item + '_' + str(layer))
    if os.path.exists(dir_path):
        # 如果目录已经存在，则先删除目录及其内容
        shutil.rmtree(dir_path)
    os.makedirs(dir_path)
    return dir_path


# 删除临时目录，保证硬盘环境
def clear_temp_file(dir_name):
    path = os.path.join(os.path.abspath(os.getcwd()), dir_name)
    if os.path.exists(path):
        shutil.rmtree(path)


# 格式化数据时间
def format_string_date(date_str, input_format, output_format):
    # 将字符串转换为 datetime 对象
    dt = datetime.strptime(date_str, input_format)
    # 将 datetime 对象格式化为指定输出格式的字符串
    formatted_str = dt.strftime(output_format)
    return formatted_str


# 插值方法
def interpolate(lon, lat, data):
    # 创建一个网格
    grid_lon, grid_lat = np.meshgrid(np.linspace(min(lon), max(lon), pixel[0]), np.linspace(min(lat), max(lat), pixel[1]))
    # 插值
    grid_data = griddata((lon, lat), data, (grid_lon, grid_lat), method='nearest').flatten()
    return grid_data



def point2shp(shp_path, lons, lats, data, item):
    # 定义驱动
    driver = ogr.GetDriverByName("ESRI Shapefile")
    # 创建一个shp文件
    data_source = driver.CreateDataSource(shp_path)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)  # 这是WGS84,想用什么自己去搜下对应的编码就行了
    # 创建点文件
    layer = data_source.CreateLayer("Point", srs, ogr.wkbPoint)
    # 定义字段的内容，添加字段
    field_name = ogr.FieldDefn(item, ogr.OFTString)
    field_name.SetWidth(14)
    layer.CreateField(field_name)
    feature = ogr.Feature(layer.GetLayerDefn())
    for i in range(len(lons)):
        x = lons[i]
        y = lats[i]
        val = data[i]
        # 写入数据
        feature.SetField(item, "{0}".format(str(val)))
        # 生成点的固定格式
        wkt = "POINT({0} {1})".format(x, y)
        point = ogr.CreateGeometryFromWkt(wkt)
        feature.SetGeometry(point)
        layer.CreateFeature(feature)
    feature = None
    data_source = None



# 归一化数据0-255
def normalization_data(array, min, max):
    # 超过最大的就按最大的算
    array[array > max] = max
    # 超过最小的就按最小的算
    array[array < min] = min
    array = array / ((max - min) / 255)
    return array

# 归一化数据0-255
def normalization_data_new(array):
    # 超过最大的就按最大的算
    min_val = min(array)
    max_val = max(array)
    # 计算插值
    diff = max_val - min_val
    normalized_array = [(x - min_val) / diff * 255 for x in array]
    return normalized_array


# 格式化数据
def format_data(lon, lat, data, item):
    data_after_round, lon_after_round, lat_after_round = round_layer_data(data, item, lon, lat)
    header = {
        "lo1": min(lon_after_round),
        "lo2": max(lon_after_round),
        "la1": min(lat_after_round),
        "la2": max(lat_after_round),
        "nx": pixel[0],
        "ny": pixel[1],
        "dx": np.round((max(lon_after_round) - min(lon_after_round)) / pixel[0], 6),
        "dy": np.round((max(lat_after_round) - min(lat_after_round)) / pixel[1], 6),
        "max": max(data_after_round),
        "min": min(data_after_round)
    }
 
    return {
         "data": data_after_round,  
        "header": header
    }
 
def dye2json(nc_path,time):
        nc_file_path = nc_path  
        analog_name =   uuid.uuid4()
        time = time or 50
        results = read_nc(nc_file_path, analog_name, time)
        # print(results)
        return results
def main():
        nc_file_path = sys.argv[1] if len(sys.argv) > 1 else "F:\\Desktop\\ZIZHI-DYE-01.nc"
        analog_name = sys.argv[2] if len(sys.argv) > 2 else '1805503841063596034'
        results = read_nc(nc_file_path, analog_name)
        # print(results)
        return results
 

if __name__ == "__main__":
   main()

