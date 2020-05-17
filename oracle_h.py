import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
import pickle
import subprocess
import sys
import os

class Oracle():
  # path to the directory .apsim files for oracle
  fpath = "C:\\Users\\saikai\\Documents\\BOPA\\oracle_h\\"
  loc_apsim = "C:\\Program Files (x86)\\APSIM710-r4158\\Model\\Apsim.exe"
  x_names = ["density",
             "depth",
             "row space",
             "N pre-sow",
             "N at sow",
             "N topdress"]
  factor_names = ["density",
                  "depth",
                  "row_spacing",
                  "fert_amount_pre_sow",
                  "fert_amount_sow",
                  "fert_amount_TopDress"]
  bnds = ( # lower and upper bounds of x
    (6.0,10.0),
    (25,150),
    (0.4,1.0),
    (0,200),
    (0,200),
    (0,200)
  )
  """2004-2013 prices"""
  _p = [0.07835,0.07638,0.11929,0.16890,0.16142,
        0.14134,0.20591,0.24409, 0.27244, 0.17677]
  out_prices = dict(zip(range(2004,2014), _p))
  _p = [0.00100,0.00134,0.00150,0.00182,0.00210,
        0.00313,0.00344,0.00325,0.00340,0.00364]
  seed_prices = dict(zip(range(2004,2014), _p))
  _p = [0.55556,0.66667,0.77778,0.68889,1.02222,
        1.51111,0.73333,1.13333,1.40000,1.28889]
  N_prices = dict(zip(range(2004,2014), _p))

  """Uniform management"""
  # gathered from the extension service in Iowa
  Xs_prior = {
    2013: [8, 50, .76, 67, 67, 67],
    2012: [8, 50, .76, 70, 70, 70],
    2011: [8, 50, .76, 74, 74, 74],
    2010: [8, 50, .76, 77, 77, 77],
    2009: [8, 50, .76, 59, 59, 59],
    2008: [8, 50, .76, 69, 69, 69],
    2007: [8, 50, .76, 74, 74, 74],
    2006: [8, 50, .76, 68, 68, 68],
    2005: [8, 50, .76, 64, 64, 64],
    2004: [8, 50, .76, 68, 68, 68]
  }


  def __init__(self,year=2013):
    with open("sites.pickle","rb") as f:
      self.sites = pickle.load(f)
    with open("Z.pickle","rb") as f:
      self.Z = pickle.load(f)
    self.year = year
    self.out_price = type(self).out_prices[year]
    self.seed_price = type(self).seed_prices[year]
    self.N_price = type(self).N_prices[year]
    self.x_prior = type(self).Xs_prior[year]


  def create_apsim_file(self, x, key):
    fname = "o{:03d}_{:03d}".format(key[0],key[1])
    f_in = type(self).fpath + fname + ".apsim"

    tree = ET.parse(f_in)

    elem = tree.find(".//start_date")
    elem.text = "01/01/"+str(self.year)
    elem = tree.find(".//end_date")
    elem.text = "31/12/"+str(self.year)
    elem = tree.find(".//date1") # sowing window START data
    elem.text = "15-apr"
    elem = tree.find(".//date2") # sowing window END data
    elem.text = "2-may"

    factors = dict()
    for i,factor_name in enumerate(type(self).factor_names):
      factors[factor_name] = tree.find(".//"+factor_name)
      # round to avoid APSIM errors
      factors[factor_name].text = str(round(x[i],3))
    tree.write(f_in)


  def run_APSIM(self):
    subprocess.run([type(self).loc_apsim, type(self).fpath+"o*.apsim"])


  def get_yield(self, key):
    fname = "o{:03d}_{:03d}".format(key[0],key[1])
    f_out = type(self).fpath + fname + ".out"
    df = pd.read_csv(f_out,delim_whitespace=True,header=2,skiprows=range(3,4))

    return df["yield"].iloc[0]


  def get_profit(self, x, key):
    y = self.get_yield(key)
    pi = (self.out_price*y -
          self.seed_price*x[0]*10**4 -
          self.N_price*x[3] -
          self.N_price*x[4] -
          self.N_price*x[5])

    return pi
