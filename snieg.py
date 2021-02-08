import json
import os
import pathlib
from distutils.dir_util import copy_tree
from shutil import copyfile, rmtree, make_archive
from zipfile import ZipFile
from colors import *
from discord.ext import commands
import discord

import aiohttp
import asyncio
from datetime import datetime

# PATHS FOR EXE FILE
import sys
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
elif __file__:
    application_path = os.path.dirname(__file__)

REALPATH = pathlib.Path(__file__).parent.absolute()
os.chdir(REALPATH)


# CONFIG
DEFAULT_CONFIG = {"custom_path": None, "id_counter": 1, "isolate_save": None, "first_run": True, "colors": True}
CONFIG = None
config_path = os.path.join(application_path, 'data', 'config.json')

def load_config():
    global CONFIG
    with open(config_path, 'r', encoding='utf-8') as f:
        CONFIG = json.load(f)

def save_config():
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(CONFIG, f)

def swap_keys(external, local, external_id, local_id, _id=404, mirror=False):
    if not mirror:
        #gamestats
        external[external_id]['SslValue']['gameStat'] = local[local_id]['SslValue']['gameStat']
        
        #garages
        for key, value in external[external_id]['SslValue']['garagesData'].items():
            if key in local[local_id]['SslValue']['garagesData'].keys():
                external[external_id]['SslValue']['garagesData'][key] = local[local_id]['SslValue']['garagesData'][key]
            else:
                default = dict(
                    selectedSlot="garage_interior_slot_1",
                    slotsDatas=dict(
                        garage_interior_slot_1=dict(
                            garageSlotZoneId="garage_interior_slot_1",
                            truckDesc=None
                        ),
                        garage_interior_slot_2=dict(
                            garageSlotZoneId="garage_interior_slot_2",
                            truckDesc=None
                        ),
                        garage_interior_slot_3=dict(
                            garageSlotZoneId="garage_interior_slot_3",
                            truckDesc=None
                        ),
                        garage_interior_slot_4=dict(
                            garageSlotZoneId="garage_interior_slot_4",
                            truckDesc=None
                        ),
                        garage_interior_slot_5=dict(
                            garageSlotZoneId="garage_interior_slot_5",
                            truckDesc=None
                        ),
                        garage_interior_slot_6=dict(
                            garageSlotZoneId="garage_interior_slot_6",
                            truckDesc=None
                        ),
                        
                    )
                )
                external[external_id]['SslValue']['garagesData'][key] = default

        if not local[local_id]['SslValue']['persistentProfileData']:
            external[external_id]['SslValue']['persistentProfileData']["ownedTrucks"] = []
            external[external_id]['SslValue']['persistentProfileData']["newTrucks"] = []
            external[external_id]['SslValue']['persistentProfileData']["addons"] = []
            external[external_id]['SslValue']['persistentProfileData']["money"] = 0
            print(red('No persistent profile data found.'))
        else:
            #copy local
            keys = ['money', "trucksInWarehouse", "newTrucks", "ownedTrucks", "addons"]
            for key in keys:
                try:
                    external[external_id]['SslValue']['persistentProfileData'][key] = local[local_id]['SslValue']['persistentProfileData'][key]
                except:
                    print(red(f'Could not copy {key}'))

            #merge in persistent profile 
            merges = ['unlockedItemNames',]
            for key in merges:
                dct = local[local_id]['SslValue']['persistentProfileData'][key]
                if isinstance(dct, dict):
                    for item_name, local_val in dct.items():
                        try:
                            if local_val and not external[external_id]['SslValue']['persistentProfileData'][key][item_name]:
                                external[external_id]['SslValue']['persistentProfileData'][key][item_name] = local_val
                        except Exception as e:
                            print(red(e))
                            
    external[external_id]['SslValue']['saveId'] = _id
    
    return external

def save_in_dir(d):
    return len([f for f in os.listdir(d) if os.path.isfile(os.path.join(d, f)) and 'CompleteSave' in f]) > 0

