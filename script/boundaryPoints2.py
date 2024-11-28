import json
from shapely.geometry import shape, Polygon, MultiPolygon,shape, mapping
from shapely.ops import polygonize, linemerge, unary_union, polygonize
from functools import partial
import pyproj
# Step 1: 多边形转点并去重
def convert_polygons_to_points(geojson_file,output_file):
    with open(geojson_file, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    points = []
    seen_ids = set()
    
    for feature in geojson_data['features']:
        if feature['geometry']['type'] == 'Polygon':
            polygon = shape(feature['geometry'])
            for point_id, point_props in enumerate(feature['properties']['points_properties']):
                point = {
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': polygon.exterior.coords[point_id]
                    },
                    'properties': {
                        'id': point_props['id'],
                        'depth': point_props['depth'],
                        'value': point_props['value']
                    }
                }
                if point['properties']['id'] not in seen_ids:
                    points.append(point)
                    seen_ids.add(point['properties']['id'])
    
    output_file = output_file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({'type': 'FeatureCollection', 'features': points}, f, indent=2, ensure_ascii=False)
    
    return output_file

# Step 2: 多边形融合并保留孔洞
def merge_polygons_with_holes(geojson_file, output_file):
    with open(geojson_file, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    polygons = []
    for feature in geojson_data['features']:
        polygons.append(shape(feature['geometry']))
    
    merged_polygon = unary_union(polygons)
    
    if isinstance(merged_polygon, MultiPolygon):
        merged_features = [{'type': 'Feature', 'geometry': mapping(poly)} for poly in merged_polygon.geoms]
    else:
        merged_features = [{'type': 'Feature', 'geometry': mapping(merged_polygon)}]
    
    feature_collection = {'type': 'FeatureCollection', 'features': merged_features}
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(feature_collection, f, indent=2, ensure_ascii=False)
    
    return output_file
# Step 3: 多边形转线，提取线段
def convert_polygons_to_lines(geojson_file, output_file):
    with open(geojson_file, 'r', encoding='utf-8') as f:
        geojson_data = json.load(f)
    
    polygons = [shape(feature['geometry']) for feature in geojson_data['features']]
    merged_polygon = unary_union(polygons)
    
    if isinstance(merged_polygon, MultiPolygon):
        boundary_lines = merged_polygon.boundary
    else:
        boundary_lines = merged_polygon.boundary
    
    lines = [{'type': 'Feature', 'geometry': mapping(boundary_lines)}]
    
    feature_collection = {'type': 'FeatureCollection', 'features': lines}
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(feature_collection, f, indent=2, ensure_ascii=False)
    
    return output_file


# Step 4: 点和线的相交分析
def analyze_points_and_lines(points_file, lines_file, output_file):
    with open(points_file, 'r', encoding='utf-8') as f:
        points_data = json.load(f)
    
    with open(lines_file, 'r', encoding='utf-8') as f:
        lines_data = json.load(f)
    
    points = [shape(feature['geometry']) for feature in points_data['features']]
    lines = [shape(feature['geometry']) for feature in lines_data['features']]
    
    # Perform intersection analysis
    intersected_points = []
    
    for point_feature in points_data['features']:
        point_geometry = shape(point_feature['geometry'])
        point_properties = point_feature['properties']
        point_id = point_properties['id']
        
        for line_feature in lines_data['features']:
            line_geometry = shape(line_feature['geometry'])
            if point_geometry.intersects(line_geometry):
                intersection = point_geometry.intersection(line_geometry)
                if intersection.geom_type == 'Point':
                    # Store intersected point with its properties
                    intersected_points.append({
                        'type': 'Feature',
                        'geometry': {
                            'type': 'Point',
                            'coordinates': (intersection.x, intersection.y)
                        },
                        'properties': point_properties
                    })
    
    # Save intersected points data to output file
    output_data = {'type': 'FeatureCollection', 'features': intersected_points}
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    return output_file


# Step 5: 更新三角形顶点属性
def update_triangle_vertex_properties(triangle_file, updated_points_file,output_file):
    with open(triangle_file, 'r', encoding='utf-8') as f:
        triangles_data = json.load(f)
    
    with open(updated_points_file, 'r', encoding='utf-8') as f:
        updated_points_data = json.load(f)
    
    for triangle in triangles_data['features']:
        triangle_points = triangle['properties']['points_properties']
        for point_prop in triangle_points:
            for updated_point in updated_points_data['features']:
                if updated_point['properties']['id'] == point_prop['id']:
                    point_prop['value'] = 1  # Update value to 1 based on intersection analysis
    
    output_file = output_file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(triangles_data, f, indent=2, ensure_ascii=False)
    
    return output_file



# 测试每个函数的输出
if __name__ == '__main__':
    input_geojson_file = r'F:\Desktop\杭州湾.geojson'
    
    # Step 1: 多边形转点并去重
    points_file = convert_polygons_to_points(input_geojson_file,"F:/Desktop/Step1_Points.json")
    print(f'Step 1 output saved to {points_file}')
    
    # Step 2: 多边形融合并保留孔洞
    merged_polygons_file = merge_polygons_with_holes(input_geojson_file,"F:/Desktop/Step2_Polygons.geojson")
    print(f'Step 2 output saved to {merged_polygons_file}')
    
    # # Step 3: 多边形转线，提取线段
    lines_file = convert_polygons_to_lines(merged_polygons_file,"F:/Desktop/Step3_Lines.geojson")
    print(f'Step 3 output saved to {lines_file}')
    
    # Step 4: 点和线的相交分析
    updated_points_file = analyze_points_and_lines(points_file, lines_file,"F:/Desktop/Step4_PointsInLines.geojson")
    print(f'Step 4 output saved to {updated_points_file}')
    
    # Step 5: 更新三角形顶点属性
    updated_triangles_file = update_triangle_vertex_properties(input_geojson_file, updated_points_file,"F:/Desktop/Step5_TrianglesWithUpdated.geojson")
    print(f'Step 5 output saved to {updated_triangles_file}')

    # 定时器
    import time
    time.sleep(3)
    # 删除中间文件
    import os
    os.remove(points_file)
    os.remove(merged_polygons_file)
    os.remove(lines_file)
    # os.remove(updated_points_file)
    # os.remove(updated_triangles_file)
