import numpy as np
from netCDF4 import Dataset

def make_obc_nc(iint, time, obc_nodes, elevation):
    # 创建一个 NetCDF 文件，指定为 NetCDF3 格式
    file_path = '../../tempfile/julian_obc.nc'
    nc = Dataset(file_path, 'w', format='NETCDF3_CLASSIC')
    # 定义全局属性
    nc.title = 'Boundary conditions'
    nc.type = 'FVCOM TIME SERIES ELEVATION FORCING FILE'

    # 定义维度
    time_dimid = nc.createDimension('time', None)  # 定义无限时间维度
    nobc_dimid = nc.createDimension('nobc', len(obc_nodes))  # 定义 nobc 维度

    # 定义变量及其属性
    iint_varid = nc.createVariable('iint', 'i4', ('time',))
    iint_varid.long_name = 'internal mode iteration number'

    time_varid = nc.createVariable('time', 'f4', ('time',))
    time_varid.long_name = 'time'
    time_varid.units = 'seconds since seconds=0.0'
    time_varid.time_zone = 'none'

    itime_varid = nc.createVariable('Itime', 'i4', ('time',))
    itime_varid.units = 'seconds since seconds=0.0'
    itime_varid.time_zone = 'none'

    itime2_varid = nc.createVariable('Itime2', 'i4', ('time',))
    itime2_varid.units = 'msec since seconds=0.0'
    itime2_varid.time_zone = 'none'

    nobc_varid = nc.createVariable('obc_nodes', 'i4', ('nobc',))
    nobc_varid.long_name = 'Open Boundary Node Number'

    # 注意调整变量顺序，将时间维度放在前面以适应 NetCDF3 格式的限制
    elevation_varid = nc.createVariable('elevation', 'f4', ('time', 'nobc'))
    elevation_varid.long_name = 'Open Boundary Elevations'
    elevation_varid.units = 'meters'

    # 从文件中加载数据
    # iint = np.loadtxt('./obc_iint.txt')
    # time = np.loadtxt('./obc_time.txt')
    # obc_nodes = np.loadtxt('./obc_nodes.txt', dtype=int)
    # elevation = np.loadtxt('./obc_elj.dat')

    # 将 elevation 数据调整为正确的形状 (100, 179)，并转置为 (179, 100) 的数据匹配 NetCDF3 的顺序
    # if elevation.shape == (100, 179):
    #     elevation = elevation.T
    # elif elevation.shape != (179, 100):
    #     raise ValueError(f"Unexpected elevation shape: {elevation.shape}, expected (100, 179) or (179, 100)")

    # 写入变量数据
    iint_varid[:] = iint
    time_varid[:] = time
    nobc_varid[:] = obc_nodes
    elevation_varid[:, :] = elevation.T  # 注意这里将数据进行转置以符合 (time, nobc) 的顺序

    itime_varid[:] = np.floor(time / 3600) + 1
    itime2_varid[:] = (time % 1) * 24 * 3600 * 1000

    # 关闭 NetCDF 文件
    nc.close()
    print('done')



    return file_path

