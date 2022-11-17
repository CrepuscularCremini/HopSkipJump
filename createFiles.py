import osmnx as ox
import geopandas as gpd
from config import dist

def get_local_network(location, type = 'bike', save = 'local_network.graphml'):

    if isinstance(location, tuple):
        G = ox.graph_from_point(location, dist=dist, dist_type = 'network', network_type = type)
    elif isinstance(location, str):
        ## make the return geocoded thing true
        G = ox.graph_from_address(location, dist=dist, dist_type = 'network', network_type = type)
    else:
        raise Exception('Check your formatting, requires either tuple (lat, long) or address')
    ## return G and the lat longs
    ox.io.save_graphml(G, filepath = save)
    return G

def get_region_network(location, type = 'bike', save = 'region_network.graphml'):
    if isinstance(location, gpd.GeoDataFrame):
        west, south, east, north = location.total_bounds
        G = ox.graph_from_bbox(north, south, east, west)
    elif isinstance(location, str):
        G = ox.graph_from_place(location, network_type = type)
    else:
        raise Exception('Check your formatting, requires either GeoDataFrame or area name')
    ox.io.save_graphml(G, filepath = save)
    return G

if __name__ == '__main__':
    point = (39.74669, -104.99953)
    G = get_local_network(point, type = 'walk', save = 'GraphML/denver_local_walk.graphml')
    G = get_local_network(point, type = 'bike', save = 'GraphML/denver_local_bike.graphml')
    G = get_region_network('Denver, Colorado, USA', type = 'walk', save = 'GraphML/denver_region_walk.graphml')
