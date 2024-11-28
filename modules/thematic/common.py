
import numpy as np
import matplotlib
matplotlib.use('Agg')
import numpy as np  
# -----------------------------
# 专题图制作公用函数
# -----------------------------
def harmonic(time, data, omega):
  # 调和分析
  M = np.size(omega)
  N = np.size(data)
  amp = np.zeros(M)
  phase = np.zeros(M)
  L = 2 * M + 1;
  A = np.zeros([N,L])
  for i in range(N):
    for j in range(M):
      tmp = omega[j] * time[i]
      A[i,j] = np.cos(tmp)
      A[i,j+M] = np.sin(tmp)
    A[i,L-1] = 1.0
  
  C = np.zeros([L,L])
  F = np.zeros([L,1])
  for i in range(L):
    for j in range(i+1):
      C[i,j] = np.sum(A[:,i] * A[:,j])
    F[i] = np.sum(A[:,i] * data[:])

  for i in range(L-1):
    for j in range(i+1,L):
      C[i,j] = C[j,i]

  X = np.linalg.solve(C,F)

  for j in range(M):
    amp[j] = np.sqrt(X[j]*X[j] + X[j+M]*X[j+M])
    phase[j] = calc_phase(X[j], X[j+M])

  amp0 = X[L-1]
  return (amp, phase, amp0)

def calc_phase(tmpa, tmpb):
  phase = np.arctan(tmpb/tmpa) * 180.0/np.pi
  if tmpa < 0.0:
    phase = phase + 180.0
  else:
    if tmpb < 0.0:
      phase = phase + 360.0
  return phase

def get_coastline(x, y, tri):
  # 由三角形网格数据提取边界线
  # 查找最左边的点
  ind0 = np.argmin(x)
  ind1 = ind0

  line_ind = np.zeros(5000,np.int32) - 1
  line_count = 1
  line_ind[0] = ind0

  while True:
    # 查找包含ind1这个点的面元
    tind = np.argwhere(tri == ind1)
    face_ind = [t[0] for t in tind]
    vertex_ind = tri[face_ind, :]
    vertex_ind.shape = -1

    # 查找面元中的点，去除重复的点以及在边界中出现过的点
    ind2 = ind0
    for vtxind in vertex_ind:
      count = np.count_nonzero(vtxind == vertex_ind)
      if count == 1 and all(vtxind != line_ind):
        ind2 = vtxind
        break
    
    line_count += 1
    line_ind[line_count-1] = ind2
    ind1 = ind2
    if ind2 == ind0: break

  linex = x[line_ind[0:line_count]]
  liney = y[line_ind[0:line_count]]
  return (linex,liney)
