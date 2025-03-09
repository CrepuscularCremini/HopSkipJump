import fiona
import pandas as pd
import geopandas as gpd
import r5py
import datetime
import numpy as np
import os
from shapely.geometry import Point
from random import uniform

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

## Functions

def brewsdaySource(df, odf, osm, gtfs, date, name, buffer = False):

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
    transit_times.rename(columns = {'travel_time_p20' : 'transit'}, inplace = True)

    mat = bike_times.merge(transit_times, on = ['from_id', 'to_id'], how = 'outer')

    odf = df.merge(mat, left_on = 'id', right_on = 'to_id')
    return odf

def brewsdayFilter(r, filter_list):
    rv = False
    bname = r['name'].lower()
    for comp in filter_list:
        if comp in bname:
            rv = True
    return rv

def brewsdayPick(vdf, imped = 'all_imped', impval = 2, bike_weight = 1, transit_weight = 1, filter_col = False, bike_max = False, transit_max = False):
#     gdf = gpd.read_file(fp)

# bike_max = None
# transit_max = None
# filter_col = 'brewery_filter'
# impval = 2
# bike_weight = 1
# transit_weight = 1

    if bike_max:
        vdf.query('bike <= @bike_max', inplace = True)
    if transit_max:
        vdf.query('transit <= @transit_max', inplace = True)
    if filter_col:
        vdf = vdf[vdf[filter_col] != True].copy()

    vdf[['bike', 'transit']] = vdf[['bike', 'transit']].fillna(60)

    vdf.reset_index(inplace = True)

    vdf['bike_imped'] = (1 / vdf.bike) ** impval
    vdf['transit_imped'] = (1 / vdf.transit) ** impval
    vdf['all_imped'] = vdf.bike_imped * bike_weight + vdf.transit_imped * transit_weight

    imped = 'all_imped'

    vdf['imped'] = vdf[imped] / vdf[imped].sum()

    vdf['lower'] = vdf.imped.shift(1, fill_value = 0).cumsum()
    vdf['upper'] = vdf.imped.cumsum()

    val = uniform(0, 1)
#     print(val)
    out_gdf = vdf.query('lower <= @val and upper > @val')

    print(out_gdf.id.values[0], out_gdf.name.values[0])

## Create Matrix

fp = r"Breweries\brewsday_picker.geojson"

run_matrix = False
if run_matrix:

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

    bds = brewsdaySource(df, odf, osm, gtfs, date, city)
    bds.to_file(fp, driver = 'GeoJSON')

## Create Filters

ep = "Breweries/BrewsdayEvents.csv"

be = pd.read_csv(ep)
be['Date'] = pd.to_datetime(be.Date, format = "%m/%d/%y")

tod = np.datetime64(datetime.datetime.today())
buff = tod - np.timedelta64(150, 'D')

be.query('Date >= @buff', inplace = True)
nb = be.Brewery.str.lower().values.tolist()

iss = '''Steadfast - not open on Tuesdays
Louis Cifer - perm closed
3 Brewers - big chain'''

iss = [x.split('-')[0].strip().lower() for x in iss.split('\n')]

ex_list = nb + iss

## Run Brewsday Selector

gdf = gpd.read_file(fp)
gdf['brewery_filter'] = gdf.apply(brewsdayFilter, args = [ex_list], axis = 1)

t = brewsdayPick(gdf, imped = 'all_imped', impval = 1, bike_weight = 1, transit_weight = 2, bike_max = 30, transit_max = 40, filter_col = 'brewery_filter')