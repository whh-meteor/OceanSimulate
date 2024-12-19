import base64
from flask import Flask, Response, request, send_file, jsonify, make_response
from modules.mesh.services import erase_geojson_with_shp,get_larger_file_index,erase_geojson_with_shp_geopandas,shp_to_geojson_with_geopandas,erase_geojson_with_shp_gdal,GenerateMesh,Geojson_to_Mesh,transPoint2WGS84,dat_to_geojson_with_conversion,Mesh_nodes_to_Triangle_Json,bln_to_geojson,LinesJosn2WGS84
from io import BytesIO
from werkzeug.utils import secure_filename
from flask_cors import CORS
from datetime import datetime, timedelta
from modules.tide.predict_with_tpxo import predict_tide
from modules.tide.obc_nc import make_obc_nc
from modules.depth.updateDEM2json import updateDepth
from modules.mesh.refinement_mesh import refinement_mesh,delete_files
from modules.mesh.updatemesh import  reindex_mesh,reindex_mesh_withfile,reindex_mesh_nofile
from modules.wind.gen_wind_nc import generate_wind_netcdf

from modules.thematic.gen_maps import get_coastline_from_npz
from modules.mesh.extra_bd_attr import extra_bd_attr
from modules.mesh.sizeCaculate import calculate_mesh_size
import numpy as np
import json
import os
import uuid
import configparser
import sys
from utils.config import get_config_path
import geobuf
config = configparser.ConfigParser()
config_file_path = get_config_path()
# 从配置文件加载大文件路径
# config = configparser.ConfigParser()
# config.read('./config.ini')  # 配置文件为 config.ini
# 读取配置文件
config.read(config_file_path)
Global_CostaLines = config['Files']['Global_CostaLines'] # 全球岸线数据
Global_DEM = config['Files']['Global_DEM'] # 全球DEM数据
ERA5_Wind = config['Files']['ERA5_Wind'] # ERA5风场数据
 
