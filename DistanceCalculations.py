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

#print __doc__

# importing site packages and modules
import math
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
import matplotlib.path as mPath
import matplotlib.patches as patches
from PyQt4 import QtCore


# distance function: calculating the distance between 2 points (type: QtCore.QPointF) based on their X and Y coordinates
def distance(point1, point2):
        dx = point1.x() - point2.x()
        dy = point1.y() - point2.y()
        dist = math.hypot(dx, dy)   #hypotenuse function
        return dist

# calculating nearest neighbor and full distance matrix from a give set of data points
def nearestNeighborDistanceCalculation(arrayOfPoints):

    global distanceMatrix
    distanceMatrix = []
    NND_matrix = []

    for i in range(0, len(arrayOfPoints)):
        distanceArray = []
        for j in range(0, len(arrayOfPoints)):
            if(i != j):
                distanceArray.append(distance(arrayOfPoints[i], arrayOfPoints[j]))
            if(i < j):
                distanceMatrix.append(distance(arrayOfPoints[i], arrayOfPoints[j]))

        NND_matrix = np.append(NND_matrix, min(distanceArray))

    # sorting the distance values into increasing order for the cumulative distribution plot
    NND_matrix = np.sort(NND_matrix)
    distanceMatrix = np.sort(distanceMatrix)

    return NND_matrix

def getDistanceMatrix():
    return distanceMatrix

# cumulative probability distribution calculation
def cumulativeProbDistributionCalculation(arrayOfDistances):

    percentage = []

    # sorting the distance values into increasing order for the cumulative distribution plot
    # arrayOfDistances = np.sort(arrayOfDistances)

    # calculating the corresponding percentages
    # percentileofscore 'weak': This kind corresponds to the definition of a cumulative distribution function.
    # A percentileofscore of 80% means that 80% of values are less than or equal to the provided score.
    for i in range(0, len(arrayOfDistances)):
        percentage.append(stats.percentileofscore(arrayOfDistances, arrayOfDistances[i], kind='weak'))

    return percentage

############# NOT USED ################
# calculating the centroid of a polygon
def calculatePolygonCentroid(array):
    # array conversion to the appropriate format (QtCore.QPointF containing list to ordinary numpy array)
    tmpArray = []
    # appending points to an array, then convert it to a shapely Polygon object, on which the centroid function is applicable
    for i in range(0, len(array)):
        tmpPoint = (array[i].x(), array[i].y())
        tmpArray.append(tmpPoint)
    npArray = np.asarray(tmpArray)
    tmpPolygon = Polygon(tmpArray)

    polygonCentroid = QtCore.QPointF(tmpPolygon.centroid.x, tmpPolygon.centroid.y)
    #print 'Centroid:', polygonCentroid
    return polygonCentroid
#######################################

# calculating the centroid of a set of points (gold particle coordinates)
def calculateGoldParticleCentroid(array):
    # array conversion to the appropriate format (QtCore.QPointF containing list to ordinary numpy array)
    tmpArrayX = []
    tmpArrayY = []
    # appending points to a list, then convert it to an array
    for i in range(0, len(array)):
        tmpPointX = array[i].x()
        tmpPointY = array[i].y()
        tmpArrayX.append(tmpPointX)
        tmpArrayY.append(tmpPointY)
    npArrayX = np.asarray(tmpArrayX)
    npArrayY = np.asarray(tmpArrayY)

    centroid = QtCore.QPointF(np.average(npArrayX), np.average(npArrayY))
    #print 'Centroid:', centroid
    return centroid

# calculating gold particles' distances from the polygon centroid
def calculateDistanceFromCentroid(centroid, array):
    distanceArray = []
    for i in range(0, len(array)):
        distanceArray.append(distance(centroid, array[i]))

    distanceArray = np.sort(distanceArray)
    return distanceArray


