import fiona
import pandas as pd
import geopandas as gpd
import r5py
import datetime
import os
from shapely.geometry import Point
from random import uniform

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

## Functions

def brewsdaySource(df, odf, osm, gtfs, date, name, fp):

    transport_network = r5py.TransportNetwork(
        osm,
        gtfs
    )

    bike = r5py.TravelTimeMatrixComputer(
        transport_network,
        origins=odf,
        destinations=df,

        transport_modes= [r5py.TransportMode.BICYCLE],
        speed_cycling = 18,
#         max_time = datetime.timedelta(minutes = 61),
        max_bicycle_traffic_stress = 2
    )

    bike_times = bike.compute_travel_times()
#     bike_times.query('travel_time <= 30', inplace = True)
    bike_times.rename(columns = {'travel_time' : 'bike'}, inplace = True)

    transit = r5py.TravelTimeMatrixComputer(
        transport_network,
        origins=odf,
        destinations=df,

        departure=date,
        departure_time_window = datetime.timedelta(minutes = 30),
        percentiles = [20],

        transport_modes= [r5py.TransportMode.TRANSIT,r5py.TransportMode.WALK],
#         max_time = datetime.timedelta(minutes = 61)
    )

    transit_times = transit.compute_travel_times()
#     transit_times.query('travel_time <= 30', inplace = True)
    transit_times.rename(columns = {'travel_time' : 'transit'}, inplace = True)

    mat = bike_times.merge(transit_times, on = ['from_id', 'to_id'], how = 'outer')

    odf = df.merge(mat, left_on = 'id', right_on = 'to_id')

    odf.to_file(fp)

def brewsdayPick(fp, imped = 'all_imped', impval = 2, bike_weight = 1, transit_weight = 1, idx_exclude = False, bike_max = False, transit_max = False):
    gdf = gpd.read_file(fp)

    if bike_max:
        gdf.query('bike <= @bike_max', inplace = True)
    if transit_max:
        gdf.query('transit <= @transit_max', inplace = True)
    if idx_exclude:
        gdf.query('id not in @idx_exclude', inplace = True)

    gdf[['bike', 'travel_tim']] = gdf[['bike', 'travel_tim']].fillna(60)

    gdf.reset_index(inplace = True)

    gdf['bike_imped'] = (1 / gdf.bike) ** impval
    gdf['transit_imped'] = (1 / gdf.travel_tim) ** impval
    gdf['all_imped'] = gdf.bike_imped * bike_weight + gdf.transit_imped * transit_weight

    imped = 'all_imped'

    gdf['imped'] = gdf[imped] / gdf[imped].sum()

    gdf['lower'] = gdf.imped.shift(1, fill_value = 0).cumsum()
    gdf['upper'] = gdf.imped.cumsum()

    val = uniform(0, 1)
#     print(val)
    out_gdf = gdf.query('lower <= @val and upper > @val')
    print(out_gdf.id.values[0], out_gdf.name.values[0])

## Run

fps = {'Toronto' : {'df' : r"c:\users\brenn\documents\projects\HopSkipJump\Breweries\OntarioBreweries",
                'gtfs' : [r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\ttc.zip"],
                'osm' : r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\toronto_canada.osm.pbf",
                'bbox' : (-79.5019,43.5938,-79.2296,43.6848),
                'date' : datetime.datetime(2024, 2, 1, 17, 30)}
        }

city = 'Toronto'

df = gpd.read_file(fps[city]['df'])
df.to_crs(epsg = 4326, inplace = True)
xmin, ymin, xmax, ymax = fps[city]['bbox']
df = df.cx[xmin:xmax, ymin:ymax].copy()

gtfs = fps[city]['gtfs']
osm = fps[city]['osm']
date = fps[city]['date']

start = (-79.4079, 43.6566)

odf = gpd.GeoDataFrame(pd.DataFrame.from_dict({'id' : [1], 'geometry' : [Point(start)]}), crs = 'EPSG:4326', geometry = 'geometry')

fp = r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\nrewsday"

# brewsdaySource(df, odf, osm, gtfs, date, city, fp)

gdf = gpd.read_file(fp)

idx = '''
170 - Halo - Mar 12
219 - Mascot Brewery - Mar 19
104 - Collective Arts - Mar 26
77  - Burdock - April 2
    - Trinity Commons - April 9
40  - Bellwoods Brewery - April 16
201 - Left Field - April 23
200 - (Left Field Other Location)
    - Blue Jays - April 30
    - International - April 30
163 - Goose Island - May 7
159 - Great Lakes Brewery - May 7
314 - Something in the Water - May 14
    - Bar Hop - May 21
    - Blue Jays - May 21
56  - Blood Brothers - May 25
170 - Halo - May 25
25  - Bandit - May 25
248 - Northern Maverick - May 28
356 - True History Brewing - June 4
295 - Saulter Street Brewery - June 11
129 - Eastbound Brewing Company - June 11
173 - High Park Brewery - June 18
15  - Amsterdam Brewhouse - June 25
    - International
48  - Big Rock Liberty Commons - July 9
201 - Left Field - July 9
172 - Henderson Brewing - July 16
    - Granite Brewing - July 20
    - Blue Jays - July 23
'''

idx = [x.split('-')[0].strip() for x in idx.split('\n')]
idx = [int(x) for x in idx if x != '']

ab = '''
37 - Belgian Moon
325 - Steam Whistle
'''
ab = [x.split('-')[0].strip() for x in ab.split('\n')]
ab = [int(x) for x in ab if x != '']

iss = '''
324 - Steadfast - not open on Tuesdays
212  - Louis Cifer - perm closed
'''
iss = [x.split('-')[0].strip() for x in iss.split('\n')]
iss = [int(x) for x in iss if x != '']

def qual(v):
    if v in idx:
        return 'brewsday'
    elif v in ab or v in iss:
        return 'issue'
    else:
        return 'ripe'

gdf['thing'] = gdf.id.apply(qual)
# gdf.to_file(fp)

brewsdayPick(fp, imped = 'all_imped', impval = 0.5, bike_weight = 4, transit_weight = 2, bike_max = None, transit_max = None, idx_exclude = idx + ab + iss)

