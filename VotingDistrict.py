import geopandas as gpd
import earthpy
import matplotlib.pyplot as plt
import matplotlib.cm as cm

class VotingDistrict:
    count = 0
    voting_districts = []

    def __init__( self ):
        self.id = VotingDistrict.count
        VotingDistrict.count += 1
        self.isBorder = False
        self.perimeter = 0.0
        self.border_len = 0.0
        self.population = 0
        self.neighbors = []
        self.embedded = []
        self.district = None
        VotingDistrict.voting_districts.append( self )

    def getPopulation( self ):
        pop = self.population
        for voting_district in self.embedded:
            pop += voting_district.population
        return pop
    
    def getVotingDistrictCount():
        return len( VotingDistrict.voting_districts )
    
    def getNumUnassigned():
        nUnassigned = 0
        for voting_district in VotingDistrict.voting_districts:
            if ( voting_district.district == None ):
                nUnassigned += 1
        return nUnassigned

    def getBorderLen( self ):
        if self.border_len > 0.0:
            return self.border_len
        
        for neighbor in self.neighbors:
            self.border_len += neighbor.border_len
            # print( '   %d: %f' %( neighbor.voting_district.id, neighbor.border_len ) )
        delta = self.perimeter - self.border_len 
        print( '%d: Delta=%0.3f' %( self.id, delta ) )
        if ( delta > 1.0 ): self.isBorder = True
        return self.border_len

    def plotBorder():
        # Read VA block group shape file
        va = gpd.read_file( "census/tl_2010_51_bg10.shp" )

        # Create border list
        isBorder = [False] * VotingDistrict.count
        for voting_district in VotingDistrict.voting_districts:
            isBorder[voting_district.id] = voting_district.isBorder

        # Add border column
        va['isBorder'] = isBorder
        va.plot(column='isBorder')
        plt.show()

    def plot( self ):
        # Read VA block group shape file
        va = gpd.read_file( "census/tl_2010_51_bg10.shp" )

        isThisVotingDistrict = [False] * VotingDistrict.count
        isThisVotingDistrict[self.id] = True
        va['ThisOne'] = isThisVotingDistrict
        va.plot(column='ThisOne')
        plt.show()
        
    def plotNeighbors( self ):
        # Read VA block group shape file
        va = gpd.read_file( "census/tl_2010_51_bg10.shp" )

        # Create neighbor column
        isNeighbor = [False] * VotingDistrict.count
        for neighbor in self.neighbors:
            isNeighbor[neighbor.voting_district.id] = True

        # Add border column
        va['isNeighbor'] = isNeighbor
        va.plot(column='isNeighbor')
        plt.show()

    #-------------------------------------------------------------------------
    # Returns the perimeter of the group of blocks specified.
    #-------------------------------------------------------------------------
    def getPerimeter( voting_districts ):
        perimeter = 0.0
        # Ensure we do not double-count by using sets
        voting_district_set = set( voting_districts )
        for voting_district in voting_district_set:
            # Add perimeter of block group to perimeter of group
            perimeter += voting_district.perimeter

            # Loop over neighboring block groups
            for neighbor in voting_district.neighbors:
                # If neighbor is in this group, subtract border length
                if ( neighbor.voting_district in voting_district_set ):
                    perimeter -= neighbor.border_len

        return perimeter

    def isEmbedded( self ):
        return ( len(self.neighbors) == 1 and 
                 self.neighbors[0].border_len == self.perimeter )
        
    def plotEmbeddedVotingDistricts():
        # Read VA block group shape file
        va = gpd.read_file( "census/tl_2010_51_bg10.shp" )

        # loop through all block groups
        isEmbedded = [False] * VotingDistrict.count
        for voting_district in VotingDistrict.voting_districts:
            if voting_district.isEmbedded():
                isEmbedded[voting_district.id] = True
                
        # Add embedded column
        va['isEmbedded'] = isEmbedded
        va.plot(column='isEmbedded')
        plt.show()

    def fixEmbeddedVotingDistricts():
        for voting_district in VotingDistrict.voting_districts:
            if voting_district.isEmbedded():
                voting_district.neighbor[0].voting_district.embedded.append( voting_district )

    def addToDistrict( self, district ):
        self.district = district
        for voting_district in self.embedded:
            voting_district.district = district

    def removeFromDistrict( self, district ):
        if self.district == district:
            self.district = None
        for voting_district in self.embedded:
            voting_district.district = self.district
