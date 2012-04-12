#!python
# requires numpy
# requires pyyaml

import os, sys, time
import pymclevel


starttime = time.time()


######## Configuration

# Dimension of the world to clean
dimensionNum = 0

# Name of the world to open
worldname = "nyll"
world = pymclevel.fromFile(worldname)
dim = world.getDimension(dimensionNum)
mats = world.materials

# Number of chunks to process before cleaning memory
# 1024 chunks ~= 288 MB
chunksToCleanUpAfter = 3072 #3072

# Radius around relevant chunks to keep
radius = 0

# Level below which abandoned mineshafts will generate
mineshaftHeight = 64

# Level of maximum chunk generator height
chunkgenHeight = 128

# Level of flatworld height
flatworldHeight = 4

# Lists of relevant blocks:
# blocks that are always relevant
relevantBlocks = set([  mats.Sapling.ID,
                        mats.Sponge.ID,
                        mats.Glass.ID,
                        mats.WhiteWool.ID,
                        mats.BlockofGold.ID,
                        mats.BlockofIron.ID,
                        mats.DoubleStoneSlab.ID,
                        mats.StoneSlab.ID,
                        mats.Brick.ID,
                        mats.TNT.ID,
                        mats.Bookshelf.ID,
                        mats.LapisLazuliBlock.ID,
                        mats.Dispenser.ID,
                        mats.NoteBlock.ID,
                        mats.Bed.ID,
                        mats.PoweredRail.ID,
                        mats.DetectorRail.ID,
                        mats.StickyPiston.ID,
                        mats.Piston.ID,
                        mats.PistonHead.ID,
                        mats.RedstoneWire.ID,
                        mats.BlockofDiamond.ID,
                        mats.CraftingTable.ID,
                        mats.Crops.ID,
                        mats.Farmland.ID,
                        mats.Furnace.ID,
                        mats.LitFurnace.ID,
                        mats.Sign.ID,
                        mats.WoodenDoor.ID,
                        mats.Ladder.ID,
                        mats.StoneStairs.ID,
                        mats.WallSign.ID,
                        mats.Lever.ID,
                        mats.StoneFloorPlate.ID,
                        mats.IronDoor.ID,
                        mats.WoodFloorPlate.ID,
                        mats.RedstoneTorchOff.ID,
                        mats.RedstoneTorchOn.ID,
                        mats.Button.ID,
                        mats.Jukebox.ID,
                        mats.NetherPortal.ID,
                        mats.JackOLantern.ID,
                        mats.Cake.ID,
                        mats.RedstoneRepeaterOff.ID,
                        mats.RedstoneRepeaterOn.ID,
                        mats.Trapdoor.ID,
                        mats.HiddenSilverfishStone.ID,
                        mats.HiddenSilverfishCobblestone.ID,
                        mats.HiddenSilverfishStoneBrick.ID,
                        mats.StoneBricks.ID,
                        mats.IronBars.ID,
                        mats.GlassPane.ID,
                        mats.Watermelon.ID,
                        mats.PumpkinStem.ID,
                        mats.MelonStem.ID,
                        mats.FenceGate.ID,
                        mats.BrickStairs.ID,
                        mats.StoneBrickStairs.ID,
                        mats.idStr["ENCHANTMENT_TABLE"].ID,
                        mats.idStr["BREWING_STAND"].ID,
                        mats.idStr["CAULDRON"].ID,
                        mats.idStr["ENDER_PORTAL"].ID,
                        mats.idStr["ENDER_PORTAL_FRAME"].ID,
                        mats.idStr["ENDER_STONE"].ID,
                        122 #Ender Egg, not supported by pymclevel yet
                        ])

# blocks that abandoned mineshafts are made of
mineshaftBlocks = set([ mats.Rail.ID,
                        mats.WoodPlanks.ID,
                        mats.Torch.ID,
                        mats.Chest.ID,
                        mats.Fence.ID,
                        mats.WoodenStairs.ID ])
                        
# blocks that the nether is made of
netherBlocks = set([ mats.Netherrack.ID ])                        
                        
# blocks that flatworlds are made of (set of non-relevant blocks.)
flatworldBlocks = set([ mats.Air.ID,
                        mats.Grass.ID,
                        mats.Dirt.ID,
                        mats.Stone.ID,
                        mats.Bedrock.ID ])

# Relevant blocks to survival, excluding mineshafts.
relevantBlocksSurvival = relevantBlocks | netherBlocks

# All of these blocks should be relevant above mineshaft level.
relevantBlocksIncludingMineshafts = relevantBlocksSurvival | mineshaftBlocks

                        

######## Subroutines (based on world type)

# For survival worlds. Villages and strongholds will be kept, mineshafts will not be.
def isChunkRelevantNoMineshafts ( chunk ):
    # keep anything above chunk generator's max height
    for height in chunk.HeightMap.flat:
        if height >= chunkgenHeight:
            return True
    # keep relevant blocks above mineshaft height (including torches, wood, etc.)
    for voxel in chunk.Blocks[ :, :, mineshaftHeight:chunkgenHeight ].flat:
        if voxel in relevantBlocksIncludingMineshafts: 
            return True
    # ignore mineshafts below a certain level
    for voxel in chunk.Blocks[ :, :, 0:mineshaftHeight ].flat:
        if voxel in relevantBlocksSurvival:
            return True
    return False

