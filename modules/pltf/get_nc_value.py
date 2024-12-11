# -*- coding: utf-8 -*-
# @Author      : J_QHQ
# @File        ：nc2png.py
# @DataTime    : 2024/3/11 09:16
# @Description : nc转png

# 注意，路径不允许有中文
import os, sys, random, shutil, datetime

import numpy as np
from PIL import Image
from netCDF4 import Dataset
from osgeo import gdal, ogr, osr


def nc_2_shp(nc_path, shp_path, siglay,time, types):
    """
    nc转shp
    :param nc_path:
    :param shp_path:
     :param siglay: 时间 共20层
    :param types:
    :return:
    """
    # 读取nc
    nc_obj = Dataset(nc_path)
    lat_list = nc_obj.variables['xc'][:]  # 54332
    lon_list = nc_obj.variables['yc'][:]  # 54332
    u = nc_obj.variables['u'][:]
    v = nc_obj.variables['v'][:]
    points = []
    v_values = []
    u_values = []

    print(f"U stats: min={np.min(u)}, max={np.max(u)}, mean={np.mean(u)}")
    print(f"V stats: min={np.min(v)}, max={np.max(v)}, mean={np.mean(v)}")

    # TODO 暂时只处理第一个time siglay，后续需要处理多个time siglay，共20个
    for o, lon in enumerate(lon_list):
        points.append([lon, lat_list[o]])
        u_values.append(u[time][siglay][o])  # 第二个0是time，0是siglay
        v_values.append(v[time][siglay][o])  # 第二个0是time，0是siglay
    # 创建shp文件
    for layer_num in range(1):  # len(siglay)
        start_time = datetime.datetime.now()
        gdal.SetConfigOption("GDAL_FILENAME_IS_UTF8", "NO")  # 为了支持中文路径，请添加下面这句代码
        gdal.SetConfigOption("SHAPE_ENCODING", "")  # 为了使属性表字段支持中文，请添加下面这句
        ogr.RegisterAll()  # 注册所有的驱动
        driver_name = "ESRI Shapefile"
        o_driver = ogr.GetDriverByName(driver_name)
        if o_driver is None:
            return
        o_data_source = o_driver.CreateDataSource(shp_path)  # 创建数据源
        if o_data_source is None:
            return
        # 创建图层，创建一个多边形图层，这里没有指定空间参考，如果需要的话，需要在这里进行指定
        geo_srs = osr.SpatialReference()
        geo_srs.SetWellKnownGeogCS("WGS84")  # srs.ImportFromEPSG(4326)
        o_layer = o_data_source.CreateLayer("pointLayer", geo_srs, ogr.wkbPoint, [])
        if o_layer is None:
            print("图层创建失败！\n")
            return
        # 创建属性字段
        for index, filed in enumerate(types):
            # 创建一个字段 ogr.OFTReal=float ogr.OFTInteger=int、ogr.OFTString=string
            o_field_name = ogr.FieldDefn(filed, ogr.OFTReal)
            o_layer.CreateField(o_field_name)
        # 获取图层
        o_defn = o_layer.GetLayerDefn()
        for node_num in range(len(lon_list)):
            feature = ogr.Feature(o_defn)
            feature.SetField('v', float(v_values[node_num]))
            feature.SetField('u', float(u_values[node_num]))
            gemo = ogr.CreateGeometryFromWkt("POINT(%s  %s)" % (str(lon_list[node_num]), str(lat_list[node_num])))
            feature.SetGeometry(gemo)
            o_layer.CreateFeature(feature)
        o_data_source.Destroy()
        print("创建shp用时:", datetime.datetime.now() - start_time)


# 删除临时目录，保证硬盘环境
def clear_temp_file(shp_path):
    path = os.path.dirname(shp_path)
    if os.path.exists(path):
        shutil.rmtree(path)


def get_file_name():
    return "temp_" + str(int(datetime.datetime.now().timestamp())) + "_" + str(random.randint(0, 10000))


