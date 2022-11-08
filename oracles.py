import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from random import randint

denver_box = {'N' : 39.785851,
            'S' : 39.653813,
            'E' : -104.867249,
            'W' : -105.075302}

def converter(num, mod):
    n_num =  num % mod
    if type(n_num) == float:
        st_num = str(num).split('.')

        idx = round(int(st_num[0]) / 100 * len(st_num[1])) - 1
        place_num = int(st_num[1][idx])
        out_num = place_num % mod
        return out_num
    else:
        return n_num

def true_oracle(state, bbox, num1, num2, num3, num4, auto_coin_flip = False):
# state = 'CO'
# bbox = denver_box
# num1, num2, num3, num4 = 30, 86.52, 3.1415926535, 81

    change_mod = {0 : [0,1,2],
                1 : [0,2,1],
                2 : [1,0,2],
                3 : [1,2,0],
                4 : [2,0,1],
                5 : [2,1,0]}

    selector = converter(num4, 6)
    f, s, t = change_mod[selector]

    nums = [num1, num2, num3]
    fn = nums[f]
    sn = nums[s]
    tn = nums[t]

    lat = fn / 100 * (bbox['N'] - bbox['S']) + bbox['S']
    long = sn / 100 * (bbox['E'] - bbox['W']) + bbox['W']

    num = converter(tn, 10) + 5

    point = Point(long, lat)

    df = gpd.read_file('SpatialDatabases/{0}/{0}.shp'.format(state))

    multiplier = len(df)
    pdf = gpd.GeoDataFrame({'name' : ['rep_point'] * multiplier, 'geometry' : [point] * multiplier}, crs = 4326)
    pdf.to_crs(df.crs, inplace = True)

    dist_mat = df.distance(pdf)
    df['point_distance'] = dist_mat
    rdec = df.nsmallest(num, columns = ['point_distance'], keep = 'all')

    rdeclist = rdec.name.tolist()

    id1 = randint(0, len(rdeclist)-1)
    id2 = randint(0, len(rdeclist)-1)

    while id2 == id1:
        id2 = randint(0, len(rdeclist) + 1)

    if auto_coin_flip == False:
        print('Heads: {0}\nTails: {1}'.format(rdeclist[id1], rdeclist[id2]))
    else:
        picker = randint(0, 1)
        if picker == 0:
            print("You're going to: {0}".format(rdeclist[id1]))
        else:
            print("You're going to: {0}".format(rdeclist[id2]))

oracle_selector('CO', denver_box, 30, 86.52, 3.1415926535, 81)



def neighborhood_oracle(state, city, nbhds, independent = False, auto_coin_flip = False):
# state = 'CO'
# city = 'Denver'
    df = gpd.read_file('SpatialDatabases/{0}/{0}.shp'.format(state))
    ndf = gpd.read_file('SpatialDatabases/Neighborhoods/{0}'.format(city))
    ndf.to_crs(df.crs, inplace = True)
    if independent:
        df.query('independen == "Yes"', inplace = True)

    ndf.query('NBHD_NAME in @nbhds', inplace = True)
    ldf = gpd.clip(df, ndf)

    id0 = input('User 1 Select a number between 0 and {0}'.format(len(ldf.columns) - 1))

    sdf = ldf.sort_values(ldf.columns[int(id0)]).copy()
    rdeclist = sdf.name.tolist()

    id1 = input('User 2 Select a number between 0 and {0}'.format(len(rdeclist)))
    id2 = input('User 3 Select a number between 0 and {0}, that isn\'t {1}'.format(len(rdeclist), id1))

    aggressiveness_counter = 0
    aggressive_additions = ['heckin', 'motherfuckin', 'god damned', 'stupid ass']
    while id2 == id1:
        id2 = input('I said  that isn\'t {0} you {1} dummy'.format(id1, ' '.join(aggressive_additions[:aggressiveness_counter])))
        if aggressiveness_counter < len(aggressive_additions):
            aggressiveness_counter += 1

    if auto_coin_flip == False:
        print('Heads: {0}\nTails: {1}'.format(rdeclist[int(id1)], rdeclist[int(id2)]))
    else:
        picker = randint(0, 1)
        if picker == 0:
            print("You're going to: {0}".format(rdeclist[id1]))
        else:
            print("You're going to: {0}".format(rdeclist[id2]))

nbhds = ['Five Points', 'Highland', 'Auraria', 'CBD', 'Jefferson Park', 'Union Station']
neighborhood_selector('CO', 'Denver', nbhds, independent = True)




round(fn / 100 * 16)
round(sn / 100 * 29)
round(tn / 100 * 29)
