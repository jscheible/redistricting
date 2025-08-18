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
from shapely.geometry import Point
import time

class Neighbor:
    def __init__( self, voting_district, border_len ):
        assert( isinstance( voting_district, VotingDistrict ) )
        assert( isinstance( border_len, float ) )
        self.voting_district = voting_district
        self.border_len = border_len

def buildDistricts():
    # Create new District objects
    for ii in list(range(nDistricts)):
        district = District()

    # Assign first VTD to each district
    for district in District.districts:
        startingVotingDistrict = district.id * avgVotingDistricts
        district.addVotingDistrict( VotingDistrict.voting_districts[startingVotingDistrict] )

    print( 'There are %d unassigned VTDs' %VotingDistrict.getNumUnassigned() )
    # While there are unassigned VTDs
    while( VotingDistrict.getNumUnassigned() > 0 ):
        print( 'There are %d unassigned VTDs' %VotingDistrict.getNumUnassigned() )

        # Loop over districts, adding one layer of VTDs at a time
        for district in District.districts:

            # Loop over block groups currently in district
            nVotingDistricts = len(district.voting_districts)
            for ii in list(range(nVotingDistricts)):
                voting_district = district.voting_districts[ii]

                # Loop over neighboring block groups
                for neighbor in voting_district.neighbors:
                    # If neighboring block group is not used...
                    if ( neighbor.voting_district.district == None ):
                        district.addVotingDistrict( neighbor.voting_district )


def assignUnassignedVotingDistricts():
    # Count unassigned voting districts
    nUnassigned = 0
    for voting_district in voting_districts:
        if ( voting_district.district == None ): nUnassigned += 1

    while ( nUnassigned > 0 ):
        # Reset number of unassigned voting districts
        nUnassigned = 0

        # Loop through voting districts
        for voting_district in voting_districts:
            # If voting district is unassigned...
            if ( voting_district.district == None ):
                # Increment count of unassigned voting districts
                nUnassigned += 1

                # Loop over adjacent voting districts
                for neighbor in voting_district.neighbors:
                    # If bordering voting district is assigned...
                    assignedTo = neighbor.voting_district.district
                    if ( assignedTo != None ):
                        # Assign this voting district to same district as neighbor
                        districts[assignedTo].addVotingDistrict( voting_district )

                        # Decrement number of unassigned voting districts
                        nUnassigned -= 1

                        # Exit loop over neighbors
                        break

def minimizeTotalPerimeter():
    numTransferred = -1
    district_perimeters = []
    totalPerimeter = 0.0
    for district in District.districts:
        district_perimeters.append( district.getPerimeter() )
    totalPerimeter = sum( district_perimeters ) / 1000.0

    while( numTransferred != 0 ):
        # Print status
        print( 'NumTransferred: %d' %numTransferred )
        print( 'Total Perimeter: %0f km' %totalPerimeter )

        # Reset numTransferred
        numTransferred = 0

        # Loop over all voting districts
        for voting_district in VotingDistrict.voting_districts:
            this_district = District.districts[voting_district.district]

            # Loop over neighbors
            for neighbor in voting_district.neighbors:
               neighbor_district = District.districts[neighbor.voting_district.district]
               if neighbor_district == this_district: continue

               # Get district perimeters
               this_perimeter = this_district.getPerimeter()
               neighbor_perimeter = neighbor_district.getPerimeter()
               original_sum = this_perimeter + neighbor_perimeter

               # move neighbor to this district
               this_district.addVotingDistrict( neighbor.voting_district )
               numTransferred += 1

               # recompute perimeters
               new_this_perimeter = this_district.getPerimeter()
               new_neighbor_perimeter = neighbor_district.getPerimeter()
               new_sum = new_this_perimeter + new_neighbor_perimeter

               # If new perimeters larger than old...
               if ( new_sum > original_sum ):
                   # move voting district back to this district
                   neighbor_district.addVotingDistrict( neighbor.voting_district )
                   numTransferred -= 1

        district_perimeters.clear()
        for district in District.districts:
            district_perimeters.append( district.getPerimeter() )
        totalPerimeter = sum( district_perimeters ) / 1000.0

def plotDistricts( numColors = 8 ):
    # Add district columns
    cong_dist = []
    color = []
    for voting_district in VotingDistrict.voting_districts:
        cong_dist.append( voting_district.district )
        color.append( voting_district.district % numColors )

    data['CongDist'] = cong_dist
    data['Color'] = color
    print( data.head() )

    # data.plot(column='CongDist')
    data.plot(column='Color')
    plt.show()

