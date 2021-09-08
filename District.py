import geopandas as gpd
import matplotlib.pyplot as plt
from VotingDistrict import VotingDistrict
import statistics

class District:
    count = 0
    districts = []
    population = 0
    
    def __init__( self ):
        self.id = District.count
        District.count += 1
        self.population = 0
        self.perimeter = 0.0
        self.voting_districts = []
        self.neighboring_districts = []
        self.perimeter_up_to_date = True
        District.districts.append( self )

    def getDiscontiguous():
        discontiguous = []
        for district in District.districts:
            if not district.isContiguous():
                discontiguous.append( district.id )
        return discontiguous
    
    def info():
        voting_districts = []
        populations = []
        perimeters = []
        print( '------------------------------------------------------------------------------' )
        print( '| District ID | Contiguous | Voting Districts | Population | Perimeter (km ) |' )
        print( '------------------------------------------------------------------------------' )
        for district in District.districts:
            voting_districts.append( district.numVotingDistricts() )
            populations.append( district.population )
            perimeters.append( district.getPerimeter()/1000.0 )
            
            if district.isContiguous():
                print( '|     %2d      |      Y     |      %6d      | %9d  |  %9.0f      |'
                       %( district.id, district.numVotingDistricts(),
                          district.population, district.getPerimeter()/1000.0) )
            else:
                print( '|     %2d      |      N     |      %6d      | %9d  |  %9.0f      |'
                       %( district.id, district.numVotingDistricts(),
                          district.population, district.getPerimeter()/1000.0) )
        print( '------------------------------------------------------------------------------' )
        print( '|   Totals    |     N/A    |      %6d      | %9d  |  %9.0f      |'
               %( sum(voting_districts), sum(populations), sum(perimeters) ) )
        print( '|   Min       |     N/A    |      %6d      | %9d  |  %9.0f      |'
               %( min(voting_districts), min(populations), min(perimeters) ) )
        print( '|   Max       |     N/A    |      %6d      | %9d  |  %9.0f      |'
               %( max(voting_districts), max(populations), max(perimeters) ) )
        print( '|   Mean      |     N/A    |      %6d      | %9d  |  %9.0f      |'
               %( statistics.mean(voting_districts), statistics.mean(populations), statistics.mean(perimeters) ) )
        print( '|   StDev     |     N/A    |      %6d      | %9d  |  %9.0f      |'
               %( statistics.stdev(voting_districts), statistics.stdev(populations), statistics.stdev(perimeters) ) )
        print( '------------------------------------------------------------------------------' )
            


    def addVotingDistrict( self, voting_district ):
        assert( isinstance( voting_district, VotingDistrict ) )
        cd = voting_district.district
        if cd != None:
            District.districts[cd].delVotingDistrict( voting_district )
        self.voting_districts.append( voting_district )
        self.perimeter_up_to_date = False
        self.population += voting_district.population
        District.population += voting_district.population
        voting_district.district = self.id

    def delVotingDistrict( self, voting_district ):
        assert( isinstance( voting_district, VotingDistrict ) )
        try:
            self.voting_districts.remove( voting_district )
            voting_district.district = None
            self.perimeter_up_to_date = False
            self.population -= voting_district.population
            District.population -= voting_district.population
        except ValueError:
            pass

    def getLargest():
        nLargest = 0
        for district in District.districts:
            nVotingDistricts = len(district.voting_districts)
            if nVotingDistricts > nLargest:
                nLargest = nVotingDistricts
                largest = district
        return largest, nLargest

    def numVotingDistricts( self ):
        return len( self.voting_districts )

    #-------------------------------------------------------------------------
    # Returns the length of the border between this list of block groups
    # and the specified district.
    #-------------------------------------------------------------------------
    def getBorderWithDistrict( voting_districts, district ):
        district_border_len = 0.0
        # Ensure uniqueness my making it a set:
        voting_district_set = set(voting_districts)
        for voting_district in voting_district_set:
            for neighbor in voting_district.neighbors:
                # Do not count neighbors that are also in this group
                if neighbor.voting_district in voting_district_set:
                    continue

                # If districts match, add border with neighbor
                if neighbor.voting_district.district == district:
                    district_border_len += neighbor.border_len
                    
        return district_border_len

    #-------------------------------------------------------------------------
    # Returns the perimeter of the district, or the perimeter of
    # the list of block groups specified in the optional parameter.
    #-------------------------------------------------------------------------
    def getPerimeter( self ):
        if ( self.perimeter_up_to_date ): return self.perimeter
        self.perimeter = 0.0
        for voting_district in self.voting_districts:
            # Add perimeter of block group to perimeter of district
            self.perimeter += voting_district.perimeter

            # Loop over neighboring block groups
            for neighbor in voting_district.neighbors:
                # If neighbor is in the same district, subtract border length
                if ( neighbor.voting_district.district == voting_district.district ):
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

    def plotDistricts():
        data = gpd.read_file( "jax_tl_2010_51_bg10.shp" )
        # Add district columns
        cong_dist = []
        for voting_district in VotingDistrict.voting_districts:
            cong_dist.append( voting_district.district )

        data['CongDist'] = cong_dist
        print( data.head() )

        data.plot(column='CongDist')
        plt.show()

    def showDistrictAndBlock( district_id, block ):
        block_ids = []
        if type(block) == int:
            block_ids.append( block )
        elif type(block) == VotingDistrict:
            block_ids.append( block.id )
        elif type(block) == list or type(block) == set:
            for item in block:
                if type(item) == int:
                    block_ids.append( item )
                elif type(item) == VotingDistrict:
                    block_ids.append( item.id )

        print( 'Showing blocks: ', block_ids )
        data = gpd.read_file( "jax_tl_2020_51_vtd20.shp" )
        # Add district columns
        cong_dist = []
        for voting_district in VotingDistrict.voting_districts:
            if voting_district.id in block_ids:
                cong_dist.append( 2 )
            else:
                if voting_district.district == district_id:
                    cong_dist.append( 0 )
                else:
                    cong_dist.append( 1 )

        data['CongDist'] = cong_dist
        print( data.head() )

        data.plot(column='CongDist')
        plt.show()
        
    def getPopMetric():
        district_populations = []
        for district in District.districts:
            district_populations.append( district.population )
        pop_mean = statistics.mean( district_populations )
        pop_stdev = statistics.stdev( district_populations )

        metric = pop_stdev/pop_mean
        return metric

    #------------------------------------------------------------------
    # Returns whether a block group is contiguous.
    #------------------------------------------------------------------
    def isContiguous( self ):
        if len( self.voting_districts ) == 0: return True
        
        voting_districts = []
        nCurrent = 0
        start = self.voting_districts[0]
        voting_districts.append( start )
        nNew = len( voting_districts )
        while ( nNew > nCurrent ):
            nCurrent = nNew
            for voting_district in voting_districts:
                for neighbor in voting_district.neighbors:
                    if ( neighbor.voting_district.district == self.id ):
                        if ( neighbor.voting_district not in voting_districts ):
                            voting_districts.append( neighbor.voting_district )
            nNew = len( voting_districts )
        assert( nCurrent <= len( self.voting_districts ))
        if nCurrent == len( self.voting_districts ):
            return True
        else:
            # print( 'Only %d of %d block groups counted' %(nCurrent,len( self.voting_districts ) ) )
            return False

    def getBorderLength( self, voting_district ):
        border_len = 0.0
        for neighbor in voting_district.neighbors:
            if neighbor.voting_district.district == voting_district.district:
                border_len += neighbor.border_len
        return border_len
        
    #------------------------------------------------------------------
    # Returns list of districts that border this block group.
    #------------------------------------------------------------------
    def getNeighboringDistricts( voting_district ):
        neighboring_districts = []
        for neighbor in voting_district.neighbors:
            if neighbor.voting_district.district not in neighboring_districts:
                neighboring_districts.append( neighbor.voting_district.district )

        try:
            neighboring_districts.remove( voting_district.district )
        except ValueError:
            # This should not happen, but we can correct it by adding this
            # block group to the neighboring district with the longest border
            best_fit = District.districts[neighboring_districts[0]]
            longest = best_fit.getBorderLength( voting_district )
            for district_id in neighboring_districts[1:]:
                district = District.districts[district_id]
                if district.getBorderLength( voting_district ) > longest:
                    best_fit = district
            best_fit.addVotingDistrict( voting_district )
            
        return neighboring_districts
        
    #------------------------------------------------------------------
    # Builds the set of this district's border blocks.
    #------------------------------------------------------------------
    def getBorderBlocks( self ):
        border_set = set()
        for voting_district in self.voting_districts:
            for neighboring_district_id in District.getNeighboringDistricts( voting_district ):
                border_set.add( (voting_district,neighboring_district_id) )
        return border_set

    #----------------------------------------------------------------------------
    # Returns True if this block group can be moved from its current district
    # to the one specified without increasing the population disparity and
    # without making its current district discontiguous.
    #----------------------------------------------------------------------------
    def isValidCandidate( self, voting_district, neighboring_district_id ):
        this_district = District.districts[voting_district.district]
        neighboring_district = District.districts[neighboring_district_id]

        # Cannot move a block to the district it's already in.
        if voting_district.district == neighboring_district_id:
            return False

        # Cannot move a block that does not belong to this distict
        if voting_district.district != self.id:
            return False

        # Cannot move a block to a district it does not border
        neighboring_districts = District.getNeighboringDistricts( voting_district )

        return ( neighboring_district_id in neighboring_districts )
        
    #----------------------------------------------------------------
    # Compute ratio of candidate's border with its current district
    # and its border with neighboring district.
    # A border rati of 0.0 means that the two do not share a border.
    #----------------------------------------------------------------
    def getBorderRatio( voting_district, district_id ):

        if voting_district.district == district_id:
            return 0.0
        
        current_district_border = 0.0
        neighboring_district_border = 0.0
        for neighbor in voting_district.neighbors:
            if neighbor.voting_district.district == voting_district.district:
                current_district_border += neighbor.border_len
            elif neighbor.voting_district.district == district_id:
                neighboring_district_border += neighbor.border_len

        return (neighboring_district_border / current_district_border)

    #------------------------------------------------------------------
    # This function returns the best block group to transfer.
    # It will return the most protruding block group that
    # does not increase population disparity.
    #------------------------------------------------------------------
    def buildCandidateDict( self ):
        candidates = {}

        # Build set of this district's border blocks
        border_set = self.getBorderBlocks()
        
        # Loop over border blocks
        for key in border_set:
            candidate = key[0]
            neighboring_district_id = key[1]
            
            # If not a valid candidate, continue looping
            if not self.isValidCandidate( candidate, neighboring_district_id ): continue

            border_ratio = District.getBorderRatio( candidate, neighboring_district_id )

            # Save this information in dictionary of candidates
            candidates.update( {key: border_ratio} )

        return candidates

    def getBestCandidate( candidates ):
        best = None
        # Loop through candidates
        for key in candidates:
            # Compare current with best and save best
            if best==None or candidates[best] < candidates[key]:
                best = key
                
        return best

    #-----------------------------------------------------------------------
    # Performs an insertion sort and returns list of district IDs
    # from most populated to least.
    #-----------------------------------------------------------------------
    def sortByPopulation():
        sorted = [District.districts[0]]
        least = District.districts[0].population
        
        for district in District.districts[1:]:
            if district.population < least:
                sorted.append( district )
                least = district.population
                continue
            
            for ii in list(range(len(sorted))):
                if district.population > sorted[ii].population:
                    sorted.insert( ii, district )
                    break
                
        return sorted
            
    #-----------------------------------------------------------------------
    # Performs an insertion sort and returns list of district IDs
    # from largest perimeter to smallest.
    #-----------------------------------------------------------------------
    def sortByPerimeter():
        sorted = [District.districts[0]]
        smallest = District.districts[0].getPerimeter()
        
        for district in District.districts[1:]:
            perim = district.getPerimeter() 
            if perim < smallest:
                sorted.append( district )
                smallest = perim
                continue

            for ii in list(range(len(sorted))):
                if  perim > sorted[ii].getPerimeter():
                    sorted.insert( ii, district )
                    break
                
        return sorted
            
    def minimizeTotalPerimeter( tolerance ):
        # tolerance: the largest allowable normalized standard deviation

        # Compute metrics
        pops = District.getDistrictPopulations()
        max_pop = max( pops )
        min_pop = min( pops )
        sd = statistics.stdev( pops )
        metric = (max_pop - min_pop) / ( District.population / District.count )

        print( 'Max Pop: %7d' %max_pop )
        print( 'Min Pop: %7d' %min_pop )
        print( 'Std Dev: %3f' %metric )

        numTransferred = -1
        # Loop twice
        while numTransferred != 0:

            numTransferred = 0
            
            # Sort districts by perimeter
            sorted = District.sortByPerimeter()

            # Show sorted districts
            for district in sorted:
                print( 'District %2d has %8d people, and perimeter of %12.3f m.'
                       %(district.id, district.population, district.getPerimeter() ) )

            # Plot districts
            # District.plotDistricts()
            
            # Loop over districts in sorted order
            for district in sorted:

                # Build list of candidate block groups to move
                print( 'Building candidates list...', end='' )
                candidates = district.buildCandidateDict()
                print( 'done.' )

                # Get best block group to move
                move_me = District.getBestCandidate( candidates )

                # Continue until there are no more to move
                while move_me != None:

                    voting_district = move_me[0]
                    neighboring_district = District.districts[move_me[1]]
                    try:
                        border_ratio = candidates.pop( move_me )
                    except KeyError:
                        # print( '( %d, %d ) not in candidates'
                        #        %(move_me[0].id, move_me[1]) )
                        move_me = District.getBestCandidate( candidates )
                        continue

                    # Ensure candidate will improve total perimeter
                    if border_ratio < 1.0:
                        move_me = District.getBestCandidate( candidates )
                        continue
                        
                    # Ensure that this candidate is still valid
                    if not district.isValidCandidate( move_me[0], move_me[1] ):
                        continue

                    # Move block group to new district
                    print( 'Moving block group %4d from %2d to %2d'
                           %( voting_district.id, voting_district.district, neighboring_district.id ) )
                    neighboring_district.addVotingDistrict( voting_district )
                    numTransferred += 1

                    # Recompute metrics.
                    pops = District.getDistrictPopulations()
                    max_pop = max( pops )
                    min_pop = min( pops )
                    sd = statistics.stdev( pops )
                    metric = (max_pop - min_pop) / ( District.population / District.count )

                    # If we have exceeded tolerance, return block
                    if ( metric > tolerance ):
                        print( 'Returning block group %4d' %voting_district.id )
                        district.addVotingDistrict( voting_district )
                        numTransferred -= 1
                        continue
                    
                    # If the current district is now discontiguous,
                    # we need to dissolve the smaller part
                    if not district.isContiguous():
                        district.fixDiscontiguous()

                    # Now need to recheck the neighboring block groups.
                    # Remove them from the candidates list.  Don't re-add.
                    # Only doing one pass per district before moving on.
                    for neighbor in voting_district.neighbors:
                        if neighbor.voting_district not in district.voting_districts:
                            continue

                        try:
                            candidates.pop( (neighbor.voting_district, neighboring_district.id) )
                        except KeyError:
                            pass

                    # Get best block group to move
                    move_me = District.getBestCandidate( candidates )

            # Fix discontiguous districts
            District.fixAllDiscontiguous()
            
            # Recompute metrics
            pops = District.getDistrictPopulations()
            max_pop = max( pops )
            min_pop = min( pops )
            sd = statistics.stdev( pops )
            metric = sd / (District.population / District.count)

            print( 'Max Pop: ', max_pop )
            print( 'Min Pop: ', min_pop )
            print( 'Std Dev: %3f' %metric )
        return
        
    #-----------------------------------------------------------------------
    # Moves border blocks, one at a time, from one district to another,
    # until the required balance is met.
    #-----------------------------------------------------------------------
    def balancePopulations( tolerance ):
        # tolerance: the largest allowable difference in population,
        #            divided by the average district poplation

        # Compute metrics
        pops = District.getDistrictPopulations()
        max_pop = max( pops )
        min_pop = min( pops )
        sd = statistics.stdev( pops )
        metric = (max_pop-min_pop) / (District.population / District.count)

        print( 'Max Pop: ', max_pop )
        print( 'Min Pop: ', min_pop )
        print( 'Std Dev: %.3f' %sd )
        print( 'Metric:  %.3f' %metric )

        numTransferred = -1
        while metric > tolerance and numTransferred != 0:

            numTransferred = 0
            
            # Sort districts by population
            sorted = District.sortByPopulation()

            # Show sorted districts
            for district in sorted:
                print( 'District %2d has %8d people, and perimeter of %12.3f m.'
                       %(district.id, district.population, district.getPerimeter() ) )

            # Loop over districts in sorted order
            for district in sorted:

                # Build list of candidate block groups to move
                print( 'Building candidates list...', end='' )
                candidates = district.buildCandidateDict()
                print( 'done.' )

                # Get best block group to move
                move_me = District.getBestCandidate( candidates )


                # Continue until there are no more to move
                while move_me != None:

                    voting_district = move_me[0]
                    neighboring_district = District.districts[move_me[1]]
                    try:
                        border_ratio = candidates.pop( move_me )
                    except KeyError:
                        # print( '( %d, %d ) not in candidates'
                        #        %(move_me[0].id, move_me[1]) )
                        move_me = District.getBestCandidate( candidates )
                        continue

                    # Ensure that this candidate is still valid
                    if not district.isValidCandidate( move_me[0], move_me[1] ):
                        move_me = District.getBestCandidate( candidates )
                        continue

                    # Check population difference between districts.
                    pop_diff = district.population - neighboring_district.population
                    if pop_diff < voting_district.population:
                        move_me = District.getBestCandidate( candidates )
                        continue
        
                    # Move block group to new district
                    print( 'Moving block group %4d from %2d to %2d'
                           %( voting_district.id, voting_district.district, neighboring_district.id ) )
                    neighboring_district.addVotingDistrict( voting_district )
                    numTransferred += 1

                    # We now need to recheck the neighboring block groups
                    # Remove them from the candidates list, and re-add
                    for neighbor in voting_district.neighbors:
                        if neighbor.voting_district not in district.voting_districts:
                            continue

                        try:
                            candidates.pop( (neighbor.voting_district, neighboring_district.id) )
                        except KeyError:
                            pass

                        for tmp in District.getNeighboringDistricts( neighbor.voting_district ):
                            # If neighbor not a valid candidate to move to
                            # the tmp district, continue looping
                            if not district.isValidCandidate( neighbor.voting_district, tmp ): continue

                            # Get border ratio
                            border_ratio = District.getBorderRatio( neighbor.voting_district, tmp )

                            # Save this information in dictionary of candidates
                            candidates.update( {(neighbor.voting_district,tmp): border_ratio} )

                    # Get best block group to move
                    move_me = District.getBestCandidate( candidates )

            # Recompute metrics
            pops = District.getDistrictPopulations()
            max_pop = max( pops )
            min_pop = min( pops )
            sd = statistics.stdev( pops )
            metric = (max_pop-min_pop) / (District.population / District.count)

            print( 'Max Pop: ', max_pop )
            print( 'Min Pop: ', min_pop )
            print( 'Std Dev: %.3f' %sd )
            print( 'Metric:  %.3f' %metric )
        return
    
    #-----------------------------------------------------------------------
    # Returns a list containing all district populations
    #-----------------------------------------------------------------------
    def getDistrictPopulations():
        populations = []
        for district in District.districts:
            populations.append( district.population )
        return populations
    #-----------------------------------------------------------------------
    # This function returns a list of tuples.  These tuples have:
    # ( candidate, neighboring_district, dPerim )
    #-----------------------------------------------------------------------
    def neighboringDistricts( self, candidate ):
        results = []
        # Loop over neighboring block groups to collect their district IDs
        neighboring_districts = []
        for neighbor in candidate.neighbors:

            # print( neighbor )
            neighbor_id = neighbor.voting_district.id
            neighbor_district_id = neighbor.voting_district.district

            # Skip blocks that are in the same district
            if neighbor_district_id == self.id: continue

            # If we've already dealt with this neighbor district, continue
            neighbor_district = District.districts[neighbor_district_id]
            if neighbor_district in neighboring_districts: continue

            # Add neighboring district to list
            neighboring_districts.append( neighbor_district )

        # If there are no neighboring district, just return
        if len(neighboring_districts) == 0:
            print( 'Candidate block group %d is not on a district border' %candidate.id )
            return results

        # Loop over neighboring districts
        for neighbor_district in neighboring_districts:

            # To transfer a block group to another district, that district should
            # have a smaller population than this one minus the block group.
            pop_diff = self.population - neighbor_district.population
            if pop_diff < 0:
                print( 'District %d has a larger population.' %neighbor_district.id )
                print( '   District %2d:   %10d'  %(self.id, self.population) )
                print( '   District %2d:   %10d'  %(neighbor_district.id, neighbor_district.population) )
                continue                   
                                                    
            if  candidate.population >= pop_diff:
                print( 'Block group %d has a population larger than difference' %candidate.id )
                print( '   Block group:    %10d'  %candidate.population )
                print( '   This district:  %10d'  %self.population )
                print( '   District %2d:   %10d'  %(neighbor_district.id, neighbor_district.population) )
                continue
            
            # ---------------------------------------------------------
            # Determine difference in total perimeter for this district
            # ---------------------------------------------------------

            # This district will lose this block group's borders with other
            # districts, and gain this block group's borders with itself.
            dPerimSelf = 0.0
            for tmp in candidate.neighbors:
                if self.id != tmp.voting_district.district:
                    dPerimSelf -= tmp.border_len
                else:
                    dPerimSelf += tmp.border_len

            # Neighboring district will gain this block group's borders with
            # other districts, and lose this block group's borders with itself.
            dPerimNeighbor = 0.0
            for tmp in candidate.neighbors:
                if neighbor_district.id != tmp.voting_district.district:
                    dPerimNeighbor += tmp.border_len
                else:
                    dPerimNeighbor -= tmp.border_len

            # Determine the total change in perimeters
            dPerim = dPerimSelf + dPerimNeighbor

            # Add this district info to results
            results.append( (candidate, neighbor_district, dPerim) )

        # Return results
        return results
        
    def reducePopulation( self ):
        totalTransferred = 0

        # Create initial list of candidate block groups for transfer
        # to neighboring districts
        
        # Collect all block groups that border less populated districts
        candidates = []
        neighboring_districts = []
        print( 'Getting candidate block groups to transfer out of %d' %self.id )
        for candidate in self.voting_districts:

            for info in self.neighboringDistricts( candidate ):
                if info not in candidates:
                    print( 'Adding candidate: %4d, district %2d' %(info[0].id, info[1].id) )
                    candidates.append( info )

        print( 'Have %d candidates.' %(len(candidates)) )
        last_transferred = None
        # Loop over candidates
        while len(candidates) > 0:

            # Ensure all districts are still contiguous
            discontiguous = District.getDiscontiguous()
            if len(discontiguous) > 0:
                District.info()
                if last_transferred != None:
                    voting_district = last_transferred[0]
                    neighboring_district = last_transferred[1]
                    print( 'Last: Block Group %d transferred from district %d to %d.'
                           %( voting_district.id, self.id, neighboring_district.id ) )
                    for dist in discontiguous:
                        District.showDistrictAndBlock( dist, last_transferred[0].id )
                exit()
            # Find the candidate block group to transfer which most reduces
            # total perimeter (or increases total perimeter the least.)
            best = candidates[0]
            for ndx in list(range(1,len(candidates))):
                if candidates[ndx][2] < best[2]:
                    best = candidates[ndx]

            # Remove all entries of best candidate from the list
            for candidate in candidates:
                if candidate[0] == best[0]:
                    candidates.remove(candidate)

            # Re-check populations
            neighbor_district = best[1]
            pop_diff = self.population - neighbor_district.population
            if pop_diff < 0.0:
                for tmp in candidates:
                    if tmp[1] == neighbor_district:
                        candidates.remove( tmp )
                continue
            
            if  best[0].population >= pop_diff:
                continue
                
            # Transfer best candidate
            neighbor_district.addVotingDistrict( best[0] )
            
            # Ensure all districts are still contiguous
            discontiguous = District.getDiscontiguous()
            if len(discontiguous) > 0:
                self.addVotingDistrict( best[0] )
                for iDisc in list(range(len(discontiguous))):
                    print( 'Removing block group %d from District %d made district %d discontiguous'
                           %(best[0].id, self.id, discontiguous[iDisc] ) )

                # Ensure all districts are still contiguous
                discontiguous = District.getDiscontiguous()
                if len(discontiguous) > 0:
                    District.info()
                    voting_district = best[0]
                    neighboring_district = best[1]
                    for iDisc in list(range(len(discontiguous))):
                        print( 'Last: Block Group %d transferred from district %d to %d.'
                               %( voting_district.id, self.id, neighboring_district.id ) )
                        print( '      Replacing it did not fix problem.' )
                        for dist in discontiguous:
                            District.showDistrictAndBlock( dist, best[0].id )
                    exit()
                continue

            last_transferred = best
            print( 'Block Group %d transferred from %d to %d'
                   %(last_transferred[0].id, self.id, neighbor_district.id ) )
            totalTransferred += 1

            # All neighbors have to be removed and readded,
            # because their borders with the neighboring district have changed
            for neighbor in best[0].neighbors:
                for tmp in candidates:
                    if tmp[0] == neighbor:
                        candidates.remove(tmp)
                        
                if neighbor.voting_district.district == self.id:
                    for info in self.neighboringDistricts( neighbor.voting_district ):
                        print( 'Adding candidate: %4d, district %2d' %(info[0].id, info[1].id) )
                        candidates.append( info )
            
            print( 'Have %d candidates.' %(len(candidates)) )
            
        print( 'Num transferred: %d' %totalTransferred )

        return totalTransferred

    #------------------------------------------------------------------
    # Returns an list of tuples.
    # Element [0] is a list of block groups.
    # Element [1] is the population of the island.
    #------------------------------------------------------------------
    def getIslands( self ):
        print( 'Getting islands for district %d' %self.id )
        voting_districts = set( self.voting_districts )
        islands = []
        while len(voting_districts) > 0:
            print( 'block groups remaining: %d' %len(voting_districts) )
            island = []
            population = 0
            start = voting_districts.pop()
            island.append( start )
            new_pop = start.population
            while new_pop != 0:
                new_pop = 0
                # Loop thru block groups currently in this island
                for ndx in list(range(len(island))):
                    voting_district = island[ndx]
                    
                    # Loop thru block groups nieghbors
                    for neighbor in voting_district.neighbors:
                        # If neighbor is in the same district
                        if ( neighbor.voting_district.district == self.id ):
                            # add neighbor to island
                            if neighbor.voting_district not in island:
                                island.append( neighbor.voting_district )
                                new_pop += neighbor.voting_district.population
                            # remove neighbor from voting_districts
                            voting_districts.discard( neighbor.voting_district )

                # Add new population to total island population
                population += new_pop

            # Add to list of islands
            islands.append( (island,population) )
            
        return islands

    def fixDiscontiguous( self ):
        # Get islands
        islands = self.getIslands()

        # Find largest by population
        largest = islands[0]
        for island in islands[1:]:
            if island[1] > largest[1]:
                largest = island

        # Loop over islands
        tmp = []
        for island in islands:
            # Keep largest
            if island == largest: continue

            # Loop until island is dissolved
            count = 0
            while len(island[0]) > 0:
                count += 1
                print( len(island[0]), ' block groups left to move' ) 
                tmp.clear()
                # Get the first block group
                for voting_district in island[0]:
                    old_district_id = voting_district.district
                    if old_district_id != self.id: continue
                    
                    print( 'This district: %d' %self.id )
                    print( 'Trying to relocate block group %d from %d.'
                           % (voting_district.id,voting_district.district) )
                    for neighbor in voting_district.neighbors:
                        print( '  Neighbor %d is in %d.'
                               % (neighbor.voting_district.id,neighbor.voting_district.district) )
                        
                        if neighbor.voting_district.district != old_district_id:
                            new_district_id = neighbor.voting_district.district
                            new_district = District.districts[new_district_id]
                            new_district.addVotingDistrict( voting_district )
                            print( 'Moving %d from %d to %d'
                                   %(voting_district.id,old_district_id,new_district_id) )
                            break
                    if count > 10: continue
                    if voting_district.district == old_district_id:
                        tmp.append( voting_district )
                        
                island[0].clear()
                for bg in tmp: island[0].append( bg )
        
    def fixAllDiscontiguous():
        for district in District.districts:
            if not district.isContiguous():
                district.fixDiscontiguous()
