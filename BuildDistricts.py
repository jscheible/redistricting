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
from BlockGroup import BlockGroup
from District import District

class Neighbor:
    def __init__( self, block_group, border_len ):
        assert( isinstance( block_group, BlockGroup ) )
        assert( isinstance( border_len, float ) )
        self.block_group = block_group
        self.border_len = border_len


def buildDistricts():
    # Create new District objects
    for ii in list(range(nDistricts)):
        district = District()
         
    # Assign first block group to each district
    for district in District.districts:
        startingBlockGroup = district.id * avgBlockGroups
        district.addBlockGroup( BlockGroup.block_groups[startingBlockGroup] )

    print( 'There are %d unassigned block groups' %BlockGroup.getNumUnassigned() )
    # While there are unassigned block groups
    while( BlockGroup.getNumUnassigned() > 0 ):
        print( 'There are %d unassigned block groups' %BlockGroup.getNumUnassigned() )
        
        # Loop over districts, adding one layer of block groups at a time
        for district in District.districts:
            
            # Loop over block groups currently in district
            nBlockGroups = len(district.block_groups)
            for ii in list(range(nBlockGroups)):
                block_group = district.block_groups[ii]
                
                # Loop over neighboring block groups
                for neighbor in block_group.neighbors:
                    # If neighboring block group is not used...
                    if ( neighbor.block_group.district == None ):
                        district.addBlockGroup( neighbor.block_group )


def assignUnassignedBlockGroups():
    # Count unassigned block groups
    nUnassigned = 0
    for block_group in block_groups:
        if ( block_group.district == None ): nUnassigned += 1

    while ( nUnassigned > 0 ):
        # Reset number of unassigned block groups
        nUnassigned = 0
        
        # Loop through block groups
        for block_group in block_groups:
            # If block group is unassigned...
            if ( block_group.district == None ):
                # Increment count of unassigned block groups
                nUnassigned += 1

                # Loop over adjacent block groups
                for neighbor in block_group.neighbors:
                    # If bordering block group is assigned...
                    assignedTo = neighbor.block_group.district
                    if ( assignedTo != None ):
                        # Assign this block group to same district as neighbor
                        districts[assignedTo].addBlockGroup( block_group )

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
        for block_group in block_groups:
            this_district = District.districts[block_group.district]
            
            # Loop over neighbors
            for neighbor in block_group.neighbors:
                neighbor_district = District.districts[neighbor.block_group.district]
                if ( neighbor_district == this_district ): continue

                # Get current metric
                current_metric = District.getMetric()
                
                # move neighbor to this distric
                neighbor_district.delBlockGroup( neighbor.block_group )
                this_district.addBlockGroup( neighbor.block_group )
                numTransferred += 1

                # recompute metric
                new_metric = District.getMetric()
                
                # If new metric is not better than the old...
                if ( new_metric >= current_metric ):
                    # move block group back to this district
                    this_district.delBlockGroup( neighbor.block_group )
                    neighbor_district.addBlockGroup( neighbor.block_group )
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
        for block_group in BlockGroup.block_groups:
            this_district = District.districts[block_group.district]
            
            # Loop over neighbors
            for neighbor in block_group.neighbors:
               neighbor_district = District.districts[neighbor.block_group.district]
               if neighbor_district == this_district: continue

               # Get district perimeters
               this_perimeter = this_district.getPerimeter()
               neighbor_perimeter = neighbor_district.getPerimeter()
               original_sum = this_perimeter + neighbor_perimeter

               # move neighbor to this district
               this_district.addBlockGroup( neighbor.block_group )
               numTransferred += 1

               # recompute perimeters
               new_this_perimeter = this_district.getPerimeter()
               new_neighbor_perimeter = neighbor_district.getPerimeter()
               new_sum = new_this_perimeter + new_neighbor_perimeter

               # If new perimeters larger than old...
               if ( new_sum >= original_sum ):
                   # move block group back to this district
                   neighbor_district.addBlockGroup( neighbor.block_group )
                   numTransferred -= 1

        district_perimeters.clear()
        for district in District.districts:
            district_perimeters.append( district.getPerimeter() )
        totalPerimeter = sum( district_perimeters ) / 1000.0

