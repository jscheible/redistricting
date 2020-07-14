#!/bin/python3
import shapefile
import censusdata
import math
import ast
import statistics
import csv
from tabulate import tabulate
import plotly.figure_factory as ff
import sys
import tkinter
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
                    # print( 'Checking block group %d' %neighbor.block_group.id )
                    # If neighboring block group is not used...
                    if ( neighbor.block_group.district == None ):
                        # print( '  Adding block group %d to district %d' %( neighbor.block_group.id, district.id ) )
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

def balancePopulations():
    margin = 0.1
    avgPop = District.population / District.count
    
    # Loop through districts to get populations
    populations = []
    for district in District.districts:
        populations.append( district.population )
        
        max_pop = max( populations )
        min_pop = min( populations )

    loop_count = 0
    print( 'Loop: ', loop_count )
    print( '   Min Pop: ', min_pop )
    print( '   Max Pop: ', max_pop )
    print( '   Factor: ',  ((max_pop - min_pop) / avgPop) )

    # While these differ by more than margin
    while (max_pop - min_pop) / avgPop > margin:
        loop_count += 1
        for district in District.districts:
            district.reducePopulation()

        # Recompute max and min populations
        populations.clear()
        for district in District.districts:
            populations.append( district.population )
        
            max_pop = max( populations )
            min_pop = min( populations )

        print( 'Loop: ', loop_count )
        print( '   Min Pop: ', min_pop )
        print( '   Max Pop: ', max_pop )
        print( '   Factor: ',  ((max_pop - min_pop) / avgPop) )
            

    
        

def plotDistricts():
    # Add district columns
    cong_dist = []
    for block_group in BlockGroup.block_groups:
        cong_dist.append( block_group.district )
            
    data['CongDist'] = cong_dist
    print( data.head() )

    data.plot(column='CongDist')
    plt.show()

def used_to_be_this():
    va_bg_pop = censusdata.download( 'sf1', 2010, censusdata.censusgeo([('state', '51'), ('county', '*'), ('block group', '*')]), ['P001001'] )

    with open('VirginiaBlockGroupPerimeters.csv', newline='') as csvfile:
        filereader = csv.reader(csvfile, delimiter=',')
        for row in filereader:
            block_group = BlockGroup()
            block_group.perimeter = float(row[1])
            try:
                block_group.population = va_bg_pop.P001001[block_group.id]
            except IndexError:
                block_group.population = 0
            
    print( 'nBlockGroups: %d' %BlockGroup.getBlockGroupCount() )
    print( 'BlockGroup.count: %d' %BlockGroup.count )

    with open('VirginiaBlockGroupBorders.csv', newline='') as csvfile:
        filereader = csv.reader(csvfile, delimiter=',')
        for row in filereader:
            ii = int( row[0] )
            jj = int( row[1] )
            border = float( row[2] )
            print( ii, jj, border )
        
            block_group = BlockGroup.block_groups[ii]
            neighbor = Neighbor( BlockGroup.block_groups[jj], border )
            block_group.neighbors.append( neighbor )

            # block_group = BlockGroup.block_groups[jj]
            # neighbor = Neighbor( BlockGroup.block_groups[ii], border )
            # block_group.neighbors.append( neighbor )

    # Loop through all block groups
    for block_group in BlockGroup.block_groups:
        border_len = block_group.getBorderLen()
        if ( border_len > block_group.perimeter + 0.1 ):
            print( block_group.id, border_len, block_group.perimeter )
            print( 'Block Group %d has a perimeter of %f and borders %f'
                   %( block_group.id, block_group.perimeter, border_len ) )

    # BlockGroup.plotBorder()

    # Find embedded block groups
    for block_group in BlockGroup.block_groups:
        if block_group.isEmbedded():
            print( 'Block Group %d is embedded.' %block_group.id )
            block_group.plot()

    # BlockGroup.plotEmbeddedBlockGroups()
    exit()
    
# ---------------------------------------------------------------------
#  START HERE
# ---------------------------------------------------------------------

RE = 6.371e6       # radius of the earth in meters
CE = 2*math.pi*RE  # Circumference of the earth in meters

# There are 11 Congressional districts in VA
nDistricts = 11

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
# plotDistricts()

# Try to equalize populations
balancePopulations()
plotDistricts()

exit()

minimizeTotalPerimeter()

# Allow below average districts to poach from larger neighbors, up to average
largest, nLargest = District.getLargest()
print( 'type(largest) ', type(largest) )
print( 'type(nLargest) ', type(nLargest) )

while( nLargest > avgBlockGroups+2 ):
    print( 'District %d has %d blockgroups.' %( largest.id, largest.numBlockGroups() ) )
    nTransferred = largest.reduceBlockGroups()
    print( 'Transferred: %d' %nTransferred )
    print( 'District %d has %d blockgroups.' %( largest.id, largest.numBlockGroups() ) )
    if nTransferred == 0:
        for district in District.districts:
            if district.numBlockGroups() > avgBlockGroups+2:
                print( 'District %d has %d blockgroups.' %( district.id, district.numBlockGroups() ) )
                nTransferred += district.reduceBlockGroups()
                print( 'District %d has %d blockgroups.' %( district.id, district.numBlockGroups() ) )
                
    largest, nLargest = District.getLargest()
    if nTransferred == 0: break
    
print( 'Equal Number of Block Groups:' )
District.info()

plotDistricts()
exit()


# Compute perimeters of districts
totalPerimeters = 0.0
for district in districts:
    print( 'District %d has a perimeter of %f meters'
           %(district.id, district.getPerimeter() ) )
    totalPerimeters += district.getPerimeter()/1000.0

print( 'Total perimeter is %.0f km' % totalPerimeters )

# Compute population of districts
totalPopulation = 0.0
for district in districts:
    print( 'District %2d has a population of %10d people'
           %(district.id, district.population ) )
    totalPopulation += district.population
print( 'Total population is %d people' % totalPopulation )

print( '--------------------------' )




# Compute population of districts
totalPopulation = 0.0
for district in districts:
    print( 'District %2d has a population of %10d people'
           %(district.id, district.population ) )
    totalPopulation += district.population
print( 'Total population is %d people' % totalPopulation )

balancePopulations()
print( "Pop Metric: %4f" %District.getPopMetric() )

