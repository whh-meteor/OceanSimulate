# import geojson
# from shapely.geometry import shape, LineString, MultiLineString, Polygon
# from shapely.ops import unary_union, polygonize

# def extract_boundary_points(input_file: str, output_file: str):
#     # 读取GeoJSON文件
#     with open(input_file, 'r') as f:
#         data = geojson.load(f)

#     # 提取所有的边
#     edges = []
#     for feature in data['features']:
#         polygon = shape(feature['geometry'])
#         coords = list(polygon.exterior.coords[:-1])  # 忽略最后一个重复的坐标
#         for i in range(len(coords)):
#             edges.append((coords[i], coords[(i + 1) % len(coords)]))

#     # 使用unary_union合并所有边，并使用polygonize创建多边形
#     merged_edges = unary_union([LineString(edge) for edge in edges])
#     polygons = list(polygonize(merged_edges))

#     # 提取最外层的多边形
#     outer_boundary = unary_union(polygons).boundary

#     # 提取边界点
#     boundary_coords = set(outer_boundary.coords)

#     # 修改最外层边界点的属性value为1
#     for feature in data['features']:
#         polygon = shape(feature['geometry'])
#         coords = list(polygon.exterior.coords[:-1])  # 忽略最后一个重复的坐标
#         for i, coord in enumerate(coords):
#             if coord in boundary_coords:
#                 feature['properties']['points_properties'][i]['value'] = 1

#     # 将修改后的数据写入GeoJSON文件
#     with open(output_file, 'w') as f:
#         geojson.dump(data, f, indent=2)

#     print(f"修改后的GeoJSON文件已保存为{output_file}")



# # 调用函数
# input_file = 'F:/Desktop/triangles.json'
# output_file = 'F:/Desktop/boundary_points.geojson'
# extract_boundary_points(input_file, output_file)


import geojson
from shapely.geometry import shape, LineString, MultiLineString
from shapely.ops import unary_union, polygonize

def extract_boundary_points(input_file: str, output_file: str):
    # 读取GeoJSON文件
    with open(input_file, 'r') as f:
        data = geojson.load(f)

    # 提取所有的边
    edges = []
    for feature in data['features']:
        polygon = shape(feature['geometry'])
        coords = list(polygon.exterior.coords[:-1])  # 忽略最后一个重复的坐标
        for i in range(len(coords)):
            edges.append((coords[i], coords[(i + 1) % len(coords)]))

    # 使用unary_union合并所有边，并使用polygonize创建多边形
    merged_edges = unary_union([LineString(edge) for edge in edges])
    polygons = list(polygonize(merged_edges))

    # 提取所有不连续三角网的外边界点
    boundary_coords = set()
    for poly in polygons:
        boundary_coords.update(poly.exterior.coords)

    # 修改最外层边界点的属性value为1，内部点保持为0
    for feature in data['features']:
        polygon = shape(feature['geometry'])
        coords = list(polygon.exterior.coords[:-1])  # 忽略最后一个重复的坐标
        for i, coord in enumerate(coords):
            # 确保点属性的顺序和数量与坐标顺序匹配
            if coord in boundary_coords:
                feature['properties']['points_properties'][i]['value'] = 1
            else:
                feature['properties']['points_properties'][i]['value'] = 0

    # 将修改后的数据写入GeoJSON文件
    with open(output_file, 'w') as f:
        geojson.dump(data, f, indent=2)

    print(f"修改后的GeoJSON文件已保存为{output_file}")

# 调用函数
input_file = 'F:/Desktop/triangles.json'
output_file = 'F:/Desktop/boundary_points.geojson'
extract_boundary_points(input_file, output_file)
