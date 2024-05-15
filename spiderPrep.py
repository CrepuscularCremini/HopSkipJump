import fiona
import pandas as pd
import geopandas as gpd
import r5py
import datetime
import os

pd.set_option('display.max_rows', 500)
pd.set_option('display.max_columns', 500)
pd.set_option('display.width', 1000)

def hsjCalculator(df, osm, gtfs, departure, name):
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
    walk_times.rename(columns = {'travel_time' : 'walk'}, inplace = True)

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
    bike_times.rename(columns = {'travel_time' : 'bike'}, inplace = True)

    transit = r5py.TravelTimeMatrixComputer(
        transport_network,
        origins=df,
        destinations=df,

        departure=date,
        departure_time_window = datetime.timedelta(hours = 1),

        transport_modes= [r5py.TransportMode.TRANSIT,r5py.TransportMode.WALK],
        max_time = datetime.timedelta(minutes = 31)
    )

    transit_times = transit.compute_travel_times()
    transit_times.query('travel_time <= 30', inplace = True)
    transit_times.rename(columns = {'travel_time' : 'transit'}, inplace = True)


    mat = walk_times.merge(bike_times, on = ['from_id', 'to_id'], how = 'outer').merge(transit_times, on = ['from_id', 'to_id'], how = 'outer')

    df.to_file(f'SpiderMap/{name}_brew.geojson', driver = 'GeoJSON')

    mdf = df.merge(mat, left_on = 'id', right_on = 'to_id', how = 'right')
    mdf.to_file(f'SpiderMap/{name}_matrix.geojson', driver = 'GeoJSON')

os.chdir(r'c:\users\brenn\documents\projects\HopSkipJump')

fps = {
    'Toronto' : {'df' : r"c:\users\brenn\documents\projects\HopSkipJump\Breweries\CanadaBreweries",
                    'gtfs' : [r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\ttc.zip"],
                    'osm' : r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\toronto_canada.osm.pbf",
                    'bbox' : (-79.944763,43.199170,-78.774719,44.000718),
                    'date' : datetime.datetime(2024, 2, 1, 16, 30)},
    'Denver' : {'df' : r"c:\users\brenn\documents\projects\HopSkipJump\Breweries\breweries",
                    'gtfs' : [r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\rtd.zip"],
                    'osm' : r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\denver-boulder_colorado.osm.pbf",
                    'bbox' : (-105.603333,39.453161,-104.584351,40.233412),
                    'date' : datetime.datetime(2024, 2, 1, 16, 30)},
    'DMV' : {'df' : r"c:\users\brenn\documents\projects\HopSkipJump\Breweries\breweries",
                    'gtfs' : [r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\wmata-rail.zip",
                                r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\wmata-bus.zip"],
                    'osm' : r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\dc-baltimore_maryland.osm.pbf",
                    'bbox' : (-77.703552,38.595407,-76.821899,39.113014),
                    'date' : datetime.datetime(2024, 2, 1, 16, 30)},
    'NY' : {'df' : r"c:\users\brenn\documents\projects\HopSkipJump\Breweries\breweries",
                   'gtfs' : [
                            r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\mta_brooklyn.zip",
                            r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\mta_bc.zip",
                            r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\mta_subway.zip",
                            r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\mta_bronx.zip",
                            r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\mta_supplemented.zip",
                            r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\mta_manhattan.zip",
                            r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\mta_staten_island.zip",
                            r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\mta_queens.zip"
                            ],
                   'osm' : r"C:\Users\Brenn\Documents\Projects\HopSkipJump\Breweries\Data\new-york_new-york.osm.pbf",
                   'bbox' : (-74.424133,40.394673,-73.641357,40.955011),
                   'date' : datetime.datetime(2024, 5, 1, 16, 30)}
}



city = 'NY'

df = gpd.read_file(fps[city]['df'])
df.to_crs(epsg = 4326, inplace = True)
xmin, ymin, xmax, ymax = fps[city]['bbox']
df = df.cx[xmin:xmax, ymin:ymax].copy()

gtfs = fps[city]['gtfs']
osm = fps[city]['osm']
date = fps[city]['date']

hsjCalculator(df, osm, gtfs, date, city)