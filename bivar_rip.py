#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Mar 26 18:12:40 2019

@author: maria reva
"""

import numpy as np
import matplotlib.pyplot as plt
from matplotlib import path
from scipy.spatial.distance import pdist, squareform
from math import pi
import pdb


def PolyArea(x,y):
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

def arc_length(x, y):
    npts = len(x)
    arc = np.sqrt((x[1] - x[0])**2 + (y[1] - y[0])**2)
    for k in range(1, npts):
        arc = arc + np.sqrt((x[k] - x[k-1])**2 + (y[k] - y[k-1])**2)

    return arc



def inpolygon(xq, yq, xv, yv):
    shape = xq.shape
    xq = xq.reshape(-1)
    yq = yq.reshape(-1)
    xv = xv.reshape(-1)
    yv = yv.reshape(-1)
    q = [(xq[i], yq[i]) for i in range(xq.shape[0])]
    p = path.Path([(xv[i], yv[i]) for i in range(xv.shape[0])])
    
    return p.contains_points(q).reshape(shape)


def frac(xp, yp, d, loc_x, loc_y):
    #make circeles centered at loc_x,loc_y
    d_t = d - .05
    th = np.linspace(0, 2*pi, 500)
    xc = d_t * np.cos(th) + loc_x
    yc = d_t* np.sin(th) + loc_y
    # get part of the curves that are inside the window xp yp
    temp=inpolygon(xc, yc, xp, yp)
    indc = np.where(temp > 0)
    # if there is some overlap between the cirlce and the regious
    if len(indc)>0:
        xi = xc[indc]
        yi = yc[indc]
        arclen = arc_length(xi, yi) # get the arclenght of the crive inside the xp yp   
        fract = (2 * pi * d) / arclen # get its fraction
    else:
            fract = 0
            
    return fract

def edge_corr(DIST,xp,yp,loc_x,loc_y):
    
    n=len(DIST);
    w=np.zeros((n,n))
    for i in range(n):
        for j in range(n):
            w[i-1,j-1]=frac(xp,yp,DIST[i-1,j-1],loc_x[i-1],loc_y[i-1]); 
    return w



def Ripley12(locs,dist,area,DIST,w):
    
    N = len(locs);
    b=[];
    K = np.zeros(len(dist));
    for k in range(len(dist)):
        b=(DIST<dist[k]);
        K[k] = sum(w[b])/N;
    
    lamb = N/area;
    K = K/lamb;
    L=np.sqrt(K/pi)-dist; 
    
    return L

def k_function_sim_bivar(loc,loc1,area,dist,sims,xp,yp,level):
        
    L_temp=[]
    n_c=len(loc)
    n_m=len(loc1)
    locs=np.concatenate((loc,loc1))
    n_lo=len(locs)

    an=pdist(locs,"euclidean")
    DIST=squareform(an)
    w=edge_corr(DIST,xp,yp,locs[:,0],locs[:,1])
    dist_int=DIST[0:n_c,n_c:n_lo]
    w_int=w[0:n_c,n_c:n_lo]
    
    L = Ripley12(loc,dist,area,dist_int,w_int)
    
    labels=np.concatenate(( np.zeros(n_c) , np.ones(n_m) ))

    #Now construct envelopes

    index = 10
    print(' ')

    for i in range(sims):
        #Generate Point Pattern
        ind_perm=np.random.permutation(len(labels))
        DIST_R=DIST[ind_perm[:, np.newaxis],ind_perm[np.newaxis,:]]
        dist_r=DIST_R[0:n_c,n_m:n_lo]
        w_r=w[0:n_c,n_m:n_lo]
        loc_c=locs[labels[ind_perm]==0,:]
        #Raw Count of Points
        L_temp.append(Ripley12(loc_c,dist,area,dist_r,w_r))

        if 100*(i/sims)>=index:
            print('percent done = ')
            print(index)
            index += 10;
            
    L_all = np.asarray(L_temp)
    L_all.sort(axis=0)
    L_upper =np.take(L_all,sims*level/100 -1,axis=0)
    L_lower =np.take(L_all,sims - sims*level/100 -1,axis=0)
    L_m=np.mean(L_all,axis=0)

    return(L,L_upper,L_lower,L_all,L_m)
    
    
def MAD_test(L,L_all,ce):
    
    L_null=np.mean(L_all,axis=0)
    n=np.size(L_all,axis=0)
    delta_1=np.sort(np.ndarray.max(np.abs(L_all-L_null),axis=1))
    delta_2=np.max(np.abs(L-L_null))
    
    lev=np.ceil(ce*(n+1)/100)
    #pdb.set_trace()
    H0=delta_2<delta_1[np.int(lev)-1]
    
    p_val=(1+np.sum(delta_2>delta_1))/(n+1)
    pdb.set_trace()
    return (H0,p_val)
    
    
    
#(L,L_upper,L_lower,L_all,L_temp)=k_function_sim_bivar(x,y,1,dist,100,xp,yp,99)
#plt.plot(dist,L)
#plt.plot(dist,L_lower,'g')
#plt.plot(dist,L_upper,'g')
