# -*- coding: utf-8 -*-
#!/urs/bin/env python3

"""
Created on Jul 12, 2022

@author: Chiwai
"""
__author__ = 'Chiwai Lee'

import sys, os
sys.path.append ("..")
sys.path.append ("../..")
sys.path.append ("../../..")
sys.path.append (os.path.join (os.path.split (sys.argv[0])[0],".."))
#
import datetime as dt
import logging
import pandas as pd
import numpy as np
##from lib.pdlib import pdTimeStamp
from pytz import timezone


 
def pdTimeStamp (dtDate, iHour=0, iMinute=0, localtz = None):
    
    sDateString = dtDate.strftime ("%Y-%m-%d")
    sTimeString = f'{iHour:02d}:{iMinute:02d}'
    pdTS = pd.Timestamp (sDateString+'T'+sTimeString)
    
    if localtz is not None:
        pdTS = pdTS.tz_localize (timezone (localtz))
        
    return pdTS


#from numpy import log as ln
##
## https://stackoverflow.com/questions/32768555/find-the-set-of-column-indices-for-non-zero-values-in-each-row-in-pandas-data-f
##
def loadJPMAuctionTable (sFileName):

    pdAuctionTail = pd.read_csv (sFileName,
                                 parse_dates = ['Date'],
                                 index_col=['Date'])\
        .dropna(how='all').fillna(0)

    pdAuctionTail.columns = ['2Y Tail', '2Y BC',
                             '3Y Tail', '3Y BC',
                             '5Y Tail', '5Y BC',
                             '7Y Tail', '7Y BC',
                             '10Y Tail', '10Y BC',
                             '20Y Tail', '20Y BC',
                             '30Y Tail', '30Y BC',
                             ]
    pdBidCover = pdAuctionTail.iloc[:, [1,3,5,7,9,11,13]]
    pdBidCover.columns = ['2Y', '3Y', '5Y', '7Y', '10Y', '20Y', '30Y']

    lsCols = pdBidCover.columns
    pdBondSeries = pdBidCover.apply (lambda x: x > 0) \
        .apply (lambda x: list (lsCols[x.values]), axis=1)\
                            .to_frame ('bond_series')

    pdBondSeries['num_auctions'] = pdBondSeries.apply (lambda x: len (x['bond_series']),
                                                       axis=1)
    pdAuctionTail = pdBondSeries.join (pdAuctionTail)   

    pdAuctionTail = _amendData (pdAuctionTail)

    return pdAuctionTail



def loadJPMFullAuctionTable (sFileName):

    pdAuction = pd.read_csv (sFileName,
                             parse_dates = ['Date'],
                             index_col=['Date'])\
        .dropna(how='all').fillna(0)


    iColNums = [(1 + i * 14) for i in range (0, 7)]
    pdBidCover = pdAuction.iloc[:, iColNums]
    pdBidCover.columns = ['2Y', '3Y', '5Y', '7Y', '10Y', '20Y', '30Y']
    lsCols = pdBidCover.columns
    pdBondSeries = pdBidCover.apply (lambda x: x > 0) \
        .apply (lambda x: list (lsCols[x.values]), axis=1)\
                             .to_frame ('bond_series')

    pdBondSeries['num_auctions'] = pdBondSeries.apply (lambda x: len (x['bond_series']),
                                                       axis=1)
    pdAuction = pdBondSeries.join (pdAuction) 

    _changeColNames (pdAuction)
    _amendFullData (pdAuction)
    
    pdAuction = pdAuction.sort_index()

    return pdAuction



