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

import sys
import os.path
from PyQt4 import QtCore, QtGui, uic
import GenerateArtificialData
import DistanceCalculations
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.path as mPath
from matplotlib.backends.backend_pdf import PdfPages
import time
from scipy import stats
import xlsxwriter as xw
from xlsxwriter.utility import xl_rowcol_to_cell
import ExcelSave
from ClusterGui import GoldExtClusterGui
import Clustering

# defining the GUI drawn in Qt Desinger
qtGoldExtMainGui = '.\\GoldExt_GUI.ui'

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtGoldExtMainGui)

class GoldExtMainGui(QtGui.QMainWindow, Ui_MainWindow):

    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        # setting a grapchics scene with appropriate size
        self.scene = QtGui.QGraphicsScene(0, 0, 690, 650)
        self.scene.wheelEvent = self.zoomWithWheel

        # button which calls the file dialog window by clicking on it
        self.openFileButton.clicked.connect(self.openAndVisualizeImage)
        # 'lambda:' argument is needed for the correct working of the button, it avoids the evaluation of the function call, so it'll call the given function only when clicked
        # delete everything from the scene
        self.clearSceneButton.clicked.connect(self.clearScene)
        self.saveStateButton.clicked.connect(self.saveState)
        self.saveImageButton.clicked.connect(self.saveImage)
        self.deleteScaleButton.clicked.connect(self.deleteScalebar)
        self.deleteAZOutlineButton.clicked.connect(self.deleteAZOutline)
        self.openSavedStateButton.clicked.connect(self.openSavedSate)
        self.generateAllRandomDataButton.clicked.connect(self.generateAllRandomData)
        self.performDBSCANButton.clicked.connect(self.performDBSCAN)
        self.performAffinityPropagationButton.clicked.connect(self.performAffinityPropagation)
        self.performMeanShiftButton.clicked.connect(self.performMeanShift)
        self.performSpatialAutocorrelationButton.clicked.connect(self.performSpatialAutocorrelation)

        self.openClusteringGuiWindowButton.clicked.connect(self.openClusteringWindowGui)

        self.synapticAreaRadioButton.setEnabled(0)
        self.synapticAreaEndingRadioButton.setEnabled(0)
        self.scalebarRadioButton.setEnabled(0)
        self.saveStateButton.setEnabled(0)
        self.openSavedStateButton.setEnabled(0)

        self.synapticAreaRadioButton.clicked.connect(self.drawSynapticAreaOutline)
        self.synapticAreaEndingRadioButton.clicked.connect(self.endOfPolygon)
        self.scalebarRadioButton.clicked.connect(self.makeImageDrawable)
        self.markSmallGoldParticlesButton.clicked.connect(self.drawSmallGoldParticles)
        #self.markLargeGoldParticlesButton.clicked.connect(self.drawLargeGoldParticles)
        self.deleteLastSmallGoldButton.clicked.connect(self.deleteSmallGoldParticles)
        #self.deleteLastLargeGoldButton.clicked.connect(self.deleteLargeGoldParticles)

        # defining variables accessible in this class
        self.synapticAreaOutlinePoints = []
        self.synapticAreaOutlinePointsInUm = []
        self.scalebarPoints = []
        self.smallGoldParticleCoordinates = []
        self.largeGoldParticleCoordinates = []
        self.smallGoldParticleCoordinatesInUm = []
        self.largeGoldParticleCoordinatesInUm = []

        self.tmpRandomSmall = []
        self.tmpRandomLarge = []

        self.expSmallPercFull = []
        self.expSmallPercNND = []
        self.expLargePercFull = []
        self.expLargePercNND = []

        self.expSmallNNDMatrix = []
        self.expSmallFullMatrix = []
        self.expLargeNNDMatrix = []
        self.expLargeFullMatrix = []

        self.allSmallPercNND = []
        self.allSmallPercFull = []
        self.allLargePercNND = []
        self.allLargePercFull = []

        self.allSmallNNDMatrix = []
        self.allSmallFullMatrix = []
        self.allLargeNNDMatrix = []
        self.allLargeFullMatrix = []

        self.smallCentroidDistance = []
        self.largeCentroidDistance = []
        self.smallRandomCentroidDistance = []
        self.largeRandomCentroidDistance = []

        self.smallClosestEdgeDistance = []
        self.smallRandomClosestEdgeDistance = []

        self.randomNNDMean = []
        self.randomAllDistanceMean = []
        self.randomCentroidMean = []
        self.randomClosestEdgeMean = []

        self.g_r = []

        self.ACF_radiusVec = []

        # recent directory variable
        self.recDir = ''

    # function that deletes everything from the screen
    def clearScene(self):
        self.recDir = openedFilename[0:-4]
        self.scene.clear()
        # setting the image scaling factor to 0, since the screen has been emptied
        #self.imageScaleLCD.display(0)
        # delete all the existing data points, outlines and the scalebar as well
        self.synapticAreaOutlinePoints = []
        self.scalebarPoints = []
        self.smallGoldParticleCoordinates = []
        self.largeGoldParticleCoordinates = []
        self.smallGoldParticleLcdNumber.display(len(self.smallGoldParticleCoordinates))
        self.largeGoldParticleLcdNumber.display(len(self.largeGoldParticleCoordinates))
        print '-----'
        print 'Screen is cleared'

    # this function loads an image to the given area (500*500 by definition) of the screen
    def openAndVisualizeImage(self):
        # opens the file dialog, to select the desired image file; only files appear with the listed extensions
        global openedFilename # making it global to be accessible for other functions as well
        if(self.recDir != ''):
            openedFilename = QtGui.QFileDialog.getOpenFileName(self, 'Open file', self.recDir, 'Image Files (*.png *.jpg *.jpeg *.tif)')
        else:
            openedFilename = QtGui.QFileDialog.getOpenFileName(self, 'Open file', '/', 'Image Files (*.png *.jpg *.jpeg *.tif)')
        # creating an object for the file read in
        img = QtGui.QPixmap(openedFilename)
        # checking if the loaded file is valid
        if(img.width() == 0):
            print '-----'
            print 'No image loaded, please choose one to proceed.'
        # if the image is loaded and valid, go on
        else:
            # rescaling the image so that it fits into the graphics scene
            global imgScaled # making it global to be accessible for other classes as well
            imgScaled = img.scaled(self.scene.width(), self.scene.height(), QtCore.Qt.KeepAspectRatio)
            #print 'Scaled image: %d * %d (pixel)' % (imgScaled.width(), imgScaled.height())
            #print imgScaled.width(), imgScaled.height()
            # visualizing the scaling factor on the LCD screen
            imageScalingFactor = float(imgScaled.width())/float(img.width())
            #self.imageScaleLCD.display(imageScalingFactor)
            # adding the rescaled image to the graphics scene
            self.scene.addPixmap(imgScaled)
            # visualizing the scene
            self.imageLoaderView.setScene(self.scene)

            self.scalebarRadioButton.setEnabled(1)
            self.openSavedStateButton.setEnabled(1)

    # letting the user to draw on the loaded image (synaptic area, gold particles)
    def makeImageDrawable(self):
        self.imgItem = QtGui.QGraphicsPixmapItem(imgScaled, None, self.scene)
        self.imgItem.mousePressEvent = self.selectScalebarPoints
        #self.imgItem.mouseDoubleClickEvent = self.endOfPolygon
        self.synapticAreaRadioButton.setEnabled(1)

    # letting the user to zoom in and out with the mouse wheel
    def zoomWithWheel(self, event):
        'zoom'
        sc = event.delta()/100.
        if sc < 0:
            sc = -1 / sc
        self.imageLoaderView.scale(sc,sc)

    # drawing the scalebar onto the screen
    def selectScalebarPoints(self, event):
        global globalScalebarPoints
        if(len(self.scalebarPoints) < 2):
            self.scalebarPoints.append(event.pos())
        if(len(self.scalebarPoints) > 1):
            # have to set an exactly flat line, for accurate distance measurements
            self.scalebarPoints[1].y = self.scalebarPoints[0].y
            self.drawScalebar(self.scalebarPoints, self.scalebarSpinBox.value())

            globalScalebarPoints = self.scalebarPoints

    def drawScalebar(self, array, scalebarValue):
        global globalScalebarValue
        globalScalebarValue = scalebarValue
        scalebarLine = QtCore.QLineF(array[0].x(), array[0].y(), array[1].x(), array[0].y())
        # adding the scalebar to the scene (visualize it)
        tmpScale = self.scene.addLine(scalebarLine, QtGui.QPen(QtCore.Qt.red))
        scaleBarString = QtCore.QString('%0.0f nm' % scalebarValue)
        printedScalebar = self.scene.addText(scaleBarString, QtGui.QFont('', 12))
        # setting the position of the scalebar
        printedScalebar.setPos(array[0].x(), array[0].y())
        # setting the color of the scalebar
        printedScalebar.setDefaultTextColor(QtCore.Qt.red)
        # calculate the nm to pixel ratio
        self.calculateNmPixelRatio(scalebarLine)
        print '-----'
        print 'Scale is set'
        self.scalebarRadioButton.setEnabled(0)

    def deleteScalebar(self):
        if(len(self.scalebarPoints) == 0):
            pass
        else:
            self.clearScene()
            self.scalebarPoints = []
            # remap the image to the scene
            self.scene.addPixmap(imgScaled)
            # visualizing the scene
            self.imageLoaderView.setScene(self.scene)
            self.makeImageDrawable()

    # calculating the nm to pixel ratio for accurate scaling
    def calculateNmPixelRatio(self, array):
        scaleBarLengthInPixel = array.length()
        scaleBarLengthInNm = self.scalebarSpinBox.value()
        global nmPixelRatio
        #print scaleBarLengthInPixel
        #print scaleBarLengthInNm
        nmPixelRatio = scaleBarLengthInPixel/scaleBarLengthInNm
        print '1 pixel = %0.3f nm' % (1.0/nmPixelRatio)

    # redefining mousPressEvent for synaptic area outline drawing
    def drawSynapticAreaOutline(self, event):
        self.imgItem.mousePressEvent = self.synapticAreaOutlineSelect

    # getting the clicked position of the mouse, and appending the coordinates into an array
    # if the array length is longer than 1, it draws lines between points
    def synapticAreaOutlineSelect(self, event):
        self.synapticAreaOutlinePoints.append(event.pos())
        if(len(self.synapticAreaOutlinePoints) > 1):
            self.scene.addItem(QtGui.QGraphicsLineItem(QtCore.QLineF(self.synapticAreaOutlinePoints[-2], self.synapticAreaOutlinePoints[-1])))
        if(len(self.synapticAreaOutlinePoints) > 2):
            self.synapticAreaEndingRadioButton.setEnabled(1)

    # this function closes the polygon and calculates its centroid
    def endOfPolygon(self, event):
        global globalSynapticAreaOutlinePoints
        self.synapticAreaOutlinePoints.append(self.synapticAreaOutlinePoints[0])
        self.scene.addPolygon(QtGui.QPolygonF(self.synapticAreaOutlinePoints), QtGui.QPen(QtCore.Qt.red))
        # creating path of synaptic area, essential for deciding wheter a point is within this border or not
        self.createPathOfSynapticArea(self.synapticAreaOutlinePoints)
        # for not to let the user draw more than one synaptic area on a single image
        self.synapticAreaRadioButton.setEnabled(0)
        self.synapticAreaEndingRadioButton.setEnabled(0)
        self.saveStateButton.setEnabled(1)

        globalSynapticAreaOutlinePoints = self.synapticAreaOutlinePoints

    def deleteAZOutline(self):
        if(self.synapticAreaOutlinePoints == 0):
            pass
        else:
            tmpScalebarPoints = self.scalebarPoints
            self.synapticAreaOutlinePoints = []
            self.synapticAreaOutlinePointsInUm = []
            self.synapticAreaOutlinePath = []
            self.clearScene()
            # remap the image to the scene
            self.scene.addPixmap(imgScaled)
            # visualizing the scene
            self.imageLoaderView.setScene(self.scene)
            self.scalebarPoints = tmpScalebarPoints
            self.imgItem = QtGui.QGraphicsPixmapItem(imgScaled, None, self.scene)
            self.drawScalebar(self.scalebarPoints, self.scalebarSpinBox.value())
            self.synapticAreaRadioButton.setEnabled(1)

    # creating a matplotlib path from the synaptic area outline points; this is needed for random data point generation
    def createPathOfSynapticArea(self, arrayOfPoints):
        global polyArea
        polyArea = DistanceCalculations.PolygonArea(arrayOfPoints)
        global AZarea, totalArea
        AZarea = polyArea/(nmPixelRatio**2)/1e6
        totalArea = imgScaled.width()*imgScaled.height()/(nmPixelRatio**2)/1e6
        print '-----'
        print 'AZ area: %0.3f um2' % AZarea
        print 'Total area: %0.3f um2' % totalArea
        #print 'Polygon area %0.3f nm2' % (polyArea/(nmPixelRatio**2))
        #print 'Ratio: %0.3f' % (totalArea / AZarea)
        self.synapticAreaOutlinePath = []
        pathInUm = []
        global realPath
        global realPathInUm
        for i in range(0, len(arrayOfPoints)):
            tempData = [arrayOfPoints[i].x(), arrayOfPoints[i].y()]
            self.synapticAreaOutlinePath.append(tempData)
            # pixel to um conversion
            tmpX = arrayOfPoints[i].x()/(nmPixelRatio * 1e3)
            tmpY = arrayOfPoints[i].y()/(nmPixelRatio * 1e3)
            tempDataInUm = [tmpX, tmpY]
            pathInUm.append(tempDataInUm)
        realPath = mPath.Path(self.synapticAreaOutlinePath)
        realPathInUm = mPath.Path(pathInUm)

    # marking small gold particles on the synaptic area
    def markSmallGoldParticles(self, event):
        self.smallGoldParticleCoordinates.append(event.pos())
        pointDiam = 4
        tmpEllipse = QtGui.QGraphicsEllipseItem(self.smallGoldParticleCoordinates[-1].x()-pointDiam/2, self.smallGoldParticleCoordinates[-1].y()-pointDiam/2, pointDiam, pointDiam)
        tmpEllipse.setPen(QtGui.QPen(QtCore.Qt.green, 2))
        self.scene.addItem(tmpEllipse)
        self.smallGoldParticleLcdNumber.display(len(self.smallGoldParticleCoordinates))

    # defining the mousePressEvent for drawing small gold particles
    def drawSmallGoldParticles(self, event):
        self.imgItem.mousePressEvent = self.markSmallGoldParticles

    # delete the last small gold particle
    def deleteSmallGoldParticles(self):
        if(len(self.smallGoldParticleCoordinates) > 0):
            p = self.smallGoldParticleCoordinates[-1]
            del self.smallGoldParticleCoordinates[-1]
            self.scene.removeItem(self.scene.itemAt(p.x(), p.y()))
        else:
            print '----'
            print 'No more small gold particles located in the active zone'
        self.smallGoldParticleLcdNumber.display(len(self.smallGoldParticleCoordinates))

    # marking large gold particles on the synaptic area
    def markLargeGoldParticles(self, event):
        self.largeGoldParticleCoordinates.append(event.pos())
        pointDiam = 8
        tmpEllipse = QtGui.QGraphicsEllipseItem(self.largeGoldParticleCoordinates[-1].x()-pointDiam/2, self.largeGoldParticleCoordinates[-1].y()-pointDiam/2, pointDiam, pointDiam)
        tmpEllipse.setPen(QtGui.QPen(QtCore.Qt.blue, 2))
        self.scene.addItem(tmpEllipse)
        self.largeGoldParticleLcdNumber.display(len(self.largeGoldParticleCoordinates))

    # defining the mousePressEvent for drawing large gold particles
    def drawLargeGoldParticles(self, event):
        self.imgItem.mousePressEvent = self.markLargeGoldParticles

    # delete the last large gold particle
    def deleteLargeGoldParticles(self):
        if(len(self.largeGoldParticleCoordinates) > 0):
            p = self.largeGoldParticleCoordinates[-1]
            del self.largeGoldParticleCoordinates[-1]
            self.scene.removeItem(self.scene.itemAt(p.x(), p.y()))
        else:
            print '----'
            print 'No more large gold particles located in the active zone'
        self.largeGoldParticleLcdNumber.display(len(self.largeGoldParticleCoordinates))

    def generateRandomSmallData(self):
        self.tmpRandomSmall = []
        if(len(self.smallGoldParticleCoordinates) == 0):
            print '-----'
            print 'There are 0 small gold particles labelled, no distribution could be generated'
        else:
            # get_extents() function of a path returns the min and max values of x and y coordinates of the path
            self.tmpRandomSmall = GenerateArtificialData.generateSetOfRandomDataPoints(realPath, None, True, len(self.smallGoldParticleCoordinates), 10*nmPixelRatio, realPath.get_extents().x0, realPath.get_extents().x1, realPath.get_extents().y0, realPath.get_extents().y1)
            # self.tmpRandomSmall = GenerateArtificialData.generateSetOfRandomDataPoints(None, None, True, len(self.smallGoldParticleCoordinates), 10 * nmPixelRatio, realPath.get_extents().x0, realPath.get_extents().x1, realPath.get_extents().y0, realPath.get_extents().y1)

    def generateRandomLargeData(self):
        self.tmpRandomLarge = []
        if(len(self.largeGoldParticleCoordinates) == 0):
            print '-----'
            print 'There are 0 large gold paricles labelled, no distribution could be generated'
        else:
            self.tmpRandomLarge = GenerateArtificialData.generateSetOfRandomDataPoints(realPath, None, True, len(self.largeGoldParticleCoordinates), 10*nmPixelRatio, realPath.get_extents().x0, realPath.get_extents().x1, realPath.get_extents().y0, realPath.get_extents().y1)

    # saving the image with the drawn objects (scalebar, AZ outline, data points)
    def saveImage(self):
        painter = QtGui.QPainter(imgScaled)
        self.scene.render(painter, QtCore.QRectF(0, 0, self.scene.width(), self.scene.height()))
        saveImageFilename = str(openedFilename[0:-4]) + '_scaled.jpg'
        imgScaled.save(saveImageFilename, "JPG")
        print '-----'
        print 'Image saved at', saveImageFilename

    def saveState(self):
        # specifying the filename of the file which contains the saved state (with a .gss extension for easier recognition)
        savedStateFilename = openedFilename[0:-3] + 'gss'

        # searching for the longest array to store data
        maxLength = 0
        lengthVec = []
        lengthVec.append(len(self.synapticAreaOutlinePoints))
        lengthVec.append(len(self.smallGoldParticleCoordinates))
        lengthVec.append(len(self.largeGoldParticleCoordinates))
        maxLength = max(lengthVec)

        # saving the calculated data in an ASCII file, with a .gss extension for easier recognition
        f = open(savedStateFilename, 'w')

        for i in range(0, maxLength + 2):
            if(i == 0): # setting up the header of the file with important informations
                value0 = str(self.scalebarSpinBox.value())
                value1 = 'nm'
                value2 = ' '
                value3 = 'AZ_area'
                value4 = str(AZarea)
                value5 = 'um2'
                value6 = ''
                value7 = ''
                value8 = ''
            if(i == 1): # name the respective lists
                value0 = 'scalebar_x'
                value1 = 'scalebar_y'
                value2 = 'synapticAreaOutline_x'
                value3 = 'synapticAreaOutline_y'
                value4 = 'smallGoldParticleCoordinates_x'
                value5 = 'smallGoldParticleCoordinates_y'
                value6 = 'largeGoldParticleCoordinates_x'
                value7 = 'largeGoldParticleCoordinates_y'
            if(i > 1):
                if(len(self.scalebarPoints) > i-2):
                    value0 = str(self.scalebarPoints[i-2].x())
                    value1 = str(self.scalebarPoints[i-2].y())
                else:
                    value0 = value1 = '-'
                if(len(self.synapticAreaOutlinePoints) > i-2):
                    value2 = str(self.synapticAreaOutlinePoints[i-2].x())
                    value3 = str(self.synapticAreaOutlinePoints[i-2].y())
                else:
                    value2 = value3 = '-'
                if(len(self.smallGoldParticleCoordinates) > i-2):
                    value4 = str(self.smallGoldParticleCoordinates[i-2].x())
                    value5 = str(self.smallGoldParticleCoordinates[i-2].y())
                else:
                    value4 = value5 = '-'
                if(len(self.largeGoldParticleCoordinates) > i-2):
                    value6 = str(self.largeGoldParticleCoordinates[i-2].x())
                    value7 = str(self.largeGoldParticleCoordinates[i-2].y())
                else:
                    value6 = value7 = '-'

            s = str(value0 + '  ' + value1 + '  ' + value2 + '  ' + value3 + '  ' + value4 + '  ' + value5 + '  ' + value6 + '  ' + value7 + '\n')
            f.write(s)

        f.close()
        print '-----'
        print 'State saved at %s' % savedStateFilename

    def openSavedSate(self):
        global globalSynapticAreaOutlinePoints, globalScalebarPoints

        self.scalebarPoints = []
        self.synapticAreaOutlinePoints = []
        self.smallGoldParticleCoordinates = []
        self.largeGoldParticleCoordinates = []

        # checking if a saved state exists for the given file image; if so, load data and redraw it onto the image
        tmpFilename =  openedFilename[0:-3] + 'gss'
        if(os.path.isfile(tmpFilename)):

            # making the image drawable again
            self.imgItem = QtGui.QGraphicsPixmapItem(imgScaled, None, self.scene)
            self.saveStateButton.setEnabled(1)

            f = open(tmpFilename, 'r')
            i = 0
            for line in f:
                row = line.split()
                if(i == 0):
                    # loading the scalebar value, and set the spinbox value accordingly
                    scaleScalar = float(row[0])
                    self.scalebarSpinBox.setValue(scaleScalar)
                if(i > 1):
                    # load data: scalebar, synaptic area outline, small and large gold particle coordinates
                    if(row[0] != '-'):
                        self.scalebarPoints.append(QtCore.QPointF(float(row[0]), float(row[1])))
                        globalScalebarPoints = self.scalebarPoints
                    if(row[2] != '-'):
                        self.synapticAreaOutlinePoints.append(QtCore.QPointF(float(row[2]), float(row[3])))
                    if(row[4] != '-'):
                        self.smallGoldParticleCoordinates.append(QtCore.QPointF(float(row[4]), float(row[5])))
                    if(row[6] != '-'):
                        self.largeGoldParticleCoordinates.append(QtCore.QPointF(float(row[6]), float(row[7])))
                i += 1
            # redrawing the loaded structures onto the image
            # scalebar
            globalScalebarPoints = self.scalebarPoints
            self.drawScalebar(self.scalebarPoints, scaleScalar)
            # synaptic area outline
            globalSynapticAreaOutlinePoints = self.synapticAreaOutlinePoints
            self.scene.addPolygon(QtGui.QPolygonF(self.synapticAreaOutlinePoints), QtGui.QPen(QtCore.Qt.red))
            # creating path from the outline points to be able to generate random data points
            self.createPathOfSynapticArea(self.synapticAreaOutlinePoints)
            globalSynapticAreaOutlinePoints = self.synapticAreaOutlinePoints
            # small gold particles
            for i in range(0, len(self.smallGoldParticleCoordinates)):
                pointDiam = 4
                tmpEllipse = QtGui.QGraphicsEllipseItem(self.smallGoldParticleCoordinates[i].x()-pointDiam/2, self.smallGoldParticleCoordinates[i].y()-pointDiam/2, pointDiam, pointDiam)
                tmpEllipse.setPen(QtGui.QPen(QtCore.Qt.green, 2))
                self.scene.addItem(tmpEllipse)
                self.smallGoldParticleLcdNumber.display(len(self.smallGoldParticleCoordinates))
            # large gold particles
            for i in range(0, len(self.largeGoldParticleCoordinates)):
                pointDiam = 8
                tmpEllipse = QtGui.QGraphicsEllipseItem(self.largeGoldParticleCoordinates[i].x()-pointDiam/2, self.largeGoldParticleCoordinates[i].y()-pointDiam/2, pointDiam, pointDiam)
                tmpEllipse.setPen(QtGui.QPen(QtCore.Qt.blue, 2))
                self.scene.addItem(tmpEllipse)
                self.largeGoldParticleLcdNumber.display(len(self.largeGoldParticleCoordinates))
            # calculate the centroid of the loaded polygon
            global polygonCentroid
            polygonCentroid = DistanceCalculations.calculateGoldParticleCentroid(self.smallGoldParticleCoordinates)

            print '-----'
            print 'Saved state loaded succesfully'
        else:
            print '-----'
            print 'No saved state found for this image'

    def experimentalDataCalculations(self):
        self.smallGoldParticleCoordinatesInUm = []
        self.largeGoldParticleCoordinatesInUm = []
        self.synapticAreaOutlinePointsInUm = []

        self.expSmallPercFull = []
        self.expSmallPercNND = []
        self.expLargePercFull = []
        self.expLargePercNND = []
        self.expSmallNNDMatrix = []
        self.expSmallFullMatrix = []
        self.expLargeNNDMatrix = []
        self.expLargeFullMatrix = []
        self.smallClosestEdgeDistance = []

        # pixel to um conversion
        for i in range(0, len(self.smallGoldParticleCoordinates)):
            self.smallGoldParticleCoordinatesInUm.append(QtCore.QPointF(self.smallGoldParticleCoordinates[i].x() / (nmPixelRatio*1e3), self.smallGoldParticleCoordinates[i].y() / (nmPixelRatio*1e3)))

        # the last element is not necessary to convert, since it is the same as the first
        for i in range(0, len(self.synapticAreaOutlinePoints) - 1):
            self.synapticAreaOutlinePointsInUm.append(QtCore.QPointF(self.synapticAreaOutlinePoints[i].x() / (nmPixelRatio*1e3), self.synapticAreaOutlinePoints[i].y() / (nmPixelRatio*1e3)))

        # calling the 2 previously defined function from module 'DistanceCalculations'
        # small gold particles
        self.expSmallNNDMatrix = DistanceCalculations.nearestNeighborDistanceCalculation(self.smallGoldParticleCoordinatesInUm)
        self.expSmallPercNND = DistanceCalculations.cumulativeProbDistributionCalculation(self.expSmallNNDMatrix)

        self.expSmallFullMatrix = DistanceCalculations.getDistanceMatrix()
        self.expSmallPercFull = DistanceCalculations.cumulativeProbDistributionCalculation(self.expSmallFullMatrix)

        self.smallClosestEdgeDistance = DistanceCalculations.getDistanceFromNearestEdge(self.smallGoldParticleCoordinatesInUm, self.synapticAreaOutlinePointsInUm)

        # large gold particles
        if(len(self.largeGoldParticleCoordinates) != 0):

            # pixel to um conversion
            for i in range(0, len(self.largeGoldParticleCoordinates)):
                self.largeGoldParticleCoordinatesInUm.append(QtCore.QPointF(self.largeGoldParticleCoordinates[i].x() / (nmPixelRatio*1e3), self.largeGoldParticleCoordinates[i].y() / (nmPixelRatio*1e3)))

            self.expLargeNNDMatrix = DistanceCalculations.nearestNeighborDistanceCalculation(self.largeGoldParticleCoordinatesInUm)
            self.expLargePercNND = DistanceCalculations.cumulativeProbDistributionCalculation(self.expLargeNNDMatrix)

            self.expLargeFullMatrix = DistanceCalculations.getDistanceMatrix()
            self.expLargePercFull = DistanceCalculations.cumulativeProbDistributionCalculation(self.expLargeFullMatrix)

        # convert the polygon centroid's coordinates to um
        polygonCentroid = DistanceCalculations.calculateGoldParticleCentroid(self.smallGoldParticleCoordinates)
        global polygonCentroidInUm
        polygonCentroidInUm = (QtCore.QPointF(polygonCentroid.x() / (nmPixelRatio*1e3), polygonCentroid.y() / (nmPixelRatio*1e3)))

        self.smallCentroidDistance = []
        self.smallCentroidDistance = DistanceCalculations.calculateDistanceFromCentroid(polygonCentroidInUm, self.smallGoldParticleCoordinatesInUm)

        # possibility to perform spatial autocorrelation on random samples
        if (self.PerformSpatialAutocorrelationCheckBox.isChecked() == True and self.g_r == []):
            # calculate mask size, which is the smallest rectangle that contains the synaptic AZ
            maskSize = DistanceCalculations.getSynapticAreaOutlineBorders(self.synapticAreaOutlinePoints)

            global binSize
            binSize = 1

            self.g_r = []

            rmax = int(np.around(nmPixelRatio * self.spatialRmaxSpinBox.value()))

            self.ACF_radiusVec, self.g_r = Clustering.calculateSpatialAutocorrelationFunction(imgScaled, maskSize, self.smallGoldParticleCoordinates, rmax, nmPixelRatio, binSize, False, self.SaveSpatialAutocorrelationCheckBox.isChecked(), 0)

    # random data generation
    def generateAllRandomData(self):
        self.allSmallPercNND = []
        self.allSmallPercFull = []
        self.allLargePercNND = []
        self.allLargePercFull = []

        self.allSmallNNDMatrix = []
        self.allSmallFullMatrix = []
        self.allLargeNNDMatrix = []
        self.allLargeFullMatrix = []

        self.smallRandomCentroidDistance = []
        self.smallRandomClosestEdgeDistance = []

        self.randomNNDMean = []
        self.randomAllDistanceMean = []
        self.randomCentroidMean = []
        self.randomClosestEdgeMean = []

        self.random_g_r = []

        self.random_L_est = []

        # start measuring the execution time of the code
        start_time = time.time()

        self.experimentalDataCalculations()

        # convert the polygon centroid's coordinates to um
        polygonCentroid = DistanceCalculations.calculateGoldParticleCentroid(self.smallGoldParticleCoordinates)
        global polygonCentroidInUm
        polygonCentroidInUm = (QtCore.QPointF(polygonCentroid.x() / (nmPixelRatio*1e3), polygonCentroid.y() / (nmPixelRatio*1e3)))

        # for spatial autocorrelation on random samples
        maskSize = DistanceCalculations.getSynapticAreaOutlineBorders(self.synapticAreaOutlinePoints)

        with PdfPages(openedFilename[0:-4] + '_random.pdf') as pdf:
            for i in range(0, self.randomSampleSpinBox.value()):
                self.generateRandomSmallData()
                # calling the 2 previously defined function from module 'DistanceCalculations'
                smallNND_matrix = DistanceCalculations.nearestNeighborDistanceCalculation(self.tmpRandomSmall / (nmPixelRatio*1e3))
                smallPercNND = DistanceCalculations.cumulativeProbDistributionCalculation(smallNND_matrix)
                self.allSmallPercNND.append(smallPercNND)
                self.allSmallNNDMatrix.append(smallNND_matrix)

                smallFullMatrix = DistanceCalculations.getDistanceMatrix() # this is only executable if previously the NND calculation was done
                smallPercFull = DistanceCalculations.cumulativeProbDistributionCalculation(smallFullMatrix)
                self.allSmallPercFull.append(smallPercFull)
                self.allSmallFullMatrix.append(smallFullMatrix)

                tmpCentroidArray = DistanceCalculations.calculateDistanceFromCentroid(polygonCentroidInUm, (self.tmpRandomSmall / (nmPixelRatio*1e3)))
                self.smallRandomCentroidDistance.append(tmpCentroidArray)

                tmpClosestEdgeArray = DistanceCalculations.getDistanceFromNearestEdge((self.tmpRandomSmall / (nmPixelRatio*1e3)), self.synapticAreaOutlinePointsInUm)
                self.smallRandomClosestEdgeDistance.append(tmpClosestEdgeArray)

                # mean values of the computed parameters into one vector
                self.randomNNDMean.append(np.mean(smallNND_matrix))
                self.randomAllDistanceMean.append(np.mean(smallFullMatrix))
                self.randomCentroidMean.append(np.mean(tmpCentroidArray))
                self.randomClosestEdgeMean.append(np.mean(tmpClosestEdgeArray))

                # possibility to perform spatial autocorrelation on random samples
                if(self.PerformSpatialAutocorrelationCheckBox.isChecked() == True):
                    rmax = int(np.around(nmPixelRatio * self.spatialRmaxSpinBox.value()))

                    tmp_g = []
                    self.ACF_radiusVec, tmp_g = Clustering.calculateSpatialAutocorrelationFunction(imgScaled, maskSize, self.tmpRandomSmall, rmax, nmPixelRatio, binSize, False, False, 0)

                    self.random_g_r.append(tmp_g)

                if(len(self.largeGoldParticleCoordinates) != 0):
                    self.generateRandomLargeData()
                    # calling the 2 previously defined function from module 'DistanceCalculations'
                    largeNND_matrix = DistanceCalculations.nearestNeighborDistanceCalculation(self.tmpRandomLarge / (nmPixelRatio*1e3))
                    largePercNND = DistanceCalculations.cumulativeProbDistributionCalculation(largeNND_matrix)
                    self.allLargePercNND.append(largePercNND)
                    self.allLargeNNDMatrix.append(largeNND_matrix)

                    largeFullMatrix = DistanceCalculations.getDistanceMatrix() # this is only executable if previously the NND calculation was done
                    largePercFull = DistanceCalculations.cumulativeProbDistributionCalculation(largeFullMatrix)
                    self.allLargePercFull.append(largePercFull)
                    self.allLargeFullMatrix.append(largeFullMatrix)

                    tmpCentroidArray = DistanceCalculations.calculateDistanceFromCentroid(polygonCentroidInUm, (self.tmpRandomLarge / (nmPixelRatio*1e3)))
                    self.largeRandomCentroidDistance.append(tmpCentroidArray)

                if(self.saveRandomDataCheckBox.isChecked()):
                    if(len(self.largeGoldParticleCoordinates) == 0):
                        # if there are no large particles labelled, create empty lists to be able to do the visualization
                        largeNND_matrix = []
                        largePercNND = []
                        largeFullMatrix = []
                        largePercFull = []
                        # this has to be done for the visualization
                        self.tmpRandomLarge = []
                        p = QtCore.QPointF(0.0, 0.0)
                        np.append(self.tmpRandomLarge,p)
                        self.tmpRandomLarge = np.asarray(self.tmpRandomLarge)
                    # pixel to um conversion
                    DistanceCalculations.visualizeData(smallNND_matrix, smallPercNND, smallFullMatrix, smallPercFull, largeNND_matrix, largePercNND, largeFullMatrix, largePercFull, realPathInUm, (self.tmpRandomSmall / (nmPixelRatio*1e3)), (self.tmpRandomLarge / (nmPixelRatio*1e3)), pdf, (imgScaled.width() / (nmPixelRatio*1e3)), (imgScaled.height() / (nmPixelRatio*1e3)))
                if(i == 0):
                    print '-----'
                print i+1, '/', self.randomSampleSpinBox.value(), 'done'

        if(self.saveRandomDataCheckBox.isChecked() == False):
            os.remove(str(openedFilename[0:-4] + '_random.pdf'))

        # if spatial autocorrelation analysis performed on the random samples, save data
        if(self.PerformSpatialAutocorrelationCheckBox.isChecked() == True):

            # check if the 2D ACF is already calculated for the actual experimental data
            if(self.g_r == []):
                print '-----'
                print 'Please perform 2D autocorrelation calculation on actual experimental data first'
            else:
                pass

            # # calculate the radii values
            # radii = []
            # radius = binSize
            # while radius <= self.spatialRmaxSpinBox.value():
            #     radii.append(radius / nmPixelRatio)
            #     radius += binSize

            # calculating mean values of g(r) functions (for experimental and random data as well)
            randomMeanGr = []
            for i in range(0, len(self.random_g_r)):

                randomMeanGr.append(np.mean(self.random_g_r[i]))

            expMeanGr = np.mean(self.g_r)
            randomMeanGr = np.sort(np.asarray(randomMeanGr))

            grIndex = DistanceCalculations.getElementIndex(expMeanGr, randomMeanGr)

            # Creating the Excel workbook in which data will be saved
            workbookFilename = str(openedFilename[0:-4]) + '_2D_ACF.xlsx'
            workbook = xw.Workbook(workbookFilename)

            self.ACF_radiusVec = self.ACF_radiusVec.tolist()

            ExcelSave.saveDataInExcel_2D_ACF(workbook, self.ACF_radiusVec, self.g_r, self.random_g_r, expMeanGr, randomMeanGr, grIndex)
            workbook.close()

            print '-----'
            print 'Random 2D ACF data is saved at:', workbookFilename

        self.saveData(self.allSmallNNDMatrix, self.allSmallFullMatrix, self.allLargeNNDMatrix, self.allLargeFullMatrix)

        print '-----'
        print 'N = %0.0f random data sets were generated in %0.3f seconds' % (self.randomSampleSpinBox.value(), float(time.time() - start_time))

        if(os.path.isfile(openedFilename[0:-4] + '_random.pdf')):
            print '-----'
            print 'PDF with random data is saved at ' + openedFilename[0:-4] + '_random.pdf'

    # save generated random data in Excel
    def saveData(self, allSmallNNDMatrix, allSmallFullMatrix, allLargeNNDMatrix, allLargeFullMatrix):

        # Creating the Excel workbook in which data will be saved
        workbookFilename = str(openedFilename[0:-4]) + '_distance_measurements.xlsx'
        workbook = xw.Workbook(workbookFilename)

        # save data in excel file
        ExcelSave.saveDataInExcel(workbook, 'Small - NND', self.randomSampleSpinBox.value(), self.expSmallNNDMatrix, self.allSmallNNDMatrix, AZarea) #, smallNND_pValue, p005_counter, p001_counter)

        # save data in excel file
        ExcelSave.saveDataInExcel(workbook, 'Small - All', self.randomSampleSpinBox.value(), self.expSmallFullMatrix, self.allSmallFullMatrix, AZarea) #, smallAll_pValue, p005_counter, p001_counter)

        # save data in excel file
        ExcelSave.saveDataInExcel(workbook, 'Small - Centroid', self.randomSampleSpinBox.value(), self.smallCentroidDistance, self.smallRandomCentroidDistance, AZarea) #, centroid_pValue, p005_counter, p001_counter)

        # save data in excel file
        ExcelSave.saveDataInExcel(workbook, 'Small - Nearest edge', self.randomSampleSpinBox.value(), self.smallClosestEdgeDistance, self.smallRandomClosestEdgeDistance, AZarea) #, nearestEdge_pValue, p005_counter, p001_counter)

        # Calculating median values from all pooled randomly generated datasets
        randomNNDMedian = np.median(np.resize(np.asarray(self.allSmallNNDMatrix), (len(self.allSmallNNDMatrix), len(self.allSmallNNDMatrix[0]))))
        randomAllDistanceMedian = np.median(np.resize(np.asarray(self.allSmallFullMatrix), (len(self.allSmallFullMatrix), len(self.allSmallFullMatrix[0]))))
        randomCendtroidMedian = np.median(np.resize(np.asarray(self.smallRandomCentroidDistance), (len(self.smallRandomCentroidDistance), len(self.smallRandomCentroidDistance[0]))))
        randomClosestEdgeMedian = np.median(np.resize(np.asarray(self.smallRandomClosestEdgeDistance), (len(self.smallRandomClosestEdgeDistance), len(self.smallRandomClosestEdgeDistance[0]))))

        # sorting the arrays and saving mean values of calculated parameters into a different worksheet
        self.randomNNDMean = np.sort(self.randomNNDMean)
        self.randomAllDistanceMean = np.sort(self.randomAllDistanceMean)
        self.randomCentroidMean = np.sort(self.randomCentroidMean)
        self.randomClosestEdgeMean = np.sort(self.randomClosestEdgeMean)

        # get index of the array, where the actual mean is just smaller than the next element in the array
        NNDIndex = DistanceCalculations.getElementIndex(np.mean(self.expSmallNNDMatrix), self.randomNNDMean)
        AllDistanceIndex = DistanceCalculations.getElementIndex(np.mean(self.expSmallFullMatrix), self.randomAllDistanceMean)
        CentroidIndex = DistanceCalculations.getElementIndex(np.mean(self.smallCentroidDistance), self.randomCentroidMean)
        ClosestEdgeIndex = DistanceCalculations.getElementIndex(np.mean(self.smallClosestEdgeDistance), self.randomClosestEdgeMean)

        # save distance calculation summary into Excel as well
        ExcelSave.saveDataInExcel_distanceSummary(workbook, self.expSmallNNDMatrix, self.expSmallFullMatrix, self.smallCentroidDistance, self.smallClosestEdgeDistance, self.randomNNDMean, self.randomAllDistanceMean, self.randomCentroidMean, self.randomClosestEdgeMean, NNDIndex, AllDistanceIndex, CentroidIndex, ClosestEdgeIndex, randomNNDMedian, randomAllDistanceMedian, randomCendtroidMedian, randomClosestEdgeMedian, [])

        workbook.close()
        print '-----'
        print 'Distance measurements data is saved at ', str(openedFilename[0:-4]) + '_distance_measurements.xlsx'

    def performSpatialAutocorrelation(self):

        # calculate mask size, which is the smallest rectangle that contains the synaptic AZ
        maskSize = DistanceCalculations.getSynapticAreaOutlineBorders(self.synapticAreaOutlinePoints)

        global binSize
        binSize = 1

        self.g_r = []

        rmax = int(np.around(nmPixelRatio * self.spatialRmaxSpinBox.value()))

        self.ACF_radiusVec, self.g_r = Clustering.calculateSpatialAutocorrelationFunction(imgScaled, maskSize, self.smallGoldParticleCoordinates, rmax, nmPixelRatio, binSize, True, self.SaveSpatialAutocorrelationCheckBox.isChecked(), 0)

        return self.g_r

    def performDBSCAN(self):
        if(len(self.smallGoldParticleCoordinates) < 1):
            print 'DBSCAN cannot be performed, not enough data points'
        else:
            epsilonInPixel = self.DBSCANEpsilonDoubleSpinBox.value() * nmPixelRatio

            # perform DBSCAN
            array, labels = Clustering.dbscanClustering(self.smallGoldParticleCoordinates, [], [], epsilonInPixel, self.DBSCANMinSampleDoubleSpinBox.value())

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
            filenameToSave = str(openedFilename[0:-4]) + '_DBSCAN_epsilon=' + str(int(self.DBSCANEpsilonDoubleSpinBox.value())) + 'nm_minSample=' + str(int(self.DBSCANMinSampleDoubleSpinBox.value())) + '.txt'
            np.savetxt(filenameToSave, dataMatrix, fmt='%0.0f')

    def performAffinityPropagation(self):
        array, labels = Clustering.affinityPropagationClustering(self.smallGoldParticleCoordinates, [], [], self.affinityPropagationDoubleSpinBox.value())

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
        filenameToSave = str(openedFilename[0:-4]) + '_affinity_propagation_pref=' + str(int(self.affinityPropagationDoubleSpinBox.value())) + '.txt'
        np.savetxt(filenameToSave, dataMatrix, fmt='%0.0f')

    def performMeanShift(self):
        array, labels = Clustering.meanShiftClustering(self.smallGoldParticleCoordinates, [], [], int(self.MeanShiftMinSampleDoubleSpinBox.value()))

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
        filenameToSave = str(openedFilename[0:-4]) + '_mean_shift_minSample=' + str(int(self.MeanShiftMinSampleDoubleSpinBox.value())) + '.txt'
        np.savetxt(filenameToSave, dataMatrix, fmt='%0.0f')

    # opening the clustering GUI
    def openClusteringWindowGui(self):
        self._new_window = GoldExtClusterGui()
        self._new_window.show()

# initializing the GUI itself
def initGUI():
    app = QtGui.QApplication(sys.argv)
    mainWindow = GoldExtMainGui()
    mainWindow.show()
    sys.exit(app.exec_())