# For creative flatworlds.     
def isChunkRelevantFlatworld ( chunk ):
    # keep anything above chunk generator's max height
    for height in chunk.HeightMap.flat:
        if height >= flatworldHeight:
            return True
    #check for relevant blocks below the generator's height
    for voxel in chunk.Blocks[ :, :, 0:flatworldHeight ].flat:
        if voxel not in flatworldBlocks: 
            return True
    return False
    
# For skylands.     
def isChunkRelevantSkylands ( chunk ):
    # keep anything above chunk generator's max height
    for height in chunk.HeightMap.flat:
        if height >= chunkgenHeight:
            return True
    for voxel in chunk.Blocks[ :, :, 0:chunkgenHeight ].flat:
        if voxel in relevantBlocksIncludingMineshafts: 
            return True
    return False

# For empty space worlds
def isChunkRelevantSpaceworld ( chunk ):
    for height in chunk.HeightMap.flat:
        if height != 0:
            return True
    return False
    
# We have to change our relevance function based on our world type
isChunkRelevant = isChunkRelevantSpaceworld

####### Main Code

#decorator for ioerrors
def workaround_io_errors(fn):
    def wrapped(*args):
        successful = False
        retval = None
        while not successful:
            try:
                retval = fn(*args)
                successful = True
            except IOError as (errno, strerror):
                print "I/O error({0}): {1}".format(errno, strerror)
                time.sleep(0.25)
        return retval
    return wrapped
    
@workaround_io_errors
def deleteChunk( x , z ):
    if dim.containsChunk( pos[0], pos[1] ):
        dim.deleteChunk( pos[0], pos[1] )
       
@workaround_io_errors 
def saveDim():
    dim.saveInPlace()
    
@workaround_io_errors 
def preloadChunkPositions():
    dim.preloadChunkPositions()
    

print "-------------------"
print "World:", worldname
print "Dimension:", dimensionNum
print "Radius:", radius
print "chunksToCleanUpAfter:", chunksToCleanUpAfter
print "Chunk Relevance Function:", isChunkRelevant.__name__
print "-------------------"
    
# determine which chunks are relevant
chunkRelevance = {}
chunksProcessed = 0

print "Determining number of chunks in dimension..."
allChunks = list( dim.allChunks )

#sort chunks by region, to minimize file access.
def cmp_regions_first( ca, cb ):
    ra = ( ca[0] / 32, ca[1] / 32 )
    rb = ( cb[0] / 32, cb[1] / 32 )
    if ra == rb:
        return cmp(ca, cb)
    else:
        return cmp(ra, rb)
allChunks.sort(cmp = cmp_regions_first )
totalChunks = len( allChunks )
#print allChunks
print totalChunks

print "Determining chunk relevance..."
starttimeChunkRelevance = time.time()
for pos in allChunks:
    
    # only process the chunk if we haven't looked at it.
    if pos not in chunkRelevance:
        chunk = dim.getChunk( pos[0], pos[1] );
        chunkRelevance[pos] = isChunkRelevant( chunk )
        
    else:
        print pos, "was in chunkRelevance."
    
    # Status report, griff!
    if chunksProcessed % 64 == 0:
        curtime = time.time()
        print 100 * float(chunksProcessed) / float(totalChunks), "% complete,", str( curtime - starttime )
    
    chunksProcessed += 1
    
    # Clean the dimension of unused memory
    assert( not chunk.dirty )
    chunk.unload() 
    assert( not chunk.isLoaded() )
    if chunksProcessed % chunksToCleanUpAfter == 0:
        print "Cleaning memory..."
        dim.close()
        dim.preloadChunkPositions()
     
curtime = time.time()
print "Chunk relevance took", str( curtime - starttimeChunkRelevance ), "s."
print "Chunk relevance complete. Processed", chunksProcessed, "chunks."

chunksProcessed = 0
# delete irrelevant chunks
for pos, relevant in chunkRelevance.items():
    if not relevant:
        # are there any relevant chunks in the radius?
        radiusRelevant = False
        for x in xrange( pos[0] - radius, pos[0] + radius + 1 ):
            for z in xrange( pos[1] - radius, pos[1] + radius + 1):
                if (x,z) in chunkRelevance:
                    if chunkRelevance[(x,z)] == True:
                        radiusRelevant = True
        
        #print "Deleting chunk at", pos
        if not radiusRelevant:
            deleteChunk( pos[0], pos[1] )
            chunksProcessed += 1
        
            # status report
            if chunksProcessed % 64 == 0:
                curtime = time.time()
                print 100 * float(chunksProcessed) / float(totalChunks), "% deleted,", str( curtime - starttime )

            # Clean the dimension of unused memory
            if chunksProcessed % chunksToCleanUpAfter == 0:
                print "Cleaning memory..."
                saveDim()        
                dim.close() 
                preloadChunkPositions()

print "Chunk Deletion complete. Deleted", chunksProcessed, "chunks (", 100 * float(chunksProcessed) / float(totalChunks), "% )"

# save the world
dim.saveInPlace()
endtime = time.time()
print 'worldcleaner took %0.3f s' % ((endtime-starttime))
