
import gmsh
import meshio
import os

def initialize_gmsh(model_name):
    gmsh.initialize(interruptible=False) # 非主线程调用
    gmsh.model.add(model_name)
def convert_geojson_to_custom_format(geojson_data):
    result = []
    for feature in geojson_data['features']:
        lon, lat = feature['geometry']['coordinates']
        # value = feature['properties']['value']
        value = 1
        result.append(f"{lon} {lat} {value}")
    return result
def read_shoreline_data_from_generated(shoreline_data, shoreline_lc, current_tag):
    shoreline_points = []
    shoreline_identifiers = []
    for line in shoreline_data:
        x, y, identifier = map(float, line.split())
        gmsh.model.geo.addPoint(x, y, 0, shoreline_lc, current_tag)
        shoreline_points.append(current_tag)
        shoreline_identifiers.append(identifier)
        current_tag += 1
    return shoreline_points, shoreline_identifiers, current_tag
def create_shoreline_lines(shoreline_points, current_tag):
    shoreline_lines = []
    for i in range(len(shoreline_points)):
        start = shoreline_points[i]
        end = shoreline_points[(i + 1) % len(shoreline_points)]
        gmsh.model.geo.addLine(start, end, current_tag)
        shoreline_lines.append(current_tag)
        current_tag += 1
    return shoreline_lines, current_tag
# 修改后的读取函数，直接处理JSON对象
# def read_inner_curve_data_from_json(json_data, current_tag):
#     inner_curve_points = []
#     inner_curve_identifiers = []
#     inner_curve_loops = []

#     for curve_data in json_data:
#         num_points = curve_data['num_points']
#         flag = curve_data['flag']
#         mesh_size = curve_data['mesh_size']
        
#         polygon_points = []
#         for point in curve_data['points']:
#             x, y, identifier = point['x'], point['y'], point['identifier']
#             gmsh.model.geo.addPoint(x, y, 0, mesh_size, current_tag)
#             polygon_points.append(current_tag)
#             inner_curve_points.append(current_tag)
#             inner_curve_identifiers.append(identifier)
#             current_tag += 1
        
#         polygon_lines, current_tag = create_polygon_lines(polygon_points, current_tag)
#         gmsh.model.geo.addCurveLoop(polygon_lines, current_tag)
#         loop_id = current_tag
#         inner_curve_loops.append(loop_id)
#         current_tag += 1
        
#         if flag == 1:
#             gmsh.model.geo.addPlaneSurface([loop_id], current_tag)
#             current_tag += 1

#     return inner_curve_loops, inner_curve_points, inner_curve_identifiers, current_tag

# 修改后的读取函数，处理新的数据格式
def read_inner_curve_data_from_json(new_json_data, current_tag):
    inner_curve_points = []
    inner_curve_identifiers = []
    inner_curve_loops = []

    for curve_data in new_json_data:
        num_points = curve_data['num_points']
        flag = curve_data['flag']
        mesh_size = curve_data['mesh_size']
        
        polygon_points = []
        for i in range(num_points):
            x, y = curve_data['points'][i][:2]  # 获取前两个元素作为 x 和 y
            identifier = curve_data['flag']  # 使用提供的 identifier
            gmsh.model.geo.addPoint(x, y, 0, mesh_size, current_tag)
            polygon_points.append(current_tag)
            inner_curve_points.append(current_tag)
            inner_curve_identifiers.append(identifier)
            current_tag += 1
        
        polygon_lines, current_tag = create_polygon_lines(polygon_points, current_tag)
        gmsh.model.geo.addCurveLoop(polygon_lines, current_tag)
        loop_id = current_tag
        inner_curve_loops.append(loop_id)
        current_tag += 1
        
        if flag == 1:
            gmsh.model.geo.addPlaneSurface([loop_id], current_tag)
            current_tag += 1

    return inner_curve_loops, inner_curve_points, inner_curve_identifiers, current_tag

def create_polygon_lines(polygon_points, current_tag):
    polygon_lines = []
    for i in range(len(polygon_points)):
        start = polygon_points[i]
        end = polygon_points[(i + 1) % len(polygon_points)]
        gmsh.model.geo.addLine(start, end, current_tag)
        polygon_lines.append(current_tag)
        current_tag += 1
    return polygon_lines, current_tag

