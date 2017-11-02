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

import xlsxwriter as xw
from xlsxwriter.utility import xl_rowcol_to_cell
import numpy as np
import MainGUI
import DistanceCalculations

def saveDataInExcel(workbook, worksheetTitle, randomN, expArray, nRandomArray, AZarea): #, pValue_array, p005Counter, p001Counter):
        worksheet = workbook.add_worksheet(worksheetTitle)
        worksheet.write(0, 0, 'AZ area (um2)')
        worksheet.write(1, 0, '%0.3f' % AZarea)
        for i in range(0, len(expArray) + 1):
            for j in range(1, randomN + 6):
                if(i == 0 and j == 1):
                    worksheet.write(i, j, 'experimental data')
                if(i == 0 and j > 1):
                    worksheet.write(i, j, 'random_' + str(j-1))
                if(i == 0 and j == randomN + 2):
                    worksheet.write(i, j, 'avg_random')
                if(i == 0 and j == randomN + 3):
                    worksheet.write(i, j, 'SD_random')
                if(i == 0 and j == randomN + 4):
                    worksheet.write(i, j, 'avg-2SD_random')
                if(i == 0 and j == randomN + 5):
                    worksheet.write(i, j, 'avg+2SD_random')
                if(j == 1 and i > 0):
                    worksheet.write(i, j, expArray[i - 1])
                if(j > 1 and j < randomN + 2 and i > 0):
                    worksheet.write(i, j, nRandomArray[j - 2][i - 1])
                if(j == randomN + 2 and i > 0):
                    cellStart = xl_rowcol_to_cell(i, 2) # converts the zero indexed row and column cell reference to a A1 style string
                    cellEnd = xl_rowcol_to_cell(i, randomN + 1)
                    worksheet.write(i, j, '=AVERAGE({!s} : {!s})'.format(cellStart, cellEnd))
                if(j == randomN + 3 and i > 0):
                    worksheet.write(i, j, '=STDEV({!s} : {!s})'.format(cellStart, cellEnd))
                if(j == randomN + 4 and i > 0):
                    cellStart = xl_rowcol_to_cell(i, randomN + 2) # converts the zero indexed row and column cell reference to a A1 style string
                    cellEnd = xl_rowcol_to_cell(i, randomN + 3)
                    worksheet.write(i, j, '=({!s} - 2*{!s})'.format(cellStart, cellEnd))
                if(j == randomN + 5 and i > 0):
                    worksheet.write(i, j, '=({!s} + 2*{!s})'.format(cellStart, cellEnd))


        #i = len(expArray) + 3
        #for j in range(0, randomN + 2):
        #    if(j == 0):
        #        worksheet.write(i, j, 'p-value')
        #    if(j == 1):
        #        worksheet.write(i, j, '-')
        #    if(j > 1):
        #        worksheet.write(i, j, pValue_array[j - 2])

        for i in range(len(expArray) + 5, len(expArray) + 10):
            for j in range(1, randomN + 2):
                cellStart = xl_rowcol_to_cell(1, j) # converts the zero indexed row and column cell reference to a A1 style string
                cellEnd = xl_rowcol_to_cell((len(expArray)), j)

                if(i == len(expArray) + 5):
                    worksheet.write(i, j, '=AVERAGE({!s} : {!s})'.format(cellStart, cellEnd))
                if(i == len(expArray) + 6):
                    worksheet.write(i, j, '=MEDIAN({!s} : {!s})'.format(cellStart, cellEnd))
                if(i == len(expArray) + 7):
                    worksheet.write(i, j, '=STDEV({!s} : {!s})'.format(cellStart, cellEnd))
                if(i == len(expArray) + 8):
                    worksheet.write(i, j, '=QUARTILE.INC({!s} : {!s}, 1)'.format(cellStart, cellEnd))
                if(i == len(expArray) + 9):
                    worksheet.write(i, j, '=QUARTILE.INC({!s} : {!s}, 3)'.format(cellStart, cellEnd))

        for i in range(len(expArray) + 5, len(expArray) + 10):
            if(i == len(expArray) + 5):
                worksheet.write(i, 0, 'Mean')
            if(i == len(expArray) + 6):
                worksheet.write(i, 0, 'Median')
            if(i == len(expArray) + 7):
                worksheet.write(i, 0, 'SD')
            if(i == len(expArray) + 8):
                worksheet.write(i, 0, 'Q1')
            if(i == len(expArray) + 9):
                worksheet.write(i, 0, 'Q3')

        # summary stats on how many of the random distributions are significantly different from the experimental data for the 2 given significance values
        #worksheet.write(len(expArray) + 12, 1, '/{!s}'.format(randomN))
        #worksheet.write(len(expArray) + 13, 0, 'p < 0.05')
        #worksheet.write(len(expArray) + 14, 0, 'p < 0.01')
        #worksheet.write(len(expArray) + 13, 1, p005Counter)
        #worksheet.write(len(expArray) + 14, 1, p001Counter)

