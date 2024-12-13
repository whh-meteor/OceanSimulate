import numpy as np
import json
import os
import uuid
import configparser
from flask import Flask, request, send_file, jsonify, make_response
from modules.pltf.dye2json import dye2json
from flask_cors import CORS
from datetime import datetime, timedelta
from modules.pltf.pltf import get_pltf_points,get_pltf_timeList
from modules.pltf.nc2png import png_from_uv
from modules.pltf.get_nc_value import uv_from_tif
from modules.common import create_project_directory
import threading
import ast
# 污染物模拟结果部分 
def simulate_routes(app):
    CORS(app, resources=r'/*')
    app.config['TEMP_DIR']
    # 获取污染物模拟结果
    @app.route('/get-dye2json', methods=['GET', 'POST'])
    def get_dye2json():
        data = request.get_json()
        time_index = data['time_index']
        nc_path = data['nc_path']
        if not os.path.exists(nc_path):
            return jsonify({'success': False, 'error': 'nc文件不存在'}), 400
        try:
            res = dye2json(nc_path, time_index)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        return jsonify({'data': res,'success': True}), 200
      ####===========================模型结果pltf渲染部分=====================================####
    # 获取某时间和层数的uv
    @app.route('/gen-pltf', methods=['GET', 'POST'])
    def gen_pltf():
        data = request.get_json()
        siglay = data.get('siglay')
        time = data.get('time')
        project_id = data.get('project_id') or  "NoID"
        create_project_directory(app.config['TEMP_DIR'],project_id)
        nc_path = data.get('nc_path') or app.config['STATIC_DIR'] +'/pltf/pltf_0002.nc'
        if not os.path.exists(nc_path):
            return jsonify({'success': False, 'error': 'nc文件不存在'}), 400
        temp_wave_png = app.config['TEMP_DIR'] +f'/{project_id}/wave/{time}_wave.png'
        if os.path.isfile(temp_wave_png):
             return send_file(temp_wave_png, mimetype='image/png')
        else: 
            png,bbox = png_from_uv(siglay,time,'200*200',temp_wave_png,nc_path)
            return send_file(temp_wave_png, mimetype='image/png')
        
    # 后台任务处理函数
    def background_task(nc_path, time_list,project_id):
        print("后台任务开始处理")
        create_project_directory(app.config['TEMP_DIR'],project_id)
        try:
            length = len(time_list)
            for i in range(length):  # 修正为 range(length)
                temp_wave_png = app.config['TEMP_DIR'] +f'/{project_id}/wave/{i}_wave.png'
                if not os.path.isfile(temp_wave_png):
                    png, bbox = png_from_uv(0, i, '200*200', temp_wave_png, nc_path)
                    print(f"任务({i})处理完成，结果保存为: {png}")
        except Exception as e:
            print(f"后台任务失败: {e}")
 
    # 获取时间信息
    @app.route('/get-nc-time', methods=['GET', 'POST'])
    def data_pltf():
        data = request.get_json()
        nc_path = data.get('nc_path')
        nc_type = data.get('nc_type')
        project_id = data.get('project_id')  or "NoID"
        create_project_directory(app.config['TEMP_DIR'],project_id)
        list=[]
        if nc_type == 'water':
            try:
                list  =get_pltf_timeList(nc_path)
                # 启动后台任务线程
                task_thread = threading.Thread(target=background_task, args=(nc_path,list,project_id))
                task_thread.start()
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 400
        elif nc_type == 'population':
            try:
                print(nc_path)
                list = get_pltf_timeList(nc_path)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 400
        return jsonify({'data': list,'success': True}), 200

        
    # 获取某时间和层数的uv
    @app.route('/get-uv', methods=['GET', 'POST'])
    def get_uv():
        import ast
        data = request.get_json()
        print(data)
        time_index = data.get('time_index') or 0
        siglay = data.get('siglay') or 0
        ncfilePath= data.get('path') or app.config['STATIC_DIR']+"/pltf/pltf_0002.nc"
        coordinates =  ast.literal_eval(data.get('coordinates')) or (116.366667, 39.933333)
        if time_index is None or siglay is None:
            return jsonify({'error': 'time_index and siglay_index are required'}), 400
        try:
            uv = uv_from_tif(siglay, time_index, '200*200', ncfilePath , coordinates)
            uv = json.dumps(np.array(uv, dtype=np.float32).astype(float).tolist())
            return jsonify({'data': uv,'success': True}), 200
        except Exception as e:
            print(str(e))
            return jsonify({'error': '发生未知错误: ' + str(e)}), 500
            
        
        
            
            