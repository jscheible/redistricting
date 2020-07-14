import geopandas as gpd
import earthpy
import matplotlib.pyplot as plt
import matplotlib.cm as cm

class BlockGroup:
    count = 0
    block_groups = []

    def __init__( self ):
        self.id = BlockGroup.count
        BlockGroup.count += 1
        self.isBorder = False
        self.perimeter = 0.0
        self.border_len = 0.0
        self.population = 0
        self.neighbors = []
        self.embedded = []
        self.district = None
        BlockGroup.block_groups.append( self )

    def getPopulation( self ):
        pop = self.population
        for block_group in self.embedded:
            pop += block_group.population
        return pop
    
    def getBlockGroupCount():
        return len( BlockGroup.block_groups )
    
    def getNumUnassigned():
        nUnassigned = 0
        for block_group in BlockGroup.block_groups:
            if ( block_group.district == None ):
                nUnassigned += 1
        return nUnassigned

    def getBorderLen( self ):
        if self.border_len > 0.0:
            return self.border_len
        
        for neighbor in self.neighbors:
            self.border_len += neighbor.border_len
            # print( '   %d: %f' %( neighbor.block_group.id, neighbor.border_len ) )
        delta = self.perimeter - self.border_len 
        print( '%d: Delta=%0.3f' %( self.id, delta ) )
        if ( delta > 1.0 ): self.isBorder = True
        return self.border_len

    def plotBorder():
        # Read VA block group shape file
        va = gpd.read_file( "census/tl_2010_51_bg10.shp" )

        # Create border list
        isBorder = [False] * BlockGroup.count
        for block_group in BlockGroup.block_groups:
            isBorder[block_group.id] = block_group.isBorder

        # Add border column
        va['isBorder'] = isBorder
        va.plot(column='isBorder')
        plt.show()

    def plot( self ):
        # Read VA block group shape file
        va = gpd.read_file( "census/tl_2010_51_bg10.shp" )

        isThisBlockGroup = [False] * BlockGroup.count
        isThisBlockGroup[self.id] = True
        va['ThisOne'] = isThisBlockGroup
        va.plot(column='ThisOne')
        plt.show()
        
    def plotNeighbors( self ):
        # Read VA block group shape file
        va = gpd.read_file( "census/tl_2010_51_bg10.shp" )

        # Create neighbor column
        isNeighbor = [False] * BlockGroup.count
        for neighbor in self.neighbors:
            isNeighbor[neighbor.block_group.id] = True

        # Add border column
        va['isNeighbor'] = isNeighbor
        va.plot(column='isNeighbor')
        plt.show()

    def isEmbedded( self ):
        return ( len(self.neighbors) == 1 and 
                 self.neighbors[0].border_len == self.perimeter )
        
    def plotEmbeddedBlockGroups():
        # Read VA block group shape file
        va = gpd.read_file( "census/tl_2010_51_bg10.shp" )

        # loop through all block groups
        isEmbedded = [False] * BlockGroup.count
        for block_group in BlockGroup.block_groups:
            if block_group.isEmbedded():
                isEmbedded[block_group.id] = True
                
        # Add embedded column
        va['isEmbedded'] = isEmbedded
        va.plot(column='isEmbedded')
        plt.show()

    def fixEmbeddedBlockGroups():
        for block_group in BlockGroup.block_groups:
            if block_group.isEmbedded():
                block_group.neighbor[0].block_group.embedded.append( block_group )

    def addToDistrict( self, district ):
        self.district = district
        for block_group in self.embedded:
            block_group.district = district

    def removeFromDistrict( self, district ):
        if self.district == district:
            self.district = None
        for block_group in self.embedded:
            block_group.district = self.district
