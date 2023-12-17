
'''

Author: Ibe Ezuma
Purpose: Final Project
Date: Dec 9, 2023
'''

# 1. Import Modules
import arcpy
import sys
import os
print("importing modules. . .")
import arcpy, os,sys
from arcpy.sa import *

#  Set up path variables
root = sys.path[0]
literalPath=r"C:\Users\ibeez\Desktop\GEOS456\pythonProject"
gdb=os.path.join(root, "FinalProject_Data")

#  Set environments (workspace, overwriteOutput)
arcpy.env.workspace = gdb
arcpy.env.overwriteOutput = True


# Create CypressHills.gdb
arcpy.AddMessage("creating file geodatabase. . .")
arcpy.CreateFileGDB_management(gdb,"CypressHills.gdb","CURRENT")

#  Setting Spatial reference
sr = arcpy.SpatialReference("NAD 1983 UTM Zone 12N")

#  Create VectorFeatures feature dataset inside gdb
arcpy.AddMessage("creating feature datasets. . .")
arcpy.CreateFeatureDataset_management("CypressHills.gdb","VectorFeatures",sr)


# Use MosaicToNewRaster to merge the two DEMs
arcpy.env.workspace = os.path.join(gdb, "FinalProject.gdb")

deme=arcpy.Raster("deme")
demw=arcpy.Raster("demw")
arcpy.MosaicToNewRaster_management("deme; demw",os.path.join(gdb,"FinalProject.gdb"),"DEM1",sr,"16_BIT_UNSIGNED","10", "1", "LAST","FIRST")

# Clip DEM to Cypress Hills Park boundary, save as DEM
DEM1=arcpy.Raster("DEM1")
cb = os.path.join(gdb,"FinalProject.gdb","Base","CypressHillsBndry")
arcpy.Clip_management(DEM1,cb,os.path.join(gdb,"CypressHills.gdb","DEM"),cb,"0","ClippingGeometry","MAINTAIN_EXTENT")

# Clip Roads and Rivers and export to VectorFeatures dataset in CypressHills.gdb
arcpy.env.workspace = os.path.join(gdb, "CypressHills.gdb")
arcpy.Clip_analysis(os.path.join(gdb,"FinalProject.gdb","Base","Roads"),cb,os.path.join(gdb, "CypressHills.gdb","VectorFeatures","Roads"))
arcpy.Clip_analysis(os.path.join(gdb,"FinalProject.gdb","Base","Rivers"),cb,os.path.join(gdb, "CypressHills.gdb","VectorFeatures","Rivers"))

# Use Select to select by attributes the facilities and wells feature classes and export selected features to the VectorFeatures dataset

arcpy.Select_analysis(os.path.join(gdb,"FinalProject.gdb","Oil_Gas","Facilities"),os.path.join(gdb,"CypressHills.gdb","VectorFeatures","Start"), "UFI = 'A21605053'")
arcpy.Select_analysis(os.path.join(gdb,"FinalProject.gdb","Oil_Gas","Wells"),os.path.join(gdb,"CypressHills.gdb","VectorFeatures","End"), "UWID = '0074013407000'")

# Create slope raster
arcpy.AddMessage("creating slope raster")
DEM=arcpy.Raster("DEM")
slope= Slope("DEM")
slope.save("Slope")

# Create Euclidean distance buffer rasters for Rivers and Roads
arcpy.AddMessage("creating Euclidean distance buffer rasters for Rivers and Roads")
Euclidean_Roads1=DistanceAccumulation("Roads","#","DEM")
Euclidean_Rivers1=DistanceAccumulation("Rivers","#", "DEM")
Euclidean_Roads1.save(os.path.join(gdb,"CypressHills.gdb","Euclidean_Roads"))
Euclidean_Rivers1.save(os.path.join(gdb,"CypressHills.gdb","Euclidean_Rivers"))

#  Reclassify Slope, Landcover, Euclidean_Roads and Euclidean_Rivers

# Reclass_Slope
arcpy.AddMessage("reclassifying slope")
myRemapRange = RemapRange([[0, 4, 1], [4, 10, 2], [10, 100, 3]])
Reclass_Slope1=Reclassify("Slope", "VALUE", myRemapRange)
Reclass_Slope1.save(os.path.join(gdb,"CypressHills.gdb","Reclass_Slope"))

