# -*- coding: utf-8 -*-
#!/urs/bin/env python3

"""
Created on Oct 30, 2022

@author: Chiwai
"""
__author__ = 'Chiwai Lee'

import sys, os
sys.path.append ("..")
sys.path.append ("../..")
sys.path.append ("../../..")
sys.path.append (os.path.join (os.path.split (sys.argv[0])[0],".."))
#from env.global_settings import sHomePythonCodes
#sys.path.append (sHomePythonCodes)

import datetime as dt
import logging
import QuantLib as ql
#from numpy import log as ln


def qlQDate (dtDate):
    
    if isinstance (dtDate, (dt.date, dt.datetime)):
        qDate = ql.Date (dtDate.day, dtDate.month, dtDate.year)
    else:
        qDate = dtDate
        
    return qDate



def _dtDate (qlDate):
    
    if isinstance (qlDate, dt.date):
        return qlDate
    
    if isinstance (qlDate, dt.datetime):
        dtDate = qlDate.date()
    else:
        
        try:
            dtDate = dt.date (qlDate.year(),
                              qlDate.month(),
                              qlDate.dayOfMonth())
        except:
            dtDate = None 
        
    return dtDate



def _toPyDate (qlDate):
    
    try:
        dtDate = dt.date (qlDate.year(),
                          qlDate.month(),
                          qlDate.dayOfMonth())
    except:
        dtDate = None 
        
    return dtDate



def _getQLCalendar (sCalendar = 'UST'):
    
    qlDefaultCalendar = ql.UnitedStates (ql.UnitedStates.GovernmentBond)
    
    dictResults = { 'USE' : ql.UnitedStates (ql.UnitedStates.NYSE),
                    'UST' : qlDefaultCalendar,
                    'EUR' : ql.Germany (ql.Germany.Eurex),
                    'GBP' : ql.UnitedKingdom (ql.UnitedKingdom.Settlement),
                    }
    
    qlCalendar = dictResults.get (sCalendar, qlDefaultCalendar)
    """
    How to use dictionary instead of nested if-then-else
    
    if sCalendar == 'USE':
        qlCalendar = ql.UnitedStates (ql.UnitedStates.NYSE)
    else:
        ##
        ## UST trading calendar
        ##
        qlCalendar = ql.UnitedStates (ql.UnitedStates.GovernmentBond)
    """
    return qlCalendar 



def qlIsBusDay (dtDate, sCalendar = 'UST'):
    
    qlDate = qlQDate (dtDate)
    qlCalendar = _getQLCalendar (sCalendar)
    
    return qlCalendar.isBusinessDay (qlDate)



def qlAdjToBusDay (dtDate, sCalendar = 'UST'):
    ##
    ## Adjust to next business day if dtDate is not a regular business day
    ##
    if not qlIsBusDay (dtDate):
        dtDate = qlAddBusDays (dtDate, 1, sCalendar)
    
    return dtDate



def qlIsEndOfMonth (dtDate, sCalendar = 'UST'):
    
    qlDate = qlQDate (dtDate)
    qlCalendar = _getQLCalendar (sCalendar)
    
    return qlCalendar.isEndOfMonth (qlDate)    



def qlGetEndOfMonth (dtDate, sCalendar = 'UST'):

    qlDate = qlQDate (dtDate)
    qlCalendar = _getQLCalendar (sCalendar)    
    qlEOMDate = qlCalendar.endOfMonth (qlDate)    
    dtDate = _toPyDate (qlEOMDate)
    
    return dtDate
    
    

def qlAddBusDays (dtDate, iNumOfBusDays = 1, sCalendar = 'UST'):
    
    qlDate = qlQDate (dtDate)
    iPeriod = ql.Period (iNumOfBusDays, ql.Days)
    qlCalendar = _getQLCalendar (sCalendar)  
    qlNewDate = qlCalendar.advance (qlDate, iPeriod)
    dtNewDate = _toPyDate (qlNewDate)
    
    return dtNewDate



def qlNumOfBusDays (dtDate1, dtDate2, sCalendar = 'UST'):
    
    qlCalendar = _getQLCalendar (sCalendar)
    qlDate1 = qlQDate (dtDate1)
    qlDate2 = qlQDate (dtDate2)
    
    iNumOfDays = qlCalendar.businessDaysBetween (qlDate1, qlDate2)
    
    return iNumOfDays 


# if __name__ == '__main__' and __package__ is None:
if __name__ == '__main__':

    from os import sys, path
    sys.path.append (path.dirname (path.dirname (path.abspath (__file__))))
    from lib.xlldate import dtIsBusDay
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
    
    logging.info (f"Testing qlibdate.py on {sToday}")
        
    ## if dtToday.isoweekday() in range (1, 6):  ## range in this way exclude 6

    dtDate1 = dt.date (2022, 11, 10)
    qDate1 = qlQDate (dtDate1)
    logging.debug (f"Note Quautlib Date structure is different: {qDate1}")
    
    logging.debug (f"QuantLib Date = {qDate1}")
    sCalendar = 'UST'
    dtDate2 = qlAddBusDays (dtDate1, -1, sCalendar)
    logging.debug (f"Previous business day = {dtDate2}")
    dtDate3 = qlAddBusDays (dtDate1, 1, sCalendar)
    logging.debug (f"Next business day = {dtDate3}")
    
    iNumOfBusDays = qlNumOfBusDays (dtDate2, dtDate3, sCalendar)
    logging.debug ("11/11/22 Friday is Veteran's Day holiday")
    logging.debug (f"Check number of business days in between: {iNumOfBusDays}")

    logging.info ("Finished Testing qllibdate.py")