# write the summary data of distance measurements into a different worksheet of Excel workbook
def saveDataInExcel_distanceSummary(workbook, expSmallNNDMatrix, expSmallFullMatrix, smallCentroidDistance, smallClosestEdgeDistance, randomNNDMean, randomAllDistanceMean, randomCentroidMean, randomClosestEdgeMean, NNDIndex, AllDistanceIndex, CentroidIndex, ClosestEdgeIndex, randomNNDMedian, randomAllDistanceMedian, randomCendtroidMedian, randomClosestEdgeMedian, areaVec):
    worksheet = workbook.add_worksheet('Mean values')
    for i in range(0, len(randomNNDMean) + 1):
        for j in range(0, 14):

            # mean values of the randomly generated data
            if(i == 0 and j == 0):
                worksheet.write(i, j, 'Random mean NND')
            if(i == 0 and j == 1):
                worksheet.write(i, j, 'Random mean all distance')
            if(i == 0 and j == 2):
                worksheet.write(i, j, 'Random mean centroid')
            if(i == 0 and j == 3):
                worksheet.write(i, j, 'Random mean closest edge')
            if(j == 0 and i > 0):
                worksheet.write(i, j, randomNNDMean[i - 1])
            if(j == 1 and i > 0):
                worksheet.write(i, j, randomAllDistanceMean[i - 1])
            if(j == 2 and i > 0):
                worksheet.write(i, j, randomCentroidMean[i - 1])
            if(j == 3 and i > 0):
                worksheet.write(i, j, randomClosestEdgeMean[i - 1])

            # mean of mean values of the randomly generated data
            if(i == 0 and j == 5):
                worksheet.write(i, j, 'Mean NND')
            if(i == 0 and j == 6):
                worksheet.write(i, j, 'Mean all distance')
            if(i == 0 and j == 7):
                worksheet.write(i, j, 'Mean centroid')
            if(i == 0 and j == 8):
                worksheet.write(i, j, 'Mean closest edge')

            if(j >= 5 and j < 9):
                cellStart = xl_rowcol_to_cell(1, j-5) # converts the zero indexed row and column cell reference to a A1 style string
                cellEnd = xl_rowcol_to_cell((len(randomNNDMean)), j-5)

            if(j == 5 and i == 1):
                worksheet.write(i, j, '=AVERAGE({!s} : {!s})'.format(cellStart, cellEnd))
            if(j == 6 and i == 1):
                worksheet.write(i, j, '=AVERAGE({!s} : {!s})'.format(cellStart, cellEnd))
            if(j == 7 and i == 1):
                worksheet.write(i, j, '=AVERAGE({!s} : {!s})'.format(cellStart, cellEnd))
            if(j == 8 and i == 1):
                worksheet.write(i, j, '=AVERAGE({!s} : {!s})'.format(cellStart, cellEnd))

            # median values of the randomly generated data
            if(i == 5 and j == 5):
                worksheet.write(i, j, 'Median NND')
            if(i == 5 and j == 6):
                worksheet.write(i, j, 'Median all distance')
            if(i == 5 and j == 7):
                worksheet.write(i, j, 'Median centroid')
            if(i == 5 and j == 8):
                worksheet.write(i, j, 'Median closest edge')

            if(j == 5 and i == 6):
                worksheet.write(i, j, randomNNDMedian)
            if(j == 6 and i == 6):
                worksheet.write(i, j, randomAllDistanceMedian)
            if(j == 7 and i == 6):
                worksheet.write(i, j, randomCendtroidMedian)
            if(j == 8 and i == 6):
                worksheet.write(i, j, randomClosestEdgeMedian)

            # mean values of the experimental data
            if(i == 0 and j == 10):
                worksheet.write(i, j, 'Exp mean NND')
            if(i == 0 and j == 11):
                worksheet.write(i, j, 'Exp mean all distance')
            if(i == 0 and j == 12):
                worksheet.write(i, j, 'Exp mean centroid')
            if(i == 0 and j == 13):
                worksheet.write(i, j, 'Exp mean closest edge')
            if(j == 10 and i == 1):
                worksheet.write(i, j, np.mean(expSmallNNDMatrix))
            if(j == 11 and i == 1):
                worksheet.write(i, j, np.mean(expSmallFullMatrix))
            if(j == 12 and i == 1):
                worksheet.write(i, j, np.mean(smallCentroidDistance))
            if(j == 13 and i == 1):
                worksheet.write(i, j, np.mean(smallClosestEdgeDistance))
            if(j == 9 and i == 3):
                worksheet.write(i, j, '1st index bigger')
            if(j == 10 and i == 3):
                worksheet.write(i, j, NNDIndex)
            if(j == 11 and i == 3):
                worksheet.write(i, j, AllDistanceIndex)
            if(j == 12 and i == 3):
                worksheet.write(i, j, CentroidIndex)
            if(j == 13 and i == 3):
                worksheet.write(i, j, ClosestEdgeIndex)

            # median values of the experimental data
            if(i == 5 and j == 10):
                worksheet.write(i, j, 'Exp median NND')
            if(i == 5 and j == 11):
                worksheet.write(i, j, 'Exp median all distance')
            if(i == 5 and j == 12):
                worksheet.write(i, j, 'Exp median centroid')
            if(i == 5 and j == 13):
                worksheet.write(i, j, 'Exp median closest edge')
            if(j == 10 and i == 6):
                worksheet.write(i, j, np.median(expSmallNNDMatrix))
            if(j == 11 and i == 6):
                worksheet.write(i, j, np.median(expSmallFullMatrix))
            if(j == 12 and i == 6):
                worksheet.write(i, j, np.median(smallCentroidDistance))
            if(j == 13 and i == 6):
                worksheet.write(i, j, np.median(smallClosestEdgeDistance))

    # print polygon area data into the summary sheet as well
    worksheet.write(8, 5, 'AZ (um2)')
    worksheet.write(8, 6, 'P1 (um2)')
    worksheet.write(8, 7, 'P2 (um2)')
    worksheet.write(8, 8, 'P3 (um2)')
    worksheet.write(8, 9, 'SUM (um2)')

    if(areaVec != []):
        worksheet.write(9, 5, areaVec[0])
        if(len(areaVec) == 1):
            worksheet.write(9, 6, 0)
            worksheet.write(9, 7, 0)
            worksheet.write(9, 8, 0)
        if(len(areaVec) == 2):
            worksheet.write(9, 6, areaVec[1])
            worksheet.write(9, 7, 0)
            worksheet.write(9, 8, 0)
        if(len(areaVec) == 3):
            worksheet.write(9, 6, areaVec[1])
            worksheet.write(9, 7, areaVec[2])
            worksheet.write(9, 8, 0)
        if(len(areaVec) == 4):
            worksheet.write(9, 6, areaVec[1])
            worksheet.write(9, 7, areaVec[2])
            worksheet.write(9, 8, areaVec[3])

        cellStart = xl_rowcol_to_cell(9, 6) # converts the zero indexed row and column cell reference to a A1 style string
        cellEnd = xl_rowcol_to_cell(9, 8)
        worksheet.write(9, 9, '=SUM({!s} : {!s})'.format(cellStart, cellEnd))

