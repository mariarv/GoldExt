import math
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mPath
import matplotlib.patches as patches
from shapely.geometry import Polygon, Point
from PyQt4 import QtGui, QtCore

# for experimental data
def openSaveStateExp(filename):

    global AZarea
    global scalebarPoints
    global synapticAreaOutlinePoints
    global synapticAreaOutlinePointsInNm 
    global smallGoldParticleCoordinates
    global smallGoldParticleCoordinatesInNm
    global nmPixelRatio
    

    scalebarPoints = []
    synapticAreaOutlinePoints = []
    synapticAreaOutlinePointsInNm = []
    smallGoldParticleCoordinates = []
    smallGoldParticleCoordinatesInNm = []

    f = open(filename, 'r')
    i = 0
    for line in f:
        row = line.split()
        if(i == 0):
            # loading the scalebar value, and set the spinbox value accordingly
            scaleScalar = float(row[0])
            AZarea = float(row[3])
        if(i > 1):
            if(row[0] != '-'):
                scalebarPoints.append(QtCore.QPointF(float(row[0]), float(row[1])))
            if(row[2] != '-'):
                synapticAreaOutlinePoints.append(QtCore.QPointF(float(row[2]), float(row[3])))
            if(row[4] != '-'):
                smallGoldParticleCoordinates.append(QtCore.QPointF(float(row[4]), float(row[5])))
        i += 1

    global nmPixelRatio
    nmPixelRatio = abs((scalebarPoints[1].x() - scalebarPoints[0].x()) / scaleScalar)

    for i in range(0, len(smallGoldParticleCoordinates)):
        smallGoldParticleCoordinatesInNm.append(QtCore.QPointF(float(smallGoldParticleCoordinates[i].x()/nmPixelRatio), float(smallGoldParticleCoordinates[i].y()/nmPixelRatio)))

    for i in range(0, len(synapticAreaOutlinePoints)):
        synapticAreaOutlinePointsInNm.append(QtCore.QPointF(float(synapticAreaOutlinePoints[i].x()/nmPixelRatio), float(synapticAreaOutlinePoints[i].y()/nmPixelRatio)))

    return 0

# X-Y dimensions of the labelled AZ
def getSynapticAreaOutlineBorders(outline):
        
    xcoord = []
    ycoord = []
    for i in range(0, len(outline)):
        xcoord.append(outline[i][0])
        ycoord.append(outline[i][1])

    # storing data in maskSize object
    maskSize = [(int(np.around(min(xcoord))), int(np.around(max(xcoord))), int(np.around(min(ycoord))), int(np.around(max(ycoord))))]
    return maskSize

# calculate Ripley's K function with border correction
def ripleysK(outline, pointPattern, rmax):

    # creating a matplotlib path object from AZ outline 
    outlinePath = []
    for i in range(0, len(outline)):
        tempDataInNm = [outline[i].x(), outline[i].y()]
        outlinePath.append(tempDataInNm)

    outlineBorders = getSynapticAreaOutlineBorders(outlinePath)
    outlinePath = mPath.Path(outlinePath)

    # creating a shapely Polygon object from AZ outline
    outlineXY = []
    for i in range(0, len(outline)):
        outlineXY.append([outline[i].x(), outline[i].y()])

    polygon_shape = Polygon(outlineXY)

    # distance vector over which Ripley's K function is calculated
    distVec = np.linspace(1, rmax, num=(rmax), endpoint=True)

    # Ripley's K initialization
    ripleyK = np.linspace(0, 0, num=len(distVec))

    for i in range(0, len(pointPattern)):
        if outlinePath.contains_point((pointPattern[i].x(), pointPattern[i].y())):    # check if the given gold labelling is within the AZ boundary
            for j in range(1, rmax+1):
                # creating a circle path with increasing radius
                tmpCircle = mPath.Path.circle(center=((pointPattern[i].x(), pointPattern[i].y())), radius=float(j))
                for k in range(0, len(pointPattern)):
                    if i != k:
                        dx = pointPattern[i].x() - pointPattern[k].x()
                        dy = pointPattern[i].y() - pointPattern[k].y()
                        pointDistance = math.hypot(dx, dy)   #hypotenuse function
                        
                        if pointDistance < j: # if the distance between the 2 given points is within the circle radius
                            # creating a shapely circle by buffering a Point object with a given radius
                            circle_shape = Point((pointPattern[i].x(), pointPattern[i].y())).buffer(float(j))
                            circleArea = circle_shape.area
                            
                            # calculate intersection area of a given circle and the AZ outline
                            intersectionArea = polygon_shape.intersection(circle_shape).area
                            ripleyK[j-1] += 1*(circleArea/intersectionArea)

    ripleyK = ripleyK * (polygon_shape.area / (len(pointPattern)**2))

    # estimated L(r) function 
    L_est = np.sqrt(np.asarray(ripleyK)/np.pi)

    Lr_r = []
    for i in range(0, len(L_est)):
        Lr_r.append(L_est[i]-distVec[i])
    
    return distVec, Lr_r

# visualize gold particles and AZ
def visualizeData(outline, pointPattern, filename):

    # calculate modified Ripley's K function (i.e. L(r)-r)
    dist, rK = ripleysK(outline, pointPattern, 80)

    # creating a matplotlib path object from AZ outline 
    outlinePath = []
    for i in range(0, len(outline)):
        tempDataInNm = [outline[i].x(), outline[i].y()]
        outlinePath.append(tempDataInNm)

    outlineBorders = getSynapticAreaOutlineBorders(outlinePath)
    outlinePath = mPath.Path(outlinePath)
    
    # patch of AZ polygon
    patchPolygon = patches.PathPatch(outlinePath, facecolor = 'orange', lw = 2, ls = 'dashdot', alpha=0.7)


    fig = plt.figure(figsize = (10,6)) # in inches
    ax1 = fig.add_subplot(121)
    
    # AZ polygon 
    ax1.add_patch(patchPolygon)
    #ax1.add_patch(patchCircle)
    # gold particle labelling
    for i in range(0, len(pointPattern)):
        ax1.plot(pointPattern[i].x(), pointPattern[i].y(), 'go', alpha=0.9)
    ax1.set_xlim(outlineBorders[0][0]-10, outlineBorders[0][1]+10)
    ax1.set_ylim(outlineBorders[0][2]-10, outlineBorders[0][3]+10)
    ax1.set_title(filename, fontsize = 12)
    ax1.set_xlabel('Distance (nm)', fontsize = 10)
    ax1.set_ylabel('Distance (nm)', fontsize = 10)

    plt.axis('scaled')

    # L(r)-r function
    ax2 = fig.add_subplot(122)
    ax2.plot(dist, rK, 'k')
    ax2.set_ylabel('L(r)-r', fontsize = 10)
    ax2.set_xlabel('Distance (nm)', fontsize = 10)

    plt.axis('equal')
    plt.show()

    return 0

                                               
filename = 'ml_02.gss'
# open saved state of labelled AZ
openSaveStateExp(filename)
# visualize data
visualizeData(synapticAreaOutlinePointsInNm, smallGoldParticleCoordinatesInNm, filename[0:-4])


