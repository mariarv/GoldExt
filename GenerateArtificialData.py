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

# importing site packages
import matplotlib.path as mPath
#import matplotlib.patches as mPatch
import DistanceCalculations
import random
import numpy as np
#import time
from PyQt5 import QtCore

# generating N number of randomly distributed data points
def generateRandomData(lowerBound_X, upperBound_X, lowerBound_Y, upperBound_Y):
    randomDataPoint_X = random.randint(int(lowerBound_X), int(upperBound_X))
    randomDataPoint_Y = random.randint(int(lowerBound_Y), int(upperBound_Y))

    # data type QPointF is necessary for the comparison between the drawn (experimental) and generated data
    dataPoint = QtCore.QPointF(randomDataPoint_X, randomDataPoint_Y)
    return dataPoint

def generateSetOfRandomDataPoints(areaPath, polygonPathList, boolWithin, numberOfDataPoints, minDistance, lowerBound_X, upperBound_X, lowerBound_Y, upperBound_Y):

    global pointListWithin
    # while cycle, which stops when a previously user-defined parameter 'numOfPointsWithin' is reached,
    # therefore we have enough data points within the synaptic area

    pointsWithin = 0
    pointListWithin = ([])
    while pointsWithin < numberOfDataPoints:
        # generating a random data point
        tmpPoint = generateRandomData(lowerBound_X, upperBound_X, lowerBound_Y, upperBound_Y)

        # if areaPath is not present as an argument, distribute data points within the rectangular area
        if(areaPath == None):
            tmpDistanceVec = np.array([])
            for q in range(0, len(pointListWithin)):
                tmpDistanceVec = np.append(tmpDistanceVec, DistanceCalculations.distance(pointListWithin[q], tmpPoint))

            if (polygonPathList == None):
                if (np.any(pointListWithin == tmpPoint) or np.any(tmpDistanceVec < minDistance)):
                    pass
                else:
                    pointListWithin = np.append(pointListWithin, tmpPoint)
                    pointsWithin += 1

        # checking if the data point generated above is within the border the used-defined area
        else:
            if(areaPath.contains_point((tmpPoint.x(), tmpPoint.y()), None, 0.0) == boolWithin):
                tmpDistanceVec = np.array([])
                for q in range(0, len(pointListWithin)):
                    tmpDistanceVec = np.append(tmpDistanceVec, DistanceCalculations.distance(pointListWithin[q], tmpPoint))
                if(polygonPathList == None):
                    if(np.any(pointListWithin == tmpPoint) or np.any(tmpDistanceVec < minDistance)):
                        pass
                    else:
                        pointListWithin = np.append(pointListWithin, tmpPoint)
                        pointsWithin += 1
                else:
                    # creating a binary vector, which will only contain a value of 1, if the randomly generated data point is within some of the internal circles
                    # therefore the randomly generated data point will only be kept if the tmpBinaryVec has only 0 values
                    tmpBinaryVec = []
                    for q in range(0, len(polygonPathList)):
                        if (polygonPathList[q].contains_point((tmpPoint.x(), tmpPoint.y()), None, 0.0) != boolWithin):
                            tmpBinaryVec = np.append(tmpBinaryVec, 0)
                        else:
                            tmpBinaryVec = np.append(tmpBinaryVec, 1)
                    if (np.any(tmpBinaryVec == 1)):
                        pass
                    else:
                        tmpDistanceVec = np.array([])
                        for q in range(0, len(pointListWithin)):
                            tmpDistanceVec = np.append(tmpDistanceVec, DistanceCalculations.distance(pointListWithin[q], tmpPoint))

                        if (np.any(pointListWithin == tmpPoint) or np.any(tmpDistanceVec < minDistance)):
                            pass
                        else:
                            pointListWithin = np.append(pointListWithin, tmpPoint)
                            pointsWithin += 1
    return pointListWithin

