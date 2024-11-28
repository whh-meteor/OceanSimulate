import numpy as np
import pandas as pd
from netCDF4 import Dataset
import xarray as xr
import geopandas as gpd
import rioxarray
from shapely.geometry import box

def Geojson_to_Mesh(geojson_data):
    nodes_dict = {}  # 用字典保存节点信息，key 为节点 id
    triangles = []
    
    # 解析 GeoJSON 中的每个 feature
    for feature in geojson_data['features']:
        triangle_id = feature['properties']['id']
        coordinates = feature['geometry']['coordinates'][0]  # 获取三角形的外环
        
        # 获取每个点的属性信息
        points_properties = feature['properties']['points_properties']
        
        # 遍历三角形的三个顶点及其属性
        node_ids = []
        for i, coord in enumerate(coordinates[:-1]):  # 跳过最后一个坐标，因为它是第一个坐标的重复
            point = points_properties[i]
            node_id = point['id']
            depth = point.get('depth', 0)
            value = int(point.get('value', 0))
            x, y = coord
            # 将节点保存到字典，key 是节点 id
            nodes_dict[node_id] = f"{node_id} {x:.15f} {y:.15f} {depth:.12f} {value}"
            node_ids.append(str(node_id))
        
        # 确保每个三角形正好有三个节点
        if len(node_ids) == 3:
            triangles.append(f"{triangle_id} {node_ids[0]} {node_ids[1]} {node_ids[2]}")
        else:
            print(f"错误: 三角形 {triangle_id} 不正好有 3 个唯一节点。")

    # 生成 mesh 文件内容
    # 按节点 id 排序
    sorted_nodes = sorted(nodes_dict.values(), key=lambda node: int(node.split()[0]))
    num_nodes = len(sorted_nodes)
    num_triangles = len(triangles)

    mesh_content = f"100079  1000  {num_nodes}  LONG/LAT\n"
    mesh_content += "\n".join(sorted_nodes) + "\n"  # 按顺序写入节点
    mesh_content += f"{num_triangles} 3 21\n"
    mesh_content += "\n".join(triangles) + "\n"
    
    return mesh_content,num_nodes,sorted_nodes,num_triangles,triangles
    # 保存为 .mesh 文件
# 创建GeoDataFrame从GeoJSON对象
def create_geodataframe_from_geojson(geojson_data):
    return gpd.GeoDataFrame.from_features(geojson_data['features'])

# 裁剪NC数据
def crop_nc_to_geojson(nc_file_path, geojson_data, output_nc_path, start_time, end_time):
    # 读取NetCDF数据
    print(f"Reading NetCDF data from {nc_file_path}")
    nc_data = xr.open_dataset(nc_file_path)
    
    # 创建GeoDataFrame
    geojson_gdf = create_geodataframe_from_geojson(geojson_data)

    # 获取GeoJSON的融合边界
    bounding_shape = geojson_gdf.union_all()

    # 设置经纬度为空间维度
    nc_data = nc_data.rename({'longitude': 'x', 'latitude': 'y'})  # 根据NetCDF文件中的实际维度名称
    nc_data.rio.set_spatial_dims('x', 'y', inplace=True)

    # 设置坐标参考系为WGS84
    nc_data.rio.write_crs("EPSG:4326", inplace=True)

    # 按时间切片
    time_filtered_data = nc_data.sel(time=slice(start_time, end_time))

    # 裁剪NetCDF数据
    cropped_data = time_filtered_data.rio.clip([bounding_shape])

    # 将 'x' 和 'y' 重新命名为 'lon' 和 'lat'
    cropped_data = cropped_data.rename({'x': 'longitude', 'y': 'latitude'})

    # 保存裁剪后的数据
    cropped_data.to_netcdf(output_nc_path)
    print(f"Cropped NetCDF data saved to {output_nc_path}")
    # 关闭NetCDF文件
    nc_data.close()

