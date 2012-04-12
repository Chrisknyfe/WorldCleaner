#!python
# requires numpy
# requires pyyaml

import os, sys, time
from optparse import OptionParser



######## CLI
parser = OptionParser(usage="usage: %prog [options] worldfolder")
parser.add_option("-d", "--dimension", dest="dimensionNum", default=0,
                  help="Dimension NUMBER of the world to clean", metavar="NUMBER")
parser.add_option("-r", "--radius", dest="radius", default=0,
                  help="NUMBER of chunks around relevant chunks to keep", metavar="NUMBER")
parser.add_option("-t", "--world-type", dest="worldtype", default="NORMAL",
                  help="TYPE of world to scan. Choices are NORMAL, FLAT, NETHER, END, SPACE, SKYLANDS, and CUSTOM. ", metavar="TYPE")
parser.add_option("--flat-height", dest="flatworldHeight", default=4,
                  help="HEIGHT of the superflat generator's terrain (default 4)", metavar="HEIGHT")
parser.add_option("-c", "--cleanup-interval", dest="chunksToCleanUpAfter", default=4096,
                  help="NUMBER of chunks to clean up after (to save memory.) 1024 chunks ~= 288 MB.", metavar="NUMBER")
parser.add_option("--reporting-interval", dest="chunksToReportAfter", default=256,
                  help="NUMBER of chunks to report progress after.", metavar="NUMBER")
parser.add_option("-q", "--quiet", action="store_true", dest="quiet",
                  help="Silence progress messages. Invalidates the -v or --verbose flags.")
parser.add_option("-v", "--verbose", action="store_true", dest="verbose",
                  help="Adds more debug messages.")

def usageexit( message ):
    print message
    parser.print_help()
    exit(1)
                  
(options, args) = parser.parse_args()

if len(args) != 1:
    usageexit( "Please only specify one argument, the world name." )
    
if options.quiet: options.verbose = False
options.chunksToCleanUpAfter = int(options.chunksToCleanUpAfter)
options.chunksToReportAfter = int(options.chunksToReportAfter)
options.flatworldHeight = int(options.flatworldHeight)

if not options.quiet: print "-- World Cleaner -- by Chrisknyfe"

import pymclevel
######## Configuration

# Name of the world to open
worldname = args[0]
world = pymclevel.fromFile(worldname)
dim = world.getDimension(options.dimensionNum)
mats = world.materials

# Level below which abandoned mineshafts will generate
mineshaftHeight = 64

# Level of maximum chunk generator height
chunkgenHeight = 128

# Chunk width / length. 
chunksidelength = 16

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

#NOTE: HEIGHTMAP IS ORDERED Z, X. BLOCKS ORDERED X, Z, Y.

# For survival worlds. Villages and strongholds will be kept, mineshafts will not be.
def isChunkRelevantNoMineshafts ( chunk ):
    # keep anything above chunk generator's max height
    for height in chunk.HeightMap.flat:
        if height > chunkgenHeight:
            return True
    # keep relevant blocks above mineshaft height (including torches, wood, etc.)
    # only go up to the column height
    for x in xrange(chunksidelength):
        for z in xrange(chunksidelength):
            for voxel in chunk.Blocks[ x, z, mineshaftHeight:chunk.HeightMap[z,x] ]:
                if voxel in relevantBlocksIncludingMineshafts: 
                    return True
    # ignore mineshafts below a certain level
    for voxel in chunk.Blocks[ :, :, 0:mineshaftHeight ].flat:
        if voxel in relevantBlocksSurvival:
            return True
    return False

# For superflat worlds.     
def isChunkRelevantSuperflat ( chunk ):
    # keep anything above chunk generator's max height
    for height in chunk.HeightMap.flat:
        if height > options.flatworldHeight:
            return True
    # check for relevant blocks below the generator's height
    for voxel in chunk.Blocks[ :, :, 0:options.flatworldHeight ].flat:
        if voxel not in flatworldBlocks: 
            return True
    return False
    
# For skylands.     
def isChunkRelevantSkylands ( chunk ):
    # keep anything above chunk generator's max height
    for height in chunk.HeightMap.flat:
        if height > chunkgenHeight:
            return True
    # iterate through columns, only going up to the column height.
    for x in xrange(chunksidelength):
        for z in xrange(chunksidelength):
            for voxel in chunk.Blocks[ x, z, 0:chunk.HeightMap[z,x] ]:
                if voxel in relevantBlocksIncludingMineshafts: 
                    return True
    return False

# For empty space worlds
def isChunkRelevantSpaceworld ( chunk ):
    for height in chunk.HeightMap.flat:
        if height != 0:
            return True
    return False
    
# For the Nether
def isChunkRelevantNether ( chunk ):
    raise NotImplementedError("Nether cleaning has not been implemented yet!");
    
