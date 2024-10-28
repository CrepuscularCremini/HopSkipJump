import pandas as pd
import geopandas as gpd
import numpy as np

import geopy
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

from shapely.geometry import Point

import os

os.chdir(r'C:\Users\Brenn\Documents\Projects\HopSkipJump')

df = pd.read_html('https://www.reddit.com/r/torontocraftbeer/wiki/craftbeerbars/', extract_links = 'all')[0]

df[['name', 'web']] = df.apply(lambda r: r[('Name and website', None)], result_type = 'expand', axis = 1)

df['location'] = df[('Location', None)].apply(lambda x: x[0])
# df['highlights'] = df[('Highlights', None)].apply(lambda x: x[0])

df = df[['name', 'web', 'location']].copy()

locator = Nominatim(user_agent='geocode')
geocode = RateLimiter(locator.geocode, min_delay_seconds=1)

df['address'] = df.location.apply(lambda s: "{}, Toronto, Ontario, Canada".format(s.split('&')[0]))

df['geocode'] = df['address'].apply(geocode)

df['point'] = df.geocode.apply(lambda x: x[-1] if pd.notna(x) else np.nan)
df['point'] = df.point.apply(lambda x: (x[1], x[0]) if pd.notna(x) else np.nan)
df['geometry'] = df.point.apply(lambda x: Point(x) if pd.notna(x) else np.nan)

gdf = gpd.GeoDataFrame(df, geometry = 'geometry', crs = 'epsg:4326')

gdf[['name', 'web', 'location', 'geometry']].to_file('BeerHalls')