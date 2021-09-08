#!/bin/python3
from shapely.geometry import Point, Polygon, MultiPolygon, shape, mapping, MultiLineString, LineString
from collections import OrderedDict
import ast
import numpy
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
    total_population = 0
    
    # Pull GEOIDs and Population from geodata file
    with open ( '../census/2020/Virginia/vageo2020.pl', 'r' ) as f:
        geo_geoid   = [ row[8] for row in csv.reader(f,delimiter='|')]

    with open ( '../census/2020/Virginia/vageo2020.pl', 'r' ) as f:
        geo_pop = [ row[90] for row in csv.reader(f,delimiter='|')]

    # Add VTD column to va
    va['VTD'] = [ ii for ii in list(range(len(va.index))) ]

    # Add population column to va
    va['POPULATION'] = [ 0 ] * len(va.index)

    # Loop over shapes and get population
    for ii in va.index:
        try:
            # Get logical record number from geodata
            geoid20 = va.at[ii,'GEOID20']
            ndx = '7000000US' + geoid20
            print ( 'NDX: ' + ndx )
            recno = geo_geoid.index(ndx)
            print ( 'RECNO: ' + str(recno) )

            print ( 'POP: ' + geo_pop[recno] )
            # Get population with logical record number
            va.at[ii,'POPULATION'] = geo_pop[recno]
                                              
        except ValueError:
            va.at[ii,'POPULATION'] = 0

        total_population += va.at[ii,'POPULATION']

    print( 'TOTAL POPULATION: ' + str(total_population) )
    
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
                        print( 'Voting District %4d matches a hole in %4d' %(jj, ii) )

                        # Add population to enclosing object
                        gdf.at[ii,'POPULATION'] += pop1

                        # Delete row from gdf
                        gdf = gdf.drop( jj )

                        # Get out of loop
                        break
                    
                    except ValueError:
                        continue

def write_shapefile( gdf ):
    columns =[ ('STATEFP20',  'str:2'),
               ('COUNTYFP20', 'str:3'),
               ('VTDST20',    'str:6'),
               ('GEOID20',    'str:11'),
               ('VTDI20',     'str:1'),
               ('NAME20',     'str:100'),
               ('NAMELSAD20', 'str:100'),
               ('LSAD20',     'int:2'),
               ('MTFCC20',    'str:5'),
               ('FUNCSTAT20', 'str:1'),
               ('ALAND20',    'int:14'),
               ('AWATER20',   'int:14'),
               ('INTPTLAT20', 'str:11'),
               ('INTPTLON20', 'str:12'),
               ('PERIMETER',  'float'),
               ('POPULATION', 'int:14'),
               ('NEIGHBORS',  'str:512') ]

    shapefile_schema = {'properties': OrderedDict( columns ),
                        'geometry': 'Polygon' }
    
    with fiona.open( './jax_tl_2020_51_vtd20.shp', 'w',
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

# Read Shapefile for Voting Districts
va = gpd.read_file( "../census/2020/Virginia/tl_2020_51_vtd20.shp" )

nObjects = len(va.index)
print( 'There are %d entries.' %nObjects )
print( va.columns )

add_population_column()
print( va.columns )

# Break up MultiPolygon Voting Districts into distinct polygons
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
                
            # Set values for new row.
            va.at[nRec, 'geometry'] = polygons[jj]
            pt = polygons[jj].representative_point()
            coords = list(pt.coords)
            va.at[nRec, 'INTPTLON10'] = coords[0][0]
            va.at[nRec, 'INTPTLAT10'] = coords[0][1]
            if jj != longest:
                va.at[nRec, 'POPULATION'] = 0
            
print( 'Rechecking polygons...' )
for ndx in va.index:
    p0 = va.at[ndx,'geometry']
    if ( type(p0) != Polygon ):
        print ( ii, ' is not a polygon' )
        exit()

nObjects = len(va.index)
print( 'We now have %d rows.' %nObjects )

# Add PERIMETER column
add_perimeter_column()

# Show population
total_pop = 0
for ii in va.index:
    total_pop += va.at[ii,'POPULATION']
print ( 'TOTAL POPULATION: ' + str(total_pop) )

fill_holes( va )

# Verify population
total_pop = 0
for ii in va.index:
    total_pop += va.at[ii,'POPULATION']
print ( 'TOTAL POPULATION: ' + str(total_pop) )

nObjects = len(va.index)
print( 'We now have %d rows.' %nObjects )

# See which ones still have holes
for ii in va.index:
    nHoles = len(p0.interiors)
    if nHoles > 0: print( 'VTD %d still has %d holes.' %(ii, nHoles) )


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
