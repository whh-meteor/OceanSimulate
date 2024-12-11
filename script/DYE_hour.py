from netCDF4 import Dataset
import numpy as np
from scipy.interpolate import griddata
import sys
import psycopg2
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
layers = [0, 2, 5]
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

# 数据库连接
def conn_pgsql():
    return psycopg2.connect(host='localhost',
                            port='5432',
                            database='zhongwang',
                            user='postgres',
                            password='123456')
def read_nc(nc_path, analog_name):
    nc_file = Dataset(nc_path)
    lon = nc_file.variables['lon'][:]
    lat = nc_file.variables['lat'][:]

    # 格式化nc文件的时间
    time = nc_file.variables['Times']
    data_time_byte=time[0, :]
    a = len(data_time_byte)

    results = []
    for i in range(0,a):
     if i>23:
         break
     data_time_byte_char = time[i, :]
     data_time_char = np.char.decode(data_time_byte_char)[:]
     data_time = ''.join(data_time_char)
     data_time = format_string_date(data_time, '%Y-%m-%dT%H:%M:%S.%f', '%Y-%m-%d %H:%M:%S')
     for item in items:
       if item in nc_file.variables:
           variable = nc_file.variables[item]
           # 遍历每一层级
           for layer in layers:
               layer_data = variable[i, layer, :]
               for i1,value in enumerate(layer_data):
                   if value<0:
                       layer_data[i1] = 0
               # 对DIN进行单位换算
               if item == 'DIN':
                   layer_data = [x * 14 / 1000 for x in layer_data]
               # 创建根目录文件夹
               dir_path = create_temp_dir(item, layer)
               # 指定shp文件路径
               shp_path = os.path.join(dir_path, item + '_' + str(layer) + '.shp')
               # 指定tiff文件路径
               tiff_path = os.path.join(dir_path, item + '_' + str(layer) + '.tif')
               # 创建shp文件
               point2shp(shp_path, lon, lat, layer_data, item)
               # 反距离权重插值，得到插值后的数据
               idw(tiff_path, shp_path, item)
               # 读取tiff文件数据
               dataset = gdal.Open(tiff_path)  # 打开文件
               grid_data = np.array(dataset.ReadAsArray(0, 0, pixel[0], pixel[1]), dtype=float)
               # 读取后删除dir目录
               dataset = None
               shutil.rmtree(dir_path)
               data_after_fli = np.flipud(grid_data)
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
                            algorithm="invdist:power=3.5:smothing=0.0:radius=1.0:max_points=12:min_points=0:nodata=0.0",
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


# 存储模型模拟nc变量数据
def store_analog_data(results):
    # 获取当前实际时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = conn_pgsql()
    cur = conn.cursor()
    # 遍历所有结果
    for result in results:
        # 将数据插入到数据库中
        cur.execute("INSERT INTO public.analog_data (analog_name, file_path, layer, item, data_time, data, create_time) VALUES (%s, %s, %s, %s, %s, %s, %s);",
                    (result['analog_name'],
                     result['nc_path'],
                     result['layer'],
                     result['item'],
                     result['datatime'],
                     json.dumps(result['json']),
                     current_time))

    conn.commit()
    cur.close()
    conn.close()

# 存储预测数据
def store_predict_data(results):
    # 获取当前实际时间
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = conn_pgsql()
    cur = conn.cursor()
    # 遍历所有结果
    for result in results:
        # 将数据插入到数据库中
        cur.execute("""
            INSERT INTO public.material_transport_history_details (id,level, item, data_time, outcome, create_time,history_id) VALUES (%s,%s, %s, %s, %s, %s,%s)
            ON CONFLICT (data_time, level,item)  
            DO NOTHING;
            """,
                    (str(uuid.uuid1()),
                     result['layer'],
                     result['item'],
                     result['datatime'],
                     json.dumps(result['json']),
                     current_time,
                     int(result['history_id'])))

    conn.commit()
    cur.close()
    conn.close()


def main():
        nc_file_path = sys.argv[1] if len(sys.argv) > 1 else 'F:\\moxing\\hedian\\wuranwu\\bbw_0010.nc'
        analog_name = sys.argv[2] if len(sys.argv) > 2 else '1805503841063596034'
        results = read_nc(nc_file_path, analog_name)
        store_predict_data(results)
        print('数据入库成功')



if __name__ == "__main__":
   main()

