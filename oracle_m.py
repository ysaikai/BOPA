import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
import pickle
import subprocess
import sys
import os

class Oracle():
  # path to the directory .apsim files for oracle
  fpath = "C:\\Users\\saikai\\Documents\\BOPA\\oracle_m\\"
  loc_apsim = "C:\\Program Files (x86)\\APSIM710-r4158\\Model\\Apsim.exe"
  x_names = ["density",
             "depth",
             "row space",
             "N pre-sow",
             "N at sow",
             "N topdress"]
  Z1 = (231, 259, 288, 317, 346) # PAWC
  Z2 = (2.56, 2.88, 3.2, 3.52, 3.84) # OC(%) for 0-5 depth
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
  # obtained by implementing x_prior in APSIM
  PIs_prior = {
    2013: [ 927., 927., 927., 928., 928.,1092.,1095.,1098.,1100.,1101.,1253.,
           1256.,1260.,1264.,1267.,1386.,1394.,1400.,1405.,1410.,1470.,1478.,
           1485.,1493.,1502.],
    2012: [1039.,1060.,1076.,1090.,1108.,1256.,1253.,1266.,1282.,1270.,1456.,
           1506.,1516.,1533.,1541.,1632.,1683.,1743.,1777.,1805.,1777.,1825.,
           1878.,1931.,1973.],
    2011: [2179.,2195.,2205.,2206.,2208.,2203.,2216.,2220.,2221.,2222.,2208.,
           2218.,2220.,2221.,2223.,2211.,2219.,2220.,2222.,2223.,2213.,2220.,
           2221.,2222.,2224.],
    2010: [1796.,1797.,1798.,1799.,1800.,1796.,1797.,1797.,1798.,1799.,1795.,
           1796.,1797.,1798.,1798.,1795.,1796.,1796.,1797.,1798.,1795.,1795.,
           1796.,1797.,1797.],
    2009: [1054.,1055.,1055.,1055.,1056.,1096.,1096.,1097.,1097.,1097.,1115.,
           1115.,1115.,1116.,1116.,1118.,1118.,1118.,1119.,1119.,1118.,1118.,
           1118.,1119.,1119.],
    2008: [1382.,1382.,1382.,1382.,1383.,1382.,1382.,1382.,1382.,1383.,1382.,
           1382.,1382.,1382.,1383.,1382.,1382.,1382.,1382.,1383.,1382.,1382.,
           1382.,1382.,1383.],
    2007: [1461.,1478.,1488.,1492.,1496.,1540.,1559.,1570.,1576.,1581.,1612.,
           1621.,1630.,1636.,1642.,1656.,1661.,1667.,1673.,1677.,1681.,1686.,
           1692.,1694.,1695.],
    2006: [ 965., 966., 967., 968., 969.,1011.,1012.,1012.,1014.,1015.,1038.,
           1039.,1040.,1041.,1043.,1054.,1055.,1057.,1058.,1059.,1064.,1065.,
           1066.,1068.,1069.],
    2005: [580.,592.,605.,620.,629.,604.,614.,625.,637.,644.,617.,627.,637.,
           647.,650.,623.,633.,644.,650.,650.,648.,654.,659.,662.,664.],
    2004: [711.,711.,711.,711.,711.,711.,711.,711.,711.,711.,711.,711.,711.,
           711.,711.,711.,711.,711.,711.,711.,711.,711.,711.,711.,711.]
  }


  def __init__(self,year=2013):
    self.year = year
    self.out_price = type(self).out_prices[year]
    self.seed_price = type(self).seed_prices[year]
    self.N_price = type(self).N_prices[year]
    self.x_prior = type(self).Xs_prior[year]
    self.PI_prior = type(self).PIs_prior[year]


  def create_apsim_file(self, x, z):
    z1,z2 = z
    fname = "oracle_{:.0f}_{:.0f}".format(z1,z2*100)
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
    subprocess.run([type(self).loc_apsim, type(self).fpath+"oracle*.apsim"])


  def get_yield(self, z):
    z1,z2 = z
    fname = "oracle_{:.0f}_{:.0f}".format(z1,z2*100)
    f_out = type(self).fpath + fname + ".out"
    df = pd.read_csv(f_out,delim_whitespace=True,header=2,skiprows=range(3,4))

    return df["yield"].iloc[0]


  def get_profit(self, x, z):
    y = self.get_yield(z)
    pi = (self.out_price*y -
          self.seed_price*x[0]*10**4 -
          self.N_price*x[3] -
          self.N_price*x[4] -
          self.N_price*x[5])

    return pi
