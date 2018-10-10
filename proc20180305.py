'''
Created on 7 mars 2018

@author: thomasgumbricht
'''

from geoimagine.kartturmain.timestep import TimeSteps
import geoimagine.support.karttur_dt as mj_dt
import geoimagine.gis.gis as mj_gis
from os import path, makedirs
from geoimagine.support.karttur_dt import Today
from copy import deepcopy

def CheckSetValue(xmlOD):
    L = []
    if type(xmlOD) is list:
        for item in xmlOD:

            paramL = ['value','label']
            valueL = [ item['@value'], item['@label'] ]
            D = dict(zip(paramL,valueL))
            L.append(D)        
    else:
        paramL = ['value','label']
        valueL = [ xmlOD['@value'], xmlOD['@label'] ]  
        D = dict( zip(paramL,valueL) )
        L.append(D) 
    return L

def CheckSetMinMax(xmlOD):
    mini = xmlOD['@min'].replace('.','')
    maxi = xmlOD['@min'].replace('.','')
    if mini[0] == '-':
        mini = mini[1:len(mini)-1]
    if maxi[0] == '-':
        maxi = maxi[1:len(maxi)-1]
    if not mini.isdigit():
        print ('min',mini)
        exit('set value min error')
    if not maxi.isdigit():
        print ('max',maxi)
        exit('set value max error')
    return {'min':xmlOD['@min'], 'max':xmlOD['@max']}

def BoolTag(booltag):
    if booltag == '': 
        return False #i.e. no item given, assume False
    if booltag[0].lower() == 'n' or booltag.lower() == 'false':
        return False
    elif booltag[0].lower() == 'y' or booltag.lower() == 'true':
        return True
    else:
        warnstr = 'Can not resolve boolean node %(s)s' %{'s':booltag}
        print (warnstr)

def CheckSetParamValues(tagAttrL, xmlOD):
    flagga = True
    paramL = []
    valueL = []
    errorD = {}
    subItems = []
    for item in tagAttrL:  
        if item[0] == 'E':
            subItems.append(item[1])
            continue
        elif item[0] == 'A':
            s = '@%s' %(item[1].lower())
        else:
            s = item[1].lower()

        #Check if the parameter is required
        if item[3].lower()[0] in ['y','t']:
            if not s in xmlOD:
                print ('s',s)
                print ('xmlOD',xmlOD)
                print ('item',item)
                
                print ('        xmlOD',xmlOD)
                print ('        xmlOD',xmlOD.keys())
                print ('        tagattrl', tagAttrL)
                errorD[item[1]] = item
                flagga = False
                warnstr = '        Warning: The required parameter "%(p)s" (%(s)s) is lacking in tag "%(t)s"'  %{'p':item[1],'s':s,'t':item[6]}
                print (warnstr)
                BALLE
            else:
                value = xmlOD[s] 
        elif s in xmlOD:
            value = xmlOD[s]
        else:
            value = item[4]
        #check if the parameter is boolean, integer or float and try to set
        if item[2][0:4].lower() == 'bool':
            value = BoolTag(value)
        elif item[2][0:3].lower() == 'int':
            try:
                value = int(value)
            except:
                warnstr = 'Warning: The parameter %(p)s must be an integer' %{'p':item[1]}
                print (warnstr)
                flagga = False
                errorD[item[1]] = item
        elif item[2][0:3].lower() in ['flo','rea']:
            try:
                value = float(value)
            except:
                warnstr = 'Warning: The parameter %(p)s must be a float' %{'p':item[1]}
                print (warnstr)
                flagga = False
                errorD[item[1]] = item
        if not flagga:
            return False
        paramL.append(item[1])
        valueL.append(value)
    return dict(zip(paramL,valueL)),subItems

class LayerCommon:
    '''
    '''
    def __init__(self):
        pass
    
    def _SetDOY(self):
        self.datum.doyStr = mj_dt.YYYYDOYStr(self.datum.acqdate)
        self.datum.doy = int(self.datum.doyStr)
        
    def _SetAcqdateDOY(self):
        self.datum.acqdatedoy = mj_dt.DateToYYYYDOY(self.datum.acqdate)
        
    def _SetBounds(self,epsg,minx,miny,maxx,maxy):
        self.epsg = epsg
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.BoundsPtL = ( (minx,maxy),(maxx,maxy),(maxx,miny), (minx,miny) )
        
    def _Update(self, upD):
        for key in upD:
            setattr(self, key, upD[key])
        
    def _Exists(self):
        """checks if the layer file exists; creates the folder path to the layer if non-existant."""
        if path.isfile(self.FPN):
            self.exists = True
            return True
        else:
            if not path.isdir(self.FP):
                makedirs(self.FP)
            self.exists = False
            return False

