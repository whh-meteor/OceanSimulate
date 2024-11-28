from flask import Flask
from route.routes import init_routes
from route.thematic import thematic_routes
import gmsh
import os
import rasterio.sample, fiona, pyogrio._vsi ,pyogrio._geometry

print(rasterio.sample,fiona ,pyogrio._vsi,pyogrio._geometry)
app = Flask(__name__)

# 初始化路由
init_routes(app)
thematic_routes(app)
if os.name == 'nt':  # Windows
    app.config['activate_path'] = 'D:\\anaconda3\\Scripts\\activate.bat oceanmesh2d'
    app.config['gmsh_path'] = 'D:\\anaconda3\\envs\\oceanmesh2d\\Scripts\\gmsh'
      
else:  # Linux/Unix
    app.config['activate_path'] =  '/home/zzc/anaconda3/bin/activate'
    app.config['gmsh_path'] =  '/home/zzc/anaconda3/envs/oceanmesh2d/bin/gmsh'
      


if __name__ == '__main__':
    # debug 热更新
    app.run(debug=True, threaded=True,port=5000, host='0.0.0.0')
