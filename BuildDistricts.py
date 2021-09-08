#!/bin/python3 -ddd
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
from VotingDistrict import VotingDistrict
from District import District

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

    print( 'There are %d unassigned block groups' %VotingDistrict.getNumUnassigned() )
    # While there are unassigned block groups
    while( VotingDistrict.getNumUnassigned() > 0 ):
        print( 'There are %d unassigned block groups' %VotingDistrict.getNumUnassigned() )
        
        # Loop over districts, adding one layer of block groups at a time
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
    # Count unassigned block groups
    nUnassigned = 0
    for voting_district in voting_districts:
        if ( voting_district.district == None ): nUnassigned += 1

    while ( nUnassigned > 0 ):
        # Reset number of unassigned block groups
        nUnassigned = 0
        
        # Loop through block groups
        for voting_district in voting_districts:
            # If block group is unassigned...
            if ( voting_district.district == None ):
                # Increment count of unassigned block groups
                nUnassigned += 1

                # Loop over adjacent block groups
                for neighbor in voting_district.neighbors:
                    # If bordering block group is assigned...
                    assignedTo = neighbor.voting_district.district
                    if ( assignedTo != None ):
                        # Assign this block group to same district as neighbor
                        districts[assignedTo].addVotingDistrict( voting_district )

                        # Decrement number of unassigned block groups
                        nUnassigned -= 1

                        # Exit loop over neighbors
                        break

def equalizePerimeters():
    numTransferred = -1
    district_perimeters = []
    metric = District.getMetric()
    print( "Metric: %.4f" %metric )
    
    while( numTransferred != 0 and metric > 0.2 ):
        # Reset numTransferred
        numTransferred = 0

        # Loop over all block groups
        for voting_district in voting_districts:
            this_district = District.districts[voting_district.district]
            
            # Loop over neighbors
            for neighbor in voting_district.neighbors:
                neighbor_district = District.districts[neighbor.voting_district.district]
                if ( neighbor_district == this_district ): continue

                # Get current metric
                current_metric = District.getMetric()
                
                # move neighbor to this distric
                neighbor_district.delVotingDistrict( neighbor.voting_district )
                this_district.addVotingDistrict( neighbor.voting_district )
                numTransferred += 1

                # recompute metric
                new_metric = District.getMetric()
                
                # If new metric is not better than the old...
                if ( new_metric >= current_metric ):
                    # move block group back to this district
                    this_district.delVotingDistrict( neighbor.voting_district )
                    neighbor_district.addVotingDistrict( neighbor.voting_district )
                    numTransferred -= 1
                        
        metric = District.getMetric()
        print( "Metric: %.4f" %metric )

                
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

        # Loop over all block groups
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
               if ( new_sum >= original_sum ):
                   # move block group back to this district
                   neighbor_district.addVotingDistrict( neighbor.voting_district )
                   numTransferred -= 1

        district_perimeters.clear()
        for district in District.districts:
            district_perimeters.append( district.getPerimeter() )
        totalPerimeter = sum( district_perimeters ) / 1000.0

def plotDistricts():
    # Add district columns
    cong_dist = []
    for voting_district in VotingDistrict.voting_districts:
        cong_dist.append( voting_district.district )
            
    data['CongDist'] = cong_dist
    print( data.head() )

    data.plot(column='CongDist')
    plt.show()

def findWorstProtrusion():
    worst_ratio = 0.0
    border_lengths = [0.0] * nDistricts
    # Find a block group that is a border district,
    neighboring_districts = set()
    for voting_district in VotingDistrict.voting_districts:
        # Collect all neighboring districts
        neighboring_districts.clear()
        for neighbor in voting_district.neighbors:
            neighboring_districts.add( neighbor.voting_district.district )

        # If this block group has only one neighboring district (its own),
        # it is not a border group.
        if len( neighboring_districts ) == 1:
            continue

        # Collect at least 20 neighbors in the same district
        # Continue to accumulate neighboring districts
        plot_these = [voting_district]
        while len(plot_these) < 20:
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
                
    print ( 'Block Group: %4d' %voting_district.id )
    # print( worst_protrusion )
    print( '    Border Ratio: %.2f' %worst_ratio )
    District.showDistrictAndBlock( worst_district, worst_protrusion )

    return worst_protrusion, worst_ratio, move_to_district

# ---------------------------------------------------------------------
#  START HERE
# ---------------------------------------------------------------------

RE = 6.371e6       # radius of the earth in meters
CE = 2*math.pi*RE  # Circumference of the earth in meters

# There are 11 Congressional districts in VA
nDistricts = 11

# tolerance is the largest permissible value
# for population diff/avg
tolerance = 0.05

# Read data file
data = gpd.read_file( "jax_tl_2020_51_vtd20.shp" )

# Create VotingDistricts from data
for ndx in data.index:
    bg = VotingDistrict()
    bg.population = data.at[ndx,'POPULATION']
    bg.perimeter = data.at[ndx,'PERIMETER']

# Add neighbors to block groups
for ndx in data.index:
    bg = VotingDistrict.voting_districts[ndx]
    neighbors = ast.literal_eval( data.at[ndx,'NEIGHBORS'] )
    for bg_num, border_len in neighbors:
        bg.neighbors.append( Neighbor(VotingDistrict.voting_districts[bg_num], border_len) )
        VotingDistrict.voting_districts[bg_num].neighbors.append( Neighbor(bg, border_len) )
        
# Average number of block groups per district
avgVotingDistricts = math.floor( VotingDistrict.getVotingDistrictCount() / nDistricts )

print( 'avgVotingDistricts: ', avgVotingDistricts )

# Build districts
buildDistricts()
print( 'First Build:' )
District.info()
plotDistricts()

# Progressively make things better
# Try to equalize populations
for tol in [4*tolerance, 3*tolerance, 2*tolerance, tolerance]:
    District.balancePopulations( tol/2.0 )
    District.minimizeTotalPerimeter( tol )

District.info()
plotDistricts()

worst_ratio = 100.0
while worst_ratio > 3.0:
    worst_protrusion, worst_ratio, move_to_district = findWorstProtrusion()
    print( 'Worst Ratio: %4d' %worst_ratio )
    for voting_district in worst_protrusion:
        District.districts[move_to_district].addVotingDistrict( voting_district )
    # Try to equalize populations
    District.balancePopulations( tolerance/2.0 )
    District.minimizeTotalPerimeter( tolerance )
    District.info()
    plotDistricts()

print( 'Final Build:' )
District.info()
plotDistricts()

exit()

# If more than half are border VTDs, this is a protrusion
print ( 'Voting District: %4d' %voting_district.id )
print ( '   len(plot_these): %2d' %len(plot_these) )
print ( '   border blocks:   %2d' %num_border_voting_districts )
print ( 'Voting District: %4d', voting_district.id )
if num_border_voting_districts >= (1./2.)*len(plot_these):
    District.showDistrictAndBlock( voting_district.district, plot_these )
