#!/bin/python3
from shapely.geometry import Point, Polygon, MultiPolygon, shape, mapping, MultiLineString, LineString
from collections import OrderedDict
import ast
import numpy
import shapefile
import fiona
import censusdata
import math
import statistics
import csv
from tabulate import tabulate
import plotly.figure_factory as ff
import sys
from copy import copy
import tkinter
import geopandas as gpd
import earthpy
import matplotlib.pyplot as plt
import matplotlib.cm as cm
from blockgroup import BlockGroup

# ---------------------------------------------------------------------
#  LL_TO_M()
# ---------------------------------------------------------------------
def ll_to_m( point ):
    RE = 6.371e6       # radius of the earth in meters
    CE = 2*math.pi*RE  # Circumference of the earth in meters
    deg_lon, deg_lat = point
    rad_lon = deg_lon * math.pi / 180.0
    rad_lat = deg_lat * math.pi / 180.0
    m_lon = math.cos(rad_lat) * deg_lon * CE / 180.0
    m_lat = deg_lat * CE / 180.0
    return ( m_lon, m_lat )

# ---------------------------------------------------------------------
#  ADD_POPULATION_COLUMN()
# ---------------------------------------------------------------------
def add_population_column():
    # Get population from census
    va_bg_pop = censusdata.download( 'sf1', 2010, censusdata.censusgeo([('state', '51'), ('county', '*'), ('block group', '*')]), ['P001001'] )

    print( va_bg_pop.P001001.values )
    # Add block group column to va
    va['BLOCKGROUP'] = [ ii for ii in list(range(len(va.index))) ]

    # Add population column to va 
    va['POPULATION'] = va_bg_pop.P001001.values

# ---------------------------------------------------------------------
#  ADD_PERIMETER_COLUMN()
# ---------------------------------------------------------------------
def add_perimeter_column():
    va['PERIMETER'] = [ 0.0 ] * len(va.index)
    for ii in va.index:
        p0 = va.at[ii,'geometry']
        perimeter = p0.exterior
        perimeter = p0.exterior.coords
        new_points = []
        for point in perimeter:
            new_points.append( ll_to_m( point ) )
        new_perim = Polygon( new_points )
        va.at[ii,'PERIMETER'] = new_perim.length

# ---------------------------------------------------------------------
#  FILL_HOLES()
# ---------------------------------------------------------------------
def fill_holes( gdf ):
    # For every Polygon, try to find a hole it fits into.
    # If an exact match is found, eliminate both the hole
    # and the Polygon that fits in it.

    # Loop over objects to find those with holes
    for ii in gdf.index:
        # We put this in a TRY block because it may be elimiinated
        try:
            p0 = gdf.at[ii,'geometry']
            pop0 = gdf.at[ii,'POPULATION']
        except KeyError:
            continue
        # Loop over holes
        nHoles = len(p0.interiors)
        holes = copy( p0.interiors )
        holes = list( holes )
        for hole in holes:
            # Loop over objects again, skipping this one
            for jj in gdf.index:
                if ii == jj: continue
                try:
                    p1 = gdf.at[jj,'geometry']
                    pop1 = gdf.at[jj,'POPULATION']
                except KeyError:
                    continue
            
                # If this object intersects the hole...
                if hole.intersects( p1 ):
                    try:
                        # Try to remove hole from holes (may not really match)
                        holes.remove( hole )

                        # Show what happened
                        print( 'Block %4d matches a hole in %4d' %(jj, ii) )

                        # Add population to enclosing object
                        gdf.at[ii,'POPULATION'] += pop1

                        # Delete row from gdf
                        gdf = gdf.drop( jj )

                        # Get out of loop
                        break
                    
                    except ValueError:
                        continue