def insert_raster(shp_path, fields, width=360, height=360):
    """
    shp转tiff 反距离权重插值
    :param shp_path:
    :param fields:
    :param width:
    :param height:
    :return:
    """
    dir_path = os.path.dirname(shp_path)
    for field in fields:
        output_file = os.path.join(dir_path, '%s.tif' % field)
        opts = gdal.GridOptions(format="GTiff", outputType=gdal.GDT_Float32, width=width, height=height,
                                # algorithm="invdist:power=3.5:smoothing=0.0:radius=1.0:max_points=12:min_points=0:nodata=0.0",
                                algorithm="invdist:power=3.5:smoothing=0.0:max_points=12:min_points=0:nodata=0.0",
                                zfield=field)
        gdal.Grid(destName=output_file, srcDS=shp_path, options=opts)


# 从tiff获取矩阵
def get_array_from_tiff(path, shape=None):
    dataset = gdal.Open(path)  # 打开文件
    [x, y] = [dataset.RasterXSize, dataset.RasterYSize]
    dataset.GetProjection
    if shape != None:
        [x, y] = shape
    # data = dataset.ReadAsArray(0, 0, x, y)  # 将数据写成数组，对应栅格矩阵 一排一个数组
    arrat_list = np.array(dataset.ReadAsArray(0, 0, x, y), dtype=float)
    geo_transform = dataset.GetGeoTransform()
    del dataset
    return arrat_list


# def normalization_data(array, min, max):
#     # 超过最大的就按最大的算
#     array[array > max] = max
#     # 超过最小的就按最小的算
#     array[array < min] = min
#     temp = min / ((max - min) / 255)
#     array = array / ((max - min) / 255) - temp
#     return array
def normalization_data(array, min_val, max_val):
    if max_val == min_val:
        return np.zeros_like(array)  # 如果范围为0，返回全零数组
    array = np.clip(array, min_val, max_val)  # 限制在[min_val, max_val]范围
    array = (array - min_val) / (max_val - min_val) * 255  # 线性归一化到[0, 255]
    return array.astype(np.uint8)


def get_shp_path(nc_file_path):
    """
    获取shp文件路径
    :param nc_file_path: E:\temp\LaiZhouWan\BHBIO_avg_0001.nc
    :return: shp文件路径
    """
    dir_path = os.path.dirname(nc_file_path)
    time_code = str(int(datetime.datetime.now().timestamp())) + "_" + str(random.randint(0, 10000))
    shp_path = os.path.join(dir_path, 'temp_' + time_code, f'%s.shp' % time_code)
    if not os.path.exists(shp_path):
        os.makedirs(shp_path)
    return shp_path


def tiff2arr(tiff_path):
    """
    tiff转arr
    :param tiff_path:
    :return:
    """
    dataset = gdal.Open(tiff_path)  # 打开文件
    [x, y] = [dataset.RasterXSize, dataset.RasterYSize]
    data = dataset.ReadAsArray(0, 0, x, y)  # 将数据写成数组，对应栅格矩阵 一排一个数组
    # 归一化数据0-255
    data = normalization_data(data, -1, 1)
    geo_transform = dataset.GetGeoTransform()
    header = {
        "lo1": geo_transform[0],
        "lo2": geo_transform[0] + geo_transform[1] * x,
        "la1": geo_transform[3],
        "la2": geo_transform[3] + geo_transform[5] * y,
        "nx": x,
        "ny": y,
        "min": 0,
        "max": 255,
        "dx": geo_transform[1],
        "dy": geo_transform[5]
    }
    print(header)
    del dataset
    return data


def arr2png(arr, png_path):
    """
    arr转png
    :param arr:
    :param png_path:
    :return:
    """
    value1 = []
    for i in range(arr[0].shape[0]):
        value2 = []
        for j in range(arr[0].shape[1]):
            value2.append([arr[0][i][j], arr[1][i][j], 0, 255])
        value1.append(value2)
    create_png(png_path, value1)


