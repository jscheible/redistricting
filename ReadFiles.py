from shapely.geometry import Polygon, MultiPolygon, MultiLineString, LineString, shape, mapping
from collections import OrderedDict
import numpy
import fiona
import math
import csv
import sys
import getopt
from copy import copy
import geopandas as gpd

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
#  PARSE_COMMAND_LINE()
# ---------------------------------------------------------------------
def parse_command_line():
    # Define global variables
    global shape_file
    global output_file
    global num_districts
    global population_file
    global votes_file

    # Remove 1st argument from the
    # list of command line arguments
    argumentList = sys.argv[1:]

    # Options
    options = "hv:s:p:o:"

    # Long options
    long_options = ["help", "votes-file=", "shape-file=", "population-file=", "output="]

    try:
        # Parsing argument
        arguments, values = getopt.getopt(argumentList, options, long_options)

        # checking each argument
        for currentArgument, currentValue in arguments:

            if currentArgument in ("-h", "--help"):
                print ( "Displaying Help" )

            elif currentArgument in ("-s", "--shape-file"):
                shape_file = currentValue

            elif currentArgument in ("-p", "--population-file"):
                population_file = currentValue

            elif currentArgument in ("-o", "--output"):
                output_file = currentValue

            elif currentArgument in ("-v", "--votes-file"):
                votes_file = currentValue

    except getopt.error as err:
        # output error, and return with an error code
        print (str(err))

# ---------------------------------------------------------------------
#  ADD_POPULATION_COLUMN()
# ---------------------------------------------------------------------
def add_population_column():
    total_population = 0

    # Pull GEOIDs and Population from geodata file
    print( "Population file: ", population_file )
    with open ( population_file, 'r', encoding = "ISO-8859-1" ) as f:
        geo_geoid = [ row[8] for row in csv.reader(f,delimiter='|')]

    with open ( population_file, 'r', encoding = "ISO-8859-1" ) as f:
        geo_pop = [ row[90] for row in csv.reader(f,delimiter='|')]

    # Add VTD column to vtd
    vtd['VTD'] = [ ii for ii in list(range(len(vtd.index))) ]

    # Add population column to vtd
    vtd['POPULATION'] = [ 0 ] * len(vtd.index)

    # Loop over shapes and get population
    for ii in vtd.index:
        try:
            # Get record number from geodata
            geoid20 = vtd.at[ii,'GEOID20']
            ndx = '7000000US' + geoid20
            print ( 'NDX: ' + ndx )
            recno = geo_geoid.index(ndx)
            print ( 'RECNO: ' + str(recno) )

            # Get population with logical record number
            print ( 'POP: ' + geo_pop[recno] )
            vtd.at[ii,'POPULATION'] = int( geo_pop[recno] )

        except ValueError:
            vtd.at[ii,'POPULATION'] = 0

        print( "Line: ", ii, "  Population: ", vtd.at[ii,'POPULATION'] )
        total_population += vtd.at[ii,'POPULATION']

    print( 'TOTAL POPULATION: ' + str(total_population) )

# ---------------------------------------------------------------------
#  ADD_VOTE_COLUMNS()
# ---------------------------------------------------------------------
def add_vote_columns():
    # Add columns to vtd
    vtd['DEMOCRAT'] = [ 0 ] * len(vtd.index)
    vtd['REPUBLICAN'] = [ 0 ] * len(vtd.index)

    # Pull GEOIDs and Votes from geodata file
    try:
        print( "Votes file: ", votes_file )
    except NameError:
        return()

    geo_geoid = []
    geo_dem = []
    geo_rep = []
    with open ( votes_file, 'r', encoding = "ISO-8859-1" ) as f:
        for row in csv.reader(f,delimiter=','):
            print( row[0], row[1], row[2] )
            geo_geoid.append( row[0] )
            geo_dem.append( row[1] )
            geo_rep.append( row[2] )

    # Add columns to vtd
    vtd['DEMOCRAT'] = [ 0 ] * len(vtd.index)
    vtd['REPUBLICAN'] = [ 0 ] * len(vtd.index)

    # Loop over shapes and get population
    for ii in vtd.index:
        try:
            # Get record number from geodata
            ndx = vtd.at[ii,'GEOID20']
            print ( 'NDX: ' + ndx )
            recno = geo_geoid.index(ndx)
            print ( 'RECNO: ' + str(recno) )

            # Get values with logical record number
            print ( 'DEM: ' + geo_dem[recno] )
            vtd.at[ii,'DEMOCRAT'] = int( geo_dem[recno] )
            print ( 'REP: ' + geo_rep[recno] )
            vtd.at[ii,'REPUBLICAN'] = int( geo_rep[recno] )

        except ValueError:
            vtd.at[ii,'DEMOCRAT'] = 0
            vtd.at[ii,'REPUBLICAN'] = 0

