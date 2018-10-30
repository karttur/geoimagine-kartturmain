'''
Created on 23 feb. 2018

@author: thomasgumbricht
'''

from os import path

from geoimagine.postgresdb import  SelectProcess, SelectUser, SelectFileFormats, ManageAncillary, ManageSentinel, ManageLandsat, ManageMODIS, ManageSMAP 
from geoimagine.ancillary import ProcessAncillary
from geoimagine.sentinel import ProcessSentinel
from geoimagine.landsat import ProcessLandsat
from geoimagine.modis import ProcessModis
from geoimagine.smap import ProcessSmap
#from geoimagine.postgresdb import ReadUserCreds
#from geoimagine.setup_processes import ProcessProcess
#from geoimagine.kartturXML import ReadXMLuser
#from geoimagine.karttur_main_old import ProcessLayout
from geoimagine.kartturmain import UserProj, SetXMLProcess, MainProc
import xmltodict
 
def ReadXMLProcesses(projFPN,verbose):
    '''
    Run processes
    '''
    srcFP = path.join(path.split(projFPN)[0],'xml')
    #Read the textfile with links to the xml files defining schemas and tables
    with open(projFPN) as f:
        xmlL = f.readlines()
    # Remove whitespace characters like `\n` at the end of each line
    xmlL = [path.join(srcFP, x.strip())  for x in xmlL if len(x) > 10 and x[0] != '#'] 

    #Get the fileformats required for all processing
    '''
    session = SelectFileFormats()
    gdalofD = session._SelectGDALof()
    session._Close()
    '''
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
        print ('You are entering as user:', userId)   
        #Connect to the Postgres Server, each xml must be checked to have an allowed user
        session = SelectProcess()
        #Get the tagAttrL for userProj
        print (session.name)
        tagAttrL = session._SelectProcessTagAttr('userproj', 'root', 'userproj')  
        print ('tagAttrL',tagAttrL)

        userProj = UserProj(userProjOD,tagAttrL)
        # set user credentials
        userProj._SetCredentials(userCat, userStratum, userProjs=userProjs, userTracts=userTracts, userSites=userSites)

        #Check that the user owns the project and the plot/site/tract requested
        projSetting = userProj._CheckUserProj()
        print ('projSetting',projSetting)

        if not projSetting:
            warnstr = 'User does not own the project'
            print (warnstr)
            session._Close()
            continue
        #Get the default region for the tract/site
        projSetting = userProj._GetDefRegion(session)
        print ('projSetting',userProj.defregion)

        '''
        #GET THE DEFAULT PERIOD, IF ANY
        tagAttrL = session._SelectProcessTagAttr('periodicity','process','period') 
        if 'period' in content:
            period = content['period']
        else:
            period = {}

        periodD = CheckSetParamValues(tagAttrL, period)[0]
        #periodicity = Periodicity(periodD)
        '''
        processesDL = content['process']
        #Check if this is a single process, if so create a list with the single process
        if not type(processesDL) is list:
            processesDL = [processesDL]
    
        for processD in processesDL:

            processid = processD['@processid']
            #Instantiate Process
            proc = SetXMLProcess(userProj, processid, content, session, verbose)
            
            #check that user has the right to this process
            permit = proc._CheckPermission(session)
            if not permit:
                ERRORCHECK
                continue
            

            #Check the input parameters
            errorD = proc._CheckParams(processD, session)

            

            procL.append(proc)
        #all the data is read, process the data
        procLL.append(procL)
        session._Close()
    return userProj, procLL

def RunProcesses(userProj, procLL):
    for procL in procLL:
        #session = ReadUserCreds()
        for proc in procL:
            print ('rootprocid',proc.rootprocid)
            print ('processid',proc.processid)
            print('overwrite',proc.overwrite)

            if proc.rootprocid == 'LayoutProc':
                session = ManageLayout()
                ProcessLayout(session,p)
                session._Close()
            elif proc.rootprocid == 'Ancillary':
                session = ManageAncillary()
                process = MainProc(userProj,proc,session,verbose)
                print (process.params)

                ProcessAncillary(process,session,verbose)
                session._Close()
            elif proc.rootprocid == 'SentinelProcess':
                session = ManageSentinel()

                process = MainProc(userProj,proc,session,verbose)

                ProcessSentinel(process,session,verbose)
                session._Close()
                
            elif proc.rootprocid == 'LandsatProc':
                session = ManageLandsat()

                process = MainProc(userProj,proc,session,verbose)

                ProcessLandsat(process,session,verbose)
                session._Close()
            elif proc.rootprocid == 'MODISProc':
                session = ManageMODIS()

                process = MainProc(userProj,proc,session,verbose)

                ProcessModis(process,session,verbose)
                session._Close()
            elif proc.rootprocid == 'SMAPProc':
                session = ManageSMAP()

                process = MainProc(userProj,proc,session,verbose)

                ProcessSmap(process,session,verbose)
                session._Close()
            else:
                exitStr = 'EXITING: Unrecogised rootprocess in kartturmain.runxml: %(r)s' %{'r':proc.rootprocid}
                exit(exitStr)
    
if __name__ == "__main__":
    prodDB = 'postgres'
    '''
    SetupSchemasTables creates schemas and tables from xml files, with the relative path to the
    xml files given in the plain text file "projFPN".
    '''
    verbose = True
    #projFN = '/Users/thomasgumbricht/Dropbox/projects/geoimagine/USERS/karttur/defaultpalettes/palettes_karttur_setup_20180221_0.txt'
    #Import ancillary data and add to db
    #projFN = '/Users/thomasgumbricht/Dropbox/projects/geoimagine/USERS/karttur/ancillary/ancillary_karttur_setup_20180221_0.txt'

    #projFN ='/Users/thomasgumbricht/Dropbox/projects/geoimagine/USERS/karttur/climateindex/climindex_karttur_setup_20180221_0.txt'
    #Extract sentinel coords
    #projFN ='/Users/thomasgumbricht/Dropbox/projects/geoimagine/USERS/karttur/sentinel/extract_sentinel_coords_20180808_0.txt'
    #Get sentinel data
    projFN ='/Users/thomasgumbricht/Dropbox/projects/geoimagine/USERS/karttur/sentinel/get_sentinel_arktis_20180608_0.txt'
    
    projFN ='/Users/thomasgumbricht/Dropbox/projects/geoimagine/USERS/karttur/landsat/extract_landsat_coords_20181007_0.txt'

    projFN ='/Users/thomasgumbricht/Dropbox/projects/geoimagine/USERS/karttur/MODIS/modis_20181009_0.txt'
    userProj, procLL = ReadXMLProcesses(projFN,verbose)
    
    projFN ='/Users/thomasgumbricht/Dropbox/projects/geoimagine/USERS/karttur/SMAP/smap_20181009_0.txt'
    projFN ='/Users/thomasgumbricht/Dropbox/projects/geoimagine/USERS/karttur/SMAP/smap_20181009_0.txt'
    userProj, procLL = ReadXMLProcesses(projFN,verbose)
    '''
    for procL in procLL:
        for proc in procL:
            print ('proc',proc)
            print (proc.rootprocid)
            print (proc.paramsD)
            print (proc.overwrite)
    '''
    RunProcesses(userProj, procLL)
    