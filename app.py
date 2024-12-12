from flask import Flask
from route.routes import init_routes
from route.thematic import thematic_routes
from route.simulate import simulate_routes
import gmsh
import os
import rasterio.sample, fiona, pyogrio._vsi ,pyogrio._geometry

print(rasterio.sample,fiona ,pyogrio._vsi,pyogrio._geometry)
app = Flask(__name__)



# 读取配置文件
from utils.config import get_config_path
import configparser
config = configparser.ConfigParser()
config_file_path = get_config_path()
config.read(config_file_path)
# 设置全局配置
app.config['TEMP_DIR'] = config['Directory']['TEMP_Dir']
app.config['STATIC_DIR'] = config['Directory']['STATIC_Dir']
app.config['PRJ_DB'] =config['Linux']['PRJ_DB']
# 初始化路由
init_routes(app)
thematic_routes(app)
simulate_routes(app)
if os.name == 'nt':  # Windows
    app.config['activate_path'] = config['NT']['activate_path']
    app.config['gmsh_path'] = config['NT']['gmsh_path']

else:  # Linux/Unix
    app.config['activate_path'] = config['Linux']['activate_path']
    app.config['gmsh_path'] = config['Linux']['gmsh_path']
    # Linux 投影配置
    os.environ['PROJ_LIB'] = app.config['PRJ_DB'] 
if __name__ == '__main__':
    # debug 热更新
    app.run(debug=True, threaded=True,port=5000, host='0.0.0.0')
