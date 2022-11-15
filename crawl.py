import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
from random import randint

def nodes_polys():
    node_subgraph = nx.ego_graph(G, node, radius=radius, distance="length")
    graph_nodes = [str(node) for node in node_subgraph.nodes()]
    graph_brews = list(set(brew_nodes) & set(graph_nodes))
    destinations.loc[idx, name] = ','.join(graph_brews)
    gdf_list.append(make_iso_polys(G, node_subgraph))

def get_next_node(G, node, radius=radius, distance="length"):
    node_subgraph = nx.ego_graph(G, node, radius=radius, distance="length")
    graph_nodes = [node for node in node_subgraph.nodes()]
    graph_brews = list(set(brew_nodes) & set(graph_nodes))
    idx = randint(0, len(graph_brews)-1)
    return graph_brews[idx]

G = ox.io.load_graphml('GraphML/denver.graphml')
brews = gpd.read_file('DenArea/DenArea.shp')

ng = ox.utils_graph.graph_to_gdfs(G, nodes=True, edges=False, node_geometry=True)
bl = ng.total_bounds
bbox = (bl[0], bl[1], bl[2], bl[3])

def crawl(start, max_distance, destinations):
start = (39.74669, -104.99953)
max_distance = 1650
destinations = gpd.read_file('CO/', bbox = bbox)

    xlist = destinations.geometry.x.to_list()
    ylist = destinations.geometry.y.to_list()
    nodelist = ox.nearest_nodes(G, X = xlist, Y = ylist)
    destinations['node'] = nodelist
    brew_nodes = destinations.node.to_list()

    lat, long = start
    start_node = ox.nearest_nodes(G, X = long, Y = lat)

    next_node = get_next_node(G, start_node, radius = max_distance, distance = 'length')
    length = nx.shortest_path_length(G, start_node, next_node, weight = 'length')
    length


brew_nodes


    # brew_nodes = [str(node) for node in brew_nodes]







	- [ ] Style: Loop v Line
	- [ ] Start: Place v. Algorithm
	- [ ] Mode: Walk v. Bike
	- [ ] Params
		- [ ] Max Distance Total
		- [ ] Number of Breweries
		- [ ] Default - max distance between pulls from cluster map analysis