def get_save_dirs(save_dir, typ = '' , backup=False):
    unzip(save_dir)
    found_dirs = [(os.path.join(save_dir, d), d) for d in os.listdir(save_dir) if os.path.isdir(os.path.join(save_dir, d)) and (save_in_dir(os.path.join(save_dir, d)) or len(d) >= 32) and not 'backup' in d]
    found_dirs = list(sorted(found_dirs, key=lambda f: pathlib.Path(f[0]).stat().st_mtime, reverse=True))
    
    if typ == 'external':
        name = 'new'
        action = 'use as new save'
    elif typ == 'local':
        name = 'existing'
        action = 'overwrite'
    elif typ == 'export':
        name = 'existing'
        action = 'export'
        
    if not len(found_dirs):
        print(red(f'No {typ} save profile found!'))
        return None
    elif len(found_dirs) > 1:
        t = '\n'.join([f'   {i+1}. {d[1]}' for i, d in enumerate(found_dirs)])
        print(f'Multiple {name} save profiles found:\n\n{white(t)}')
        idx = int(input(f'\nWhich file to {action}?: '))
        save_dir = found_dirs[idx-1]
    else:
        save_dir = found_dirs[0]
    
    if backup:
        illegal_chars = ('<', ':', '"', '/', '\\', '|', '?', '*')
        date_for_file = str(datetime.now().replace(microsecond=0)).replace(' ', '_')
        for illegal_char in illegal_chars:
            date_for_file = date_for_file.replace(illegal_char, '-')
        
        base_backup_path = os.path.join(os.path.dirname(save_dir[0]), 'backups', save_dir[1])
 
        backup_dir = base_backup_path + '_snieg_backup-' + date_for_file
        if os.path.isdir(backup_dir):
            files = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if os.path.isfile(os.path.join(backup_dir, f))]
            dirs = [os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if os.path.isdir(os.path.join(backup_dir, f))]
            for f in files:
                os.remove(f)
            for d in dirs:
                rmtree(d)
        copy_tree(save_dir[0], backup_dir)

    return save_dir

def file_to_copy(fname):
    if 'level' in fname:
        return True
    elif fname in ['achievements.dat',]:
        return True
    return False

def file_to_persist(fname, save_save=False):
    if fname in ['CommonSslSave.dat', 'user_profile.dat', 'user_settings.dat']:
        return True
    elif fname.startswith('CompleteSave') and save_save:
        return True
    return False

def get_last_id(target_dir):
    files = [fname for fname in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, fname)) and 'CompleteSave' in fname]
    ids = []
    for f in files:
        fp = os.path.join(target_dir, f)
        with open(fp, 'r') as savefile:
            try:
                text = savefile.read()
                end_symbol = text[-1]
                local = text
                if end_symbol != '}':
                    local = local[:-1]
                save = json.loads(local)
            except:
                return 0
        ids.append(save[f.split('.')[0]]["SslValue"]['saveId'])
    return max(ids) if ids else 0

# unused, probably has no effect
# def add_common_entry(target_dir, slot):
#     entries = []
    
#     files = [fname for fname in os.listdir(target_dir) if os.path.isfile(os.path.join(target_dir, fname)) and 'CompleteSave' in fname]
    
#     sslfp = os.path.join(target_dir, 'CommonSslSave.dat')
#     with open(sslfp, 'r') as sslfile:
#         text = sslfile.read()
#         end_symbol = text[-1]
#         local = text
#         if end_symbol != '}':
#             local = local[:-1]
#         ssl = json.loads(local)
        
#     ssl['CommonSslSave']["SslValue"]["saveSlotsTransaction"] = []
#     for f in files:
#         fp = os.path.join(target_dir, f)
#         with open(fp, 'r') as savefile:
#             text = savefile.read()
#             end_symbol = text[-1]
#             local = text
#             if end_symbol != '}':
#                 local = local[:-1]
#             save = json.loads(local)
            
#         slot = get_slot_from_fname(f)
#         entry = {
#             "saveId": save[f.split('.')[0]]["SslValue"]['saveId'],
#             "slot": slot,
#             "action": "SaveGame",
#             "saveTime": ssl['CommonSslSave']["SslValue"]['saveTime'] if ssl['CommonSslSave']["SslValue"].get('saveTime') else {"timestamp":"0x00000176a00b4d80"}  
#         }
        
#         ssl['CommonSslSave']["SslValue"]["saveSlotsTransaction"].append(entry)
    
    
#     with open(sslfp, 'w+') as f:
#         f.write(json.dumps(ssl))

def unzip(d):
    files = [os.path.join(d, f) for f in os.listdir(d) if os.path.isfile(os.path.join(d, f)) and f.endswith('.zip') or f.endswith('.rar')]
    for f in files:
        if f.endswith('.zip'):
            with ZipFile(f, 'r') as zip_ref:
                for _f in zip_ref.namelist():
                    zip_ref.extract(_f, d)
            os.remove(f)
        if f.endswith('.rar'):
            print(red(f'Could not unrar {f}, unrar the file manually.'))
            

