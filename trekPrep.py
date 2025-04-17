import pandas as pd
import geopandas as gpd
import r5py

import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

import os
import datetime

##

brews = gpd.read_file('Breweries/OntarioBreweries')
stations = gpd.read_file('Trekkables/ontario_stations.geojson')
lanes = gpd.read_file('Trekkables/ontario_bics.geojson')

brews.to_crs(epsg = 2952, inplace = True)
stations.to_crs(epsg = 2952, inplace = True)
lanes.to_crs(epsg = 2952, inplace = True)

## Lane Classifier

# bics = {'cycle_track' : 'High',
# 'local_street_bikeway' : 'High',
# 'bike_path' : 'High',
#
# 'multi_use_path' : 'Medium',
#
# 'painted_bike_lane' : 'Low'}
#
# # 'shared_roadway',
# # 'major_shared_roadway',
# # 'gravel_trail',
#
# lanes['Comfort'] = lanes.canbics_class.map(bics)
# lanes.dropna(subset = 'Comfort', inplace = True)
#
# lanes[['fid', 'Comfort', 'geometry']].to_crs(epsg = 4326).to_file('Trekkables/ontario_bics.geojson')

## Buffer (simple)

stations['buffer'] = stations.buffer(1000)
lanes['buffer'] = lanes.buffer(1000)

sa = stations.set_geometry('buffer')[['buffer']]
sa['StationArea'] = 'Yes'
sa = sa.dissolve('StationArea').reset_index()

la = lanes.set_geometry('buffer')[['buffer']]
la['LaneArea'] = 'Yes'
la = la.dissolve('LaneArea').reset_index()

## Overlay

bj = brews.sjoin(sa, how = 'left', predicate = 'within', rsuffix = 's').sjoin(la, how = 'left', predicate = 'within', rsuffix = 'l')

bj.StationArea = bj.StationArea.fillna('No')
bj.LaneArea = bj.LaneArea.fillna('No')

## Classifier

def classifier(r):
    bike = r.LaneArea
    transit = r.StationArea

    if bike == 'Yes' and transit == 'Yes':
        return 'Bike and Transit'
    elif bike == 'Yes':
        return 'Bike'
    elif transit == 'Yes':
        return 'Transit'
    else:
        return 'Neither'

bj['trek'] = bj.apply(classifier, axis = 1)
bj.drop(columns = ['StationArea', 'LaneArea'], inplace = True)

bj.to_crs(epsg = 4326, inplace =True)

bj.to_file('Trekkables/ontario_trek_brews.geojson', driver = 'GeoJSON')

## Create color maps

bmap = LinearSegmentedColormap.from_list('blues', ['#eceff4', '#5e81ac'])
gmap = LinearSegmentedColormap.from_list('greens', ['#eceff4', '#a3be8c'])
pmap = LinearSegmentedColormap.from_list('purples', ['#eceff4', '#b48ead'])

b_list = []
g_list = []
p_list = []
for val in range(7):
    bl = mpl.colors.rgb2hex(bmap(val / 6))
    b_list.append(bl)

    gl = mpl.colors.rgb2hex(gmap(val / 6))
    g_list.append(gl)

    pl = mpl.colors.rgb2hex(pmap(val / 6))
    p_list.append(pl)

print(b_list)
print(g_list)
print(p_list)