# generating homogeneous localizations (square pattern) on a binary image, every deltaPixel-th pixel will be changed to 1 from 0 (to test g(r) function)
def generateSquareHomogeneousLocalizations(image, maskSize, deltaPixel):
    homLoc = []

    if(maskSize != None):
        # to create homogeneous localization points within a region of interest (within the smallest rectangle enclosing the AZ)
        for i in range(maskSize[0][0], maskSize[0][1] + 1):
            for j in range(maskSize[0][2], maskSize[0][3] + 1):
                if ((i % deltaPixel == 0) and (j % deltaPixel == 0)):
                    homLoc.append(QtCore.QPointF(i, j))
    else:
        # to create homogeneous localization points within the whole image
        for i in range(0, image.width()):
            for j in range(0, image.height()):
                if((i % deltaPixel == 0) and (j % deltaPixel == 0)):
                    homLoc.append(QtCore.QPointF(i, j))

    return homLoc

# generating homogeneous localizations (triangle pattern) on a binary image, every deltaPixel-th pixel will be changed to 1 from 0 (to test g(r) function)
def generateTriangleHomogeneousLocalizations(image, maskSize, deltaPixel):
    homLoc = ([])

    if(maskSize != None):
        # to create homogeneous localization points within a region of interest (within the smallest rectangle enclosing the AZ)
        for i in range(maskSize[0][0], maskSize[0][1] + 1):
            for j in range(maskSize[0][2], maskSize[0][3] + 1):
                if(i % np.around(deltaPixel / 2) == 0):
                    if(j % np.around(deltaPixel * np.sqrt(3)/2) == 0):
                        homLoc.append(QtCore.QPointF(i, j))

        # save y coordinates in a vector
        yCoordVec = ([])
        for i in range(0, len(homLoc)):
            if (np.any(yCoordVec == homLoc[i].y())):
                pass
            else:
                yCoordVec = np.append(yCoordVec, homLoc[i].y())
        # sort y coordinates in an ascending order
        yCoordVec = np.sort(yCoordVec)

        # get the indeces of elements with a given y coordinate
        indexVec = []
        for i in range(0, len(yCoordVec)):
            tmpVec = []
            for j in range(0, len(homLoc)):
                if (homLoc[j].y() == yCoordVec[i]):
                    tmpVec.append(j)

            indexVec.append(tmpVec)

        # print indexVec

        # for even rows, get every third element to delete from index = 2
        # for odd rows, get every third element to delete from index = 1
        # save these index values in a vector
        indexVecToDelete = []
        for i in range(0, len(indexVec)):
            if (i % 2 == 0):
                for j in np.arange(1, len(indexVec[i]), 2):
                    indexVecToDelete.append(indexVec[i][j])
            if (i % 2 != 0):
                for j in np.arange(0, len(indexVec[i]), 2):
                    indexVecToDelete.append(indexVec[i][j])

        # print indexVecToDelete

        # sort indices in an ascending order
        indexVecToDelete = np.asarray(np.sort(indexVecToDelete))

        # type conversion and delete respective elements to get a hexagonal pattern of localization points
        homLoc = np.asarray(homLoc)
        for i in np.arange(1, len(indexVecToDelete) + 1):
            homLoc = np.delete(homLoc, indexVecToDelete[-i])

    return homLoc