def copy_files(external_dir, local_dir, save_save=False):
    files = [f for f in os.listdir(external_dir) if os.path.isfile(os.path.join(external_dir, f)) and file_to_copy(f) and not file_to_persist(f, save_save=False)]
    removed = 0
    
    for filename in os.listdir(local_dir):
        if file_to_persist(filename):
            continue
        file_path = os.path.join(local_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                rmtree(file_path)
            removed += 1
        except Exception as e:
            print(red('Failed to delete %s. Reason: %s' % (file_path, e)))
        
    for f in files:
        copyfile(os.path.join(external_dir, f), os.path.join(local_dir, f))
    print(f'Removed {removed} files. Copied {len(files)} files.')

def get_completesave_info(path, name, show_trucks=True):
    info = {}
    with open(path, 'r') as f:
        text = f.read()
        end_symbol = text[-1]
        local = text
        if end_symbol != '}':
            local = local[:-1]
        save_info = json.loads(local)

    key = name.split('.')[0] 
    try:
        info['discoveredObjectives'] = len(save_info[key]['SslValue']['discoveredObjectives'])
    except:
        info['discoveredObjectives'] = 0
        
    try:
        info['viewedUnactivatedObjectives'] = len(save_info[key]['SslValue']['viewedUnactivatedObjectives'])
    except:
        info['viewedUnactivatedObjectives'] = 0
    info['regions'] = len(save_info[key]['SslValue']['visitedLevels'])
    
    if show_trucks:
        try:
            info['ownedTrucks'] = save_info[key]['SslValue']['persistentProfileData']['trucksInWarehouse']
        except:
            info['ownedTrucks'] = []
            
        try:
            info['money'] = save_info[key]['SslValue']['persistentProfileData']['money']
        except:
            info['money'] = 0
        
    return info

def get_slot_from_fname(fname):
    print(fname)
    if '.' in fname:
        fname = fname.split('.')[0]
    idx = fname.replace('CompleteSave', '') or '0'
    return int(idx) + 1

def get_input_completesave(external_dir, msg='??', show_trucks=True):
    _files = [f for f in os.listdir(external_dir) if os.path.isfile(os.path.join(external_dir, f)) and 'CompleteSave' in f]
    if len(_files) > 1:
        files = [None for _ in range(4)]
        for f in _files:
            files[get_slot_from_fname(f)-1] = f
    else:
        files = _files
        
    if len(files) > 1:
        print('Multiple saves found in save profile:')
        texts = []
        for i, f in enumerate(list(files)):
            ppd = save_ppd(os.path.join(external_dir, f), f) if f else None

            if f and ppd:
                saveinfo = get_completesave_info(os.path.join(external_dir, f), f, show_trucks)
                t = f'\n   {i+1}. [Slot {i+1} in game] {f}\n'
                t += f"     - Visited Maps: {saveinfo['regions']}\n"
                t += f"     - Objectives:   {saveinfo['discoveredObjectives']} discovered, {saveinfo['viewedUnactivatedObjectives']} viewed."
                if show_trucks:
                    t += f"\n     - Trucks in warehouse:"
                    for truck_dict in saveinfo['ownedTrucks']:
                        name = truck_dict.get('type', '???') 
                        name = name.replace('_',' ').upper()
                        t += '\n        - ' + name
                    t += f"\n     - Money: {saveinfo['money']}"
            else:
                t = f'\n   {i+1}. [Slot {i+1} in game] Empty.\n'
                files[i] = None
            texts.append(white(t))
            
        print('\n'.join(texts), '\n')
        idx = int(input(msg))
        f = files[idx-1]
        if not f:
            print(red('Unable to clone empty save slot.'))
            return None, None
    elif len(files) == 1:
        f = files[0]
    else:
        print(red('No save file found!'))
        return None, None
    
    return os.path.join(external_dir, f), f


def warn():
    
    print(red('\n   ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! !'))
    print(red('\n   ! ! !  RECOVER ALL VEHICLES TO THE GARAGE ON YOUR MAIN SAVE ! ! !'))
    print(red('\n   ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! !\n'))
    
    print(red('\n   ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! !'))
    print(red('\n   ! ! ! MAKE SURE YOU HAVE AN EXISTING SAVE IN THE SAME SLOT  ! ! !'))
    print(red('\n   ! ! !    AS THE EXTERNAL GAME SAVE THAT YOU WANT TO LOAD    ! ! !'))
    print(red('\n   ! ! !  IF NOT CREATE A NEW GAME ON THE CORRESPONDING SLOT   ! ! !'))
    print(red('\n   ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! !\n'))
    
    
    input(bg_white('Continue... (Press ENTER)', pad=True, style=style.DIM))



def get_local_save_path():
    local_dp = f'C:\\Users\\{os.getlogin()}\\Documents\\My Games\\SnowRunner'
    if not os.path.isdir(local_dp):
        if not CONFIG['custom_path']:
            print(red('Save directory not found, checking OneDrive.'))
            local_dp = f'C:\\Users\\{os.getlogin()}\\OneDrive\\Documents\\My Games\\SnowRunner'
            if not os.path.isdir(local_dp):
                print(red('OneDrive directory not found.'))
                local_dp = input('Paste your snowrunner save directory path here (SnowRunner folder in Documents\\My Games, to paste copy and press right mouse button).\n> ')
                CONFIG['custom_path'] = local_dp
                save_config()
        else:
            print(green('Loaded custom save directory'))


    return os.path.join(local_dp, 'base', 'storage')

def get_fname_from_slotn(n):
    idx = n - 1 if n > 0 else ''
    return f'CompleteSave{idx}.dat'


def remove_empty_saves(path):
    return
    files = [(os.path.join(path,f), f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and 'CompleteSave' in f]
    for f in files:
        if not save_ppd(*f):
            os.remove(f[0])

def load_save(mirror=False):
    warn()
    os.system('cls')
        
    print(yellow('[LOOKING FOR NEW SAVE PROFILES]'))
    external_dir = get_save_dirs(os.path.join(application_path,'saves'), typ = 'external')
    if not external_dir:
        return
    print(green(f'Using external save profile ' + external_dir[0]))
    
    print(yellow(f'\n[CHOOSING NEW SAVE FILE] - {external_dir[1]}'))
    external_dir = external_dir[0]
    external_input_save_path, external_input_save_fname   = get_input_completesave(external_dir, msg='Which external save to load map progress from?: ', show_trucks=False)
    if not external_input_save_path:
        return
    print(green('Loading map progress from ' + external_input_save_path))
    
    print(yellow('\n[LOOKING FOR EXISTING SAVE PROFILES]'))
    local_dp = get_local_save_path()
    
    local_dir = get_save_dirs(local_dp, backup=True, typ = 'local')
    if not local_dir:
        return
    print(green('Using local save profile ' + local_dir[0]))
    
    remove_empty_saves(local_dir[0])
    
    print(yellow(f'\n[CHOOSING LOCAL SAVE FILE] - {local_dir[1]}'))
    
    
    #default_save_fname = get_fname_from_slotn(CONFIG['save_slot'])
    
    
    local_dir = local_dir[0]
    
    save_save = False
    files = [f for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f)) and 'CompleteSave' in f]
    
    if len(files) > 1 and CONFIG['isolate_save'] == None:
        print(f'Remove your previous saves from current save profile?: {green("(your previous saves will remain in backup folder)")}\n')
        print('    1. Yes (default, recommended)')
        print('    2. No')
        x = input('\nOption: ')
        save_save = True if x == '2' else False
        if not save_save:
            print(yellow('Only one save slot will remain in Snowrunner files.', style=style.NORMAL))
        print('')
    elif CONFIG['isolate_save'] != None:
        save_save = CONFIG['isolate_save']

    local_input_save_path, local_input_save_fname   = get_input_completesave(local_dir, msg='Which local save to load your vehicles from?: ', show_trucks=True) #FILE TO LOAD VEHICLES FROM
    if not local_input_save_path:
        return
    
    print(green('Loading vehicles from ' + local_input_save_path))

    local_output_save_path,  local_output_save_fname  = (os.path.join(local_dir, external_input_save_fname), external_input_save_fname)

 
    if os.path.isfile(local_output_save_path):
        with open(local_output_save_path, 'r') as f:
            try:
                text = f.read()
                end_symbol = text[-1]
                ow = text
                if end_symbol != '}':
                    ow = ow[:-1]
                ow = json.loads(ow)
                _id = int(ow[local_output_save_fname.split('.')[0]]['SslValue']['saveId'])
                print(yellow(f'\nFound existing file with id {_id}'))
            except:
                _id = get_next_id()
                save_config()
    else:
        _id = get_next_id()
        save_config()
        
      
    with open(external_input_save_path, 'r') as f:
        text = f.read()
        end_symbol = text[-1]
        external = text
        if end_symbol != '}':
            external = external[:-1]
        external = json.loads(external)
        
  
    with open(local_input_save_path, 'r') as f:
        text = f.read()
        end_symbol = text[-1]
        local = text
        if end_symbol != '}':
            local = local[:-1]
        local = json.loads(local)
        
    external = swap_keys(external, local, external_input_save_fname.split('.')[0], local_input_save_fname.split('.')[0], _id=_id, mirror=mirror)
    
    copy_files(external_dir, local_dir)
    
    with open(local_output_save_path, 'w+') as f:
        f.write(json.dumps(external))
        print(green(f'\nUpdated {local_output_save_path}\n   Using {external_input_save_path}\n    Modified from {local_input_save_path}', style=style.NORMAL))
    
    print(yellow('\n   ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! !'))
    print(yellow('\n   ! ! ! REMEMBER TO RECOVER YOUR VEHICLES TO THE GARAGE BEFORE SHARING SAVED GAME ! ! !'))
    print(yellow('\n   ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! !\n'))
    print(cyan("\n  ? Try restarting the game and epic games launcher if saves don't show up."))
    

