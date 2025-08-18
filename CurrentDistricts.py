import censusdata
import math
import ast
import statistics
import csv
from tabulate import tabulate
import plotly.figure_factory as ff
import sys
import geopandas as gpd
import earthpy
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import sys, getopt
from VotingDistrict import VotingDistrict
from District import District

import shapely
from shapely.geometry import Point, Polygon, MultiPolygon, MultiLineString, LineString
from shapely.geometry import shape, mapping
from collections import OrderedDict
import numpy
import fiona
import math
import plotly.figure_factory as ff
from copy import copy
import tkinter
import earthpy

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
    print( "Population file: ", population_file )
    with open ( population_file, 'r', encoding = "ISO-8859-1" ) as f:
        geo_geoid = [ row[8] for row in csv.reader(f,delimiter='|')]

    with open ( population_file, 'r', encoding = "ISO-8859-1" ) as f:
        geo_pop = [ row[90] for row in csv.reader(f,delimiter='|')]

    # Add population column to vtd
    cd['POPULATION'] = [ 0 ] * len(cd.index)

    # Loop over shapes and get population
    for ii in cd.index:
        try:
            # Get record number from geodata
            geoid = cd.at[ii,'GEOID']
            ndx = '7000000US' + geoid
            print ( 'NDX: ' + ndx )
            recno = geo_geoid.index(ndx)
            print ( 'RECNO: ' + str(recno) )

            # Get population with logical record number
            print ( 'POP: ' + geo_pop[recno] )
            cd.at[ii,'POPULATION'] = int( geo_pop[recno] )

        except ValueError:
            cd.at[ii,'POPULATION'] = 0

        print( "Line: ", ii, "  Population: ", cd.at[ii,'POPULATION'] )
        total_population += vtd.at[ii,'POPULATION']

    print( 'TOTAL POPULATION: ' + str(total_population) )

# ---------------------------------------------------------------------
#  ADD_PERIMETER_COLUMN()
# ---------------------------------------------------------------------
def add_perimeter_column():
    cd['PERIMETER'] = [ 0.0 ] * len(cd.index)
    for ii in cd.index:
        p0 = cd.at[ii,'geometry']
        perimeter = p0.exterior
        perimeter = p0.exterior.coords
        new_points = []
        for point in perimeter:
            new_points.append( ll_to_m( point ) )
        new_perim = Polygon( new_points )
        cd.at[ii,'PERIMETER'] = new_perim.length

# ---------------------------------------------------------------------
#  ADD_PERIMETER_COLUMN()
# ---------------------------------------------------------------------
def plotDistricts():
    # Add district columns
    cong_dist = []
    for voting_district in VotingDistrict.voting_districts:
        cong_dist.append( voting_district.district )

    data['CongDist'] = cong_dist
    print( data.head() )

    data.plot(column='CongDist')
    plt.show()

# ---------------------------------------------------------------------
#  PARSE_COMMAND_LINE()
# ---------------------------------------------------------------------
def parse_command_line():
    # Define global variables
    global shape_file
    global nDistricts
    # tolerance is the largest permissible value
    # for population diff/avg
    global tolerance

    # Set default for tolerance
    tolerance = 0.05

    # Remove 1st argument from the
    # list of command line arguments
    argumentList = sys.argv[1:]

    # Options
    options = "hs:p:"

    # Long options
    long_options = [ "help", "shape-file=", "population-file=" ]

    try:
        # Parsing argument
        arguments, values = getopt.getopt(argumentList, options, long_options)

        # checking each argument
        for currentArgument, currentValue in arguments:

            if currentArgument in ("-h", "--help"):
                print ( "Displaying Help" )

            elif currentArgument in ("-s", "--shape-file"):
                shape_file = currentValue

            elif currentArgument in ("-s", "--population-file"):
                population_file = currentValue

    except getopt.error as err:
        # output error, and return with an error code
        print (str(err))

# ---------------------------------------------------------------------
#  START HERE
# ---------------------------------------------------------------------
def districtInfo():
    voting_districts = []
    populations = []
    perimeters = []
    print( '------------------------------------------------------------------------------' )
    print( '| District ID | Contiguous | Voting Districts | Population | Perimeter (km ) |' )
    print( '------------------------------------------------------------------------------' )

    # Break up MultiPolygon Congressional Districts into distinct polygons
    for ii in list(range(nObjects)):
        population = 0
        populations.append( population )
        perimeter = cd.at[ii,'PERIMETER']/1000.0
        perimeters.append( perimeter )
        cd_num = int(cd.at[ii,'CD119FP'])
        print( '|     %2d      |      Y     |      %6d      | %9d  |  %9.0f      |'
               %( cd_num, 0, population, perimeter ) )

    print( '------------------------------------------------------------------------------' )
    print( '|   Totals    |     N/A    |      %6d      | %9d  |  %9.0f      |'
           %( 0, sum(populations), sum(perimeters) ) )
    print( '|   Min       |     N/A    |      %6d      | %9d  |  %9.0f      |'
           %( 0, min(populations), min(perimeters) ) )
    print( '|   Max       |     N/A    |      %6d      | %9d  |  %9.0f      |'
           %( 0, max(populations), max(perimeters) ) )
    print( '|   Mean      |     N/A    |      %6d      | %9d  |  %9.0f      |'
           %( 0, numpy.mean(populations), numpy.mean(perimeters) ) )
    print( '|   StDev     |     N/A    |      %6d      | %9d  |  %9.0f      |'
           %( 0, numpy.std(populations), numpy.std(perimeters) ) )
    print( '------------------------------------------------------------------------------' )

# ---------------------------------------------------------------------
#  START HERE
# ---------------------------------------------------------------------

RE = 6.371e6       # radius of the earth in meters
CE = 2*math.pi*RE  # Circumference of the earth in meters

# Parse Command Line
parse_command_line()

# Read data file
cd = gpd.read_file( shape_file )

# Show number of entries and column headers
nObjects = len(cd.index)
print( 'There are %d entries.' %nObjects )
print( cd.columns )

# Add PERIMETER column
add_perimeter_column()

# Show district info
districtInfo()

exit()

print( 'Final Build:' )

plotDistricts()

