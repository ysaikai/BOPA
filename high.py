import numpy as np
import multiprocessing as mp
import itertools
import pickle
import os
import sys
import time
import datetime
from copy import deepcopy
from scipy.stats import norm
from scipy.optimize import minimize, basinhopping
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import ConstantKernel, Matern, WhiteKernel
from scipy.linalg import cholesky
import warnings
warnings.filterwarnings('ignore')
from oracle_h import *

os.chdir(os.path.dirname(os.path.abspath(__file__)))

"""Parameters"""
year = 2013
n_iter = 10
n_MC = 2

"""Initialization"""
O = Oracle(year)
bnds = O.__class__.bnds
with open("PI_prior.pickle","rb") as f:
  PI_prior = pickle.load(f)[year]
dim_x = len(bnds) # dimension of x
dim_z = len(O.Z[0]) # dimension of z

max_xzpi = np.zeros((len(O.Z), dim_x+dim_z+1)) # to search for the limit


def run_BO(tt):
  """
  Functions
  """
  def ei(x,z,model):
    xz = np.atleast_2d(np.hstack((x,z)))
    mu, sig = model.predict(xz, return_std=True)
    mu = mu.item()
    sig = sig.item()
    if sig != 0:
      d1 = mu - np.max(S[:,O.Z.index(z),-1])
      d2 = d1/sig
      alpha = d1*norm.cdf(d2) + sig*norm.pdf(d2)
    else:
      alpha = 0

    return alpha


  def maximize_alpha(z,model):
    min_f = np.inf
    min_x = None
    for _ in range(30):
      x0 = np.empty(dim_x)
      for j in range(len(x0)):
        x0[j] = np.random.uniform(bnds[j][0], bnds[j][1])
      res = minimize(lambda x: -ei(x,z,model),
                     x0, method='L-BFGS-B', bounds=bnds)
      if res.fun < min_f:
        min_x = res.x
        min_f = res.fun

    return min_x


  def maximize_mu(z,model):
    def neg_mu(x):
      xz = np.atleast_2d(np.hstack((x,z)))
      return -np.asscalar(model.predict(xz))

    min_f = np.inf
    min_x = None
    for _ in range(100):
      x0 = np.empty(len(bnds))
      for j in range(len(x0)):
        x0[j] = np.random.uniform(bnds[j][0], bnds[j][1])
      res = minimize(neg_mu, x0, method='L-BFGS-B', bounds=bnds)
      if res.fun < min_f:
        min_x = res.x
        min_f = res.fun

    return np.hstack((min_x,-min_f))


  def update(t):
    _XZ = S[:t+1,:,:dim_x+dim_z].reshape((-1,dim_x+dim_z))
    _PI = S[:t+1,:,-1].reshape(-1,1)
    gpr.fit(_XZ,_PI)
    print("Maximizing mu in Year {}/{} ({}/{})".format(t+1,n_iter,tt+1,n_MC))
    for i,z in enumerate(O.Z):
      mu_max[i][t] = maximize_mu(z,gpr)


  """
  Run
  """
  S = np.zeros((n_iter,len(O.Z),dim_x+dim_z+1)) # samples
  mu_max = np.empty((len(O.Z),n_iter,dim_x+1))

  kern = ConstantKernel()*Matern([1.0]*(dim_x+dim_z),
                                 length_scale_bounds=(0.1,10**4),
                                 nu=1.5) + WhiteKernel()
  gpr = GaussianProcessRegressor(kernel=kern,alpha=0,n_restarts_optimizer=20)

  """Prior knowledge"""
  _XZ = list()
  for z in O.Z:
    _XZ.append(list(np.hstack((O.x_prior,z))))
  gpr.set_params(optimizer=None)
  gpr.fit(_XZ,PI_prior)
  gpr.set_params(optimizer="fmin_l_bfgs_b")

  """Initial samples"""
  t = 0
  X = np.empty((len(O.Z),dim_x))
  for j,z in enumerate(O.Z):
    for k in range(dim_x):
      lb = max(bnds[k][0], O.x_prior[k]*.5)
      ub = min(bnds[k][1], O.x_prior[k]*1.5)
      X[j][k] = np.random.uniform(lb,ub)
    S[t,j,:-1] = np.hstack((X[j],z))
    key = O.sites[j]
    O.create_apsim_file(X[j],key)
  O.run_APSIM()
  for j,z in enumerate(O.Z):
    key = O.sites[j]
    S[t][j][-1] = O.get_profit(X[j],key)
  update(t)

  """Experiments"""
  for t in range(1,n_iter):
    _gpr = deepcopy(gpr)
    _gpr.set_params(optimizer=None)
    _XZ = S[:t,:,:-1].reshape((-1,dim_x+dim_z))
    _PI = S[:t,:,-1].reshape((-1,1))
    _NEXT = np.zeros((len(O.Z),dim_x+dim_z))

    _Z = [z for z in O.Z]
    np.random.shuffle(_Z)
    print("Maximizing alpha in Year {}/{} ({}/{})".format(t+1,n_iter,tt+1,n_MC))
    for j,z in enumerate(_Z):
      x = maximize_alpha(z,_gpr)
      _NEXT[j] = np.hstack((x,z))
      """Pseudo-Update"""
      _XZ = np.vstack((_XZ,_NEXT[j]))
      _PI = np.vstack((_PI,np.min(gpr.y_train_))) # worst values
      _gpr.fit(_XZ,_PI) # update
      _gpr.kernel_ = gpr.kernel_

    """Update"""
    for xz in _NEXT:
      z = tuple(xz[6:])
      j = O.Z.index(z)
      S[t,j,:-1] = xz
      key = O.sites[j]
      O.create_apsim_file(xz[:6], key)
    O.run_APSIM()
    for xz in _NEXT:
      z = tuple(xz[6:])
      j = O.Z.index(z)
      key = O.sites[j]
      S[t][j][-1] = O.get_profit(xz[:6], key)
      if S[t][j][-1] > max_xzpi[j][-1]:
        max_xzpi[j] = S[t][j]
    update(t)

  return S, mu_max


for tt in range(n_MC):
  print("{}/{}".format(tt+1,n_MC))
  tick = time.time()
  S, mu_max = run_BO(tt)

  """
  Results
  """
  PI = np.empty((n_iter,len(O.Z)))
  for t in range(n_iter):
    for j,z in enumerate(O.Z):
      x = mu_max[j][t][:6]
      key = O.sites[j]
      O.create_apsim_file(x,key) # create an APSIM file
    O.run_APSIM()
    for j,z in enumerate(O.Z):
      x = mu_max[j][t][:6]
      key = O.sites[j]
      PI[t][j] = O.get_profit(x,key)
      if PI[t][j] > max_xzpi[j][-1]:
        max_xzpi[j] = np.hstack((x,z,PI[t][j]))

  now = datetime.datetime.now()
  fname = "S" + str(year) + "_" + now.strftime("%Y%m%d%H%M%S") + ".pickle"
  with open(fname,"wb") as f:
    pickle.dump(S,f)
  fname = "BOPA" + fname[1:]
  with open(fname,"wb") as f:
    pickle.dump([mu_max,PI],f)

  tock = time.time()
  print("It took {:.0f}s.".format(tock-tick))


now = datetime.datetime.now()
fname = "max_xzpi" + str(year) + "_" + now.strftime("%Y%m%d%H%M%S") + ".pickle"
with open(fname,"wb") as f:
  pickle.dump(max_xzpi,f)