class Layer(LayerCommon):
    """Layer is the parentid class for all spatial layers."""
    def __init__(self, composition, locusD, datumD, filepath): 
        """The constructor expects an instance of the composition class."""
        LayerCommon.__init__(self)

        self.comp = composition
        self.locus = lambda: None
        for key, value in locusD.items():
            setattr(self.locus, key, value)

        self.path = filepath

        self.datum = lambda: None
        for key, value in datumD.items():
            setattr(self.datum, key, value)
        if self.datum.acqdate:
            self._SetDOY()
            self._SetAcqdateDOY()
        if self.path.hdrfiletype[0] == '.':
            self.path.hdr = self.path.ext = self.path.hdrfiletype
        else:
            self.path.hdr = self.path.ext ='.%s' %(self.path.hdrfiletype)
        if hasattr(self.path, 'datfiletype') and len(self.path.datfiletype) >= 2:
            if self.path.datfiletype[0] == '.':
                self.path.dat = self.path.datfiletype
            else:
                self.path.dat = '.%s' %(self.path.datfiletype)
        self._SetPath()
     
    def _SetPath(self):
        """Sets the complete path to region files"""
        #print ('FUCKING PATH',self.path.volume, self.comp.system, self.comp.source, self.comp.division, self.comp.folder, self.locuspath, self.datum.acqdatestr)

        self.FN = '%(prefix)s_%(prod)s_%(reg)s_%(d)s_%(suf)s%(e)s' %{'prefix':self.comp.prefix,'prod':self.comp.product,'reg':self.locus.locus, 'd':self.datum.acqdatestr, 'suf':self.comp.suffix,'e':self.path.ext}            
        self.FP = path.join('/Volumes',self.path.volume, self.comp.system, self.comp.source, self.comp.division, self.comp.folder, self.locus.path, self.datum.acqdatestr)
        self.FPN = path.join(self.FP,self.FN)
        if ' ' in self.FPN:
            exitstr = 'EXITING region FPN contains space %s' %(self.FPN)
            exit(exitstr)
                  
class VectorLayer(Layer):
    def __init__(self, comp, locusD, datumD, filepath): 
        Layer.__init__(self, comp, locusD, datumD, filepath)
        if not 'shp' in filepath.hdrfiletype.lower():
            'Error in hdrfiletype for vector file'
            BALLE

    
    def CreateVectorAttributeDef(self,fieldDD): 
        fieldDefD = {}
        self.fieldDefL =[]
        for key in fieldDD:
            fieldD = fieldDD[key]
            if 'width' in fieldD:
                width = fieldD['width']
            else:
                self.width = 8
            if 'precision' in fieldD:
                precision = fieldD['precision']
            else:
                precision = 0
            if 'keyfield' in fieldD:
                keyfield = fieldD['keyfield']
            elif 'field' in fieldD:
                keyfield = fieldD['field']
            else:
                keyfield = False
            fieldDefD[key] = {'type':fieldD['type'].lower(), 'width':width, 'precision': precision, 'transfer': fieldD['transfer'].lower(), 'source':fieldD['source'], 'keyfield':keyfield}      
        for key in fieldDefD:
            self.fieldDefL.append(mj_gis.FieldDef(key,fieldDefD[key]))
     
class RasterLayer(Layer):
    def __init__(self, comp, locusD, datumD, filepath): 
        Layer.__init__(self, comp, locusD, datumD, filepath)
        
    def GetRastermetadata(self):
        #TGTODO THIS AND NEXT MUST BE REDUNDANT- NO IT IS JUST IN IMPORT OF ANCIAARY
        self.spatialRef, self.metadata = mj_gis.GetRasterMetaData(self.FPN)
        #transfer cellnull and celltype to composition
        self.comp.spatialRef = self.spatialRef
        self.comp.metadata = self.metadata
        #self.comp.cellnull = self.metadata.cellNull
        #self.comp.celltype = self.metadata.cellType
        
    def ReadRasterLayerOld(self,**kwargs):
        readD = {'mode':'edit'}
        if kwargs is not None:
            for key, value in kwargs.items():
                readD[key] = value
                #setattr(self, key, value)
        self.BAND =  mj_gis.ReadRasterArray(self.FPN, readD)
     
    def RasterOpenGetFirstLayer(self,**kwargs):
        modeD = {'mode':'read'}
        if kwargs is not None:
            for key, value in kwargs.items():
                modeD[key] = value
                #setattr(self, key, value)
        self.DS,self.layer = mj_gis.RasterOpenGetFirstLayer(self.FPN,modeD)
        self.GetGeoFormatD()
        
    def RasterCreateWithFirstLayer(self,layer):
        self.dstDS = mj_gis.RasterCreateWithFirstLayer(self.FPN,layer)

            
    def GetGeoFormatD(self):
        self.geoFormatD = {'lins':self.layer.lins,'cols':self.layer.cols,'projection':self.layer.projection,'geotrans':self.layer.geotrans,'cellsize':self.layer.cellsize}
        
    def SetGeoFormat(self,geoFormatD):
        """Sets the geoFormat
            Expects a dict with {['lins'],['cols'],['projection'],['geotrans'],['cellsize']}
        """ 
        for key, value in geoFormatD.items():
            setattr(self, key, value)
        
    def CreateDSWriteRasterArray(self,**kwargs):
        writeD = {'complete':True, 'of':'GTiff'}
        if kwargs is not None:
            for key, value in kwargs.items():
                writeD[key] = value
        mj_gis.CreateDSWriteRasterArray(self, writeD)
      
