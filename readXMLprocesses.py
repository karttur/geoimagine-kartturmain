'''
Created on 23 feb. 2018

@author: thomasgumbricht
'''

from os import path

from geoimagine.postgresdb import  SelectProcess, SelectUser, ManageAncillary, ManageSentinel, ManageLandsat, ManageMODIS, ManageSMAP, ManageLayout, ManageExport, ManageSqlDumps 
from geoimagine.postgresdb import ManageUserProj
from geoimagine.ancillary import ProcessAncillary
from geoimagine.sentinel import ProcessSentinel
from geoimagine.landsat import ProcessLandsat
from geoimagine.modis import ProcessModis
from geoimagine.smap import ProcessSmap
from geoimagine.grace import ProcessGrace
from geoimagine.timeseries import ProcessTimeSeries, ProcessTimeSeriesGraph
from geoimagine.layout import ProcessLayout
from geoimagine.export import ProcessExport
from geoimagine.overlay import ProcessOverlay
from geoimagine.image import ProcessImage
from geoimagine.scalar import ProcessScalar
from geoimagine.userproj import ProcessUserProj
from geoimagine.gdalutilities import ProcessGdalUtilities
from geoimagine.mask import ProcessMasking
from geoimagine.transform import ProcessTransform
from geoimagine.updatedb import ProcessUpdateDB
from geoimagine.dem import ProcessDEM
from geoimagine.sqldump import ProcessSqlDumps
#from geoimagine.postgresdb import ReadUserCreds
#from geoimagine.setup_processes import ProcessProcess
#from geoimagine.kartturXML import ReadXMLuser
#from geoimagine.karttur_main_old import ProcessLayout
from geoimagine.kartturmain import UserProj, SetXMLProcess, MainProc
import xmltodict
 
def ReadXMLProcesses(projFPN,verbose):
    '''
    Read processes
    ''' 

    if path.splitext(projFPN)[1].lower() == '.xml':
        xmlL = [projFPN]
    else:
        srcFP = path.join(path.split(projFPN)[0],'xml')
        #Read the textfile with links to the xml files defining schemas and tables
        print ('reading txt',projFPN)
        with open(projFPN) as f:
            xmlL = f.readlines()
        # Remove whitespace characters like `\n` at the end of each line
        xmlL = [path.join(srcFP, x.strip())  for x in xmlL if len(x) > 10 and x[0] != '#'] 

    #Loop over all xml files and setup the processes
    procLL = []
    for xml in xmlL:
        procL = []
        if verbose:
            print ('    Reading xml',xml)
        with open(xml) as fd:
            doc = xmltodict.parse(fd.read())
        #Get the root and the content
        rootid = next(iter(doc.items()))[0]
        content = next(iter(doc.items()))[1]      
        #Get the userProj(ordered dictionary)
        userProjOD = content['userproj']

        userid = userProjOD['@userid']
        if '@userpswd' in userProjOD:
            userpswd = userProjOD['@userpswd']
        else:
            userpswd = ''

        session = SelectUser()
        userData = session._SelectUserCreds(userid,userpswd)
        session._Close()
        if userData == None:
            exit('No user found with given password')

        if userData:
            userId, userCat, userStratum, userProjs, userTracts, userSites = userData
            #userProj._SetCredentials(userCat, userStratum, userProjs=userProjs, userTracts=userTracts, userSites=userSites)
        else:
            exit('no user found')
        #print ('You are entering as user:', userId)   
        #Connect to the Postgres Server, each xml must be checked to have an allowed user
        session = SelectProcess()

        tagAttrL = session._SelectProcessTagAttr('userproj', 'root', 'userproj')  

        userProj = UserProj(userProjOD,tagAttrL,xml)
        # set user credentials
        userProj._SetCredentials(userCat, userStratum, userProjs=userProjs, userTracts=userTracts, userSites=userSites)

        #Check that the user owns the project and the plot/site/tract requested
        projSetting = userProj._CheckUserProj()

        if not projSetting:
            warnstr = 'User does not own the project'
            print (warnstr)
            session._Close()
            continue
        #Get the default region for the tract/site
        projSetting = userProj._GetDefRegion(session)

        if not 'process' in content:
            exit('no process defined')
        processesDL = content['process']

        #Check if this is a single process, if so create a list with the single process
        if not type(processesDL) is list:
            processesDL = [processesDL]
    
        for processD in processesDL:
            processid = processD['@processid']
            #Instantiate Process
            proc = SetXMLProcess(userProj, processid, content, session, xml, verbose)
            #check that user has the right to this process
            permit = proc._CheckPermission(session)
            if not permit:
                exitstr = 'You do not have the required priveledges '
                exit(exitstr)
                continue
            #Check the input parameters
            errorD = proc._CheckParams(processD, session)
            procL.append(proc)

        #all the data is read, process the data
        procLL.append(procL)
        session._Close()
    return procLL
    #return userProj, procLL

