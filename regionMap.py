import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
from config import cluster_time, dist, bike_speed, walk_speed

G = ox.io.load_graphml('GraphML/denver.graphml')
destinations = gpd.read_file('DenArea/')
destinations.to_crs(epsg = 4326, inplace = True)

def cluster_creation(G, destinations):
    xlist = destinations.geometry.x.to_list()
    ylist = destinations.geometry.y.to_list()
    nodelist = ox.get_nearest_nodes(G, X = xlist, Y = ylist)

    destinations['node'] = nodelist

    bike_dist = (bike_speed * 1000 * cluster_time / 60)
    walk_dist = (walk_speed * 1000 * cluster_time / 60)
    brew_nodes = destinations.node.to_list()

    for idx, val in destinations.iterrows():
        node = destinations.loc[idx, 'node']

        walk_subgraph = nx.ego_graph(G, node, radius=walk_dist, distance="length")
        bike_subgraph = nx.ego_graph(G, node, radius=bike_dist, distance="length")

        walk_nodes = [str(node) for node in walk_subgraph.nodes()]
        bike_nodes = [str(node) for node in bike_subgraph.nodes()]
        walk_brews = list(set(brew_nodes) & set(walk_nodes))
        bike_brews = list(set(brew_nodes) & set(bike_nodes))

        destinations.loc['walk_nodes'] = ','.join(walk_brews)
        destinations.loc['bike_nodes'] = ','.join(bike_brews)

    destinations.walk_nodes
