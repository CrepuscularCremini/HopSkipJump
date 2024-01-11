import fiona
import pandas as pd
import geopandas as gpd
import r5py
import datetime

import os

os.chdir(r'c:\users\brenn\documents\projects\HopSkipJump')

df = gpd.read_file(r"c:\users\brenn\documents\projects\HopSkipJump\Breweries\CanadaBreweries")
gtfs = [r"C:\Users\Brenn\Documents\Toronto\Classes\SpaceTime\f\networkAnalysis\poa\gtfs.zip"]
osm = r"C:\Users\Brenn\Documents\Toronto\Classes\SpaceTime\f\networkAnalysis\poa\toronto_canada.osm.pbf"

clip = gpd.read_file(r"C:\Users\Brenn\Downloads\toronto-boundary-wgs84\citygcs_regional_mun_wgs84.shp")

df.to_crs(epsg = 32617, inplace = True)
clip.to_crs(epsg = 32617, inplace = True)

df = df.clip(clip)
df.to_crs(epsg = 4326, inplace = True)

def hsjCalculator(df, osm, gtfs, name):

    try:
        df.id.head()
    except AttributeError:
        df.reset_index(inplace = True, names = ['id'])

    transport_network = r5py.TransportNetwork(
        osm,
        gtfs
    )

    walk = r5py.TravelTimeMatrixComputer(
        transport_network,
        origins=df,
        destinations=df,

        transport_modes= [r5py.TransportMode.WALK],
        speed_walking = 5,
        max_time = datetime.timedelta(minutes = 31)
    )

    walk_times = walk.compute_travel_times()
    walk_times.query('travel_time <= 30', inplace = True)

    bike = r5py.TravelTimeMatrixComputer(
        transport_network,
        origins=df,
        destinations=df,

        transport_modes= [r5py.TransportMode.BICYCLE],
        speed_cycling = 18,
        max_time = datetime.timedelta(minutes = 31),
        max_bicycle_traffic_stress = 2
    )

    bike_times = bike.compute_travel_times()
    bike_times.query('travel_time <= 30', inplace = True)

    transit = r5py.TravelTimeMatrixComputer(
        transport_network,
        origins=df,
        destinations=df,

        departure=datetime.datetime(2023, 1, 1, 8, 30),
        departure_time_window = datetime.timedelta(hours = 1),

        transport_modes= [r5py.TransportMode.TRANSIT,r5py.TransportMode.WALK],
        max_time = datetime.timedelta(minutes = 31)
    )

    transit_times = transit.compute_travel_times()
    transit_times.query('travel_time <= 30', inplace = True)


    mat = walk_times.merge(bike_times, on = ['from_id', 'to_id'], how = 'outer').merge(transit_times, on = ['from_id', 'to_id'], how = 'outer')

    df.to_file(f'SpiderMap/{name}_brew.geojson', driver = 'GeoJSON')

    mdf = df.merge(mat, left_on = 'id', right_on = 'to_id', how = 'right')
    mdf.to_file(f'SpiderMap/{name}_matrix.geojson', driver = 'GeoJSON')

hsjCalculator(df, osm, gtfs, 'Toronto')