# ---------------------------------------------------------------------
#  ADD_PERIMETER_COLUMN()
# ---------------------------------------------------------------------
def add_perimeter_column():
    vtd['PERIMETER'] = [ 0.0 ] * len(vtd.index)
    for ii in vtd.index:
        p0 = vtd.at[ii,'geometry']
        perimeter = p0.exterior
        perimeter = p0.exterior.coords
        new_points = []
        for point in perimeter:
            new_points.append( ll_to_m( point ) )
        new_perim = Polygon( new_points )
        vtd.at[ii,'PERIMETER'] = new_perim.length

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
               ('DEMOCRAT',   'int:14'),
               ('REPUBLICAN', 'int:14'),
               ('NEIGHBORS',  'str:512') ]

    shapefile_schema = {'properties': OrderedDict( columns ),
                        'geometry': 'Polygon' }

    with fiona.open( output_file, 'w',
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
# Parse command line
parse_command_line()

# Read Shapefile for Voting Districts
vtd = gpd.read_file( shape_file )

nObjects = len(vtd.index)
print( 'There are %d entries.' %nObjects )
print( vtd.columns )

add_vote_columns()
print( vtd.columns )

add_population_column()
print( vtd.columns )

# Break up MultiPolygon Voting Districts into distinct polygons
for ii in list(range(nObjects)):
    p0 = vtd.at[ii,'geometry']
    if ( type(p0) == MultiPolygon ):
        print ( ii, ' is not a polygon' )
        polygons = list( p0.geoms )
        lengths = [ poly.length for poly in polygons ]
        print( lengths )
        longest = lengths.index(max(lengths))
        print( 'Longest is %d' %longest )
        # Loop through polygons
        for jj in list(range(len(polygons))):
            line = vtd.loc[ii]
            if jj == longest:
                nRec = ii
            else:
                nRec = len(vtd)
                vtd.loc[nRec] = vtd.loc[ii]

            # Set values for new row.
            vtd.at[nRec, 'geometry'] = polygons[jj]
            pt = polygons[jj].representative_point()
            coords = list(pt.coords)
            vtd.at[nRec, 'INTPTLON10'] = coords[0][0]
            vtd.at[nRec, 'INTPTLAT10'] = coords[0][1]
            if jj != longest:
                vtd.at[nRec, 'POPULATION'] = 0

print( 'Rechecking polygons...' )
for ndx in vtd.index:
    p0 = vtd.at[ndx,'geometry']
    if ( type(p0) != Polygon ):
        print ( ii, ' is not a polygon' )
        exit()

nObjects = len(vtd.index)
print( 'We now have %d rows.' %nObjects )

# Add PERIMETER column
add_perimeter_column()

# Show population
total_pop = 0
for ii in vtd.index:
    total_pop += vtd.at[ii,'POPULATION']
print ( 'TOTAL POPULATION: ' + str(total_pop) )

fill_holes( vtd )

# Verify population
total_pop = 0
for ii in vtd.index:
    total_pop += vtd.at[ii,'POPULATION']
print ( 'TOTAL POPULATION: ' + str(total_pop) )

nObjects = len(vtd.index)
print( 'We now have %d rows.' %nObjects )

# See which ones still have holes
for ii in vtd.index:
    nHoles = len(p0.interiors)
    if nHoles > 0: print( 'VTD %d still has %d holes.' %(ii, nHoles) )


print( 'vtd: ', len(vtd) )
print( 'vtd.index: ', len(vtd.index) )

neighbors = [[] for ii in vtd.index ]

for ii in vtd.index:
    p0 = vtd.at[ii,'geometry']
    for jj in vtd.index:
        if ii >= jj: continue
        p1 = vtd.at[jj,'geometry']
        if p0.intersects(p1):
            border = shape(mapping(p0.intersection(p1)))
            if border.length > 0.0:
                length = 0.0
                new_lines = []
                if type(border) == LineString:
                    border = MultiLineString( [border] )
                for linestring in border.geoms:
                    new_coords = []
                    for point in linestring.coords:
                        new_coords.append( ll_to_m( point ) )
                    try:
                        if len(new_coords) > 1:
                            new_lines.append( LineString( new_coords ) )
                    except ValueError:
                        continue

                    new_border = MultiLineString( new_lines )

                print( '%d,%d,%f' %(ii, jj, new_border.length) )
                neighbors[ii].append( (jj, new_border.length) )
                # neighbors[jj].append( (ii, new_border.length) )

vtd['NEIGHBORS'] = neighbors
write_shapefile( vtd )
exit()
