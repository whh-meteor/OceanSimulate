#!/bin/env python
#coding=utf-8
import numpy as np
import matplotlib.tri as tri
import matplotlib.pyplot as plt
from scipy.io import netcdf_file
from utils import get_coastline

nf = netcdf_file("F:\\Desktop\\ZIZHI-DYE-01.nc", 'r', mmap=True)
lon = nf.variables['x'][:]
lat = nf.variables['y'][:]
nv = nf.variables['nv'][:]
h  = nf.variables['h'][:]
nele = nf.dimensions['nele']
node = nf.dimensions['node']

# get the coast line from triangle grid data
nvp = nv.transpose() - 1
coastx,coasty = get_coastline(lon,lat,nvp)
np.savez('coastline.npz', coastx=coastx, coasty=coasty)

fig = plt.figure()
triang = tri.Triangulation(lon,lat,nvp)
plt.triplot(triang,color='k',linewidth=0.05)
plt.plot(coastx,coasty,color='b',linewidth=1.0)
ax = plt.gca()
ax.set_aspect('equal')
plt.xlabel('Longitude (m)')
plt.ylabel('Latitude (m)')

plt.show()

lon = None
lat = None
nv = None
h = None
nf.close()

