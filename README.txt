WorldCleaner is a tool for reducing the size of your minecraft worlds by deleting chunks that don't have user-placed blocks. It is inspired by minecraft chunk deleter (http://code.google.com/p/minecraft-chunk-deleter/), and is going to be an Anvil-ready version of that program. This is written on top of pymclevel (https://github.com/mcedit/pymclevel).

To use:
- Install numpy and pyyaml, the prerequisites for pymclevel.
- Install pymclevel or simply place it next to worldcleaner.py
- Edit the input parameters (command line params coming soon!):
    dimensionNum: dimension of the world to clean
    worldname: name of the world to open
    chunksToCleanUpAfter: number of chunks to clean memory after, to work around a memory leak in pymclevel. 1024 chunks corresponds to about 288 MB.
    radius: radius around relevant chunks to keep, measured in chunks.
- Run the script
- Wait for a long time (optimization, progress saving and in-progress chunk deletion coming soon!)

Enjoy!
- Chrisknyfe