def plotDistricts():
    # Add district columns
    cong_dist = []
    for block_group in BlockGroup.block_groups:
        cong_dist.append( block_group.district )
            
    data['CongDist'] = cong_dist
    print( data.head() )

    data.plot(column='CongDist')
    plt.show()

def findWorstProtrusion():
    worst_ratio = 0.0
    border_lengths = [0.0] * nDistricts
    # Find a block group that is a border district,
    neighboring_districts = set()
    for block_group in BlockGroup.block_groups:
        # Collect all neighboring districts
        neighboring_districts.clear()
        for neighbor in block_group.neighbors:
            neighboring_districts.add( neighbor.block_group.district )

        # If this block group has only one neighboring district (its own),
        # it is not a border group.
        if len( neighboring_districts ) == 1:
            continue

        # Collect at least 20 neighbors in the same district
        # Continue to accumulate neighboring districts
        plot_these = [block_group]
        while len(plot_these) < 20:
            for ii in list(range(len(plot_these))):
                tmp = plot_these[ii]
                for neighbor in tmp.neighbors:
                    neighboring_districts.add( neighbor.block_group.district )
                    if neighbor.block_group.district == block_group.district:
                        if neighbor.block_group not in plot_these:
                            plot_these.append( neighbor.block_group )

        # Count how many are border groups
        num_border_block_groups = 0
        for tmp in plot_these:
            for neighbor in tmp.neighbors:
                if neighbor.block_group.district != block_group.district:
                    num_border_block_groups += 1
                    break

        # Get length of border between this group and all districts
        border_lengths.clear()
        border_lengths = [0.0] * nDistricts

        for district in neighboring_districts:
            border_lengths[district] = District.getBorderWithDistrict( plot_these, district )

        # If the groups' border with the parent district is less than with another
        self_border = border_lengths[block_group.district]
        perimeter = BlockGroup.getPerimeter( plot_these )
        border_ratio = perimeter / self_border
        if worst_ratio < border_ratio:
            best_district = border_lengths.index(max(border_lengths))
            if best_district != block_group.district:
                worst_ratio = border_ratio
                worst_protrusion = plot_these
                worst_district = block_group.district
                move_to_district = best_district
                
    print ( 'Block Group: %4d' %block_group.id )
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
data = gpd.read_file( "jax_tl_2010_51_bg10.shp" )

# Create BlockGroups from data
for ndx in data.index:
    bg = BlockGroup()
    bg.population = data.at[ndx,'POPULATION']
    bg.perimeter = data.at[ndx,'PERIMETER']

# Add neighbors to block groups
for ndx in data.index:
    bg = BlockGroup.block_groups[ndx]
    neighbors = ast.literal_eval( data.at[ndx,'NEIGHBORS'] )
    for bg_num, border_len in neighbors:
        bg.neighbors.append( Neighbor(BlockGroup.block_groups[bg_num], border_len) )
        BlockGroup.block_groups[bg_num].neighbors.append( Neighbor(bg, border_len) )
        
# Average number of block groups per district
avgBlockGroups = math.floor( BlockGroup.getBlockGroupCount() / nDistricts )

print( 'avgBlockGroups: ', avgBlockGroups )

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

print( 'Final Build:' )
District.info()
plotDistricts()

worst_ratio = 100.0
while worst_ratio > 3.0:
    worst_protrusion, worst_ratio, move_to_district = findWorstProtrusion()
    print( 'Worst Ratio: %4d' %worst_ratio )
    for block_group in worst_protrusion:
        District.districts[move_to_district].addBlockGroup( block_group )

District.info()
plotDistricts()

exit()

# If more than half are border groups, this is a protrusion
print ( 'Block Group: %4d' %block_group.id )
print ( '   len(plot_these): %2d' %len(plot_these) )
print ( '   border blocks:   %2d' %num_border_block_groups )
print ( 'Block Group: %4d', block_group.id )
if num_border_block_groups >= (1./2.)*len(plot_these):
    District.showDistrictAndBlock( block_group.district, plot_these )