def file_to_export(fname):
    if 'level' in fname or fname in ['achievements.dat',]:
        return True

async def send(config, embed, f=None, fname=None):

    for whc in config['webhooks']:
        async with aiohttp.ClientSession() as session:
            s = False
            try:
                webhook = discord.Webhook.from_url(whc['url'], adapter=discord.AsyncWebhookAdapter(session))
                await webhook.send(embed=embed, file=discord.File(f,filename=fname+'.zip'), username=whc['name'],avatar_url=whc.get('avatar_url'))
                if whc.get('channel_invite_url'):
                    print(green(f'File has been sent to {whc.get("channel_invite_url")}'))
            except Exception as e:
                print(red(str(e)))

def get_free_slots(save_path):
    names = []
    for f in os.listdir(save_path):
        if os.path.isfile(os.path.join(save_path, f)) and 'CompleteSave' in f:
            with open(os.path.join(save_path, f), 'r') as sf:
                text = sf.read()
                end_symbol = text[-1]
                local = text
                if end_symbol != '}':
                    local = local[:-1]
                save = json.loads(local)
                ppd = save[f.split('.')[0]]['SslValue']['persistentProfileData']
            if ppd:
                names.append(f.split('.')[0].replace('CompleteSave', ''))
                
    f_idxs = [int(idx or '0') for idx in names]
    fs = [x+1 for x in range(4) if x not in f_idxs]
    return fs
    
