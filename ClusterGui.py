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

from PyQt5 import QtCore, QtWidgets, uic, QtGui
import MainGUI
import GenerateArtificialData
import matplotlib.path as mPath
import matplotlib.pyplot as plt
import time
import Clustering
import DistanceCalculations
import GenerateArtificialData
import ExcelSave
import numpy as np
from scipy import stats
import xlsxwriter as xw
from xlsxwriter.utility import xl_rowcol_to_cell
import random

# defining the GUI drawn in Qt Desinger
qtGoldExtClusterGui = './GoldExt_GUI_Cluster.ui'

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtGoldExtClusterGui)

#class GoldExtClusterGui(QtGui.QMainWindow, Ui_MainWindow):
class GoldExtClusterGui(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.polyCounter = 0

        self.polygonAreaRadioButton.setEnabled(1)
        self.polygonAreaEndingRadioButton.setEnabled(0)

        self.polygonAreaRadioButton.clicked.connect(self.drawPolygonAreaOutline)
        self.polygonAreaEndingRadioButton.clicked.connect(self.endPolygonArea)
        self.populateSynapticAreaButton.clicked.connect(self.populatePolygonArea)
        self.populateAZBackgroundButton.clicked.connect(self.createAZBackgroundLabelling)
        self.populateBackgroundAreaButton.clicked.connect(self.createBackgroundLabelling)
        self.clearSceneButton.clicked.connect(self.clearScene)
        self.saveStateButton.clicked.connect(self.saveRandomState)
        self.openSavedStateButton.clicked.connect(self.openSavedSate)

        self.generateRandomDataButton.clicked.connect(self.generateAllRandomData)
        self.performDBSCANButton.clicked.connect(self.performDBSCAN)
        self.performAffinityPropagationButton.clicked.connect(self.performAffinityPropagation)
        self.performMeanShiftButton.clicked.connect(self.performMeanShift)
        self.performSpatialAutocorrelationButton.clicked.connect(self.performSpatialAutocorrelation)

        self.polygonAreaOutlinePoints = []
        self.polygonAreaOutlinePath = []
        self.randomGoldParticlesInPolygon = []
        self.randomAZBackgroundParticles = []
        self.randomBackgroundParticles = []
        self.tmpRandomSmall = []
        self.internalPolygonList = []
        self.internalPolygonAreaList = []
        self.polygonAreaGoldParticlesPerAreaList = []
        self.polygonAreaList = []

        self.randomGoldParticlesInPolygonItemList = []
        self.randomAZBackgroundParticlesItemList = []
        self.randomBackgroundParticlesItemList = []

        self.allSmallPercNND = []
        self.allSmallPercFull = []
        self.allSmallNNDMatrix = []
        self.allSmallFullMatrix = []

        self.centroidDistance = []
        self.randomCentroidDistance = []

        self.smallClosestEdgeDistance = []
        self.smallRandomClosestEdgeDistance = []

        self.randomNNDMean = []
        self.randomAllDistanceMean = []
        self.randomCentroidMean = []
        self.randomClosestEdgeMean = []

        self.g_r = []

        self.ACF_radiusVec = []

        global numberOfAZBackgroundParticles, totalNumberOfGoldParticlesToPlace, trueAZDensity, backgroundDensity
        numberOfAZBackgroundParticles = 0
        totalNumberOfGoldParticlesToPlace = 0
        trueAZDensity = 0
        backgroundDensity = 0

        self.redrawFromMainGui()

    def redrawFromMainGui(self):
        # setting a grapchics scene with appropriate size
        self.scene = QtWidgets.QGraphicsScene(0, 0, 690, 650)
        # making the image scalable with the mouse wheel
        self.scene.wheelEvent = self.zoomWithWheel
        # adding the rescaled image to the graphics scene
        self.scene.addPixmap(MainGUI.imgScaled)
        # visualizing the scene
        self.imageLoaderView.setScene(self.scene)
        self.imgItem = QtWidgets.QGraphicsPixmapItem(MainGUI.imgScaled, None) #, self.scene)
        self.scene.addItem(self.imgItem)
        # redrawing scalebar from the previous image
        scalebarLine = QtCore.QLineF(MainGUI.globalScalebarPoints[0].x(), MainGUI.globalScalebarPoints[0].y(), MainGUI.globalScalebarPoints[1].x(), MainGUI.globalScalebarPoints[1].y())
        self.scene.addLine(scalebarLine, QtGui.QPen(QtCore.Qt.red))
        scaleBarString = str('%0.0f nm' % MainGUI.globalScalebarValue)
        printedScalebar = self.scene.addText(scaleBarString, QtGui.QFont('', 12))
        # setting the position of the scalebar
        printedScalebar.setPos(MainGUI.globalScalebarPoints[0].x(), MainGUI.globalScalebarPoints[0].y())
        # setting the color of the scalebar
        printedScalebar.setDefaultTextColor(QtCore.Qt.red)

        # redrawing the synaptic area outline
        self.scene.addPolygon(QtGui.QPolygonF(MainGUI.globalSynapticAreaOutlinePoints), QtGui.QPen(QtCore.Qt.red))

    # delete the polygon areas drawn before
    def clearScene(self):
        self.scene.clear()
        self.randomGoldParticlesInPolygon = []
        self.randomBackgroundParticles = []
        self.randomAZBackgroundParticles = []
        self.polygonAreaOutlinePoints = []
        self.redrawFromMainGui()
        self.polygonAreaRadioButton.setEnabled(1)

    # letting the user to zoom in and out with the mouse wheel
    def zoomWithWheel(self, event):
        'zoom'
        sc = event.delta()/100.
        if sc < 0:
            sc = -1 / sc
        self.imageLoaderView.scale(sc,sc)

    def drawPolygonAreaOutline(self, event):
        self.imgItem.mousePressEvent = self.polygonAreaOutlineSelect
        self.polyCounter = 0
        self.internalPolygonList = []

    # getting the clicked position of the mouse, and appending the coordinates into an array
    # if the array length is longer than 1, it draws lines between points
    def polygonAreaOutlineSelect(self, event):
        self.polygonAreaRadioButton.setEnabled(0)
        self.polygonAreaOutlinePoints.append(event.pos())
        if(len(self.polygonAreaOutlinePoints) > 1):
            #tmpLineItem = QtWidgets.QGraphicsLineItem(QtCore.QLineF(self.polygonAreaOutlinePoints[-2], self.polygonAreaOutlinePoints[-1]))
            self.scene.addItem(QtWidgets.QGraphicsLineItem(QtCore.QLineF(self.polygonAreaOutlinePoints[-2], self.polygonAreaOutlinePoints[-1])))
        if(len(self.polygonAreaOutlinePoints) > 2):
            self.polygonAreaEndingRadioButton.setEnabled(1)

    # this function closes the polygon
    def endPolygonArea(self, event):
        self.polygonAreaOutlinePoints.append(self.polygonAreaOutlinePoints[0])
        self.drawPolygon(self.polygonAreaOutlinePoints)

        # to be able to populate multiple polygons inside an AZ
        if self.polyCounter < self.numberOfInternalPolygonsDoubleSpinBox.value():
            self.internalPolygonList.append(self.polygonAreaOutlinePoints)
            self.polygonAreaOutlinePoints = []
            self.polyCounter += 1
        if self.polyCounter == self.numberOfInternalPolygonsDoubleSpinBox.value():
            self.imgItem.mousePressEvent = 0
            self.polygonAreaEndingRadioButton.setEnabled(0)
            self.createPathOfPolygonArea(self.internalPolygonList)

    def drawPolygon(self, arrayOfPoints):
        tmpPolygon = QtWidgets.QGraphicsPolygonItem()
        tmpPolygon.setPolygon(QtGui.QPolygonF(arrayOfPoints))
        self.scene.addItem(tmpPolygon)
        tmpPolygon.setPen(QtGui.QPen(QtCore.Qt.yellow, 1))


    # creating a matplotlib path from the synaptic area outline points; this is needed for random data point generation
    def createPathOfPolygonArea(self, listOfInternalPolygons):

        global realPolyPath
        global realPolyPathInUm
        realPolyPath = []
        realPolyPathInUm = []
        self.internalPolygonAreaList = []
        self.polygonAreaList = []
        self.polygonAreaList.append(MainGUI.AZarea)

        for i in range(0, len(listOfInternalPolygons)):
            polyAreaToPopulate = DistanceCalculations.PolygonArea(listOfInternalPolygons[i])
            polyAreaToPopulateInUm = polyAreaToPopulate/(MainGUI.nmPixelRatio**2)/1e6
            self.internalPolygonAreaList.append(polyAreaToPopulateInUm)
            self.polygonAreaList.append(polyAreaToPopulateInUm)
            print ('-----')
            print ('Internal polygon area: %0.5f um2' % polyAreaToPopulateInUm)
            self.polygonAreaOutlinePath = []
            pathInUm = []

            for j in range(0, len(listOfInternalPolygons[i])):
                tempData = [listOfInternalPolygons[i][j].x(), listOfInternalPolygons[i][j].y()]
                self.polygonAreaOutlinePath.append(tempData)
                # pixel to um conversion
                tmpX = listOfInternalPolygons[i][j].x() / (MainGUI.nmPixelRatio * 1e3)
                tmpY = listOfInternalPolygons[i][j].y() / (MainGUI.nmPixelRatio * 1e3)
                tempDataInUm = [tmpX, tmpY]
                pathInUm.append(tempDataInUm)
            realPolyPath.append(mPath.Path(self.polygonAreaOutlinePath))
            realPolyPathInUm.append(mPath.Path(pathInUm))

    # populate the polygon area with randomly generated data points
    def populatePolygonArea(self):
        if(len(self.randomGoldParticlesInPolygon) > 0):
            # clear the scene and redraw the internal polygons of the AZ
            self.scene.clear()
            self.redrawFromMainGui()
            for i in range(0, len(self.internalPolygonList)):
                self.drawPolygon(self.internalPolygonList[i])
            self.randomGoldParticlesInPolygon = []
        if(len(self.randomBackgroundParticles) > 0):
            self.visualizeRandomData(self.randomBackgroundParticles, 2)
        if(len(self.randomAZBackgroundParticles) > 0):
            self.visualizeRandomData(self.randomAZBackgroundParticles, 3)

        cumulativeInternalPolygonArea = 0
        for i in range(0, len(self.internalPolygonAreaList)):
            cumulativeInternalPolygonArea += self.internalPolygonAreaList[i]

        #for i in range(0, len(self.internalPolygonAreaList)):
        #    print 'Poly %d: %0.1f' % (i, self.internalPolygonAreaList[i]/cumulativeInternalPolygonArea*100), '%'

        global totalNumberOfGoldParticlesToPlace
        totalNumberOfGoldParticlesToPlace = int(self.densityDoubleSpinBox.value() * MainGUI.AZarea)
        if(totalNumberOfGoldParticlesToPlace < 1):
            totalNumberOfGoldParticlesToPlace = 1

        self.polygonAreaGoldParticlesPerAreaList = []
        numberPlaced = 0
        for i in range(0, len(self.internalPolygonAreaList)):
            self.polygonAreaGoldParticlesPerAreaList.append(int(totalNumberOfGoldParticlesToPlace * (self.internalPolygonAreaList[i]/cumulativeInternalPolygonArea)))
            numberPlaced += self.polygonAreaGoldParticlesPerAreaList[-1]

        #print self.polygonAreaGoldParticlesPerAreaList, numberPlaced, totalNumberOfGoldParticlesToPlace
        remainingParticlesToPlace = totalNumberOfGoldParticlesToPlace - numberPlaced
        #print remainingParticlesToPlace

        start_time = time.time()
        self.randomGoldParticlesInPolygon = np.asarray(self.randomGoldParticlesInPolygon)
        # place randomly the gold particles within the internal polygons based on their area, to have roughly equal densities within them
        for i in range(0, len(self.polygonAreaGoldParticlesPerAreaList)):
            dataPointCounter = 0
            while dataPointCounter < self.polygonAreaGoldParticlesPerAreaList[i]:
                tmpRandomParticles = GenerateArtificialData.generateSetOfRandomDataPoints(realPolyPath[i], None,  True, 1, 10*MainGUI.nmPixelRatio, realPolyPath[i].get_extents().x0, realPolyPath[i].get_extents().x1, realPolyPath[i].get_extents().y0, realPolyPath[i].get_extents().y1)

                tmpDistanceVec = np.array([])
                for q in range(0, len(self.randomGoldParticlesInPolygon)):
                    tmpDistanceVec = np.append(tmpDistanceVec, DistanceCalculations.distance(self.randomGoldParticlesInPolygon[q], tmpRandomParticles[-1]))

                if(np.any(self.randomGoldParticlesInPolygon == tmpRandomParticles[-1]) or np.any(tmpDistanceVec < 10*MainGUI.nmPixelRatio)):
                    pass
                else:
                    self.randomGoldParticlesInPolygon = np.append(self.randomGoldParticlesInPolygon, tmpRandomParticles[-1])
                    dataPointCounter += 1

        # place randomly the remaining gold particles
        dataPointCounter = 0
        while dataPointCounter < remainingParticlesToPlace:
            j = random.randint(0, int(self.numberOfInternalPolygonsDoubleSpinBox.value())-1)
            tmpRandomParticles = GenerateArtificialData.generateSetOfRandomDataPoints(realPolyPath[j], None,  True, 1, 10*MainGUI.nmPixelRatio, realPolyPath[j].get_extents().x0, realPolyPath[j].get_extents().x1, realPolyPath[j].get_extents().y0, realPolyPath[j].get_extents().y1)

            tmpDistanceVec = np.array([])
            for q in range(0, len(self.randomGoldParticlesInPolygon)):
                tmpDistanceVec = np.append(tmpDistanceVec, DistanceCalculations.distance(self.randomGoldParticlesInPolygon[q], tmpRandomParticles[-1]))
            for q in range(0, len(self.randomAZBackgroundParticles)):
                tmpDistanceVec = np.append(tmpDistanceVec, DistanceCalculations.distance(self.randomAZBackgroundParticles[q], tmpRandomParticles[-1]))
            for q in range(0, len(self.randomBackgroundParticles)):
                tmpDistanceVec = np.append(tmpDistanceVec, DistanceCalculations.distance(self.randomBackgroundParticles[q], tmpRandomParticles[-1]))

            if(np.any(self.randomGoldParticlesInPolygon == tmpRandomParticles[-1]) or np.any(tmpDistanceVec < 10*MainGUI.nmPixelRatio)):
                pass
            else:
                self.randomGoldParticlesInPolygon = np.append(self.randomGoldParticlesInPolygon, tmpRandomParticles[-1])
                dataPointCounter += 1

        self.visualizeRandomData(self.randomGoldParticlesInPolygon, 1)
        # since the above procedure generate a numpy array, it has to be converted into a list to able to delete elementwise from it
        #self.randomGoldParticlesInPolygon = self.randomGoldParticlesInPolygon.tolist()
        #self.visualizeRandomData(self.randomGoldParticlesInPolygon, 1)
        self.internalGoldParticleLcdNumber.display(totalNumberOfGoldParticlesToPlace)

        global trueAZDensity
        trueAZDensity = ((len(self.randomGoldParticlesInPolygon) + len(self.randomAZBackgroundParticles)) / MainGUI.AZarea)

        print ('-----')
        print ('N = %0.0f random gold particles were generated in %0.3f seconds' % (totalNumberOfGoldParticlesToPlace, float(time.time() - start_time)))
        print ('True density within the AZ: %0.3f gold particles/um2' % trueAZDensity)
        print ('-----')

    def createAZBackgroundLabelling(self):
        if(len(self.randomAZBackgroundParticles) > 0):
            for i in range(0, len(self.randomAZBackgroundParticles)):
                p = self.randomAZBackgroundParticles[-1]
                self.randomAZBackgroundParticles = np.delete(self.randomAZBackgroundParticles, -1)
                self.scene.removeItem(self.randomAZBackgroundParticlesItemList[-1])
                del self.randomAZBackgroundParticlesItemList[-1]
            self.randomAZBackgroundParticles = []

        global numberOfAZBackgroundParticles

        if(self.AZBackgroundDensityDoubleSpinBox.value() == 0):
            numberOfAZBackgroundParticles = 0
        else:
            numberOfAZBackgroundParticles = self.AZBackgroundDensityDoubleSpinBox.value() * MainGUI.AZarea
            if(0 < numberOfAZBackgroundParticles < 1):
                numberOfAZBackgroundParticles = 1
            else:
                numberOfAZBackgroundParticles = int(self.AZBackgroundDensityDoubleSpinBox.value() * MainGUI.AZarea)

        start_time = time.time()
        dataPointCounter = 0
        while dataPointCounter < numberOfAZBackgroundParticles:
            tmpRandomParticles = GenerateArtificialData.generateSetOfRandomDataPoints(MainGUI.realPath, realPolyPath, True, 1, 10*MainGUI.nmPixelRatio, MainGUI.realPath.get_extents().x0, MainGUI.realPath.get_extents().x1, MainGUI.realPath.get_extents().y0, MainGUI.realPath.get_extents().y1)

            tmpDistanceVec = np.array([])
            for q in range(0, len(self.randomGoldParticlesInPolygon)):
                tmpDistanceVec = np.append(tmpDistanceVec, DistanceCalculations.distance(self.randomGoldParticlesInPolygon[q], tmpRandomParticles[-1]))
            for q in range(0, len(self.randomAZBackgroundParticles)):
                tmpDistanceVec = np.append(tmpDistanceVec, DistanceCalculations.distance(self.randomAZBackgroundParticles[q], tmpRandomParticles[-1]))
            for q in range(0, len(self.randomBackgroundParticles)):
                tmpDistanceVec = np.append(tmpDistanceVec, DistanceCalculations.distance(self.randomBackgroundParticles[q], tmpRandomParticles[-1]))

            if (np.any(self.randomAZBackgroundParticles == tmpRandomParticles[-1]) or np.any(tmpDistanceVec < (10 * MainGUI.nmPixelRatio))):
                pass
            else:
                self.randomAZBackgroundParticles = np.append(self.randomAZBackgroundParticles, tmpRandomParticles[-1])
                dataPointCounter += 1

        self.visualizeRandomData(self.randomAZBackgroundParticles, 3)
        self.AZBackgroundGoldParticleLcdNumber.display(numberOfAZBackgroundParticles)

        global trueAZDensity
        trueAZDensity = ((len(self.randomGoldParticlesInPolygon) + len(self.randomAZBackgroundParticles)) / MainGUI.AZarea)

        print ('-----')
        print ('N = %0.0f random AZ background particles were generated in %0.3f seconds' % (numberOfAZBackgroundParticles, float(time.time() - start_time)))
        print ('True density within the AZ: %0.3f gold particles/um2' % trueAZDensity)
        print ('-----')

    # generate random background labelling with a given density
    def createBackgroundLabelling(self):
        if(len(self.randomBackgroundParticles) > 0):
            for i in range(0, len(self.randomBackgroundParticles)):
                p = self.randomBackgroundParticles[-1]
                self.randomBackgroundParticles = np.delete(self.randomBackgroundParticles, -1)
                self.scene.removeItem(self.randomBackgroundParticlesItemList[-1])
                del self.randomBackgroundParticlesItemList[-1]
            self.randomBackgroundParticles = []

        if(self.backgroundDensityDoubleSpinBox.value() == 0):
            numberOfBackgroundParticles = 0
        else:
            numberOfBackgroundParticles = self.backgroundDensityDoubleSpinBox.value() * MainGUI.totalArea
            if(0 < numberOfBackgroundParticles < 1):
                numberOfBackgroundParticles = 1
            else:
                numberOfBackgroundParticles = int(self.backgroundDensityDoubleSpinBox.value() * MainGUI.totalArea)

        start_time = time.time()

        dataPointCounter = 0
        while dataPointCounter < numberOfBackgroundParticles:
            tmpRandomParticles = GenerateArtificialData.generateSetOfRandomDataPoints(MainGUI.realPath, None, False, 1, 10 * MainGUI.nmPixelRatio, 0, MainGUI.imgScaled.width(), 0, MainGUI.imgScaled.height())

            tmpDistanceVec = np.array([])
            for q in range(0, len(self.randomGoldParticlesInPolygon)):
                tmpDistanceVec = np.append(tmpDistanceVec, DistanceCalculations.distance(self.randomGoldParticlesInPolygon[q], tmpRandomParticles[-1]))
            for q in range(0, len(self.randomAZBackgroundParticles)):
                tmpDistanceVec = np.append(tmpDistanceVec, DistanceCalculations.distance(self.randomAZBackgroundParticles[q], tmpRandomParticles[-1]))
            for q in range(0, len(self.randomBackgroundParticles)):
                tmpDistanceVec = np.append(tmpDistanceVec, DistanceCalculations.distance(self.randomBackgroundParticles[q], tmpRandomParticles[-1]))

            if (np.any(self.randomBackgroundParticles == tmpRandomParticles[-1]) or np.any(tmpDistanceVec < (10 * MainGUI.nmPixelRatio))):
                pass
            else:
                self.randomBackgroundParticles = np.append(self.randomBackgroundParticles, tmpRandomParticles[-1])
                dataPointCounter += 1

        # since the above procedure generate a numpy array, it has to be converted into a list to able to delete elementwise from it
        # self.randomBackgroundParticles = self.randomBackgroundParticles.tolist()
        self.visualizeRandomData(self.randomBackgroundParticles, 2)
        self.backgroundGoldParticleLcdNumber.display(numberOfBackgroundParticles)

        global backgroundDensity
        backgroundDensity = (numberOfBackgroundParticles / MainGUI.totalArea)

        print ('-----')
        print ('N = %0.0f random background particles were generated in %0.3f seconds' % (numberOfBackgroundParticles, float(time.time() - start_time)))
        print ('True density outside the AZ: %0.3f gold particles/um2' % backgroundDensity)

    # plot randomly generated data on the screen
    def visualizeRandomData(self, arrayOfPoints, color):
        for i in range(0, len(arrayOfPoints)):
            pointDiam = 4
            tmpEllipse = QtWidgets.QGraphicsEllipseItem(arrayOfPoints[i].x()-pointDiam/2, arrayOfPoints[i].y()-pointDiam, pointDiam, pointDiam)
            if(color == 1):
                tmpEllipse.setPen(QtGui.QPen(QtCore.Qt.green, 2))
                self.randomGoldParticlesInPolygonItemList.append(tmpEllipse)
            if(color == 2):
                tmpEllipse.setPen(QtGui.QPen(QtCore.Qt.magenta, 2))
                self.randomBackgroundParticlesItemList.append(tmpEllipse)
            if(color == 3):
                tmpEllipse.setPen(QtGui.QPen(QtCore.Qt.yellow, 2))
                self.randomAZBackgroundParticlesItemList.append(tmpEllipse)
            self.scene.addItem(tmpEllipse)

    def saveRandomState(self):
        savedFileName = (QtWidgets.QFileDialog.getSaveFileName(self, 'Save Random State', MainGUI.openedFilename[0][0:-4], 'GoldExt SaveState (*.gss)')) # QtCore.QDir.currentPath()
        f = open(savedFileName[0], 'w')

        # searching for the longest array to store data
        maxLength = 0
        lengthVec = []
        lengthVec.append(len(self.randomGoldParticlesInPolygon))
        lengthVec.append(len(self.randomAZBackgroundParticles))
        lengthVec.append(len(self.randomBackgroundParticles))
        if(int(self.numberOfInternalPolygonsDoubleSpinBox.value()) != 0):
            for i in range(0, int(self.numberOfInternalPolygonsDoubleSpinBox.value())):
                lengthVec.append(len(self.internalPolygonList[i]))

        maxLength = max(lengthVec)

        dataMatrix = []
        matrixColNumber = len(self.internalPolygonList) * 2 + 6
        if ((len(self.internalPolygonList) * 2 + 6) < 11):
            matrixColNumber = 11

        for i in range(0, matrixColNumber):
            tmpVec = []
            for j in range(0, maxLength + 2):
                tmpVec.append('-')
            dataMatrix.append(tmpVec)

        for i in range(0, maxLength + 2):
            if(i == 0): # name the respective lists
                dataMatrix[0][i] = str(int(self.numberOfInternalPolygonsDoubleSpinBox.value()))
                dataMatrix[1][i] = 'numberOfInternalPolygons'
                dataMatrix[3][i] = str(int(self.densityDoubleSpinBox.value()))
                dataMatrix[4][i] = 'AZ_internalPolygonGoldParticleDensity'
                dataMatrix[6][i] = str(int(self.AZBackgroundDensityDoubleSpinBox.value()))
                dataMatrix[7][i] = 'AZ_backgroundGoldParticleDensity'
                dataMatrix[9][i] = str(int(self.backgroundDensityDoubleSpinBox.value()))
                dataMatrix[10][i] = 'backgroundDensity'

            if(i == 1): # name the respective lists
                dataMatrix[0][i] = 'goldLabelling_x'
                dataMatrix[1][i] = 'goldLabelling_y'
                dataMatrix[2][i] = 'AZbackgroundLabelling_x'
                dataMatrix[3][i] = 'AZBackgroundLabelling_y'
                dataMatrix[4][i] = 'backgroundLabelling_x'
                dataMatrix[5][i] = 'backgroundLabelling_y'

                counter = 6
                for j in np.arange(0, len(self.internalPolygonList)):
                    dataMatrix[counter][i] = 'internalPolygon' + str(j + 1) + '_x'
                    dataMatrix[counter + 1][i] = 'internalPolygon' + str(j + 1) + '_y'
                    counter += 2

            if(i > 1):

                if (len(self.randomGoldParticlesInPolygon) > i - 2):
                    dataMatrix[0][i] = str(self.randomGoldParticlesInPolygon[i - 2].x())
                    dataMatrix[1][i] = str(self.randomGoldParticlesInPolygon[i - 2].y())

                if (len(self.randomAZBackgroundParticles) > i - 2):
                    dataMatrix[2][i] = str(self.randomAZBackgroundParticles[i - 2].x())
                    dataMatrix[3][i] = str(self.randomAZBackgroundParticles[i - 2].y())

                if (len(self.randomBackgroundParticles) > i - 2):
                    dataMatrix[4][i] = str(self.randomBackgroundParticles[i - 2].x())
                    dataMatrix[5][i] = str(self.randomBackgroundParticles[i - 2].y())

                counter = 6
                for j in np.arange(0, len(self.internalPolygonList)):
                    if (len(self.internalPolygonList[j]) > i - 2):

                        dataMatrix[counter][i] = str(self.internalPolygonList[j][i - 2].x())
                        dataMatrix[counter + 1][i] = str(self.internalPolygonList[j][i - 2].y())
                        counter += 2

        # save data in a .gss file
        dataMatrix = np.transpose((np.asarray(dataMatrix)))
        np.savetxt(savedFileName[0], dataMatrix, fmt='%s')

        print ('-----')
        print ('State saved at %s' % savedFileName[0])

    def openSavedSate(self):
        self.clearScene()
        self.randomGoldParticlesInPolygon = []
        self.randomBackgroundParticles = []

        global clusterOpenedFilename

        clusterOpenedFilename = QtWidgets.QFileDialog.getOpenFileName(self, 'Open saved state', MainGUI.openedFilename[0][0:-4], 'GoldExt SavedState (*.gss)')

        f = open(clusterOpenedFilename[0], 'r')
        i = 0
        for line in f:
            row = line.split()
            if(i == 0):
                self.numberOfInternalPolygonsDoubleSpinBox.setValue(float(row[0]))
                self.densityDoubleSpinBox.setValue(float(row[3]))
                self.AZBackgroundDensityDoubleSpinBox.setValue(float(row[6]))
                self.backgroundDensityDoubleSpinBox.setValue(float(row[9]))
                self.internalPolygonList = []
                for j in range(0, int(row[0])):
                    self.internalPolygonList.append([])
            if(i >= 2):
                # load data: random and background labellings, internal polygons within the synaptic AZ
                if(row[0] != '-'):
                    self.randomGoldParticlesInPolygon.append(QtCore.QPointF(float(row[0]), float(row[1])))
                if(row[2] != '-'):
                    self.randomAZBackgroundParticles.append(QtCore.QPointF(float(row[2]), float(row[3])))
                if(row[4] != '-'):
                    self.randomBackgroundParticles.append(QtCore.QPointF(float(row[4]), float(row[5])))

                counter = 6
                j = 0
                while counter < 6 + len(self.internalPolygonList)*2:
                    if(row[counter] != '-'):
                        self.internalPolygonList[j].append(QtCore.QPointF(float(row[counter]), float(row[counter + 1])))
                    counter += 2
                    j += 1
            i += 1

        # redrawing the loaded structures onto the image
        # internal polygons within the synaptic AZ
        for i in range(0, len(self.internalPolygonList)):
            self.scene.addPolygon(QtGui.QPolygonF(self.internalPolygonList[i]), QtGui.QPen(QtCore.Qt.yellow))
        # creating path from the outline points to be able to generate random data points
        self.createPathOfPolygonArea(self.internalPolygonList)
        # gold particles of internal polygons
        self.visualizeRandomData(self.randomGoldParticlesInPolygon, 1)
        self.internalGoldParticleLcdNumber.display(len(self.randomGoldParticlesInPolygon))
        # background gold particles in the AZ
        self.visualizeRandomData(self.randomAZBackgroundParticles, 3)
        self.AZBackgroundGoldParticleLcdNumber.display(len(self.randomAZBackgroundParticles))
        # background gold particles
        self.visualizeRandomData(self.randomBackgroundParticles, 2)
        self.AZBackgroundGoldParticleLcdNumber.display(len(self.randomAZBackgroundParticles))
        self.backgroundGoldParticleLcdNumber.display(len(self.randomBackgroundParticles))
        print ('-----')
        print ('Saved state loaded succesfully')

        trueAZDensity = ((len(self.randomGoldParticlesInPolygon) + len(self.randomAZBackgroundParticles)) / MainGUI.AZarea)
        print ('-----')
        print ('True density within the AZ: %0.3f gold particles/um2' % trueAZDensity)
        print ('-----')

    # generate random data within the whole AZ to compare with the artificially clustered data
    def generateRandomSmallData(self):
        self.tmpRandomSmall = []
        if((len(self.randomGoldParticlesInPolygon) + len(self.randomAZBackgroundParticles)) == 0):
            print ('-----')
            print ('There are 0 random gold particles labelled, no distribution could be generated')
        else:
            # get_extents() function of a path returns the min and max values of x and y coordinates of the path
            self.tmpRandomSmall = GenerateArtificialData.generateSetOfRandomDataPoints(MainGUI.realPath, None, True, (len(self.randomGoldParticlesInPolygon) + len(self.randomAZBackgroundParticles)), 10*MainGUI.nmPixelRatio, MainGUI.realPath.get_extents().x0, MainGUI.realPath.get_extents().x1, MainGUI.realPath.get_extents().y0, MainGUI.realPath.get_extents().y1)

            # xVec = []
            # yVec = []
            # for i in range(0, len(self.tmpRandomSmall)):
            #     xVec.append(self.tmpRandomSmall[i].x())
            #     yVec.append(self.tmpRandomSmall[i].y())
            #
            # dataMatrix = []
            # dataMatrix.append(xVec)
            # dataMatrix.append(yVec)
            # dataMatrix = np.transpose(np.asarray(dataMatrix))
            #
            # filename = str(clusterOpenedFilename[0:-4]) + '_random.txt'
            # np.savetxt(filename, dataMatrix, fmt='%0.3f')

    # N set of random data generation
    def generateAllRandomData(self):
        self.allSmallPercNND = []
        self.allSmallPercFull = []
        self.allSmallNNDMatrix = []
        self.allSmallFullMatrix = []
        self.randomCentroidDistance = []
        self.smallRandomClosestEdgeDistance = []

        self.randomNNDMean = []
        self.randomAllDistanceMean = []
        self.randomCentroidMean = []
        self.randomClosestEdgeMean = []

        allGoldLabeling = []
        for i in range(0, len(self.randomGoldParticlesInPolygon)):
            allGoldLabeling.append(self.randomGoldParticlesInPolygon[i])
        for i in range(0, len(self.randomAZBackgroundParticles)):
            allGoldLabeling.append(self.randomAZBackgroundParticles[i])

        polygonCentroid = DistanceCalculations.calculateGoldParticleCentroid(allGoldLabeling)
        global polygonCentroidInUm
        polygonCentroidInUm = (QtCore.QPointF(polygonCentroid.x() / (MainGUI.nmPixelRatio*1e3), polygonCentroid.y() / (MainGUI.nmPixelRatio*1e3)))

        AZOutlineInUm = []
        for i in range(0, len(MainGUI.globalSynapticAreaOutlinePoints) - 1):
            AZOutlineInUm.append(MainGUI.globalSynapticAreaOutlinePoints[i] / (MainGUI.nmPixelRatio*1e3))

        # for spatial autocorrelation on random samples
        maskSize = DistanceCalculations.getSynapticAreaOutlineBorders(MainGUI.globalSynapticAreaOutlinePoints)
        self.random_g_r = []

        # start measuring the execution time of the code
        start_time = time.time()

        self.experimentalDataCalculations()

        for i in range(0, int(self.randomDataSampleDoubleSpinBox.value())):
            self.generateRandomSmallData()
            # calling the 2 previously defined function from module 'DistanceCalculations'
            smallNND_matrix = DistanceCalculations.nearestNeighborDistanceCalculation(self.tmpRandomSmall / (MainGUI.nmPixelRatio*1e3))
            smallPercNND = DistanceCalculations.cumulativeProbDistributionCalculation(smallNND_matrix)
            self.allSmallPercNND.append(smallPercNND)
            self.allSmallNNDMatrix.append(smallNND_matrix)

            smallFullMatrix = DistanceCalculations.getDistanceMatrix() # this is only executable if previously the NND calculation was done
            smallPercFull = DistanceCalculations.cumulativeProbDistributionCalculation(smallFullMatrix)
            self.allSmallPercFull.append(smallPercFull)
            self.allSmallFullMatrix.append(smallFullMatrix)

            tmpArray = DistanceCalculations.calculateDistanceFromCentroid(polygonCentroidInUm, (self.tmpRandomSmall / (MainGUI.nmPixelRatio*1e3)))
            self.randomCentroidDistance.append(tmpArray)

            tmpClosestEdgeArray = DistanceCalculations.getDistanceFromNearestEdge((self.tmpRandomSmall / (MainGUI.nmPixelRatio*1e3)), AZOutlineInUm)
            self.smallRandomClosestEdgeDistance.append(tmpClosestEdgeArray)

            # mean values of the computed parameters into one vector
            self.randomNNDMean.append(np.mean(smallNND_matrix))
            self.randomAllDistanceMean.append(np.mean(smallFullMatrix))
            self.randomCentroidMean.append(np.mean(tmpArray))
            self.randomClosestEdgeMean.append(np.mean(tmpClosestEdgeArray))

            # possibility to perform spatial autocorrelation on random samples
            if(self.PerformSpatialAutocorrelationCheckBox.isChecked() == True):
                global binSize
                binSize = 1

                rmax = int(np.around(MainGUI.nmPixelRatio * self.spatialRmaxSpinBox.value()))

                tmp_g = []
                self.ACF_radiusVec, tmp_g = Clustering.calculateSpatialAutocorrelationFunction(MainGUI.imgScaled, maskSize, self.tmpRandomSmall, rmax, MainGUI.nmPixelRatio, binSize, False, False, 1)
                self.random_g_r.append(tmp_g)

            print (i+1, '/', int(self.randomDataSampleDoubleSpinBox.value()), 'done')

        # if spatial autocorrelation analysis performed on the random samples, save data
        if(self.PerformSpatialAutocorrelationCheckBox.isChecked() == True):

            # check if the 2D ACF is already calculated for the actual experimental data
            if(self.g_r == []):
                print ('-----')
                #print 'Please perform 2D autocorrelation calculation on actual experimental data first'
                self.performSpatialAutocorrelation()
            else:
                pass

            # calculating mean values of g(r) functions (for experimental and random data as well)
            randomMeanGr = []
            for i in range(0, len(self.random_g_r)):

                randomMeanGr.append(np.mean(self.random_g_r[i]))

            expMeanGr = np.mean(self.g_r)
            randomMeanGr = np.sort(np.asarray(randomMeanGr))

            grIndex = DistanceCalculations.getElementIndex(expMeanGr, randomMeanGr)

            # Creating the Excel workbook in which data will be saved
            workbookFilename = str(clusterOpenedFilename[0][0:-4]) + '_2D_ACF.xlsx'
            workbook = xw.Workbook(workbookFilename)

            self.ACF_radiusVec = self.ACF_radiusVec.tolist()

            ExcelSave.saveDataInExcel_2D_ACF(workbook, self.ACF_radiusVec, self.g_r, self.random_g_r, expMeanGr, randomMeanGr, grIndex)
            workbook.close()

            print ('-----')
            print ('Random 2D ACF data is saved at:', workbookFilename)

        self.saveData(self.allSmallNNDMatrix, self.allSmallFullMatrix)

        print ('-----')
        print ('N = %0.0f random data sets were generated in %0.3f seconds' % (self.randomDataSampleDoubleSpinBox.value(), float(time.time() - start_time)))

    # computing the features of artificially clustered data
    def experimentalDataCalculations(self):
        self.randomGoldParticlesInPolygonInUm = []
        self.expSmallPercFull = []
        self.expSmallPercNND = []
        self.expSmallNNDMatrix = []
        self.expSmallFullMatrix = []
        self.centroidDistance = []

        # pixel to um conversion
        for i in range(0, len(self.randomGoldParticlesInPolygon)):
            self.randomGoldParticlesInPolygonInUm.append(QtCore.QPointF(self.randomGoldParticlesInPolygon[i].x() / (MainGUI.nmPixelRatio*1e3), self.randomGoldParticlesInPolygon[i].y() / (MainGUI.nmPixelRatio*1e3)))
        for i in range(0, len(self.randomAZBackgroundParticles)):
            self.randomGoldParticlesInPolygonInUm.append(QtCore.QPointF(self.randomAZBackgroundParticles[i].x() / (MainGUI.nmPixelRatio*1e3), self.randomAZBackgroundParticles[i].y() / (MainGUI.nmPixelRatio*1e3)))

        # calling the 2 previously defined function from module 'DistanceCalculations'
        # small gold particles
        self.expSmallNNDMatrix = DistanceCalculations.nearestNeighborDistanceCalculation(self.randomGoldParticlesInPolygonInUm)
        self.expSmallPercNND = DistanceCalculations.cumulativeProbDistributionCalculation(self.expSmallNNDMatrix)

        self.expSmallFullMatrix = DistanceCalculations.getDistanceMatrix()
        self.expSmallPercFull = DistanceCalculations.cumulativeProbDistributionCalculation(self.expSmallFullMatrix)

        global polygonCentroidInUm
        polygonCentroidInUm = DistanceCalculations.calculateGoldParticleCentroid(self.randomGoldParticlesInPolygonInUm)

        #polygonCentroidInUm = (QtCore.QPointF(polygonCentroid.x() / (MainGUI.nmPixelRatio*1e3), polygonCentroid.y() / (MainGUI.nmPixelRatio*1e3)))

        # calculating the distance from the centroid of the labelled gold particles
        self.centroidDistance = DistanceCalculations.calculateDistanceFromCentroid(polygonCentroidInUm, self.randomGoldParticlesInPolygonInUm)

        AZOutlineInUm = []
        for i in range(0, len(MainGUI.globalSynapticAreaOutlinePoints) - 1):
            AZOutlineInUm.append(MainGUI.globalSynapticAreaOutlinePoints[i] / (MainGUI.nmPixelRatio*1e3))

        self.smallClosestEdgeDistance = DistanceCalculations.getDistanceFromNearestEdge(self.randomGoldParticlesInPolygonInUm, AZOutlineInUm)

    # save data in an Excel file
    def saveData(self, allSmallNNDMatrix, allSmallFullMatrix):

        # Creating the Excel workbook in which data will be saved
        workbookFilename = str(clusterOpenedFilename[0][0:-4]) + '_distance_measurements.xlsx'
        workbook = xw.Workbook(workbookFilename)

        # save data in excel file
        ExcelSave.saveDataInExcel(workbook, 'Small - NND', int(self.randomDataSampleDoubleSpinBox.value()), self.expSmallNNDMatrix, self.allSmallNNDMatrix, MainGUI.AZarea) #, smallNND_pValue, p005_counter, p001_counter)

        # save data in excel file
        ExcelSave.saveDataInExcel(workbook, 'Small - All', int(self.randomDataSampleDoubleSpinBox.value()), self.expSmallFullMatrix, self.allSmallFullMatrix, MainGUI.AZarea) #, smallAll_pValue, p005_counter, p001_counter)

        # save data in excel file
        ExcelSave.saveDataInExcel(workbook, 'Small - Centroid', int(self.randomDataSampleDoubleSpinBox.value()), self.centroidDistance, self.randomCentroidDistance, MainGUI.AZarea) #, centroid_pValue, p005_counter, p001_counter)

        # save data in excel file
        ExcelSave.saveDataInExcel(workbook, 'Small - Nearest edge', int(self.randomDataSampleDoubleSpinBox.value()), self.smallClosestEdgeDistance, self.smallRandomClosestEdgeDistance, MainGUI.AZarea) #, nearestEdge_pValue, p005_counter, p001_counter)

        # Calculating median values from all pooled randomly generated datasets
        randomNNDMedian = np.median(np.resize(np.asarray(self.allSmallNNDMatrix), (len(self.allSmallNNDMatrix), len(self.allSmallNNDMatrix[0]))))
        randomAllDistanceMedian = np.median(np.resize(np.asarray(self.allSmallFullMatrix), (len(self.allSmallFullMatrix), len(self.allSmallFullMatrix[0]))))
        randomCendtroidMedian = np.median(np.resize(np.asarray(self.randomCentroidDistance), (len(self.randomCentroidDistance), len(self.randomCentroidDistance[0]))))
        randomClosestEdgeMedian = np.median(np.resize(np.asarray(self.smallRandomClosestEdgeDistance), (len(self.smallRandomClosestEdgeDistance), len(self.smallRandomClosestEdgeDistance[0]))))

        # sorting the arrays and saving mean values of calculated parameters into a different worksheet
        self.randomNNDMean = np.sort(self.randomNNDMean)
        self.randomAllDistanceMean = np.sort(self.randomAllDistanceMean)
        self.randomCentroidMean = np.sort(self.randomCentroidMean)
        self.randomClosestEdgeMean = np.sort(self.randomClosestEdgeMean)

        # get index of the array, where the actual mean is just smaller than the next element in the array
        NNDIndex = DistanceCalculations.getElementIndex(np.mean(self.expSmallNNDMatrix), self.randomNNDMean)
        AllDistanceIndex = DistanceCalculations.getElementIndex(np.mean(self.expSmallFullMatrix), self.randomAllDistanceMean)
        CentroidIndex = DistanceCalculations.getElementIndex(np.mean(self.centroidDistance), self.randomCentroidMean)
        ClosestEdgeIndex = DistanceCalculations.getElementIndex(np.mean(self.smallClosestEdgeDistance), self.randomClosestEdgeMean)

        # save distance calculation summary into Excel as well
        ExcelSave.saveDataInExcel_distanceSummary(workbook, self.expSmallNNDMatrix, self.expSmallFullMatrix, self.centroidDistance, self.smallClosestEdgeDistance, self.randomNNDMean, self.randomAllDistanceMean, self.randomCentroidMean, self.randomClosestEdgeMean, NNDIndex, AllDistanceIndex, CentroidIndex, ClosestEdgeIndex, randomNNDMedian, randomAllDistanceMedian, randomCendtroidMedian, randomClosestEdgeMedian, self.polygonAreaList)

        workbook.close()
        print ('-----')
        print ('Distance measurements data is saved at ', str(clusterOpenedFilename[0][0:-4]) + '_distance_measurements.xlsx')

    def performDBSCAN(self):
        # has to be converted to pixel, given in nm by GUI interaction
        epsilonInPixel = self.DBSCANEpsilonDoubleSpinBox.value() * MainGUI.nmPixelRatio
        # perform DBSCAN
        array, labels = Clustering.dbscanClustering(self.randomGoldParticlesInPolygon, self.randomAZBackgroundParticles, self.randomBackgroundParticles, epsilonInPixel, self.DBSCANMinSampleDoubleSpinBox.value())

        # appending X and Y coordinates of the localization points to vectors to save them with the cluster IDs (labels)
        xVec = []
        yVec = []
        for i in range(0, len(array)):
            xVec.append(array[i][0])
            yVec.append(array[i][1])

        # appending vectors to a matrix
        dataMatrix = []
        dataMatrix.append(xVec)
        dataMatrix.append(yVec)
        dataMatrix.append(labels)

        # transpose the matrix to have the data columnwise and save it with a '_DBSCAN' suffix
        dataMatrix = np.transpose(np.asarray(dataMatrix))
        filenameToSave = str(clusterOpenedFilename[0:-4]) + '_DBSCAN_epsilon=' + str(int(self.DBSCANEpsilonDoubleSpinBox.value())) + 'nm_minSample=' + str(int(self.DBSCANMinSampleDoubleSpinBox.value())) + '.txt'
        np.savetxt(filenameToSave, dataMatrix, fmt='%0.0f')

    def performAffinityPropagation(self):
        array, labels = Clustering.affinityPropagationClustering(self.randomGoldParticlesInPolygon, self.randomAZBackgroundParticles, self.randomBackgroundParticles, self.affinityPropagationDoubleSpinBox.value())

        # appending X and Y coordinates of the localization points to vectors to save them with the cluster IDs (labels)
        xVec = []
        yVec = []
        for i in range(0, len(array)):
            xVec.append(array[i][0])
            yVec.append(array[i][1])

        # appending vectors to a matrix
        dataMatrix = []
        dataMatrix.append(xVec)
        dataMatrix.append(yVec)
        dataMatrix.append(labels)

        # transpose the matrix to have the data columnwise and save it with a '_affinity_propagation' suffix
        dataMatrix = np.transpose(np.asarray(dataMatrix))
        filenameToSave = str(clusterOpenedFilename[0][0:-4]) + '_affinity_propagation_pref=' + str(int(self.affinityPropagationDoubleSpinBox.value())) + '.txt'
        np.savetxt(filenameToSave, dataMatrix, fmt='%0.0f')

    def performMeanShift(self):
        array, labels = Clustering.meanShiftClustering(self.randomGoldParticlesInPolygon, self.randomAZBackgroundParticles, self.randomBackgroundParticles, int(self.MeanShiftMinSampleDoubleSpinBox.value()))

        # appending X and Y coordinates of the localization points to vectors to save them with the cluster IDs (labels)
        xVec = []
        yVec = []
        for i in range(0, len(array)):
            xVec.append(array[i][0])
            yVec.append(array[i][1])

        # appending vectors to a matrix
        dataMatrix = []
        dataMatrix.append(xVec)
        dataMatrix.append(yVec)
        dataMatrix.append(labels)

        # transpose the matrix to have the data columnwise and save it with a '_mean_shift' suffix
        dataMatrix = np.transpose(np.asarray(dataMatrix))
        filenameToSave = str(clusterOpenedFilename[0][0:-4]) + '_mean_shift_minSample=' + str(int(self.MeanShiftMinSampleDoubleSpinBox.value())) + '.txt'
        np.savetxt(filenameToSave, dataMatrix, fmt='%0.0f')

    def performSpatialAutocorrelation(self):
        #for generation of homogeneously distributed localizations
        #homLoc = Clustering.generateHomogenousLocalizations(imgScaled, 2)
        #Clustering.calculateSpatialAutocorrelationFunction(imgScaled, homLoc, 200, 1, 1)

        self.experimentalDataCalculations()
        maskSize = DistanceCalculations.getSynapticAreaOutlineBorders(MainGUI.globalSynapticAreaOutlinePoints)

        # concatenate localization-containing arrays
        allGoldParticles = []
        allGoldParticles = np.concatenate((self.randomGoldParticlesInPolygon, self.randomBackgroundParticles, self.randomAZBackgroundParticles), axis = 0)

        binSize = 1

        rmax = int(np.around(MainGUI.nmPixelRatio * self.spatialRmaxSpinBox.value()))

        self.g_r = []
        self.ACF_radiusVec, self.g_r = Clustering.calculateSpatialAutocorrelationFunction(MainGUI.imgScaled, maskSize, allGoldParticles, rmax, MainGUI.nmPixelRatio, binSize, True, self.SaveSpatialAutocorrelationCheckBox.isChecked(), 1)

        return self.g_r


# main
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    clusterWindow = GoldExtClusterGui()
    clusterWindow.show()
    app.exec_()