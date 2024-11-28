
import netCDF4 as nc 
from netCDF4 import Dataset, num2date
import numpy as np
import json
from datetime import datetime, timedelta
from pyproj import Proj, transform
# 获取NetCDF文件中的时间列表并转换为JSON格式
def extract_time_from_nc(nc_file_path):
      # 打开NetCDF文件
    with nc.Dataset(nc_file_path, 'r') as dataset:
  # 提取时间变量
        time_var = dataset.variables['time'][:]
        time_units = "hours since 1900-01-01"
        
        # 解析时间单位，获取时间参考点
        time_units_split = time_units.split(" since ")
        time_reference = time_units_split[1]  # 获取基准时间部分

        # 将时间参考点转换为datetime对象（添加时分秒部分）
        time_reference = datetime.strptime(time_reference + " 00:00:00", "%Y-%m-%d %H:%M:%S")

        # 计算并返回时间列表
        time_data = []
        for idx, time_value in enumerate(time_var):
            # 将time_value转换为float类型以避免错误
            time_value = float(time_value)
            time_point = time_reference + timedelta(hours=time_value)  # 使用小时单位
            # 将时间索引和实际时间以字典形式保存
            time_data.append({"index": idx, "time": time_point.strftime('%Y-%m-%d %H:%M:%S')})

    return time_data
# 读取NetCDF文件并提取u、v数据
def extract_uv(file_path, time_idx, siglay_idx):
    ds = nc.Dataset(file_path)
    
    u = ds.variables['u'][time_idx, siglay_idx, :]
    v = ds.variables['v'][time_idx, siglay_idx, :]
    
    lon = ds.variables['xc'][:]
    lat = ds.variables['yc'][:]
    
    return lon, lat, u, v

# 将UTM坐标转换为WGS84
def utm_to_wgs84(lon, lat,zone_number=40):
  
    central_meridian = zone_number * 3  # 对于3度带，每个带的中央经线是带号乘以3

    gauss_kruger = Proj(proj='tmerc', lat_0=0, lon_0=central_meridian, k=1, x_0=500000, y_0=0, ellps='WGS84', datum='WGS84')
    wgs84 = Proj(proj='latlong', datum='WGS84')
    lon_wgs84, lat_wgs84 = transform(gauss_kruger, wgs84, lon, lat)
    # transformer = pyproj.Transformer.from_crs(f"EPSG:326{zone}", "EPSG:4326")
    # lon_wgs84, lat_wgs84 = transformer.transform(lon, lat)
    return lon_wgs84, lat_wgs84






# 将提取的u、v数据转换为GeoJSON格式
def uv_to_geojson(lon, lat, u, v):
    features = []
    for i in range(len(lon)):
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [lon[i], lat[i]]
            },
            "properties": {
                "u": float(u[i]),
                "v": float(v[i])
            }
        })
    
    geojson_data = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # with open(output_file, 'w') as f:
    #     json.dump(geojson_data, f, indent=4)
    return geojson_data


 

 
def get_pltf_timeList(nc_path):
    timelist =extract_time_from_nc(nc_path)
    return timelist
def get_pltf_points(nc_path, time_idx, siglay_idx):

    # 提取u、v数据并转换为GeoJSON
    lon, lat, u, v = extract_uv(nc_path, time_idx, siglay_idx)
    lon_wgs84, lat_wgs84 = utm_to_wgs84(lon, lat)
    return uv_to_geojson(lon_wgs84, lat_wgs84, u, v)
    
    
 