class RegionLayer(Layer): 
    """layer class for arbitrary layers.""" 
    def __init__(self,comp, location, datum, movieframe = False): 

        """The constructor expects an instance of the composition class."""
        Layer.__init__(self, comp, datum)
        
        self.layertype = 'region'
        self.movieframe = movieframe
        self.location = lambda: None
        
        self.location.regionid = location
        
        #Set the filename and path
        self.SetRegionPath()
        
    def _SetLayerPath(self):
        BALLE
        self._SetRegionPath()
        
    def _SetRegionPath(self):
        """Sets the complete path to region files"""

        self.FN = '%(prefix)s_%(prod)s_%(reg)s_%(d)s%(suf)s%(e)s' %{'prefix':self.comp.prefix,'prod':self.comp.product,'reg':self.location.regionid, 'd':self.datum.acqdatestr, 'suf':self.comp.suffix,'e':self.comp.ext}            
        if self.movieframe:
            self.FP = os.path.join(self.comp.mainpath, self.comp.source, self.comp.division, self.comp.folder, self.location.regionid)
        else:
            self.FP = os.path.join(self.comp.mainpath, self.comp.source, self.comp.division, self.comp.folder, self.location.regionid, self.datum.acqdatestr)

        self.FPN = os.path.join(self.FP,self.FN)
        if ' ' in self.FPN:
            exitstr = 'EXITING region FPN contains space %s' %(self.FPN)
            exit(exitstr)
   
class TextLayer(Layer):
    def __init__(self, comp, locusD, datumD, filepath): 
        Layer.__init__(self, comp, locusD, datumD, filepath)
                      
class Location:
    '''
    classdocs
    '''
    def __init__(self, processid, defregid, system, division, session): 
        self.defregid = defregid
        self.system = system
        self.division = division
        self.locusD = {}
        self.locusL = []
        print ('system',system)
        print ('division',division)
        if division in ['NA','none','None','na']:
            #No spatial data involved
            pass
        elif division == 'region':
            self.locusL.append(self.defregid)
            self.locusD[self.defregid] = {'locus':self.defregid, 'path':self.defregid}
        elif division == 'tiles' and system.lower() == 'modis':
            from geoimagine.support.modis import ConvertMODISTilesToStr as convTile
            tiles = session._SelectModisRegionTiles({'regionid':self.defregid})
            for tile in tiles:
                hvD = convTile(tile)
                self.locusL.append(hvD['prstr'])
                self.locusD[hvD['prstr']] = {'locus':hvD['prstr'], 'path':hvD}
        elif division == 'tiles' and system.lower() == 'sentinel' and processid[0:7] in ['downloa', 'explode','extract','geochec','findgra','reorgan']:
            self.locusL.append('unknwon')
            self.locusD['unknown'] = {'locus':'unknwon', 'path':'unknwon'}
        elif division == 'scenes' and system.lower() == 'landsat' and processid[0:7] in ['downloa', 'explode','extract','geochec','findgra','reorgan']:
            self.locusL.append('unknwon')
            self.locusD['unknown'] = {'locus':'unknwon', 'path':'unknwon'}

        else:
            print ('add division, system', division, system, processid)
            BALLE
        print ('self.locusD',self.locusD)