# save 2D ACF data into an Excel file
def saveDataInExcel_2D_ACF(workbook, radii, g_r, random_g_r, expMeanGr, randomMeanGr, grIndex):
    # experimental and random raw data
    worksheet = workbook.add_worksheet('2D ACF raw data')
    for i in range(0, len(g_r) + 1):
        for j in range(0, len(randomMeanGr) + 2):
            if(i == 0 and j == 0):
                worksheet.write(i, j, 'radius (nm)')
            if(i == 0 and j == 1):
                worksheet.write(i, j, 'experimental data')
            if(i == 0 and j > 1):
                worksheet.write(i, j, 'random_' + str(j-1))
            if(i > 0 and j == 0):
                worksheet.write(i, j, radii[i-1])
            if(i > 0 and j == 1):
                worksheet.write(i, j, g_r[i-1])
            if(i > 0 and j > 1):
                worksheet.write(i, j, random_g_r[j-2][i-1])

    # experimental and random summary
    worksheet = workbook.add_worksheet('2D ACF summary')
    for i in range(0, len(randomMeanGr) + 1):
        if(i == 0):
            worksheet.write(i, 0, 'random mean')
        if(i > 0):
            worksheet.write(i, 0, randomMeanGr[i-1])

    # median value calculation for experimental and random data
    randomMedianGr = np.median(np.resize(np.asarray(random_g_r), (len(random_g_r), len(random_g_r[0]))))
    expMedian = np.median(g_r)

    cellStart = xl_rowcol_to_cell(1, 0) # converts the zero indexed row and column cell reference to a A1 style string
    cellEnd = xl_rowcol_to_cell((len(randomMeanGr)), 0)


    worksheet.write(0, 2, 'mean random mean')
    worksheet.write(1, 2, '=AVERAGE({!s} : {!s})'.format(cellStart, cellEnd))

    worksheet.write(5, 2, 'random median')
    worksheet.write(6, 2, randomMedianGr)

    worksheet.write(0, 4, 'experimental mean')
    worksheet.write(1, 4, expMeanGr)
    worksheet.write(3, 4, grIndex)
    worksheet.write(3, 3, '1st index bigger')

    worksheet.write(5, 4, 'experimental median')
    worksheet.write(6, 4, expMedian)

