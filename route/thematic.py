import numpy as np
import json
import os
import uuid
import configparser
from flask import Flask, request, send_file, jsonify, make_response
from modules.thematic.gen_maps import get_coastline_from_npz
from flask_cors import CORS
from datetime import datetime, timedelta
import ast
# 专题图制作    

def thematic_routes(app):
    CORS(app, resources=r'/*')
    app.config['TEMP_DIR'] # 临时文件目录
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
        allType = ['mesh_coastline','amplitude', 'flow', 'flow_nodepth', 'flow_tide', 'griddepth', 'lagtrack','pollutant']
        # 判断thematic_type是否在allType
        if thematic_type not in allType:
            return jsonify({'status': 'failed','message': 'thematic_type is none'})
        # -----------------------------
        # 网格和岸线专题图制作
        # -----------------------------
        if thematic_type =='mesh_coastline':
        # 读取thematic_configs中所有的参数
            water_nc_path = thematic_configs.get('water_nc_path') #必填
            costaline = thematic_configs.get('costaline') or app.config['TEMP_DIR'] +f'/{project_id}/coastline.npz'
            png_path = thematic_configs.get('png_path') or app.config['TEMP_DIR'] +f'/{project_id}/png/'
            # 获取专题图参数配置
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

            image_files = list_images_in_directory( app.config['TEMP_DIR'] +f"/{project_id}/png/{thematic_type}/")
            return jsonify({'data': image_files,'success': True}), 200
            
        # -----------------------------
        # 潮位振幅等值线制作
        # -----------------------------
        elif thematic_type == 'amplitude':
            water_nc_path = thematic_configs.get('water_nc_path') #必填
            costaline = thematic_configs.get('costaline') or app.config['TEMP_DIR'] +f'/{project_id}/coastline.npz'
            png_path = thematic_configs.get('png_path') or app.config['TEMP_DIR'] +f'/{project_id}/png/'

            from modules.thematic.gen_maps import gen_tide_analysis
            temp_tidenpz = app.config['TEMP_DIR'] +f'/{project_id}/tide_analysis.npz'
            gen_tide_analysis(water_nc_path, temp_tidenpz)  # 潮汐调和分析

            # 获取专题图参数配置
            lon_min = thematic_configs.get('lon_min') or None
            lon_max = thematic_configs.get('lon_max')  or None
            lat_min = thematic_configs.get('lat_min') or None
            lat_max = thematic_configs.get('lat_max')  or None
            dpi = thematic_configs.get('dpi') or 300
            # 绘制潮位调和分析图
            from modules.thematic.plot_tide_analysis import plot_tide_analysis
            plot_tide_analysis(temp_tidenpz, costaline, png_path ,                 
                        lon_min=lon_min, 
                        lon_max=lon_max, 
                        lat_min=lat_min, 
                        lat_max=lat_max,
                        dpi=dpi,
                        png_name=thematic_name # 输出文件名
                        )  # 绘制振幅和相位等值线图
            
            image_files = list_images_in_directory(app.config['TEMP_DIR'] +f"/{project_id}/png/{thematic_type}/")
            return jsonify({'data': image_files,'success': True}), 200
        
        # -----------------------------
        # 流场+水深专题图制作
        # -----------------------------
        elif thematic_type == 'flow':
            water_nc_path = thematic_configs.get('water_nc_path') #必填
            png_path = thematic_configs.get('png_path') or app.config['TEMP_DIR'] +f'/{project_id}/png/'
            # 获取专题图参数配置
            inter = thematic_configs.get('inter') or 10  # 采样间隔
            time_range =  ast.literal_eval(thematic_configs.get('time_range')) or (0, 10)  # 时间步范围
            siglay_step = thematic_configs.get('siglay_step') or 1  # 层数间隔
            speed = thematic_configs.get('speed') or 3  # 流速
            scale = thematic_configs.get('scale') or 15  # 矢量图比例尺
            width = thematic_configs.get('width') or 0.003  # 矢量宽度
            quiverkey_pos = ast.literal_eval(thematic_configs.get('quiverkey_pos')) or (0.1, -0.1)  # 流速比例尺位置
            compass_pos =  ast.literal_eval(thematic_configs.get('compass_pos') )or (0.95, 0.95)  # 指北针位置
            title_prefix = thematic_configs.get('title_prefix') or "Ocean Flow"  # 标题前缀
            dpi = thematic_configs.get('dpi') or 600  # 图片分辨率
            coast_color = thematic_configs.get('coast_color') or 'blue'  # 岸线颜色
            coast_linewidth = thematic_configs.get('coast_linewidth') or 2  # 岸线宽度
            quiver_color = thematic_configs.get('quiver_color') or'red'  # 矢量颜色
            lon_min = thematic_configs.get('lon_min') or None
            lon_max = thematic_configs.get('lon_max')  or None
            lat_min = thematic_configs.get('lat_min') or None
            lat_max = thematic_configs.get('lat_max')  or None
            # 岸线生成
            from modules.thematic.flow_vector_withDepth import flow_vector_withDepth
            flow_vector_withDepth(
                nc_path=water_nc_path,
                costline_path=costaline,
                png_path=png_path,
                inter=inter,  # 采样间隔
                time_range=time_range,  # 时间步范围
                siglay_step = siglay_step,  # 层数间隔
                speed=speed,  # 流速比例尺
                scale=scale,  # 矢量图比例尺
                width=width,  # 矢量宽度
                quiverkey_pos=quiverkey_pos,  # 流速比例尺位置
                compass_pos=compass_pos,  # 指北针位置
                title_prefix=title_prefix,  # 标题前缀
                dpi=dpi,  # 图片分辨率
                coast_color=coast_color,  # 岸线颜色
                coast_linewidth=coast_linewidth,  # 岸线宽度
                quiver_color=quiver_color,  # 矢量颜色
                lon_min=None, 
                lon_max=None, 
                lat_min=None, 
                lat_max=None,
                png_name=thematic_name # 输出文件名
            )
            image_files = list_images_in_directory(app.config['TEMP_DIR'] +f"/{project_id}/png/{thematic_type}/")
            return jsonify({'data': image_files,'success': True}), 200
        
        # -----------------------------
        # 流场-无水深专题图制作
        # -----------------------------
        elif thematic_type == 'flow_nodepth':
            water_nc_path = thematic_configs.get('water_nc_path') #必填
            png_path = thematic_configs.get('png_path') or app.config['TEMP_DIR'] +f'/{project_id}/png/'
            # 获取专题图参数配置
            inter = thematic_configs.get('inter') or 10  # 采样间隔
            time_range =  ast.literal_eval(thematic_configs.get('time_range')) or (0, 10)  # 时间步范围
            siglay_step = thematic_configs.get('siglay_step') or 1  # 层数间隔
            speed = thematic_configs.get('speed') or 3  # 流速
            scale = thematic_configs.get('scale') or 15  # 矢量图比例尺
            width = thematic_configs.get('width') or 0.003  # 矢量宽度
            quiverkey_pos = ast.literal_eval(thematic_configs.get('quiverkey_pos')) or (0.1, -0.1)  # 流速比例尺位置
            compass_pos =  ast.literal_eval(thematic_configs.get('compass_pos') )or (0.95, 0.95)  # 指北针位置
            title_prefix = thematic_configs.get('title_prefix') or "Ocean Flow"  # 标题前缀
            dpi = thematic_configs.get('dpi') or 600  # 图片分辨率
            coast_color = thematic_configs.get('coast_color') or 'blue'  # 岸线颜色
            coast_linewidth = thematic_configs.get('coast_linewidth') or 2  # 岸线宽度
            quiver_color = thematic_configs.get('quiver_color') or'red'  # 矢量颜色
            lon_min = thematic_configs.get('lon_min') or None
            lon_max = thematic_configs.get('lon_max')  or None
            lat_min = thematic_configs.get('lat_min') or None
            lat_max = thematic_configs.get('lat_max')  or None


            from modules.thematic.flow_vector_noDepth import flow_vector_noDepth
            flow_vector_noDepth(
                nc_path=water_nc_path,
                costline_path=costaline,
                png_path=png_path,
                inter=inter,  # 采样间隔
                time_range=time_range,  # 时间步范围
                siglay_step = siglay_step,  # 层数间隔
                speed=speed,  # 流速
                scale=scale,  # 矢量图比例尺
                width=width,  # 矢量宽度
                quiverkey_pos=quiverkey_pos,  # 流速比例尺位置
                compass_pos=compass_pos,  # 指北针位置
                title_prefix=title_prefix,  # 标题前缀
                dpi=dpi,  # 图片分辨率
                coast_color=coast_color,  # 岸线颜色
                coast_linewidth=coast_linewidth,  # 岸线宽度
                quiver_color=quiver_color , # 矢量颜色
                lon_min=lon_min, 
                lon_max=lon_max, 
                lat_min=lat_min, 
                lat_max=lat_max,
                png_name=thematic_name # 输出文件名
            )
            image_files = list_images_in_directory(app.config['TEMP_DIR'] +f"/{project_id}/png/{thematic_type}/")
            return jsonify({'data': image_files,'success': True}), 200
        # -----------------------------
        # 点潮位流速专题图制作
        # -----------------------------
        elif thematic_type == 'flow_tide':
            water_nc_path = thematic_configs.get('water_nc_path') #必填
            png_path = thematic_configs.get('png_path') or app.config['TEMP_DIR'] +f'/{project_id}/png/'
            # 获取专题图参数配置
            lon_stn = ast.literal_eval(thematic_configs.get('lon_stn')) or [450500, 451500]  # 观测站经度序列
            lat_stn = ast.literal_eval(thematic_configs.get('lat_stn')) or [4250500, 4252000]  # 观测站维度序列
            stn_name = thematic_configs.get('stn_name') or ['默认站1', '默认站2']  # 观测站名称
            time_interval = ast.literal_eval(thematic_configs.get('time_interval')) or (0, 100)  # 时间步范围
             # 绘制点潮位流速图
            from modules.thematic.points_tide_flow import points_tide_flow
            points_tide_flow(
                water_nc_path, 
                    png_path ,
                    lon_stn=lon_stn,# 观测站经度序列
                    lat_stn=lat_stn, # 观测站维度序列
                    stn_name=stn_name, # 观测站名称
                    time_interval=time_interval, # 时间步长
                    png_name=thematic_name # 输出文件名
                 ) 
            image_files = list_images_in_directory(app.config['TEMP_DIR'] +f"/{project_id}/png/{thematic_type}/")
            return jsonify({'data': image_files,'success': True}), 200
        # -----------------------------
        # 水深专题图制作
        # -----------------------------
        elif thematic_type == 'griddepth':
            water_nc_path = thematic_configs.get('water_nc_path') #必填
            png_path = thematic_configs.get('png_path') or app.config['TEMP_DIR'] +f'/{project_id}/png/'
            # 获取专题图参数配置
            tri_linewidth = thematic_configs.get('tri_linewidth') or 0.3
            lon_min = thematic_configs.get('lon_min') or None
            lon_max = thematic_configs.get('lon_max')  or None
            lat_min = thematic_configs.get('lat_min') or None
            lat_max = thematic_configs.get('lat_max')  or None
            dpi = thematic_configs.get('dpi') or 300

            from modules.thematic.plot_depth import plot_depth
            plot_depth(water_nc_path, 
                costaline, 
                png_path, 
                tri_linewidth=tri_linewidth, 
                lon_min=lon_min, 
                lon_max=lon_max, 
                lat_min=lat_min, 
                lat_max=lat_max,
                dpi=dpi,   png_name=thematic_name # 输出文件名
                )
            
            image_files = list_images_in_directory(app.config['TEMP_DIR'] +f"/{project_id}/png/{thematic_type}/")
            return jsonify({'data': image_files,'success': True}), 200
        # -----------------------------
        # 拉格朗日粒子追踪专题图制作
        # -----------------------------
        elif thematic_type == 'lagtrack':
            
            lag_nc_path = thematic_configs.get('lag_nc_path') #必填
            lag_index = thematic_configs.get('lag_index') or 0
            png_path = thematic_configs.get('png_path') or app.config['TEMP_DIR'] +f'/{project_id}/png/'
            from modules.thematic.lag_script import lag_script
            lag_script(lag_nc_path, 
                       costaline,
                        png_path,
                       lag_index=lag_index,
                       png_name=thematic_name) 
            
            image_files = list_images_in_directory(app.config['TEMP_DIR'] +f"/{project_id}/png/{thematic_type}/")
            return jsonify({'data': image_files,'success': True}), 200
        # -----------------------------
        # 污染物扩散专题图制作
        # -----------------------------
        elif thematic_type == 'pollutant':
            pollutant_nc_path = thematic_configs.get('pollutant_nc_path') #必填
            png_path = thematic_configs.get('png_path') or app.config['TEMP_DIR'] +f'/{project_id}/png/'
            # 获取专题图参数配置
            lon_min = thematic_configs.get('lon_min') or None
            lon_max = thematic_configs.get('lon_max')  or None
            lat_min = thematic_configs.get('lat_min') or None
            lat_max = thematic_configs.get('lat_max')  or None
            time_index = thematic_configs.get('time_index') or 0
            siglay_index = thematic_configs.get('siglay_index') or 0
            dlon = thematic_configs.get('dlon') or None
            dlat = thematic_configs.get('dlat') or None
            dpi = thematic_configs.get('dpi') or 300
 
            # 污染物扩散图
            from modules.thematic.pollutantDispersion import pollutantDispersion
            pollutantDispersion(pollutant_nc_path, 
                                png_path, 
                                lon_min=lon_min, 
                                lon_max=lon_max, 
                                lat_min=lat_min, 
                                lat_max=lat_max,
                                dlon=dlon,# 工程中心点经度
                                dlat=dlat, # 工程中心点纬度
                                time_index=time_index,
                                siglay_index= siglay_index,
                                dpi=dpi, 
                                png_name=thematic_name # 输出文件名
                            ) 
            image_files = list_images_in_directory(app.config['TEMP_DIR'] +f"/{project_id}/png/{thematic_type}/")
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