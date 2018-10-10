'''
Created on 7 mars 2018

@author: thomasgumbricht
'''

from sys import exit
import os
import geoimagine.support.karttur_dt as mj_dt
from geoimagine.ktpandas import PandasTS
     
class TimeSteps:
    """Periodicity sets the time span, seasonality and timestep to process data for."""   
    def __init__(self,periodD):
        """The constructor expects the following variables: int:timestep, date:startdate, date:enddate, [int:addons], [int:maxdaysaddons], [int:seasonstartDOY], [int:seasonendDOY]."""
        for key, value in periodD.items():
            setattr(self, key, value)
        self.datumL = []
        self.datumD = {}
        if not self.timestep:
            self.SetStaticTimeStep()
        elif self.timestep == 'static':
            self.SetStaticTimeStep()
        elif self.timestep == 'singledate':
            self.SingleDateTimeStep()
        elif self.timestep == 'singleyear':
            self.SingleYearTimeStep(periodD)
        elif self.timestep == 'staticmonthly':
            self.SingleStaticMonthlyStep(periodD)
        elif self.timestep == 'fiveyears':
            self.FiveYearStep(periodD)
        
        else:
            self.SetStartEndDates(periodD)
            if self.timestep in ['M','MS','monthly','monthlyday']:
                self.MonthlyTimeStep(periodD)
                self.startdatestr = self.startdatestr[0:6]
                self.enddatestr = self.enddatestr[0:6]
                self.pandasCode = 'MS'
                self.SetMstep(periodD)

            elif self.timestep == 'varying':
                self.Varying(periodD)
            elif self.timestep == 'allscenes':
                self.AllScenes(periodD)
            elif self.timestep == 'inperiod':
                self.InPeriod(periodD)
            elif self.timestep == 'ignore':
                self.Ignore(periodD)
            elif self.timestep[len(self.timestep)-1] == 'D':
                self.SetDstep()
            elif self.timestep == '8D':
                self.SetDstep()
            elif self.timestep == '16D':
                self.SetDstep(periodD)
            else:
                exitstr = 'Unrecognized timestep in class TimeSteps %s' %(self.timestep)
                exit(exitstr)
                
    def SetStartEndDates(self, periodD):
        self.startdate = mj_dt.IntYYYYMMDDDate(periodD['startyear'],periodD['startmonth'],periodD['startday'])       
        self.enddate = mj_dt.IntYYYYMMDDDate(periodD['endyear'],periodD['endmonth'],periodD['endday'])
        self.startdatestr = mj_dt.DateToStrDate(self.startdate)
        self.enddatestr = mj_dt.DateToStrDate(self.enddate)
        if self.enddate < self.startdate:
            exitstr = 'period starts after ending'
            exit(exitstr)
        #self.processDateD = {}
        
    def SetSeasonStartEndDates(self, periodD):
        self.startdoy = self.enddoy = 0
        if periodD['seasonstartmonth'] != 0 and periodD['seasonstartday'] != 0 and periodD['seasonendmonth'] != 0 and periodD['seasonendday'] != 0:
            seasonstart = mj_dt.IntYYYYMMDDDate(2001,periodD['seasonstartmonth'],periodD['seasonstartday'])       
            seasonend = mj_dt.IntYYYYMMDDDate(2001,periodD['seasonendmonth'],periodD['seasonendday'])
            self.startdoy = int(mj_dt.YYYYDOYStr(seasonstart))
            self.enddoy = int(mj_dt.YYYYDOYStr(seasonend))
 
    def SetStaticTimeStep(self):
        self.datumL.append('0')
        self.datumD['0'] = {'acqdate':False, 'acqdatestr':'0'}
        #self.datumL.append({'acqdate':False, 'acqdatestr':'0'})
        
    def SingleYearTimeStep(self,periodD):
        if not periodD['startyear'] == periodD['endyear'] or periodD['startyear'] < 1000:
            exitstr = 'error in period: year'
            exit(exitstr)
        acqdatestr = '%(y)d' %{'y':periodD['startyear']}
        if not len(acqdatestr) == 4 or not acqdatestr.isdigit:
            exitstr = 'len(acqdatestr) != 4'
            exit(exitstr)
        self.datumL.append(acqdatestr)
        acqdate = mj_dt.SetYYYY1Jan(int(acqdatestr))

        self.datumD[acqdatestr] = {'acqdate':acqdate, 'acqdatestr':acqdatestr}
    
    def FiveYearStep(self,periodD):
        if not periodD['startyear'] < periodD['endyear'] or periodD['startyear'] < 1000 or periodD['endyear'] > 9999:
            exitstr = "periodD['startyear'] < periodD['endyear'] or periodD['startyear'] < 1000 or periodD['endyear'] > 9999"
            exit(exitstr)
        for y in range(periodD['startyear'],periodD['endyear']+1,5):
            acqdatestr = '%(y)d' %{'y':y}
            if not len(acqdatestr) == 4:
                exitstr = 'len(acqdatestr) != 4'
                exit(exitstr)
            BALLE
            #self.datumL.append({'acqdatestr':acqdatestr, 'timestep':'fiveyears'})

    def SingleStaticMonthlyStep(self,periodD):
        if periodD['endmonth'] < periodD['startmonth'] or periodD['startmonth'] > 12 or periodD['endmonth'] > 12:
            exitstr = "periodD['endmonth'] < periodD['startmonth'] or periodD['startmonth'] > 12 or periodD['endmonth'] > 12"
            exit(exitstr)
        for m in range(periodD['startmonth'],periodD['endmonth']+1):
            if m < 10:
                mstr = '0%(m)d' %{'m':m}
            else:
                mstr = '%(m)d' %{'m':m} 
            BALLE
            #self.datumL.append({'acqdatestr':mstr, 'timestep':'staticmonthly'})
            
    def MonthlyDayTimeStepOld(self,periodD):
        mstr = self.MonthToStr(periodD['startmonth'])
        yyyymmdd = '%(yyyy)s%(mm)s01' %{'yyyy':periodD['startyear'],'mm':mstr }
        startmonth = mj_dt.yyyymmddDate(yyyymmdd)
        mstr = self.MonthToStr(periodD['endmonth'])
        yyyymmdd = '%(yyyy)s%(mm)s01' %{'yyyy':periodD['endyear'],'mm':mstr }
        endmonth = mj_dt.yyyymmddDate(yyyymmdd)
        acqdatestr = mj_dt.DateToStrDate(startmonth)
        self.datumL.append({'acqdatestr':acqdatestr[0:6], 'timestep':'monthlyday'})
        monthday = startmonth
        while monthday < endmonth:
            monthday = mj_dt.AddMonth(monthday)
            acqdatestr = mj_dt.DateToStrDate(monthday)
            #Only set the month, for ile structure consistency
            pass
            #self.datumL.append({'acqdatestr':acqdatestr[0:6], 'timestep':'monthlyday'})
            
    def MonthlyTimeStep(self,periodD):
        #get start date
        mstr = self.MonthToStr(periodD['startmonth'])
        yyyymmdd = '%(yyyy)s%(mm)s01' %{'yyyy':periodD['startyear'],'mm':mstr }
        startdate = mj_dt.yyyymmddDate(yyyymmdd)

        #get end date
        mstr = self.MonthToStr(periodD['endmonth'])
        yyyymm = '%(yyyy)s%(mm)s' %{'yyyy':periodD['endyear'],'mm':mstr }
        enddate = mj_dt.YYYYMMtoYYYYMMDD(yyyymm,32)

        #yyyymmdd = '%(yyyy)s%(mm)s31' %{'yyyy':periodD['endyear'],'mm':mstr }
        #endmonth = mj_dt.yyyymmddDate(yyyymmdd)
        acqdatestr = mj_dt.DateToStrDate(startdate)
        acqdate = startdate
        self.datumL.append({'acqdate':acqdate, 'acqdatestr':acqdatestr[0:6], 'timestep':'MS'})
        while True:
            acqdate = mj_dt.AddMonth(acqdate,1)
            if acqdate > enddate:
                break
            acqdatestr = mj_dt.DateToStrDate(acqdate)
            self.datumL.append({'acqdate':acqdate, 'acqdatestr':acqdatestr[0:6], 'timestep':'MS'})
        
    def SetDstep(self):
        print ('Setting Dstep',self.timestep)

        pdTS = PandasTS(self.timestep)
        
        npTS = pdTS.SetDatesFromPeriod(self) 
        for d in range(npTS.shape[0]):
            acqdate = npTS[d].date()
            acqdatestr = mj_dt.DateToStrDate(acqdate)
            
            self.datumL.append(acqdatestr)
            self.datumD[acqdatestr] = {'acqdate':acqdate, 'acqdatestr':acqdatestr}

            '''
            self.datumL.append({'acqdate':acqdate, 'acqdatestr':acqdatestr, 'timestep':self.timestep})
            #self.processDateL.append(npTS[d].date())
            self.processDateD[acqdate] = {'acqdate':acqdate,'acqdatestr':acqdatestr, 'acqdate':npTS[d].date(),'timestep':self.timestep}
            #self.pandasDateL.append(npTS[d].date())
            '''
    
    def SetMstep(self):
        pdTS = PandasTS(self)
        npTS = pdTS.SetMonthsFromPeriod(self)
        for d in range(npTS.shape[0]):
            acqdate = npTS[d].date()

            acqdatestr = mj_dt.DateToStrDate(npTS[d])
            self.processDateD[acqdate] = {'acqdatestr':acqdatestr[0:6], 'acqdate':acqdate,'timestep':self.timestep}
            BALE
                       
    def Varying(self):
        self.datumL.append({'acqdatestr':'varying', 'timestep':'varying'})
        BALLE
        
    def AllScenes(self, periodD):
        self.SetStartEndDates( periodD)
        self.SetSeasonStartEndDates( periodD )
        #self.datumL.append({'acqdatestr':'allscenes', 'timestep':'allscenes'})
        self.datumL.append('all')
        self.datumD['all'] = {'acqdate':'all', 'acqdatestr':'all', 'startdate':self.startdate, 'enddate':self.enddate, 'startdoy':self.startdoy, 'enddoy':self.enddoy}

        
    def Ignore(self):
        self.datumL.append({'acqdatestr':'ignore', 'timestep':'ignore'})
        BALLE
        
    def InPeriod(self):
        self.datumL.append({'acqdatestr':'inperiod', 'timestep':'inperiod','startdate':self.startdate, 'enddate':self.enddate})
            
    def FindVaryingTimestep(self,path):
        BALLE
        if os.path.exists(path):
            folders = [f for f in os.listdir(path) if os.path.isdir(os.path.join(path, f))]
            self.datumL = []
            for f in folders:
                try:
                    int(f)
                    self.datumL.append({'acqdatestr':f, 'timestep':'varying'})
                except:
                    pass
                
    def MonthToStr(self,m):
        if m < 10:
            mstr = '0%(m)d' %{'m':m}
        else:
            mstr = '%(m)d' %{'m':m}
        return mstr

    def SetAcqDateDOY(self):
        BALLE
        for d in self.datumL:
            acqdate = mj_dt.yyyymmddDate(d['acqdatestr'])
            #d['acqdatedaystr'] = mj_dt.DateToYYYYDOY( acqdate)
                   
    def SetAcqDate(self):
        NALLE
        for d in self.datumL:
            pass
            #d['acqdate'] = mj_dt.yyyymmddDate(d['acqdatestr'])
        