# save modified Ripley's K data into an Excel file
def saveDataInExcel_Ripley(workbook, radii, L_est, random_L_est):
    # experimental and random raw data
    worksheet = workbook.add_worksheet('Ripley raw data')
    for i in range(0, len(L_est) + 1):
        for j in range(0, len(random_L_est) + 2):
            if(i == 0 and j == 0):
                worksheet.write(i, j, 'radius (nm)')
            if(i == 0 and j == 1):
                worksheet.write(i, j, 'experimental data')
            if(i == 0 and j > 1):
                worksheet.write(i, j, 'random_' + str(j-1))
            if(i > 0 and j == 0):
                worksheet.write(i, j, radii[i-1])
            if(i > 0 and j == 1):
                worksheet.write(i, j, L_est[i-1])
            if(i > 0 and j > 1):
                worksheet.write(i, j, random_L_est[j-2][i-1])

# save empty circle data into an Excel file
def saveDataInExcel_emptyCirle(workbook, emptyCircleMatrix, cumulativePercentageMatrix):

    # experimental and random raw data
    worksheet = workbook.add_worksheet('Empty circles, r in nm')

    # since circle containing arrays could have different length, find the longest
    tmpLengthVec = []
    for i in range(0, len(emptyCircleMatrix)):
        tmpLengthVec.append(len(emptyCircleMatrix[i]))

    maxLength = max(tmpLengthVec)

    tmpDataMatrix = []
    for i in range(0, len(emptyCircleMatrix)):
        tmpDataVec = []
        for j in range(1, 6):
            if(len(emptyCircleMatrix[i]) < j):
                pass
            else:
                tmpDataVec.append(emptyCircleMatrix[i][-j])
        tmpDataMatrix.append(tmpDataVec)

    emptyCircleRadiusAverageVec = []
    emptyCircleRadiusSumVec = []
    emptyCircleRadiusSumPerNumberVec = []
    for i in range(0, len(tmpDataMatrix)):
        if(i == 0):
            average = np.average(np.asarray(tmpDataMatrix[i]))
            sum = np.sum(np.asarray(tmpDataMatrix[i]))
            sumPerNumber = np.sum(np.asarray(tmpDataMatrix[i]))/len(emptyCircleMatrix[i])
        else:
            emptyCircleRadiusAverageVec.append(np.average(np.asarray(tmpDataMatrix[i])))
            emptyCircleRadiusSumVec.append(np.sum(np.asarray(tmpDataMatrix[i])))
            emptyCircleRadiusSumPerNumberVec.append(np.sum(np.asarray(tmpDataMatrix[i]))/len(emptyCircleMatrix[i]))

    # 0 index column contains experimental data
    averageIndex = DistanceCalculations.getElementIndex(average, np.sort(np.asarray(emptyCircleRadiusAverageVec)))
    sumIndex = DistanceCalculations.getElementIndex(sum, np.sort(np.asarray(emptyCircleRadiusSumVec)))
    sumPerNumberIndex = DistanceCalculations.getElementIndex(sumPerNumber, np.sort(np.asarray(emptyCircleRadiusSumPerNumberVec)))

    for i in range(0, maxLength + 1):
        for j in range(0, len(emptyCircleMatrix)):
            if(i == 0 and j == 0):
                worksheet.write(i, j, 'experimental data')
            if(i == 0 and j > 0):
                worksheet.write(i, j, 'random_' + str(j))
            if(i > 0 and j >= 0):
                if(i > len(emptyCircleMatrix[j])):
                    worksheet.write(i, j, '-')
                else:
                    worksheet.write(i, j, emptyCircleMatrix[j][i-1])

    # summary of the generated circles
    worksheet = workbook.add_worksheet('Summary')
    for i in range(0, 6): # to have the circle radius of the 5 largest empty circles drawn in the AZ
        for j in range(0, len(emptyCircleMatrix)):
            if(i == 0 and j == 0):
                worksheet.write(i, j, 'experimental data')
            if (i == 0 and j > 0):
                worksheet.write(i, j, 'random_' + str(j))
            if(i > 0 and j >= 0):
                if(len(emptyCircleMatrix[j]) < i):
                    worksheet.write(i, j, '-')
                else:
                    worksheet.write(i, j, emptyCircleMatrix[j][-i])

        for j in range(0, len(emptyCircleMatrix)):
            cellStart = xl_rowcol_to_cell(1, j)  # converts the zero indexed row and column cell reference to a A1 style string
            cellEnd = xl_rowcol_to_cell(5, j)

            worksheet.write(7, j, '=AVERAGE({!s} : {!s})'.format(cellStart, cellEnd))
            worksheet.write(8, j, '=STDEV({!s} : {!s})'.format(cellStart, cellEnd))
            worksheet.write(10, j, '=SUM({!s} : {!s})'.format(cellStart, cellEnd))

            if(j == 0):
                worksheet.write(12, j, sumPerNumber)
            else:
                worksheet.write(12, j, (emptyCircleRadiusSumVec[j-1] / len(emptyCircleMatrix[j])))

    worksheet.write(0, len(emptyCircleMatrix) + 2, 'Average')
    worksheet.write(0, len(emptyCircleMatrix) + 3, 'Sum')
    worksheet.write(0, len(emptyCircleMatrix) + 4, 'Sum / circle number')
    worksheet.write(1, len(emptyCircleMatrix) + 1, '1st index bigger')
    worksheet.write(1, len(emptyCircleMatrix) + 2, averageIndex)
    worksheet.write(1, len(emptyCircleMatrix) + 3, sumIndex)
    worksheet.write(1, len(emptyCircleMatrix) + 4, sumPerNumberIndex)

    # cumulative probabilities
    worksheet = workbook.add_worksheet('Cumulative probabilities')

    for i in range(0, maxLength + 1):
        for j in range(0, len(cumulativePercentageMatrix)):
            if(i == 0 and j == 0):
                worksheet.write(i, j, 'experimental data')
            if(i == 0 and j > 0):
                worksheet.write(i, j, 'random_' + str(j))
            if(i > 0 and j >= 0):
                if(i > len(cumulativePercentageMatrix[j])):
                    worksheet.write(i, j, '-')
                else:
                    worksheet.write(i, j, cumulativePercentageMatrix[j][i-1])