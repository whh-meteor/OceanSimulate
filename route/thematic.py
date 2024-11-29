import numpy as np
import json
import os
import uuid
import configparser
from flask import Flask, request, send_file, jsonify, make_response
from modules.thematic.gen_maps import get_coastline_from_npz
from flask_cors import CORS
from datetime import datetime, timedelta
# 专题图制作    
def thematic_routes(app):
    CORS(app, resources=r'/*')
    @app.route('/redraw_thematic', methods=['GET', 'POST'])
    def redraw_thematic():
        
        data = request.get_json()
        print(data)
        # 获取工程id
        project_id = data.get('project_id')
        # 获取专题图类型
        thematic_type = data.get('thematic_type')
        # thematic_name = data.get('thematic_name')
        thematic_name = str(uuid.uuid4()) + '.png'
        # 获取专题图配置参数
        thematic_configs= data.get('thematic_configs')
        allType = ['mesh_coastline','amplitude', 'flow', 'flow_nodepth', 'flow_tide', 'griddepth', 'lagtrack']
        # 判断thematic_type是否在allType
        if thematic_type not in allType:
            return jsonify({'status': 'failed','message': 'thematic_type is none'})
        # 获取数据
        if thematic_type =='mesh_coastline':
        # 读取thematic_configs中所有的参数
            water_nc_path = thematic_configs.get('water_nc_path')
            costaline = thematic_configs.get('costaline') or f'./tempfile/coastline.npz'
            png_path = thematic_configs.get('png_path') or f'./tempfile/{project_id}/png/'
            # 获取tri_linewidth，如果为空，则默认设置为0.05
            tri_linewidth = thematic_configs.get('tri_linewidth') or 0.05
            costa_linewidth = thematic_configs.get('costa_linewidth')or 1.0
            lon_min = thematic_configs.get('lon_min') or None
            lon_max = thematic_configs.get('lon_max')  or None
            lat_min = thematic_configs.get('lat_min') or None
            lat_max = thematic_configs.get('lat_max')  or None
            dpi = thematic_configs.get('dpi') or 300
 
            # 岸线生成
            from modules.thematic.mesh_costline import mesh_costline
            mesh_costline(
                filepath=water_nc_path,
                costline_path=costaline,
                png_path=png_path,
                tri_linewidth = tri_linewidth,# 三角网格线宽
                costa_linewidth = costa_linewidth,# 岸线宽度
                lon_min=lon_min,  # 经度最小值
                lon_max=lon_max,  # 经度最大值
                lat_min=lat_min, # 纬度最小值
                lat_max=lat_max, # 纬度最大值
                dpi=dpi,  # 输出分辨率
                png_name=thematic_name # 输出文件名
            )
            # image_path = f"./tempfile/{project_id}/png/{thematic_type}/{thematic_name}"
            image_path = f"./tempfile/{project_id}/png/{thematic_type}/"
            image_files = list_images_in_directory(image_path)
            return jsonify({'data': image_files,'success': True}), 200
            # return send_file(image_path, mimetype='image/png')
        
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