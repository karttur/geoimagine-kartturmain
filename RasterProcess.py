'''
Created on 12 juni 2018

@author: thomasgumbricht
'''
import os
import numpy as np

class Overlay:
    '''
    '''
    def __init__(self, params, srcD, dstD):
        pass
    
        if params.overlay == 'add':
            pass
    
def SetMask(system,params, srcLayer, maskLayer, dstLayer):
    if srcLayer.FPN == dstLayer.FPN:
        ERRORCHECK
    
    srcLayer.ReadRasterLayer()
    maskLayer.ReadRasterLayer()
    maskNull = params.maskNull
    dstNull = dstLayer.comp.cellnull
    #dstNull is the same as srcNull
    dstNull = self.srcData.compD[srcKey].cellnull
    BAND = srcLayer.BAND
    BAND[maskLayer.BAND == maskNull] = dstNull
    dstLayer.BAND = BAND
    dstLayer.WriteRasterLayer() 
    #Set masked = True
    dstLayer.RegisterLayer(system)
    
def Reclass(srcLayer, dstLayer, reclass, inplace = False):
    '''
    '''
    #Open the srcLayer
    srcLayer.RasterOpenGetFirstLayer( mode = 'read')
    #read the srcLayer band
    srcLayer.layer.ReadBand()
    #Close the srcLayer
    srcLayer.DS.CloseDS()
    #Get srcnull
    srcNull = srcLayer.comp.cellnull
    #Get dstnull
    dstNull = dstLayer.comp.cellnull
    #copy src band as dst band
    dstBAND = np.copy(srcLayer.layer.NPBAND)
    #Get the src Band
    srcBAND = srcLayer.layer.NPBAND

    resetNull = False
    #Loop the reclass entries
    for item in reclass:
        if reclass[item]['op'] == '=': 
            if type(reclass[item]['val']) is list:
                ERRORCHECK
            else:
                print ('ordinary reclass', item, 'to', reclass[item]['val'])
                dstBAND[srcBAND == item] = reclass[item]['val']        
        elif reclass[item]['op'] == '>':
            dstBAND[srcBAND > item] = reclass[item]['val']
            if srcNull > reclass[item]['val']: resetNull = True
        elif reclass[item]['op'] == '<':
            dstBAND[srcBAND < item] = reclass[item]['val']
            if srcNull < reclass[item]['val']: resetNull = True
        elif reclass[item]['op'] == '>=':
            dstBAND[srcBAND >= item] = reclass[item]['val']
            if srcNull >= reclass[item]['val']: resetNull = True
        elif reclass[item]['op'] == '<=':
            dstBAND[srcBAND <= item] = reclass[item]['val']
            if srcNull <= reclass[item]['val']: resetNull = True
        else:
            RECLASSNOTSET

    #Reset null if required
    if resetNull:
        dstBAND[srcBAND == srcNull] = dstNull

    #Create dst geoformats
    dstLayer.SetGeoFormat(srcLayer.geoFormatD)
    #Set the reclassified band to the dst    
    dstLayer.BAND = dstBAND
    #create and write the reclass raster
    if dstLayer.FPN == srcLayer.FPN:
        if not inplace:
            exit('To replace the original layer in Reclass, you ave to set inplace to True')
    dstLayer.CreateDSWriteRasterArray() 
