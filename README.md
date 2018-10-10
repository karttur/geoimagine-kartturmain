# geoimagine-kartturmain

Karttur Geoimagine main python project

## Introduction

Karttur's GeoImagine Framework is an attempt for semi-automated processing of spatial data. In principle the Framework can handle data over any region at any spatial resolution. The intention is to allow different users to do different processing, and setup automated processing chains. That will probably never be fully implemented, and the Framework is more or less just a working environment that I have created for handling the projects I have. This post is about the Framework's _main_ package kartturmain that contains 7 python modules:

- \_\_init.py\_\_
- proc20180305.py
- RasterProcess.py
- runxml.py
- timespte.py
- version.py

### \_\_init.py\_\_

As with all other \_\_init.py\_\_ modules it is used for interfacing objects inside the package modules to be accessible to call from outside the package.

#### Dependencies

\_\_init.py\_\_ depends only on mudules included in the package itself.

#### Classes

\_\_init.py\_\_ does not contain any class definitions.

### proc20180305.py

This module contains the Framework central processor that interpretes the user definied processes, assembles the information, and then directs the compiled process object to the correct package (i.e. if you processes Landsat images, it will send the process object to the [landsat package](../geoimagine-landsat) etc).

#### Dependencies

The module proc20180305.py requires the timestep.py module from within the package, and the packages support.karttur_dt and gis.gis from the GeoImagigine Framework.

geoimagine.kartturmain.timestep
geoimagine.support.karttur_dt
geoimagine.gis.gis

#### Classes

- LayerCommon
- Layer(LayerCommon)
- VectorLayer(Layer)
- RasterLayer(Layer)
- RegionLayer(Layer)
- TextLayer(Layer)
- Location
- Composition
- UserProj
- SetXMLProcess
- MainProc

### RasterProcess.py

Temporarily put in kartturmain, should be moved to a raster package

### runxml.py

runxml.py is the starting point for executing user defined processes. The module expects a text file linking to one or more xml files defining the (sequence of) process(es) to run. The full path to the text file must be given, e.g:
```
projFN ='/Users/thomasgumbricht/Dropbox/projects/geoimagine/USERS/karttur/MODIS/modis_20181009_0.txt'
```
The project file (projFN) is opened and all non-commented (#) lines are read and interpreted as xml files and the commands in the xml files are read and compiled to process objects.
```
##### MODIS #####
#Search datapool for modis tiles
modis-search_data-pool.xml
```
The xml files must contain data that is specific for each process. (I NEED TO WRITE THAT BLOG). The xml file called from the txt file above contains the following commands:
```
<?xml version='1.0' encoding='utf-8'?>
<searchdatapool>
	<userproj userid = 'karttur' projectid = 'karttur' tractid= 'karttur' siteid = '*' plotid = '*' system = 'modis'></userproj>
	<period startyear = '2001' endyear = '2018' timestep='8D'></period>

	<process processid ='searchDataPool' dsversion = '1.3'>
		<parameters product="MYD09A1" version="006" serverurl="http://e4ftl01.cr.usgs.gov" ></parameters>
		<dstpath volume = "Karttur2tb" mainpath = "/Volumes/Karttur2tb/Downloads/MODIS" hdrfiletype = "shp" datfiletype = "shp"></dstpath>
	</process>

	<process processid ='searchDataPool' dsversion = '1.3'>
		<parameters product="MOD09A1" version="006" serverurl="http://e4ftl01.cr.usgs.gov" ></parameters>
		<dstpath volume = "Karttur2tb" mainpath = "/Volumes/Karttur2tb/Downloads/MODIS" hdrfiletype = "shp" datfiletype = "shp"></dstpath>
	</process>

	<process processid ='searchDataPool' dsversion = '1.3'>
		<parameters product="MCD43A4" version="006" serverurl="http://e4ftl01.cr.usgs.gov" ></parameters>
		<dstpath volume = "Karttur2tb" mainpath = "/Volumes/Karttur2tb/Downloads/MODIS" hdrfiletype = "shp" datfiletype = "shp"></dstpath>
	</process>

</searchdatapool>
```
#### Dependencies

As runxml.py calls all processing, it must call all other GeoImagine packages.

- geoimagine.postgresdb
- geoimagine.ancillary
- geoimagine.sentinel
- geoimagine.landsat
- geoimagine.modis
- geoimagine.smap
- geoimagine.kartturmain (UserProj, SetXMLProcess, MainProc)

#### Classes

runxml.py does not define any class.

### timestep.py

The timestep.py module translates the process xml files definition of temporal coverage and temporal frequency to actual dates (as a list and a dictionary).

#### Dependencies

- geoimagine.support.karttur_dt
- geoimagine.ktpandas

#### Classes

- TimeSteps

### version.py

version.py just define the version number.