# calculating polygon area with the shoelace formula
def PolygonArea(arrayOfPoints):
    polyArea = 0.0
    # check the input data type, and proceed accordingly (QPointF or numpy array)
    if(type(arrayOfPoints[0]) == QtCore.QPointF):
        for i in range(0, len(arrayOfPoints)):
            j = (i + 1) % len(arrayOfPoints)
            polyArea += arrayOfPoints[i].x() * arrayOfPoints[j].y()
            polyArea -= arrayOfPoints[j].x() * arrayOfPoints[i].y()
    if(type(arrayOfPoints[0]) == np.ndarray):
        for i in range(0, len(arrayOfPoints)):
            j = (i + 1) % len(arrayOfPoints)
            polyArea += arrayOfPoints[i][0] * arrayOfPoints[j][1]
            polyArea -= arrayOfPoints[j][0] * arrayOfPoints[i][1]
    polyArea = abs(polyArea) / 2.0
    return polyArea


# visualize data in a saved PDF file
def visualizeData(smallNNDdistanceArray, smallNNDpercentage, smallFullDistanceArray, smallFullPercentage, largeNNDdistanceArray, largeNNDpercentage, largeFullDistanceArray, largeFullPercentage, areaPath, smallDataPointsWithin, largeDataPointsWithin, pdf, sceneWidth, sceneHeight):

    fig = plt.figure(figsize = (16,12)) # in inches

    ax1 = fig.add_subplot(121)
    patch = patches.PathPatch(areaPath, facecolor = 'orange', lw = 2, ls = 'dashdot')
    ax1.add_patch(patch)
    for i in range(0, len(smallDataPointsWithin)):
        ax1.plot(smallDataPointsWithin[i].x(), smallDataPointsWithin[i].y(), 'go')
    for i in range(0, len(largeDataPointsWithin)):
        ax1.plot(largeDataPointsWithin[i].x(), largeDataPointsWithin[i].y(), 'bo')
    ax1.set_xlim(0, sceneWidth)
    ax1.set_ylim(0, sceneHeight)
    ax1.set_title('Synaptic area with randomly generated gold particles', fontsize = 12)
    ax1.set_xlabel('Distance (um)', fontsize = 10)
    ax1.set_ylabel('Distance (um)', fontsize = 10)

    ax2 = fig.add_subplot(222)
    smallLabel = 'Small, n = ' + str(len(smallNNDpercentage))
    largeLabel = 'Large, n = ' + str(len(largeNNDpercentage))
    ax2.set_ylim(0, 101)
    ax2.plot(smallNNDdistanceArray, smallNNDpercentage, 'g-', label = smallLabel)
    ax2.plot(largeNNDdistanceArray, largeNNDpercentage, 'b-', label = largeLabel)
    ax2.set_title('Nearest Neighbor Distance', fontsize = 12)
    ax2.set_xlabel('Distance (um)', fontsize = 10)
    ax2.set_ylabel('Cumulative probability distribution (%)', fontsize = 10)
    plt.legend(loc = 'lower right')

    ax3 = fig.add_subplot(224)
    ax3.set_ylim(0, 101)
    ax3.plot(smallFullDistanceArray, smallFullPercentage, 'g-')
    ax3.plot(largeFullDistanceArray, largeFullPercentage, 'b-')
    ax3.set_title('All distances', fontsize = 12)
    ax3.set_xlabel('Distance (um)', fontsize = 10)
    ax3.set_ylabel('Cumulative probability distribution (%)', fontsize = 10)

    pdf.savefig()
    plt.close()

    return 0

# this function is used for 2D spatial autocorrelation function calculation, the mask size will cover the X-Y dimensions of the labelled AZ
def getSynapticAreaOutlineBorders(listOfCoordinates):

        xcoord = []
        ycoord = []
        for i in range(0, len(listOfCoordinates)):
            xcoord.append(listOfCoordinates[i].x())
            ycoord.append(listOfCoordinates[i].y())

        #print 'xrange:', min(xcoord), max(xcoord)
        #print 'yrange:', min(ycoord), max(ycoord)

        maskSize = [(int(np.around(min(xcoord))), int(np.around(max(xcoord))), int(np.around(min(ycoord))), int(np.around(max(ycoord))))]
        return maskSize