def save_ppd(path, f):
    with open(path, 'r') as sf:
        text = sf.read()
        end_symbol = text[-1]
        local = text
        if end_symbol != '}':
            local = local[:-1]
        save = json.loads(local)
    return save[f.split('.')[0]]['SslValue']['persistentProfileData']

def get_next_id():
    CONFIG['id_counter'] += 1
    return CONFIG['id_counter']

def set_save_to_slot(save_path, save_fname, slot_n=4, clone=False):
    return save_path, save_fname
    new_key = f'CompleteSave{slot_n-1 if slot_n > 1 else ""}'
    new_fname = new_key + '.dat'
    if save_fname == new_key:
        return save_path, save_fname
    
    if not clone:
        print(f'Save will be moved to slot {slot_n}.')
    
    new_path = save_path.replace(save_fname, new_fname)
    
    with open(save_path, 'r') as f:
        text = f.read()
        end_symbol = text[-1]
        local = text
        if end_symbol != '}':
            local = text[:-1]
        save_file = json.loads(local)
        
    save_file[new_key] = save_file.pop(save_fname.split(".")[0])
    save_file[new_key]['SslValue']['saveId'] = get_next_id()
    save_config()
    
    while os.path.isfile(new_path) and save_ppd(new_path, new_fname):
        print(red(f'There is an existing save on slot {slot_n}:'))
        print(white(f'     1. Remove save at slot {slot_n} (default)'))
        print(white('     2. Chose different slot'))
        act = input('Choose action: ') or '1'
        if act == '1':
            os.remove(new_path)
        elif act == '2':
            fs = get_free_slots(os.path.dirname(save_path))
            slot_n = int(input(f'Which slot to clone the save to (free slot numbers: {fs}): '))
            new_key = f'CompleteSave{slot_n-1 if slot_n > 1 else ""}'
            new_fname = new_key + '.dat'
            new_path = save_path.replace(save_fname, new_fname)
            
            
            
    with open(new_path, 'w+') as f:
        f.write(json.dumps(save_file))
        
    if not clone:
        os.remove(save_path)
    
    return new_path, new_fname

def clone_save():
    print(red('\n   ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! !'))
    print(red('\n   ! ! ! RECOVER ALL VEHICLES TO THE GARAGE BEFORE CLONING THE SAVE FILE ! ! !'))
    print(red('\n   ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! !\n'))
    
    input('\n' + bg_white('Continue... (Press ENTER)', pad=True, style=style.DIM))
    
    os.system('cls')
    
    print(yellow('[LOOKING FOR EXISTING SAVE PROFILES]'))
    local_dir = get_save_dirs(get_local_save_path(), backup=False, typ = 'export')
    print(green('Using local save profile ' + local_dir[0]))
    if not local_dir:
        return
    
    remove_empty_saves(local_dir[0])
    
    print(yellow(f'\n[CHOOSING LOCAL SAVE FILE] - {local_dir[1]}'))
    local_input_save_path, local_input_save_fname   = get_input_completesave(local_dir[0], msg='Which local save to include in export file?: ', show_trucks=True) #FILE TO LOAD VEHICLES FROM
    if not local_input_save_path:
        return
    
    print(yellow(f'\n[EDITING SAVE POSITION] - {local_input_save_fname}'))
    fs = get_free_slots(local_dir[0])
    slt = int(input(f'Which slot to clone the save to (free slot numbers: {fs}): '))
    while slt < 1 or slt > 4:
        slt = int(input(f'Which slot to clone the save to (free slot numbers: {fs}): '))
        
    new_local_input_save_path, new_local_input_save_fname = set_save_to_slot(local_input_save_path, local_input_save_fname, slt, clone=True)
    if not new_local_input_save_fname:
        return
    
    print(green(f'Save cloned to slot {slt}.'))


