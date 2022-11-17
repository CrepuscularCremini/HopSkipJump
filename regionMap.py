import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
from shapely.geometry import Point, LineString, Polygon
from config import cluster_time, dist, bike_speed, walk_speed
from mapHelpers import js_var, file_copy
import pygeos
import os
import matplotlib
from random import randint

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
    # graph_brews = list(set(brew_nodes) & set(graph_nodes))
    # destinations.loc[idx, name] = ','.join(graph_brews)
    gdf_list.append(make_iso_polys(G, node_subgraph))

def assign_cluster_id(join_gdf, id_name, destinations, color_ramp):
    join_gdf.reset_index(inplace = True)
    join_gdf.rename(columns = {'index' : id_name}, inplace = True)

    dest_project = ox.projection.project_gdf(destinations)
    join_gdf = ox.projection.project_gdf(join_gdf)

    dest_project = dest_project.sjoin_nearest(join_gdf, max_distance = 25)
    dest_project = dest_project[['node', id_name]].copy()

    mode_destinations = destinations.merge(dest_project, on = 'node', how = 'left')

    color_map = {}

    for idx in mode_destinations[id_name].unique():
        # normid =  idx / mode_destinations[id_name].max()
        cmap = matplotlib.cm.get_cmap(color_ramp)
        val = randint(0, 100) / 100
        hex = matplotlib.colors.rgb2hex(cmap(val))
        color_map[idx] = hex

    mode_destinations['color'] = mode_destinations[id_name].map(color_map)

    return mode_destinations

def popup_maker(gdf, name_field = 'Name', website_field = 'Website'):
    noweb = '<strong>{0}</strong>'
    web = '<a href=https://{1}><strong>{0}</strong></a>'
    gdf['popup'] = gdf.apply(lambda r: web.format(r[name_field], r[website_field])\
                            if pd.notnull(r[website_field])\
                            else noweb.format(r[name_field]), axis = 1)

def cluster_creation(G, destinations, walk = True, bike = False, folder = None, walk_G = None, bike_G = None):
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
        if walk:
            if walk_G:
                nodes_polys(walk_G, node, destinations, walk_dist, 'walk_nodes', idx, brew_nodes, walk_gdfs)
            else:
                nodes_polys(G, node, destinations, walk_dist, 'walk_nodes', idx, brew_nodes, walk_gdfs)

        if bike:
            if bike_G:
                nodes_polys(bike_G, node, destinations, bike_dist, 'bike_nodes', idx, brew_nodes, bike_gdfs)
            else:
                nodes_polys(G, node, destinations, bike_dist, 'bike_nodes', idx, brew_nodes, bike_gdfs)

    if walk:
        walk_gdf = pd.concat(walk_gdfs)
        walk_gdf = walk_gdf.dissolve().explode(ignore_index = True, index_parts = False)
        walk_mode = assign_cluster_id(walk_gdf, 'walk_id', destinations, 'nipy_spectral')
        popup_maker(walk_mode)

        if folder:
            walk_mode.to_file(os.path.join(folder, 'walk_region.js'), driver = 'GeoJSON')
            walk_gdf.to_file(os.path.join(folder, 'walk_clusters.js'), driver = 'GeoJSON')

    if bike:
        bike_gdf = pd.concat(bike_gdfs)
        bike_gdf = bike_gdf.dissolve().explode(ignore_index = True, index_parts = False)
        bike_mode = assign_cluster_id(walk_gdf, 'bike_id', destinations)
        popup_maker(bike_mode)

        if folder:
            bike_mode.to_file(os.path.join(folder, 'bike_region.js'), driver = 'GeoJSON')
            bike_gdf.to_file(os.path.join(folder, 'bike_clusters.js'), driver = 'GeoJSON')

    if walk and bike:
        return walk_mode, bike_mode
    elif walk:
        return walk_mode
    else:
        return bike_mode

def region_map(out_folder, start_point = None, out_name='region', type = 'walk'):
    brew_file = f"{type}_region.js"
    cluster_file = f"{type}_clusters.js"

    if start_point:
        lat, long = start_point
    else:
        gdf = gpd.read_file(os.path.join(out_folder, brew_file), driver = 'GeoJSON')
        ct = gdf.dissolve().centroid
        long, lat = ct.x.values[0], ct.y.values[0]

    js_var(os.path.join(out_folder, brew_file), 'brews')
    js_var(os.path.join(out_folder, cluster_file), 'clusters')
    file_copy('Templates', out_folder, ['geolet.js', 'map.css'])

    with open('Templates/region_map_template.html', 'r', encoding='utf-8') as file:
        data = file.readlines()

    data[8] = '		<script type="text/javascript" src="{0}"></script>\n'.format(brew_file)
    data[9] = '		<script type="text/javascript" src="{0}"></script>\n'.format(cluster_file)
    data[15] = '			var startLoc = [{0}, {1}]\n'.format(lat, long)

    map_path = '{0}/{1}.html'.format(out_folder, out_name)
    with open(map_path, 'w', encoding='utf-8') as file:
        file.writelines(data)


if __name__ == "__main__":
    G = ox.io.load_graphml('GraphML/denver_region_walk.graphml')
    ng = ox.graph_to_gdfs(G, edges = False)
    bl = ng.total_bounds
    bbox = (bl[0], bl[1], bl[2], bl[3])
    ds = gpd.read_file('HSJ_Breweries/DenverBreweries', bbox = bbox)

    cluster_creation(G, ds, walk = True, bike = False, folder = 'RegionMap')
    region_map('RegionMap/')
