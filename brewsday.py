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

def brewsdaySource(df, osm, gtfs, departure, name, fp):

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
        max_time = datetime.timedelta(minutes = 31),
        max_bicycle_traffic_stress = 2
    )

    bike_times = bike.compute_travel_times()
    bike_times.query('travel_time <= 30', inplace = True)
    bike_times.rename(columns = {'travel_time' : 'bike'}, inplace = True)

    transit = r5py.TravelTimeMatrixComputer(
        transport_network,
        origins=odf,
        destinations=df,

        departure=date,
        departure_time_window = datetime.timedelta(minutes = 30),
        percentiles = [50],

        transport_modes= [r5py.TransportMode.TRANSIT,r5py.TransportMode.WALK],
        max_time = datetime.timedelta(minutes = 31)
    )

    transit_times = transit.compute_travel_times()
    transit_times.query('travel_time <= 30', inplace = True)
    transit_times.rename(columns = {'travel_time' : 'transit'}, inplace = True)

    mat = bike_times.merge(transit_times, on = ['from_id', 'to_id'], how = 'outer')

    odf = df.merge(mat, left_on = 'id', right_on = 'to_id')

    odf.to_file(fp)

def brewsdayPick(fp, imped = 'all_imped', idx_exclude = False, bike_max = False, transit_max = False):
    gdf = gpd.read_file(fp)

    if bike_max:
        gdf.query('bike <= @bike_max', inplace = True)
    if transit_max:
        gdf.query('transit <= @transit_max', inplace = True)
    if idx_exclude:
        gdf.query('id not in @idx_exclude', inplace = True)

    gdf[['bike', 'transit']] = gdf[['bike', 'transit']].fillna(60)

    gdf.reset_index(inplace = True)

    gdf['bike_imped'] = (1 / gdf.bike) ** 2
    gdf['transit_imped'] = (1 / gdf.transit) ** 2
    gdf['all_imped'] = gdf.bike_imped + gdf.transit_imped

    imped = 'all_imped'

    gdf['imped'] = gdf[imped] / gdf[imped].sum()

    gdf['lower'] = gdf.imped.shift(1, fill_value = 0).cumsum()
    gdf['upper'] = gdf.imped.cumsum()

    val = uniform(0, 1)
#     print(val)
    out_gdf = gdf.query('lower <= @val and upper > @val')
    print(out_gdf.id.values[0], out_gdf.name.values[0])

## Run

# fps = {'Toronto' : {'df' : r"c:\users\brenn\documents\projects\HopSkipJump\Breweries\CanadaBreweries",
#                 'gtfs' : [r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\ttc.zip"],
#                 'osm' : r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\toronto_canada.osm.pbf",
#                 'bbox' : (-79.5019,43.5938,-79.2296,43.6848),
#                 'date' : datetime.datetime(2024, 2, 1, 17, 30)}
#         }
#
#
# city = 'Toronto'
#
# df = gpd.read_file(fps[city]['df'])
# df.to_crs(epsg = 4326, inplace = True)
# xmin, ymin, xmax, ymax = fps[city]['bbox']
# df = df.cx[xmin:xmax, ymin:ymax].copy()
#
# gtfs = fps[city]['gtfs']
# osm = fps[city]['osm']
# date = fps[city]['date']
#
# start = (-79.39949, 43.66239)
#
# odf = gpd.GeoDataFrame(pd.DataFrame.from_dict({'id' : [1], 'geometry' : [Point(start)]}), crs = 'EPSG:4326', geometry = 'geometry')

fp = r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\brewsday"

idx = [507, 492, 1086, 505, 1255, 1212, 491, 490] # been to on Brewsday
ab = [487, 488, 493] # not vibing
iss = [502, 515, 1178, 495] # necessary exclusions
    # 502 - Kensington Brewery - not open
    # 515 - Ace Hill -
    # 1178 - Steadfast - not open on Tuesdays
    # 495 - Laylow - permanently closed

brewsdayPick(fp, imped = 'all_imped', idx_exclude = idx + ab + iss, bike_max = 20)