def create_png(png_path, values):
    # 检查并创建上级目录
    parent_dir = os.path.dirname(png_path)
    if not os.path.exists(parent_dir):
        os.makedirs(parent_dir)

    # 生成png
    png = np.array(values, np.uint8)
    im = Image.fromarray(png)
    im.save(png_path)

    # png垂直翻转
    imNew = Image.open(png_path)
    ng = imNew.transpose(Image.FLIP_TOP_BOTTOM)
    ng.save(png_path)
def check_shapefile(shp_path):
    driver = ogr.GetDriverByName("ESRI Shapefile")
    data_source = driver.Open(shp_path, 0)  # 只读模式
    if data_source is None:
        raise RuntimeError(f"无法打开 Shapefile: {shp_path}")
    
    layer = data_source.GetLayer()
    num_points = layer.GetFeatureCount()
    print(f"Shapefile 包含点数: {num_points}")
    
    for feature in layer:
        geom = feature.GetGeometryRef()
        print(f"点位置: ({geom.GetX()}, {geom.GetY()})")
        for field_name in feature.keys():
            print(f"属性 {field_name}: {feature.GetField(field_name)}")
    
    data_source.Destroy()
def calculate_bbox_from_tiff(tiff_path):
    """
    计算给定TIFF文件的边界框 (bbox)。
    
    参数:
        tiff_path (str): TIFF 文件路径。
        
    返回:
        bbox (tuple): (min_x, min_y, max_x, max_y)
    """
    dataset = gdal.Open(tiff_path)
    geotransform = dataset.GetGeoTransform()
    width = dataset.RasterXSize
    height = dataset.RasterYSize

    # 左上角 (min_x, max_y)
    min_x = geotransform[0]
    max_y = geotransform[3]

    # 右下角 (max_x, min_y)
    max_x = min_x + geotransform[1] * width
    min_y = max_y + geotransform[5] * height

    dataset = None  # 关闭文件
    return (min_x, min_y, max_x, max_y)
def extract_value_from_tiff(tiff_path, coordinates):
    """
    从 TIFF 文件中根据坐标提取值。

    参数：
        tiff_path (str): TIFF 文件路径。
        coordinates (tuple): 经纬度坐标 (lon, lat)。

    返回：
        float: 提取的值。
    """
    import rasterio
    from rasterio.features import geometry_window

    with rasterio.open(tiff_path) as src:
        lon, lat = coordinates
        # 获取像素索引
        row, col = src.index(lon, lat)
        print(f"row: {row}, col: {col}")
        # 读取像素值
        value = src.read(1)[row, col]
        print(f"value: {value}")

    return value
def uv_from_tif(siglay, time, scale,  nc_file_path, coordinates):
    """
    从两个 TIFF 文件中根据坐标提取值，返回 u 和 v 两个值。

    参数：
        siglay (int): 水平层索引。
        time (int): 时间索引。
        scale (str): 缩放比例，例如 "1*1"。
      
        nc_file_path (str): 输入 NetCDF 文件路径。
        coordinates (tuple): 提取值的经纬度坐标 (lon, lat)。

    返回：
        tuple: (png_path, bbox, (u_value, v_value))
    """
    import os

    scale = scale.split("*")
    types = ['u', 'v'] 
    shp_path = get_shp_path(nc_file_path)  # 获取 shp 文件路径
    

    nc_2_shp(nc_file_path, shp_path, siglay, time, types)  # nc 转 shp
    insert_raster(shp_path, types, int(scale[0]), int(scale[1]))  # shp 转 tiff

 
    # 删除临时数据
    dir_path = os.path.dirname(shp_path)
    u_v = []
    values = []

    for t in types:
        tiff_path = os.path.join(dir_path, t + '.tif')  # 获取 u, v 文件路径
        u_v.append(tiff2arr(tiff_path))  # 获取 u, v 矩阵

        # 根据坐标提取值
        value = extract_value_from_tiff(tiff_path, coordinates)
        values.append(value)

    # 删除临时文件
    clear_temp_file(shp_path)
    # 返回 png 路径、bbox 和提取的 u, v 值
    return  values

