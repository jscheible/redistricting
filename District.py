from BlockGroup import BlockGroup

class District:
    count = 0
    districts = []
    
    def __init__( self ):
        self.id = District.count
        District.count += 1
        self.population = 0
        self.perimeter = 0.0
        self.block_groups = []
        self.neighboring_districts = []
        self.perimeter_up_to_date = True
        District.districts.append( self )
        
    def info():
        print( '--------------------------' )
        for district in District.districts:
            if district.isContiguous():
                print( 'District %d is contiguous' %district.id )
            else:
                print( 'District %d is not contiguous' %district.id )
            print( 'District %d has %d block groups' %(district.id, district.numBlockGroups()) )
            print( 'District %d has %d people' %(district.id, district.population) )
        print( '--------------------------' )

    def addBlockGroup( self, block_group ):
        assert( isinstance( block_group, BlockGroup ) )
        cd = block_group.district
        if cd != None:
            District.districts[cd].delBlockGroup( block_group )
        self.block_groups.append( block_group )
        self.perimeter_up_to_date = False
        self.population += block_group.population
        block_group.addToDistrict( self.id )

    def delBlockGroup( self, block_group ):
        assert( isinstance( block_group, BlockGroup ) )
        try:
            self.block_groups.remove( block_group )
            block_group.district = None
            self.perimeter_up_to_date = False
            self.population -= block_group.population
        except ValueError:
            pass

    def getLargest():
        nLargest = 0
        for district in District.districts:
            nBlockGroups = len(district.block_groups)
            if nBlockGroups > nLargest:
                nLargest = nBlockGroups
                largest = district
        return largest, nLargest

    def numBlockGroups( self ):
        return len( self.block_groups )
    
    def getPerimeter( self ):
        if ( self.perimeter_up_to_date ): return self.perimeter
        self.perimeter = 0.0
        for block_group in self.block_groups:
            # Add perimeter of block group to perimeter of district
            self.perimeter += block_group.perimeter

            # Loop over neighboring block groups
            for neighbor in block_group.neighbors:
                # If neighbor is in the same district, subtract border length
                if ( neighbor.block_group.district == block_group.district ):
                    self.perimeter -= neighbor.border_len
        self.perimeter_up_to_date = True
        return self.perimeter

    def getMetric():
        district_perimeters = []
        district_populations = []
        for district in District.districts:
            district_perimeters.append( district.getPerimeter() )
            district_populations.append( district.population )
        perim_mean = statistics.mean( district_perimeters )
        perim_stdev = statistics.stdev( district_perimeters )
        pop_mean = statistics.mean( district_populations )
        pop_stdev = statistics.stdev( district_populations )

        metric = ( perim_stdev/perim_mean + pop_stdev/pop_mean ) / 2.0
        return metric
        
    def getPopMetric():
        district_populations = []
        for district in District.districts:
            district_populations.append( district.population )
        pop_mean = statistics.mean( district_populations )
        pop_stdev = statistics.stdev( district_populations )

        metric = pop_stdev/pop_mean
        return metric

    def isContiguous( self ):
        if len( self.block_groups ) == 0: return True
        
        block_groups = []
        nCurrent = 0
        start = self.block_groups[0]
        block_groups.append( start )
        nNew = len( block_groups )
        while ( nNew > nCurrent ):
            nCurrent = nNew
            for block_group in block_groups:
                for neighbor in block_group.neighbors:
                    if ( neighbor.block_group.district == self.id ):
                        if ( neighbor.block_group not in block_groups ):
                            block_groups.append( neighbor.block_group )
            nNew = len( block_groups )
        if nCurrent == len( self.block_groups ):
            return True
        else:
            # print( 'Only %d of %d block groups counted' %(nCurrent,len( self.block_groups ) ) )
            return False

    def reducePopulation( self ):
        totalTransferred = 0
        nCurrent = self.population
        nTransferred = -1
        while nTransferred != 0:
            nTransferred = 0

            # Collect all blocks that border less populated districts
            candidates = []
            
            # Loop over block groups in current district
            for candidate in self.block_groups:
                # print( 'Finding neighbors of %d' %block_group.id )
                neighboring_districts = []
                # Loop over neighboring block groups to collect their district IDs
                for neighbor in candidate.neighbors:
                    # print( neighbor )
                    neighbor_id = neighbor.block_group.id
                    neighbor_district_id = neighbor.block_group.district
                    
                    # Skip blocks that are in the same district
                    if neighbor_district_id == self.id: continue

                    # If neighboring district is not in the list, add it
                    nieghbor_district = District.districts[neighbor_district_id]
                    if neighbor_district not in neighboring_districts:
                        neighboring_districts.append( neighbor_district )

                # Loop over neighboring districts
                for neighbor_district in neighboring_districts:

                    # If this candidate for transfer has a population less than
                    # the difference in populations between the two districts
                    pop_diff = self.population - neighbor_district.population
                    if  candidate.population < pop_diff:

                        # The change in total population difference will be twice
                        # the difference between the population of the candidate
                        # and the current difference
                        dPopDiff = 2 * ( pop_diff - candidate.population )
                        
                        # Determine difference in total perimeter for this district
                        # Will lose this block group's borders with other districts,
                        # and will gain this block group's borders with this district
                        dPerimSelf = 0.0
                        for tmp in block_group.neighbors:
                            if self.id != tmp.block_group.district:
                                dPerimSelf -= tmp.block_group.border
                            else:
                                dPerimSelf += tmp.block_group.border

                        # Neighbor will gain this block group's borders with other districts,
                        # and will lose this block group's borders with neighbor district
                        dPerimNeighbor = 0.0
                        for tmp in block_group.neighbors:
                            if neighbors_district_id != tmp.block_group.district:
                                dPerimNeighbor += tmp.block_group.border
                            else:
                                dPerimNeighbor -= tmp.block_group.border
                        
                        # Determine difference in total perimeter for neighbors
                        dPerim = dPerimSelf + dPerimNeighbor

                        # Save all this in our candidates list
                        candidates.append( (candidate.id, neighbors_district_id, dPopDiff, dPerim ) )
                        
                    
            print( 'Num transferred: %d' %nTransferred )
            totalTransferred += nTransferred
            if nTransferred == 0:
                break

        return totalTransferred