def create_surface(outer_loop_tag, inner_curve_loops, current_tag):
    gmsh.model.geo.addPlaneSurface([outer_loop_tag] + inner_curve_loops, current_tag)
    return current_tag + 1

def generate_mesh():
    gmsh.model.geo.synchronize()
    gmsh.model.mesh.generate(2)

def finalize_gmsh(output_filename):
    gmsh.write(output_filename)
    # gmsh.fltk.run()
    gmsh.finalize()
# 读取 .msh 文件
def read_msh_file(msh_file):
    mesh = meshio.read(msh_file)
    points = mesh.points[:, :2]  # 只保留 X, Y 坐标
    cells = mesh.cells_dict.get('triangle', [])  # 获取三角形单元
    return points, cells

# 创建简化的 .mesh 文件
def create_simple_mesh_file(mesh_file, points, cells):
    num_points = len(points)
    num_cells = len(cells)

    with open(mesh_file, 'w') as f:
        f.write(f'100079  1000  {num_points}  PROJCS["UTM-50",GEOGCS["Unused",DATUM["UTM Projections",'
                'SPHEROID["WGS 1984",6378137,298.257223563]],PRIMEM["Greenwich",0],UNIT["Degree",'
                '0.0174532925199433]],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",500000],'
                'PARAMETER["False_Northing",0],PARAMETER["Central_Meridian",123],PARAMETER["Scale_Factor",0.9996],'
                'PARAMETER["Latitude_Of_Origin",0],UNIT["Meter",1]]\n')

        for i, point in enumerate(points):
            x, y = point[0], point[1]
            f.write(f"{i + 1} {x:.15f} {y:.15f} 0.000000 0\n")

        f.write(f"{num_cells} 3 21\n")
        for i, cell in enumerate(cells):
            f.write(f"{i + 1} {cell[0] + 1} {cell[1] + 1} {cell[2] + 1}\n")
import time
import os
# 删除文件
def delete_files(*files):
    for file in files:
        if os.path.exists(file):
            # os.remove(file)
            # print(f"已删除文件: {file}")
            try:
                os.remove(file)
            except PermissionError:
                # 如果遇到权限错误，尝试等待一段时间后重试
                print(f"文件 {file} 被占用，等待一会儿再删除...")
                time.sleep(1)  # 等待1秒
                try:
                    os.remove(file)
                except Exception as e:
                    print(f"删除文件失败: {e}")
def refinement_mesh(geojson_data,mesh_size,inner_curve_data,mesh_out_file):
    # 初始化 Gmsh
    model_name = "modified_model"
    initialize_gmsh(model_name)

    shoreline_lc = mesh_size
    inner_curve_lc = 1000
    current_tag = 1
    # 读取岸线Geojson数据
    formatted_data = convert_geojson_to_custom_format(geojson_data)
    for line in formatted_data:
        print(line)
    # 调用时使用转换后的格式化数据
    shoreline_points, shoreline_identifiers, current_tag = read_shoreline_data_from_generated(formatted_data, shoreline_lc, current_tag)
    # 创建岸线多边形的边界线
    shoreline_lines, current_tag = create_shoreline_lines(shoreline_points, current_tag)

    # 创建岸线多边形的曲线环
    gmsh.model.geo.addCurveLoop(shoreline_lines, current_tag)
    outer_loop_tag = current_tag
    current_tag += 1

    # 读取内部加密曲线数据
    inner_curve_loops, inner_curve_points, inner_curve_identifiers, current_tag = read_inner_curve_data_from_json(inner_curve_data, current_tag)

    # 创建主面
    current_tag = create_surface(outer_loop_tag, inner_curve_loops, current_tag)

    # 生成网格
    generate_mesh()

    # 保存生成的网格并结束
    msh_files = "files.msh"
    finalize_gmsh(msh_files)
     # 读取 .msh 文件提取点和单元信息
    mesh_points, cells = read_msh_file(msh_files)
    # 创建简化的 .mesh 文件
 
    mesh_out_file = mesh_out_file
    create_simple_mesh_file(mesh_out_file, mesh_points, cells)

    # 删除中间文件
    delete_files( msh_files)
    return mesh_out_file
    # # 打印标识符（可选）
    # print("岸线标识符:", shoreline_identifiers)
    # print("内部曲线标识符:", inner_curve_identifiers)