def RunProcesses(procLL,verbose):
    for procL in procLL:
        #session = ReadUserCreds()
        for proc in procL:
            if proc.rootprocid == 'LayoutProc':
                session = ManageLayout()
                process = MainProc(proc,session,verbose)
                ProcessLayout(process,session,verbose)
                session._Close()
                
            elif proc.rootprocid == 'Ancillary':
                session = ManageAncillary()
                process = MainProc(proc,session,verbose)
                ProcessAncillary(process,session,verbose)
                session._Close()
                
            elif proc.rootprocid == 'SentinelProcess':
                session = ManageSentinel()
                process = MainProc(proc,session,verbose)
                ProcessSentinel(process,session,verbose)
                session._Close()  
                 
            elif proc.rootprocid == 'LandsatProc':
                session = ManageLandsat()
                process = MainProc(proc,session,verbose)
                ProcessLandsat(process,session,verbose)
                session._Close()
                
            elif proc.rootprocid == 'MODISProc':
                session = ManageMODIS()
                process = MainProc(proc,session,verbose)
                ProcessModis(process,session,verbose)
                session._Close()
                
            elif proc.rootprocid == 'SMAPProc':
                session = ManageSMAP()
                process = MainProc(proc,session,verbose)
                ProcessSmap(process,session,verbose)
                session._Close()
                
            elif proc.rootprocid == 'GRACEProc':
                #Grace is treated as an ancillary layer, but has other processing capacity
                session = ManageAncillary()
                process = MainProc(proc,session,verbose)
                ProcessGrace(process,session,verbose)
                session._Close()
                
            elif proc.rootprocid in ['TimeSeries','TimeSeriesGraph']:
                #Grace is treated as an ancillary layer, but has other processing capacity
                if proc.systemD['system'] == 'smap':
                    session = ManageSMAP()
                elif proc.systemD['system'] == 'ancillary':
                    session = ManageAncillary()
                elif proc.systemD['system'] == 'grace':
                    session = ManageAncillary()
                elif proc.systemD['system'] == 'modis':
                    session = ManageMODIS()
                else:
                    print (proc.systemD['system'])
                    exitstr = 'system not available under Process TimeSeries'
                    exit(exitstr)
                
                process = MainProc(proc,session,verbose)
                
                if proc.rootprocid == 'TimeSeries':
                    ProcessTimeSeries(process,session,verbose)
                else:
                    ProcessTimeSeriesGraph(process,session,verbose)
                session._Close()
                
            elif proc.rootprocid in ['Overlay','OverlaySpecial', 'Image','Scalar','Masking','Transform', 'Updatedb', 'DEM']:
                #Grace is treated as an ancillary layer, but has other processing capacity

                if proc.systemD['system'] == 'smap':
                    session = ManageSMAP()
                elif proc.systemD['system'] == 'ancillary':
                    session = ManageAncillary()
                elif proc.systemD['system'] == 'grace':
                    session = ManageAncillary()
                elif proc.systemD['system'] == 'modis':
                    session = ManageMODIS()
                else:
                    exitstr = 'system %s not available under root %s' %(proc.systemD['system'], proc.rootprocid)
                    exit(exitstr)
                    
                process = MainProc(proc,session,verbose)

                if proc.rootprocid in ['Overlay', 'OverlaySpecial']:
                    ProcessOverlay(process,session,verbose)
                elif proc.rootprocid == 'Image':
                    ProcessImage(process,session,verbose)
                elif proc.rootprocid == 'Scalar':
                    ProcessScalar(process,session,verbose)
                    
                elif proc.rootprocid == 'Masking':
                    ProcessMasking(process,session,verbose)
                    
                elif proc.rootprocid == 'Transform':
                    ProcessTransform(process,session,verbose)
                    
                elif proc.rootprocid == 'Updatedb':
                    ProcessUpdateDB(process,session,verbose)
                    
                elif proc.rootprocid == 'DEM':
                    ProcessDEM(process,session,verbose)
                
                else:
                    exitstr = 'Root process id not recognized %s' %(proc.rootprocid)
                    exit(exitstr)

                session._Close()
                
            elif proc.rootprocid == 'Export':
                #Grace is treated as an ancillary layer, but has other processing capacity
                session = ManageExport()
                process = MainProc(proc,session,verbose)
                ProcessExport(process,session,verbose)
                session._Close()
                
            elif proc.rootprocid == 'GdalUtilities':
                #Grace is treated as an ancillary layer, but has other processing capacity
                if proc.systemD['system'] == 'smap':
                    session = ManageSMAP()
                elif proc.systemD['system'] == 'ancillary':
                    session = ManageAncillary()
                elif proc.systemD['system'] == 'grace':
                    session = ManageAncillary()
                elif proc.systemD['system'] == 'modis':
                    session = ManageMODIS()
                else:
                    exitstr = 'system not recognozed under GdalUtil'
                    exit(exitstr)
                process = MainProc(proc,session,verbose)
                ProcessGdalUtilities(process,session,verbose)
                session._Close()
                
            elif proc.rootprocid == 'ManageProject':
                #Grace is treated as an ancillary layer, but has other processing capacity
                session = ManageUserProj()
                process = MainProc(proc,session,verbose)
                ProcessUserProj(process,session,verbose)
                session._Close()
            elif proc.rootprocid == 'ManageSqlDumps':
                session = ManageSqlDumps()
                process = MainProc(proc,session,verbose)
                ProcessSqlDumps(process,session,verbose)
                session._Close()
            else:
                exitStr = 'EXITING: Unrecogised rootprocess in kartturmain.readXMLprocesses: %(r)s' %{'r':proc.rootprocid}
                exit(exitStr)