#Reclass_Landcover
arcpy.AddMessage("reclassifying landcover")
myRemapValue = RemapRange([[1, 3], [2, 1], [3, 1], [4, 1], [5, 2], [6, 3], [7, 3]])
Reclass_land1=Reclassify(os.path.join(gdb,"FinalProject.gdb","Landcover"), "VALUE", myRemapValue)
Reclass_land1.save(os.path.join(gdb,"CypressHills.gdb","Reclass_Landcover"))

#Reclass_Rivers
arcpy.AddMessage("reclassifying river")
arcpy.Clip_management("Euclidean_Rivers",cb,os.path.join(gdb,"CypressHills.gdb","ERv"),cb,"","ClippingGeometry","NO_MAINTAIN_EXTENT")
myRemapRange = RemapRange([[0, 50, 3], [50, 250, 2], [250, 2890, 1]])
Reclass_Rivers1=Reclassify(os.path.join(gdb,"CypressHills.gdb","ERv"), "VALUE", myRemapRange)
Reclass_Rivers1.save(os.path.join(gdb,"CypressHills.gdb","Reclass_Rivers"))

#Reclass_Roads
arcpy.AddMessage("reclassifying road")
arcpy.Clip_management("Euclidean_Roads",cb,os.path.join(gdb,"CypressHills.gdb","ERd"),cb,"","ClippingGeometry","NO_MAINTAIN_EXTENT")
myRemapRange = RemapRange([[0, 30, 1], [30, 250, 2], [250, 3695, 3]])
Reclass_Roads1=Reclassify(os.path.join(gdb,"CypressHills.gdb","ERd"), "VALUE", myRemapRange)
Reclass_Roads1.save(os.path.join(gdb,"CypressHills.gdb","Reclass_Roads"))


# Use Weighted Overlay tool to create the CostSurface Raster
arcpy.AddMessage("using Weighted Overlay tool to create the CostSurface Raster")
myWOTable = WOTable([["Reclass_Slope", 15, "VALUE", RemapValue([[1, 1], [2, 2], [3, 3],["NODATA", "NODATA"]])],
                     ["Reclass_Landcover", 30, "VALUE", RemapValue([[1, 1], [2, 2], [3, 3],["NODATA", "NODATA"]])],
                     ["Reclass_Rivers", 40, "VALUE",RemapValue([[1, 1], [2, 2], [3, 3],["NODATA", "NODATA"]])],
                     ["Reclass_Roads", 15, "VALUE", RemapValue([[1, 1], [2, 2], [3, 3],["NODATA", "NODATA"]])]],[1, 3, 1])

outWeightedOverlay = WeightedOverlay(myWOTable)
outWeightedOverlay.save(os.path.join(gdb,"CypressHills.gdb","CostSurface"))

# Create cost distance raster
arcpy.AddMessage("creating cost distance raster")
outCostDist = CostDistance(os.path.join(gdb,"CypressHills.gdb","VectorFeatures","Start"),"CostSurface","#","CostBackLink")
outCostDist.save(os.path.join(gdb,"CypressHills.gdb","CostDistance"))


outCostPath = CostPath(os.path.join(gdb,"CypressHills.gdb","VectorFeatures","End"),"CostDistance","CostBackLink","EACH_CELL")
outCostPath.save(os.path.join(gdb,"CypressHills.gdb","CostPath"))

# Convert CostPath raster to polyline

arcpy.AddMessage("converting CostPath raster to polyline")
arcpy.RasterToPolyline_conversion("CostPath",os.path.join(gdb,"CypressHills.gdb","VectorFeatures","Pipeline"))

arcpy.ia.ZonalStatisticsAsTable(cb,"LAYER","DEM","MeanElevation","", "MEAN")

with arcpy.da.SearchCursor("MeanElevation","MEAN") as cursor:
    for row in cursor:
        print("The Mean Elevation in metres  is:", row[0])

arcpy.ia.ZonalStatisticsAsTable(cb,"LAYER","Slope","MeanSlope","", "MEAN")
with arcpy.da.SearchCursor("MeanSlope","MEAN") as cursor:
    for row in cursor:
        print("The Mean Slope in degrees is:", row[0])

