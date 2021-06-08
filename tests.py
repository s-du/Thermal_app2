from tools import thermal_tools as tt
from tools import flir_image_extractor
import numpy as np
fir = flir_image_extractor.FlirImageExtractor()
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

"""img_folder = r'F:\3D studies 2021\20210222 - Vol diest\Thermique_for_app\draft_2'
tmin = -18
tmax = 8
mode = 'other'

tt.process_all_th_pictures(img_folder, tmin, tmax, 'plasma', mode)"""

#img_1 = r'C:\Users\sdu\Desktop\Python 2021\test_thermal_app\exemple2\therm (1).JPG'
#img_2 = r'C:\Users\sdu\Desktop\Python 2021\test_thermal_app\exemple2\therm (17).JPG'

"""
fir.get_print_meta(img_1)
fir.get_print_meta(img_2)
"""


# fir.process_image(img_1, img_2, raw_output=False)
# fir.plot()

#fir.process_image(img_1, img_2)
#fir.plot()

#fir.raw2temp(2000, fir.meta)

"""
a = fir.raw2temp(1500, E=fir.meta['Emissivity'], OD=fir.default_distance, RTemp=fir.extract_float(
                                                                              fir.meta['ReflectedApparentTemperature']),
                                                                          ATemp=fir.extract_float(
                                                                              fir.meta['AtmosphericTemperature']),
                                                                          IRWTemp=fir.extract_float(
                                                                              fir.meta['IRWindowTemperature']),
                                                                          IRT=fir.meta['IRWindowTransmission'],
                                                                          RH=fir.extract_float(
                                                                              fir.meta['RelativeHumidity']),
                                                                          PR1=fir.meta['PlanckR1'], PB=fir.meta['PlanckB'],
                                                                          PF=fir.meta['PlanckF'],
                                                                          PO=fir.meta['PlanckO'], PR2=fir.meta['PlanckR2'])

b = fir.raw2temp(3000, E=fir.meta['Emissivity'], OD=fir.default_distance, RTemp=fir.extract_float(
                                                                              fir.meta['ReflectedApparentTemperature']),
                                                                          ATemp=fir.extract_float(
                                                                              fir.meta['AtmosphericTemperature']),
                                                                          IRWTemp=fir.extract_float(
                                                                              fir.meta['IRWindowTemperature']),
                                                                          IRT=fir.meta['IRWindowTransmission'],
                                                                          RH=fir.extract_float(
                                                                              fir.meta['RelativeHumidity']),
                                                                          PR1=fir.meta['PlanckR1'], PB=fir.meta['PlanckB'],
                                                                          PF=fir.meta['PlanckF'],
                                                                          PO=fir.meta['PlanckO'], PR2=fir.meta['PlanckR2'])

c = fir.raw2temp(4500, E=fir.meta['Emissivity'], OD=fir.default_distance, RTemp=fir.extract_float(
                                                                              fir.meta['ReflectedApparentTemperature']),
                                                                          ATemp=fir.extract_float(
                                                                              fir.meta['AtmosphericTemperature']),
                                                                          IRWTemp=fir.extract_float(
                                                                              fir.meta['IRWindowTemperature']),
                                                                          IRT=fir.meta['IRWindowTransmission'],
                                                                          RH=fir.extract_float(
                                                                              fir.meta['RelativeHumidity']),
                                                                          PR1=fir.meta['PlanckR1'], PB=fir.meta['PlanckB'],
                                                                          PF=fir.meta['PlanckF'],
                                                                          PO=fir.meta['PlanckO'], PR2=fir.meta['PlanckR2'])

d = fir.raw2temp(6000, E=fir.meta['Emissivity'], OD=fir.default_distance, RTemp=fir.extract_float(
                                                                              fir.meta['ReflectedApparentTemperature']),
                                                                          ATemp=fir.extract_float(
                                                                              fir.meta['AtmosphericTemperature']),
                                                                          IRWTemp=fir.extract_float(
                                                                              fir.meta['IRWindowTemperature']),
                                                                          IRT=fir.meta['IRWindowTransmission'],
                                                                          RH=fir.extract_float(
                                                                              fir.meta['RelativeHumidity']),
                                                                          PR1=fir.meta['PlanckR1'], PB=fir.meta['PlanckB'],
                                                                          PF=fir.meta['PlanckF'],
                                                                          PO=fir.meta['PlanckO'], PR2=fir.meta['PlanckR2'])

print(a,b,c,d)
"""

img_source = r'C:\Users\sdu\Desktop\Python 2021\test_thermal_app\vol3_final\thermalMesh\mesh_th_processed(mesh 0)\ortho2.tif'
img = mpimg.imread(img_source)
imgplot = plt.imshow(img)