import osmnx as ox
from config import dist

def get_local_network(location, type = 'bike'):

    if isinstance(location, tuple):
        G = ox.graph_from_point(location, dist=dist, dist_type = 'network', network_type = type)
    elif isinstance(location, str):
        ## make the return geocoded thing true
        G = ox.graph_from_address(location, dist=dist, dist_type = 'network', network_type = type)
    else:
        raise Exception('Check your formatting, requires either tuple (lat, long) or address')
    ## return G and the lat longs
    return G

def get_general_network(location, type = 'bike', filepath = None):
    G = ox.graph_from_place(location, network_type = type)
    if filepath:
        ox.io.save_graphml(filepath)
    else:
        ox.io.save_graphml('graph.graphml')
    return G

if __name__ == '__main__':
    point = (39.74669, -104.99953)
    G = get_local_network(point, type = 'walk')
    ox.io.save_graphml(G, filepath = 'GraphML/denver_walk.graphml')