# For a custom terrain generator. Insert your own code here!
def isChunkRelevantCustom ( chunk ):
    raise NotImplementedError("Implement your own custom terrain generator!");
    
# We have to change our relevance function based on our world type
isChunkRelevant = None
options.worldtype = options.worldtype.lower()

if options.worldtype == "normal":
    isChunkRelevant = isChunkRelevantNoMineshafts
elif options.worldtype == "flat":
    isChunkRelevant = isChunkRelevantSuperflat
elif options.worldtype == "nether":
    isChunkRelevant = isChunkRelevantNether
elif options.worldtype == "end" or options.worldtype == "space":
    isChunkRelevant = isChunkRelevantSpaceworld
elif options.worldtype == "skylands":
    isChunkRelevant = isChunkRelevantSkylands
elif options.worldtype == "custom":
    isChunkRelevant = isChunkRelevantCustom
else:
    usageexit ("World type %s not supported!" % (options.worldtype) )
    

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
    
if not options.quiet:
    print "-------------------"
    print "World:", worldname
    print "World Type:", options.worldtype
    if options.worldtype == "flat":
        print "Superflat Height:", options.flatworldHeight
    print "Dimension:", options.dimensionNum
    print "Radius:", options.radius
    print "Chunks to clean up after:", options.chunksToCleanUpAfter
    print "-------------------"
    
# determine which chunks are relevant
chunkRelevance = {}
chunksProcessed = 0

if options.verbose: print "Determining number of chunks in dimension..."
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

if options.verbose: print totalChunks, "chunks to process."
if not options.quiet: print "Determining chunk relevance..."

starttime = time.time()
for pos in allChunks:
    
    # only process the chunk if we haven't looked at it.
    if pos not in chunkRelevance:
        chunk = dim.getChunk( pos[0], pos[1] );
        chunkRelevance[pos] = isChunkRelevant( chunk )        
    else:
        print pos, "was in chunkRelevance."
    
    # Status report, griff!
    if not options.quiet and chunksProcessed % options.chunksToReportAfter == 0:
        elapsed  = time.time() - starttime
        percent = 100 * float(chunksProcessed) / float(totalChunks)
        predicted = (elapsed) * float(totalChunks) / float( max(chunksProcessed, 1) )
        remaining = predicted - elapsed
        if options.verbose:
            print '%.2f%% chunks processed (%d chunks); %ds elapsed, %ds remaining (%d predicted)' % ( percent, chunksProcessed, elapsed , remaining, predicted )
        else:
            print '%.2f%% chunks processed' % ( percent )
    
    chunksProcessed += 1
    
    # Clean the dimension of unused memory
    assert( not chunk.dirty )
    chunk.unload() 
    assert( not chunk.isLoaded() )
    if chunksProcessed % options.chunksToCleanUpAfter == 0:
        if options.verbose: print "Cleaning memory..."
        dim.close()
        dim.preloadChunkPositions()
     
curtime = time.time()
if options.verbose: print "Chunk relevance took", str( curtime - starttimeChunkRelevance ), "s."
if options.verbose: print "Chunk relevance complete. Processed", chunksProcessed, "chunks."

chunksProcessed = 0
# delete irrelevant chunks
if not options.quiet: print "Deleting chunks..."
for pos, relevant in chunkRelevance.items():
    if not relevant:
        # are there any relevant chunks in the radius?
        radiusRelevant = False
        for x in xrange( pos[0] - options.radius, pos[0] + options.radius + 1 ):
            for z in xrange( pos[1] - options.radius, pos[1] + options.radius + 1):
                if (x,z) in chunkRelevance:
                    if chunkRelevance[(x,z)] == True:
                        radiusRelevant = True
        
        #print "Deleting chunk at", pos
        if not radiusRelevant:
            deleteChunk( pos[0], pos[1] )
            chunksProcessed += 1
        
            # status report
            if not options.quiet and chunksProcessed % options.chunksToReportAfter == 0:
                elapsed  = time.time() - starttime
                percent = 100 * float(chunksProcessed) / float(totalChunks)
                if options.verbose:
                    print '%.2f%% chunks deleted (%d chunks); %ds elapsed' % ( percent, chunksProcessed, elapsed )
                else:
                    print '%.2f%% chunks deleted' % ( percent )
                    

            # Clean the dimension of unused memory
            if chunksProcessed % options.chunksToCleanUpAfter == 0:
                if options.verbose: print "Cleaning memory..."
                saveDim()        
                dim.close() 
                preloadChunkPositions()

if not options.quiet: print "Chunk Deletion complete."
if options.verbose: print "Deleted", chunksProcessed, "chunks (", 100 * float(chunksProcessed) / float(totalChunks), "% )"

# you saved the world!
saveDim()
endtime = time.time()
print "worldcleaner took %ds" % (endtime-starttime)
