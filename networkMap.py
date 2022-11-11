import pandas as pd
import geopandas as gpd
import osmnx as ox
import networkx as nx
from shapely.geometry import Point, LineString
import matplotlib
import os
import shutil
from config import bike_speed, walk_speed, network_time, dist
from mapHelpers import js_var, file_copy

# list(list(G.edges(data=True))[0][-1].keys())

def norm_color(time, color_ramp):
    norm = time / network_time
    cmap = matplotlib.cm.get_cmap(color_ramp)
    hex = matplotlib.colors.rgb2hex(cmap(norm))
    return hex

def network_map_calculation(point, destinations, G, folder = None):
    lat, long = point
    ptdf = gpd.GeoDataFrame({'Point' : ['Origin'], 'geometry':[Point(long, lat)]}, crs = 'EPSG:4326')

    # destinations = ox.projection.project_gdf(destinations, to_crs = 'EPSG:32613')
    # ptdf = ox.projection.project_gdf(ptdf, to_crs = 'EPSG:32613')
    # G = ox.projection.project_graph(G, to_crs = 'EPSG:32613')

    destinations = destinations.clip(ptdf.buffer(dist)).copy()

    ## pretty sure this s depreicated now, switch to bottom
    # origin_node = ox.distance.get_nearest_node(G, point)
    origin_node = ox.distance.nearest_nodes(G, long, lat)

    # node_lambda = lambda r: ox.distance.get_nearest_node(G, (r.geometry.y, r.geometry.x))
    node_lambda = lambda r: ox.distance.nearest_nodes(G, r.geometry.x, r.geometry.y)
    destinations['node'] = destinations.apply(node_lambda, axis = 1)

    distance_lambda = lambda n: nx.shortest_path_length(G, source = origin_node, target = n, weight = 'length')
    destinations['origin_distance'] = destinations.node.apply(distance_lambda)

    destinations.eval('bike_time = origin_distance / (@bike_speed * 1000 / 60)', inplace = True)
    destinations.eval('walk_time = origin_distance / (@walk_speed * 1000 / 60)', inplace = True)

    destinations['bike_color'] = destinations.bike_time.apply(norm_color, args = ['Greens'])
    destinations['walk_color'] = destinations.walk_time.apply(norm_color, args = ['Blues'])

    noweb = '<strong>{0}</strong><br><br>Approximate Travel Time:<br>&nbsp;&nbsp;&nbsp;Bike: {1} minutes<br>&nbsp;&nbsp;&nbsp;&nbsp;Walk: {2} minutes'
    web = '<a href={3}><strong>{0}</strong></a><br><br>Approximate Travel Time:<br>&nbsp;&nbsp;&nbsp;&nbsp;Bike: {1} minutes<br>&nbsp;&nbsp;&nbsp;&nbsp;Walk: {2} minutes'
    destinations['popup'] = destinations.apply(lambda r: web.format(r['name'], round(r.bike_time, 1), round(r.walk_time, 0), r.website)\
                            if pd.notnull(r.website)\
                            else noweb.format(r['name'], round(r.bike_time, 0), round(r.walk_time, 1)), axis = 1)

    if folder:
        destinations.to_crs(epsg = 4326, inplace = True)
        destinations.query('bike_time <= @network_time').to_file(os.path.join(folder, 'bike_network.js'), driver = 'GeoJSON')
        destinations.query('walk_time <= @network_time').to_file(os.path.join(folder, 'walk_network.js'), driver = 'GeoJSON')
        ptdf.to_file(os.path.join(folder, "home_base.js"), driver = 'GeoJSON')

    return destinations

def route_to_geometry(route):
    x = []
    y = []
    for u, v in zip(route[:-1], route[1:]):
        # if there are parallel edges, select the shortest in length
        data = min(G.get_edge_data(u, v).values(), key=lambda d: d["length"])
        if "geometry" in data:
            # if geometry attribute exists, add all its coords to list
            xs, ys = data["geometry"].xy
            x.extend(xs)
            y.extend(ys)
        else:
            # otherwise, the edge is a straight line from node to node
            x.extend((G.nodes[u]["x"], G.nodes[v]["x"]))
            y.extend((G.nodes[u]["y"], G.nodes[v]["y"]))

    line_list = [(a, b) for (a, b) in zip(x, y)]
    line_geom = LineString(line_list)

    return line_geom

def network_map(out_folder, start_point, out_name = 'network'):
    lat, long = start_point
    js_var(os.path.join(out_folder, 'bike_network.js'), 'bike')
    js_var(os.path.join(out_folder, 'walk_network.js'), 'walk')
    js_var(os.path.join(out_folder, 'home_base.js'), 'home')

    file_copy('Templates', out_folder, ['geolet.js', 'map.css', 'home-base.svg'])

    with open('Templates/network_map_template.html', 'r', encoding='utf-8') as file:
        data = file.readlines()

    data[8] = '		<script type="text/javascript" src="bike_network.js"></script>\n'
    data[9] = '		<script type="text/javascript" src="walk_network.js"></script>\n'
    data[10] = '		<script type="text/javascript" src="home_base.js"></script>\n'
    data[16] = '			var startLoc = [{0}, {1}]\n'.format(lat, long)

    map_path = '{0}/{1}.html'.format(out_folder, out_name)
    with open(map_path, 'w', encoding='utf-8') as file:
        file.writelines(data)

if __name__ == '__main__':
    G = ox.io.load_graphml('GraphML/denver.graphml')
    point = (39.74669, -104.99953)
    destinations = gpd.read_file('DenArea')
    destinations.to_crs(epsg = 4326, inplace = True)
    folder = 'NetworkMap'

    dest = network_map_calculation(point, destinations, G, folder)
    network_map(folder, 'network', point)