def generate_obc_files(t, s, output_file_iint, output_file_time):
    # 生成 iint.txt 文件
    with open(output_file_iint, 'w') as file:
        for i in range(1, t + 1):
            file.write(f"{i}\n")
    
    # 生成 time.txt 文件
    with open(output_file_time, 'w') as file:
        for i in range(t):
            file.write(f"{i * s}\n")

def process_wind_data(filenr, filemshnd, filemshcl, ncl,uwind,vwind):
     
    # 读取网格信息
    ndxy = pd.read_excel(filemshnd, header=None).values.astype(np.float32)
    clid = pd.read_excel(filemshcl, header=None).values
    print(ndxy,clid)
    # 有效索引范围
    max_index_ndxy = len(ndxy)
    print(max_index_ndxy)
    # 检查并过滤无效索引
    invalid_rows = np.where((clid[:, 0] < 1) | (clid[:, 0] > max_index_ndxy) |
                            (clid[:, 1] < 1) | (clid[:, 1] > max_index_ndxy) |
                            (clid[:, 2] < 1) | (clid[:, 2] > max_index_ndxy))[0]
    print(invalid_rows)
    if len(invalid_rows) > 0:
        print(f"发现无效索引值，共 {len(invalid_rows)} 个无效单元。")
        for row in invalid_rows:
            print(f"行 {row + 1}: {clid[row]}")

    # 过滤掉无效单元
    valid_clid = clid[(clid[:, 0] >= 1) & (clid[:, 0] <= max_index_ndxy) &
                      (clid[:, 1] >= 1) & (clid[:, 1] <= max_index_ndxy) &
                      (clid[:, 2] >= 1) & (clid[:, 2] <= max_index_ndxy)]
    clid = valid_clid

    # 输出中心点数量
    ncl = len(clid)
    print(f"中心点数量: {ncl}")

    # 读取 NetCDF 文件中的经纬度和时间信息
    ds = Dataset(filenr)
    xin = ds.variables['longitude'][:].astype(np.float32)
    yin = ds.variables['latitude'][:].astype(np.float32)
    nx = len(xin)
    ny = len(yin)
    # 检查数组维度
    print(f"xin shape: {xin.shape}, yin shape: {yin.shape}")

    # 输出 u10 的 shape
    print(f"u10 的 shape: {ds.variables['u10'].shape}")
    print(f"v10 的 shape: {ds.variables['v10'].shape}")
    ntime = ds.variables['u10'].shape[0]
    print(f"时间步数量: {ntime}")

    # 初始化索引
    clxid1, clyid1 = np.zeros(ncl, dtype=int), np.zeros(ncl, dtype=int)
    clxid2, clyid2 = np.zeros(ncl, dtype=int), np.zeros(ncl, dtype=int)
    clxid3, clyid3 = np.zeros(ncl, dtype=int), np.zeros(ncl, dtype=int)
    clxid4, clyid4 = np.zeros(ncl, dtype=int), np.zeros(ncl, dtype=int)
    print(f"初始化索引: {clxid1, clyid1}")
    # 创建用于存储单元的中心坐标
    vartmpcl = np.zeros((ncl, 2), dtype=np.float32)
    print(f"创建用于存储单元的中心坐标: {vartmpcl}")
    # 找到每个单元的中心点坐标
    for iclid in range(ncl):
        xiclid = (ndxy[clid[iclid, 0] - 1, 0] + ndxy[clid[iclid, 1] - 1, 0] + ndxy[clid[iclid, 2] - 1, 0]) / 3
        yiclid = (ndxy[clid[iclid, 0] - 1, 1] + ndxy[clid[iclid, 1] - 1, 1] + ndxy[clid[iclid, 2] - 1, 1]) / 3
        vartmpcl[iclid, 0] = xiclid
        vartmpcl[iclid, 1] = yiclid
        fndpnt = np.inf

        # 找到最近的四个网格点
        for ifndx in range(nx):
            for ifndy in range(ny):
                dstnt = abs(xiclid - xin[ifndx]) + abs(yiclid - yin[ifndy])
                # print(f"迭代dstnt：{dstnt}")
                if dstnt < fndpnt:
                    fndpnt = dstnt
                    # print(f"迭代fndpnt：{fndpnt}")
                    clxid4[iclid] = clxid3[iclid]
                    clyid4[iclid] = clyid3[iclid]
                    clxid3[iclid] = clxid2[iclid]
                    clyid3[iclid] = clyid2[iclid]
                    clxid2[iclid] = clxid1[iclid]
                    clyid2[iclid] = clyid1[iclid]
                    clxid1[iclid] = ifndx
                    clyid1[iclid] = ifndy
    print(f"迭代")
    # 初始化插值结果的列表
    uwind_all = []
    vwind_all = []

    # 按时间处理数据
    for imon in range(ntime):
        u10 = ds.variables['u10'][imon, :, :].astype(np.float32)
        v10 = ds.variables['v10'][imon, :, :].astype(np.float32)

        # 四点平均计算插值
        uwind_avg = (u10[clxid1, clyid1] + u10[clxid2, clyid2] + u10[clxid3, clyid3] + u10[clxid4, clyid4]) / 4
        vwind_avg = (v10[clxid1, clyid1] + v10[clxid2, clyid2] + v10[clxid3, clyid3] + v10[clxid4, clyid4]) / 4
        # print(f"迭代uwind_avg：{uwind_avg}")
        # print(f"迭代vwind_avg：{vwind_avg}")
        uwind_avg = np.nan_to_num(uwind_avg, nan=0.0)  # 将 NaN 替换为 0
        vwind_avg = np.nan_to_num(vwind_avg, nan=0.0)
        # 添加到列表
        uwind_all.extend(uwind_avg.flatten())
        vwind_all.extend(vwind_avg.flatten())
    print(f"按时间处理数据")


    print(f"uwind_all shape: {(uwind_all)}, vwind_all shape: {(vwind_all)}")

    # 保存插值结果
    np.savetxt(uwind, uwind_all, fmt='%.14f')
    np.savetxt(vwind, vwind_all, fmt='%.14f')
    print('已成功生成 uwind.txt 和 vwind.txt。')
    # 关闭 NetCDF 文件
    ds.close()

