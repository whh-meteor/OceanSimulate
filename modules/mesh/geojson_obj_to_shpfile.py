import geopandas as gpd
from shapely.geometry import shape

def geojson_obj_to_shp(geojson_obj, shp_output_path):
    """
    将 GeoJSON 对象转换为 Shapefile 文件

    参数:
        geojson_obj (dict): 输入的 GeoJSON 对象
        shp_output_path (str): 输出的 Shapefile 文件路径
    """
    try:
        # 提取 features 的 geometry 和 properties
        features = geojson_obj.get('features', [])
        
        # 判断 features 是否是列表
        if isinstance(features, dict):  # 如果 features 是字典，说明数据格式错误
            features = [features]  # 将其转换为列表

        if not features:
            print("GeoJSON 中没有有效的 features 数据")
            return

        # 解析几何数据
        geometries = [shape(feature['geometry']) for feature in features]
        properties = [feature['properties'] for feature in features]
        
        # 检查是否正确解析了几何数据
        if not geometries:
            print("没有有效的几何数据")
            return
        
        # 创建 GeoDataFrame
        gdf = gpd.GeoDataFrame(properties, geometry=geometries)

        # 打印 GeoDataFrame 内容，以确认几何数据
        print("GeoDataFrame 内容:")
        print(gdf.head())

        # 设置坐标系为 WGS84
        gdf.set_crs("EPSG:4326", allow_override=True, inplace=True)
        
        # 保存为 Shapefile
        gdf.to_file(shp_output_path, driver='ESRI Shapefile')
        print(f"成功将 GeoJSON 对象转换为 Shapefile，文件路径: {shp_output_path}")
    except Exception as e:
        print(f"转换失败: {e}")