def export():
    print(red('\n   ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! !'))
    print(red('\n   ! ! ! RECOVER ALL VEHICLES TO THE GARAGE BEFORE EXPORTING THE SAVE FILE ! ! !'))
    print(red('\n   ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! ! !\n'))
    
    input('\n' + bg_white('Continue... (Press ENTER)', pad=True, style=style.DIM))
    
    os.system('cls')
    
    print(yellow('[LOOKING FOR EXISTING SAVE PROFILES]'))
    local_dir = get_save_dirs(get_local_save_path(), backup=False, typ = 'export')
    print(green('Using local save profile ' + local_dir[0]))
    if not local_dir:
        return
    
    remove_empty_saves(local_dir[0])
    
    print(yellow(f'\n[CHOOSING LOCAL SAVE FILE] - {local_dir[1]}'))
    local_input_save_path, local_input_save_fname   = get_input_completesave(local_dir[0], msg='Which local save to include in export file?: ', show_trucks=True) #FILE TO LOAD VEHICLES FROM
    if not local_input_save_path:
        return
    

    illegal_chars = ('<', ':', '"', '/', '\\', '|', '?', '*')
    
    #create new dir
    save_done = False
    is_default = False
    while not save_done:
        save_name = input('File name (optional, leave blank for default name): ')
        if not save_name:
            save_name = local_dir[1]
            is_default = True
        
        if any(char in save_name for char in illegal_chars):
            print(red(f"File name cannot contain following characters {' '.join(illegal_chars)}."))
            continue
        break
    
    local_dir = local_dir[0]
    
    print(green(f'Created save file {save_name}'))
    
    d = os.path.join(application_path, 'export', save_name)
    
    date_for_file = str(datetime.now().replace(microsecond=0)).replace(' ', '_')
    for illegal_char in illegal_chars:
        date_for_file = date_for_file.replace(illegal_char, '-')
    
    d_zip = os.path.join(application_path, 'export', save_name if not is_default else  f'{date_for_file}_{save_name}')
    
    if os.path.exists(d):
        rmtree(d)
    inner_d = os.path.join(d, save_name)
    os.makedirs(inner_d)
    
    #copy dir contents
    files = [f for f in os.listdir(local_dir) if os.path.isfile(os.path.join(local_dir, f)) and file_to_export(f) or f == local_input_save_fname]
    

    for f in files:
        print(green(f' > Copying {f}', style=style.NORMAL))
        copyfile(os.path.join(local_dir, f), os.path.join(inner_d, f))
        
    
    
    make_archive(d_zip, 'zip', d, save_name)
            
        
    rmtree(d)
    print(green(f'Created export file {d_zip+".zip"}'))

    print(yellow('\n[SEND SAVE]'))
    print('\n1. Yes (default)\n2. No')
    x = input('\nSend exported save to Discord?: ') 

    if x == '1' or not x:
        webhook_configs = os.path.join(application_path, 'data', 'webhooks.json')
        with open(webhook_configs, 'r', encoding='utf-8') as f:
            whc = json.load(f)
        author = input('Your name (optional): ')
        description = input('Description (optional): ')
        if description:
            description = description.capitalize()
    
        embed = discord.Embed(title=author, description=description, color=discord.Colour.from_rgb(3, 175, 255))
        embed.set_author(name=datetime.now().replace(microsecond=0), icon_url='https://www.freeiconspng.com/uploads/blue-save-disk-icon-0.png')
        embed.set_footer(text=f"File: {save_name.replace(' ', '_')}.zip")
        
        loop = asyncio.get_event_loop()
        loop.run_until_complete(send(whc, embed, f=d_zip+'.zip', fname=save_name))

    
def copy_backup_files(external_dir, local_dir):
    files = [f for f in os.listdir(external_dir) if os.path.isfile(os.path.join(external_dir, f))]
    removed = 0
    
    for filename in os.listdir(local_dir):
        file_path = os.path.join(local_dir, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                rmtree(file_path)
            removed += 1
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))
        
    for f in files:
        copyfile(os.path.join(external_dir, f), os.path.join(local_dir, f))
    print(f'\nRemoved {removed} files. Copied {len(files)} files.\n')