if __name__ == "__main__":
    geojson_data = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.85700950339825,
                    38.83188663435498
                ]
            },
            "properties": {
                "id": 1,
                "depth": 48.031421,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.89152939832498,
                    38.83103659789209
                ]
            },
            "properties": {
                "id": 2,
                "depth": 48.154379,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.92604782720132,
                    38.830176377210755
                ]
            },
            "properties": {
                "id": 3,
                "depth": 48.30311,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.94868772888394,
                    38.82059757399525
                ]
            },
            "properties": {
                "id": 4,
                "depth": 48.892689,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.94757404123925,
                    38.793598476074344
                ]
            },
            "properties": {
                "id": 5,
                "depth": 49.854774,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.94646184572109,
                    38.76659922611931
                ]
            },
            "properties": {
                "id": 6,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.94535114015642,
                    38.73959982420133
                ]
            },
            "properties": {
                "id": 7,
                "depth": 50.454956,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.94424192237693,
                    38.71260027039161
                ]
            },
            "properties": {
                "id": 8,
                "depth": 51.242326,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.943134190219,
                    38.685600564761366
                ]
            },
            "properties": {
                "id": 9,
                "depth": 51.827182,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.94202794152372,
                    38.65860070738187
                ]
            },
            "properties": {
                "id": 10,
                "depth": 52.112801,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.94092317413686,
                    38.631600698324384
                ]
            },
            "properties": {
                "id": 11,
                "depth": 52.563476,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.93981988590888,
                    38.6046005376602
                ]
            },
            "properties": {
                "id": 12,
                "depth": 53.088428,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.93871807469489,
                    38.5776002254606
                ]
            },
            "properties": {
                "id": 13,
                "depth": 53.656415,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.93761773835466,
                    38.55059976179694
                ]
            },
            "properties": {
                "id": 14,
                "depth": 54.232453,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.93651887475261,
                    38.52359914674056
                ]
            },
            "properties": {
                "id": 15,
                "depth": 54.808491,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.93542148175776,
                    38.49659838036281
                ]
            },
            "properties": {
                "id": 16,
                "depth": 55,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.93432555724377,
                    38.46959746273513
                ]
            },
            "properties": {
                "id": 17,
                "depth": 55,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.93323109908889,
                    38.442596393928895
                ]
            },
            "properties": {
                "id": 18,
                "depth": 55.107103,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.92106099673173,
                    38.42488158340379
                ]
            },
            "properties": {
                "id": 19,
                "depth": 55,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.88673619625487,
                    38.42573284966636
                ]
            },
            "properties": {
                "id": 20,
                "depth": 54.354777,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.85240995563242,
                    38.4265740774797
                ]
            },
            "properties": {
                "id": 21,
                "depth": 53.581043,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.81808229188466,
                    38.427405265571046
                ]
            },
            "properties": {
                "id": 22,
                "depth": 52.80731,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.78375322203634,
                    38.42822641268273
                ]
            },
            "properties": {
                "id": 23,
                "depth": 52.033577,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.74942276311658,
                    38.42903751757221
                ]
            },
            "properties": {
                "id": 24,
                "depth": 51.316804,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.71509093215883,
                    38.429838579012014
                ]
            },
            "properties": {
                "id": 25,
                "depth": 50.575049,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.6807577462009,
                    38.430629595789775
                ]
            },
            "properties": {
                "id": 26,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.64642322228478,
                    38.43141056670828
                ]
            },
            "properties": {
                "id": 27,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.61208737745667,
                    38.432181490585386
                ]
            },
            "properties": {
                "id": 28,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.57775022876689,
                    38.43294236625411
                ]
            },
            "properties": {
                "id": 29,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.54341179326987,
                    38.43369319256256
                ]
            },
            "properties": {
                "id": 30,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.49762524039127,
                    38.434678660006426
                ]
            },
            "properties": {
                "id": 31,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.4985570109169,
                    38.46168953178921
                ]
            },
            "properties": {
                "id": 32,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.49949003024487,
                    38.488700259567324
                ]
            },
            "properties": {
                "id": 33,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.50042430018279,
                    38.515710843281624
                ]
            },
            "properties": {
                "id": 34,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.5013598225421,
                    38.54272128287305
                ]
            },
            "properties": {
                "id": 35,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.50229659913825,
                    38.569731578282585
                ]
            },
            "properties": {
                "id": 36,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.5032346317906,
                    38.59674172945124
                ]
            },
            "properties": {
                "id": 37,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.5041739223225,
                    38.62375173632005
                ]
            },
            "properties": {
                "id": 38,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.50511447256116,
                    38.65076159883016
                ]
            },
            "properties": {
                "id": 39,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.5060562843379,
                    38.6777713169227
                ]
            },
            "properties": {
                "id": 40,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.50699935948795,
                    38.70478089053889
                ]
            },
            "properties": {
                "id": 41,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.50794369985056,
                    38.73179031961995
                ]
            },
            "properties": {
                "id": 42,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.50888930726896,
                    38.75879960410718
                ]
            },
            "properties": {
                "id": 43,
                "depth": 50,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.50983618359042,
                    38.78580874394192
                ]
            },
            "properties": {
                "id": 44,
                "depth": 49.710655,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.51078433066623,
                    38.81281773906553
                ]
            },
            "properties": {
                "id": 45,
                "depth": 48.401131,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.51173375035174,
                    38.83982658941947
                ]
            },
            "properties": {
                "id": 46,
                "depth": 47.173121,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.54626734835172,
                    38.83907846389125
                ]
            },
            "properties": {
                "id": 47,
                "depth": 47.330086,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.58079965444539,
                    38.83832014187634
                ]
            },
            "properties": {
                "id": 48,
                "depth": 47.571697,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.6153306511989,
                    38.837551624532004
                ]
            },
            "properties": {
                "id": 49,
                "depth": 47.757381,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.64986032118263,
                    38.83677291303096
                ]
            },
            "properties": {
                "id": 50,
                "depth": 48.056084,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.68438864697116,
                    38.83598400856141
                ]
            },
            "properties": {
                "id": 51,
                "depth": 48.358148,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.71891561114334,
                    38.83518491232701
                ]
            },
            "properties": {
                "id": 52,
                "depth": 48.429417,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.75344119628234,
                    38.83437562554686
                ]
            },
            "properties": {
                "id": 53,
                "depth": 48.169437,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.78796538497573,
                    38.83355614945556
                ]
            },
            "properties": {
                "id": 54,
                "depth": 47.902344,
                "value": 2
            }
        },
        {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [
                    119.82248815981553,
                    38.83272648530311
                ]
            },
            "properties": {
                "id": 55,
                "depth": 47.87436,
                "value": 2
            }
        }
    ]
}
    inner_curve_data = [
    {
        "num_points": 4,
        "flag": 1,
        "mesh_size": 0.01,
        "points": [
            {"x": 119.80830000908423, "y": 38.75331810333401, "identifier": 0},
            {"x": 119.80830000908423, "y": 38.71992021215772, "identifier": 0},
            {"x": 119.85509903346895, "y": 38.71992021215772, "identifier": 0},
            {"x": 119.85509903346895, "y": 38.75331810333401, "identifier": 0}
        ]
    },
    {
        "num_points": 4,
        "flag": 1,
        "mesh_size": 0.01,
        "points": [
            {"x": 119.71420409835827, "y": 38.804161617472545, "identifier": 0},
            {"x": 119.71420409835827, "y": 38.736232761246214, "identifier": 0},
            {"x": 119.78938125454869, "y": 38.736232761246214, "identifier": 0},
            {"x": 119.78938125454869, "y": 38.804161617472545, "identifier": 0}
        ]
    }
]
   
    refinement_mesh(geojson_data,inner_curve_data)
