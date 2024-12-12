import numpy as np
import json
import os
import uuid
import configparser
from flask import Flask, request, send_file, jsonify, make_response
from modules.pltf.dye2json import dye2json
from flask_cors import CORS
from datetime import datetime, timedelta
import ast
# 污染物模拟结果部分 
def simulate_routes(app):
    CORS(app, resources=r'/*')
    app.config['TEMP_DIR'] # 临时文件目录
    @app.route('/get-dye2json', methods=['GET', 'POST'])
    def get_dye2json():
        # 从json中获取时间
        data = request.get_json()
        time = data['time']
        # 获取nc文件路径
        nc_path = data['nc_path']
        # 检查参数
        if not os.path.exists(nc_path):
            return jsonify({'success': False, 'error': 'nc文件不存在'}), 400
        # 调用dye2json模块，异常处理
        try:
            res = dye2json(nc_path, time)
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 400
        return jsonify({'data': res,'success': True}), 200
            
        
        
            
            