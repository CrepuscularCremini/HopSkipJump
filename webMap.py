import pandas as pd
import geopandas as gpd
import os
from shapely.geometry import LineString
import matplotlib.pyplot as plt

os.chdir(r'c:\users\brenn\documents\projects\HopSkipJump')

ttm = pd.read_csv('HSJ_Breweries/ttm_denver.csv')
gdf = gpd.read_file('HSJ_Breweries/DenverBreweries')

gdf.reset_index(inplace = True, names = 'id')

jgdf = gdf[['id', 'Name', 'geometry']].copy()

ndf = ttm.merge(jgdf, left_on = 'from_id', right_on = 'id', how = 'inner').merge(jgdf, left_on = 'to_id', right_on = 'id', how = 'inner', suffixes = ('_from', '_to'))

ndf['geometry'] = ndf.apply(lambda r: LineString([r.geometry_from, r.geometry_to]), axis = 1)

ndf = gpd.GeoDataFrame(ndf, crs = gdf.crs)

brew = ndf.query('from_id == 10 and from_id != to_id and travel_time <= 10')

fig, ax = plt.subplots()
brew.plot(color = 'lightgray', ax = ax, zorder = 0)
gdf.query('id in @brew.to_id.unique()').plot(color = 'darkblue', ax = ax, zorder = 1)
gdf.query('id in @brew.from_id.unique()').plot(color = 'red', ax = ax, zorder = 2)
plt.show()