def _changeColNames (pdAuction):

    liMaturities = [2, 3, 5, 7, 10, 20, 30]

    dictNames1 = { 'Treasuries ' + str(i) + 'y Auction tail' : 
                   str(i) + 'Y Tail' for i in liMaturities}    
    dictNames2 = { 'Treasuries ' + str(i) + 'y Bid-to-cover ratio' :
                   str(i) + 'Y BC' for i in liMaturities}
    dictNames3 = { 'Treasuries ' + str(i) + 'y Indirect Bidders (%)' :
                   str(i) + 'Y Indirect' for i in liMaturities}    
    dictNames4 = { 'Treasuries ' + str(i) + 'y Direct Bidders (%)' :
                   str(i) + 'Y Direct' for i in liMaturities}
    dictNames5 = { 'Treasuries ' + str(i) + 'y Auction type (0=reopening)' :
                   str(i) + 'Y Reopening' for i in liMaturities}
    dictNames6 = { 'Treasuries ' + str(i) + 'y SOMA %age at auction' :
                   str(i) + 'Y SOMA' for i in liMaturities}    
    dictNames7 = { 'Treasuries ' + str(i) + 'y Dep. Institutions %age at auction' :
                   str(i) + 'Y DepInsts' for i in liMaturities}
    dictNames8 = { 'Treasuries ' + str(i) + 'y Individuals %age at auction' :
                   str(i) + 'Y Individuals' for i in liMaturities}
    dictNames9 = { 'Treasuries ' + str(i) + 'y Dealers %age at auction' :
                   str(i) + 'Y Dealers' for i in liMaturities}
    dictNames10 = { 'Treasuries ' + str(i) + 'y Pension funds %age at auction' :
                    str(i) + 'Y Pensions' for i in liMaturities}
    dictNames11 = { 'Treasuries ' + str(i) + 'y Investment funds %age at auction' :
                    str(i) + 'Y Investments' for i in liMaturities}     
    dictNames12 = { 'Treasuries ' + str(i) + 'y Foreign %age at auction' :
                    str(i) + 'Y Foreigns' for i in liMaturities}
    dictNames13 = { 'Treasuries ' + str(i) + 'y Auction size ($bn)' :
                    str(i) + 'Y AuctionSize' for i in liMaturities}
    dictNames14 = { 'Treasuries ' + str(i) + 'y Auction yield (%)' :
                    str(i) + 'Y AuctionYield' for i in liMaturities}       

    dictAll = {**dictNames1, **dictNames2, ** dictNames3, **dictNames4, **dictNames5, 
               **dictNames6, **dictNames7, ** dictNames8, **dictNames9, **dictNames10,
               **dictNames11, **dictNames12, ** dictNames13, **dictNames14 }
    pdAuction.rename (columns = dictAll, inplace = True)

    return



def _amendData (pdData):
    ##
    ## Update 7/25/22 data if 7/27/22 does not exist
    ##
    dtNewDate = dt.date (2022, 7, 27)
    tsIndexNew = pdTimeStamp (dtNewDate)

    if tsIndexNew not in pdData.index:

        dtDate = dt.date (2022, 7, 25)
        tsIndex = pdTimeStamp (dtDate)

        pdRowOld = pdData.loc[tsIndex,:]
        lsValues = ['2Y', '5Y']
        pdData.loc[[tsIndex], 'bond_series'] = pd.Series ([lsValues], index=[tsIndex]) 
        pdData.loc[tsIndex, 'num_auctions']= 2
        pdData.loc[tsIndex, ['7Y Tail', '7Y BC']] = np.array ([0, 0])        

        pdData.loc[tsIndexNew, :] = pdRowOld
        lsValues = ['7Y']
        pdData.loc[[tsIndexNew], 'bond_series'] = pd.Series ([lsValues], index=[tsIndexNew]) 
        pdData.loc[tsIndexNew, 'num_auctions']= 1
        pdData.loc[tsIndexNew, ['2Y Tail', '2Y BC', '5Y Tail', '5Y BC']] = np.array ([0, 0, 0, 0])

    return pdData



