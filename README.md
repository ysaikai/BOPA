# Machine learning for optimizing complex site-specific management
by Yuji Saikai, [Vivak Patel](http://pages.stat.wisc.edu/~vrpatel6/), and [Paul D. Mitchell](https://aae.wisc.edu/faculty/pdmitchell/)

- APSIM is assumed to be installed on Windows (see ``oracle_m.py`` or ``oracle_h.py`` for more information)
- APSIM files are constructed in advanced for each site and stored in ``oracle_m`` and ``oracle_h`` directories
- Run the following on Windows:
  - ``medium.py`` for simulations with medium complexity
  - ``high.py`` for simulations with high complexity respectively

&nbsp;

**Abstract**

Despite the promise of precision agriculture for increasing the productivity by implementing site-specific management, farmers remain skeptical and its utilization rate is lower than expected. A major cause is a lack of concrete approaches to higher profitability. When involving many variables in both controlled management and monitored environment, optimal site-specific management for such high-dimensional cropping systems is considerably more complex than the traditional low-dimensional cases widely studied in the existing literature, calling for a paradigm shift in optimization of site-specific management. We develop a machine learning algorithm that enables farmers to efficiently learn their own site-specific management through on-farm experiments. We test its performance in two simulated scenarios---one of medium complexity with 150 management variables and one of high complexity with 864 management variables. Results show that, relative to uniform management, site-specific management learned from 5-year experiments generates $43/ha higher profits with 25 kg/ha less nitrogen fertilizer in the first scenario and $40/ha higher profits with 55 kg/ha less nitrogen fertilizer in the second scenario. Thus, complex site-specific management can be learned efficiently and be more profitable and environmentally sustainable than uniform management.

[[preprint](bopa.pdf)], [[published](https://doi.org/10.1016/j.compag.2020.105381)]

&nbsp;

**Learned site-specific management**

![](mngmnt_learned_B0.png)
![](mngmnt_learned_B1.png)
![](mngmnt_learned_B2.png)