def get_backup_dirs(save_dir):
    found_dirs = [(os.path.join(save_dir, d), d) for d in os.listdir(save_dir) if os.path.isdir(os.path.join(save_dir, d)) and 'snieg_backup' in d]
    found_dirs = list(sorted([fname for fname in found_dirs], key=lambda f: pathlib.Path(f[0]).stat().st_mtime, reverse=True))
        
    if not len(found_dirs):
        print(f'No backups found!')
        return None
    elif len(found_dirs) > 1:
        t = '\n'.join([f'   {i+1}. {d[1].split("snieg_backup")[-1][1:].replace("_", " ").replace("-", ".")}' for i, d in enumerate(found_dirs)])
        print(f'Multiple backups found:\n\n{white(t)}')
        idx = int(input(f'\nWhich backup to restore? (default - 1): ') or 1)
        save_dir = found_dirs[idx-1]
    else:
        save_dir = found_dirs[0]
        
    return save_dir

def backup():
    print(yellow('[LOOKING FOR BACKUPS]'))
    #load backup file
    local_dir = get_local_save_path()
    
    backup_dirs_path = os.path.join(local_dir, 'backups')
    if not os.path.isdir(backup_dirs_path):
        os.makedirs(backup_dirs_path)
    
    
    
    backup_dir_path, backup_dir_name = get_backup_dirs(backup_dirs_path)
    print(green(f'Using backup {backup_dir_path}'))
    
    #backup file
    print(yellow('\n[LOOKING FOR EXISTING SAVES]'))
    save_dir_path, save_dir_name = get_save_dirs(local_dir, typ='local')
    print(green(f'Loading backup to {backup_dir_path}'))
   
              
    input(f'\nApply backup {cyan(backup_dir_name)}? (Press Enter)')
    copy_backup_files(backup_dir_path, save_dir_path)

    remove_empty_saves(save_dir_path)

async def download_attachment(attachment, clear_saves):
    filename = attachment.filename
    if filename.endswith('.zip'):
        saves_folder = os.path.join(application_path, 'saves')
        if clear_saves:
            files = [os.path.join(saves_folder, f) for f in os.listdir(saves_folder) if os.path.isfile(os.path.join(saves_folder, f))]
            dirs = [os.path.join(saves_folder, f) for f in os.listdir(saves_folder) if os.path.isdir(os.path.join(saves_folder, f))]
            for f in files:
                os.remove(f)
            for d in dirs:
                rmtree(d)
            total_len = len(files) + len(dirs)
        await attachment.save(os.path.join(application_path, 'saves', filename))
        print(green(f'Downloaded {filename}.'))


def download_recent(browse=False):
    print(yellow('[STARTING PROCESS]'))
    bot = commands.Bot(command_prefix=".sng ")
    with open(os.path.join(application_path, 'data', 'bot.json'), 'r', encoding='utf-8') as f:
        info = json.load(f)
    print(green('Loaded info.'))   
    
    print('\nClear old save files from /saves?\n')
    print(white('   1. Yes (default)\n   2. No'))
    opt = input('\nOption: ') or '1'
    clear_saves = True if opt == '1' else False
    if clear_saves:
        print('Old saves will be removed.')
    
    print(yellow('\n[CONNECTING DISCORD DOWNLOADER]'))
    
    @bot.event
    async def on_ready():
        print(green('Downloader connected.'))
        print(yellow('\n[LOOKING FOR LAST SAVE ON DISCORD]'))
        channel_id = info['channel_id']
        channel = bot.get_channel(channel_id)
        attachments = []
        
        async for message in channel.history(limit=None):
            if message.attachments:
                for _attachment in message.attachments:
                    attachments.append(
                        {
                            'attachment' : _attachment,
                            'embed' : message.embeds[0] if message.embeds else None,
                            'timestamp' : message.created_at
                        })     
            if len(attachments) and browse == False:
                print(green('Last save file located.'))
                break
    
        
        if not len(attachments):
            print(red(f'No save files found in #{channel.name}.'))
        else:
            try:
                if browse == False:
                    attachment = attachments[0]['attachment']
                else:
                
                    for i, attachment in enumerate(reversed(attachments)):
                        e = attachment['embed']
                        t = f'{len(attachments) - i}. [{cyan(str(attachment["timestamp"].replace(microsecond=0)))}]'
                        t += f" {white(e.title)}" if e.title else ""
                        t += " -"
                        t += f" {e.description}" if e.description else ""
                        t += f" ({attachment['attachment'].filename})"
                        t += '\n'
                        print(t)
                    idx = int(input('Which save to download (1 - default): ') or '1') 
                    attachment = attachments[idx- 1]['attachment']
                print()
                print(yellow('[DOWNLOADING ATTACHMENT]'))

                await download_attachment(attachment, clear_saves)
                await bot.close()
            except Exception as e:
                print(red('Error: ' + str(e)))
                input()
                return
        
            print('\nChose action:\n')
            print('    1. Load save (default)')
            print('    2. Mirror save')
            print('    3. Cancel')
            act = int(input('\nAction: ') or '1')
            if act in (1,2):
                load_save(mirror = act == 2)
        
    try:
        bot.run(info['token'],reconnect=True)
    except Exception as e:
        msg = red("Error: " + str(e))
        sug = red("Please restart snieg.")
        print(msg + '\n' + sug)
        input()

