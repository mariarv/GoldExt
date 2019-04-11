#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 21:37:29 2019

@author: maria
"""

from PyQt5 import QtCore, QtWidgets, uic, QtGui
import MainGUI
import GenerateArtificialData
import matplotlib.path as mPath
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
import xlsxwriter as xw
from xlsxwriter.utility import xl_rowcol_to_cell
import random
import bivar_rip
import pdb
import pyqtgraph as pg
# defining the GUI drawn in Qt Desinger
qtGoldExtClusterGui = './GoldExt_Bivar.ui'

Ui_MainWindow, QtBaseClass = uic.loadUiType(qtGoldExtClusterGui)


class GoldExtBivar(QtWidgets.QMainWindow, Ui_MainWindow):

    def __init__(self,smallGoldParticleCoordinates,largeGoldParticleCoordinates,synapticAreaOutlinePoints,nmPixelRatio):
        QtWidgets.QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)
        
        self.smallGoldParticleCoordinates=smallGoldParticleCoordinates
        self.largeGoldParticleCoordinates=largeGoldParticleCoordinates
        self.synapticAreaOutlinePoints=synapticAreaOutlinePoints
        self.nmPixelRatio=nmPixelRatio
        #self.comboBox = QtWidgets.QComboBox(self)
        self.comboBox.addItem("Small GP vs Large GP")
        self.comboBox.addItem("Large GP vs Small GP")
                
        self.pushButton.clicked.connect(self.RipFun)
        #self.graphicsView=pg.PlotWidget(self.centralwidget)
        self.graphicsView.setLabel('bottom', 'r', units = "nm")
        self.graphicsView.setLabel('left', 'L_biv(r)-r')  
        
        self.lineEdit_4.setReadOnly(True)
        self.lineEdit_5.setMaxLength(5)
        
        #self.buttonMADtest(self.MADtest)

        #self.dataplot = self.graphicsView.addPlot()
        
    def RipFun(self):
        
        self.graphicsView.clear()
        
        temp_small=[]
        smallGParticleCoord=np.empty((0))
        for i in range(0, len(self.smallGoldParticleCoordinates)):
            temp_small.append((self.smallGoldParticleCoordinates[i].x() / (self.nmPixelRatio*1e3), self.smallGoldParticleCoordinates[i].y() / (self.nmPixelRatio*1e3)))
        smallGParticleCoord=np.array(temp_small)
        smallGParticleCoord=smallGParticleCoord*1e3
        
        temp_large=[]
        largeGParticleCoord=np.empty((0))
        for i in range(0, len(self.largeGoldParticleCoordinates)):
            temp_large.append((self.largeGoldParticleCoordinates[i].x() / (self.nmPixelRatio*1e3), self.largeGoldParticleCoordinates[i].y() / (self.nmPixelRatio*1e3)))
        largeGParticleCoord=np.array(temp_large)
        largeGParticleCoord=largeGParticleCoord*1e3
        
        temp_syn=[]
        syn_bord=np.empty((0))
        for i in range(0, len(self.synapticAreaOutlinePoints) - 1):
            temp_syn.append((self.synapticAreaOutlinePoints[i].x() / (self.nmPixelRatio*1e3), self.synapticAreaOutlinePoints[i].y() / (self.nmPixelRatio*1e3)))
        syn_bord=np.array(temp_syn)
        syn_bord=syn_bord*1e3
        
        
        dist_max= self.SpinBoxRadius.value()
        dist_step= self.SpinBoxSpatStep.value()
        sims=self.spinBoxSims.value()
        ce= self.spinBoxSims_level.value()
        
        dist=np.arange(0,dist_max,dist_step)
        
        

        area=bivar_rip.PolyArea(syn_bord[:,0], syn_bord[:,1])
        
        if self.comboBox.currentIndex() >0:
            (L,L_upper,L_lower,L_all,L_m)=bivar_rip.k_function_sim_bivar(largeGParticleCoord,smallGParticleCoord,area,dist,sims,syn_bord[:,0],syn_bord[:,1],ce)
            (H0,p_val)=bivar_rip.MAD_test(L,L_all,ce)
            self.lineEdit_4.setText(str(H0))
            self.lineEdit_5.setText(str(p_val))
        else:
            (L,L_upper,L_lower,L_all,L_m)=bivar_rip.k_function_sim_bivar(smallGParticleCoord,largeGParticleCoord,area,dist,sims,syn_bord[:,0],syn_bord[:,1],ce)
            (H0,p_val)=bivar_rip.MAD_test(L,L_all,ce)
            self.lineEdit_4.setText(str(H0))
            self.lineEdit_5.setText(str(p_val))


        #pdb.set_trace()
        pen1=pg.mkPen(color='k',width=3.0)
        pen12=pg.mkPen(color='c',width=3.0)

        pen2=pg.mkPen(color=(100,0,100,100),width=1.0)
        plt2=self.graphicsView.plot(dist,L_lower,pen=pen2)
        plt1=self.graphicsView.plot(dist,L_upper,pen=pen2)
        
    
        brush_fill = (100,0,100,100)
        fill = pg.FillBetweenItem(plt1, plt2, brush=brush_fill)
        #fill1 = pg.FillBetweenItem(plt2, plt1, brush=brush_fill)

        self.graphicsView.addItem(fill)
        #self.graphicsView.addItem(fill)
        '''       
        fig = self.graphicsView.addPlot()
        plt1=fig.plot(dist,L_lower,pen=pen2)
        plt2=fig.graphicsView.plot(dist,L_upper,pen=pen2)
    
     
        brush_fill = (100,0,100,100)
        fill = pg.FillBetweenItem(plt1, plt2, brush=brush_fill)
        fill1 = pg.FillBetweenItem(plt2, plt1, brush=brush_fill)
        
        fig.addItem(fill1)
        fig.addItem(fill)
        '''
        self.graphicsView.addLegend(size=None, offset=(300, 20))

        self.graphicsView.showGrid(x=True, y=True)
        self.graphicsView.plot(dist,L, pen=pen12, name='Data')
        self.graphicsView.plot(dist,L_m, pen=pen1, name='Emperical Random')
        






        
       