def _amendFullData (pdData):
    ##
    ## Update 7/25/22 data if 7/27/22 does not exist
    ##
    def _removeAuctionData (pdData, tsIndex, sStartLabel, sEndLabel):
        
        iStartIndex = pdData.columns.get_loc (sStartLabel)
        iEndIndex = pdData.columns.get_loc (sEndLabel)
        iSize = iEndIndex - iStartIndex + 1
        lsCols = pdData.columns[iStartIndex:(iEndIndex + 1)].tolist()
        pdData.loc[tsIndex, lsCols] = np.array ([0] * iSize)
        
        return pdData 
    
    dtNewDate = dt.date (2022, 7, 27)
    tsIndexNew = pdTimeStamp (dtNewDate)

    if tsIndexNew not in pdData.index:

        dtDate = dt.date (2022, 7, 25)
        tsIndex = pdTimeStamp (dtDate)
        pdRowOld = pdData.loc[tsIndex,:]
        ###
        ### Only 2Y and 5Y
        ###
        lsValues = ['2Y', '5Y']
        pdData.loc[[tsIndex], 'bond_series'] = pd.Series ([lsValues], index=[tsIndex]) 
        pdData.loc[tsIndex, 'num_auctions']= 2
        ###
        ### Remove 7Y data
        ###
        pdData = _removeAuctionData (pdData, tsIndex, '7Y Tail', '7Y AuctionYield')
        ###
        ### Only 7Y
        ###
        pdData.loc[tsIndexNew, :] = pdRowOld
        lsValues = ['7Y']
        pdData.loc[[tsIndexNew], 'bond_series'] = pd.Series ([lsValues], index=[tsIndexNew]) 
        pdData.loc[tsIndexNew, 'num_auctions']= 1
        ###
        ### Remove 2Y and 5Y data
        ###
        pdData = _removeAuctionData (pdData, tsIndexNew, '2Y Tail', '2Y AuctionYield')
        pdData = _removeAuctionData (pdData, tsIndexNew, '5Y Tail', '5Y AuctionYield')
     
    return pdData



def loadJPMAuctionTable_new (sFileName):
    ##
    ## Testing vectorized version, slower than above
    ##
    ## https://kanoki.org/2022/02/11/how-to-return-multiple-columns-using-pandas-apply/
    ##
    def _convertInfo (x, cols):

        a = list (cols[x.values])
        b = len (a)

        return pd.Series ([a, b])

    pdAuctionTail = pd.read_csv (sFileName,
                                 parse_dates = ['Date'],
                                 index_col=['Date'])\
        .dropna(how='all').fillna(0)

    pdBidCover = pdAuctionTail.iloc[:, [1,3,5,7,9,11,13]]
    pdBidCover.columns = ['2Y', '3Y', '5Y', '7Y', '10Y', '20Y', '30Y']
    lsCols = pdBidCover.columns
    pdTemp = pdBidCover.apply (lambda x: x > 0)
    pdBondSeries = pdTemp.apply (lambda x: _convertInfo (x, lsCols), axis=1)
    pdBondSeries.columns = ['bond_series', 'num_auctions']
    pdAuctionTail = pdBondSeries.join (pdAuctionTail)  

    return pdAuctionTail



def pdGetSingleAuction (pdAuctionTail, iTenor = 10):
    ##
    ## https://stackoverflow.com/questions/17071871/how-do-i-select-rows-from-a-dataframe-based-on-column-values
    ## https://stackoverflow.com/questions/41518920/python-pandas-how-to-query-if-a-list-type-column-contains-something
    ## https://stackoverflow.com/questions/32768555/find-the-set-of-column-indices-for-non-zero-values-in-each-row-in-pandas-data-f
    ##
    sTenor = str (iTenor) + 'Y'
    sCols = ['bond_series', 'num_auctions', sTenor + ' Tail', sTenor + ' BC']
    pdResults = pdAuctionTail[sCols].copy()
    mask = pdResults['bond_series'].apply (lambda x: sTenor in x)
    pdResults = pdResults[mask]

    return pdResults



def pdGetSingleAuction (pdAuctionTail, iTenor = 10):
    ##
    ## https://stackoverflow.com/questions/17071871/how-do-i-select-rows-from-a-dataframe-based-on-column-values
    ## https://stackoverflow.com/questions/41518920/python-pandas-how-to-query-if-a-list-type-column-contains-something
    ## https://stackoverflow.com/questions/32768555/find-the-set-of-column-indices-for-non-zero-values-in-each-row-in-pandas-data-f
    ##
    sTenor = str (iTenor) + 'Y'
    sCols = ['bond_series', 'num_auctions', sTenor + ' Tail', sTenor + ' BC']
    pdResults = pdAuctionTail[sCols].copy()
    ##
    ## Get rows with the auction results
    ##
    mask = pdResults['bond_series'].apply (lambda x: sTenor in x)
    pdResults = pdResults[mask]

    return pdResults



