# Snieg
Snowrunner save sharing with Discord integration.

## How does it work?
Map progress in coop is saved only by the host in Snowrunner. This script allows you to share the progress to other people. 
When you load the external save file, it overwrites your current map progress, level and unlocks, keeping your money and trucks. This solution enables you to have different people hosting the coop game without losing the progress. After loading the save a new save slot will appear in your game.
When you get the hang of it, exporting and loading saves takes less than a minute.

## Limitations
1. **You have to recover all your vehicles before exporting and loading saves.**
If export the file without retaining your vehicles everyone who loads the save will get access to them on their local save, since ungaraged vehicles are stored in map files, which are fully copied, not merged.
If you load the file without retaining your vehicles you will lose them, since they will be overwritten by the map files that you loaded.
2. Having multiple people play separately using the same save will result is not supported and will result in branching of your save files. You will effectively have to chose which one to load, since you can't merge.
3. When you load the save file it will appear in the exact position as the external save that you loaded (if you load a save from someone who created their save at slot 2, it will be loaded at slot 2 on your computer too).

## Issues
1. Sometimes you'll have to restart your game because save file will refuse to show up for the first time.
2. Sometimes a save will randomly refuse to show up even after restarting the game twice, the exact cause of this issue is unknown and it can happen only for some people. In this case the only 2 possible solutions are:
    - try option 8 (Reload snieg) and 7 (Fix invisible saves), those have some chance of fixing the issue,
    - load backup save using snieg.
3. Sometimes snieg will not be able to resolve your Snowrunner save directory path and will ask you to paste it in the console. Default path of that directory is: `C:\Users\<user_name>\Documents\My Games\SnowRunner`

## Important
1. If you're using Epic Games Launcher:

When you load the save using snieg it will detect that files have changed. When you run the game it will ask you to `[UPLOAD TO CLOUD]` (keep what you have right now) or `[DOWNLOAD TO MACHINE]` (load files from before you used snieg). Chose first option here.

2. Recover all your vehicles before exporting and loading saves.
3. Keep it organized with your friends, if you play separately some of you can miss progress.

## Discord integration
Snieg can send and download files using Discord webhook and a bot. How to set it up is later described in Setup section.
In short, you create a webhook for your channel of choice and then all save files will be sent to that channel.
[example save]

In order to download files from Discord you have to create an app on Discord's developer portal (also described later).

### Requirements
- Python (3.7.9)

### Setup
1. Install requirements
    `python -m pip install  -r requirements.txt`
   
### Discord setup
1. Create a webhook for the channel.
    - Right click on the text channel
    - Integrations, create new webhook
    - Click copy webhook url.
2. Configure the webhook for snieg.
    - Open your snieg folder and then `data/webhooks.json`
    - Replace <webhook_url> with the url that you just copied.
    - You can alternatively change the name of the webhook, it's avatar url and channel invite url (it shows up in snieg after file has been sent successfully, right click on the channel and create invite link, ideally one that doesnt expire).
3. Create discord app. Go to https://discord.com/developers/applications, create new application. Select it, go to Bot and copy the token.
4. Configure the bot for snieg.
    - Open your snieg folder and then `data/bot.json`
    - Replace <bot_token> with the token you just copied.
    - Make sure you have developer mode enabled on Discord. Go to Settings -> Appearance -> Developer Mode and turn it on.
    - Right-click on the text channel that you selected for snieg webhook and copi it's ID, replace 000000000000000000 in `data/bot.json` with that ID.
    - Invite your bot to your discord.
    - Make sure you haven't permitted your bot from viewing messages in that channel.