class Composition:
    '''
    classdocs
    '''
    def __init__(self, compD, system, division):
        self.checkL  = ['source','product','folder','band','prefix','suffix']
        print ('compD',compD)
        for key in compD:
            if key in self.checkL:
                if '_' in compD[key]:
                    exitstr = 'the "%s" parameter can not contain underscore (_): %s ' %(key, compD[key])
                    exit(exitstr) 
            setattr(self, key, compD[key])

        if not hasattr(self, 'band'):
            exitstr = 'All compositions must contain a band'
            exit(exitstr)
            
        if not hasattr(self, 'folder'):
            exitstr = 'All compositions must contain a folder'
            exit(exitstr)
            
        if not hasattr(self, 'suffix'):
            self.suffix = '0'
        
        if self.suffix == '':
            self.suffix = '0'
            
        self._SetCompid()
        self._SetSystem(system)
        self._SetDivision(division)

        
    def _SetSystem(self,system):
        self.system = system

        
    def _SetDivision(self,division):
        self.division = division
        
    def _SetCompid(self):
        self.compid = '%(f)s_%(b)s' %{'f':self.folder, 'b':self.band}
            
            
    def _Update(self, compD):
        for key in compD:
            if key in self.checkL:
                if '_' in compD[key]:
                    exitstr = 'the "%s" parameter can npot contain underscore (_): %s ' %(key, compD[key])
                    exit(exitstr) 
            setattr(self, key, compD[key])
    
    
class UserProj:
    '''
    Define the user project
    '''
    def __init__(self, userprojD,tagAttrL):
        '''
        The Constructor expects two dictionaries defining the user
        '''
        self.userprojD = CheckSetParamValues(tagAttrL, userprojD)[0]

        for key in self.userprojD:
            setattr(self, key, self.userprojD[key])   
            
            
    def _SetCredentials(self, userCat, userStratum, **kwargs):
        self.usercat = userCat
        self.userstratum = userStratum
        for key in kwargs:
            setattr(self, key, [item[0] for item in kwargs[key]]) 

    def _CheckUserProj(self):
        '''
        Checks if the user owns the region and has the right to perform the process
        '''
        print ('self.userProjs',self.userProjs)
        print ('self.projectid',self.projectid)
        if not self.projectid in self.userProjs:
            exitstr = 'No project %(p)s owned by user %(u)s\    projectes owned by user: %(l)s' \
            %{'p':self.projectid, 'u':self.userId, 'l':self.userProjs}
            exit(exitstr)
        if self.plotid not in ['','*']:
            exit('plot wise processing not implemented')
        elif self.siteid not in ['','*']:
            if self.siteid in self.userSites:
                self.tract = False
            else:
                warnstr = 'No site %(s)s owned by user %(u)s\    sites owned by user: %(l)s' \
                %{'p':self.siteid, 'u':self.userId, 'l':self.sites}
                print (warnstr)
                return False
        elif self.tractid not in ['','*']:
            if self.tractid in self.userTracts:
                self.site = False
            else:
                warnstr = 'No tract %(t)s owned by user %(u)s\    tracts owned by user: %(l)s' \
                %{'p':self.tractid, 'u':self.userid, 'l':self.tracts}
                exit(exitstr)
                print (warnstr)
                return False        
        return True

    def _GetDefRegion(self,session):
        '''
        Sets the default region
        '''
        print ('self.tractid',self.tractid)

        if self.tractid:
            self.defregion = session._SelectTractDefRegion(self.tractid)[0]
        elif self.siteid:
            exit('add site defregion')
        if self.defregion == 'globe':
            exit('globe is not allowed')
        #TGTODO Check if user has the right to this region