# this function calculates the distance of a given set of gold particles from their nearest edge of the synaptic AZ
def getDistanceFromNearestEdge(listOfParticleCoordinates, listOfEdgeCoordinates):

    # calculate distances from each gold localization to each edge point, and store the data in a matrix
    distanceMatrixFromEdges = []
    for i in range(0, len(listOfParticleCoordinates)):
        distanceArray = []
        for j in range(0, len(listOfEdgeCoordinates)):
            # getting triangle side values
            if(j < len(listOfEdgeCoordinates) - 1):
                a = distance(listOfEdgeCoordinates[j], listOfEdgeCoordinates[j + 1])
                b = distance(listOfEdgeCoordinates[j], listOfParticleCoordinates[i])
                c = distance(listOfEdgeCoordinates[j + 1], listOfParticleCoordinates[i])
            if(j == len(listOfEdgeCoordinates) - 1):
                a = distance(listOfEdgeCoordinates[j], listOfEdgeCoordinates[0])
                b = distance(listOfEdgeCoordinates[j], listOfParticleCoordinates[i])
                c = distance(listOfEdgeCoordinates[0], listOfParticleCoordinates[i])

            # calculate the height for side "a" from the formula of the triangle's general altitude theorem
            # this value will be the distance from a given gold localization to its nearest edge
            ma = (np.sqrt((a+b+c)*(-a+b+c)*(a-b+c)*(a+b-c)))/(2*a)
            distanceArray.append(ma)

        distanceMatrixFromEdges.append(min(distanceArray))

    # sorting the distance values in an increasing order
    distanceMatrixFromEdges = np.sort(np.asarray(distanceMatrixFromEdges))
    return distanceMatrixFromEdges

# get the index of the first element in the array which is bigger than a given value
def getElementIndex(value, array):
    if(value < array[0]):
        return '-INF'
    if(value > array[-1]):
        return '+INF'
    else:
        if(value == array[-1]):
            return len(array)
        for i in range(0, len(array) - 1):
            if(value >= array[i] and value < array[i + 1]):
                return i + 2

