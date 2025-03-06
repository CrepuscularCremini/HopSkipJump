import pandas as pd
import geopandas as gpd

import os

os.chdir('/home/moonbeam/Documents/HopSkipJump')

brews = gpd.read_file('Data/ontario_breweries.geojson')
stations = gpd.read_file('Trekkables/ontario_stations.geojson')
lanes = gpd.read_file('Data/ontario_bike.geojson')

brews.to_crs(epsg = 2952, inplace = True)
stations.to_crs(epsg = 2952, inplace = True)
lanes.to_crs(epsg = 2952, inplace = True)

## Lane Classifier

bics = {'cycle_track' : 'High',
'local_street_bikeway' : 'High',
'bike_path' : 'High',

'multi_use_path' : 'Medium',

'painted_bike_lane' : 'Low'}

# 'shared_roadway',
# 'major_shared_roadway',
# 'gravel_trail',

lanes['Comfort'] = lanes.canbics_class.map(bics)
lanes.dropna(subset = 'Comfort', inplace = True)

lanes[['fid', 'Comfort', 'geometry']].to_crs(epsg = 4326).to_file('Trekkables/ontario_bics.geojson')

## Buffer (simple)

stations['buffer'] = stations.buffer(1000)
lanes['buffer'] = lanes.buffer(1000)

sa = stations.set_geometry('buffer')[['buffer']]
sa['StationArea'] = 'Yes'
sa = sa.dissolve('StationArea')

la = lanes.set_geometry('buffer')[['buffer']]
la['LaneArea'] = 'Yes'
la = la.dissolve('LaneArea')

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

