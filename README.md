# Snieg
Snowrunner save sharing with Discord integration.

## How does it work?
Map progress in coop is saved only by the host in Snowrunner. This script allows you to share the progress to other people. 
When you load the external save file, it overwrites your current map progress, level and unlocks. This solution enables you to have different people hosting the coop game without losing the progress. After loading the save a new save slot will appear in your game. Everything map-related is saved.

## Limitations
1. You have to recover all your vehicles to the garage before exporting and loading saves.
If export the file without retaining your vehicles everyone who loads the save will get access to them on their local save, since ungaraged vehicles are stored in map files, which are fully copied, not merged.
If you load the file without retaining your vehicles you will lose them, since they will be overwritten by the map files that you loaded.
2. Having multiple people play separately using the same save will result is not supported and will result in branching of your save files. You will effectively have to chose which one to load, since you can't merge.
3. When you load the save file it will appear in the exact position as the external save that you loaded (if you load a save from someone who created their save at slot 2, it will be loaded at slot 2 on your computer too).

## Issues
Sometimes you'll have to restart your game because save file will refuse to show up for the first time. 

## Important
1. If you're using Epic Games Launcher:
When you load the save using snieg it will detect that files have changed. When you run the game it will ask you to [UPLOAD TO CLOUD] (keep what you have right now) or [DOWNLOAD TO MACHINE] (load files from before you used snieg). Chose first option here.
2. Recover all your vehicles before exporting and loading saves.

### Requirements
- Python (3.7.9)

### Setup
