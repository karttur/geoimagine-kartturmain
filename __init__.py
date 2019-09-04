"""
kartturXML
==========================================

Reads the standardizeed xml format of all process control for Karttur Geo Imagine framework

Functions
---------
readXML      -- reads the XML file

Author
------
Thomas Gumbricht (thomas.gumbricht@karttur.com)

"""
from .version import __version__, VERSION, metadataD
#from .process import UserProj, SetXMLProcess, CheckSetParamValues
from .proc20180305 import MainProc, Composition, LayerCommon, RegionLayer, VectorLayer, RasterLayer, UserProj, SetXMLProcess
from .timestep import TimeSteps