cl=os.path.join(gdb,"FinalProject.gdb","Landcover")
arcpy.ia.ZonalStatisticsAsTable(cl,"VALUE",cl,"AreaLandcover","", "MEAN")
with arcpy.da.SearchCursor("AreaLandcover",["VALUE","AREA"]) as cursor:
    for row in cursor:
        if row[0]==1:
            print("The Area covered by Cropland in cubic metres:", row[1])

        elif row [0]==2:
            print("The Area covered by Forage in cubic metres :", row[1])

        elif row [0]==3:
            print("The Area covered by Grasslands in cubic metres :", row[1])

        elif row [0]==4:
            print("The Area covered by Shrubs in cubic metres:", row[1])

        elif row [0]==5:
            print("The Area covered by Trees in cubic metres  :", row[1])

        else:
            print("The Area covered by Water bodies in cubic metres:", row[1])



#Total length of proposed pipeline (use geometry token)
with arcpy.da.SearchCursor(os.path.join(gdb,"CypressHills.gdb","VectorFeatures","Pipeline"),"SHAPE@LENGTH") as cursor:
    length = 0
    for row in cursor:
        length += row[0]
print("The total length of the Pipeline in metres is :", length)

arcpy.AddMessage("creating layer files. . .")
arcpy.MakeFeatureLayer_management(cb,"CypressHills_Bndry")
arcpy.SaveToLayerFile_management("CypressHills_Bndry", "CypressHillsBndry")

arcpy.MakeFeatureLayer_management(os.path.join(gdb,"CypressHills.gdb","VectorFeatures","Start"),"start")
arcpy.SaveToLayerFile_management("start", "Start")

arcpy.MakeFeatureLayer_management(os.path.join(gdb,"CypressHills.gdb","VectorFeatures","End"),"end")
arcpy.SaveToLayerFile_management("end", "End")

arcpy.MakeFeatureLayer_management(os.path.join(gdb,"CypressHills.gdb","VectorFeatures","Roads"),"road")
arcpy.SaveToLayerFile_management("road", "Roads")

arcpy.MakeFeatureLayer_management(os.path.join(gdb,"CypressHills.gdb","VectorFeatures","Rivers"),"river")
arcpy.SaveToLayerFile_management("river", "Rivers")

arcpy.MakeFeatureLayer_management(os.path.join(gdb,"CypressHills.gdb","VectorFeatures","Pipeline"),"pipeline")
arcpy.SaveToLayerFile_management("pipeline", "Pipeline")

aprx = arcpy.mp.ArcGISProject(os.path.join(gdb,"FinalProject.aprx"))
mp = aprx.listMaps("Map")[0]

lyrPath=[]
arcpy.env.workspace=gdb
for l in arcpy.ListFiles("*.lyrx"):
    path=arcpy.Describe(l)
    fp=os.path.join(gdb,path.basename+".lyrx")
    lyrPath.append(fp)


arcpy.env.workspace = os.path.join(gdb, "CypressHills.gdb")


arcpy.AddMessage("adding layers to map. . .")

for l in lyrPath:
    if l ==os.path.join(gdb,"CypressHillsBndry.lyrx"):
        m = arcpy.mp.LayerFile(l)
        mp.addLayer(m,"BOTTOM")
    else:
        m = arcpy.mp.LayerFile(l)
        mp.addLayer(m,"TOP")

arcpy.AddMessage("adding basemap. . .")
mp.addBasemap("Topographic")


lyt = aprx.listLayouts("Layout")[0]
mf = lyt.listElements("MAPFRAME_ELEMENT")[0]
Desc=arcpy.Describe(cb)
ext=Desc.extent
mf.camera.setExtent(ext)

arcpy.env.workspace=gdb
arcpy.AddMessage("exporting PDF. . .")
lyt = aprx.listLayouts("Layout")[0]
lyt.exportToPDF = (os.path.join(gdb,"Cypress Hills Proposed Pipeline 8.5x11 Landscape.pdf"))

aprx.saveACopy(os.path.join(gdb,"FinalProject_Updated.aprx"))

arcpy.env.workspace = os.path.join(gdb, "CypressHills.gdb")
arcpy.AddMessage("deleting unwanted files. . .")
arcpy.Delete_management(os.path.join(gdb,"CypressHills.gdb","Euclidean_Roads"))
arcpy.Delete_management(os.path.join(gdb,"CypressHills.gdb","Euclidean_Rivers"))
arcpy.Delete_management(os.path.join(gdb,"CypressHills.gdb","ERv"))
arcpy.Delete_management(os.path.join(gdb,"CypressHills.gdb","ERd"))


arcpy.env.workspace=gdb
for l in arcpy.ListFiles("*.lyrx"):
    file=os.path.join(gdb,l)
    os.remove(file)

arcpy.AddMessage("Project is Done!!!!")
