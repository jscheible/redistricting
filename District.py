import geopandas as gpd
import matplotlib.pyplot as plt
from VotingDistrict import VotingDistrict
import numpy
from shapely.geometry import Point, Polygon, MultiPolygon, MultiLineString, LineString, shape, mapping
import sys
import time

class District:
    count = 0
    districts = []
    population = 0

    def __init__( self ):
        self.id = District.count
        District.count += 1
        self.population = 0
        self.democrat = 0
        self.republican = 0
        self.perimeter = 0.0
        self.area = 0.0
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

    def getWeightedCentroid( self ):
        sum_lat = 0.0
        sum_lon = 0.0
        sum_pop = 0
        for vtd in self.voting_districts:
            sum_lat += vtd.population * vtd.intptlat
            sum_lon += vtd.population * vtd.intptlon
            sum_pop += vtd.population

        return sum_lat/sum_pop, sum_lon/sum_pop

    def voting():
        print( '----------------------------------------------------' )
        print( '| District ID |   Democrat   | Republican | Result |' )
        print( '----------------------------------------------------' )
        for district in District.districts:
            if district.democrat > district.republican:
                result = 'D'
            elif district.democrat < district.republican:
                result = 'R'
            else:
                result = '-'

            print( '|     %2d      |  %7d     |  %7d   |   %s    |'
                       %( district.id, district.democrat, district.republican, result ) )
        print( '----------------------------------------------------' )

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
               %( numpy.mean(voting_districts), numpy.mean(populations), numpy.mean(perimeters) ) )
        print( '|   Metric    |     N/A    |      %6d      |     N/A    |       N/A       |'
               %( 100*(max(populations)-min(populations))/ numpy.mean(populations) ) )
        print( '------------------------------------------------------------------------------' )
        sys.stdout.flush()
        time.sleep(1)

    def addVotingDistrict( self, voting_district ):
        assert( isinstance( voting_district, VotingDistrict ) )
        cd = voting_district.district
        if cd != None:
            District.districts[cd].delVotingDistrict( voting_district )
        self.voting_districts.append( voting_district )
        self.perimeter_up_to_date = False
        self.population += voting_district.population
        self.democrat += voting_district.democrat
        self.republican += voting_district.republican
        self.area += voting_district.area
        District.population += voting_district.population
        self.getCompactness()
        voting_district.district = self.id

    def delVotingDistrict( self, voting_district ):
        assert( isinstance( voting_district, VotingDistrict ) )
        try:
            self.voting_districts.remove( voting_district )
            voting_district.district = None
            self.perimeter_up_to_date = False
            self.population -= voting_district.population
            self.democrat -= voting_district.democrat
            self.republican -= voting_district.republican
            self.area -= voting_district.area
            District.population -= voting_district.population
            self.getCompactness()
        except ValueError:
            pass

    #-----------------------------------------------------------------------
    # Returns a compactness measure
    #-----------------------------------------------------------------------
    def getCompactness( self ):
        if ( not self.perimeter_up_to_date ):
            self.getPerimeter()
            self.compactness = self.area / ((self.perimeter/1000.0)*(self.perimeter/1000.0))
        return self.compactness

    #-----------------------------------------------------------------------
    # Returns the VTD furthest from the population centroid
    #-----------------------------------------------------------------------
    def getMostRemoteVTD( self ):
        mostDistant = 0.0
        clat, clon = self.getWeightedCentroid()
        for vtd in self.voting_districts:
            dist = ( clat - vtd.intptlat )**2 + ( clon - vtd.intptlat )**2
            if dist > mostDistant:
                furthest = vtd
                mostDistant = dist

        return furthest

    #-----------------------------------------------------------------------
    # Returns the largest voting district by number of VTDs
    #-----------------------------------------------------------------------
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

    def showMetrics():
        # Recompute metrics
        pops = District.getDistrictPopulations()
        max_pop = max( pops )
        min_pop = min( pops )
        metric = ( max_pop - min_pop ) / (District.population / District.count)

        print( 'Max Pop: ', max_pop )
        print( 'Min Pop: ', min_pop )
        print( 'Metric: %3f' %metric )

    #-------------------------------------------------------------------------
    # Returns the length of the border between this list of VTDs
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
    # Returns the perimeter of the district
    #-------------------------------------------------------------------------
    def getPerimeter( self ):
        if ( self.perimeter_up_to_date ): return self.perimeter
        self.perimeter = 0.0
        for voting_district in self.voting_districts:
            # Add perimeter of VTD to perimeter of district
            self.perimeter += voting_district.perimeter

            # Loop over neighboring VTDs
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
        perim_mean = numpy.mean( district_perimeters )
        perim_stdev = numpy.std( district_perimeters )
        pop_mean = numpy.mean( district_populations )
        pop_stdev = numpy.std( district_populations )

        metric = ( perim_stdev/perim_mean + pop_stdev/pop_mean ) / 2.0 
        return metric

    def plotDistricts():
        data = gpd.read_file( shape_file )
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
        data = gpd.read_file( shape_file )

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
        pop_mean = numpy.mean( district_populations )
        pop_stdev = numpy.std( district_populations )

        metric = pop_stdev/pop_mean
        return metric

    #------------------------------------------------------------------
    # Returns whether a district is contiguous.
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
    def getBorderVTDs( self ):
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
    # Compute ratio of candidate's border with neighboring district
    # and its perimeter.
    # A border ratio of 0.0 means that the two do not share a border.
    #----------------------------------------------------------------
    def getBorderRatio( self, voting_district ):

        if voting_district.district == self.id:
            return 0.0

        current_district_border = 0.0
        neighboring_district_border = 0.0
        for neighbor in voting_district.neighbors:
            if neighbor.voting_district.district == self.id:
                neighboring_district_border += neighbor.border_len

        return (neighboring_district_border / voting_district.perimeter)

    #------------------------------------------------------------------
    # This function builds a dictionary of border VTDs with
    # their border ratio (district border / perimeter).
    #------------------------------------------------------------------
    def buildCandidateDict( self ):
        candidates = {}

        # Build set of this district's border VTDs
        border_set = self.getBorderVTDs()

        # Loop over border VTDs
        for key in border_set:
            candidate = key[0]
            neighboring_district_id = key[1]

            # If not a valid candidate, continue looping
            if not self.isValidCandidate( candidate, neighboring_district_id ): continue

            # Get border ratio
            border_ratio = District.districts[neighboring_district_id].getBorderRatio( candidate )

            # Save this information in dictionary of candidates
            candidates.update( {key: border_ratio } )

        return candidates

    #------------------------------------------------------------------
    # This function returns the best VTD to transfer.
    # It will return the VTD with the smallest border ratio.
    #------------------------------------------------------------------
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
    # from least compact to most compact.
    #-----------------------------------------------------------------------
    def sortByCompactness():
        sorted = [District.districts[0]]
        mostCompact = District.districts[0].getCompactness()

        for district in District.districts[1:]:
            compactness = district.getCompactness() 
            if compactness > mostCompact:
                sorted.append( district )
                mostCompact = compactness
                continue

            for ii in list(range(len(sorted))):
                if compactness < sorted[ii].getCompactness():
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

    #------------------------------------------------------------------------
    # Get VTDs that have a border with another district that is longer
    # than the border with their own district.
    #------------------------------------------------------------------------
    def getCandidates2():
        candidates = {}
        for vtd in VotingDistrict.voting_districts:
            # Get the border ratio for this VTD
            border_ratio = vtd.getBorderRatio()

            # If border ratio is over 0.5, go to next
            if border_ratio >= 0.5: continue

            # If there is a border with another district that is longer, add to candidates
            for neighbor in vtd.neighbors:
                ratio = vtd.getBorderRatioWithDistrict( neighbor.voting_district.district )
                if ratio > border_ratio:
                    candidates.update( { vtd: border_ratio } )
                    continue
        return candidates

    #------------------------------------------------------------------------
    # Move the VTD with the smallest border ratio with its own district.
    # Move to the neighbor district with the largest border ratio.
    # Rebuild the candidate list after each moved VTD.
    #------------------------------------------------------------------------
    def minimizeTotalPerimeter2( tolerance ):
        # tolerance: the largest allowable difference in population, divided by the average
        # Compute metrics
        pops = District.getDistrictPopulations()
        max_allowed_population = (1.0 + tolerance/2.0)*( District.population / District.count )
        min_allowed_population = (1.0 - tolerance/2.0)*( District.population / District.count )
        max_pop = max( pops )
        min_pop = min( pops )
        metric = (max_pop - min_pop) / ( District.population / District.count )

        print( 'Minimizing total perimeter.' )
        print( 'Max Pop: %7d' %max_pop )
        print( 'Max Allowed: %7d' %max_allowed_population )
        print( 'Min Pop: %7d' %min_pop )
        print( 'Min Allowed: %7d' %min_allowed_population )
        print( 'Tolerance: %3f' %tolerance )
        print( 'Metric:  %3f' %metric )

        numTransferred = -1
        while numTransferred != 0:

            print( "Transferred last cycle: ", numTransferred )
            numTransferred = 0

            # Get all border VTDs
            candidates = District.getCandidates2()

            # Get best VTD to move
            move_me = District.getBestCandidate( candidates )

            # Continue until there are no more candidates to move or one has been moved
            while move_me != None and numTransferred <= 0:

                thisVTD = move_me
                try:
                    border_ratio = candidates.pop( move_me )
                    print( "Border Ratio: ", border_ratio )
                except KeyError:
                    move_me = District.getBestCandidate( candidates )
                    continue

                # Get VTD's current district
                thisDistrict = District.districts[thisVTD.district]
                print( "Current district: ", thisDistrict.id )

                # Get thisVTD's neighboring districts and border ratios
                neighboring_districts = {}
                for neighbor in District.getNeighboringDistricts( thisVTD ):
                    print( "Neighbor district: ", neighbor )
                    neighbor_border_ratio = thisVTD.getBorderRatioWithDistrict( neighbor )
                    print( "Neighbor Border Ratio: ", neighbor_border_ratio )
                    if neighbor_border_ratio > border_ratio:
                        neighboring_districts.update( {neighbor:neighbor_border_ratio} )

                # Loop over these pulling one with the longest border first
                while len( neighboring_districts ) > 0:
                    longest_neighbor_district_id = None
                    longest_neighbor_district = None
                    longest_border = border_ratio
                    for key in neighboring_districts:
                        if neighboring_districts[key] > longest_border:
                            longest_border = neighboring_districts[key]
                            longest_neighbor_district_id = key
                            longest_neighbor_district = District.districts[key]

                    # If longest_neighbor_district is not set, punt
                    if longest_neighbor_district == None:
                        move_me = District.getBestCandidate( candidates )
                        break

                    # Remove longest from dictionary
                    neighboring_districts.pop( longest_neighbor_district_id )

                    # Ensure that this candidate is still valid
                    if not thisDistrict.isValidCandidate( thisVTD, longest_neighbor_district_id ):
                        continue

                    # Print populations
                    print( "This district's population will be: ", thisDistrict.population - thisVTD.population )
                    print( "Neighbor district's population will be: ", longest_neighbor_district.population + thisVTD.population )
                    print( "This VTD's population: ", thisVTD.population )
                    # Do not move if current district population will drop below minimum allowed
                    if (thisDistrict.population - thisVTD.population) < min_allowed_population:
                        continue

                    # Do not move if neighboring district population will exceed maximum allowed
                    if (longest_neighbor_district.population + thisVTD.population) > max_allowed_population:
                        continue

                    # Move VTD to new district and exit loop
                    print( 'Moving VTD %4d from %2d to %2d'
                           %( thisVTD.id, thisVTD.district, longest_neighbor_district_id ) )
                    longest_neighbor_district.addVotingDistrict( thisVTD )
                    numTransferred += 1

                    # If the current district is now discontiguous,
                    # we need to dissolve the smaller part
                    if not thisDistrict.isContiguous():
                        print( "District has become discontiguous.  Fixing." )
                        thisDistrict.fixDiscontiguous()

                    break

                # Get next best VTD to move
                move_me = District.getBestCandidate( candidates )

            # Fix discontiguous districts
            District.fixAllDiscontiguous()

            # Recompute metrics
            pops = District.getDistrictPopulations()
            max_pop = max( pops )
            min_pop = min( pops )
            metric = ( max_pop - min_pop ) / (District.population / District.count)

            print( 'Max Pop: ', max_pop )
            print( 'Min Pop: ', min_pop )
            print( 'Metric: %3f' %metric )
        return

    def minimizeTotalPerimeter( tolerance ):
        # tolerance: the largest allowable difference in population, divided by the average
        # Compute metrics
        pops = District.getDistrictPopulations()
        max_allowed_population = (1.0 + tolerance/2.0)*( District.population / District.count )
        min_allowed_population = (1.0 - tolerance/2.0)*( District.population / District.count )
        max_pop = max( pops )
        min_pop = min( pops )
        metric = (max_pop - min_pop) / ( District.population / District.count )

        print( 'Max Pop: %7d' %max_pop )
        print( 'Max Allowed: %7d' %max_allowed_population )
        print( 'Min Pop: %7d' %min_pop )
        print( 'Min Allowed: %7d' %min_allowed_population )
        print( 'Metric:  %3f' %metric )

        numTransferred = -1
        # Loop twice
        while numTransferred != 0:

            numTransferred = 0

            # Sort districts by compactness ( A/P^2 )
            sorted = District.sortByCompactness()

            # Show sorted districts
            for district in sorted:
                print( 'District %2d has compactness factor of %12.3f.'
                       %(district.id, district.getCompactness() ) )

            # Plot districts
            # District.plotDistricts()

            # Loop over districts in sorted order
            for district in sorted:

                print( 'District %2d has compactness factor of %12.3f.'
                       %(district.id, district.getCompactness() ) )

                # Build list of candidate VTDs to move
                # print( 'Building candidates list...', end='' )
                candidates = district.buildCandidateDict()
                # print( 'done.' )

                # Get best VTD to move
                move_me = District.getBestCandidate( candidates )

                # Continue until there are no more to move
                while move_me != None:

                    thisVTD = move_me[0]
                    try:
                        # distance_from_centroid = candidates.pop( move_me )
                        # print( "Distance from district centroid: ", distance_from_centroid )
                        border_ratio = candidates.pop( move_me )
                        # print( "Border Ratio: ", border_ratio )
                    except KeyError:
                        # print( '( %d, %d ) not in candidates'
                        #        %(move_me[0].id, move_me[1]) )
                        move_me = District.getBestCandidate( candidates )
                        continue

                    # Get thisVTD's neighboring districts
                    longest_border = 0
                    longest_neighbor_district = None
                    for neighbor in District.getNeighboringDistricts( thisVTD ):
                        border_length = thisVTD.getBorderLenWithDistrict( neighbor )
                        if border_length > longest_border:
                            longest_border = border_length
                            longest_neighbor_district = neighbor

                    # If longest_neighbor_district is not set, punt
                    if longest_neighbor_district == None:
                        move_me = District.getBestCandidate( candidates )
                        continue

                    # Ensure that this candidate is still valid
                    if not district.isValidCandidate( thisVTD, longest_neighbor_district ):
                        move_me = District.getBestCandidate( candidates )
                        continue

                    # Do not move if current district population will drop below minimum allowed
                    if (district.population - thisVTD.population) < min_allowed_population:
                        move_me = District.getBestCandidate( candidates )
                        continue

                    # Do not move if neighboring district population will exceed maximum allowed
                    if (longest_neighbor.population - thisVTD.population) > max_allowed_population:
                        move_me = District.getBestCandidate( candidates )
                        continue

                    # Move VTD to new district
                    print( 'Moving VTD %4d from %2d to %2d'
                           %( thisVTD.id, thisVTD.district, longest_neighbor.id ) )

                    # Recompute metrics.
                    pops = District.getDistrictPopulations()
                    max_pop = max( pops )
                    min_pop = min( pops )
                    metric = (max_pop - min_pop) / ( District.population / District.count )

                    # If the current district is now discontiguous,
                    # we need to dissolve the smaller part
                    if not district.isContiguous():
                        district.fixDiscontiguous()

                    # Get best VTD to move
                    move_me = District.getBestCandidate( candidates )

            # Fix discontiguous districts
            District.fixAllDiscontiguous()

            # Recompute metrics
            pops = District.getDistrictPopulations()
            max_pop = max( pops )
            min_pop = min( pops )
            metric = ( max_pop - min_pop ) / (District.population / District.count)

            print( 'Max Pop: ', max_pop )
            print( 'Min Pop: ', min_pop )
            print( 'Metric: %3f' %metric )
        return

    #-----------------------------------------------------------------------
    # Moves border VTDs, one at a time, from one district to another,
    # until the required balance is met.
    #-----------------------------------------------------------------------
    def balancePopulations( tol ):
        # Compute metrics
        pops = District.getDistrictPopulations()
        max_pop = max( pops )
        min_pop = min( pops )
        metric = (max_pop-min_pop) / numpy.mean( pops )

        print( 'Max Pop: ', max_pop )
        print( 'Min Pop: ', min_pop )
        print( 'Metric:  %.3f' %metric )
        print( 'Tolerance:  %.3f' %tol )

        # If Metric is already below tolerance, exit
        if metric <= tol: return

        # Set max_pop_diff to something too big for first loop
        max_pop_diff = max_pop

        numTransferred = -1
        while numTransferred != 0 and metric > tol :
            print( "Num Transferred last cycle: ", numTransferred )

            # Get max population difference
            pops = District.getDistrictPopulations()
            max_pop = max( pops )
            min_pop = min( pops )
            metric = (max_pop-min_pop) / (District.population / District.count)

            # If nothing got better, exit loop
            if ( max_pop - min_pop >= max_pop_diff ): break

            # Set max_pop_diff
            max_pop_diff = max_pop - min_pop

            # Reset numTransferred for this loop
            numTransferred = 0

            # Sort districts by population
            sorted = District.sortByPopulation()

            # Show sorted districts
            for district in sorted:
                print( 'District %2d has %8d people, and perimeter of %12.3f m.'
                       %(district.id, district.population, district.getPerimeter() ) )

            # Loop over districts in sorted order
            for district in sorted:

                # Build list of candidate VTDs to move
                # print( 'Building candidates list...', end='' )
                candidates = district.buildCandidateDict()
                # print( 'done.' )

                # Get best VTD to move
                move_me = District.getBestCandidate( candidates )

                # Continue until there are no more to move
                while move_me != None:

                    voting_district = move_me[0]
                    neighboring_district = District.districts[move_me[1]]
                    try:
                        distance_from_centroid = candidates.pop( move_me )
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
                    if pop_diff <= voting_district.population:
                        move_me = District.getBestCandidate( candidates )
                        continue

                    # Move VTD to new district
                    print( 'VTD %4d population: %6d'
                           %( voting_district.id, voting_district.population ) )
                    print( 'District %2d population: %6d' %( district.id, district.population ) )
                    print( 'District %2d population: %6d' %( neighboring_district.id, neighboring_district.population ) )
                    print( 'Moving VTD %4d from %2d to %2d'
                           %( voting_district.id, voting_district.district, neighboring_district.id ) )

                    neighboring_district.addVotingDistrict( voting_district )
                    print( 'VTD %4d is now in %2d'
                           %( voting_district.id, voting_district.district ) )
                    print( 'District %2d population: %6d' %( district.id, district.population ) )
                    print( 'District %2d population: %6d' %( neighboring_district.id, neighboring_district.population ) )
                    numTransferred += 1

                    # Get next best VTD to move
                    move_me = District.getBestCandidate( candidates )

            # Recompute metrics
            pops = District.getDistrictPopulations()
            max_pop = max( pops )
            min_pop = min( pops )
            metric = (max_pop-min_pop) / (District.population / District.count)

            print( 'Max Pop: ', max_pop )
            print( 'Min Pop: ', min_pop )
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
        # Loop over neighboring VTDs to collect their district IDs
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
            print( 'Candidate VTD %d is not on a district border' %candidate.id )
            return results

        # Loop over neighboring districts
        for neighbor_district in neighboring_districts:

            # To transfer a VTD to another district, that district should
            # have a smaller population than this one minus the VTD.
            pop_diff = self.population - neighbor_district.population
            if pop_diff < 0:
                print( 'District %d has a larger population.' %neighbor_district.id )
                print( '   District %2d:   %10d'  %(self.id, self.population) )
                print( '   District %2d:   %10d'  %(neighbor_district.id, neighbor_district.population) )
                continue                   

            if  candidate.population >= pop_diff:
                print( 'VTD %d has a population larger than difference' %candidate.id )
                print( '   VTD:            %10d'  %candidate.population )
                print( '   This district:  %10d'  %self.population )
                print( '   District %2d:   %10d'  %(neighbor_district.id, neighbor_district.population) )
                continue

            # ---------------------------------------------------------
            # Determine difference in total perimeter for this district
            # ---------------------------------------------------------

            # This district will lose this VTD's borders with other
            # districts, and gain this VTD's borders with itself.
            dPerimSelf = 0.0
            for tmp in candidate.neighbors:
                if self.id != tmp.voting_district.district:
                    dPerimSelf -= tmp.border_len
                else:
                    dPerimSelf += tmp.border_len

            # Neighboring district will gain this VTD's borders with
            # other districts, and lose this VTD's borders with itself.
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

        # Create initial list of candidate VTDs for transfer
        # to neighboring districts

        # Collect all VTDs that border less populated districts
        candidates = []
        neighboring_districts = []
        print( 'Getting candidate VTDs to transfer out of %d' %self.id )
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
                    print( 'Last: VTD %d transferred from district %d to %d.'
                           %( voting_district.id, self.id, neighboring_district.id ) )
                    for dist in discontiguous:
                        District.showDistrictAndBlock( dist, last_transferred[0].id )
                exit()
            # Find the candidate VTD to transfer which most reduces
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
                    print( 'Removing VTD %d from District %d made district %d discontiguous'
                           %(best[0].id, self.id, discontiguous[iDisc] ) )

                # Ensure all districts are still contiguous
                discontiguous = District.getDiscontiguous()
                if len(discontiguous) > 0:
                    District.info()
                    voting_district = best[0]
                    neighboring_district = best[1]
                    for iDisc in list(range(len(discontiguous))):
                        print( 'Last: VTD %d transferred from district %d to %d.'
                               %( voting_district.id, self.id, neighboring_district.id ) )
                        print( '      Replacing it did not fix problem.' )
                        for dist in discontiguous:
                            District.showDistrictAndBlock( dist, best[0].id )
                    exit()
                continue

            last_transferred = best
            print( 'VTD %d transferred from %d to %d'
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
    # Element [0] is a list of VTDs.
    # Element [1] is the population of the island.
    #------------------------------------------------------------------
    def getIslands( self ):
        print( 'Getting islands for district %d' %self.id )
        voting_districts = set( self.voting_districts )
        islands = []
        while len(voting_districts) > 0:
            print( 'VTDs remaining: %d' %len(voting_districts) )
            island = []
            population = 0
            start = voting_districts.pop()
            island.append( start )
            new_pop = start.population
            while new_pop != 0:
                new_pop = 0
                # Loop thru VTDs currently in this island
                for ndx in list(range(len(island))):
                    voting_district = island[ndx]

                    # Loop thru VTDs nieghbors
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
                print( len(island[0]), ' VTDs left to move' ) 
                tmp.clear()
                # Get the first VTD
                for voting_district in island[0]:
                    old_district_id = voting_district.district
                    if old_district_id != self.id: continue

                    print( 'This district: %d' %self.id )
                    print( 'Trying to relocate VTD %d from %d.'
                           % (voting_district.id,voting_district.district) )
                    for neighbor in voting_district.neighbors:
                        print( '  Neighbor %d is in %d.'
                               % (neighbor.voting_district.id,neighbor.voting_district.district) )

                        if neighbor.voting_district.district != old_district_id:
                            new_district_id = neighbor.voting_district.district
                            new_district = District.districts[new_district_id]
                            new_district.addVotingDistrict( voting_district )
                            # print( 'Moving %d from %d to %d'
                            #        %(voting_district.id,old_district_id,new_district_id) )
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