def create_netcdf_file(t,ncl,nnd,res_nc_file,output_file_iint,output_file_time,uwind,vwind):
    # 创建 NetCDF 文件
    ncid = Dataset(res_nc_file, 'w', format='NETCDF3_CLASSIC')

    # 设置全局属性
    ncid.title = 'FVCOM variable surface heat forcing file'
    ncid.type = 'FVCOM variable surface heat forcing file'
    ncid.source = 'fvcom grid (unstructured) surface forcing'

    # 定义维度
    node_dimid = ncid.createDimension('node', nnd)
    nele_dimid = ncid.createDimension('nele', ncl)
    time_dimid = ncid.createDimension('time', None)

    # 定义变量及其属性
    iint_varid = ncid.createVariable('iint', 'i4', ('time',))
    time_varid = ncid.createVariable('time', 'f4', ('time',))
    uwind_varid = ncid.createVariable('uwind_speed', 'f4', ('time', 'nele'))
    vwind_varid = ncid.createVariable('vwind_speed', 'f4', ('time', 'nele'))

    # 结束定义部分，准备写入数据
    ncid.sync()

    # 从文件中加载数据
    try:
        iint = np.loadtxt(output_file_iint)
        time = np.loadtxt(output_file_time)
        uwind = np.loadtxt(uwind).reshape((t, ncl))
        vwind = np.loadtxt(vwind).reshape((t, ncl))
    except OSError as e:
        print(f"文件读取错误: {e}")
        ncid.close()
        exit(1)
    except ValueError as e:
        print(f"数据形状调整错误: {e}")
        ncid.close()
        exit(1)

    # 写入数据到变量
    iint_varid[:] = iint
    time_varid[:] = time
    uwind_varid[:, :] = uwind
    vwind_varid[:, :] = vwind

    # 关闭 NetCDF 文件
    ncid.close()
    print('NetCDF 文件已成功创建。')