def pdGetOneAuctionResults (pdAuctionData, iTenor = 10):
    ##
    ## https://stackoverflow.com/questions/17071871/how-do-i-select-rows-from-a-dataframe-based-on-column-values
    ## https://stackoverflow.com/questions/41518920/python-pandas-how-to-query-if-a-list-type-column-contains-something
    ## https://stackoverflow.com/questions/32768555/find-the-set-of-column-indices-for-non-zero-values-in-each-row-in-pandas-data-f
    ##
    sTenor = str (iTenor) + 'Y'
    sStartLabel = sTenor + ' Tail'
    sEndLabel = sTenor + ' AuctionYield'
    
    iStartIndex = pdAuctionData.columns.get_loc (sStartLabel)
    iEndIndex = pdAuctionData.columns.get_loc (sEndLabel)
    #iSize = iEndIndex - iStartIndex + 1
    lsCols = pdAuctionData.columns[iStartIndex:(iEndIndex + 1)].tolist()
    
    sCols = ['bond_series', 'num_auctions'] + lsCols
    pdResults = pdAuctionData[sCols].copy()
    ##
    ## Get rows with the auction results
    ##
    mask = pdResults['bond_series'].apply (lambda x: sTenor in x)
    pdResults = pdResults[mask]

    return pdResults



def getDoubleAuctionTable (pdAuctionTail):

    pdDouble = pdAuctionTail[pdAuctionTail['num_auctions'] > 1]

    return pdDouble



def column_index (df, query_cols):

    cols = df.columns.values
    sidx = np.argsort(cols)

    return sidx[np.searchsorted (cols,query_cols,sorter=sidx)]



# if __name__ == '__main__' and __package__ is None:
if __name__ == '__main__':

    from os import sys, path
    sys.path.append (path.dirname (path.dirname (path.abspath (__file__))))

    """
    FORMAT = '%(asctime)-15s - %(name)s - %(levelname)s - %(message)s'
    logging.basicConfig (format=FORMAT,filename='C:\TEMP\logs\RatesModelsServer_{:%Y%m%d_%H_%M}.log'.format(dt.datetime.now()),filemode='w+',level=logging.DEBUG)
    logger = logging.getLogger()
    """        
    logger = logging.getLogger (__name__)

    if __debug__:
        print ('Debug ON')
    else:
        print ('Debug OFF')
        print = logger.debug

    logging.basicConfig (level=logging.DEBUG,
                         format='%(asctime)s %(levelname)-8s %(message)s',
                         datefmt='%a, %d %b %Y %H:%M:%S')
                            #filename='/temp/myapp.log',
                            #filemode='w')

    # todayDate = dt.datetime.today().date()
    dtToday = dt.date.today() 
    #dtToday = dt.date (2019, 1, 29)
    sToday =  dtToday.strftime ('%m/%d/%Y')

    logging.info (f"Uploading AuctionTail on {sToday}")

    #sFileName = "C:/dev/data/UST Auction data_20220926.csv"
    #pdAuctionTail = loadJPMAuctionTable (sFileName)
    #pd20YAuctionTail = pdGetSingleAuction (pdAuctionTail, 20)

    #sFileNameAll = "C:/dev/data/UST Auction All Data_20221012.csv"
    sFileNameAll = "UST Auction All Data_20230214.csv"

    pdAuctionData = loadJPMFullAuctionTable (sFileNameAll)
    pdAuctionData2 = pdGetOneAuctionResults (pdAuctionData, 2)
    pdAuctionData3 = pdGetOneAuctionResults (pdAuctionData, 3)
    pdAuctionData5 = pdGetOneAuctionResults (pdAuctionData, 5)
    pdAuctionData7 = pdGetOneAuctionResults (pdAuctionData, 7)
    pdAuctionData10 = pdGetOneAuctionResults (pdAuctionData, 10)
    pdAuctionData20 = pdGetOneAuctionResults (pdAuctionData, 20)
    pdAuctionData30 = pdGetOneAuctionResults (pdAuctionData, 30)

    logging.info ("Done")

