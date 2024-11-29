
import json
from osgeo import gdal, ogr
import numpy as np
 
# 获取GeoJSON的四至范围
def get_geojson_bbox(geojson_data):
    min_lon, min_lat = float('inf'), float('inf')
    max_lon, max_lat = float('-inf'), float('-inf')

    for feature in geojson_data['features']:
        coordinates = feature['geometry']['coordinates'][0]
        for lon, lat in coordinates:
            min_lon = min(min_lon, lon)
            max_lon = max(max_lon, lon)
            min_lat = min(min_lat, lat)
            max_lat = max(max_lat, lat)

    return min_lon, min_lat, max_lon, max_lat
# 获取GeoJSON的四至范围
def get_geojson_bbox_extent(geojson_data, expansion_value=0):
    min_lon, min_lat = float('inf'), float('inf')
    max_lon, max_lat = float('-inf'), float('-inf')

    for feature in geojson_data['features']:
        coordinates = feature['geometry']['coordinates'][0]
        for lon, lat in coordinates:
            min_lon = min(min_lon, lon)
            max_lon = max(max_lon, lon)
            min_lat = min(min_lat, lat)
            max_lat = max(max_lat, lat)

    # 向外扩张四至范围
    return min_lon - expansion_value, min_lat - expansion_value, max_lon + expansion_value, max_lat + expansion_value

# 裁剪DEM文件
def clip_dem(dem_file, bbox, output_file):
    min_lon, min_lat, max_lon, max_lat = bbox
    gdal.Warp(output_file, dem_file, format="GTiff", 
              outputBounds=(min_lon, min_lat, max_lon, max_lat))

# 读取裁剪后的DEM
def read_dem_grd(file_path):
    dataset = gdal.Open(file_path)
    dem_data = dataset.ReadAsArray()
    gt = dataset.GetGeoTransform()
    return dem_data, gt

# 获取DEM中的值
def get_dem_value(dem_data, gt, lon, lat):
    px = int((lon - gt[0]) / gt[1])
    py = int((lat - gt[3]) / gt[5])
    
    if 0 <= px < dem_data.shape[1] and 0 <= py < dem_data.shape[0]:
        return dem_data[py, px]
    else:
        return None
import ast 
# 更新GeoJSON中的点属性

def update_geojson_with_dem(geojson_data, dem_data, gt):
    # print(type(geojson_data)) 
    # print(type(geojson_data['features'][0]['id']))  
    # print(type(geojson_data['features'][0]['properties']['points_properties']))  

    for feature in geojson_data['features']:
        coordinates = feature['geometry']['coordinates'][0]
        
        # 将 points_properties 从字符串转换为列表
        points_properties_str = feature['properties']['points_properties']
        points_properties = ast.literal_eval(points_properties_str)

        for i, point_property in enumerate(points_properties):
            lon, lat = coordinates[i][:2]
            dem_value = get_dem_value(dem_data, gt, lon, lat)
            if dem_value is not None:
                # point_property['depth'] = float(dem_value) # 更新点属性中的depth值
                if float(dem_value) > 0:
                    point_property['depth'] = 0  # 当值大于0时，将其设置为0
                    print(f"警告：原始深度值 {dem_value} 大于0，已被设置为0。")
                else:
                    point_property['depth'] = float(dem_value)  # 更新点属性中的depth值

        # 更新回原始数据结构
        feature['properties']['points_properties'] = points_properties
    
    return geojson_data

# 保存更新后的GeoJSON
def save_geojson(geojson_data, output_file):
    geojson_data = convert_numpy_types(geojson_data)  # 转换numpy类型
    return geojson_data
    with open(output_file, 'w') as f:
        json.dump(geojson_data, f, indent=2)


# 将numpy类型转换为Python原生类型
def convert_numpy_types(data):
    if isinstance(data, dict):
        return {k: convert_numpy_types(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_numpy_types(item) for item in data]
    elif isinstance(data, np.generic):
        return data.item()
    else:
        return data


def updateDepth(dem_file,geojson_data,output_file,output_dem_file):
    print("GDAL version:", gdal.__version__)
   
    # # 示例使用
    # dem_file = r'F:\Desktop\【LTGK】海洋一所\240531084643LTX\1开发域-2022\3编码实现\后端\Python-Flask\static\dem\topo15.grd'
    # geojson_file = r'F:\Desktop\【LTGK】海洋一所\240531084643LTX\1开发域-2022\3编码实现\后端\Python-Flask\static\dem\mesh.json'
    # output_file = r'F:\Desktop\【LTGK】海洋一所\240531084643LTX\1开发域-2022\3编码实现\后端\Python-Flask\static\dem\mesh_dem.json'
    # output_dem_file = r'F:\Desktop\【LTGK】海洋一所\240531084643LTX\1开发域-2022\3编码实现\后端\Python-Flask\static\dem\clipped_dem.tif'

    # # 读取GeoJSON文件
    # with open(geojson_file, 'r') as f:
    #     geojson_data = json.load(f)

    # 获取GeoJSON的四至范围
    # bbox = get_geojson_bbox(geojson_data)
    bbox = get_geojson_bbox_extent(geojson_data, expansion_value=0.01)  # 向外扩张0.01度


    # 裁剪DEM
    clip_dem(dem_file, bbox, output_dem_file)

    # 读取裁剪后的DEM
    dem_data, gt = read_dem_grd(output_dem_file)

    # 更新GeoJSON中的点属性
    updated_geojson = update_geojson_with_dem(geojson_data, dem_data, gt)
    print("成功更新水深值")
    # print(updated_geojson)
    # 保存更新后的GeoJSON
    return   save_geojson(updated_geojson, output_file)

    