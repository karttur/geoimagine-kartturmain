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
    def __init__(self,periodD,timestep = False, verbose=0):
        """The constructor expects the following variables: int:timestep, date:startdate, date:enddate, [int:addons], [int:maxdaysaddons], [int:seasonstartDOY], [int:seasonendDOY]."""
        self.verbose = verbose
        for key, value in periodD.items():
            setattr(self, key, value)
        
        if timestep:
            #overrides the overall timestep with composition specific timestep
            self.timestep = timestep
        if self.verbose > 1:
            print ('    Setting timestep',self.timestep)
        self.datumL = []
        self.datumD = {} 
        self.pdTS = PandasTS(self.timestep)
        if not self.timestep:
            self.SetStaticTimeStep()
        elif self.timestep == 'static':
            self.SetStaticTimeStep()
        elif self.timestep == 'singledate':
            self.SingleDateTimeStep(periodD)
        elif self.timestep == 'singleyear':
            self.SingleYearTimeStep(periodD)
        elif self.timestep in ['staticmonthly','static-M','static-MS']:
            self.SingleStaticMonthlyStep(periodD)
        elif self.timestep == 'fiveyears':
            self.FiveYearStep(periodD)
        elif self.seasonalts:
            self._SetSeasonalTS(periodD)
        else:
            self.SetStartEndDates(periodD)
            self.SetSeasonStartEndDates(periodD)
            
            if self.timestep in ['A','AS','annual']:
                self.startdatestr = self.startdatestr[0:4]
                self.enddatestr = self.enddatestr[0:4]
                self.pandasCode = 'A'
                self.SetAstep()
                
            elif self.timestep in ['timespan-A']:
                self.startdatestr = self.startdatestr[0:4]
                self.enddatestr = self.enddatestr[0:4]
                self.pandasCode = 'A'
                self.SetAtimespan()
                
            elif self.timestep in ['timespan-M','timespan-MS']:
                self.startdatestr = self.startdatestr[0:6]
                self.enddatestr = self.enddatestr[0:6]
                self.pandasCode = 'M'
                self.SetMtimespan()
                
            elif 'timespan-' in self.timestep:
                #must be 'timespan-XXD'
                startdate = mj_dt.yyyymmddDate(self.startdatestr)
                enddate = mj_dt.yyyymmddDate(self.enddatestr)
                self.startdatestr = mj_dt.DateToYYYYDOY(startdate)
                self.enddatestr = mj_dt.DateToYYYYDOY(enddate)
                dstep = self.timestep.split('-')[1]
                dstep = int(dstep[0:len(dstep)-1])
                self.pandasCode = '%(s)dD' %{'s':dstep}
                self.SetxDtimespan(dstep)

                
            elif self.timestep in ['M','MS','monthly','monthlyday']:
                #self.MonthlyTimeStep(periodD)
                #self.startdatestr = self.startdatestr[0:6]
                #self.enddatestr = self.enddatestr[0:6]
                self.pandasCode = 'MS'
                self.SetMstep()
            elif self.timestep[0:8] == 'autocorr': 
                self._SetAutoCorrTS(periodD)
            elif self.timestep in ['seasonal-M', 'seasonal-Mday']:
                self._SetSeasonalTS(periodD)
            elif self.timestep == 'varying':
                self.Varying(periodD)
            elif self.timestep in ['allscenes','anyscene']:
                self.AllScenes(periodD)
            elif self.timestep == 'inperiod':
                self.InPeriod(periodD)
            elif self.timestep == 'ignore':
                self.Ignore(periodD)
            elif self.timestep == 'D':
                self.SetDstep()
            elif self.timestep[-1] == 'D':
                if (self.timestep[0:8] == 'seasonal'):
                    self._SetSeasonalTS(periodD)
                else:
                    self.SetXDstep()
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
        
    def SingleDateTimeStep(self,periodD):
        self.startdate = self.enddate = mj_dt.IntYYYYMMDDDate(periodD['startyear'],periodD['startmonth'],periodD['startday'])       
        self.startdatestr = self.enddatestr = mj_dt.DateToStrDate(self.startdate)
        self.datumD[self.startdatestr] = {'acqdate':self.startdate, 'acqdatestr':self.startdatestr}
    
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
            self.datumL.append(mstr)
            self.datumD[mstr] = {'acqdatestr':mstr, 'acqdate':False, 'season':m}
        self.timestep = 'static-M'

        self.moviedatum = 'static-M' 
        
    def _SetSeasonalTS(self,periodD):  
        '''
        '''
        if self.timestep in ['M','MS','monthly','monthlyday','seasonal-M','seasonal-mday']:
            #Get the mpnth of the first date set
            m = periodD['startmonth']
            datumD = {1:'01',2:'02',3:'03',4:'04',5:'05',6:'06',7:'07',8:'08',9:'09',10:'10',11:'11',12:'12'}
            timespan = '%s-%s' %(self.startyear, self.endyear)
            datumL = []
            datumL.append(datumD[m])
            #Loop forward until a complete year is finished
            while True:
                m += 1
                if m > 12:
                    m = 1
                if m == int(datumL[0]):
                    break
                datumL.append(datumD[m])
            for datum in datumL:
                datum = '%s@M%s' %(timespan,datum)
                self.datumL.append(datum)
                self.datumD[datum] = {'acqdatestr':datum, 'acqdate':False, 'season':m}
            self.timestep = 'seasonal-M'

        elif self.timestep[len(self.timestep)-1] == 'D':
            if (self.timestep[0:8] == 'seasonal'):
                step = self.timestep.split('-')[1]
                midstep = 0
                
                self.dstep = self.periodstep = int(step[0:len(step)-1])
                midstep  = int(self.dstep/2)
            else:
                self.dstep = self.periodstep = int(self.timestep[0:len(self.timestep)-1])
                midstep  = int(self.dstep/2)
            self.SetStartEndDates(periodD)
            
            doy = mj_dt.DateToDOY(self.startdate)
            #Find the lowest doy (1 or higher)
            inidoy = doy
            if self.dstep <= 0:
                print (self.dstep)
                ERROR
            while True:
                if inidoy - self.dstep <= 0:
                    break
                inidoy -= self.dstep

            #Get the doy of the first date set
            datumL = []
            doy = mj_dt.DateToDOY(self.startdate)
            doy += midstep
            #Find the lowest doy (1 or higher)
            inidoy = doy
            while True:
                if inidoy - self.dstep <= 0:
                    break
                inidoy -= self.dstep

            datumL.append(mj_dt.DoyStr(doy))
            #Loop forward until a complete year is finished
            while True:
                doy += self.dstep
                if doy > 365:
                    doy = inidoy
                if doy == int(datumL[0]):
                    break
                datumL.append(mj_dt.DoyStr(doy))
            timespan = '%s-%s' %(self.startyear, self.endyear)
            for d in datumL:
                datum = '%s@D%s' %(timespan,d)
                self.datumL.append(datum)
                season = 1+int((int(d)-int(inidoy))/self.dstep)
                self.datumD[datum] = {'acqdatestr':datum, 'acqdate':False, 'season':season}
                
            self.timestep = 'seasonal-%(t)s' %{'t':self.timestep}

            self.moviedatum = '%s@%sD' %(timespan,self.dstep)

        else:
            NOTYEAT
        
    def _SetAutoCorrTS(self,periodD):  
        '''
        '''
        datumL = []
        timespan = '%s-%s' %(self.startyear, self.endyear)
        if self.timestep in ['autocorr-M','autocorr-MS']:
            #Get the mpnth of the first date set
            #Always skip the first autocrr, by default = 1
            for t in range(1,periodD['nlags']+1):
                #t -= periodD['mirror']
                if periodD['mirror'] > 0 and t > periodD['mirror']:
                    #t =  periodD['mirror']*2 - t 
                    lag = 'lag%(dt)d' %{'dt':t-periodD['nlags']}
                else:
                    lag = 'lag%(dt)d' %{'dt':t}
                datum = '%s@M%s' %(timespan,lag)
                self.datumL.append(datum)
                self.datumD[datum] = {'acqdatestr':datum, 'acqdate':False, 'season':t}
                self.timestep = 'autocorr-M'

        elif self.timestep[len(self.timestep)-1] == 'D':
            FIX

        else:
            NOTYEAT
            
    def SetDstep(self):
        self.pdTS = PandasTS(self.timestep)
        npTS = self.pdTS.SetDatesFromPeriod(self) 
        #lastDate = npTS[-1]
        self.pandasCode = self.timestep
        for d in npTS:
            acqdate = d.date()
            acqdatestr =mj_dt.DateToStrDate(acqdate)         
            self.datumL.append(acqdatestr)
            self.datumD[acqdatestr] = {'acqdate':acqdate, 'acqdatestr':acqdatestr}

    def SetXDstep(self):
        '''
        '''
        self.pdTS = PandasTS(self.timestep)
        step = int(self.timestep[0:len(self.timestep)-1])
        self.dstep = step
        midstep  = int(step/2)
        #Step with the dates set to end of each period
        npTSEnds = self.pdTS.SetDatesFromPeriodEnds(self,step)

        lastPeriodDate = npTSEnds[-1]
        npTS = self.pdTS.SetDatesFromPeriod(self) 
        lastDate = npTS[-1]

        self.pandasCode = self.timestep
        #Added midstep again 20 nov 2018

        if lastDate > lastPeriodDate:
            rng = npTS.shape[0]-1
        else:
            rng = npTS.shape[0]
        doy = mj_dt.DateToDOY(self.startdate)
        #Find the lowest doy (1 or higher)
        inidoy = doy
        if self.dstep <= 0:
            print (self.dstep)
            ERROR
        while True:
            if inidoy - self.dstep <= 0:
                break
            inidoy -= self.dstep 
        for d in range(rng):
            acqdate = npTS[d].date()
            
            #Here comes the trick, the acqdatestr for D data (whihc is a span) is always the central day
            
            acqlastdate = mj_dt.DeltaTime(acqdate, step-1-midstep)
            
            if acqlastdate <= self.enddate:
         
                doy = mj_dt.DateToDOY(acqdate)
                acqmiddate = mj_dt.DeltaTime(acqdate, midstep)
                acqdatestr = mj_dt.DateToYYYYDOY(acqmiddate)
                self.datumL.append(acqdatestr)
                season = 1+int((doy-inidoy)/self.dstep)
                firstdate = acqdate
                lastdate = mj_dt.DeltaTime(acqdate, step-1)
                self.datumD[acqdatestr] = {'acqdate':acqdate, 'acqdatestr':acqdatestr, 'season':season,'firstdate':firstdate,'lastdate':lastdate}
            else:
                print ('discarded',acqdate,acqlastdate,self.enddate,step-1-midstep)
        self.moviedatum = '%s-%s' %(self.datumL[0], self.datumL[len(self.datumL)-1])
        
    def SetMstep(self):
        self.dstep = self.periodstep = 0
        self.pdTS = PandasTS(self.timestep) 
        npTS = self.pdTS.SetMonthsFromPeriod(self)
        #npTS = self.pdTS.SetDatesFromPeriod(self) 
        for d in range(npTS.shape[0]):  
            acqdate = npTS[d].date()

            acqlastdate = mj_dt.AddMonth(acqdate, 1)
            acqlastdate = mj_dt.DeltaTime(acqlastdate, -1)
            if acqlastdate <= self.enddate:
                acqdatestr = mj_dt.DateToStrDate(acqdate)
                if self.timestep in ['monthlyday']:
                    pass
                else:
                    acqdatestr = acqdatestr[0:6]
                self.datumL.append(acqdatestr)
                self.datumD[acqdatestr] = {'acqdate':acqdate, 'acqdatestr':acqdatestr,  'season':acqdate.month}
        
                
        self.moviedatum = '%s-%s' %(self.datumL[0], self.datumL[len(self.datumL)-1])
        
    def SetAstep(self):
        pdTS = PandasTS(self.timestep)
        npTS = pdTS.SetYearsFromPeriod(self)

        for year in npTS:
            acqdate = mj_dt.IntYYYYMMDDDate(year,self.startdate.month,self.startdate.day)
            acqdatestr = '%(y)d' %{'y':year}
            self.datumL.append(acqdatestr)
            self.datumD[acqdatestr] = {'acqdate':acqdate, 'acqdatestr':acqdatestr}
  
    def SetAtimespan(self):
        acqdatestr = '%s-%s' %(self.startdatestr,self.enddatestr)
        self.datumL = [acqdatestr]
        self.datumD[acqdatestr] = {'acqdate':False, 'acqdatestr':acqdatestr}
        
    def SetMtimespan(self):
        '''
        '''
        acqdatestr = '%s-%s@M' %(self.startdatestr,self.enddatestr)
        self.datumL = [acqdatestr]
        self.datumD[acqdatestr] = {'acqdate':False, 'acqdatestr':acqdatestr}
        
    def SetxDtimespan(self,x):
        '''
        '''
        #TGTODO Change the length fo timestamp to 20 and return to the below
        #acqdatestr = '%s-%s@%sD' %(self.startdatestr,self.enddatestr,x)
        acqdatestr = '%s-%s@D' %(self.startdatestr,self.enddatestr)
        self.datumL = [acqdatestr]
        self.datumD[acqdatestr] = {'acqdate':False, 'acqdatestr':acqdatestr}
                       
    def Varying(self):
        self.datumL.append({'acqdatestr':'varying', 'timestep':'varying'})
        BALLE
        
    def AllScenes(self, periodD):
        self.SetStartEndDates( periodD)
        self.SetSeasonStartEndDates( periodD )
        #self.datumL.append({'acqdatestr':'allscenes', 'timestep':'allscenes'})
        self.datumL.append('all')
        self.datumD['all'] = {'acqdate':False, 'acqdatestr':'all', 'startdate':self.startdate, 'enddate':self.enddate, 'startdoy':self.startdoy, 'enddoy':self.enddoy}
   
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
        