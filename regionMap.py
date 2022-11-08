import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
from shapely.geometry import Point, LineString, Polygon
from config import cluster_time, dist, bike_speed, walk_speed

G = ox.io.load_graphml('GraphML/denver_walk.graphml')
ng = ox.utils_graph.graph_to_gdfs(G, nodes=True, edges=False, node_geometry=True)
bl = ng.total_bounds
bbox = (bl[0], bl[1], bl[2], bl[3])
ds = gpd.read_file('CO/', bbox = bbox)

def make_iso_polys(G, subgraph, edge_buff=25, node_buff=50, infill = False):
    isochrone_polys = []
    node_points = [Point((data["x"], data["y"])) for node, data in subgraph.nodes(data=True)]
    nodes_gdf = gpd.GeoDataFrame({"id": list(subgraph.nodes)}, geometry=node_points)
    nodes_gdf = nodes_gdf.set_index("id")

    nodes_gdf = nodes_gdf.set_crs(epsg = 4326)

    edge_lines = []
    for n_fr, n_to in subgraph.edges():
        f = nodes_gdf.loc[n_fr].geometry
        t = nodes_gdf.loc[n_to].geometry
        edge_lookup = G.get_edge_data(n_fr, n_to)[0].get("geometry", LineString([f, t]))
        edge_lines.append(edge_lookup)

    edge_gdf = gpd.GeoDataFrame({'geometry' : edge_lines}, geometry = 'geometry')
    edge_gdf = edge_gdf.set_crs(epsg = 4326)

    nodes_gdf = ox.project_gdf(nodes_gdf)
    edge_gdf = ox.project_gdf(edge_gdf)

    n = nodes_gdf.buffer(node_buff).geometry
    e = edge_gdf.buffer(edge_buff).geometry

    all_gs = list(n) + list(e)
    un = gpd.GeoSeries(all_gs).unary_union

    # if infill == True:
    un = Polygon(un.exterior)

    new_iso = gpd.GeoDataFrame({'geometry' : [un]}, geometry = 'geometry', crs = n.crs)
    new_iso.to_crs(epsg = 4326, inplace = True)

    return new_iso

def nodes_polys(G, node, destinations, radius, name, idx, brew_nodes, gdf_list):
    node_subgraph = nx.ego_graph(G, node, radius=radius, distance="length")
    graph_nodes = [str(node) for node in node_subgraph.nodes()]
    graph_brews = list(set(brew_nodes) & set(graph_nodes))
    destinations.loc[idx, name] = ','.join(graph_brews)
    gdf_list.append(make_iso_polys(G, node_subgraph))

def cluster_creation(G, destinations, walk = True, bike = False, walk_G = None, bike_G = None):
    xlist = destinations.geometry.x.to_list()
    ylist = destinations.geometry.y.to_list()
    nodelist = ox.nearest_nodes(G, X = xlist, Y = ylist)

    destinations['node'] = nodelist

    bike_dist = (bike_speed * 1000 * cluster_time / 60)
    walk_dist = (walk_speed * 1000 * cluster_time / 60)
    brew_nodes = destinations.node.to_list()
    brew_nodes = [str(node) for node in brew_nodes]

    walk_gdfs = []
    bike_gdfs = []

    for idx, val in destinations.iterrows():
        node = destinations.loc[idx, 'node']

        if walk == True:
            if walk_G:
                nodes_polys(walk_G, node, destinations, walk_dist, 'walk_nodes', idx, brew_nodes, walk_gdfs)
            else:
                nodes_polys(G, node, destinations, walk_dist, 'walk_nodes', idx, brew_nodes, walk_gdfs)
            # walk_subgraph = nx.ego_graph(G, node, radius=walk_dist, distance="length")
            # walk_nodes = [str(node) for node in walk_subgraph.nodes()]
            # walk_brews = list(set(brew_nodes) & set(walk_nodes))
            # destinations.loc[idx, 'walk_nodes'] = ','.join(walk_brews)
            # walk_gdfs.append(make_iso_polys(G, walk_subgraph))

        if bike == True:
            if bike_G:
                nodes_polys(bike_G, node, destinations, bike_dist, 'bike_nodes', idx, brew_nodes, bike_gdfs)
            else:
                nodes_polys(G, node, destinations, bike_dist, 'bike_nodes', idx, brew_nodes, bike_gdfs)
            # bike_subgraph = nx.ego_graph(G, node, radius=bike_dist, distance="length")
            # bike_nodes = [str(node) for node in bike_subgraph.nodes()]
            # bike_brews = list(set(brew_nodes) & set(bike_nodes))
            # destinations.loc[idx, 'bike_nodes'] = ','.join(bike_brews)
            # bike_gdfs.append(make_iso_polys(G, bike_subgraph))

    if walk == True:
            walk_gdf = pd.concat(walk_gdfs)
            walk_gdf = walk_gdf.dissolve().explode(ignore_index = True, index_parts = False)

    if bike == True:
        bike_gdf = pd.concat(bike_gdfs)
        bike_gdf = bike_gdf.dissolve().explode(ignore_index = True, index_parts = False)

    if walk == True and bike == True:
        return destinations, walk_gdf, bike_gdf
    elif walk == True and bike == False:
        return destinations, walk_gdf
    elif walk == False and bike == True:
        return destinations, bike_gdf
    else:
        return destinations

dest, walk = cluster_creation(G, ds, walk = True, bike = False)

import matplotlib.pyplot as plt

fig, ax = plt.subplots(figsize = (10,10))
walk.plot(ax = ax, cmap = 'Spectral')
dest.plot(ax = ax, color = 'k')
ax.set_axis_off()

dest.to_file('RegionMap/dataframe')
walk.to_file('RegionMap/walk_clusters')