def change_save_slot():
    print(yellow('Saves on default slot will be overwritten.'))
    x = int(input(f'Default save slot: '))
    while x < 1 and x > 4:
        x = int(input(f'Default save slot: '))
    CONFIG['save_slot'] = x
    save_config()

def toggle_isolate():
    CONFIG['isolate_save'] = not CONFIG['isolate_save']
    save_config()

def fix_saves():
    local_dp = get_local_save_path()
    local_dir = get_save_dirs(local_dp, backup=True, typ = 'local')
    files = [f for f in os.listdir(local_dir[0]) if os.path.isfile(os.path.join(local_dir[0], f)) and 'CompleteSave' in f]
    print(files)
    for f in files:
        fp = os.path.join(local_dir[0], f)
        with open(fp, 'r') as savefile:
            text = savefile.read()
            end_symbol = text[-1]
            local = text
            if end_symbol != '}':
                local = local[:-1]
            save = json.loads(local)
            
        save[f.split('.')[0]]["SslValue"]['saveId'] = get_next_id()
        
        with open(fp, 'w') as f:
            f.write(json.dumps(save))
        
        save_config()
        

def set_colors():
    toggle_colorize(CONFIG['colors'])

def first_run():
    global CONFIG
    print(cyan('[INITIAL RUN]'))
    l = get_local_save_path()
    local_dir = get_save_dirs(l, typ = 'local')
    d = dict(DEFAULT_CONFIG)
    d['colors'] = CONFIG['colors']
    CONFIG = d
    CONFIG['id_counter'] = get_last_id(local_dir[0])
    set_colors()
    CONFIG['first_run'] = False
    save_config()
    print(green('Config created.'))
    



def tog_colors():
    CONFIG['colors'] = not CONFIG['colors']
    toggle_colorize(CONFIG['colors'])
    save_config()
    
if __name__ == '__main__':
    os.system('color')
    load_config()
    set_colors()
    fix_highlight = white
    if CONFIG['first_run']:
        first_run()
        
    while True:
        
        try:
            os.system('cls')
            print(yellow('\n\n[SNIEG]\n'))
            print(white('   1. Download last save'))
            print(white('   2. Export save'))
            print(white('   3. Load save'))
            print(white('   4. Download save'))
            print(white('   5. Mirror save'))  
            print(white('   6. Load backup save'))
            print('')
            print(fix_highlight(f'   7. Fix invisible saves', style=style.DIM if fix_highlight == white else style.BRIGHT))
            print(white(f'   8. Reload snieg', style=style.DIM))
            print(f'   9. Isolate save: {green("Yes") if CONFIG["isolate_save"] else red("No")}')
            print(f'   0. Console colors: {green("Yes") if get_colorize() else red("No")}')
            fix_highlight = white
            
            if CONFIG['custom_path']:
                print(white(f'  Custom SnowRunner folder path: {CONFIG["custom_path"]}', style=style.DIM))
            x = input('\nChoose action: ')
            
            if x in ('1', '2', '3', '4', '5', '6'):
                os.system('cls')
            
            if x == '3':
                load_save()
            elif x == '1':
                try:
                    download_recent() 
                except RuntimeError as e:
                    print(red("Error: " + str(e)))
            elif x == '2':
                try:
                    export()
                except RuntimeError as e:
                    print(red("Error: " + str(e)))
            elif x == '4':
                download_recent(browse=True)
            elif x == '5':
                load_save(mirror=True)
            elif x == '6':
                backup()
            elif x == '7':
                fix_saves()
                fix_highlight = green
            elif x == '8':
                first_run()
                input(bg_white('Finish action... (Press ENTER)', pad=True, style=style.DIM))
            elif x == '9':
                toggle_isolate()
            elif x == '0':
                tog_colors()
            if x in ('1', '2', '3', '4', '5'):
                print('')
                input(bg_white('Finish action... (Press ENTER)', pad=True, style=style.DIM))
            save_config()
        except KeyboardInterrupt:
            input(red('\nStopped. (Press ENTER)'))
            break
        #except Exception as e:
            #input(red(f'\nError: {str(e)}'))

