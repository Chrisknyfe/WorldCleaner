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
worldname = "creative"
world = pymclevel.fromFile(worldname)
dim = world.getDimension(dimensionNum)
mats = world.materials

# Number of chunks to process before cleaning memory
# 1024 chunks ~= 288 MB
chunksToCleanUpAfter = 8192 #3072

# Radius around relevant chunks to keep
radius = 3

# Level below which abandoned mineshafts will generate
mineshaftLevel = 64

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
                        
# blocks that flatworlds are made of
flatworldBlocks = set([ mats.Air.ID,
                        mats.Grass.ID,
                        mats.Dirt.ID,
                        mats.Stone.ID,
                        mats.Bedrock.ID ])


# All of these blocks should be relevant above mineshaft level.
relevantBlocksAboveMineshaftLevel = relevantBlocks | mineshaftBlocks
                        

######## Subroutines (based on world type)

# For survival worlds. Villages and strongholds will be kept, mineshafts will not be.
def isChunkRelevantNoMineshafts ( chunk ):
    for voxel in chunk.Blocks[ :, :, 0:mineshaftLevel ].flat:
        if voxel in relevantBlocks:
            return True
    for voxel in chunk.Blocks[ :, :, mineshaftLevel: ].flat:
        if voxel in relevantBlocksAboveMineshaftLevel: 
            return True
    return False

# For creative flatworlds.     
def isChunkRelevantFlatworld ( chunk ):
    for voxel in chunk.Blocks.flat:
        if voxel not in flatworldBlocks: 
            return True
    return False
    
# For skylands.     
def isChunkRelevantSkylands ( chunk ):
    for voxel in chunk.Blocks.flat:
        if voxel in relevantBlocksAboveMineshaftLevel: 
            return True
    return False

# For empty space worlds
def isChunkRelevantSpaceworld ( chunk ):
    for voxel in chunk.Blocks.flat:
        if voxel != 0: 
            return True
    return False
    
# We have to change our relevance function based on our world type
isChunkRelevant = isChunkRelevantNoMineshafts

####### Main Code

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
chunksDeepSearched = 0

print "Determining number of chunks in dimension..."
allChunks = list( dim.allChunks )
totalChunks = len( allChunks )
print totalChunks

print "Determining chunk relevance..."
for pos in allChunks:
    
    # only process the chunk if we haven't looked at it.
    if pos not in chunkRelevance:
        chunk = dim.getChunk( pos[0], pos[1] );
        chunkRelevance[pos] = isChunkRelevant( chunk )
        chunksDeepSearched += 1
        # all chunks within the radius are also relevant.
        if chunkRelevance[pos]:
            for x in xrange( pos[0] - radius, pos[0] + radius + 1 ):
                for z in xrange( pos[1] - radius, pos[1] + radius + 1):
                    chunkRelevance[(x,z)] = True
    else:
        print pos, "was in chunkRelevance."
    
    # Status report, griff!
    if chunksProcessed % 64 == 0:
        curtime = time.time()
        print float(chunksProcessed) / float(totalChunks), "% complete,", chunksDeepSearched, "searched,", str( curtime - starttime )
    
    chunksProcessed += 1
    
    # Clean the dimension of unused memory
    assert( not chunk.dirty )
    chunk.unload() 
    assert( not chunk.isLoaded() )
    if chunksDeepSearched % chunksToCleanUpAfter == 0:
        print "Cleaning memory..."
        dim.close()
        dim.preloadChunkPositions()
     
    
print "Chunk relevance complete. Processed", chunksProcessed, "chunks. Deep-searched", chunksDeepSearched, "chunks."

chunksProcessed = 0
# delete irrelevant chunks
for pos, relevant in chunkRelevance.items():
    if not relevant:
        
        
        #print "Deleting chunk at", pos
        # IOErrors might happen if we're working too fast?
        successful = False
        while not successful:
            try:
                if dim.containsChunk( pos[0], pos[1] ):
                    dim.deleteChunk( pos[0], pos[1] )
                successful = True
            except IOError as (errno, strerror):
                print "I/O error({0}): {1}".format(errno, strerror)
                time.sleep(0.25)
        chunksProcessed += 1
        
        # status report
        if chunksProcessed % 64 == 0:
            curtime = time.time()
            print float(chunksProcessed) / float(totalChunks), "% deleted,", str( curtime - starttime )

        # Clean the dimension of unused memory
        if chunksProcessed % chunksToCleanUpAfter == 0:
            print "Cleaning memory..."
            # IOErrors might happen if we're working too fast?
            successful = False
            while not successful:
                try:
                    dim.saveInPlace()
                    successful = True
                except IOError as (errno, strerror):
                    print "I/O error({0}): {1}".format(errno, strerror)
                    time.sleep(0.25)
                    
            dim.close()
                    
            successful = False
            while not successful:
                try:
                    dim.preloadChunkPositions()
                    successful = True
                except IOError as (errno, strerror):
                    print "I/O error({0}): {1}".format(errno, strerror)
                    time.sleep(0.25)
            

print "Chunk Deletion complete. Deleted", chunksProcessed, "chunks (", float(chunksProcessed) / float(totalChunks), "% )"

# save the world
dim.saveInPlace()
endtime = time.time()
print 'worldcleaner took %0.3f s' % ((endtime-starttime))