# 定义函数以保存经纬度数据为Excel文件
def save_lat_lon_to_excel(data, filename):
    # 将数据分割为行
    # rows = data.strip().split('\n')
    rows = [line.strip() for line in data]  # 使用列表推导处理每一行
    # 提取经纬度
    lat_lon_data = [[float(row.split()[1]), float(row.split()[2])] for row in rows]
    
       # 创建DataFrame并保存为Excel，省略表头
    df_lat_lon = pd.DataFrame(lat_lon_data)
    df_lat_lon.to_excel(filename, index=False, header=False)  # 设置 header=False 取消表头
     

# 定义函数以保存索引信息为Excel文件
def save_cells_to_excel(data, filename):
    # 将数据分割为行
    # rows = data.strip().split('\n')
    rows = [line.strip() for line in data]  # 使用列表推导处理每一行
    # 提取索引
    cell_data = [[int(row.split()[1])] + list(map(int, row.split()[2:])) for row in rows]
    
      # 创建DataFrame并保存为Excel，省略表头
    df_cells = pd.DataFrame(cell_data)
    df_cells.to_excel(filename, index=False, header=False)  # 设置 header=False 取消表头
# 定义函数以生成网格文件、网格数据、网格索引、网格中心点坐标、网格时间步数、网格文件名、裁剪后网CDF文件名、裁剪后网CDF文件名、生成的网CDF文件名
def generate_wind_netcdf(mesh_bbox,start_time,end_time,time_step,geojson,nc_file,nc_file_clip,nc_file_res,output_file_iint,output_file_time,uwind,vwind,nodesxlsx,cellsxlsx):
     
    mesh_content,num_nodes,sorted_nodes,num_triangles,triangles= Geojson_to_Mesh(geojson) # 提取网格信息
    crop_nc_to_geojson(nc_file, mesh_bbox, nc_file_clip, start_time, end_time) # 裁剪 NetCDF 文件
    t = Dataset(nc_file_clip).variables['u10'].shape[0]  # 时间步数
    print(f"时间数量：{t}")
    ncl = num_triangles
    print(f"三角形数量：{ncl}")
    nnd=num_nodes
    print(f"节点数量：{nnd}")
    
    save_lat_lon_to_excel(sorted_nodes, nodesxlsx) # 保存节点坐标
    save_cells_to_excel(triangles, cellsxlsx) # 保存网格索引
    generate_obc_files(t, time_step, output_file_iint, output_file_time) # 生成 iint.txt 和 time.txt 文件
    process_wind_data(nc_file_clip, nodesxlsx, cellsxlsx, ncl,uwind,vwind) # 处理网格数据并生成 uwind.txt 和 vwind.txt 文件 (有问题)
    create_netcdf_file(t,ncl,nnd,nc_file_res,output_file_iint,output_file_time,uwind,vwind) #    生成 NetCDF 文件
    
    return nc_file_res
if __name__ == '__main__':
 
    # 2. 提取时间
    
    start_time = "2020-01-02 12:00:00"
    end_time = "2020-01-05 12:00:00"

    crop_nc_to_geojson('F:/Desktop/make_wind/make_wind/UV010P202001.nc', geojson, "UV010P202001_crop.nc", start_time, end_time)

    # 2. 生成 iint.txt 和 time.txt 文件
    filenr = "UV010P202001_crop.nc"
    filemshnd = 'node.xlsx'
    filemshcl = 'cell.xlsx'
    ncl = 17526
    nnd=8960
    # t = 96  # 时间步数
    t = Dataset(filenr).variables['u10'].shape[0]
    s = 3600  # 时间间隔
    output_file_iint = 'wind_Iint2.txt'
    output_file_time = 'wind_Time2.txt'

    generate_obc_files(t, s, output_file_iint, output_file_time)
    process_wind_data(filenr, filemshnd, filemshcl, ncl)
    create_netcdf_file(t,ncl,nnd,'casename_wnd.nc')