# generating homogeneous localizations (hexagonal pattern) on a binary image, every deltaPixel-th pixel will be changed to 1 from 0 (to test g(r) function)
def generateHexagonalHomogeneousLocalizations(image, maskSize, deltaPixel):
    homLoc = []

    if (maskSize != None):
        # to create homogeneous localization points within a region of interest (within the smallest rectangle enclosing the AZ)
        for i in range(maskSize[0][0], maskSize[0][1] + 1):
            for j in range(maskSize[0][2], maskSize[0][3] + 1):
                if (i % np.around(deltaPixel / 2) == 0):
                    if (j % np.around(deltaPixel * np.sqrt(3) / 2) == 0):
                        homLoc.append(QtCore.QPointF(i, j))

        # save y coordinates in a vector
        yCoordVec = ([])
        for i in range(0, len(homLoc)):
            if (np.any(yCoordVec == homLoc[i].y())):
                pass
            else:
                yCoordVec = np.append(yCoordVec, homLoc[i].y())
        # sort y coordinates in an ascending order
        yCoordVec = np.sort(yCoordVec)

        # get the indeces of elements with a given y coordinate
        indexVec = []
        for i in range(0, len(yCoordVec)):
            tmpVec = []
            for j in range(0, len(homLoc)):
                if (homLoc[j].y() == yCoordVec[i]):
                    tmpVec.append(j)

            indexVec.append(tmpVec)

        # print indexVec

        # for even rows, get every third element to delete from index = 2
        # for odd rows, get every third element to delete from index = 1
        # save these index values in a vector
        indexVecToDelete = []
        for i in range(0, len(indexVec)):
            if (i % 2 == 0):
                for j in np.arange(1, len(indexVec[i]), 2):
                    indexVecToDelete.append(indexVec[i][j])
            if (i % 2 != 0):
                for j in np.arange(0, len(indexVec[i]), 2):
                    indexVecToDelete.append(indexVec[i][j])

        # print indexVecToDelete

        # sort indices in an ascending order
        indexVecToDelete = np.asarray(np.sort(indexVecToDelete))

        # type conversion and delete respective elements to get a hexagonal pattern of localization points
        homLoc = np.asarray(homLoc)
        for i in np.arange(1, len(indexVecToDelete) + 1):
            homLoc = np.delete(homLoc, indexVecToDelete[-i])

        # up until here, triagonal localization distribution

        # save y coordinates in a vector
        xCoordVec = ([])
        for i in range(0, len(homLoc)):
            if(np.any(xCoordVec == homLoc[i].x())):
                pass
            else:
                xCoordVec = np.append(xCoordVec, homLoc[i].x())
        # sort y coordinates in an ascending order
        xCoordVec = np.sort(xCoordVec)
        # print xCoordVec

        # get the indeces of elements with a given y coordinate
        indexVec = []
        for i in range(0, len(xCoordVec)):
            tmpVec = []
            for j in range(0, len(homLoc)):
                if(homLoc[j].x() == xCoordVec[i]):
                    tmpVec.append(j)

            indexVec.append(tmpVec)
        # print indexVec

        # for even rows, get every third element to delete from index = 2
        # for odd rows, get every third element to delete from index = 1
        # save these index values in a vector
        indexVecToDelete = []
        for i in range(0, len(indexVec)):
            if(i % 3 == 2):
                for j in np.arange(0, len(indexVec[i]), 1):
                    indexVecToDelete.append(indexVec[i][j])
        # print indexVecToDelete

        # sort indices in an ascending order
        indexVecToDelete = np.asarray(np.sort(indexVecToDelete))

        # type conversion and delete respective elements to get a hexagonal pattern of localization points
        homLoc = np.asarray(homLoc)
        for i in np.arange(1, len(indexVecToDelete)+1):
            homLoc = np.delete(homLoc, indexVecToDelete[-i])

    return homLoc

def deleteRandomLocalizations(localizationPoints, percentageToDelete):

    numberOfLocalizationsToDelete = int(len(localizationPoints) * (percentageToDelete / 100))

    for i in range(0, numberOfLocalizationsToDelete):
        indexToDelete = random.randint(0, len(localizationPoints)-1)
        localizationPoints = np.delete(localizationPoints, indexToDelete)

    return localizationPoints

def randomizeLocalizations(localizationPoints, jitterSD, minDistance, trialNumber):

    trialCounter = 0
    while trialCounter < trialNumber:

        randomizedLocalizationPoints = []

        # fit a multivariate gaussian to every point with a covariance matrix of ([jitterSD**2, 0], [0, jitterSD**2])
        for i in range(0, len(localizationPoints)):
            mean = (localizationPoints[i].x(), localizationPoints[i].y())
            cov = ([jitterSD ** 2, 0], [0, jitterSD ** 2])
            tmpRandomizedLocalization = np.random.multivariate_normal(mean, cov, 1)
            randomizedLocalizationPoints.append((QtCore.QPointF(tmpRandomizedLocalization[0][0], tmpRandomizedLocalization[0][1])))

        NND = DistanceCalculations.nearestNeighborDistanceCalculation(randomizedLocalizationPoints)
        if(np.amin(NND) >= minDistance):
            break
        if(trialCounter+1 == trialNumber):
            print ('-----')
            print ('Cannot create such a distribution in %0.0f trials, original distribution returned' % trialNumber)
            return localizationPoints
        else:
            trialCounter += 1

    return randomizedLocalizationPoints