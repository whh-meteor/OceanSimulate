from flask import Flask
from route.routes import init_routes
from route.thematic import thematic_routes
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

# 初始化路由
init_routes(app)
thematic_routes(app)
if os.name == 'nt':  # Windows
    app.config['activate_path'] = config['NT_Gmsh']['activate_path']
    app.config['gmsh_path'] = config['NT_Gmsh']['gmsh_path']
    # app.config['activate_path'] = 'D:\\anaconda3\\Scripts\\activate.bat oceanmesh2d'
    # app.config['gmsh_path'] = 'D:\\anaconda3\\envs\\oceanmesh2d\\Scripts\\gmsh'
else:  # Linux/Unix
    app.config['activate_path'] = config['Linux_Gmsh']['activate_path']
    app.config['gmsh_path'] = config['Linux_Gmsh']['gmsh_path']
      


if __name__ == '__main__':
    # debug 热更新
    app.run(debug=True, threaded=True,port=5000, host='0.0.0.0')
