'''
    GoldExt - objective quantification of nanoscale protein distributions
    Copyright (C) 2017 Miklos Szoboszlay -  contact: mszoboszlay(at)gmail(dot)com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

from sklearn.cluster import DBSCAN, KMeans, AffinityPropagation, MeanShift, estimate_bandwidth, spectral_clustering
from sklearn.preprocessing import StandardScaler
#from sklearn.feature_extraction import image
import math
import numpy as np
import matplotlib.pyplot as plt
from itertools import cycle
from scipy.stats import sem
from scipy.spatial import Voronoi
from matplotlib import cm
from PyQt5 import QtCore
import DistanceCalculations
import ClusterGui
import MainGUI
import random

#from sklearn.neighbors import typedefs

# converts the PyQt.QtCore.QPointF format to simple floats to be able to perform the clustering
def convertArrayFormat(array1, array2, array3):
    convertedArray = []
    for i in range(0, len(array1)):
        convertedArray.append([array1[i].x(), array1[i].y()])
    for i in range(0, len(array2)):
        convertedArray.append([array2[i].x(), array2[i].y()])
    for i in range(0, len(array3)):
        convertedArray.append([array3[i].x(), array3[i].y()])
    return convertedArray

# DBSCAN - Density-Based Spatial Clustering of Applications with Noise. Finds core samples of high density and expands clusters from them. Good for data which contains clusters of similar density.
def dbscanClustering(array1, array2, array3, epsilon, numberOfMinSamples):
    convertedArray = convertArrayFormat(array1, array2, array3)
    convertedArray = StandardScaler(with_mean = False, with_std = False).fit_transform(convertedArray)
    # Compute DBSCAN
    db = DBSCAN(eps = epsilon, min_samples = numberOfMinSamples, metric='euclidean').fit(convertedArray)
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_

    # Number of clusters in labels, ignoring noise if present.
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)

    # print labels
    # unique, counts = np.unique(labels, return_counts=True)
    #
    # print unique, counts
    #
    # unique2, counts2 = np.unique(counts, return_counts=True)
    # print unique2, counts2

    #for i in range(0, n_clusters_):
    #    print 'element: %0.0f, occurence: %0.0f' % (i, labels.count(i))

    print ('-----')
    print ('Number of clusters: ', n_clusters_)

    # visualize data
    # Black removed and is used for noise instead.
    unique_labels = set(labels)
    colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))
    fig = plt.figure(figsize = (16,12)) # in inches
    for k, col in zip(unique_labels, colors):
        if k == -1:
            # Black used for noise.
            col = 'k'

        class_member_mask = (labels == k)

        xy = convertedArray[class_member_mask & core_samples_mask]
        plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=col,
                 markeredgecolor='k', markersize=14)

        xy = convertedArray[class_member_mask & ~core_samples_mask]
        plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=col,
                 markeredgecolor='k', markersize=6)

    plt.title('Estimated number of clusters: %d' % n_clusters_)
    plt.show()

    return convertedArray, labels

# affinity propagation clustering
def affinityPropagationClustering(array1, array2, array3, pref):
    convertedArray = convertArrayFormat(array1, array2, array3)
    arrayToSave = convertedArray
    convertedArray = StandardScaler().fit_transform(convertedArray)
    # Compute affinity propagation
    af = AffinityPropagation(preference = pref).fit(convertedArray)

    cluster_centers_indices = af.cluster_centers_indices_
    labels = af.labels_

    n_clusters_ = len(cluster_centers_indices)
    print ('-----')
    print ('Number of clusters: ', n_clusters_)

    fig = plt.figure(figsize = (16,12)) # in inches

    colors = cycle('bgrcmykbgrcmykbgrcmykbgrcmyk')
    for k, col in zip(range(n_clusters_), colors):
        class_members = labels == k
        cluster_center = convertedArray[cluster_centers_indices[k]]
        plt.plot(convertedArray[class_members, 0], convertedArray[class_members, 1], col + '.')
        plt.plot(cluster_center[0], cluster_center[1], 'o', markerfacecolor=col, markeredgecolor='k', markersize=14)

        for x in convertedArray[class_members]:
            plt.plot([cluster_center[0], x[0]], [cluster_center[1], x[1]], col)

    plt.title('Estimated number of clusters: %d' % n_clusters_)
    plt.show()

    return arrayToSave, labels

# MeanShift clustering
def meanShiftClustering(array1, array2, array3, numberOfMinSamples):
    convertedArray = convertArrayFormat(array1, array2, array3)
    arrayToSave = convertedArray
    convertedArray = StandardScaler().fit_transform(convertedArray)
    if (len(convertedArray) > 3):
        # Compute MeanShift
        # bandwidth = estimate_bandwidth(convertedArray, quantile = 0.2, n_samples = 500)
        # ms = MeanShift(bandwidth = bandwidth, bin_seeding = True)
        ms = MeanShift()
        ms.fit(convertedArray)
        labels = ms.labels_
        cluster_centers = ms.cluster_centers_

        # couting the number of members for each cluster and assign clusters with less than 'numberOfMinSamples' members to noise
        counterVec = ([])
        maxLabel = max(labels)
        labels = list(labels)
        for i in range(0, maxLabel + 1):
            counterVec = np.append(counterVec, labels.count(i))

        # checking the labels whose number is less than 'numberOfMinsSamples'
        noiseLabelVec = ([])
        for i in range(0, len(counterVec)):
            if (counterVec[i] < numberOfMinSamples):
                noiseLabelVec = np.append(noiseLabelVec, i)

        # creating new labels, with excluding those whose number is less than 'numberOfMinSamples' and handle them as noise
        newLabels = []
        for i in range(0, len(labels)):
            if (np.any(noiseLabelVec == labels[i])):
                newLabels.append(-1)
            else:
                newLabels.append(labels[i])

        # changing labels to match those of other clustering algorithms
        for i in range(0, len(newLabels)):
            # decrease labelling uniformly by 1
            newLabels[i] -= 1

        # changing the -1 labels to max, and -2 labelling back to the original -1
        maxLabel = max(newLabels)
        for i in range(0, len(newLabels)):
            if (newLabels[i] == -1):
                newLabels[i] = (maxLabel + 1)
            if (newLabels[i] == -2):
                newLabels[i] = -1
            else:
                pass

        # Number of clusters in labels, ignoring noise if present
        labels_unique = np.unique(newLabels)
        n_clusters_ = len(set(labels_unique)) - (1 if -1 in newLabels else 0)
    else:
        n_clusters_ = 0

    print ('number of estimated clusters : %d' % n_clusters_)

    fig = plt.figure(figsize = (16,12)) # in inches
    colors = cycle('bgrcmykbgrcmykbgrcmykbgrcmyk')

    newLabels = np.asarray(newLabels) # for accurate plotting
    for k, col in zip(range(n_clusters_), colors):
        my_members = newLabels == k
        cluster_center = cluster_centers[k]
        plt.plot(convertedArray[my_members, 0], convertedArray[my_members, 1], col + '.')
        plt.plot(cluster_center[0], cluster_center[1], 'o', markerfacecolor=col, markeredgecolor='k', markersize=14)
    plt.title('Estimated number of clusters: %d' % n_clusters_)
    plt.show()

    return arrayToSave, newLabels

############################
# 2D spatial autocorrelation
############################

# converting cartesian to polar coordinates
def cartesianToPolar(x, y):
    # return r, theta (degress)
    r = math.hypot(x, y)
    theta = math.degrees(math.atan2(y, x))
    return(r, theta)

# this function binarize the imported image, zeros everywhere except the user-defined localization points for small gold particles
def convertImageToBinary(image, localizationCoordinates):
    binarizedImage = np.zeros((image.width(), image.height()))
    for i in range(0, len(localizationCoordinates)):
        binarizedImage[(int(np.around(localizationCoordinates[i].x())), int(np.around(localizationCoordinates[i].y())))] = 1  # rounding is needed since zooming could result in non-integer type coordinates
    return binarizedImage

def calculateSpatialAutocorrelationFunction(image, maskSize, localizationCoordinates, rmax, nmPixelRatio, binning_factor, boolPlotData, boolSaveData, loc):
    # binarizing the image
    binarizedImage = convertImageToBinary(image, localizationCoordinates)

#    if(boolSaveData == 1):
#        # save binarizedImage into an ASCII file for MATLAB testing
#        filename = MainGUI.openedFilename[0:-4] + '_binarized_image.dat'
#        f = open(filename, 'w')
#
#        for i in range(0, len(binarizedImage)):
#            for j in range(0, len(binarizedImage[i])):
#                s = str(str(int(binarizedImage[i][j])) + ' ')
#                f.write(s)
#            f.write('\n')
#        f.close()
#        print '-----'
#        print 'Binarized image saved'

    # region of interest, to autocorrelate the whole image, should have the same size as whole image
    # mask = np.ones((image.width(), image.height()))
    # region of interest, to autocorrelate just the AZ (the smallest rectangle that encloses the AZ)
    mask = np.ones(((maskSize[0][1] - maskSize[0][0]), (maskSize[0][3] - maskSize[0][2])))


    # labelling density calculation
    # for the whole image
    # totalArea = image.width() * image.height()  # in pixels
    # for the smallest rectangle that encloses the AZ
    totalArea = (maskSize[0][1] - maskSize[0][0]) * (maskSize[0][3] - maskSize[0][2])
    n_loc = float(len(localizationCoordinates))   # else the result is going to be zero
    density = n_loc/totalArea

    ##########################################################################
    # from this point on, based on Veatch et al, 2012; supplementary File_S1.m
    ##########################################################################

    L1 = image.height() + rmax    # for correct size zero padding
    L2 = image.width() + rmax   # for correct size zero padding


    # normalization factor in the denominator
    tmp_NP = abs(np.fft.fft2(mask, (L1, L2)))
    tmp_NP = np.square(tmp_NP)

    NP = (np.fft.fftshift(np.fft.ifft2(tmp_NP))).real

    # spatial autocorrelation function
    tmp_G1 = abs(np.fft.fft2(binarizedImage, (L1, L2)))
    tmp_G1 = np.square(tmp_G1)
    G1 = (np.fft.fftshift(np.fft.ifft2(tmp_G1)).real/(NP*density**2))

    # cropping the image
    xmin = (int(L2/2+1)) - rmax - 1 # for some reason, indexing is changed (L1 reflects to width)
    ymin = (int(L1/2+1)) - rmax - 1
    new_width = 2*rmax
    new_height = 2*rmax

    rangeX = range(xmin, (xmin + new_width + 1))
    rangeY = range(ymin, (ymin + new_height + 1))

    # 'crop' G1 to the appropriate size
    G = G1[rangeX, :]
    G = G[:, rangeY]

    # map to x positions with center x = 0
    x_multiplier = []
    for i in range(-rmax, rmax+1):
        x_multiplier.append(i)
    x_multiplier = np.asarray(x_multiplier)
    
    xvals = np.ones((2*rmax+1, 1))*x_multiplier # should be a column vector converted into a matrix (2*rmax+1 times)

    # map to y positions with center y = 0
    y_multiplier = x_multiplier.reshape(2*rmax+1, 1)

    yvals = y_multiplier*np.ones((1, 2*rmax+1))

    zvals = G

    r = []
    theta = []
    for i in range(0, len(xvals)):
        tmp_r = []
        tmp_theta = []
        for j in range(0, len(xvals[i])):
            a = cartesianToPolar(xvals[i][j], yvals[i][j])
            tmp_r.append(a[0])
            tmp_theta.append(math.radians(a[1]))    # in Veatch et al., 2012, theta is in radians, conversion is needed from degree to radian
        r.append(tmp_r)
        theta.append(tmp_theta)

    r = np.asarray(r)
    theta = np.asarray(theta)

    Ar = r.reshape(1, (2*rmax+1)**2)

    Avals = []
    for i in range(0, len(zvals)):
        for j in range(0, len(zvals[0])):
            Avals.append(zvals[j][i])

    rr = np.sort(Ar)        # sort by r values
    ind = np.argsort(Ar)    # sorting based on index, for later reindexing g

    # ind is FAILED to reproduce from MATLAB, but this could be because of the similar values of rr

    vv = np.zeros((1, len(Avals)))
    for i in range(0, len(ind[0])):
        vv[0][i] = Avals[ind[0][i]]  # reindex g

    # until here, sorted Avals are equal in MATLAB code from Veatch et al., 2012 and GoldExt, binning could result in different output of the scripts

    # the radii to extract
    global radii
    radii = []
    #binning_factor = 5
    for i in range(0, int((max(rr[0]) + 1) / binning_factor)):
        radii.append(i * binning_factor)

    binned_data = np.histogram(rr, bins = len(radii))
    a = binned_data[1][1:]  # the first value is zero which we do not need

    # binned_index variable is a locigal, and gives 1s where the bin number matches, 0s else
    binned_index = np.digitize(rr, a)   # little jitter compared to the MATLAB code

    g = []
    sd_g = []
    for i in range(1, rmax+1):
        index_count = 0
        tmp_g = []
        for j in range(0, len(binned_index[0])):
            if(binned_index[0][j] == i):
                index_count += 1
                tmp_g.append(vv[0][j])
            else:
                pass
        if(index_count == 0):
            pass
        else:
            tmp_g = np.asarray(tmp_g)
            g.append(np.average(tmp_g))
            sd_g.append(np.std(tmp_g))

    #print g[:-1]
    #radii = radii[:len(g)]
    #print len(g), len(sd_g), len(radii)

    # resize arrays to contain data up to rmax
    g = g[1: (radii.index(rmax) + 1)]
    sd_g = sd_g[1: (radii.index(rmax) + 1)]
    radii = radii[1: (radii.index(rmax))]

    #print len(g), len(sd_g), len(radii)

    radii = np.asarray(radii)
    conv_radii = radii / nmPixelRatio

    if(boolPlotData == True):
        constantX = [0, 500]
        constantY = [1, 1]

        fig = plt.figure(figsize=(8,6))
        g_plot = fig.add_subplot(111)
        #g_plot.errorbar(radii, g, sd_g)
        g_plot.plot(conv_radii, g, 'k-')
        g_plot.plot(constantX, constantY, 'r-')
        g_plot.set_title('2D autocorrelation')
        g_plot.set_autoscaley_on(False)
        g_plot.set_xlim([0.5, np.amax(conv_radii) + 1.5])
        g_plot.set_xlabel('Radius (nm)')
        g_plot.set_ylabel('g(r)')

        plt.show()

    if(boolSaveData == True):
        # save 2D autocorrelation function into an ASCII file
        if(loc == 0):
            filename = MainGUI.openedFilename[0][0:-4] + '_g(r)_rmax' + str(int(np.around(rmax/MainGUI.nmPixelRatio))) + 'nm.dat'
        if(loc == 1):
            filename = ClusterGui.clusterOpenedFilename[0][0:-4] + '_g(r)_rmax' + str(int(np.around(rmax/MainGUI.nmPixelRatio))) + 'nm.dat'
        f = open(filename, 'w')

        for i in range(0, len(g)):
            value0 = str(radii[i] / MainGUI.nmPixelRatio)
            value1 = str(g[i])
            s = str(value0 + '  ' + value1 + '\n')
            f.write(s)
        f.close()
        print ('-----')
        print ('g(r) saved at ' + filename)

    return [conv_radii, g]

################################
# end of spatial autocorrelation
################################