# calculates the closest localization point for all points within the labelled polygon area
def calculateEmptyCircle(listOfEdgeCoordinates, listOfParticleCoordinates, radiusThreshold, AZedgeInclusion, plotLabel):    # radius threshold in nm

    biggestEmptyCirclePathList = []
    biggestEmptyCircleRadiiList = []
    biggestEmptyCircleCenterList = []

    # creating a matplotlib path from the synaptic AZ outline points
    tmpVec = []
    for i in range(0, len(listOfEdgeCoordinates)):
        tmpPoint = [listOfEdgeCoordinates[i].x(), listOfEdgeCoordinates[i].y()]
        tmpVec.append(tmpPoint)
    AZpolygonPath = mPath.Path(tmpVec)

    # get the X-Y dimensions of the synaptic AZ
    extent = getSynapticAreaOutlineBorders(listOfEdgeCoordinates)

    # within the synaptic AZ, for every data point (pixelwise), measure the closest gold labelling (which will be the radius of the largest empty circle from the given data point)
    for i in range(extent[0][0], extent[0][1]+1):
        for j in range(extent[0][2], extent[0][3]+1):
            tmpPoint = QtCore.QPointF(i, j)
            tmpDistanceVec = []
            if(AZpolygonPath.contains_point((tmpPoint.x(), tmpPoint.y()), None, 0.0) == True):
                for k in range(0, len(listOfParticleCoordinates)):
                    tmpDistance = distance(tmpPoint, listOfParticleCoordinates[k])
                    tmpDistanceVec.append(tmpDistance)

                minDistance = min(tmpDistanceVec)
                tmpCircle = mPath.Path.circle(center=(tmpPoint.x(), tmpPoint.y()), radius=minDistance)
                if(AZedgeInclusion == True):
                    if not(tmpCircle.intersects_path(AZpolygonPath, filled=False)) and minDistance >= radiusThreshold:
                        biggestEmptyCirclePathList.append(tmpCircle)
                        biggestEmptyCircleRadiiList.append(minDistance)
                        biggestEmptyCircleCenterList.append(tmpPoint)
                if(AZedgeInclusion == False):
                    if(minDistance >= radiusThreshold):
                        biggestEmptyCirclePathList.append(tmpCircle)
                        biggestEmptyCircleRadiiList.append(minDistance)
                        biggestEmptyCircleCenterList.append(tmpPoint)

    finalEmptyCirclePathList = []
    finalEmptyCircleRadiiList = []
    finalEmptyCircleCenterList = []

    # iteratively find the biggest circle in the list, delete it, then delete every circles within largest one; repeat this until the list is not empty
    while(len(biggestEmptyCirclePathList) != 0):
        maxIndex = biggestEmptyCircleRadiiList.index(max(biggestEmptyCircleRadiiList))

        finalEmptyCirclePathList.append(biggestEmptyCirclePathList[maxIndex])
        finalEmptyCircleRadiiList.append(biggestEmptyCircleRadiiList[maxIndex])
        finalEmptyCircleCenterList.append(biggestEmptyCircleCenterList[maxIndex])

        del biggestEmptyCirclePathList[maxIndex]
        del biggestEmptyCircleRadiiList[maxIndex]
        del biggestEmptyCircleCenterList[maxIndex]

        indexVec = []

        for i in range(0, len(biggestEmptyCirclePathList)):
            if (finalEmptyCirclePathList[-1].contains_point((biggestEmptyCircleCenterList[i].x(), biggestEmptyCircleCenterList[i].y()), None, 0.0) == True and finalEmptyCirclePathList[-1].intersects_path(biggestEmptyCirclePathList[i], filled=True)):
                indexVec.append(i)

        for i in range(1, len(indexVec)+1):
            del biggestEmptyCirclePathList[indexVec[-i]]
            del biggestEmptyCircleRadiiList[indexVec[-i]]
            del biggestEmptyCircleCenterList[indexVec[-i]]

    # final vector to store data in
    emptyCircleDataVec = []
    for i in range(0, len(finalEmptyCircleRadiiList)):
        emptyCircleDataVec.append((finalEmptyCircleCenterList[i], finalEmptyCircleRadiiList[i]))

    if(plotLabel == 1):
        # plot data
        fig = plt.figure(figsize=(8, 6))  # in inches
        ax1 = fig.add_subplot(111, aspect='equal')
        patch = patches.PathPatch(AZpolygonPath, facecolor='orange', lw=2, ls='dashdot')
        ax1.add_patch(patch)
        for i in range(0, len(listOfParticleCoordinates)):
            ax1.plot(listOfParticleCoordinates[i].x(), listOfParticleCoordinates[i].y(), 'ko')
        ax1.set_xlim(extent[0][0]-1, extent[0][1]+1)
        ax1.set_ylim(extent[0][2]-1, extent[0][3]+1)
        for i in range(0, len(finalEmptyCirclePathList)):
            circ = plt.Circle((finalEmptyCircleCenterList[i].x(), finalEmptyCircleCenterList[i].y()), radius=finalEmptyCircleRadiiList[i], color='g', fill=False)
            ax1.add_patch(circ)
            ax1.plot(finalEmptyCircleCenterList[i].x(), finalEmptyCircleCenterList[i].y(), 'gx')
        ax1.set_title('Synaptic AZ with gold particle labelling', fontsize=20)
        ax1.set_xlabel('Distance (pixel)', fontsize=16)
        ax1.set_ylabel('Distance (pixel)', fontsize=16)
        plt.show()

    return emptyCircleDataVec