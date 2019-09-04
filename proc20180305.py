'''
Created on 7 mars 2018

@author: thomasgumbricht
'''

from geoimagine.kartturmain.timestep import TimeSteps
import geoimagine.support.karttur_dt as mj_dt
import geoimagine.gis.gis as mj_gis
from os import path, makedirs
from geoimagine.support.karttur_dt import Today
from geoimagine.postgresdb import ManageLayout

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
            warnstr = 'Can not resolve boolean node %(s)s - set to False' %{'s':booltag}
            print (warnstr)
            return False

def CheckSetParamValues(tagAttrL, xmlOD, xml):
    '''
    '''
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

        if item[3].lower()[0] in ['y','t']:
            if xmlOD == None:
                warnstr = '        Warning: The required parameter "%(p)s" (%(s)s) is lacking in tag "%(t)s"'  %{'p':item[1],'s':s,'t':item[6]}
                print (warnstr)
                print ('This can depend on errors in srcpath or dstpath, e.g. the use of "tar" instead of "dst", or src instead of dst!')
                exit()
            if not s in xmlOD:
                errorD[item[1]] = item
                flagga = False
                warnstr = '    Warning: The required parameter "%(p)s" (%(s)s) is lacking in tag "%(t)s" in \n    %(xml)s'  %{'p':item[1],'s':s,'t':item[6], 'xml':xml}
                print (warnstr)
                SNULLE
                exit()
            else:
                value = xmlOD[s] 
        elif xmlOD == None:
            value = item[4]
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
    '''Functions common to all layers
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

    def _SetPath(self):
        """Sets the complete path to the file"""
        self.FN = '%(prefix)s_%(prod)s_%(reg)s_%(d)s_%(suf)s%(e)s' %{'prefix':self.comp.prefix,'prod':self.comp.product,'reg':self.locus.locus, 'd':self.datum.acqdatestr, 'suf':self.comp.suffix,'e':self.path.ext}            
        if self.movieframe:
            self.FP = path.join('/Volumes',self.path.volume, self.comp.system, self.comp.source, self.comp.division, self.comp.folder, self.locus.path, 'images')
        elif self.movieclock:
            self.FP = path.join('/Volumes',self.path.volume, self.comp.system, self.comp.source, self.comp.division, self.comp.folder, self.locus.path, 'clock')
        else:
            self.FP = path.join('/Volumes',self.path.volume, self.comp.system, self.comp.source, self.comp.division, self.comp.folder, self.locus.path, self.datum.acqdatestr)
   
        self.FPN = path.join(self.FP,self.FN)
        if ' ' in self.FPN:
            exitstr = 'EXITING FPN contains space %s' %(self.FPN)
            exit(exitstr)
         
    def _Register(self,session):
        pass
            
class Layer(LayerCommon):
    """Layer is the parentid class for all spatial layers."""
    def __init__(self, composition, locusD, datumD, filepath, movieframe = False, movieclock = False): 
        """The constructor expects an instance of the composition class."""

        LayerCommon.__init__(self)
        self.movieframe = movieframe
        self.movieclock = movieclock

        self.comp = composition

        #THE FOLLOWING IS REDUNDANT AND I CANNOT REMEMBER WHY AND WHEN I DID THIS
        if not 'system' in locusD:
            locusD['system'] = self.comp.system

        if not 'division' in locusD:
            locusD['division'] = self.comp.division

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
     
class VectorLayer(Layer):
    '''Class for vector data layer
    '''
    def __init__(self, comp, locusD, datumD, filepath): 
        '''Constructor expects a composition, a locus a date and a filepath
        '''
        Layer.__init__(self, comp, locusD, datumD, filepath)
        if not 'shp' in filepath.hdrfiletype.lower():
            
            print ('Error in hdrfiletype for vector file',filepath.hdrfiletype)
            exit()
    def CreateVectorAttributeDef(self,fieldDD): 
        '''Vector attribute table definition
        '''
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
     
    def OpenVector(self):
        '''Open existing vector file
        '''
        srcDS,srcLayer = mj_gis.ESRIOpenGetLayer(self.FPN)
        for feature in srcLayer.layer:
            geom = mj_gis.Geometry()
            #add the feature and extract the geom
            geom.GeomFromFeature(feature)
            
    def _GetBounds(self):
        srcDS,srcLayer,fieldDefL = mj_gis.ESRIOpenGetLayer(self.FPN,'read')
        
        self.spatialRef = mj_gis.MjProj()
        self.spatialRef.SetProj(srcLayer.spatialRef)
        for feature in srcLayer.layer:
            geom = mj_gis.Geometry()
            #add the feature and extract the geom
            geom.GeomFromFeature(feature)
            self.minx, self.miny, self.maxx, self.maxy = geom.shapelyGeom.bounds
        self.spatialRef.ReadSpatialRef()
        
        self.BoundsPtL = ( (self.minx,self.maxy),(self.maxx,self.maxy),(self.maxx,self.miny), (self.minx,self.miny) )

            
class SVGLayer(Layer):
    '''Class for vector data layer
    '''
    def __init__(self, comp, locusD, datumD, filepath): 
        '''Constructor expects a composition, a locus a date and a filepath
        '''
        Layer.__init__(self, comp, locusD, datumD, filepath)
        if not 'svg' in filepath.hdrfiletype.lower():
            
            print ('Error in hdrfiletype for vector file',filepath.hdrfiletype)
            exit()
            
class MapLayer(Layer):
    '''Class for vector data layer
    '''
    def __init__(self, comp, locusD, datumD, filepath): 
        '''Constructor expects a composition, a locus a date and a filepath
        '''
        Layer.__init__(self, comp, locusD, datumD, filepath)
        if filepath.hdrfiletype.lower() not in ['png','pdf','html','show']:     
            print ('Error in hdrfiletype for map lyaout file',filepath.hdrfiletype)
            exit()
      
class RasterLayer(Layer):
    '''Class for raster data layer
    '''
    def __init__(self, comp, locusD, datumD, filepath):
        '''Constructor expects a composition, a locus a date and a filepath
        ''' 
        Layer.__init__(self, comp, locusD, datumD, filepath)
        
    def GetRastermetadata(self):
        #TGTODO THIS AND NEXT MUST BE REDUNDANT- NO IT IS JUST IN IMPORT OF ANCIAARY
        self.spatialRef, self.metadata = mj_gis.GetRasterMetaData(self.FPN)
        #transfer cellnull and celltype to composition
        self.comp.spatialRef = self.spatialRef
        self.comp.metadata = self.metadata
             
    def ReadRasterLayer(self,**kwargs):
        readD = {'mode':'edit','complete':True,'flatten':True}
        if kwargs is not None:
            for key, value in kwargs.items():
                readD[key] = value
        self.layer =  mj_gis.ReadRasterArray(self.FPN, readD)
     
    def CreateDstLayer(self,**kwargs):
        writeD = {'mode':'edit','complete':True,'flatten':True}
        if kwargs is not None:
            for key, value in kwargs.items():
                writeD[key] = value
        self.layer =  mj_gis.RasterCreateWithFirstLayer(self.FPN, writeD)
     
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
      
    def ReadSrcLayer(self):
        ''' Opens and reads a complete raster file, and reads the geoformat, file is then closed'''
        self.ReadRasterLayer(complete= True, flatten = False, mode='edit')

    def CopyGeoformatFromSrcLayer(self,otherLayer):
        '''Direct copy of geoformat from srcLayer to dstLayer
        '''
        if not hasattr(self,'layer'):
            self.layer = lambda:None
        itemL = ['lins','cols','projection','geotrans','cellsize']
        for item in itemL:
            setattr(self.layer, item, getattr(otherLayer,item))
        
    def DeleteLayer(self):
        pass
    
class MovieFrame(Layer):  
    '''Class for movieframe as layer
    '''
    def __init__(self, comp, locusD, datumD, filepath): 
        Layer.__init__(self, comp, locusD, datumD, filepath, True)
           
class MovieClock(Layer): 
    '''Class for movieclock frame as layer
    ''' 
    def __init__(self, comp, locusD, datumD, filepath): 
        Layer.__init__(self, comp, locusD, datumD, filepath, False, True)
     
class RegionLayer(Layer): 
    '''Class for regional (arbitary) layer
    '''
    def __init__(self,comp, location, datum): 
        """The constructor expects an instance of the composition class."""
        Layer.__init__(self, comp, datum)
        
        self.layertype = 'region'
        self.location = lambda: None
        
        self.location.regionid = location
        
        #Set the filename and path
        self.SetRegionPath()
                
    def _SetRegionPathOld(self):
        """Sets the complete path to region files"""

        self.FN = '%(prefix)s_%(prod)s_%(reg)s_%(d)s%(suf)s%(e)s' %{'prefix':self.comp.prefix,'prod':self.comp.product,'reg':self.location.regionid, 'd':self.datum.acqdatestr, 'suf':self.comp.suffix,'e':self.comp.ext}            
        if self.movieframe:
            self.FP = path.join(self.comp.mainpath, self.comp.source, self.comp.division, self.comp.folder, self.location.regionid)
        else:
            self.FP = path.join(self.comp.mainpath, self.comp.source, self.comp.division, self.comp.folder, self.location.regionid, self.datum.acqdatestr)

        self.FPN = path.join(self.FP,self.FN)
        if ' ' in self.FPN:
            exitstr = 'EXITING region FPN contains space %s' %(self.FPN)
            exit(exitstr)
   
class TextLayer(Layer):
    '''Class for non-spatial (text) layer
    '''
    def __init__(self, comp, locusD, datumD, filepath): 
        Layer.__init__(self, comp, locusD, datumD, filepath)
                      
class Location:
    '''Class for defining spatial data framework location
    '''
    def __init__(self, paramsD, processid, siteid, tractid, defregid, system, division, session): 
        self.defregid = defregid
        self.system = system
        self.division = division
        self.locusD = {}
        self.locusL = []
        if division in ['NA','none','None','na']:
            #No spatial data involved
            pass
        elif division == 'region':
            self.locusL.append(self.defregid)
            self.locusD[self.defregid] = {'locus':self.defregid, 'path':self.defregid, 'system':system, 'division':division}

        elif division == 'tiles' and system.lower() in ['modis','export','archive']:
            from geoimagine.support.modis import ConvertMODISTilesToStr as convTile
            if 'singletile' in processid.lower():
                tiles = [(paramsD['htile'],paramsD['vtile'])]
            else:
                tiles = session._SelectModisRegionTiles({'siteid':siteid,'tractid':tractid,'regionid':self.defregid})

            for tile in tiles:
                hvD = convTile(tile)
                tilepath = path.join(hvD['pstr'],hvD['rstr'])
                self.locusL.append(hvD['prstr'])
                self.locusD[hvD['prstr']] = {'locus':hvD['prstr'], 'path':tilepath,'htile':hvD['p'],'vtile':hvD['r'], 'system':system, 'division':division}

        elif division == 'tiles' and system.lower() == 'sentinel' and processid[0:7] in ['downloa', 'explode','extract','geochec','findgra','reorgan']:
            self.locusL.append('unknwon')
            self.locusD['unknown'] = {'locus':'unknwon', 'path':'unknwon', 'system':system, 'division':division}
        elif division == 'scenes' and system.lower() == 'landsat' and processid[0:7] in ['downloa', 'explode','extract','geochec','findgra','reorgan']:
            self.locusL.append('unknwon')
            self.locusD['unknown'] = {'locus':'unknwon', 'path':'unknwon', 'system':system, 'division':division}
        
        elif division == 'scenes' and system.lower() == 'landsat' :
            from geoimagine.support.landsat import ConvertLandsatScenesToStr as convScene
            if 'singlescene' in processid.lower():
                scenes = [(paramsD['wrspath'],paramsD['wrsrow'])]
            else:
                scenes = session._SelectLandsatRegionScenes({'siteid':siteid,'tractid':tractid,'regionid':self.defregid})
                
            for scene in scenes:
                prD = convScene(scene)
                scenepath = path.join(prD['pstr'],prD['rstr'])
                self.locusL.append(prD['prstr'])
                self.locusD[prD['prstr']] = {'locus':prD['prstr'], 'path':scenepath,'wrspath':prD['p'],'wrsrow':prD['r'], 'system':system, 'division':division}


            '''
            elif division == 'scenes' and system.lower() == 'landsat' :
                self.locusL.append('unknown')
                self.locusD['unknown'] = {'locus':'unknwon', 'path':'unknwon', 'system':system, 'division':division}
            '''
        else:
            print ('add division, system', division, system, processid)
            exit('kartturmain.procYYYYMMDD class Location')

class Composition:
    '''Class for defining framework file path and name
    '''
    def __init__(self, compD, system, division):
        self.checkL  = ['source','product','folder','band','prefix','suffix']

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
                    exitstr = 'the "%s" parameter can not contain underscore (_): %s ' %(key, compD[key])
                    exit(exitstr) 
            setattr(self, key, compD[key])
       
    def _CreatePalette(self):
        if not hasattr(self, 'palette'):
            self.palette = False
        elif not self.palette:
            pass
        else:  
            if self.palette == 'default':
                self.palette = self.compid
            session = ManageLayout()
            if self.palette == 'default':
                query = {'compid':self.compid}
                self.palettename = session._SelectCompDefaultPalette(query)
                if self.palettename == None:
                    exitstr = 'No default palette for compid %(c)s' %{'c':self.compid}
                    exit(exitstr)
            else:
                self.palettename = self.palette
            query = {'palette':self.palettename}
            paramL = ['value','red','green','blue','alpha','label','hint']
            self.colorRamp = session._SelectPaletteColors(query,paramL)
            session._Close() 

class UserProj:
    '''Class for identifying user, project and location
    '''
    def __init__(self, userprojD,tagAttrL,xml):
        '''Constructor expects a dict, a list and the name of the source xml
        '''
        self.userprojD = CheckSetParamValues(tagAttrL, userprojD, xml)[0]
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

        if not self.projectid in self.userProjs:
            exitstr = 'No project %(p)s owned by user %(u)s\n    projects owned by user: %(l)s' \
            %{'p':self.projectid, 'u':self.userid, 'l':self.userProjs}
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
                warnstr = 'No tract %(t)s owned by user %(u)s\n    tracts owned by user: %(l)s' \
                %{'t':self.tractid, 'u':self.userid, 'l':self.userTracts}
                exit(warnstr)
                print (warnstr)
                return False        
        return True

    def _GetDefRegion(self,session):
        '''Sets the default region
        '''
        if self.tractid:
            self.defregion, self.defregtype = session._SelectTractDefRegion(self.tractid)

        elif self.siteid:
            exit('add site defregion')
        if self.defregion == 'globe':
            exit('globe is not allowed')
        #TGTODO Check if user has the right to this region

class SetXMLProcess:
    '''Converts xml codes to framework processes
    '''
    def __init__(self, userProj, processid, content, session, xml, verbose):
        '''
        The constructor sets the userProj (class) and the overall periodD
        '''
        self.userProj = userProj
        self.processid = processid
        self.verbose = verbose
        self.xml = xml
        
        tagAttrL = session._SelectProcessTagAttr('periodicity','process','period') 
        if 'period' in content:
            period = content['period']
            self.periodD = CheckSetParamValues(tagAttrL, period,xml)[0]    
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
        '''Check if the element contains any sub element
        '''
        #tagAttrL, tagItem[comp], tagName, paramD['parent'], session
        for tagAttr in tagAttrL:
            if tagAttr[0] == 'E':
                #this can only be the setvalues or minmax under the the node tag 
                subTagAttrL = session._SelectProcessTagAttr(self.processid,tagAttr[6],tagAttr[1])
                if len(subTagAttrL) == 0:
                    print ('subTagAttrL',subTagAttrL)
                    exit('kartturmain.procYYYYMMDD _CheckSubElements')
                if type(element) is list:
                    for itm in element:
                        paramD, subItems = CheckSetParamValues(subTagAttrL, itm, self.xml)
                        if tagName == 'transformoffset':
                            setattr(self.transformoffset, paramD['id'], paramD)
                        elif tagName == 'transformscale':
                            setattr(self.transformscale, paramD['id'], paramD)
                        #the possible subelements

                        elif tagName == 'node':   
                            if 'setvalue' in itm:
                                paramD['setvalue'] = CheckSetValue(itm['setvalue'])
                            if 'minmax' in itm:
                                paramD['minmax'] = CheckSetMinMax(itm['minmax'])
                            self.node.paramsD[paramName][nodeparent].append(paramD)
                        else:
                            exitstr ='Unknown listed sub tag "%s"' %(tagName)
                            print (exitstr)
                            exit('kartturmain.procYYYYMMDD _CheckSubElements')        
                else:
                    paramD, subItems = CheckSetParamValues(subTagAttrL, element, self.xml)
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
                    elif tagName == 'srccomp' or tagName.split('-')[0] == 'srccomp':
                        print ('fucking paramname',paramName)
                        if paramName == paramD['band']: 
                            self.srccompD[paramName] = paramD
                        elif '--' in paramName and paramName.split('--')[0] == paramD['band']:

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
                        FNISAA
                        exit(exitstr)

    def _CheckParams(self, processD, session):
        '''Checks given parameters against database entries
        '''
        print ('_CheckParams',processD)
        #Create all the variables and dictionaries
        self.dstcompD = {}
        self.dstcopyD = {}
        self.srccompD = {}
        self.replaceD = {}
        self.paramsD = {'creator': self.userProj.userid, 'today': Today()}        
        self.node = lambda: None
        self.node.paramsD = {}

        #self.system is only for addsubproc
        self.system = lambda: None
        self.system.paramD = {}
        
        #self.systemD is the process itself
        self.systemD = {}
        
        self.srcraw = lambda: None
        self.srcraw.paramsD = {}
        
        self.stats = lambda: None
        self.stats.paramsD = {}
        
        self.comp = lambda: None
        self.comp.paramsD = {}
        
        self.index = lambda: None
        self.index.paramsD = {}
        
        self.xy = lambda: None
        self.xy.paramsD = {}
        
        self.resolfac = lambda: None
        self.resolfac.paramsD = {}
        
        self.metadef = lambda: None
        self.metadef.paramsD = {}
        
        self.transformoffset = lambda: None
        
        self.transformscale = lambda: None

        #get the rooprocid of the process
        query ={'subprocid':self.processid}

        self.rootprocid = session._SelectRootProcess(query)[0]  
        #Check and set system setting (the overall system, the source division and the destination division)
        systemsettings = session._SelectProcessSystems(query)
        sysOK = False
        systemParams = ['system', 'srcsystem', 'dstsystem', 'srcdivision', 'dstdivision']

        for procsys in systemsettings:
            if procsys[0] == self.userProj.system:
                sysOK = True
                self.systemD = dict(zip(systemParams, procsys))
        if not sysOK:
            print ('systemsettings',systemsettings)
            print ('self.userProj.system',self.userProj.system)
            exitstr = 'kartturmain.proc20180305-_CheckParams: The process %s can not be run on the system: %s' %(self.processid, self.userProj.system)   
            exit(exitstr)


        #Set the boolean variables common to all processes
        self._SetOverwriteDeletePipeline(processD)

        #Loop over all tags in the process
        for tagName in processD:
            if tagName[0] == '@':
                #process attributes are already processed
                continue
            if tagName in ['overwrite','delete','update','pipeline','acceptmissing']:
                continue
            
            #replacetag is for importing series data and can be anything, just skip here
            if 'replacetag' in self.paramsD and tagName == self.paramsD['replacetag']:
                self.replaceD = {}
                for item in processD[tagName]:
                    if item == '@type':
                        key = processD[tagName][item]
                        self.replaceD[key] = {}
                    else:
                        self.replaceD[key][item] = processD[tagName][item]
                continue

            #Get the expected variables from the db
            tagAttrL = session._SelectProcessTagAttr(self.processid,'process',tagName)

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
                paramD,subItems = CheckSetParamValues(tagAttrL, tagItem,self.xml)
                if tagName == 'parameters':
                    self.paramsD = paramD
                    self.paramsD['creator'] = self.userProj.userid 
                    self.paramsD['today'] = Today() 
                    self.subparamsD = {}
                    if tagItem != None: #None is when the parameter tag i empty
                        for col in tagItem:
                            if col[0] == '@' or col in ['title','label','suberrortext','rooterrortext',
                                                        'projtitle','projlabel','tracttitle','tractlabel']:
                                #skip any attributes, only get subitems
                                continue
                            self.subparamsD[col] = {}
                            subTagAttrL = session._SelectProcessTagAttr(self.processid,tagName,col)
                            if type(tagItem[col]) is list:
                                for itm in tagItem[col]:
                                    paramD, subItems = CheckSetParamValues(subTagAttrL, itm, self.xml)
                                    self.subparamsD[col][paramD['id']] = paramD
                            else:
                                paramD, subItems = CheckSetParamValues(subTagAttrL, tagItem[col])
                                self.subparamsD[col][paramD['id']] = paramD

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
                elif tagName in ['srccomp','dstcomp'] or tagName.split('-')[0] == 'srccomp':
                    for comp in tagItem:
                        if comp[0] == '@':
                            #skip any attributes from 'srccomp' or 'dstcomp'
                            continue
                        #replace the element (tag) to search for

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
                elif tagName == 'stats':    
                    #special tag for importing ancillary data                        
                    self.stats.paramsD[paramD['id']] = paramD 
                elif tagName == 'comp':    
                    #special tag for compositions                        
                    self.comp.paramsD[paramD['id']] = paramD 
                elif tagName == 'index':    
                    #special tag for indexes                       
                    self.index.paramsD[paramD['id']] = paramD
                elif tagName == 'resolfac':    
                    #special tag for indexes                       
                    self.resolfac.paramsD[paramD['id']] = paramD
                elif tagName == 'xy':    
                    #special tag for xy coord extract/plot                       
                    self.xy.paramsD[paramD['id']] = paramD
                elif tagName in ['transformoffset', 'transformscale']:   
                    #special tag for image lineratransform data  
                    for comp in tagItem:
                        if comp[0] == '@':
                            #skip any attributes from 'srccomp' or 'dstcomp'
                            continue
                        self._CheckSubElements(tagAttrL, tagItem[comp], tagName, comp, paramD['parent'], session)                       
                elif tagName == 'column':       
                    #special tag for columns defining meta data for landsat collections                       

                    self.metadef.paramsD[paramD['column']] = paramD
                else: # unrecognized pditem
                    exitstr = '    EXITING: Unknown tag found: "%s"' %tagName
                    exit(exitstr)

        #Check if srcperiod and dstperiod are set, if not set to overall period        

        if not hasattr(self, 'srcperiod'):      
            self.srcperiodD = deepcopy(self.periodD) 
        if not hasattr(self, 'dstperiod'):
            self.dstperiodD = deepcopy(self.periodD)
            #self.srcperiodD = self.periodD
        if not hasattr(self, 'dstperiod'):
            self.dstperiodD = deepcopy(self.periodD)
            
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

            if self.processid =='organizeancillary': # and self.paramsD['subprocid'] == 'regioncategories':
                pass
        return True
                
    def _SetOverwriteDeletePipeline(self,pD):
        if 'overwrite' in pD:
            self.overwrite = BoolTag(pD['overwrite'] )
        else:
            self.overwrite = False
        if 'delete' in pD:
            self.delete = BoolTag(pD['delete'] )
        else:
            self.delete = False
        if 'update' in pD:
            self.update = BoolTag(pD['update'] )
        else:
            self.update = False
        if 'pipeline' in pD:
            self.pipeline = BoolTag(pD['pipeline'] )
        else:
            self.pipeline = False
        if 'acceptmissing' in pD:
            self.acceptmissing = BoolTag(pD['acceptmissing'] )
        else:
            self.acceptmissing = False
        
class MainProc:
    '''
    classdocs
    '''
    def __init__(self, proc, session, verbose):
        """The constructor expects an instance of the composition class."""

        self.proc = proc
        self.verbose = verbose
        self.session = session
        if self.verbose > 1:
            print ('db session:', self.session.name)
        
        #Set overwrite and delete
        self.delete = proc.delete
        self.overwrite = proc.overwrite
        self.update = proc.update
        self.pipeline = proc.pipeline
        #Set the system, must always be included
        self.system = lambda: None
        for key in proc.systemD:
            setattr(self.system, key, proc.systemD[key])
            
        #Set the parameters, must always be included
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
         
        if self.verbose > 1:          
            print ('SETTING LOCATIONS')
        self._SetLocations()
        if self.verbose > 1:
            print ('SETTING TIMESTEPS')
        self._SetTimeSteps()
        if self.verbose > 1:
            print ('SETTING COMPOSITIONS')
        self._SetCompositions()  
 
        if self.verbose > 1:
            print ('SETTING LAYERS')
        self._SetLayers()
        if self.verbose > 1:
            print ('FINISHED MAINPROC')
        
    def _SetTimeSteps(self):
        self.srcperiod = TimeSteps(self.proc.srcperiodD)
        self.dstperiod = TimeSteps(self.proc.dstperiodD)

    def _SetCompositions(self):
        '''
        '''
        self.srcCompD = {}
        self.dstCompD = {}
        self.compD = {}
        
        if self.verbose > 1:
            print ('    db session:',self.session.name)
        if 'seasonfill' in self.proc.processid.lower():
            self.proc.srccompD['season'] = {}  
        
        self.srcIdDict = {}
        
        for comp in self.proc.srccompD:
            if 'id' in self.proc.srccompD[comp]:  
                self.srcIdDict[self.proc.srccompD[comp]['id']] = comp 
                  
        for srccomp in self.proc.srccompD:
            #THIS SHOULD BE BETTER 
            if not 'system' in self.proc.srccompD[srccomp]:
                if self.proc.systemD['srcsystem'] in ['export']:
                    #export does not exists as system, only as folder
                    self.proc.srccompD[srccomp]['system'] = self.proc.systemD['system']
                else:
                    self.proc.srccompD[srccomp]['system'] = self.proc.systemD['srcsystem']

            self.compD[srccomp] = self.session._SelectComp(self.proc.srccompD[srccomp])
       
            self.srcCompD[srccomp] = Composition(self.compD[srccomp],self.proc.systemD['srcsystem'],self.proc.systemD['srcdivision'])
            if 'copycomp' in self.proc.paramsD:
                self._SetDstComp(srccomp)
                
            #Update scrCompD with id if that is included
            if 'id' in self.proc.srccompD[srccomp]:
                self.srcCompD[srccomp]._Update({'id':self.proc.srccompD[srccomp]['id']})
              
            #DstcopyD is a special composition dictionary used only for Ancillary data
            if comp in self.proc.dstcopyD:
                self.proc.dstcompD[comp] = self.session._SelectComp(self.proc.srccompD[comp])

        if len(self.proc.srccompD) == 0 and 'copycomp' in self.proc.paramsD:

            if self.proc.paramsD['copycomp'] == 'systemregion':
                locus = self.proc.userProj.defregion
                #print ('locus',locus)
                compid = '%(f)s_%(b)s' %{'f':'defaultregions','b':'roi'}
                comp = {'system':'system','folder':'defaultregions', 'band':'roi'}
                comp = self.session._SelectComp('system',comp)
                #print ('comp',comp)
                self.proc.srccompD[compid] = comp
                #print ('comp',comp)
                self.srcCompD[compid] = Composition(comp,self.proc.systemD['srcsystem'],self.proc.systemD['srcdivision'])

                queryD = {'regionid':locus}
                paramL = ['compid','source','product','suffix','acqdate','acqdatestr','regionid']
                layerStuff = self.session._SelectLayerOnLocus('system',queryD,paramL)
                                
        for comp in self.proc.dstcompD: 
            self.dstCompD[comp] = Composition(self.proc.dstcompD[comp],self.proc.systemD['dstsystem'],self.proc.systemD['dstdivision'])

        if hasattr(self,'extraSrcCompD'):
            for comp in self.extraSrcCompD:
                self.proc.srccompD[comp] = self.extraSrcCompD[comp]
                self.srcCompD[comp] = Composition(self.proc.srccompD[comp],self.proc.systemD['srcsystem'],self.proc.systemD['srcdivision'])

    def _SetDstComp(self,srccomp):
        '''
        '''
        def _tractProject():
            dstcomp = srccomp
            self._ReplaceComp(srccomp,dstcomp)
            self.proc.dstcompD[dstcomp]['band'] = self.proc.dstcompD[dstcomp]['prefix'] = 'roi'
            self.proc.dstcompD[dstcomp]['product'] = self.proc.userProj.userid
            self.proc.dstcompD[dstcomp]['folder'] = 'tracts'
            #For the tractproject, it is the tract itelsf that is the system region
            self.dstlocations = Location(self.proc.paramsD, self.proc.processid, self.proc.userProj.siteid, self.proc.userProj.tractid, self.proc.paramsD['tractid'], self.proc.systemD['dstsystem'], self.proc.systemD['dstdivision'],self.session)
        
        def _movie():
            dstcomp = srccomp
            #Celltype only determines how to set the path, and need to be set to these inconsisten values here!!!
            #DO NOT CHANGE
            self.proc.dstcompD[dstcomp] = {'celltype':self.proc.paramsD['copycomp']}                
            self.proc.srccompD[srccomp]['system'] = 'export'
            #RESET THE src SYSTM
            self.srcCompD[srccomp] = Composition(self.compD[srccomp],'export',self.proc.systemD['srcdivision'])
            self._ReplaceComp(srccomp,dstcomp)
            #Set the srcIdDict['base']
            self.srcIdDict['base'] = srccomp
        
        def _template():

            template = self.proc.paramsD['template'] 
            dstcompL = list(self.proc.dstcompD.keys())
            
            for dstcomp in dstcompL:
                newcompD = {}
                for item in self.compD[srccomp]:
                    if item in self.proc.dstcompD[dstcomp] and self.proc.dstcompD[dstcomp][item] not in ['src',-2222]:
                        newcompD[item] = self.proc.dstcompD[dstcomp][item]
                    else:
                        newcompD[item] = self.compD[srccomp][item]
                #Replace the dstcomp
                if 'id' in self.proc.dstcompD[dstcomp]:
                    newcompD['id'] = self.proc.dstcompD[dstcomp]['id']
                self.proc.dstcompD[dstcomp] = newcompD
                
        

        def _anytoall():
            for dstcomp in self.proc.dstcompD:
                newcompD = {}
                for item in self.proc.dstcompD[dstcomp]:
                    newcompD[item] = self.proc.dstcompD[dstcomp][item]

                for item in self.compD[srccomp]:
                    if item in self.proc.dstcompD[dstcomp] and self.proc.dstcompD[dstcomp][item] not in ['src',-2222]:
                        newcompD[item] = self.proc.dstcompD[dstcomp][item]
                    else:
                        newcompD[item] = self.compD[srccomp][item]
                #Replace the dstcomp
                if 'id' in self.proc.dstcompD[dstcomp]:
                    newcompD['id'] = self.proc.dstcompD[dstcomp]['id']
                    #self.dstCompD[comp]._Update({'id':self.proc.dstcompD[comp]['id']})
                self.proc.dstcompD[dstcomp] = newcompD
            #Set to pass once done
            self.proc.paramsD['copycomp'] = 'pass' 
            
        def _archive():
            dstcomp = srccomp
            newcompD = {}
            for item in self.compD[srccomp]:
                newcompD[item] = self.compD[srccomp][item]
            self.proc.dstcompD[dstcomp] = newcompD
            
        def _exporttobyte():
            dstcomp = srccomp
            newcompD = {}
            for item in self.compD[srccomp]:
                newcompD[item] = self.compD[srccomp][item]
            newcompD['celltype'] = 'Byte'
            newcompD['cellnull'] = 255
            self.proc.dstcompD[dstcomp] = newcompD
            
        def _exportmap():
            dstcomp = srccomp
            newcompD = {}
            for item in self.compD[srccomp]:
                newcompD[item] = self.compD[srccomp][item]
            newcompD['celltype'] = 'map'
            newcompD['cellnull'] = 255
            self.proc.dstcompD[dstcomp] = newcompD
            
        def _exportSvg():
            dstcomp = srccomp
            newcompD = {}
            for item in self.compD[srccomp]:
                newcompD[item] = self.compD[srccomp][item]
            newcompD['celltype'] = 'svg'
            newcompD['suffix'] = self.proc.paramsD['suffix']

            self.proc.dstcompD[dstcomp] = newcompD
 
            #if self.proc.paramsD['dst_region'] != 'None': 
            #self.proc.userProj.defregion = self.proc.paramsD['dst_region']
            #paramsD, processid, siteid, tractid, defregid, system, division, session
            self.srclocations = Location(self.proc.paramsD, self.proc.processid, False, False, self.proc.paramsD['src_region'], self.proc.systemD['srcsystem'], self.proc.systemD['srcdivision'],self.session)
            
            
        def _seasonalts():
            newcompD = {}
            for item in self.compD[srccomp]:
                newcompD[item] = self.compD[srccomp][item]
            newcompD['folder'] = '%s-sesn' %(newcompD['folder'])
            if len(newcompD['folder']) > 32:
                exitstr = 'Season folder name is too long: %s' %(newcompD['folder'])
                EXITAGAIN
            #Reset the dst peridod
            self.proc.dstperiodD['seasonalts'] = True
            self.dstperiod = TimeSteps(self.proc.dstperiodD)
        
            #Create the dstcomp
            #self.dstCompD[comp] = newcompD
            self.proc.dstcompD[srccomp] = newcompD
            
        def _DtoMdataunits():
            newcompD = {}
            dstcomp = list(self.proc.dstcompD.keys())[0]             
            for item in self.proc.dstcompD:
                if item in self.proc.dstcompD[dstcomp] and self.proc.dstcompD[dstcomp][item]  not in ['src',-2222]:
                    newcompD[item] = self.proc.dstcompD[dstcomp][item]
                else:
                    newcompD[item] = self.compD[srccomp]
                    
        def _applystaticmask():
            #Copy the srcComp to dstcomp
            if self.proc.srccompD[srccomp]['id'] == 'layer':
                dstcomp = list(self.proc.dstcompD.keys())[0]
                for item in self.compD[srccomp]:
                    if item in self.proc.dstcompD[dstcomp] and self.proc.dstcompD[dstcomp][item] not in  ['src', '**', -2222]:
                        pass
                    else:
                        self.proc.dstcompD[dstcomp][item] = self.compD[srccomp][item] 
                if self.proc.dstcompD[dstcomp]['suffix'] == 'auto':
                    self.proc.dstcompD[dstcomp]['suffix'] = '%(s)s-mask' %{'s':self.proc.srccompD[srccomp]['suffix']}

                if len(self.proc.dstcompD[dstcomp]['suffix']) > 32:
                    exitstr = 'suffix is too long: %s' %(self.proc.dstcompD['suffix'])
                    exit(exitstr)
                    
        def _subtractseason():
            if self.proc.srccompD[srccomp]['id'] == 'layer':
                dstcomp = list(self.proc.dstcompD.keys())[0]    
                for item in self.compD[srccomp]:         
                    if item in self.proc.dstcompD[dstcomp] and self.proc.dstcompD[dstcomp][item]  not in ['src',-2222]:
                        pass
                    else:
                        self.proc.dstcompD[dstcomp][item] = self.compD[srccomp][item] 
                                                   
        def _gdaaltranslate():
            #Reset dstlocations, unless dst_region is not set (default = 'None')
            if self.proc.paramsD['dst_region'] != 'None': 
                self.proc.userProj.defregion = self.proc.paramsD['dst_region']
                self.dstlocations = Location(self.proc.paramsD, self.proc.processid,self.proc.userProj.defregion, self.proc.systemD['dstsystem'], self.proc.systemD['dstdivision'],self.session)
        
        def _seasonfillts():
            #equals 1 to 1 but with forced naming of folder for dst
            #And then creates a second src comp
            dstcomp = srccomp
            newcompD = {}
            for item in self.compD[srccomp]:
                newcompD[item] = self.compD[srccomp][item]
            newcompD['folder'] = '%s-fill' %(newcompD['folder'])
            if len(newcompD['folder']) > 32:
                exitstr = 'Fill folder name is too long: %s' %(newcompD['folder'])
                print (exitstr)
                EXITAGAIN
            self.proc.dstcompD[dstcomp] = newcompD 
            #Create a second source period (for the season)
            newcompD = {}
            for item in self.compD[srccomp]:
                newcompD[item] = self.compD[srccomp][item]
            newcompD['folder'] = '%s-sesn' %(newcompD['folder'])
            self.proc.seasonperiodD = {}
            for item in self.proc.srcperiodD:
                self.proc.seasonperiodD[item] = self.proc.srcperiodD[item]
            self.proc.seasonperiodD['seasonalts'] = True
            self.seasonperiod = TimeSteps(self.proc.seasonperiodD)
            #Create the srccomp for season
            self.proc.srccompD['season'] = newcompD
            
        def _setassimilation():
            if self.proc.srccompD[srccomp]['id'] == 'master':
                return
            #dst compostions set after the slave to be assimilated to the master
            #The assimialtion requires three files:
            #slave termporal average
            #master temporal average
            #master over slave standard deviation
            if self.proc.srccompD[srccomp]['folder'][-5:-1] == '-ses':
                folder = '%(f)s-assim' %{'f':self.proc.srccompD[srccomp]['folder'][0:-5]}
                
            else:
                folder = '%(f)s-assim' %{'f':self.proc.srccompD[srccomp]['folder']}
            if self.proc.paramsD['suffix'] == 'auto':
                suffix = self.proc.srccompD[srccomp]['folder']
            else:
                suffix = self.proc.paramsD['suffix']
            mastermeanBand = 'mstavg-%(s)s' %{'s':self.proc.srccompD[srccomp]['band']} 
            mastermeanPrefix = 'mstavg-%(s)s' %{'s':self.proc.srccompD[srccomp]['prefix']}
            slavemeanBand = 'slvavg-%(s)s' %{'s':self.proc.srccompD[srccomp]['band']} 
            slavemeanPrefix = 'slvavg-%(s)s' %{'s':self.proc.srccompD[srccomp]['prefix']}
            stdratioBand = 'stdrat-%(s)s' %{'s':self.proc.srccompD[srccomp]['band']} 
            stdratioPrefix = 'stdrat-%(s)s' %{'s':self.proc.srccompD[srccomp]['prefix']}
            bandidD = {}
            bandidD['mstavg'] = {'id':'mstavg','band':mastermeanBand, 'prefix':mastermeanPrefix}
            bandidD['slvavg'] = {'id':'slvavg','band':slavemeanBand, 'prefix':slavemeanPrefix}
            bandidD['stdrat'] = {'id':'stdrat','band':stdratioBand, 'prefix':stdratioPrefix}
            #celltype for all dst is Float32
            celltype = 'Float32'
            cellnull = -32768

            #create the dst compositions:
            for b in bandidD:
                newcompD = {}
                for item in self.compD[srccomp]:
                    newcompD[item] = self.compD[srccomp][item]
                newcompD['folder'] = folder
                newcompD['band'] = bandidD[b]['band']
                newcompD['prefix'] = bandidD[b]['prefix']
                newcompD['id'] = b
                newcompD['suffix'] = suffix
                newcompD['cellnull'] = cellnull
                newcompD['celltype'] = celltype
                if len(newcompD['folder']) > 32:
                    exitstr = 'Fill folder name is too long: %s' %(newcompD['folder'])
                    print (exitstr)
                    EXITAGAIN
                if len(newcompD['suffix']) > 32:
                    exitstr = 'Fill folder name is too long: %s' %(newcompD['folder'])
                    print (exitstr)
                    EXITAGAIN
                    
                #Set dstcomp to the id rather than the band
                self.proc.dstcompD[b] = newcompD       
   
            #reset the dstperiod to static
            self.proc.dstperiodD['timestep'] = 'static'
            self.dstperiod = TimeSteps(self.proc.dstperiodD)
            
        def _assimilate():
            assimfolder = '%(f)s-assim' %{'f':self.proc.srccompD[srccomp]['folder']} 
            assimsuffix = self.proc.paramsD['assimsuffix']
            mastermeanBand = 'mstavg-%(s)s' %{'s':self.proc.srccompD[srccomp]['band']} 
            mastermeanPrefix = 'mstavg-%(s)s' %{'s':self.proc.srccompD[srccomp]['prefix']}
            slavemeanBand = 'slvavg-%(s)s' %{'s':self.proc.srccompD[srccomp]['band']} 
            slavemeanPrefix = 'slvavg-%(s)s' %{'s':self.proc.srccompD[srccomp]['prefix']}
            stdratioBand = 'stdrat-%(s)s' %{'s':self.proc.srccompD[srccomp]['band']} 
            stdratioPrefix = 'stdrat-%(s)s' %{'s':self.proc.srccompD[srccomp]['prefix']}
            bandidD = {}
            bandidD['mstavg'] = {'id':'mstavg','band':mastermeanBand, 'prefix':mastermeanPrefix}
            bandidD['slvavg'] = {'id':'slvavg','band':slavemeanBand, 'prefix':slavemeanPrefix}
            bandidD['stdrat'] = {'id':'stdrat','band':stdratioBand, 'prefix':stdratioPrefix}

            #create the asimilation src compositions:
            self.extraSrcCompD = {}
            for b in bandidD:
                newcompD = {}
                for item in self.compD[srccomp]:
                    newcompD[item] = self.compD[srccomp][item]
                newcompD['folder'] = assimfolder
                newcompD['band'] = bandidD[b]['band']
                newcompD['prefix'] = bandidD[b]['prefix']
                newcompD['id'] = b
                newcompD['suffix'] = assimsuffix
                newcompD['timestep'] = 'static'
                 
                #Set srccomp to the id rather than the band
                #self.proc.srccompD[b] = newcompD 
                self.extraSrcCompD[b] = newcompD   
            #Force id to original src
            self.compD[srccomp]['id'] = 'slave'
            #reset the period to static
            staticPeriodD = {}
            staticPeriodD['timestep'] = 'static'
            self.assimperiod = TimeSteps(staticPeriodD)
            #create the output
            newcompD = {}
            for item in self.compD[srccomp]:
                newcompD[item] = self.compD[srccomp][item]
            newcompD['folder'] = assimfolder
            newcompD['id'] = item
            newcompD['suffix'] = self.proc.paramsD['dstsuffix']
            self.proc.dstcompD[item] = newcompD
            self.dstperiod = TimeSteps(self.proc.srcperiodD)

        def _trendts(suffixaddon):
            timestampaddon = '-%s' %(self.srcperiod.pandasCode)
            l = len(timestampaddon)
            fntimestamp = self.compD[srccomp]['folder'][len(self.compD[srccomp]['folder'])-l:len(self.compD[srccomp]['folder'])]

            if fntimestamp.lower() == timestampaddon.lower():
                folderD = {'avg':'%s-stats' %(self.compD[srccomp]['folder']),'std':'%s-stats' %(self.compD[srccomp]['folder']),
                            'mk':'%s-trend' %(self.compD[srccomp]['folder']),'ols':'%s-trend' %(self.compD[srccomp]['folder'])}
                folderD['ols-ic'] = '%s-trend' %(self.compD[srccomp]['folder'])
                folderD['ols-r2'] = '%s-trend' %(self.compD[srccomp]['folder'])
                folderD['ols-rmse'] = '%s-trend' %(self.compD[srccomp]['folder'])
                
                folderD['ts-mdsl'] = '%s-trend' %(self.compD[srccomp]['folder'])
                folderD['ts-hisl'] = '%s-trend' %(self.compD[srccomp]['folder'])
                folderD['ts-losl'] = '%s-trend' %(self.compD[srccomp]['folder'])
                folderD['ts-ic'] = '%s-trend' %(self.compD[srccomp]['folder'])
            else:
                folderD = {'avg':'%s-%s-stats' %(self.compD[srccomp]['folder'],self.srcperiod.pandasCode),'std':'%s-%s-stats' %(self.compD[srccomp]['folder'],self.srcperiod.pandasCode),
                            'mk':'%s-%s-trend' %(self.compD[srccomp]['folder'],self.srcperiod.pandasCode),'ols':'%s-%s-trend' %(self.compD[srccomp]['folder'],self.srcperiod.pandasCode)}
                folderD['ols-ic'] = '%s-%s-trend' %(self.compD[srccomp]['folder'],self.srcperiod.pandasCode)
                folderD['ols-r2'] = '%s-%s-trend' %(self.compD[srccomp]['folder'],self.srcperiod.pandasCode)
                folderD['ols-rmse'] = '%s-%s-trend' %(self.compD[srccomp]['folder'],self.srcperiod.pandasCode)
                
                folderD['ts-mdsl'] = '%s-%s-trend' %(self.compD[srccomp]['folder'],self.srcperiod.pandasCode)
                folderD['ts-hisl'] = '%s-%s-trend' %(self.compD[srccomp]['folder'],self.srcperiod.pandasCode)
                folderD['ts-losl'] = '%s-%s-trend' %(self.compD[srccomp]['folder'],self.srcperiod.pandasCode)
                folderD['ts-ic'] = '%s-%s-trend' %(self.compD[srccomp]['folder'],self.srcperiod.pandasCode)

            bandD = {}
            celltypeD = {}
            bandD['avg'] = 'avg-%s' %(self.compD[srccomp]['band'])
            bandD['std'] =  'std-%s' %(self.compD[srccomp]['band'])
            bandD['mk'] = 'mk-z-%s' %(self.compD[srccomp]['band'])
            celltypeD['mk'] = 'Float32'
            bandD['ols'] = 'ols-sl-%s' %(self.compD[srccomp]['band'])
            celltypeD['ols'] = 'Float32'
            bandD['ols-ic'] = 'ols-ic-%s' %(self.compD[srccomp]['band'])
            bandD['ols-r2'] = 'ols-r2-%s' %(self.compD[srccomp]['band'])
            celltypeD['ols-r2'] = 'Float32'
            bandD['ols-rmse'] = 'ols-rmse-%s' %(self.compD[srccomp]['band'])
            
            bandD['ts-mdsl'] = 'ts-mdsl-%s' %(self.compD[srccomp]['band'])
            celltypeD['ts-mdsl'] = 'Float32'
            bandD['ts-hisl'] = 'ts-hisl-%s' %(self.compD[srccomp]['band'])
            celltypeD['ts-hisl'] = 'Float32'
            bandD['ts-losl'] = 'ts-losl-%s' %(self.compD[srccomp]['band'])
            celltypeD['ts-losl'] = 'Float32'
            bandD['ts-ic'] = 'ts-ic-%s' %(self.compD[srccomp]['band'])
            
            if 'mk' in self.proc.stats.paramsD:
                self.proc.stats.paramsD['ts-mdsl'] = {'band':'ts-mdsl'}
                self.proc.stats.paramsD['ts-hisl'] = {'band':'ts-hisl'}
                self.proc.stats.paramsD['ts-losl'] = {'band':'ts-losl'}
                self.proc.stats.paramsD['ts-ic'] = {'band':'ts-ic'}
            if 'ols' in self.proc.stats.paramsD:
                self.proc.stats.paramsD['ols-ic'] = {'band':'ols-ic'}
                self.proc.stats.paramsD['ols-r2'] = {'band':'ols-r2'}
                self.proc.stats.paramsD['ols-rmse'] = {'band':'ols-rmse'}
                                           
            #Complex, dst is per stat item
            for statItem in self.proc.stats.paramsD:
                
                newcompD = {}
                for item in self.compD[srccomp]:
                    newcompD[item] = self.compD[srccomp][item]  
                
                newcompD['folder'] = folderD[statItem]
                newcompD['band'] = bandD[statItem]
                newcompD['prefix'] = bandD[statItem]
                newcompD['suffix'] = '%(s)s%(a)s' %{'s':newcompD['suffix'],'a':suffixaddon}
                newcompD['cellnull'] = -32768
                
                if statItem in celltypeD:
                    #if not in statItem in celltypeD, the original data celltype
                    newcompD['celltype'] = celltypeD[statItem]

                #Create the dstcomp
                self.proc.dstcompD[statItem] = newcompD
            #Reset the dst peridod
            self.proc.dstperiodD['timestep'] = 'timespan-%s' %(self.srcperiod.pandasCode)
                          
            self.dstperiod = TimeSteps(self.proc.dstperiodD)
            
        def _resamplets():
            #Set up a dict for all possible temporal resampling alternatives
            tsDict = {'M':'M', 'A':'A'}
            for i in range (1,33):
                dd = '%(i)dD' %{'i':i}
                tsDict[dd] = dd

            #Set the exact periods needed to run the resampling, not the ones given in the xnml
            if self.params.targettimestep[len(self.params.targettimestep)-1] == 'D':
                step = int(self.params.targettimestep.replace('D',''))
                #Set the periods with full data available from the src to fill a resample period
                s = 0
                firstSrcDate = mj_dt.yyyymmddDate(self.srcperiod.datumL[0])
                year = self.proc.periodD['startyear']
                while True: 
                    doy = self.params.startstep+s*step
                    startdate = mj_dt.YYYYDOYToDate(year,doy)
                    if startdate >= firstSrcDate:
                        break
                    s += 1  
                #reset the periodicity to reflect the starting date
                self.proc.srcperiodD['startyear'] = self.proc.dstperiodD['startyear'] = startdate.year
                self.proc.srcperiodD['startmonth'] = self.proc.dstperiodD['startmonth'] = startdate.month
                self.proc.srcperiodD['startday'] = self.proc.dstperiodD['startday'] = startdate.day
                self.proc.dstperiodD['timestep'] = self.params.targettimestep
                self.srcperiod = TimeSteps(self.proc.srcperiodD)
                self.dstperiod = TimeSteps(self.proc.dstperiodD)
                
            elif self.proc.srcperiodD['timestep'] == 'D':
                if self.params.targettimestep == 'M':
                    step = 1
                    #Set the periods with full data available from the src to fill a resample period
                    s = 0
                    firstSrcDate = mj_dt.yyyymmddDate(self.srcperiod.datumL[0])
                    year = self.proc.periodD['startyear']
                    while True: 
                        doy = self.params.startstep+s
                        startdate = mj_dt.YYYYDOYToDate(year,doy)
                        if startdate >= firstSrcDate:
                            break
                        s += 1  
                    #reset the periodicity to reflect the starting date
                    self.proc.srcperiodD['startyear'] = self.proc.dstperiodD['startyear'] = startdate.year
                    self.proc.srcperiodD['startmonth'] = self.proc.dstperiodD['startmonth'] = startdate.month
                    self.proc.srcperiodD['startday'] = self.proc.dstperiodD['startday'] = startdate.day
                    self.proc.dstperiodD['timestep'] = self.params.targettimestep
                    self.srcperiod = TimeSteps(self.proc.srcperiodD)
                    self.dstperiod = TimeSteps(self.proc.dstperiodD)
                else:
                    SNULLEBULLE
            else:
                self.proc.dstperiodD['timestep'] = self.params.targettimestep
                #self.srcperiod = TimeSteps(self.proc.srcperiodD)
                self.dstperiod = TimeSteps(self.proc.dstperiodD)
                
            dstcomp = list(self.proc.dstcompD.keys())[0]
            for item in self.compD[srccomp]:
                if item in self.proc.dstcompD[dstcomp] and self.proc.dstcompD[dstcomp][item] not in  ['src', '**', -2222]:
                    pass
                else:
                    self.proc.dstcompD[dstcomp][item] = self.compD[srccomp][item] 

            if self.proc.dstcompD[dstcomp]['suffix'] == 'auto':
                self.proc.dstcompD[dstcomp]['suffix'] = '%(s)s-%(t)s' %{'s':self.proc.srccompD[srccomp]['suffix'],'t':tsDict[self.params.targettimestep]}
            if self.proc.dstcompD[dstcomp]['folder'] == 'auto':
                self.proc.dstcompD[dstcomp]['folder'] = '%(s)s-%(t)s' %{'s':self.proc.srccompD[srccomp]['folder'],'t':tsDict[self.params.targettimestep]}
                
            #self.proc.dstcompD[srccomp]['suffix'] = '%(s)s-mask' %{'s':self.proc.srccompD[srccomp]['suffix']}
            if len(self.proc.dstcompD[dstcomp]['suffix']) > 32:
                exitstr = 'suffix is too long: %s' %(self.proc.dstcompD[dstcomp]['suffix'])
                exit(exitstr)
                
            self.dstperiod = TimeSteps(self.proc.dstperiodD)
            if self.params.targettimestep[len(self.params.targettimestep)-1] == 'D' or self.proc.srcperiodD['timestep'] == 'D':
                self.dstperiod.periodstep = step
            elif len(self.srcperiod.datumL) == len(self.dstperiod.datumL):
                exitstr = 'No change in temporal frequency'
                print (exitstr) 
                SNULLE
            else:
                if not int(round(len(self.srcperiod.datumL))/len(self.dstperiod.datumL)) == float(len(self.srcperiod.datumL))/len(self.dstperiod.datumL):
                    print (  int(round(len(self.srcperiod.datumL))/len(self.dstperiod.datumL)) )
                    print ( float(len(self.srcperiod.datumL))/len(self.dstperiod.datumL) )
                    print (len(self.srcperiod.datumL),self.srcperiod.datumL)
                    print (len(self.dstperiod.datumL),self.dstperiod.datumL)
                    #print ('step',step)
                    SNULLE
                    print ('self.proc.srcperiod',self.proc.srcperiodD['timestep'])
                    #ERRRORIGN
                else:
                    self.dstperiod.periodstep = int(round(len(self.srcperiod.datumL))/len(self.dstperiod.datumL))   
                    
        def _signiftrend():
            #TGTTODO I can not have p005 set as fixed  
            if self.compD[srccomp]['folder'][len(self.compD[srccomp]['folder'])-6: len(self.compD[srccomp]['folder'])] == '-trend':
                folder = '%s-change' %(self.compD[srccomp]['folder'][0:len(self.compD[srccomp]['folder'])-6])
            else:
                folder = '%s-change' %(self.compD[srccomp]['folder']) 

            if self.proc.srccompD[srccomp]['id'] == 'intercept':  
                layerL = ['change','changep']
                addToBandL = ['change','change']
                addToSuffixL = ['model','model@p']
            elif self.proc.srccompD[srccomp]['id'] == 'slope':
                layerL = ['slopep']
                addToBandL = ['delta']
                addToSuffixL = ['slope@p']
            else:
                layerL = []

            for x,l in enumerate(layerL):
                newcompD = {}
                for item in self.compD[srccomp]:
                    newcompD[item] = self.compD[srccomp][item]  
                newcompD['folder'] = folder
                newcompD['band'] = newcompD['prefix'] =  '%s-%s' %(self.proc.paramsD['basename'],addToBandL[x]) 
                newcompD['suffix'] = '%s-%s' %(addToSuffixL[x],newcompD['suffix']) 
                #Create the dstcomp
                self.proc.dstcompD[l] = newcompD
                
        def _tpitri(txi):
            folder = '%(b)s-%(txi)s' %{'b':self.compD[srccomp]['folder'],'txi':txi}
        
            scalefac = 1
            offsetadd = 0
            cellnull = -9999
            celltype = 'Int16'

            self.proc.tpiD = {}
            self.tpiL = list(self.proc.resolfac.paramsD.keys())
            if not 1 in self.tpiL:
                self.tpiL.append(1)

            self.tpiL.sort()

            for tpi in self.tpiL:
                
                bandname = '%(txi)s%(d)d-%(b)s' %{'txi':txi,'d':tpi*self.proc.paramsD['resolid0'],'b':self.compD[srccomp]['band']}
                prefix = '%(txi)s%(d)d-%(p)s' %{'txi':txi,'d':tpi*self.proc.paramsD['resolid0'],'p':self.compD[srccomp]['prefix']}
                self.proc.tpiD[bandname] = {'resolfac':tpi}
                newcompD = {}
                for item in self.compD[srccomp]:
                    newcompD[item] = self.compD[srccomp][item]  
                
                newcompD['folder'] = folder
                newcompD['band'] = bandname
                newcompD['prefix'] = prefix
                newcompD['celltype'] = celltype
                newcompD['cellnull'] = cellnull 
                newcompD['dataunit'] = txi
                newcompD['scalefac'] = scalefac
                newcompD['offsetadd'] = offsetadd
                
                #Create the dstcomp
                self.proc.dstcompD[bandname] = newcompD
                
        def _slope():
            folder = '%(b)s-slope' %{'b':self.compD[srccomp]['folder']}
        
            scalefac = 1
            offsetadd = 0
            cellnull = -9999
            celltype = 'Float32'
            newcompD = {}
            if self.proc.paramsD['percent']:
                newcompD['dataunit'] = 'percent'
                bandname = 'slope-p-%(b)s' %{'b':self.compD[srccomp]['band']}
                prefix = 'slope-p-%(p)s' %{'p':self.compD[srccomp]['prefix']}
            else:
                newcompD['dataunit'] = 'degrees'
                bandname = 'slope-d-%(b)s' %{'b':self.compD[srccomp]['band']}
                prefix = 'slope-d-%(p)s' %{'p':self.compD[srccomp]['prefix']}

            for item in self.compD[srccomp]:
                newcompD[item] = self.compD[srccomp][item]  
            
            newcompD['folder'] = folder
            newcompD['band'] = bandname
            newcompD['prefix'] = prefix
            newcompD['celltype'] = celltype
            newcompD['cellnull'] = cellnull 
            
            newcompD['scalefac'] = scalefac
            newcompD['offsetadd'] = offsetadd
            
            #Create the dstcomp
            self.proc.dstcompD[bandname] = newcompD
            
        def _aspect():
            folder = '%(b)s-aspect' %{'b':self.compD[srccomp]['folder']}
        
            scalefac = 1
            offsetadd = 0
            cellnull = -9999
            celltype = 'Float32'
            newcompD = {}
            if self.proc.paramsD['trigonometric']:
                newcompD['dataunit'] = 'angle'
                bandname = 'aspect-trig-%(b)s' %{'b':self.compD[srccomp]['band']}
                prefix = 'aspect-trig-%(p)s' %{'p':self.compD[srccomp]['prefix']}
            else:
                newcompD['dataunit'] = 'azimuth'
                bandname = 'aspect-%(b)s' %{'b':self.compD[srccomp]['band']}
                prefix = 'aspect-%(p)s' %{'p':self.compD[srccomp]['prefix']}

            for item in self.compD[srccomp]:
                newcompD[item] = self.compD[srccomp][item]  
            
            newcompD['folder'] = folder
            newcompD['band'] = bandname
            newcompD['prefix'] = prefix
            newcompD['celltype'] = celltype
            newcompD['cellnull'] = cellnull 
            
            newcompD['scalefac'] = scalefac
            newcompD['offsetadd'] = offsetadd
            
            #Create the dstcomp
            self.proc.dstcompD[bandname] = newcompD
            
        def _hillshade():
            folder = '%(b)s-shade' %{'b':self.compD[srccomp]['folder']}
        
            scalefac = 1
            offsetadd = 0
            cellnull = -9999
            celltype = 'Int16'
  
            bandname = 'shade-%(b)s' %{'b':self.compD[srccomp]['band']}
            prefix = 'shade-%(p)s' %{'p':self.compD[srccomp]['prefix']}

            newcompD = {}
            for item in self.compD[srccomp]:
                newcompD[item] = self.compD[srccomp][item]  
            
            newcompD['folder'] = folder
            newcompD['band'] = bandname
            newcompD['prefix'] = prefix
            newcompD['celltype'] = celltype
            newcompD['cellnull'] = cellnull 
            newcompD['dataunit'] = 'hillshade'
            newcompD['scalefac'] = scalefac
            newcompD['offsetadd'] = offsetadd
            
            #Create the dstcomp
            self.proc.dstcompD[bandname] = newcompD
                
        def _autocorr():
            '''
            '''
            if self.proc.paramsD['partial']:
                folder ='%s-pacf' %(self.compD[srccomp]['folder'])
                bandname = '%(b)s-pacf' %{'b':self.compD[srccomp]['band']}
                prefix = '%(p)s-pacf' %{'p':self.compD[srccomp]['prefix']}
            else:
                folder ='%s-acf' %(self.compD[srccomp]['folder'])
                bandname = '%(b)s-acf' %{'b':self.compD[srccomp]['band']}
                prefix = '%(p)s-acf' %{'p':self.compD[srccomp]['prefix']}
       
            #Create the new (lag) composition
            newcompD = {}
            for item in self.compD[srccomp]:
                newcompD[item] = self.compD[srccomp][item]  
            
            newcompD['folder'] = folder
            newcompD['band'] = bandname
            newcompD['prefix'] = prefix
            #Celltype must be float 32
            newcompD['celltype'] = 'Float32'
            #Set dataunit to 
            newcompD['dataunit'] = 'correlation'
            newcompD['scalefac'] = 1
            newcompD['offsetadd'] = 0

            #Create the dstcomp
            self.proc.dstcompD[bandname] = newcompD

            self.proc.dstperiodD['timestep'] = 'autocorr-%s' %(self.srcperiod.pandasCode)
            #Send some extra stuff along
            self.proc.dstperiodD['nlags'] = self.proc.paramsD['nlags']
            self.proc.dstperiodD['mirror'] = self.proc.paramsD['mirror']
            self.dstperiod = TimeSteps(self.proc.dstperiodD)
  
        def _indexcrosstrend(suffixaddon,folderaddon):
            '''
            '''
            #folderNameD = {'naivetrend':'nt'}
            #if self.srcperiod.timestep not in ['M']:
            #    FIXADETTA
            #Get the indexes to work on
            self.indexL = list(self.proc.index.paramsD.keys())

            #Get the crosscorrelations to test
            self.xcrosscompsL = []
            if self.proc.paramsD['xcrosseason']:self.xcrosscompsL.append('season')
            if self.proc.paramsD['xcrosstendency']:self.xcrosscompsL.append('tendency')
            if self.proc.paramsD['xcrossresidual']:self.xcrosscompsL.append('residual')
            if self.proc.paramsD['xcrossobserved']:self.xcrosscompsL.append('obs')

            #Get the layers to create for each crosscorrelation test
            self.xcrossdstL =[]
            if self.proc.paramsD['xcrosspearson']:self.xcrossdstL.append('pearson')
            #if self.proc.paramsD['xcrossmax']:self.xcrossdstL.append('maxcorr')
            if self.proc.paramsD['xcrosslag']:self.xcrossdstL.append('lag')

            dstfolder  ='%s-ixc%s' %(self.compD[srccomp]['folder'],folderaddon)        
            #all outputs are created, to make the looping faster, but only the ones given are saved
            #allcrosscompsL = ['pearson','maxcorr','lag']
            ''' CREATE TARGETS'''
            self.dstIndexD ={} 
    
            for i in self.indexL:
                for c in self.xcrosscompsL:
                    for l in self.xcrossdstL:
                        
                        bandname = prefix = '%(c)s-%(l)s-%(i)s' %{'c':c, 'l':l,'i':i}
                        #Create the new (lag) composition
                        newcompD = {}
                        for item in self.compD[srccomp]:
                            newcompD[item] = self.compD[srccomp][item]  
                        
                        newcompD['folder'] = dstfolder
                        newcompD['band'] = bandname
                        newcompD['prefix'] = prefix
                        newcompD['suffix'] = '%(s)s%(a)s' %{'s':newcompD['suffix'],'a':suffixaddon}
                        if l == 'lag':
                            newcompD['celltype'] = 'Int16'
                        else:
                            newcompD['celltype'] = 'Float32'
                        newcompD['cellnull'] = -32768
                        #Set dataunit to 
                        newcompD['dataunit'] = 'correlation'
                        newcompD['scalefac'] = 1
                        newcompD['offsetadd'] = 0
                        #Create the dstcomp
                        self.proc.dstcompD[bandname] = newcompD
                        
            #Reset the dst peridod
            self.proc.dstperiodD['timestep'] = 'timespan-%s' %(self.srcperiod.pandasCode)           
            self.dstperiod = TimeSteps(self.proc.dstperiodD)
            
        def _imagecrosstrend(suffixaddon,folderaddon):
            '''
            '''
            #if self.srcperiod.timestep not in ['M']:
            #    FIXADETTA

            #Get the crosscorrelations to test
            self.xcrosscompsL = []
            if self.proc.paramsD['xcrosseason']:self.xcrosscompsL.append('season')
            if self.proc.paramsD['xcrosstendency']:self.xcrosscompsL.append('tendency')
            if self.proc.paramsD['xcrossresidual']:self.xcrosscompsL.append('residual')
            if self.proc.paramsD['xcrossobserved']:self.xcrosscompsL.append('obs')

            #Set the list of outputs
            self.xcrossdstL =['pearson','lag']
            #if self.proc.paramsD['xcrosspearson']:self.xcrossdstL.append('pearson')
            #if self.proc.paramsD['xcrosslag']:self.xcrossdstL.append('lag')
            self.xcrossLagL =[]
            if self.proc.paramsD['savelags'] >= 0:
                self.xcrossLagL.append(0)
                for n in range (1,self.proc.paramsD['savelags']+1):
                    self.xcrossLagL.append(n)
                    if self.proc.paramsD['mirrorlag']:
                        self.xcrossLagL.append(-n)

            ''' CREATE TARGETS'''
            self.dstIndexD ={} 
            dstComp0 = list(self.proc.dstcompD.keys())[0]

            for c in self.xcrosscompsL:
                for l in self.xcrossdstL:
                    newcompD = {}
                    newcompD['source'] = self.proc.dstcompD[dstComp0]['source']
                    newcompD['product'] = self.proc.dstcompD[dstComp0]['product']
                    newcompD['folder'] = self.proc.dstcompD[dstComp0]['folder']

                    bandname = prefix = '%(c)s-%(l)s' %{'c':c, 'l':l}
                    newcompD['band'] = bandname
                    newcompD['prefix'] = prefix
                    newcompD['measure'] = 'R'
                    newcompD['suffix'] = '%(s)s%(a)s' %{'s':self.proc.dstcompD[dstComp0]['suffix'],'a':suffixaddon}
                    if l == 'lag':
                        newcompD['celltype'] = 'Int16'
                    else:
                        newcompD['celltype'] = 'Float32'
                    newcompD['cellnull'] = -32768
                    #Set dataunit to lag for lag TGTODO
                    newcompD['dataunit'] = 'correlation'
                    newcompD['scalefac'] = 1
                    newcompD['offsetadd'] = 0                    
                    #Create the new dstcomp
                    self.proc.dstcompD[bandname] = newcompD
                #And then the fixed lags to produce
                for lc in self.xcrossLagL:
                    newcompD = {}
                    newcompD['source'] = self.proc.dstcompD[dstComp0]['source']
                    newcompD['product'] = self.proc.dstcompD[dstComp0]['product']
                    newcompD['folder'] = self.proc.dstcompD[dstComp0]['folder']
                    bandname = prefix = '%(c)s-pearson-lag%(lc)d' %{'c':c, 'lc':lc}
                    newcompD['band'] = bandname
                    newcompD['prefix'] = prefix
                    newcompD['measure'] = 'R'
                    newcompD['suffix'] = '%(s)s%(a)s' %{'s':self.proc.dstcompD[dstComp0]['suffix'],'a':suffixaddon}
                    newcompD['celltype'] = 'Float32'
                    newcompD['cellnull'] = -32768
                    newcompD['dataunit'] = 'correlation'
                    newcompD['scalefac'] = 1
                    newcompD['offsetadd'] = 0                    
                    #Create the new dstcomp
                    self.proc.dstcompD[bandname] = newcompD
                           
            #remove the default dst comp - it is just a dummy
            self.proc.dstcompD.pop(dstComp0)
            #Reset the dst peridod
            self.proc.dstperiodD['timestep'] = 'timespan-%s' %(self.srcperiod.pandasCode)
            print  ('timestep',self.proc.dstperiodD['timestep'])          
            self.dstperiod = TimeSteps(self.proc.dstperiodD)

        def _copycomp():
            if srccomp == self.proc.paramsD['copycomp']:
                for dstCompItem in self.proc.dstcompD:
                    newcompD = {}
                    for item in self.compD[srccomp]:
                        if item in self.proc.dstcompD[dstCompItem] and self.proc.dstcompD[dstCompItem][item]  not in ['src',-2222]:
                            newcompD[item] = self.proc.dstcompD[dstCompItem][item]
                        else:
                            newcompD[item] = self.compD[srccomp][item]
                    #Replace the dstcomp
                    self.dstCompD[dstCompItem] = newcompD 
                    self.proc.dstcompD[dstCompItem] = newcompD
        if self.verbose > 1:
            print ('    Fixing copycomp',self.proc.paramsD['copycomp'])
        
        if self.proc.paramsD['copycomp'] == 'pass':
            return
        
        elif 'seasonfill' in self.proc.processid.lower() and srccomp == 'season':
            return
        
        elif self.proc.paramsD['copycomp'] == '1to1': 
            #The dstcomp and srccomp are identical
            self._ReplaceComp(srccomp,srccomp)
            if 'suffix' in self.proc.paramsD and self.proc.paramsD['suffix'] != 'copy':
                self.proc.dstcompD[srccomp]['suffix'] = self.proc.paramsD['suffix']
            
        elif self.proc.paramsD['copycomp'] == 'tractproject': 
            #tractproject converts an ancillary layer to a tract
            _tractProject()
            
        elif self.proc.paramsD['copycomp'] in ['movieframeappend']: 

            for item in self.srcIdDict:

                if item[0:3] in ['top','lef']:
                    if self.srcIdDict[item] == srccomp:
                        print ('setting movie',item)
                        _movie()

                    
        elif self.proc.paramsD['copycomp'] in ['movieframe','movieclock']: 
            #dstcomp and srccomp are identical
            _movie()
        elif self.proc.paramsD['copycomp'] in ['movieframeoverlay']: 
            #dstcomp and srccomp are identical
            for item in self.srcIdDict:
                if item[0:4] == 'base':
                    _movie()
        
        elif self.proc.paramsD['copycomp'] in ['template','fromid']:
            _template()
            
        elif self.proc.paramsD['copycomp'] == 'archive':
            _archive()

        elif self.proc.paramsD['copycomp'] == 'anytoall':
            _anytoall()
   
        elif self.proc.paramsD['copycomp'] == 'exporttobyte': 
            _exporttobyte()
            
        elif self.proc.paramsD['copycomp'] == 'exportmap': 
            _exportmap()
           
        elif self.proc.paramsD['copycomp'] == 'seasonalts': 
            _seasonalts()
        
        elif self.proc.paramsD['copycomp'] == 'DtoMdataunits': 
            _DtoMdataunits()
                                         
        elif self.proc.paramsD['copycomp'] == 'tostatictimestep':  
            self.proc.dstperiodD['timestep'] = 'static'
            self.dstperiod = TimeSteps(self.proc.dstperiodD)
                    
        elif self.proc.paramsD['copycomp'] == 'applystaticmask':  
            _applystaticmask()
            
        elif self.proc.paramsD['copycomp'] == 'subtractseason': 
            _subtractseason()
                                        
        elif self.proc.paramsD['copycomp'] == 'gdaltranslate': 
            _gdaaltranslate()
               
        elif self.proc.paramsD['copycomp'] == 'seasonfillts': 
            _seasonfillts()
           
        elif self.proc.paramsD['copycomp'] == 'trendts': 
            _trendts('')
            
        elif self.proc.paramsD['copycomp'] == 'resamplets':         
            _resamplets()
                      
        elif self.proc.paramsD['copycomp'] == 'signiftrend':  
            _signiftrend()
            
        elif self.proc.paramsD['copycomp'] == 'tpi':  
            _tpitri('tpi')
        
        elif self.proc.paramsD['copycomp'] == 'tri':  
            _tpitri('tri')
            
        elif self.proc.paramsD['copycomp'] == 'roughness':  
            _tpitri('rn')
            
        elif self.proc.paramsD['copycomp'] == 'hillshade':  
            _hillshade()
            
        elif self.proc.paramsD['copycomp'] == 'slope':  
            _slope()
            
        elif self.proc.paramsD['copycomp'] == 'aspect':  
            _aspect()
            
        elif self.proc.paramsD['copycomp'] == 'autocorr':  
            _autocorr()
            
        elif self.proc.paramsD['copycomp'] == 'setassimilation':  
            _setassimilation()
            
        elif self.proc.paramsD['copycomp'] == 'assimilate':  
            _assimilate()
            
        elif self.proc.paramsD['copycomp'] == 'exportsvg':
            _exportSvg()
            
        elif self.proc.paramsD['copycomp'] == 'indexcrosstrend': 
            #First set the trends that are requeted
            #must be set first to allow the correct Timestep to be set in 
            #_indexcrosstrend

            if self.proc.paramsD['naive']:
                suffixaddon = folderaddon = '-n'
                if self.proc.paramsD['naive']:
                    suffixaddon =  '%sadd' %(suffixaddon)
                else:
                    suffixaddon = '%smpl' %(suffixaddon)
            else:
                
                if self.proc.paramsD['trend'] == 'spline':
                    suffixaddon = folderaddon = '-s'
                else:
                    PLEASEADD
                if self.proc.paramsD['forceseason']:
                    suffixaddon = '%sfs' %(suffixaddon)

            if len(self.proc.paramsD['kernel']) > 5:
                suffixaddon =  '%s-k' %(suffixaddon)
   
            if self.proc.paramsD['abs']:
                suffixaddon =  '%s-abs' %(suffixaddon)
    
            if self.proc.paramsD['yearfac'] > 1:
                suffixaddon= '%(s)s-a%(y)d' %{'s':suffixaddon, 'y':self.proc.paramsD['yearfac']}
            else:
                suffixaddon= '%(s)s-a1' %{'s':suffixaddon}
            _trendts(suffixaddon)  
            _indexcrosstrend(suffixaddon,folderaddon)
            self.proc.paramsD['xcross'] = True
            self.proc.paramsD['xcrosscompsL'] = self.xcrosscompsL
            self.proc.paramsD['xcrossdstL'] = self.xcrossdstL
            
            if len(self.xcrosscompsL) == 0 or len(self.xcrossdstL) == 0 or self.indexL == 0:
                exit('No destination layer set')
                    
        elif self.proc.paramsD['copycomp'] == 'imagecrosstrend': 
            #THIS LOPPS TWICE NOW, ONE IS ENOUGH BOTH GIVE SAME DST OUTPUT
            if self.proc.paramsD['naive']:
                suffixaddon = folderaddon = '-n'
                if self.proc.paramsD['naive']:
                    suffixaddon =  '%sadd' %(suffixaddon)
                else:
                    suffixaddon = '%smpl' %(suffixaddon)
            else:    
                if self.proc.paramsD['trend'] == 'spline':
                    suffixaddon = folderaddon = '-s'
                else:
                    PLEASEADD
                if self.proc.paramsD['forceseason']:
                    suffixaddon = '%sfs' %(suffixaddon)
            if len(self.proc.paramsD['kernel']) > 5:
                suffixaddon =  '%s-k' %(suffixaddon)
            if self.proc.paramsD['abs']:
                suffixaddon =  '%s-abs' %(suffixaddon)
            if self.proc.paramsD['yearfac'] > 1:
                suffixaddon= '%(s)s-a%(y)d' %{'s':suffixaddon, 'y':self.proc.paramsD['yearfac']}
            else:
                suffixaddon= '%(s)s-a1' %{'s':suffixaddon}
            _imagecrosstrend(suffixaddon,folderaddon)

            self.proc.paramsD['xcross'] = True
            self.proc.paramsD['xcrosscompsL'] = self.xcrosscompsL
            self.proc.paramsD['xcrossdstL'] = self.xcrossdstL
            self.proc.paramsD['xcrossLagL'] = self.xcrossLagL
            if len(self.xcrosscompsL) == 0 or len(self.xcrossdstL) == 0:
                exit('No destination layer set')
            #Set copycomp to pass, as a double pass will ruin the dst comp
            self.proc.paramsD['copycomp'] = 'pass'
                   
        elif self.proc.paramsD['copycomp'] in srcCompL:
            _copycomp()
            
        else:
            print (self.proc.paramsD['copycomp'] )
            NOTDONE
        
    def _ReplaceComp(self,srccomp,dstcomp):
        newcompD = {}
        for item in self.compD[srccomp]:
            if srccomp in self.proc.dstcompD and item in self.proc.dstcompD[dstcomp] and self.proc.dstcompD[dstcomp][item] != 'src':
                newcompD[item] = self.proc.dstcompD[dstcomp][item]
            else:
                newcompD[item] = self.compD[srccomp][item]
        #Replace the dstcomp
        #self.dstCompD[srccomp] = newcompD
        self.proc.dstcompD[dstcomp] = newcompD
               
    def _SetLocations(self):
        '''
        '''
        if 'src_defregid' in self.proc.paramsD:

            query = {'regionid':self.proc.paramsD['src_defregid']}
            #print (self.session.name)
            defregionid = self.session._GetDefRegion(query)
            if defregionid == None:
                exitstr ='No valid dfault region identified for paramer src_defregid'
                exit(exitstr)
            #Only defaut region accepted 
            self.srclocations = Location(self.proc.paramsD, self.proc.processid, '*', '*', defregionid[0], self.proc.systemD['srcsystem'], self.proc.systemD['srcdivision'],self.session)
        else:    
            self.srclocations = Location(self.proc.paramsD, self.proc.processid, self.proc.userProj.siteid, self.proc.userProj.tractid, self.proc.userProj.defregion, self.proc.systemD['srcsystem'], self.proc.systemD['srcdivision'],self.session)

        if 'dst_defregid' in self.proc.paramsD:
            self.dstlocations = Location(self.proc.paramsD, self.proc.processid, '*', '*', self.proc.paramsD['dst_defregid'], self.proc.systemD['dstsystem'], self.proc.systemD['dstdivision'],self.session)

        else:
            self.dstlocations = Location(self.proc.paramsD, self.proc.processid, self.proc.userProj.siteid, self.proc.userProj.tractid, self.proc.userProj.defregion, self.proc.systemD['dstsystem'], self.proc.systemD['dstdivision'],self.session)
 
    def _SetLayers(self):
        '''
        '''
        self.srcLayerD = {}
        self.dstLayerD = {}
        if self.verbose > 1:
            print ('    Setting source layers')
        self._SetSrcLayers()
        if self.verbose > 1:
            print ('    Setting destination layers')
        self._SetDstLayers()
    
    def _SetSrcLayers(self):
        '''
        '''
        for locus in self.srclocations.locusL:

            self.srcLayerD[locus] = {}
            for datum in self.srcperiod.datumL:
                #print ('            datum:',datum)
                self.srcLayerD[locus][datum] = {}
                for srccomp in self.srcCompD:
                    #print ('                srccomp:',srccomp)
                    #Check if the composition has its own timestep, and adjust
                    if 'timestep' in self.proc.srccompD[srccomp]:
                        #print ('                    timestep:',self.proc.srccompD[srccomp]['timestep'])
                        altperiod = TimeSteps(self.proc.srcperiodD,self.proc.srccompD[srccomp]['timestep'])
                        if self.proc.srcperiodD['timestep'] == self.proc.srccompD[srccomp]['timestep']:
                            datumD = self.srcperiod.datumD[datum]
                        elif self.proc.srccompD[srccomp]['timestep'] == 'static':
                            datumD = altperiod.datumD['0']
                        elif self.proc.srccompD[srccomp]['timestep'] == 'staticmonthly':
                            print ('altperiod.datumD',altperiod.datumL)
                            SNULLE
                            datumD = altperiod.datumD['0']
                        elif self.proc.srccompD[srccomp]['timestep'] in ['seasonal-M','seasonal-Mday']:
                            datumD = altperiod.datumD[datum]
                        else:
                            print (self.proc.srccompD[srccomp]['timestep'])
                            PLEASEADD
                    else:
                        datumD = self.srcperiod.datumD[datum]
                    if self.srcCompD[srccomp].celltype in ['txt','csv','none']:
                        self.srcLayerD[locus][datum][srccomp] = TextLayer(self.srcCompD[srccomp], self.srclocations.locusD[locus], datumD, self.srcpath)
                    elif 'shp' in self.srcpath.hdrfiletype:
                        self.srcLayerD[locus][datum][srccomp] = VectorLayer(self.srcCompD[srccomp], self.srclocations.locusD[locus], datumD, self.srcpath)
                    elif 'png' in self.srcpath.hdrfiletype and self.proc.processid.lower() in ['movieframe','movieframeoverlay','movieframeappend',
                                                'movieframemodisappendsingletile','movieframemodisappendregiontiles']:
                        self.srcLayerD[locus][datum][srccomp] = MovieFrame(self.srcCompD[srccomp], self.srclocations.locusD[locus], datumD, self.srcpath)

                    else:
    
                        if 'seasonfill' in self.proc.processid.lower() and srccomp == 'season':
                            #print ('                season')
                            #This is for the special season comp used for combining a full timesereies and a seasonal timeseries
                            if self.srcperiod.timestep[len(self.srcperiod.timestep)-1] == 'D':
                                timespan = '%s-%s' %(self.srcperiod.startyear, self.srcperiod.endyear)
                                doy = datum[len(datum)-3:len(datum)]
                                seasondatum = '%s@D%s' %(timespan,doy)
                            elif self.srcperiod.timestep == 'M':
                                timespan = '%s-%s' %(self.srcperiod.startyear, self.srcperiod.endyear)
                                month = datum[len(datum)-2:len(datum)]
                                seasondatum = '%s@M%s' %(timespan,month)
                            else:
                                RULLEKULLE
                            self.srcLayerD[locus][datum][srccomp] = RasterLayer(self.srcCompD[srccomp], self.srclocations.locusD[locus], self.seasonperiod.datumD[seasondatum], self.srcpath)
                        else:
                            self.srcLayerD[locus][datum][srccomp] = RasterLayer(self.srcCompD[srccomp], self.srclocations.locusD[locus], datumD, self.srcpath)
                            '''
                            print ('band',srccomp,self.srcCompD[srccomp].band)
                            print ('prefix',srccomp,self.srcCompD[srccomp].prefix)
                            print ('ordinaery raster', self.srcLayerD[locus][datum][srccomp].FPN)
                            print ('self.srcCompD[srccomp]',self.srcCompD[srccomp].band)
                            if srccomp == 'ortho-wet':
                                MADDE
                            '''
                    if not path.exists(self.srcLayerD[locus][datum][srccomp].FPN):
                        #print ('acceptmissing',self.proc.acceptmissing)
                        if self.proc.acceptmissing:
                            self.srcLayerD[locus][datum][srccomp] = False
                            print ('        Skipping missing comp, locus, datum', srccomp, locus, datum)

                        else:
                            print ('acceptmissing',self.proc.acceptmissing)
                            exitstr = 'EXITING, path does not exist: %(p)s' %{'p':self.srcLayerD[locus][datum][srccomp].FPN}
                            print (exitstr)
                            print (self.proc.xml)
                            NONEXISTINGPATH
                            exit(exitstr)
        '''
        for locus in self.srclocations.locusL:
            for datum in self.srcperiod.datumL:
                for comp in self.srcCompD:
                    print (locus,datum,comp)
                    if self.srcLayerD[locus][datum]:
                        print (self.srcLayerD[locus][datum][comp].FPN)
        print (self.proc.srcperiodD)
        BALLE
        '''
     

    def _SetDstLayers(self):
        '''
        '''
        for locus in self.dstlocations.locusL:
            self.dstLayerD[locus] = {}
            for datum in self.dstperiod.datumL:
                #print ('datum', datum)
                self.dstLayerD[locus][datum] = {}
                for comp in self.dstCompD:
                    #The setting of TimeStep should be done beforehand
                    if 'timestep' in self.proc.dstcompD[comp]:
                        #THIS SHOULD BE DONE JUST ONCE
                        altperiod = TimeSteps(self.proc.dstperiodD,self.proc.dstcompD[comp]['timestep'])
                        if self.proc.dstperiodD['timestep'] == self.dstCompD[comp]:
                            datumD = self.dstperiod.datumD[datum]
                        elif self.proc.dstcompD[comp]['timestep'] == 'static':
                            datumD = altperiod.datumD['0']
                        elif self.proc.dstcompD[comp]['timestep'] == 'A':
                            datumD = altperiod.datumD[datum[0:4]]
                        elif self.proc.dstcompD[comp]['timestep'] == 'M':
                            datumD = altperiod.datumD[datum[0:6]]
                        elif self.proc.dstcompD[comp]['timestep'] in ['seasonal-M','seasonal-Mday']:
                            datumD = altperiod.datumD[datum]
                        else:
                            print (self.proc.dstcompD[comp]['timestep'])
                            PLEASEADD
                    else:
                        datumD = self.dstperiod.datumD[datum]
  
                    if self.dstCompD[comp].celltype in ['movieframe','movieframeoverlay','movieframeappend']:
                        self.dstLayerD[locus][datum][comp] = MovieFrame(self.dstCompD[comp], self.dstlocations.locusD[locus], datumD, self.dstpath)
                    elif self.dstCompD[comp].celltype == 'movieclock':
                        self.dstLayerD[locus][datum][comp] = MovieClock(self.dstCompD[comp], self.dstlocations.locusD[locus], datumD, self.dstpath)
                    elif self.dstCompD[comp].celltype == 'vector':
                        self.dstLayerD[locus][datum][comp] = VectorLayer(self.dstCompD[comp], self.dstlocations.locusD[locus], datumD, self.dstpath)
                    elif self.dstCompD[comp].celltype == 'svg':
                        self.dstLayerD[locus][datum][comp] = SVGLayer(self.dstCompD[comp], self.dstlocations.locusD[locus], datumD, self.dstpath)
                    elif self.dstCompD[comp].celltype == 'map':
                        self.dstLayerD[locus][datum][comp] = MapLayer(self.dstCompD[comp], self.dstlocations.locusD[locus], datumD, self.dstpath)

                    else:
                        self.dstLayerD[locus][datum][comp] = RasterLayer(self.dstCompD[comp], self.dstlocations.locusD[locus], datumD, self.dstpath)

        for locus in self.dstlocations.locusL:
            for datum in self.dstperiod.datumL:
                print ('    datum',datum)
                for comp in self.dstCompD:
                    print ('        comp',comp)
                    print (self.dstLayerD[locus][datum][comp].FPN)

        print (self.proc.dstperiodD)