def write_shapefile( gdf ):
    columns =[ ('STATEFP10',  'str:2'),
               ('COUNTYFP10', 'str:3'),
               ('TRACTCE10',  'str:6'),
               ('BLKGRPCE10', 'str:1'),
               ('GEOID10',    'str:12'),
               ('NAMELSAD10', 'str:13'),
               ('MTFCC10',    'str:5'),
               ('FUNCSTAT10', 'str:1'),
               ('ALAND10',    'int:14'),
               ('AWATER10',   'int:14'),
               ('INTPTLAT10', 'str:11'),
               ('INTPTLON10', 'str:12'),
               ('PERIMETER',  'float'),
               ('BLOCKGROUP', 'int:6'),
               ('POPULATION', 'int:14'),
               ('NEIGHBORS',  'str:512') ]

    shapefile_schema = {'properties': OrderedDict( columns ),
                        'geometry': 'Polygon' }
    
    with fiona.open( './jax_tl_2010_51_bg10.shp', 'w',
                     driver = 'ESRI Shapefile',
                     crs = {'init': 'epsg:4269'},
                     schema = shapefile_schema ) as sink:
        # Loop over each record
        for ndx in gdf.index:
            # Create data record to write
            data = [ (col[0], gdf.at[ndx,col[0]]) for col in columns ]

            # Loop over each column in the record
            for ii in list(range(len(data))):
                # Change numpy.int64 data to int
                if type( data[ii][1] ) == numpy.int64:
                    data[ii] = ( data[ii][0], data[ii][1].item() )

                # Format NEIGHBORS data as a string.
                # This will require ast.literal_eval() to convert back to a list.
                if data[ii][0] == 'NEIGHBORS':
                    list_str = '['
                    for x,y in data[ii][1]:
                        list_str += '(' + str(x) + ',' + str(round(y,2)) + '),'
                    if len(list_str) > 1:
                        list_str = list_str[0:-1]
                    list_str += ']'
                    data[ii] = ( data[ii][0], list_str )
                    
            coords = [ gdf.at[ndx,'geometry'].exterior.coords ]
            dict = { 'type': 'Feature',
                     'id': ndx,
                     'properties': OrderedDict( data ),
                     'geometry': {'type': 'Polygon', 'coordinates': coords }
            }

            sink.write( dict )
        

    
# ---------------------------------------------------------------------
#  MAIN PROGRAM
# ---------------------------------------------------------------------

# Read Shapefiles
# sf = shapefile.Reader("census/tl_2010_51_bg10")
# shapes = sf.shapes()

va = gpd.read_file( "census/tl_2010_51_bg10.shp" )

nObjects = len(va.index)
print( 'There are %d entries.' %nObjects )
print( va.columns )

add_population_column()
print( va.columns )

# Break up MultiPolygon Block Groups into distinct polygons
for ii in list(range(nObjects)):
    p0 = va.at[ii,'geometry']
    if ( type(p0) == MultiPolygon ):
        print ( ii, ' is not a polygon' )
        polygons = list( p0 )
        lengths = [ poly.length for poly in polygons ]
        print( lengths )
        longest = lengths.index(max(lengths))
        print( 'Longest is %d' %longest )
        # Loop through polygons
        for jj in list(range(len(polygons))):
            line = va.loc[ii]
            if jj == longest:
                nRec = ii
            else:
                nRec = len(va)
                va.loc[nRec] = va.loc[ii]

            va.set_value( nRec, 'geometry', polygons[jj] )
            pt = polygons[jj].representative_point()
            coords = list(pt.coords)
            va.set_value( nRec, 'INTPTLON10', coords[0][0] )
            va.set_value( nRec, 'INTPTLAT10', coords[0][1] )
            va.set_value( nRec, 'POPULATION', 0 )

            
print( 'Rechecking polygons...' )
for ndx in va.index:
    p0 = va.at[ndx,'geometry']
    if ( type(p0) != Polygon ):
        print ( ii, ' is not a polygon' )
        exit()

nObjects = len(va.index)
print( 'We now have %d rows.' %nObjects )

add_perimeter_column()

fill_holes( va )


nObjects = len(va.index)
print( 'We now have %d rows.' %nObjects )

# See which ones still have holes
for ii in va.index:
    nHoles = len(p0.interiors)
    if nHoles > 0: print( 'BlockGroup %d still has %d holes.' %(ii, nHoles) )

# Add PERIMETER column
add_perimeter_column()

# write_shapefile( va )

print( 'va: ', len(va) )
print( 'va.index: ', len(va.index) )

neighbors = [[] for ii in va.index ]

for ii in va.index:
    p0 = va.at[ii,'geometry']
    for jj in va.index:
        if ii >= jj: continue
        p1 = va.at[jj,'geometry']
        if p0.intersects(p1):
            border = shape(mapping(p0.intersection(p1)))
            if border.length > 0.0:
                length = 0.0
                new_lines = []
                if type(border) == LineString: border = MultiLineString( [border] )
                for linestring in border:
                    new_coords = []
                    for point in linestring.coords:
                        new_coords.append( ll_to_m( point ) )
                    try:
                        new_lines.append( LineString( new_coords ) )
                    except ValueError:
                        continue
                        
                    new_border = MultiLineString( new_lines )
                    
                print( '%d,%d,%f' %(ii, jj, new_border.length) )
                neighbors[ii].append( (jj, new_border.length) )
                # neighbors[jj].append( (ii, new_border.length) )

va['NEIGHBORS'] = neighbors
write_shapefile( va )
exit()

