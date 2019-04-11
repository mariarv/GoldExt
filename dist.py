#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Mar 27 12:57:30 2019

@author: maria
"""

import numpy as np
import scipy.spatial.distance as dist
 
XA = np.random.rand(4,2)
XB = np.random.rand(4,2)
print ("XA :")
print (XA)
print ("Size XA :")
print (XA.size)
print ("XB :")
print (XB)
print ("Size XB :")
print (XB.size)
my_pairwise_dist = dist.pdist(XA,"euclidean")
my_individual_dist = dist.cdist(XA,XB,"euclidean")
print ("Euclidean Pairwise Distance for XA :")
print (my_pairwise_dist)
print ("Euclidean Distance between XA and XB :")
print (my_individual_dist)