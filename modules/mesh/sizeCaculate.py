
import json
import math

def calculate_mesh_size(geojson_data, mode="average"):
    """
    计算GeoJSON中所有三角形的网格边长（mesh_size）。
    
    :param geojson_data: GeoJSON 格式的数据，其中包含多个三角形
    :param mode: 计算模式，可选 "average"（平均值）, "min"（最短边）, "max"（最长边）
    :return: 所有三角形的边长统计值
    """
    def calculate_edge_length(p1, p2):
        """计算两点之间的欧几里得距离"""
        return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
    
    all_edge_lengths = []
    
    for feature in geojson_data['features']:
        # 获取三角形的坐标点
        coordinates = feature['geometry']['coordinates'][0]
        
        # 确保是三角形，包含 3 个点
        if len(coordinates) != 4:
            raise ValueError("Feature is not a triangle.")
        
        # 计算三角形的每条边长
        edge_lengths = [
            calculate_edge_length(coordinates[0], coordinates[1]),
            calculate_edge_length(coordinates[1], coordinates[2]),
            calculate_edge_length(coordinates[2], coordinates[0])
        ]
        
        # 收集所有边长
        all_edge_lengths.extend(edge_lengths)
    
    # 根据 mode 返回结果
    if mode == "average":
        return sum(all_edge_lengths) / len(all_edge_lengths)
    elif mode == "min":
        return min(all_edge_lengths)
    elif mode == "max":
        return max(all_edge_lengths)
    else:
        raise ValueError("Invalid mode. Choose 'average', 'min', or 'max'.")