class SetXMLProcess:
    '''
    classdocs
    '''
    def __init__(self, userProj, processid, content, session, verbose):
        '''
        The constructor sets the userProj (class) and the overall periodD
        '''
        self.userProj = userProj
        self.processid = processid
        self.verbose = verbose
        
        tagAttrL = session._SelectProcessTagAttr('periodicity','process','period') 
        if 'period' in content:
            period = content['period']
            self.periodD = CheckSetParamValues(tagAttrL, period)[0]    
        else:
            self.periodD = {'timestep': 0}

    def _CheckPermission(self, session):
        '''
        Checks if the user has the right to perform the process
        '''
        query = {'subprocid':self.processid}
        result = session._SelectStratum(query)
        if result == None:
            exitstr = 'EXITING, The process %s is not defined in kartturmanin.proc20180305._CheckPermission' %(self.processid)
            exit(exitstr)
        procStratum = result[0]  
        if procStratum > self.userProj.userstratum:
            if procStratum == 10:
                warnstr = '    Only superuser have access to the process %(p)s' %{'p':self.processid}
            else:
                warnstr = '    User %(u)s does not have the right to the process %(p)s' %{'u':self.userProj.userid,'p': self.processid}
            print (warnstr)
            return False
        else:
            return True
                        
    def _CheckSubElements(self, tagAttrL, element, tagName, paramName, nodeparent, session):
        #tagAttrL, tagItem[comp], tagName, paramD['parent'], session
        #Check if the element contains any sub element
        for tagAttr in tagAttrL:
            if tagAttr[0] == 'E':
                #this can only be the setvalues or minmax under the the node tag 
                subTagAttrL = session._SelectProcessTagAttr(self.processid,tagAttr[6],tagAttr[1])
                if len(subTagAttrL) == 0:
                    print ('subTagAttrL',subTagAttrL)
                    BALLE
                if type(element) is list:
                    for itm in element:
                        paramD, subItems = CheckSetParamValues(subTagAttrL, itm)
                        #the possible subelements
                        print ('tagname',tagName)
                        FITTA
                        if tagName == 'node':   
                            if 'setvalue' in itm:
                                paramD['setvalue'] = CheckSetValue(itm['setvalue'])
                            if 'minmax' in itm:
                                paramD['minmax'] = CheckSetMinMax(itm['minmax'])
                            self.node.paramsD[paramName][nodeparent].append(paramD)
                        else:
                            exitstr ='Unknown listed sub tag %s' %(tagName)
                            exit(exitstr)
                else:
                    paramD, subItems = CheckSetParamValues(subTagAttrL, element)
                    if tagName == 'node':   
                        if 'setvalue' in element:
                            paramD['setvalue'] = CheckSetValue(element['setvalue'])

                        if 'minmax' in element:
                            paramD['minmax'] = CheckSetMinMax(element['minmax'])

                        self.node.paramsD[paramName][nodeparent].append(paramD)
                    elif tagName == 'dstcomp':
                        if paramName == paramD['band']:
                            self.dstcompD[paramName] = paramD
                        else:
                            exitstr = 'The dstcomp tag must be identical with the band name (%s != %s)' %(paramName, paramD['band'])
                            exit(exitstr)                                                                                               
                    elif tagName == 'srccomp':
                        if paramName == paramD['band']: 
                            self.srccompD[paramName] = paramD

                        else:
                            exitstr = 'The srccomp tag must be identical with the band name (%s != %s)' %(paramName, paramD['band'])
                            exit(exitstr) 
                    elif tagName == 'procsys':
                        self.system.paramD[paramName] = paramD
                    else:
                        print ('subTagAttrL',subTagAttrL)
                        print ('paramS',paramD)
                        exitstr ='Unknown single sub tag %s' %(tagName)
                        print (exitstr)
                        FIYYA
                        exit(exitstr)

    def _CheckParams(self, processD, session):
        '''
        Checks given parameters against database entries
        '''
        #Create all the variables and dictionaries
        self.dstcompD = {}
        self.dstcopyD = {}
        self.srccompD = {}
        self.paramsD = {'creator': self.userProj.userid, 'today': Today()}        
        self.node = lambda: None
        self.node.paramsD = {}
        #self.system = {}
        #self.system is only for addsubproc
        self.system = lambda: None
        self.system.paramD = {}
        #self.systemD is the process itself
        self.systemD = {}
        
        self.srcraw = lambda: None
        self.srcraw.paramsD = {}
        #get the rooprocid of the process
        query ={'subprocid':self.processid}

        self.rootprocid = session._SelectRootProcess(query)[0]  
        #Check and set system setting (the overall system, the source division and the destination division)
        systemsettings = session._SelectProcessSystems(query)
        sysOK = False
        systemParams = ['system', 'srcsystem', 'dstsystem', 'srcdivision', 'dstdivision']
        #print ('systemsettings',systemsettings)
        for procsys in systemsettings:

            if procsys[0] == self.userProj.system:
                sysOK = True
                self.systemD = dict(zip(systemParams, procsys))
                print ('SYSTEM',self.systemD)
                #self.system, self.srcsystem, self.dstsystem, self.srcdivision, self.dstdivision = procsys
        if not sysOK:
            print ('systemsettings',systemsettings)
            print ('self.userProj.system',self.userProj.system)
            exitstr = 'kartturmain.proc20180305-_CheckParams: The process %s can not be run on the system: %s' %(self.processid, self.userProj.system)   
            print (exitstr)
            exit(exitstr)

        #Set the boolean variables common to all processes
        self._SetOverwriteDeletePipeline(processD)
        
        #Loop over all tags in the process
        for tagName in processD:
            print ('    tagname',tagName)

        #Loop over all tags in the process
        for tagName in processD:
            if tagName[0] == '@':
                #process attributes are already processed
                continue
            
            if tagName in ['overwrite','delete','pipeline']:
                continue
            
            #Get the expected variables from the db
            tagAttrL = session._SelectProcessTagAttr(self.processid,'process',tagName)
            print ('tagAttrL',tagAttrL)

            
            if len(tagAttrL) == 0:
                exitstr = 'No tags/attributes found for processid "%s", tag name "%s"' %(self.processid, tagName)
                exit(exitstr)

            if type(processD[tagName]) is list:
                if tagName in ['parameters', 'period', 'srcperiod', 'dstperiod', 'srcpath', 'dstpath']:
                    exitstr = 'Each process can only have one tag named %(p)s' %{'p':tagName}
                    exit(exitstr)
            else:
                #Convert to list anyway
                processD[tagName] = [processD[tagName]]

            for tagItem in processD[tagName]:
                print ('    checking tagItem',tagItem)
                
                paramD,subItems = CheckSetParamValues(tagAttrL, tagItem)
                #print (paramD,subItems)

                if tagName == 'parameters':
                    self.paramsD = paramD
                    self.paramsD['creator'] = self.userProj.userid 
                    self.paramsD['today'] = Today() 
                elif tagName == 'period':
                    #Resets period from default
                    self.periodD = paramD
                elif tagName == 'srcpath':
                    self.srcpathD = paramD

                elif tagName == 'dstpath':
                    self.dstpathD = paramD
                elif tagName == 'srcperiod':
                    #Resets period from default
                    self.srcperiodD = paramD
                elif tagName == 'dstperiod':
                    #Resets period from default
                    self.dstperiodD = paramD
                    
                elif tagName == 'system':
                    for procsys in tagItem:
                        if not type(tagItem[procsys]) is list:
                            tagItem[procsys] = [tagItem[procsys]]
                        for ps in tagItem[procsys]:                            
                            elementname = ps['@system']

                            self._CheckSubElements(tagAttrL, ps, 'procsys', elementname, tagName, session)
                    
                elif tagName in ['srccomp','dstcomp']:
                    '''
                    for comp in tagItem:
                        print ('comp',comp, tagItem[comp])
                        print (comp[0])
                    print ('subItems',subItems)
                    '''
                    for comp in tagItem:
                        if comp[0] == '@':
                            #skip any attributes from 'srccomp' or 'dstcomp'
                            continue
                        #replace the element (tag) to search for
                        print ('tagAttrL',tagAttrL)
                        print ('comp',tagItem[comp])
                        
                        #if the subItems indicate a named composition use that
                        if subItems[0] != '*':
                            for x,tagAttr in enumerate(tagAttrL):
                                if tagAttr[1] == '*':
                                    tagAttr = [item for item in tagAttr]
                                    tagAttr[1] = comp
                                    tagAttrL[x] = tagAttr

                        self._CheckSubElements(tagAttrL, tagItem[comp], tagName, comp, paramD['parent'], session)
                elif tagName == 'node':
                    #special node for setting parameters when defining other processes                         
                    if not paramD['element'] in self.node.paramsD:
                        self.node.paramsD[paramD['element']] = {}
                        if not paramD['parent'] in self.node.paramsD[paramD['element']]:
                            self.node.paramsD[paramD['element']][paramD['parent']] = [] 
                    for node in tagItem:
                        if node[0] == '@':
                            #this the element and parent already set in the lines just above
                            continue
                        #reset node parameters to list
                        if not type(tagItem[node]) is list: 
                            tagItem[node] = [tagItem[node]]
                        for nodeD in tagItem[node]:
                            self._CheckSubElements(tagAttrL, nodeD, tagName, paramD['element'], paramD['parent'], session)
                       
                elif tagName == 'srcraw':    
                    #special tag for importing ancillary data                        
                    self.srcraw.paramsD[paramD['id']] = paramD
                elif tagName == 'dstcopy':    
                    #special tag for importing ancillary data                        
                    self.dstcopyD[paramD['band']] = paramD
                    
                else: # unrecognized pditem
                    exitstr = 'missing tag %s' %tagName
                    print (exitstr)
                    BALLE
                    exit(exitstr)

        #Check if srcperiod and dstperiod are set, if not set to overall period        
        if not hasattr(self, 'srcperiod'):
            self.srcperiodD = self.periodD
        if not hasattr(self, 'dstperiod'):
            self.dstperiodD = self.periodD
            
        if self.verbose:
            print ('    process:', self.processid)
            print ('    rootprocess:', self.rootprocid)
            print ('    system:')
            for key in self.systemD:
                printstr = '        %(k)s: %(v)s' %{'k':key, 'v':self.systemD[key]}
                print (printstr)       
            print ('    overwrite:', self.overwrite)
            print ('    delete:', self.delete)
            print ('    pipeline:', self.pipeline)
            print ('    source timestep:', self.srcperiodD['timestep'])
            print ('    destination timestep:', self.dstperiodD['timestep'])
            print ('    parameters:')
            for key in self.paramsD:
                printstr = '        %(k)s: %(v)s' %{'k':key, 'v':self.paramsD[key]}
                print (printstr)
            if hasattr(self, 'srcpathD'):
                print ('    source path:')
                for key in self.srcpathD:
                    printstr = '        %(k)s: %(v)s' %{'k':key, 'v':self.srcpathD[key]}
                    print (printstr)
            if hasattr(self, 'dstpathD'):
                print ('    destination path:')
                for key in self.dstpathD:
                    printstr = '        %(k)s: %(v)s' %{'k':key, 'v':self.dstpathD[key]}
                    print (printstr)  
            if self.srccompD:
                print ('    source compostions:')
                for key in self.srccompD:
                    printstr = '        %(k)s: %(v)s' %{'k':key, 'v':self.srccompD[key]}
                    print (printstr)
            if self.dstcompD:
                print ('    destination compostions:')
                for key in self.dstcompD:
                    printstr = '        %(k)s: %(v)s' %{'k':key, 'v':self.dstcompD[key]}
                    print (printstr)   
            if self.node.paramsD:
                print ('    node:')
                for key in self.node.paramsD:
                    printstr = '        %(k)s: %(v)s' %{'k':key, 'v':self.node.paramsD[key]}
                    print (printstr) 
            print ('\n')
            #if self.processid =='addsubproc':
            #    BALLE
            if self.processid =='organizeancillary': # and self.paramsD['subprocid'] == 'regioncategories':
                pass
        return True
            
    def _BoolTag(self, booltag):
        if booltag == '': 
            return False #i.e. no item given, assume False
        if booltag[0].lower() == 'n' or booltag.lower() == 'false':
            return False
        elif booltag[0].lower() == 'y' or booltag.lower() == 'true':
            return True
        else:
            warnstr = 'Can not resolve boolean node %(s)s - set to False' %{'s':booltag}
            print (warnstr)
            return False
        
    def _SetOverwriteDeletePipeline(self,pD):
        if 'overwrite' in pD:
            self.overwrite = self._BoolTag(pD['overwrite'] )
        else:
            self.overwrite = False
        if 'delete' in pD:
            self.delete = self._BoolTag(pD['delete'] )
        else:
            self.delete = False
        if 'pipeline' in pD:
            self.pipeline = self._BoolTag(pD['pipeline'] )
        else:
            self.pipeline = False

        