def findWorstProtrusion():
    worst_ratio = 0.0
    border_lengths = [0.0] * nDistricts
    # Find a voting district that is a border district,
    neighboring_districts = set()
    for voting_district in VotingDistrict.voting_districts:
        # Collect all neighboring districts
        neighboring_districts.clear()
        for neighbor in voting_district.neighbors:
            neighboring_districts.add( neighbor.voting_district.district )

        # If this voting district has only one neighboring district (its own),
        # it is not a border VTD.
        if len( neighboring_districts ) == 1:
            continue

        # Collect at least 4 neighbors in the same district
        # Continue to accumulate neighboring districts
        plot_these = [voting_district]
        while len(plot_these) < 4:
            for ii in list(range(len(plot_these))):
                tmp = plot_these[ii]
                for neighbor in tmp.neighbors:
                    neighboring_districts.add( neighbor.voting_district.district )
                    if neighbor.voting_district.district == voting_district.district:
                        if neighbor.voting_district not in plot_these:
                            plot_these.append( neighbor.voting_district )

        # Count how many are border groups
        num_border_voting_districts = 0
        for tmp in plot_these:
            for neighbor in tmp.neighbors:
                if neighbor.voting_district.district != voting_district.district:
                    num_border_voting_districts += 1
                    break

        # Get length of border between this group and all districts
        border_lengths.clear()
        border_lengths = [0.0] * nDistricts

        for district in neighboring_districts:
            border_lengths[district] = District.getBorderWithDistrict( plot_these, district )

        # If the groups' border with the parent district is less than with another
        self_border = border_lengths[voting_district.district]
        perimeter = VotingDistrict.getPerimeter( plot_these )
        border_ratio = perimeter / self_border
        if worst_ratio < border_ratio:
            best_district = border_lengths.index(max(border_lengths))
            if best_district != voting_district.district:
                worst_ratio = border_ratio
                worst_protrusion = plot_these
                worst_district = voting_district.district
                move_to_district = best_district

    print ( 'Voting District: %4d' %voting_district.id )
    # print( worst_protrusion )
    print( '    Border Ratio: %.2f' %worst_ratio )
    # District.showDistrictAndBlock( worst_district, worst_protrusion )

    return worst_protrusion, worst_ratio, move_to_district

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
    options = "hs:n:t:"

    # Long options
    long_options = [ "help", "shape-file=", "num-districts=", "tolerace=" ]

    try:
        # Parsing argument
        arguments, values = getopt.getopt(argumentList, options, long_options)

        # checking each argument
        for currentArgument, currentValue in arguments:

            if currentArgument in ("-h", "--help"):
                print ( "Displaying Help" )
                exit()

            elif currentArgument in ("-s", "--shape-file"):
                shape_file = currentValue

            elif currentArgument in ("-n", "--num-districts"):
                nDistricts = int(currentValue)

            elif currentArgument in ("-t", "--tolerance"):
                tolerance = float(currentValue)

    except getopt.error as err:
        # output error, and return with an error code
        print (str(err))

# ---------------------------------------------------------------------
#  START HERE
# ---------------------------------------------------------------------

RE = 6.371e6       # radius of the earth in meters
CE = 2*math.pi*RE  # Circumference of the earth in meters

# Parse Command Line
parse_command_line()

# Read data file
data = gpd.read_file( shape_file )

# Create VotingDistricts from data
for ndx in data.index:
    vtd = VotingDistrict()
    vtd.population = int( data.at[ndx,'POPULATION'] )
    vtd.perimeter  = float( data.at[ndx,'PERIMETER'] )
    vtd.intptlat   = float( data.at[ndx,'INTPTLAT20'] )
    vtd.intptlon   = float( data.at[ndx,'INTPTLON20'] )
    vtd.area       = float( data.at[ndx,'ALAND20'] ) + float( data.at[ndx,'AWATER20'] )

    try:
        vtd.democrat   = int( data.at[ndx,'DEMOCRAT'] )
        vtd.republican = int( data.at[ndx,'REPUBLICAN'] )
    except:
        vtd.democrat   = 0
        vtd.republican = 0

# Add neighbors to voting districts
for ndx in data.index:
    vtd = VotingDistrict.voting_districts[ndx]
    neighbors = ast.literal_eval( data.at[ndx,'NEIGHBORS'] )
    for vtd_num, border_len in neighbors:
        vtd.neighbors.append( Neighbor(VotingDistrict.voting_districts[vtd_num], border_len) )
        VotingDistrict.voting_districts[vtd_num].neighbors.append( Neighbor(vtd, border_len) )

# Average number of voting districts per district
avgVotingDistricts = math.floor( VotingDistrict.getVotingDistrictCount() / nDistricts )

print( 'avgVotingDistricts: ', avgVotingDistricts )

# Build districts
buildDistricts()
print( 'First Build:' )
District.info()
# plotDistricts()

# Progressively make things better
# Try to equalize populations
for tol in [4*tolerance, 3*tolerance, 2*tolerance, tolerance]:
    District.balancePopulations( tol / 2.0 )
    print( "Balanced population with tol: ", (tol/2.0) )
    District.info()
    District.minimizeTotalPerimeter2( tol )
    print( "Minimized perimeter with tol: ", tol )
    District.info()

print( 'Before Protrusion Correction:' )
District.info()
# District.voting()
plotDistricts()

worst_ratio = 100.0
count = 0
max_count = 20
while worst_ratio > 3.0 and count < max_count:
    count += 1
    worst_protrusion, worst_ratio, move_to_district = findWorstProtrusion()
    print( 'Count: %4d' %count )
    print( 'Worst Ratio: %4d' %worst_ratio )
    for voting_district in worst_protrusion:
        District.districts[move_to_district].addVotingDistrict( voting_district )
    # Try to equalize populations
    District.balancePopulations( tolerance/2.0 )
    print( "Balanced to tolerance of ", tolerance/2.0 )
    District.info()
    time.sleep(1)
    District.minimizeTotalPerimeter2( tolerance )
    print( "Minimized total perimeter with tolerance of ", tolerance )
    District.info()
    time.sleep(1)
    # plotDistricts()

print( 'Final Build:' )
District.info()
District.voting()
# District.voting()
plotDistricts()

exit()

# Find the worst VTD and plot it.
worst = None
worst_ratio = 0.0
for vtd in VotingDistrict.voting_districts:
    ratio = vtd.getBorderRatio()
    if worst_ratio < ratio:
        worst = vtd
        worst_ratio = ratio

District.showDistrictAndBlock( vtd.district, vtd )

# If more than half are border VTDs, this is a protrusion
print ( 'Voting District: %4d' %voting_district.id )
print ( '   len(plot_these): %2d' %len(plot_these) )
print ( '   border blocks:   %2d' %num_border_voting_districts )
print ( 'Voting District: %4d', voting_district.id )
if num_border_voting_districts >= (1./2.)*len(plot_these):
    District.showDistrictAndBlock( voting_district.district, plot_these )