def init_routes(app):
    CORS(app, resources=r'/*')
    # CORS(app, resources={r"/*": {"origins": "http://localhost:8080"}})
    # 全局异常处理
    @app.errorhandler(Exception)
    def handle_exception(e):
        app.logger.error(f"An error occurred: {e}")
        return jsonify({"error": str(e)}), 500
    @app.route('/')
    ####=======================测试部分=====================================####
    def index():
        
        return app.config['TEMP_DIR'] ,app.config['STATIC_DIR']
   
    def geojson_to_mesh(geojson_file, mesh_file):
        with open(geojson_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        nodes = []
        triangles = []
        
        node_map = {}
        seen_nodes = set()  # 用于存储已经见过的节点ID
        
        # 遍历每个三角形的特征
        for feature in data['features']:
            if feature['geometry']['type'] == 'Polygon':
                triangle_id = feature['properties']['id']# 获取三角形ID
                coords = feature['geometry']['coordinates'][0]  # 获取三角形的坐标
                if triangle_id == "350" :
                    print(f"坐标1 : {coords[0]}, 坐标2: {coords[1]}, 坐标3: {coords[2]}") 

                # 遍历每个feature的坐标点的属性
                node_ids = [] # 记录三角形每个节点的id
                for point_property in feature['properties']['points_properties']: # 循环3次
                    depth = point_property['depth']
                    value = point_property['value']
                    node_id = point_property['id']  # 获取节点ID
                    if triangle_id == "350" :
                        print(f"Node ID: {node_id}, Depth: {depth}, Value: {value}") 
                    
                    node_ids.append(node_id)
                    
                    index = 1
                    if index < len(coords): # 循环3次
                        lon, lat = coords[index - 1]  # index从0开始,到2结束
                            # 如果节点ID已经在seen_nodes中，则跳过该节点
                        nodes.append((node_id, lon, lat, depth, value))
                        node_map[node_id] = len(nodes)  # 映射原始node_id到节点列表中的索引
                        index = index + 1
                        
                    else:
                        print(f"Warning: Node ID {node_id} is out of range for coordinates.")
                if triangle_id == "350" :
                    print(f"Node IDs: {node_ids}") # 三角形的三个节点
                triangles.append(f"{triangle_id} {node_ids[0]} {node_ids[1]} {node_ids[2]} ")
        # 准备.mesh文件内容
        num_nodes = len(nodes)
        mesh_content = []

        # 1 头信息
        mesh_content.append(f"100079  1000  {num_nodes}  LONG/LAT")

        # 2 节点部分
        for node in nodes:
            mesh_content.append(f"{node[0]} {node[1]} {node[2]} {node[3]} {node[4]} "+ "\n")

        # 3 三角形头
        num_triangles = len(data['features'])
        mesh_content.append(f"{num_triangles} 3 21")
        # 4 三角形内容
        mesh_content.append('\n'.join(triangles)) 


        # 写入.mesh文件
        with open(mesh_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(mesh_content))
        return mesh_content

    ####===========================专题图制作部分=====================================####
    # 生成专题图
    @app.route('/genimg-pltf', methods=['GET', 'POST'])
    def gen_maps():
        # 获取id
        data = request.get_json()
        projectid = data.get('id')
        if projectid is None:
            return jsonify({'error': 'project ID  is required'}), 400

        print("工程id："+projectid)
 
        image_dir = app.config['TEMP_DIR']+f'/{projectid}/png/'

        # 判断文件夹是否存在，如果不存在则创建
        if not os.path.exists(image_dir):
            os.makedirs(image_dir)
            # 创建子目录
            sub_dirs = ['mesh_coastline','amplitude', 'flow', 'flow_nodepth', 'flow_tide', 'griddepth','lagtrack','pollutant']
            for sub_dir in sub_dirs:
                sub_dir_path = os.path.join(image_dir, sub_dir)
                if not os.path.exists(sub_dir_path):
                    os.makedirs(sub_dir_path)
            # 根据结果nc文件生成全部的图片
            temp_costaline_npz =  app.config['TEMP_DIR']+f'/{projectid}/coastline.npz'
            temp_tide_npz =  app.config['TEMP_DIR']+f'/{projectid}/tide_analysis.npz'
            get_coastline_from_npz(app.config['STATIC_DIR']+"/pltf/pltf_0002.nc", # 水动力网格文件路径
                            app.config['STATIC_DIR']+"/pltf/ezwssc_0001.nc",# 污染物nc文件路径
                            app.config['STATIC_DIR']+"/pltf/lagnc_lagtra.nc", # 粒子追踪文件路径
                            temp_costaline_npz,
                            temp_tide_npz,
                            image_dir)
             
            image_files = list_images_in_directory(image_dir)
            return jsonify({'data': image_files,'success': True}), 200
        else:
 
                    # 列出目录下所有图片文件
            image_files = list_images_in_directory(image_dir)
            return jsonify({'data': image_files,'success': True}), 200
 

    def list_images_in_directory(directory):
        """遍历目录及其子目录，列出所有图片文件的相对路径。"""
        image_files = []
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    image_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(image_path, directory)
                    normalized_path = relative_path.replace("\\", "/")  # 替换反斜杠为正斜杠
                    image_files.append(normalized_path)
        return image_files
    @app.route('/get-img/<id>/<type>/<filename>')
    def get_maps(id,type,filename):
        # 构建图片的完整路径
        image_path = app.config['TEMP_DIR']+f"/{id}/png/{type}/{filename}"
        # 如果图片不存在，则生成图片
        if not os.path.exists(image_path):
            return  jsonify({'data': "未找到图片",'success': False}), 404
        # 使用 send_file 返回图片数据
        return send_file(image_path, mimetype='image/png')
    #   return jsonify({'data': costline,'success': True}), 200
  
    ####===========================水深部分=====================================####
    #更新网格水深值
    @app.route('/updateDepth', methods=['GET', 'POST'])
    def updatedepth():
        # 从请求中解析GeoJSON和步长参数
        data = request.get_json()
        print(data)
        # 从JSON中获取GeoJSON对象
        geojson = data.get('geojson1')
        if geojson is None:
            return jsonify({'error': 'GeoJSON is required'}), 400
 
        # 调用更新水深 的函数
        geojson= updateDepth(Global_DEM,geojson,app.config['TEMP_DIR'] +'/mesh_depth.json', app.config['TEMP_DIR'] +"/dem.tif" )
        # 返回生成的 .mesh 文件内容
        return jsonify({'data': geojson,'success': True}), 200
    ####===========================风场部分=====================================####
    @app.route('/gen-windnc', methods=['GET', 'POST'])
    def gen_windnc():
        # 从请求中解析GeoJSON和步长参数
        data = request.get_json()
        # print(data)
        # 从JSON中获取GeoJSON对象
        geojson = data.get('mesh_geojson')
        mesh_bbox = data.get('mesh_bbox')
        if geojson is None:
            return jsonify({'error': 'GeoJSON is required'}), 400
        # 获取起止时间、步长
        time_step = data.get('time_step')
        start_time = data.get('start_time')
        end_time = data.get('end_time')
        end_time = data.get('end_time')
        if start_time is None or end_time is None:
            return jsonify({'error': 'Start time and end time are required'}), 400
        # 调用生成风场的函数

        try:
            # 检查必要的输入参数
            if not all([mesh_bbox, start_time, end_time, time_step, geojson]):
                raise ValueError("缺少必要的参数：mesh_bbox, start_time, end_time, time_step, geojson")

            nc_file_path = app.config['TEMP_DIR']+f'/wind/wind_{uuid.uuid4()}.nc' # 结果文件
            temp_clip_nc = app.config['TEMP_DIR']+f"/clip_{uuid.uuid4()}.nc"
            temp_wind_Iint2 = app.config['TEMP_DIR']+f"/wind_Iint2_{uuid.uuid4()}.txt"
            temp_wind_Time2= app.config['TEMP_DIR']+f"/wind_Time2_{uuid.uuid4()}.txt"
            temp_uwind = app.config['TEMP_DIR']+f"/uwind_{uuid.uuid4()}.txt"
            temp_vwind = app.config['TEMP_DIR']+f"/vwind_{uuid.uuid4()}.txt"
            temp_nodes = app.config['TEMP_DIR']+f"/nodes_{uuid.uuid4()}.xlsx"
            temp_cells = app.config['TEMP_DIR']+f"/cells_{uuid.uuid4()}.xlsx"
            # 调用函数生成NetCDF文件
            nc = generate_wind_netcdf(
                mesh_bbox,
                start_time,
                end_time,
                time_step,
                geojson,
               ERA5_Wind,# 风场文件
                temp_clip_nc,
                nc_file_path,  # 将重复的文件路径变量合并
                temp_wind_Iint2,
                temp_wind_Time2,
                temp_uwind,
                temp_vwind,
               temp_nodes,
                temp_cells
            )
            
            # 检查文件生成是否成功
            if not os.path.exists(nc_file_path):
                raise FileNotFoundError("文件未生成成功: " + nc_file_path)
            
        except ValueError as ve:
            return jsonify({'error': str(ve)}), 400
        except FileNotFoundError as fnf_error:
            return jsonify({'error': str(fnf_error)}), 500
        except Exception as e:
            return jsonify({'error': '发生未知错误: ' + str(e)}), 500
        delete_files( temp_clip_nc,temp_wind_Iint2, temp_wind_Time2, temp_uwind, temp_vwind, temp_nodes, temp_cells)
        print (nc)
        return jsonify({'data': nc,'success': True}), 200
        # return send_file(nc, as_attachment=True)
    #获取nc文件
    @app.route('/get-windnc/<id>/<name>', methods=['GET'])
    def get_windnc(id,name):
        if id is None:
             return jsonify({'error': 'id is required'}), 400
        if name is None:
            return jsonify({'error': 'nc_path is required'}), 400
        # 调用函数返回文件数据
        try:
            path = app.config['TEMP_DIR']+f"/wind/{name}"
            with open(path, 'rb') as f:
                nc_data = f.read()
            return send_file(BytesIO(nc_data), as_attachment=True, download_name=os.path.basename(name),
                                mimetype='application/octet-stream')
        except FileNotFoundError as fnf_error:
            return jsonify({'error': str(fnf_error)}), 404
        except Exception as e:
            return jsonify({'error': '发生未知错误: ' + str(e)}), 500
            
    ####=======================MESH网格部分=====================================####
    # 上传网格
    @app.route('/uploadMesh', methods=['GET', 'POST'])
    def upload_mesh():
        if request.method == 'POST':

            # 检查是否有文件上传
            if 'file' not in request.files:
                return jsonify({"message": "No file part in the request"}), 400

            # 获取所有上传的文件列表
            files = request.files.getlist('file')
            print(files)
            # 检查是否选择了文件
            if not files:
                return jsonify({"message": "No file selected"}), 400

            # 保存所有上传的文件x
            saved_files = []
            for file in files:
                if file.filename == '':
                    return jsonify({"message": "One or more files have no name"}), 400

                filename = secure_filename(file.filename)
                file.save(app.config['TEMP_DIR'] +f"/{filename}")
                saved_files.append(filename)
                geojson=Mesh_nodes_to_Triangle_Json(app.config['TEMP_DIR'] +f"/{filename}")

            return jsonify({"message": "Files uploaded successfully", "files": saved_files,"geojson":geojson}), 200

        # 如果请求方法不是 POST，则返回一个错误信息
        return jsonify({"message": "Invalid request method"}), 405
    # Geojson转Mesh
    @app.route('/json2mesh', methods=['GET', 'POST'])
    def json2mesh():
        # 检查请求是否为 JSON
        if not request.is_json:
            return jsonify({"error": "Invalid input format. Expected JSON."}), 400
        # print(request.get_json())
        # 获取 JSON 数据
        data = request.get_json()
        
        geojson = data.get('geojson')
        # print(geoJson)
        # geoJson2 = data.get('geoJson2')
        if geojson is None:
            return jsonify({"error": "Missing nets in request data."}), 400
        
        # # 确保 'features' 的每个元素的 'points_properties' 是列表，然后转换为字符串
        for feature in geojson['features']:
            if isinstance(feature['properties']['points_properties'], list):
                feature['properties']['points_properties'] = json.dumps(feature['properties']['points_properties'])
        print(type(geojson['features'][0]['properties']['points_properties'])) #<class 'list'>
        depth_file = app.config['TEMP_DIR']+f'/mesh_depth_{uuid.uuid4()}.json'
        dem_file = app.config['TEMP_DIR']+f'/dem_{uuid.uuid4()}.tif'
        geojson= updateDepth(Global_DEM,geojson,depth_file, dem_file )  
        # 调用处理函数（替换为您的实际逻辑）
        mesh_file_content = Geojson_to_Mesh(geojson)
        # 重排索引
        mesh_file_content  = reindex_mesh_nofile(mesh_file_content)
        # 创建一个 in-memory 字节流来保存生成的 mesh 文件
        mesh_io = BytesIO(mesh_file_content.encode('utf-8'))

        return send_file(mesh_io, as_attachment=True, download_name=app.config['TEMP_DIR'] +'/output.mesh', mimetype='text/plain')
    #  生成网格
    @app.route('/gen-mesh', methods=['GET', 'POST'])
    def generate2mesh():
      
        # 从请求中解析GeoJSON和步长参数
        data = request.get_json()
        print(data)
        # 从JSON中获取GeoJSON对象
        geojson = data.get('geojson1')
          # 获取步长参数 , 默认0.01
        mesh_size = data.get('mesh_size')
        if mesh_size is None or mesh_size<=0:
            return jsonify({'error': 'Invalid mesh_size.'}), 400
        print(mesh_size)
        if geojson is None:
            return jsonify({'error': 'GeoJSON is required'}), 400
        print(mesh_size)
        # 调用生成 mesh 的函数
        mesh_file_path= GenerateMesh(geojson, mesh_size,"geo.geo","msh.msh",app.config['TEMP_DIR'] +"/mesh.mesh")
        geojson =  Mesh_nodes_to_Triangle_Json(mesh_file_path)
        # 返回生成的 .mesh 文件内容
        return jsonify({'data': geojson,'success': True}), 200
    # 面与岸线裁剪 
    @app.route('/clip-mesh', methods=['GET', 'POST'])
    def clip2mesh():
        # 从请求中解析GeoJSON和步长参数
        data = request.get_json()
        # print(data)
        # 从JSON中获取GeoJSON对象
        geojson = data.get('geojson1')
        if geojson is None:
            return jsonify({'error': 'GeoJSON is required'}), 400
        # 调用生成 mesh 的函数
        
        clip_temp_file = app.config['TEMP_DIR']+f"/ClipArea2Mesh__{uuid.uuid4()}"
        # shpPath = erase_geojson_with_shp_geopandas(geojson,Global_CostaLines,clip_temp_file+".shp")
        # geojson =  shp_to_geojson_with_geopandas(shpPath)
        geojson =  erase_geojson_with_shp_geopandas(geojson,Global_CostaLines,clip_temp_file+".shp")
        # 删除临时文件
        delete_files( clip_temp_file+ ".shp",
                     clip_temp_file+ ".cpg",
                    clip_temp_file+ ".dbf",
                     clip_temp_file+ ".shx",
                     clip_temp_file+ ".prj")
        # 返回生成的geojson文件内容
        return jsonify({'data': geojson,'success': True}), 200
    # 根据裁剪区域生成网格
    @app.route('/gen-clipmesh', methods=['GET', 'POST'])
    def genclip2mesh():
        data = request.get_json() # 从请求中解析GeoJSON和步长参数
        geojson = data.get('geojson1') # 从JSON中获取GeoJSON对
        mesh_size = data.get('mesh_size') # 获取步长参数 , 默认0.1
        if mesh_size is None or mesh_size<=0:
            return jsonify({'error': 'Invalid mesh_size.'}), 400
        if geojson is None:
            return jsonify({'error': 'GeoJSON is required'}), 400
        print("网格步长：")
        print(mesh_size)
        # 调用生成 mesh 的函数
        mesh_file_path= GenerateMesh(geojson, mesh_size,app.config['TEMP_DIR'] +"/geo.geo",app.config['TEMP_DIR'] +"/msh.msh",app.config['TEMP_DIR'] +"/mesh.mesh")
        large = get_larger_file_index(mesh_file_path)
        print("最大区域")
        print(large)
        geojson2 =  Mesh_nodes_to_Triangle_Json(mesh_file_path[large])
 
        geojson4 = updateDepthAndReindex(geojson2,mesh_size)
        # 删除返回生成的 .mesh 文件内容
        for file_path in mesh_file_path:
            delete_files(file_path)
        return jsonify({'data': geojson4,'success': True}), 200
    # 网格移动后裁剪
    @app.route('/clipmesh', methods=['GET', 'POST'])
    def clipOffsetmesh():

        data = request.get_json()
        geojson = data.get('geojson1')
        bbox = data.get('bbox')
        print("边界值")
        print(bbox)
        if geojson is None:
            return jsonify({'error': 'GeoJSON is required'}), 400
        #调用裁剪 mesh 的函数
        offset_temp_file = app.config['TEMP_DIR']+f"/offsetMesh__{uuid.uuid4()}"
        geojson2 =  erase_geojson_with_shp(bbox,geojson, Global_CostaLines, offset_temp_file+".shp")
        # # 删除临时文件
        delete_files( offset_temp_file+ ".shp",
                     offset_temp_file+ ".cpg",
                    offset_temp_file+ ".dbf",
                     offset_temp_file+ ".shx",
                     offset_temp_file+ ".prj")
        # 计算网格步长
        average_mesh_size = calculate_mesh_size(geojson2, mode="average")
        print(f"Average mesh size: {average_mesh_size}")
        geojson3=updateDepthAndReindex(geojson2,average_mesh_size)
            # 编码 GeoJSON 为 geobuf 格式的 bytes
        geobuf_bytes = geobuf.encode(geojson3)

        # 将 bytes 转换为 Base64 编码字符串
        geobuf_base64 = base64.b64encode(geobuf_bytes).decode('utf-8')
        print(geobuf_base64)
        # return jsonify({'geobuf': geobuf_base64}), 200 
        # 返回二进制数据
        # return Response(geobuf.encode( (geojson3)), content_type='application/octet-stream')
        return jsonify({'data': geobuf_base64,'success': True}), 200
    # 网格加密
    @app.route('/encrypt-mesh', methods=['GET', 'POST'])
    def encrypt_mesh():
        # # 从请求中解析多个Geojson和参数
        data=request.get_json()
        geojson_data = data.get('geojson1')
        inner_curve_data = data.get('inner_curve_data')
        print("加密区数据：")
        print(inner_curve_data)
        mesh_size = data.get('mesh_size')
        print("网格尺寸：")
        print(mesh_size)
        if geojson_data is None or inner_curve_data is None:
            return jsonify({'error': 'Missing nets in request data.'}), 400
        if mesh_size is None:
            return jsonify({'error': 'Missing mesh_size in request data.'}), 400
        # 调用加密函数
        mesh_file_path = refinement_mesh( geojson_data,mesh_size,inner_curve_data,mesh_out_file=app.config['TEMP_DIR'] +f"/加密_{uuid.uuid4() }.mesh")  # 在文件名中添加 UUID)
        mesh_json = Mesh_nodes_to_Triangle_Json(mesh_file_path)

        delete_files(mesh_file_path)

        mesh_json2 = updateDepthAndReindex(mesh_json,mesh_size)
        return jsonify({'data': mesh_json2,'success': True}), 200

    # 对网格进行索引重排、水深赋值、边界赋值
    def updateDepthAndReindex(geojson,mesh_size_buffer,global_costalines=Global_CostaLines):
        # 确保 'features' 的每个元素的 'points_properties' 是列表，然后转换为字符串
        for feature in geojson['features']:
            if isinstance(feature['properties']['points_properties'], list):
                feature['properties']['points_properties'] = json.dumps(feature['properties']['points_properties'])
        print(type(geojson['features'][0]['properties']['points_properties'])) #<class 'list'>
        depth_file = app.config['TEMP_DIR']+f'/mesh_depth_{uuid.uuid4()}.json'
        dem_file = app.config['TEMP_DIR']+f'/dem_{uuid.uuid4()}.tif'
        geojson= updateDepth(Global_DEM,geojson,depth_file, dem_file )   
        mesh_file_content = Geojson_to_Mesh(geojson) # json 2 mesh

        mesh_file_content  = reindex_mesh_nofile(mesh_file_content)  # 重排索引
        # 保存临时文件
        tempfile = app.config['TEMP_DIR']+f"/updateDepthAndReindex临时mesh_{uuid.uuid4() }.mesh"
        with open(tempfile,'w') as f:
            f.write(mesh_file_content)
        geojson2= Mesh_nodes_to_Triangle_Json(tempfile) # mesh 2 json
        delete_files(depth_file,dem_file,tempfile) # 删除临时文件
        #如果mesh_size不为负数，则进行边界赋值
        if mesh_size_buffer>0:
            geojson3 = extra_bd_attr(geojson2,mesh_size_buffer*1.2,global_costalines) # 边界赋值
            print("边界赋值完成")
            return geojson3
        return geojson2
    ####=======================岸线部分========================================####
    @app.route('/uploadAxBln', methods=['GET', 'POST'])
    def upload_bln():
        if request.method == 'POST':
            if 'file' not in request.files:
                return jsonify({"message": "请求中没有文件部分"}), 400
    @app.route('/coastline-clip-mesh', methods=['GET', 'POST'])
    def coastline_clip_mesh():
        data = request.get_json()
        clip_geojson = data.get('clip_geojson')
        mesh_geojson = data.get('mesh_geojson')
        mesh_bbox = data.get('mesh_bbox')
        if clip_geojson is None or mesh_geojson is None:
            return jsonify({'error': 'GeoJSON is required'}), 400
        # 临时文件
        temp_cosatalines = app.config['TEMP_DIR'] +'/clip_temp_costalines_' + str(uuid.uuid4())  
        temp_shp_clip = app.config['TEMP_DIR'] +'/clip_temp_bbox_' + str(uuid.uuid4())  
        from modules.mesh.geojson_obj_to_shpfile import geojson_obj_to_shp
        geojson_obj_to_shp(clip_geojson,temp_cosatalines+".shp")
        geojson_res =  erase_geojson_with_shp(mesh_bbox,mesh_geojson, temp_cosatalines+".shp", temp_shp_clip+".shp")
         # 计算网格步长
        average_mesh_size = calculate_mesh_size(geojson_res, mode="average")
        print(f"Average mesh size: {average_mesh_size}")
        geojson_res=updateDepthAndReindex(geojson_res,average_mesh_size,temp_cosatalines+".shp")

        delete_files(temp_cosatalines+".shp",temp_cosatalines+".cpg",temp_cosatalines+".dbf",temp_cosatalines+".shx",temp_cosatalines+".prj")
        delete_files(temp_shp_clip+".shp",temp_shp_clip+".cpg",temp_shp_clip+".dbf",temp_shp_clip+".shx",temp_shp_clip+".prj")
        return jsonify({'data': geojson_res,'success': True}), 200

   ####=======================潮位部分========================================####
    @app.route('/get_tide', methods=['POST'])
    def get_tide():

        data = request.get_json()
        points = data.get('points')
        start_time = data.get('start_time')
        end_time = data.get('end_time')

        # 检查请求数据是否完整
        if not points or not start_time or not end_time:
            return jsonify({'error': 'Missing required parameters'}), 400

            # 将字符串时间转换为datetime对象
        try:
            start_dt = datetime.fromisoformat(start_time)
            end_dt = datetime.fromisoformat(end_time)
            # 生成整点时间数组
            times = []
            current_time = start_dt.replace(minute=0, second=0, microsecond=0)

            while current_time <= end_dt:
                times.append(current_time)
                current_time += timedelta(hours=1)

        except ValueError:
            return jsonify({'error': 'Invalid date format, use ISO format: YYYY-MM-DDTHH:MM:SS'}), 400


        # 潮汐预测
        try:
            predicted_results = predict_tide(points=points, times=times)

            # 取times的索引数组，从0开始
            iint = np.array(list(range(len(times))))

            # 起始时间作为0，后续根据前一段时间求秒数的插值（秒数）
            time = np.array([(t - start_dt).total_seconds() for t in times])  # 将 time 转换为 NumPy 数组

            # 取points的索引数组，从1开始
            obc_nodes = np.array(list(range(1, len(points) + 1)))  # 从1开始

            # 取predicted_results
            elevation = np.array(predicted_results)  # 确保 elevation 是 NumPy 数组

            # 制作nc文件
            file_path = make_obc_nc(iint, time, obc_nodes, elevation)

            # file_path = 'predict.dat'
            # with open(file_path, 'w') as file:
            #     # 先写入每个点的潮位预测
            #     for heights in zip(*predicted_results):  # 转置，使每列对应一个点
            #         file.write(' '.join(f"{height:>10.4f}" for height in heights) + '\n')

            print("潮位预测完成，结果已保存到predict.dat文件。")

            # 返回文件给前端
            return send_file(file_path, as_attachment=True)

        except ValueError:
            return jsonify({'error': '潮位预测失败'}), 400