class MainProc:
    '''
    classdocs
    '''
    def __init__(self, proj, proc, session, verbose):
        """The constructor expects an instance of the composition class."""
        self.proj = proj
        self.proc = proc
        self.verbose = verbose
        self.session = session
        print ('senssion', self.session.name)
        
        #Set overwrite and delete
        self.delete = proc.delete
        self.overwrite = proc.overwrite
        self.pipeline = proc.pipeline
        #Set the system parameters, must always be included
        self.system = lambda: None
        for key in proc.systemD:
            setattr(self.system, key, proc.systemD[key])
            
        #Set the system parameters, must always be included
        self.params = lambda: None
        for key in proc.paramsD:
            setattr(self.params, key, proc.paramsD[key])
            
        if hasattr(proc, 'srcpathD'):
            self.srcpath = lambda: None
            for key in proc.srcpathD:
                setattr(self.srcpath, key, proc.srcpathD[key])
        if hasattr(proc, 'dstpathD'):
            self.dstpath = lambda: None
            for key in proc.dstpathD:
                setattr(self.dstpath, key, proc.dstpathD[key])    

        self._SetLocations()
        self._SetTimeSteps()
        self._SetCompositions(session)      
        self._SetLayers()

    def _SetTimeSteps(self):
        self.srcperiod = TimeSteps(self.proc.srcperiodD)
        self.dstperiod = TimeSteps(self.proc.dstperiodD)
  
    def _SetCompositions(self, session):
        '''
        '''
        self.srcCompD = {}
        self.dstCompD = {}
        self.compD = {}
        for comp in self.proc.srccompD:
            print ('before')
            if not 'system' in self.proc.srccompD[comp]:
                print ('THIS SHOULD BE BETTER DONE')
                self.proc.srccompD[comp]['system'] = self.proc.systemD['srcsystem']
                
            #print (self.proc.systemD['srcsystem'], self.proc.srccompD[comp]['system'])
            #BALLE
            #self.compD[comp] = session._SelectComp( self.proc.srccompD[comp] )
            self.compD[comp] = session._SelectComp(self.proc.systemD['srcsystem'], self.proc.srccompD[comp])
            print ('self.compD[comp]',self.compD[comp])

            self.srcCompD[comp] = Composition(self.compD[comp],self.proc.systemD['srcsystem'],self.proc.systemD['srcdivision'])
            print ('after')
            #DstcopyD is a special composition dictionary used only for Ancillary data
            if comp in self.proc.dstcopyD:
                self.proc.dstcompD[comp] = session._SelectComp(self.proc.systemD['srcsystem'], self.proc.srccompD[comp])
                
            
        '''   
        print ('dst',self.proc.dstcompD)
        print ('copy',self.proc.dstcopyD)
        #DstcopyD is a special composition dictionary used only for Ancilary data
        for comp in self.proc.dstcopyD:
            print ('self.proc.dstcopyD',self.proc.dstcopyD)
            print ('self.srcCompD',self.srcCompD)
            #Copy the srcCompD 
            self.proc.dstcompD[comp] = deepcopy(self.proc.srccompD[comp])
            print ('self.proc.dstcompD',self.proc.dstcompD)
        '''
        for comp in self.proc.dstcompD:
            #print ('comp',comp)
            self.dstCompD[comp] = Composition(self.proc.dstcompD[comp],self.proc.systemD['dstsystem'],self.proc.systemD['dstdivision'])
        #print (self.proc.srccompD)
        #print (self.srcCompD[comp])   

               
    def _SetLocations(self):
        '''
        '''

        self.srclocations = Location(self.proc.processid, self.proc.userProj.defregion, self.proc.systemD['srcsystem'], self.proc.systemD['srcdivision'],self.session)
        self.dstlocations = Location(self.proc.processid,self.proc.userProj.defregion, self.proc.systemD['dstsystem'], self.proc.systemD['dstdivision'],self.session)
 
    def _SetLayers(self):
        '''
        '''
        self.srcLayerD = {}
        self.dstLayerD = {}
        self._SetSrcLayers()
        self._SetDstLayers()
    
    def _SetSrcLayers(self):
        '''
        '''

        for locus in self.srclocations.locusL:
            self.srcLayerD[locus] = {}
            for datum in self.srcperiod.datumL:
                self.srcLayerD[locus][datum] = {}
                for comp in self.srcCompD:

                    #self.dstLayerD[locus][datum][comp] = {}
                    print (self.srcpath.hdrfiletype)
                    print ('comp',comp)
                    print ('self.srcLayerD[locus][datum]',self.srcLayerD[locus][datum])
                    print ('self.srcCompD[comp]',self.srcCompD[comp])
                    print ('self.srcCompD[comp]',self.srcCompD[comp].celltype)
                    
                    if self.srcCompD[comp].celltype in ['txt','csv','none']:
                        self.srcLayerD[locus][datum][comp] = TextLayer(self.srcCompD[comp], self.srclocations.locusD[locus], self.srcperiod.datumD[datum], self.srcpath)
                    elif 'shp' in self.srcpath.hdrfiletype:
                        self.srcLayerD[locus][datum][comp] = VectorLayer(self.srcCompD[comp], self.srclocations.locusD[locus], self.srcperiod.datumD[datum], self.srcpath)
                    else:
                        self.srcLayerD[locus][datum][comp] = RasterLayer(self.srcCompD[comp], self.srclocations.locusD[locus], self.srcperiod.datumD[datum], self.srcpath)
                    print (self.srcLayerD)
                    print (locus, datum, comp)

                    print (self.srcLayerD[locus][datum][comp].FPN)
                    
                    if not path.exists(self.srcLayerD[locus][datum][comp].FPN):
                        exitstr = 'EXITING, path does not exist: %(p)s' %{'p':self.srcLayerD[locus][datum][comp].FPN}
                        exit(exitstr)
               
    def _SetDstLayers(self):
        '''
        '''

        for locus in self.dstlocations.locusL:
            self.dstLayerD[locus] = {}
            for datum in self.dstperiod.datumL:

                self.dstLayerD[locus][datum] = {}
                for comp in self.dstCompD:
                    #self.dstLayerD[locus][datum][comp] = {}
                    if self.dstCompD[comp].celltype == 'vector':
                        self.dstLayerD[locus][datum][comp] = VectorLayer(self.dstCompD[comp], self.dstlocations.locusD[locus], self.dstperiod.datumD[datum], self.dstpath)
                    else:
                        self.dstLayerD[locus][datum][comp] = RasterLayer(self.dstCompD[comp], self.dstlocations.locusD[locus], self.dstperiod.datumD[datum], self.dstpath)
                    
                    '''
                    #self.srcLayerD[locus][datum][comp] = self.srcCompD[comp]
                    #self.dstLayerD[locus][datum][comp]['comp'] = self.dstCompD[comp]
                    if (self.dstLayerD[locus][datum][comp]['comp'].celltype == 'vector'):
                        self.dstLayerD[locus][datum][comp]['layer'] = VectorLayer(self.dstCompD[comp], self.dstlocations.locusD[locus], self.srcperiod.datumD[datum], self.dstpath)
                    else:
                        self.dstLayerD[locus][datum][comp]['layer'] = RasterLayer(self.dstCompD[comp], self.dstlocations.locusD[locus], self.srcperiod.datumD[datum], self.dstpath)
                    '''
