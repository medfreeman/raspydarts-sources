#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
awesome electronic darts' game
"""

################
# Import pyDarts internal classes and load essentials
################

import sys
import datetime
from time import sleep
import os, os.path
from copy import deepcopy
import random
from subprocess import Popen

from threading import Event

try:
    from include import cconfig
    from include import clogs
    from include import cevent
    from include import cfiles

    # Starts logger system, it will filter on a config basis
    logs = clogs.Logs()
    # Load config file
    Config = cconfig.Config(logs)
    # Check local config file existance and create if necessary
    Config.check_config_file()
    # Read config file for main configuration and store it in object data storage
    Config.read_file("SectionGlobals")
    # Read hidden default values
    Config.read_file("SectionAdvanced")
    # Read Config file for keys combination : rpi send a key=>it correspond to a hit
    ConfigKeys = Config.read_file("SectionKeys")
    # Read Config file for rpi configuration
    Config_rpi = Config.read_file("Raspberry")
    # Read Config file for rpi Dart Board Pins configuration
    config_leds = Config.read_file("Raspberry_Leds")
    # Read Config file for LED Target configuration
    config_target_leds = Config.read_file("LEDTarget")
    # Read Config file for Favorites
    config_favorites = Config.read_file("Favorites", none='')
    # Read Config file for events
    config_events = Config.read_file("Events")
    # Read Config file for global options
    config_globals = Config.read_file("SectionGlobals")
    # Read Config file for advanced
    config_advanced = Config.read_file("SectionAdvanced")
    # Read inputs
    config_input = Config.read_file("Raspberry_BoardPinsIns")
    # Read outputs
    config_output = Config.read_file("Raspberry_BoardPinsOuts")
    # Read Config file for camera configuration
    config_camera = Config.read_file("Camera")

    ####
    # LOAD colorset
    ####
    colorset_theme = config_globals['colorset']
    # For random files
    File = cfiles.Cfile(Config, logs, theme=colorset_theme)
    logs.info(f"Theme dir is {File.theme_dir}")
    logs.info(f"Personnal dir is {Config.user_dir}")
    logs.info(f"Root dir is {Config.root_dir}")
    # Colorset
    config_colorset = Config.get_colorset(Config.user_dir, colorset_theme)
    # Value for segment color exist ?
    colors_values_for_segments = Config.get_values_segment_colors(config_colorset)
    # Shine little dart
    bg_colors_sending = ""
    if colors_values_for_segments:
        bg_colors_sending = "_".join(colors_values_for_segments)
    else:
        bg_colors_sending = ",".join(color for color in [Config.get_value('SectionAdvanced', 'target-bgcolor1'),
                                                         Config.get_value('SectionAdvanced', 'target-bgcolor2'),
                                                         Config.get_value('SectionAdvanced', 'target-bgcolor3')])
    ####

    # Games' options
    for game in config_advanced['game-options-list'].split(','):
        Config.read_file(f"game-{game.replace(' ', '_')}")

    # Update logs system with loglevel set in config
    logs.set_level(Config.get_value('SectionGlobals', 'debuglevel', 0))

    # dispatcher dispatcher
    subsribers = []
    if config_leds['PIN_STRIPLED'] in ('10', '12', '18', '21'):
        subsribers.append('StripLeds')
    if config_leds['PIN_TARGETLED'] in ('10', '12', '18', '21'):
        subsribers.append('TargetLeds')
    if Config.get_value('SectionAdvanced', 'use-dmd'):
        subsribers.append('Dmd')
    if Config.get_value('SectionAdvanced', 'use-matrix'):
        subsribers.append('Matrix')
    if Config.get_value('SectionAdvanced', 'use-other') or Config.get_value('SectionAdvanced', 'use-hue'):
        subsribers.append('Other')

    mqtt_broker = Config.get_value('SectionAdvanced', 'mqtt-broker')
    logs.debug(f"use-dmd option is set to : {Config.get_value('SectionAdvanced', 'use-dmd')}")
    logs.debug(f"use-matrix option is set to : {Config.get_value('SectionAdvanced', 'use-matrix')}")
    logs.debug(f"use-other option is set to : {Config.get_value('SectionAdvanced', 'use-other')}")
    logs.debug(f"mqtt-broker option is set to : {Config.get_value('SectionAdvanced', 'mqtt-broker')}")

    dispatcher = cevent.Event(logs, config_events, subscribers=subsribers, broker=mqtt_broker)

    # For old versions +> write new config file
    logs.debug(f"target segment colors option is set to : {bg_colors_sending}")
    logs.debug(f"target-bgbrightness option is set to : {Config.get_value('SectionAdvanced', 'target-bgbrightness')}")

except Exception as exception:
    print("[FATAL] Unable to load internal first level dependancies or to create basic instances. Your download seems corrupted. Please download raspydarts again.")
    print(f"[FATAL] Error was {exception}")
    exit(1)

#################
# Start Leds servers
#################

if Config.file_exists and config_leds['PIN_STRIPLED'] in ('10', '12', '18', '21'):
    logs.debug("Starting Strip Leds Server")
    strip_log = open('logs/StripLeds.log', "w", 1)
    cmd = ['sudo', 'python3', 'addons/StripLeds_Server.py'
            , f'-host={mqtt_broker}'
            , '9'
            , f"{dispatcher.strip_topic}"
            , f"{config_leds['PIN_STRIPLED']}"
            , f"{config_leds['NBR_STRIPLED']}"
            , f"{config_leds['BRI_STRIPLED']}"]
    p_strip = Popen(cmd, stdout=strip_log)
    dispatcher.strip_leds = True
    logs.debug(f"Launched {' '.join(cmd)}")
    sleep(0.5)
else:
    dispatcher.strip_leds = False
    p_strip = None

if Config.file_exists and config_leds['PIN_TARGETLED'] in ('10' , '12', '18', '21'):
    logs.debug("Starting Target Leds Server")
    logs.debug(f"Using this configuration : {config_target_leds}")
    target_log = open('logs/TargetLeds.log', "w", 1)
    cmd = ['sudo', 'python3', '/pydarts/addons/TargetLeds_Server.py'
            , f'-host={mqtt_broker}'
            , f'-bgcolors={bg_colors_sending}'
            , f"-bgbrightness={Config.get_value('SectionAdvanced', 'target-bgbrightness')}"
            , '10'
            , f'{dispatcher.target_topic}'
            , f'{config_target_leds}'
            , f"{config_leds['PIN_TARGETLED']}"
            , f"{config_leds['BRI_TARGETLED']}"]
    p_target = Popen(cmd, stdout=target_log)
    dispatcher.target_leds = True
    logs.debug(f"Launched {' '.join(cmd)}")
    sleep(0.5)
else:
    dispatcher.target_leds = False
    p_target = None

if Config.file_exists and Config.get_value('SectionAdvanced', 'use-hue'):
    logs.debug("Starting Hue Server")
    hue_log = open('logs/Hue.log', "w", 1)
    cmd = ['python3', '/pydarts/addons/Hue_Server.py'
            , f'-host={mqtt_broker}'
            , f'{dispatcher.other_topic}']
    p_hue = Popen(cmd, stdout=hue_log)
    dispatcher.other = True
    logs.debug(f"Launched {' '.join(cmd)}")
elif Config.get_value('SectionAdvanced', 'use-other'):
    dispatcher.other = True
else:
    dispatcher.other = False


logs.debug(f"dispatcher.strip_leds is set to {dispatcher.strip_leds}")
logs.debug(f"dispatcher.target_leds is set to {dispatcher.target_leds}")
logs.debug(f"subsribers is set to {subsribers}")

#################
# Welcome
#################
print("############### Welcome to RaspyDarts ########################")
print("#      A Free, Open-Source and Open-Hardware Darts Game      #")
print("#             Please check the website to know more          #")
print("#               {}               #".format(Config.officialwebsite))
print("#                     or check the Wiki                      #")
print("#         {}         #".format(Config.wiki))
print("#            or use --help for available options             #")
print("##############################################################")

########################
# Create various instances of second layer internal classes
########################
# from include import CBluetooth
from include import craspberry
from include import cdmd
from include import cvideos
from include import cimages
from include import cupdate
#from include import cplayer
from include import cscreen
from include import clocale
from include import cclient
from include import cscores
from include import ccamera

# Create locale instance
Lang = clocale.Locale(logs, Config)
# Manage display
font = Config.get_value('SectionGlobals', 'font', False)  # Local players
releasedartstime = int(Config.get_value('SectionGlobals', 'releasedartstime'))# Relase darts delay
wait_event_time = int(Config.get_value('SectionGlobals', 'waitevent_time', False))
t_event = Event()

# Manage raspberry gpio
try:
    rpi = craspberry.Craspberry(logs, Config, config_target_leds, dispatcher, t_event=t_event)
    rpi_error = None
except Exception as exception:
    print(f"[ERROR] {exception}")

    rpi_error = exception
    try:
        rpi = craspberry.Craspberry(logs, Config, config_target_leds, dispatcher, t_event=t_event)
    except Exception as exception:
        print(f"[ERROR] {exception}")

        rpi_error = exception

dispatcher.add_rpi(rpi)

# Manage Raspydarts dmd
dmd = cdmd.Cdmd(logs, dispatcher, File)

# Manage Raspydarts Video Player
video_level = int(Config.get_value('SectionGlobals', 'videos'))
volume = int(Config.get_value('SectionGlobals', 'soundvolume'))
try:
    videosound_multiplier = int(Config.get_value('SectionGlobals', 'videosound_multiplier'))
    if videosound_multiplier < 1 or videosound_multiplier > 5:
        raise('not valid multiplier')
    logs.info(f"Video sound multiplier is set to {videosound_multiplier}")
except:
    videosound_multiplier = 1
    logs.error(f"{Config.get_value('SectionGlobals', 'videosound_multiplier')} is not a valid videosound_multiplier(1-5). Back to 1")

try:
    sound_multiplier = float(Config.get_value('SectionGlobals', 'sound_multiplier'))
    if sound_multiplier < 10 or sound_multiplier > 100:
        raise('not valid multiplier')
    logs.info(f"Sound multiplier is set to {sound_multiplier}")
except:
    sound_multiplier = 100
    logs.error(f"{Config.get_value('SectionGlobals', 'sound_multiplier')} is not a valid sound_multiplier(10-100. ex : 75). Back to 100")

video_player = cvideos.Videos(logs, File, level=video_level, volume=volume, multiplier=videosound_multiplier)
image_player = cimages.Images(logs, File, level=video_level)

#display = cscreen.Screen(Config, logs, File, Lang, rpi, dmd, video_player, Font=font, wait_event_time=wait_event_time, t_event=t_event)
display = cscreen.Screen(Config, logs, File, Lang, rpi, dmd, video_player, image_player, Font=font, wait_event_time=wait_event_time)
display.set_soundmultiplier(sound_multiplier)

image_player.set_display(display)

rpi.set_play_sound(display.play_sound)
rpi.set_send_insult(dmd.send_insult)

if rpi_error is not None:
    display.mcp_error(rpi_error)

# Manage Webcam USB
camera = ccamera.Camera(Config, display, logs)

# Client of Master Server
NetMasterClient = cclient.MasterClient(logs)
# v1.2 SQlite score storage
scores = cscores.Scores(Config, logs)

#################################
# Install additional librairies # 
#    Delete script if succeed   #
#################################

update_lib = "/pydarts/scripts/update_lib.sh"
if os.path.isfile(update_lib):
    logs.info("================================================================")
    logs.info("Install additional librairies\n")
    display.message(['Install_additional_librairies'], 0, None, 'middle')
    code_retour = os.system(f"sh {update_lib}")
    if code_retour == 0:
        logs.info("Install additional librairies succeed !\n")
        os.remove(update_lib)
    else:
        logs.erreur(f"Erreur lors de l'exécution du script (code {code_retour})")
    logs.info("================================================================")

#####################
# Update librairies #
#####################

if not Config.file_exists and False:
    logs.info("================================================================")
    logs.info("Updating librairies\n")
    display.message(['Updating_librairies'], 0, None, 'middle')
    cmd = '/pydarts/scripts/update_tool.sh'
    os.system(cmd)
    logs.info("================================================================")

##############
# AUTO UPDATE
##############
game_type = None

display.init_colorset()

version = cupdate.get_version(logs)
if Config.get_value('SectionGlobals', 'check_for_updates', False):
    try:
        display.message(['update-check'], 0, None, 'middle')
        last, new_version, size = cupdate.get_last(logs, \
                config_favorites['servers'].split(',')[0].split(':')[0], '5000', version)

        if last is not None:
            display.message(['update-download'], 0, None, 'middle')
            last, size = cupdate.download_update(logs, \
                    config_favorites['servers'].split(',')[0].split(':')[0], '5000', last, size)

            if last is None:
                display.message(['update-failed'], 0, None, 'middle')
            else:
                response = display.wait_validation("update-available")
                if response:
                    display.message(['updating'], 0, None, 'middle')
                    cupdate.apply_update(logs, last, new_version)
                    display.message([f'Version {new_version} installée', 'restarting'], \
                            1000,  'middle', bg_color='menu-ok')
                    version = new_version

                    game_type = 'restart'
    except Exception as exception:
        print("[WARNING] Unable to check/get updates.")
        print(f"[WARNING] Error was {exception}")
        print(f"version is {version}")

##############
# INIT
##############

# Give translations to object rpi
dispatcher.publish('off', limit=['TARGET', 'STRIP', 'OTHER'])
dispatcher.publish('launch', limit=['TARGET', 'STRIP', 'OTHER', 'LIGHT', 'STROBE'])

# Beautiful intro screen
if game_type != 'restart' and rpi_error is None:
    if bool(config_advanced['launch-game-celebration']):
        rpi.light_toys(['LIGHT_CELEBRATION'])
    dmd.send_text(Lang.translate('Welcome'))
    #display.nice_shot(Lang.translate('Welcome'))
    rpi.light_toys(['LIGHT_CELEBRATION'], False)

# If exists, display version's changelog
display.display_changelog(version)

# Sound volume
if volume:
    display.sound_volume = volume

# Sys requirements check
if sys.version[:3] not in Config.supported_python_versions:
    logs.warning(f"Your version of python {sys.version[:3]} is not known as raspydarts compatible.")
    logs.warning(f"Please execute raspydarts with one of this version of python : {Config.supported_python_versions}.")

# Verbosity
debuglevel = int(Config.get_value('SectionGlobals', 'debuglevel'))
if debuglevel >= 1 and debuglevel <= 4:
    logs.update_facility(debuglevel)

####################
# Calibration Wizard
####################

if not Config.file_exists:
    logs.debug("Launching raspberry input wizard")

    config_done = False
    cancel = 0
    while not config_done:
        if cancel > 2:
            logs.debug("Configuration canceled by user")
            sys.exit(0)

        cancel += 1
        # Display first use wizard
        config_done = display.get_rpi_config()

    p_target = False
    p_strip = False
    game_type = 'restart'

#####################
# Init some vars
#####################
match_qty = 0  # Count number of matches

# Init vars according to Customization, config else
#solo = int(Config.get_value('SectionGlobals', 'solo'))
play_firstname = bool(Config.get_value('SectionGlobals', 'play_firstname'))
print_dartstroke = bool(Config.get_value('SectionGlobals', 'print_dartstroke'))
light_target = bool(Config.get_value('SectionGlobals', 'light_target'))
light_strip = bool(Config.get_value('SectionGlobals', 'light_strip'))
illumination_mode = bool(Config.get_value('SectionGlobals', 'illumination_mode'))
illumination_color = Config.get_value('SectionGlobals', 'illumination_color')
pnj_time = int(Config.get_value('SectionGlobals', 'pnj_time'))
sound_duration = int(Config.get_value('SectionGlobals', 'nextplayer_sound_duration'))
try:
    competition_mode = bool(Config.get_value('SectionGlobals', 'competition_mode'))
except:
    competition_mode = False

#logs.debug(f"Solo option is set to : {solo}s")
logs.debug(f"play_firstname option is set to : {play_firstname}")
logs.debug(f"print_dartstroke option is set to : {print_dartstroke}")
logs.debug(f"light_target option is set to : {light_target}")
logs.debug(f"light_strip option is set to : {light_strip}")
logs.debug(f"illumination_mode option is set to : {illumination_mode}")
logs.debug(f"illumination color option is set to : {illumination_color}")
logs.debug(f"pnj_time option is set to : {pnj_time}ms")
logs.debug(f"nextplayer_sound_duration option is set to : {sound_duration}ms")
logs.debug(f"wait_event_time option is set to : {wait_event_time}ms")

stats_screen = False  # Return value of Stats Screen (start again a new game with same parameters)
netgamename = Config.get_value('SectionAdvanced', 'netgamename', False)  # Game Name

if game_type != 'restart':
    game_type = 'local'

local_players = Config.get_value('Favorites', 'firstnames', False, None, split=',')
players_bank = Config.get_value('SectionAdvanced', 'localplayers', False, split=',')         # Local players
selected_game = Config.get_value('SectionAdvanced', 'selectedgame', False, 'None')            # Selected game
if selected_game is not None and local_players is not None:
    direct_play = Config.get_value('SectionAdvanced', 'directplay', False, False)            # By-passs menus, use dirstnames and selected_game parameters
else:
    direct_play = False
pref_fun_game = Config.get_value('SectionAdvanced', 'preferedfungame', False, None)
pref_classic_game = Config.get_value('SectionAdvanced', 'preferedclassicgame', False, None)
pref_sport_game = Config.get_value('SectionAdvanced', 'preferedsportgame', False, None)
pref_category = Config.get_value('SectionAdvanced', 'preferedcategory', False, None)
nb_sets = int(Config.get_value('SectionAdvanced', 'nb_sets', False, None))

favorites_players = Config.get_value('Favorites', 'firstnames', False, split=',')

logs.debug(f"firstnames option is set to : {local_players}")
logs.debug(f"localplayers option is set to : {players_bank}")
logs.debug(f"local_players option is set to : {local_players}")
logs.debug(f"selected_game option is set to : {selected_game}")
logs.debug(f"direct_play option is set to : {direct_play}")
logs.debug(f"pref_fun_game option is set to : {pref_fun_game}")
logs.debug(f"pref_sport_game option is set to : {pref_sport_game}")
logs.debug(f"pref_classic_game option is set to : {pref_classic_game}")
logs.debug(f"pref_category option is set to : {pref_category}")

wait_finish = not File.is_dir('next_player', 'sounds')

# Load game's logo
display.message(['Loading logos...'], 0, None, 'middle')

for category in ('classic', 'fun', 'sport'):
    games = display.get_games_list(category)
    display.game_menu(category, games, config_favorites['games'], 1, load=True)
    display.game_menu(category, games, config_favorites['games'], 2, load=True)
del games

if pref_category is None:
    category = 'classic'
else:
    category = pref_category

######################
######## SOFTWARE LOOP
######################

versionGame = ''

try:
    while game_type not in ('restart', 'quit', 'shutdown'):

        # Init (or reset) network status
        net_status = None  # Master or slave

        # To restore special bg
        display.reset_background()
        #############################
        # NEW MENUS SEQUENCE
        #############################

        ######
        # START AGAIN (possibility to start a new game straight away without using menus again)
        ######

        if stats_screen == 'startagain':
            if game_type == 'local':
                menu = True
                if config_globals['keeporder']:
                    for player in players:
                        player.reset()
                else:
                    # Try to order players depending of game
                    try:
                        local_players = game.next_game_order(players)
                        all_players = local_players
                        players_count = len(local_players)
                    except Exception as exception:
                        logs.error("Unable to order players from previous results.")
                        logs.error(f"Error was {exception}")
            elif game_type in ('netjoin', 'netcreate'):
                players_count = len(local_players)
                menu = 'connect'

        ###
        ### DIRECT PLAY MODE (possibility to launch a game without passing thru menus).
        ### Only available if it hasen't be disabled by any process
        elif game_type == 'local' and local_players is not None and selected_game is not None and direct_play:
            try:
                Game = selected_game.replace(' ', '_')
                menu = True
                all_players = local_players
                players_count = len(local_players)
                choosed_game = __import__("games.{Game}", fromlist=["games"])

                # Merge config file options and default game options
                default_game_options = choosed_game.OPTIONS

                if debuglevel == 2:
                    try:
                        debug_game_options = choosed_game.DEBUG
                    except:
                        debug_game_options = {} #empty dictionary
                    default_game_options.update(debug_game_options)
                # Take config file Game options if they exists
                config_game_options = Config.read_file(Game)
                if not config_game_options: config_game_options = {}  # Default to empty dict

                old_options = []
                for config_game_option in config_game_options:
                    option_found = False
                    for default_game_option in default_game_options:
                        if config_game_option == default_game_option:
                            option_found = True
                    if not option_found: #pas trouvé
                        old_options.append(config_game_option) #Donc une ancienne option

                if len(old_options) > 0:
                    display.display_background()
                    display.message([Lang.translate('options-old')], 5000, None, 'middle', 'big')
                    for option in old_options: #Nettoyage
                        del config_game_options[option]

                game_options = default_game_options.copy()
                game_options.update(config_game_options)
                display.game_options = game_options
                display.selected_game = Game
                # Enable Direct Play mode
                direct_play = True
            except Exception as exception:
                logs.error(f"Unable launch Direct Play mode. Error was {exception}")
                menu = 'gametype'
        else:
            menu = 'gametype'

        #######################
        # Menus loop
        #######################
        while menu is not True:

            fast_games_mode = bool(Config.get_value('SectionGlobals', 'fast_games_mode', False))
            only_favorites_games_mode = bool(Config.get_value('SectionGlobals', 'only_favorites_games_mode', False))

            ########
            # MAIN MENU - GAME TYPE (LOCAL, NETWORK, NETWORK MANUAL)
            ########
            if (menu == 'gametype' and not fast_games_mode) or (menu == 'mainmenu' and fast_games_mode) :
                rpi.light_toys(['LIGHT_NAVIGATE', 'LIGHT_VALIDATE'])
                rpi.light_toys(['LIGHT_BACK'], False)
                dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER', 'LIGHT', 'STROBE'])
                game_type = display.main_menu()
                if game_type in ('restart', 'quit', 'shutdown'):
                    rpi.light_toys(['LIGHT_VALIDATE'], False)
                    break
                elif game_type == 'infos':
                    display.infos_menu(Config)
                elif game_type != 'miscellaneous':
                    menu = 'players'
            elif menu == 'gametype' and fast_games_mode :
                    menu = 'players'

            ########
            # PLAYERS NAMES
            ########
            if menu == 'players':
                dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER', 'LIGHT', 'STROBE'])
                rpi.light_toys(['LIGHT_PLAYERS'])
                rpi.light_toys(['LIGHT_BACK'])
                # Display menu anyway
                nb_sets = int(Config.get_value('SectionAdvanced', 'nb_sets', False, None))
                # Get players favorite color
                players_favorite_color = Config.get_players_color()

                if game_type in ('netjoin', 'netcreate'):
                    nb_sets, players_list, competition_mode, players_favorite_color = \
                            display.players_menu(local_players, bank=players_bank, sets=None, context=game_type,
                                                 colors_available = dispatcher.get_colors(), players_color = players_favorite_color)
                    nb_sets = 1
                else:
                    nb_sets, players_list, competition_mode, players_favorite_color = \
                            display.players_menu(local_players, bank=players_bank, sets=nb_sets, competition_mode=competition_mode,
                                                 colors_available = dispatcher.get_colors(), players_color = players_favorite_color)

                if players_list == 'escape':
                    if not fast_games_mode :
                        menu = 'gametype'
                    elif  fast_games_mode :
                        menu = 'mainmenu'
                else:
                    local_players = players_list[::]
                    players_count = len(local_players)  # players_count = Number of players

                    if game_type in ('netjoin', 'netcreate'):
                        menu = 'serverlist'
                    elif game_type == 'local':
                        menu = 'gamecategory'
                rpi.light_toys(['LIGHT_PLAYERS'], False)

                if competition_mode:
                    video_player.set_level(0)
                    image_player.set_level(0)
                    #solo = -1
                    releasedartstime = 1
                    display.set_blinktime(500)
                else:
                    display.reset_mode()
                    #solo = int(Config.get_value('SectionGlobals', 'solo'))
                    releasedartstime = int(Config.get_value('SectionGlobals', 'releasedartstime'))# Relase darts delay
                    display.set_blinktime(int(Config.get_value('SectionGlobals', 'blinktime')))

                    video_player.set_level(video_level)
                    image_player.set_level(video_level)
                logs.debug(f"Competition mode : {competition_mode}")
                logs.debug(f"Video : {video_player.level}")
                logs.debug(f"Image : {image_player.level}")
                logs.debug(f"releasedartstime  : {releasedartstime}")

            ########
            # NETWORK USING MASTER SERVER
            ########
            if menu == 'serverlist':  # Choice server (when several)
                dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER', 'LIGHT', 'STROBE'])
                if config_favorites['servers'] == '':
                    display.message(["Aucun server paramétré."], wait=5, refresh=True)
                    menu = 'servers'
                    game_type = 'miscellaneous'
                else:
                    net_client = cclient.Client(logs)
                    # No interaction if only one server on favorites
                    Server = display.server_menu(net_client, config_favorites['servers'].split(','))
                    servername = Server.split(':')[0]
                    serverport = 25005
                    masterserverport = 25006 #int(Server.split(':')[1])
                    serveralias = Server.split('.')[0]
                    logs.debug(f"Using {servername}:{masterserverport}")
                    if Server == 'escape':
                        # Back to home
                        menu = 'gametype'
                    else:
                        menu = 'createorjoin'


            if menu == 'createorjoin':
                menu = 'connect'
                if game_type == 'netjoin':
                    logs.debug(f"Get remote game list on {servername}:{masterserverport}")
                    netgamename = display.net_game_list(NetMasterClient, players_count, servername, masterserverport)
                    if netgamename == 'escape':
                        menu = 'gametype'
                else:
                    netgamename = f'game{random.randint(10000, 99999)}'

            ########
            # NET CONNECTION
            ########
            # If network, connect to server
            if game_type in ('netjoin', 'netcreate') and menu == 'connect':
                logs.debug("Net game requested.")
                releasedartstime = 0 # In case of online game, force the SOLO MODE OFF from config (players must push PLAYERBUTTON every rounds, mandatory)
                try:
                    display.display_background()
                    display.message([Lang.translate('game-client-connecting')], wait=500)
                    net_client.connect_host(servername, serverport)    #int(serverport))
                    menu = 'net1'
                except Exception as exception:
                    logs.error(f"Unable to reach server : {servername}:{serverport}. Error is {exception}")
                    display.display_background()
                    display.message([Lang.translate('game-client-no-connection')])
                    menu = 'gametype'

            if game_type in ('netjoin', 'netcreate') and menu == 'net1':
                # Check client/server version compatibility
                logs.debug("Join {} remote game".format(netgamename))
                serverversion = net_client.get_server_version(netgamename)
                display.version_check(serverversion)
                net_status = net_client.join2(netgamename)
                logs.debug("net_status = {}".format(net_status))
                # If you are master go to the game selector
                if net_status == 'YOUAREMASTER' and stats_screen != 'startagain':
                    menu = 'gamecategory'
                # If you are master and asked to start again, so... go to starting page
                elif net_status in ['YOUAREMASTER', 'YOUARESLAVE']:
                    menu = 'net3'

            if game_type == 'miscellaneous':
                # PREFERENCES
                rpi.light_toys(['LIGHT_BACK'])
                if menu != 'servers':
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    Misc = display.miscellaneous((cupdate,config_favorites))

                    if Misc == 'escape':
                        if not fast_games_mode :
                            menu = 'gametype'
                        elif  fast_games_mode :
                            menu = 'mainmenu'
                    elif Misc == 'restart':
                        game_type = Misc
                    else:
                        menu = Misc

                if menu == 'firstnames':
                    # FAVORITE PLAYERS
                    rpi.light_toys(['LIGHT_PLAYERS'])
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    # Get players favorite color
                    players_favorite_color = Config.get_players_color()
                    useless, firstnames, players_favorite_color = display.players_menu(favorites_players, context='pref', bank=players_bank,
                                                                 colors_available = dispatcher.get_colors(), players_color = players_favorite_color)
                    if firstnames != 'escape':
                        config_favorites['players_color'] = str(players_favorite_color)
                        config_favorites['firstnames'] = ','.join(firstnames)
                        favorites_players = firstnames[::]
                        local_players = firstnames[::]
                        Config.write_file()
                    rpi.light_toys(['LIGHT_PLAYERS'], False)

                elif menu == 'games':
                    # FAVORITE GAMES
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    games = display.favorites_games_menu(config_favorites['games'])
                    if games != 'escape':
                        config_favorites['games'] = games
                        Config.write_file()

                elif menu == 'servers':
                    # SERVERS MENU
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    servers = display.favorites_servers_menu(config_favorites['servers'])
                    if servers != 'escape':
                        config_favorites['servers'] = servers
                        Config.write_file()
                    menu = ''

                elif menu == 'setup':
                    # SETUP MENU
                    setup = display.setup_menu()

                    while setup != 'escape':
                        if setup == 'test-buttons':
                            display.test_buttons_menu()

                        elif setup == 'test-target':
                            display.test_target_menu()

                        elif setup == 'test-toys':
                            display.test_toys_menu()

                        elif setup == 'reset':
                            response = display.wait_validation("reinit-question")
                            if response:
                                display.message(['reseting'], 0, None, 'middle')
                                os.rename(Config.configFile, f"{Config.configFile}.back")
                                game_type = 'restart'
                                break

                        elif setup == 'setup-buttons':
                            try:
                                buttons = rpi.gpio.get_defaults()
                            except:
                                buttons = rpi.get_defaults()
                            setupbuttons = display.setup_buttons_menu(Config_rpi, buttons)
                            if setupbuttons != 'escape':
                                Config_rpi = setupbuttons
                                if not rpi.set_io(setupbuttons):
                                    display.message(['config-noMCP'], None, 'red', 'middle', 'big')
                                else:
                                    rpi.config.set_config('Raspberry', setupbuttons)
                                    Config.write_file()

                        elif setup == 'setup-leds':
                            setupleds = ''
                            selY = 1
                            selX = 1
                            Nmoy = 6
                            work = str(config_target_leds)
                            while setupleds != 'escape':
                                if isinstance(setupleds, dict):
                                    config_target_leds = setupleds
                                    rpi.config.set_config('LEDTarget', setupleds)
                                    Config.write_file()
                                    break
                                elif setupleds[0:3:1] == 'try':
                                    # try
                                    leds = setupleds.split('|')[1]
                                    work = setupleds.split('|')[2]
                                    work = f"{setupleds.split('|')[3]}|{work}"
                                    selY = int(setupleds.split('|')[4])
                                    selX = int(setupleds.split('|')[5])
                                    Nmoy = int(setupleds.split('|')[6])
                                    dispatcher.publish('leds', leds, limit=['TARGET', 'STRIP', 'OTHER'])
                                    if setupleds.count('|') != 6:
                                        work = str(config_target_leds)
                                setupleds = display.setup_leds_menu(work, selY, selX, Nmoy)

                        elif setup == 'setup-pinleds':
                            used_pins = []
                            for key in config_input:
                                try:
                                    used_pins.append(int(config_input[key]))
                                except:
                                    pass
                            for key in config_output:
                                try:
                                    used_pins.append(int(config_output[key]))
                                except:
                                    pass

                            tmp = display.setup_pinsleds_menu(config_leds, used_pins)
                            if tmp != 'escape':
                                config_leds = tmp
                                rpi.config.set_config('Raspberry_Leds', config_leds)
                                Config.write_file()

                        elif setup == 'setup-couleurs-segments':
                            tmp = display.setup_couleurs_segments_menu(dispatcher.get_colors(), dispatcher)
                            if tmp != 'escape':
                                Config.set_value_colorset(File.theme_dir,tmp)
                                color_values = []
                                for (key, value) in tmp:
                                    color_values.append(str(value).replace('(','').replace(')','').replace(' ',''))
                                dispatcher.publish('reload', "|".join(color_values), limit=['TARGET','STRIP','OTHER'])

                        elif setup == 'setup-cam':
                            tmp = display.setup_cam_menu(config_camera)
                            if tmp != 'escape':
                                config_camera = tmp
                                rpi.config.set_config('Camera', config_camera)
                                Config.write_file()
                                camera = ccamera.Camera(Config, display, logs)

                        setup = display.setup_menu()

                elif menu == 'firstname-bank':
                    # Firstnames bank menu
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    rpi.light_toys(['LIGHT_PLAYERS'])
                    # Get players favorite color
                    players_favorite_color = Config.get_players_color()
                    #
                    useless, bank, players_favorite_color = display.players_menu(players_bank, context='bank',
                                                             colors_available = dispatcher.get_colors(), players_color = players_favorite_color)
                    if bank != 'escape':
                        config_favorites['players_color'] = str(players_favorite_color)
                        config_advanced['localplayers'] = ','.join(bank)
                        Config.write_file()
                        players_bank = bank[::]
                    rpi.light_toys(['LIGHT_PLAYERS'], False)

                elif menu == 'backups':
                    # BACKUP MENU
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    b = display.backup_menu()
                    if b == 'restart':
                        game_type = 'restart'
                        break

                elif menu == 'customization':
                    # CUSTOMIZATION
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    cust = display.customization_menu(Config.config['SectionGlobals'], dispatcher.get_colors())
                    if cust != 'escape':
                        Config.config['SectionGlobals'] = cust
                        Config.write_file()
                        config_globals = Config.read_file("SectionGlobals")
                        video_level = int(Config.get_value('SectionGlobals', 'videos'))
                        video_player.set_level(video_level)
                        image_player.set_level(video_level)
                        video_player.set_volume(int(Config.get_value('SectionGlobals', 'soundvolume')))
                        display.sound_volume = int(Config.get_value('SectionGlobals', 'soundvolume'))
                        #solo = int(Config.get_value('SectionGlobals', 'solo'))
                        releasedartstime = int(Config.get_value('SectionGlobals', 'releasedartstime'))
                        play_firstname = bool(Config.get_value('SectionGlobals', 'play_firstname'))
                        print_dartstroke = bool(Config.get_value('SectionGlobals', 'print_dartstroke'))
                        light_target = bool(Config.get_value('SectionGlobals', 'light_target'))
                        light_strip = bool(Config.get_value('SectionGlobals', 'light_strip'))
                        competition_mode = bool(Config.get_value('SectionGlobals', 'competition_mode'))
                        illumination_mode = bool(Config.get_value('SectionGlobals', 'illumination_mode'))
                        illumination_color = Config.get_value('SectionGlobals', 'illumination_color')

                        logs.update_facility(int(Config.get_value('SectionGlobals', 'debuglevel')))
                        display.wait_event_time = int(Config.get_value('SectionGlobals', 'waitevent_time'))
                        display.file_class.reset_theme(Config.get_value('SectionGlobals', 'colorset'))
                        display.init_colorset()
                        #display.define_constants(True, Font=cust['font'])

                elif menu == 'animations':
                    # LEDS ANIMATIONS
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    event = display.animations_menu(dispatcher.get_events())
                    work = ''
                    while event != 'escape':
                        if work != '':
                            animation = dispatcher.string_to_pref(work)
                        else:
                            try:
                                animation = config_events[event].copy()
                            except:
                                dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                                animation = None

                        anim = display.event_menu(event, dispatcher.get_strip(), dispatcher.get_target(), dispatcher.get_colors(), animation)
                        
                        if anim[0:3:1] == 'try':
                            if anim.find('hue') >= 0:
                                work = "{" + anim.split('{')[1].split('}|')[0] + "}"
                                for a in anim.split('}|')[1::]:
                                    dispatcher.publish('special', a, limit=['TARGET', 'STRIP', 'OTHER'])
                            else:
                                work = anim.split('|')[1]
                                for a in anim.split('|')[2::]:
                                    dispatcher.publish('special', a, limit=['TARGET', 'STRIP', 'OTHER'])
                        elif anim == 'escape':
                            dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                            event = display.animations_menu(dispatcher.get_events(), selected_event=event)
                            work = ''
                        else:
                            # save
                            config_events[event] = dispatcher.string_to_pref(anim)
                            Config.write_file()
                            dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                            event = display.animations_menu(dispatcher.get_events(), selected_event=event)
                            work = ''
                if game_type != 'restart':
                    game_type = 'miscellaneous'
                else:
                    break

            if (net_status == 'YOUAREMASTER' or game_type == 'local') and menu == 'gamecategory' and not only_favorites_games_mode:
                # GAME CATEGORY SELECTION
                # Display game category
                dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])

                if config_favorites['games'] == '':
                    response = display.game_category_menu(False, category=category)
                else:
                    response = display.game_category_menu(True, category=category)
                if response == 'escape':
                    menu = 'players'
                    if net_status is not None:
                        net_client.leave_game(netgamename, local_players, net_status)
                        net_client.close_host()
                        net_status = None  # reset Network status if you leave network game
                else:
                    category = response
                    if selected_game is None:
                        if category == 'fun':
                            selected_game = f"{pref_fun_game}"
                        elif category == 'classic':
                            selected_game = f"{pref_classic_game}"
                        elif category == 'sport':
                            selected_game = f"{pref_sport_game}"
                        if selected_game is not None:
                            selected_game = selected_game.replace('_', ' ')
                    menu = 'gamelist'
            elif (net_status == 'YOUAREMASTER' or game_type == 'local') and menu == 'gamecategory' and only_favorites_games_mode:
                    menu = 'gamelist'
                    category = 'favoris'

            if (net_status == 'YOUAREMASTER' or game_type == 'local') and menu == 'gamelist':
                # GAME SELECTION
                # Display game choice and option only for game creators (local and netcreate)
                if category == 'favoris':
                    games = display.get_games_list(category, favorites=config_favorites['games'])
                else:
                    games = display.get_games_list(category)

                if category == 'favoris' and len(games) == 0 and only_favorites_games_mode:
                    display.update_screen(display.message(["no-favs-games"], wait=3000, size='big', refresh=True))
                    Game = 'escape'
                else:
                    dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                    display.update_screen(display.message(["Loading"], wait=0, refresh=False))
                    Game = display.game_menu(category, games, config_favorites['games'], players_count, selected_game=selected_game)

                if Game == 'escape':
                    if not only_favorites_games_mode:
                        menu = 'gamecategory'
                    else:
                        menu = 'players'
                        category = ''
                else:
                    choosed_game = __import__(f"games.{Game.replace(' ', '_')}", fromlist=["games"])
                    Game = Game.split('.')[1]
                    try:
                        versionGame=choosed_game.VERSION
                    except:
                        versionGame='' # not have version number at this time
                    try:
                        playersOk = choosed_game.check_players_allowed(players_count)
                        if not playersOk:
                            display.message([f"{Lang.translate('bad-numberofplayers')}"], 2500, 'menu-ko', 'middle', 'big')
                        else:
                            logs.debug(f"Ok, {players_count} players allowed")
                            selected_game = Game
                            menu = 'gameoptions'
                    except:
                        logs.debug(f"KO, cannot check if {players_count} players allowed")
                        selected_game = Game
                        menu = 'gameoptions'

            if (net_status == 'YOUAREMASTER' or game_type == 'local') and menu == 'gameoptions':
                # GAME OPTIONS
                # Display game choice and option only for game creators (local and netcreate)
                default_game_options = choosed_game.OPTIONS
                if debuglevel == 2:
                    try:
                        debug_game_options = choosed_game.DEBUG
                    except:
                        debug_game_options = {} #empty dictionary
                    default_game_options.update(debug_game_options)
                config_game_options = Config.read_file(f"game-{Game.replace(' ', '_')}")  # Take config file Game options if they exists
                if not config_game_options: config_game_options = {}  # Default to empty dict

                old_options = []
                for config_game_option in config_game_options:
                    option_found = False
                    for default_game_option in default_game_options:
                        if config_game_option == default_game_option:
                            option_found = True
                    if not option_found: #pas trouvé
                        old_options.append(config_game_option) #Donc une ancienne option

                if len(old_options) > 0:
                    display.display_background()
                    display.message([Lang.translate('options-old')], 5000, None, 'middle', 'big')
                    for option in old_options: #Nettoyage
                        del config_game_options[option]

                game_options = default_game_options.copy()
                game_options.update(config_game_options)

                dispatcher.publish('menu', limit=['TARGET', 'STRIP', 'OTHER'])
                game_options = display.options_menu(game_options, Game.replace(' ', '_'), players_count, versionGame)
                if game_options == 'escape':
                    menu = 'gamelist'
                elif net_status is None:
                    menu = True
                else:
                    menu = 'net3'


            if net_status == 'YOUAREMASTER' and menu == 'net3':
                # MasterPlayer send game info to server
                # Send Game info (gamename and selected options - can be merged)
                net_client.send_game(Game.replace(' ', '_'))
                net_client.send_options(game_options, choosed_game.NB_DARTS, nb_sets)
                menu = 'starting'
                try:  # Check if it is the right place
                    logs.debug(f"Sending game info to master server {servername}:{masterserverport}")
                    NetMasterClient.connect_master(servername, masterserverport)
                    NetMasterClient.send_game_info(servername, serveralias, serverport, netgamename, Game.replace(' ', '_'), config_globals['netgamecreator'], players_count, nb_sets)
                    NetMasterClient.close_connection()
                except Exception as exception:
                    logs.warning(f"Unable to reach Master Server {servername} on port {masterserverport}. Error was : {exception}")

            """
            Notice Master server that we joined and add local players to game on
            master server
            """
            if net_status == 'YOUARESLAVE' and menu == 'net3':
                try:
                    NetMasterClient.connect_master(servername, masterserverport)
                    NetMasterClient.join_game(netgamename, len(local_players))
                    NetMasterClient.close_connection()
                    menu = 'starting'
                except:
                    logs.warning("Unable to add local players to Master Server")

            if menu == 'starting':
                """
                Network game menu - Starting - If network enabled, all_players (All players names)
                list is updated via network
                """
                # Wait for the choosed game from server
                if net_status == 'YOUARESLAVE':
                    Game = net_client.get_game()
                # Display starting page with a few game info
                all_players = display.starting(net_client, net_status, local_players, netgamename, Game.replace(' ', '_'))
                menu = True  # Means that goes on...
                if all_players == [] or all_players == -1:  # Empty network Player List or -1 signal
                    net_client.leave_game(netgamename, local_players, net_status)
                    net_client.close_host()
                    # For Slave players, display the message and wait for Enter to be pressed
                    if not all_players:
                        display.message([Lang.translate('master-player-has-left')], None, None, 'middle')
                        NetMasterClient.connect_master(servername, masterserverport)
                        NetMasterClient.cancel_game(netgamename)
                        NetMasterClient.close_connection()
                        rpi.listen_inputs(['arrows'], ['escape', 'enter'])
                    elif all_players == -1:  # Notice Master server that someone is leaving
                        NetMasterClient.connect_master(servername, masterserverport)
                        NetMasterClient.leave_game(netgamename, len(local_players))
                        NetMasterClient.close_connection()
                    menu = 'gametype'
                    net_status = None  # reset Network status if you leave network game
                else:
                    menu = 'net4'
            # If network disabled - local games
            else:
                all_players = local_players  #  In local games, all players are local players
                players_count = len(all_players)  # Refresh count of number of players again

            if net_status == 'YOUARESLAVE' and menu == 'net4':
                """ Display message while it download info from server """
                players_count = len(all_players)  # Refresh count of number of players again
                display.message([Lang.translate('getting-info-from-server')], 0, None, 'middle')
                try:
                    choosed_game = __import__("games.classic.{}".format(Game.replace(' ', '_')), fromlist=["games"])
                except:
                    try:
                        choosed_game = __import__("games.fun.{}".format(Game.replace(' ', '_')), fromlist=["games"])
                    except:
                        choosed_game = __import__("games.sport.{}".format(Game.replace(' ', '_')), fromlist=["games"])
                game_options, nb_sets = net_client.get_options()
                display.game_options = game_options
                display.selected_game = Game.replace(' ', '_')
                logs.debug("Starting a network game of {} (with options {} with {} players : {}".format(Game.replace(' ', '_'), game_options, players_count, all_players))
                menu = True

            if net_status == "YOUAREMASTER" and menu == 'net4':
                """ players are ready - game will be launch so we can delete game from master server """
                players_count = len(all_players)  # Refresh count of number of players again
                menu = True
                try:
                    NetMasterClient.connect_master(servername, masterserverport)
                    NetMasterClient.launch_game(netgamename)
                    NetMasterClient.close_connection()
                except Exception as e:
                    logs.warning(f"Unable to reach Master Server {servername} on port {masterserverport} in order to remove game")

        """ END OF MENU LOOP """
        if game_type not in ('restart' ,'quit' ,'shutdown'):
            if stats_screen == 'startagain':
                old_player = players[:]
            # Now create players objects
            players = []
            nbcol = int(Config.get_value('SectionGlobals','nbcol'))
            
            for ident in range(0, players_count):
                # Create Player object
                try:
                    players.append(choosed_game.CPlayerExtended(ident, nbcol, interior=Config.get_value('SectionAdvanced','interior')))
                except:
                    players.append(choosed_game.CPlayerExtended(ident, nbcol))
                    
                players[ident].name = all_players[ident]
                
                if all_players[ident].find("]") != -1:
                    players[ident].computer = True
                    if all_players[ident].find('[NoOb]') != -1:
                        players[ident].level = 1
                        players[ident].name = players[ident].name.replace('[NoOb]','')
                    elif all_players[ident].find('[BegiN]') != -1:
                        players[ident].level = 2
                        players[ident].name = players[ident].name.replace('[BegiN]','')
                    elif all_players[ident].find('[InTeR]') != -1:
                        players[ident].level = 3
                        players[ident].name = players[ident].name.replace('[InTeR]','')
                    elif all_players[ident].find('[PrO]') != -1:
                        players[ident].level = 4
                        players[ident].name = players[ident].name.replace('[PrO]','')
                    else:
                        players[ident].level = 5
                        players[ident].name = players[ident].name.replace('[ExperT]','')
            stats_screen = False

            ################
            # MATCH Loop
            ################

            # Match loop ends if match_done is true
            match_done = False
            set_done = False
            set_winner = None
            Set = 0
            Sets = []
            # StartTime / EndTime / winner
            now = datetime.datetime.now()
            Sets.append([Set + 1, now, None, -1, 0, 0])
            play_id = now.strftime("%Y%m%d%H%M%S")

            interrupted = False
            # Round init
            actual_round = 1
            # Player Launch Init
            player_launch = 1
            # Actual Player Init
            actual_player = 0
            # Create Game objects and init var
            display.teaming = False
            try:
                versionGame=choosed_game.VERSION
            except:
                versionGame='' # game has no version at this time
            game = choosed_game.Game(display, Game.replace(' ', '_'), players_count, game_options, Config, logs, rpi, dmd, video_player)
            game_is_ok_for_color = game.game_is_ok_for_color
            try:
                playersOk = game.check_players_allowed(players_count)
            except:
                playersOk = False
            if not playersOk:
                display.message([f"{Lang.translate('bad-numberofplayers')}"], 2500, 'menu-ko', 'middle', 'big')
                # pas le droit de jouer joueurs insuffisant
                last_game_screen = None
                stats_screen = None
                match_done = True
                set_done = True
                interrupted = True
                continue

            if stats_screen != 'startagain':
                for ident in range(0, players_count):
                    # Override existing color
                    if players[ident].name in players_favorite_color :
                        players[ident].init_color(players_favorite_color[players[ident].name])
                    else:
                        if display.teaming and ident >= int(players_count / 2):
                            players[ident].init_color(players[ident - int(players_count / 2)].color)
                        else:
                            players[ident].init_color(display.colorset[f'player{ident + 1}'])

            try:
                game_theme = game_options['theme']
                if game_theme != 'default':
                    display.file_class.reset_theme(game_theme)
                    display.init_colorset()
            except:
                logs.error(f"No personnalisable theme for {game}")
            display.define_constants(players_count, Font=config_globals['font'])

            game.dispatcher = dispatcher
            try:
                light_segment = game.light_segment
            except:
                light_segment = True
            try:
                if game_type in ('netjoin', 'netcreate'):
                    display.game_type = 'online'
                else:
                    display.game_type = 'local'
            except:
                pass
            # Dart Stroke Init
            dart_stroke = None
            # Increment the number of Match done
            match_qty += 1
            # Backup of the Hit for a usage in following round
            prev_dart_stroke = None
            back_count = 0
            # Used to store Cheats
            magickey = ""
            handler = game.init_handler()

            # Run handicap
            try:
                game.check_handicap(players)
            except Exception as exception:
                logs.error(f"Handicap failed : {exception}")

            # Store game properties in local DB
            data = {'game_options': ""}
            for opts in game_options:
                data['game_options'] += f"{opts}={game_options[opts]}|"
            data['game_name'] = Game.replace(' ', '_')
            data['nb_players'] = players_count
            game_id = scores.add_game(data)
            logs.debug(f"Local game id is : {game_id}")
            # Reinit leds
            dispatcher.publish('newgame', limit=['TARGET', 'STRIP', 'OTHER', 'LIGHT', 'STROBE'])
            rpi.target_leds = ''
            rpi.target_leds_blink = ''
            logs.debug("###### NEW GAME #########")
            # Disable videos during online game
            if net_status in ('YOUARESLAVE', 'YOUAREMASTER') or competition_mode:
                video_player.set_level(0)
                image_player.set_level(0)
            intro_done = False
            played_video = None
            played_sound = None
            cupdate.send_infos(logs, Game, players_count, game_options, Config.rpi_version, Config.rpi_serial, "start", competition_mode, play_id, version=version)

        else:
            match_done = True
            set_done = True

        # Main loop (every input runs a loop - a dart, a button or a click)
        while not match_done:
            while not set_done:
                post_round_handler = game.init_handler()
                rpi.light_toys(['LIGHT_NAVIGATE', 'LIGHT_VALIDATE', 'LIGHT_PLAYERS'], False)
                rpi.light_toys(['LIGHT_NEXTPLAYER'])

                if player_launch == 1 :
                    rpi.light_toys(['LIGHT_BACK'], False)
                else:
                    rpi.light_toys(['LIGHT_BACK'], True)

                if players[actual_player].computer:
                    rpi.light_toys(['LIGHT_LASER'], False)
                else:
                    rpi.light_toys(['LIGHT_LIGHT'])
                    rpi.light_toys(['LIGHT_LASER'])

                ##############
                # Step 1 : The player plays
                ##############
                pre_dart = -1
                post_dart = -1
                post_round = -2
                early_player_button = -1
                missed_dart = -1
                if not intro_done:
                    if File.is_dir('game_start', 'sounds'):
                        played_video = game.play_intro_only_video()
                        played_sound = display.play_sound('game_start')
                    else:
                        played_sound, played_video = game.play_intro()
                    intro_done = True

                # Display debug every round
                logs.debug("###### NEW ROUND #########")
                logs.debug(f"Game Round {actual_round}. Round of player {players[actual_player].name}.\
                                 Dart {player_launch}.")

                # Backup round
                try :
                    game.backup_round(players, player_launch)
                except:
                    logs.error("Cannot backup round")
                    pass

                # Pre Play Checks
                if net_status == 'YOUARESLAVE':
                    try:
                        randomval = net_client.get_random(actual_round, actual_player, player_launch)
                        game.set_random(players, actual_round, actual_player, player_launch, randomval)
                    except Exception as exception:
                        logs.error(f"Problem getting and setting random value from master client : {exception}")
                        # On eteint la cible si besoin
                        dispatcher.publish('off', limit=['TARGET', 'STRIP', 'OTHER'])

                ##############
                # pre_dart - Is a game method that prepares game before each dart
                ##############
                pre_dart = game.pre_dart_check(players, actual_round, actual_player, player_launch)

                if player_launch == 1 and len(magickey) == 0 and pre_dart != 4:
                    dmd.send_text(players[actual_player].name)
                    logs.debug(f"Display {players[actual_player].name}")
                    if handler['announcement'] is None:
                        display.message([players[actual_player].name], 0, None, 'middle', 'big')
                    # Play sound for first dart (playername otherwise default)
                    display.sound_start_round(players[actual_player].name, play_firstname=play_firstname)

                ##############
                #
                if net_status == 'YOUAREMASTER':
                    try:
                        randomval = game.get_random(players, actual_round, actual_player, player_launch)
                        net_client.send_random(randomval, actual_round, actual_player, player_launch)
                    except Exception as exception:
                        logs.error(f"Problem sending random value to slave clients : {exception}")
                        # On eteint la cible si besoin
                        dispatcher.publish('off', limit=['TARGET', 'STRIP', 'OTHER'])

                # If the player is allowed to play
                if pre_dart != 4 and player_launch <= game.nb_darts:

                    try :
                        # For Simon game
                        logs.debug("POSTPRE")
                        for element in game.post_pre_dart_check(players, actual_round, actual_player, player_launch):
                            logs.debug(f"POSTPRE : {element}")
                            if element == 'PRESSURE':
                                dispatcher.publish('pressure', limit=['TARGET', 'STRIP', 'OTHER', 'LIGHT', 'STROBE'])
                            if element == 'NOPRESSURE':
                                dispatcher.publish('nopressure', limit=['TARGET', 'STRIP', 'OTHER', 'LIGHT', 'STROBE'])

                    except:
                        pass

                    # Display board
                    ClickZones = game.refresh_game_screen(players, actual_round, game.max_round, game.nb_darts - player_launch + 1,
                                        game.nb_darts, game.logo, game.headers, actual_player, OnScreenButtons=config_globals['onscreenbuttons'],
                                        Set=Set, MaxSet=nb_sets
                                        )

                    # On illumine si besoin
                    if light_target and game_is_ok_for_color:
                        dispatcher.publish('Background', limit=['TARGET', 'STRIP', 'OTHER'])
                    if illumination_mode:
                        dispatcher.publish('special', f'STRIP:Light, 0.3,{illumination_color}', limit=['TARGET', 'STRIP', 'OTHER'])
                    elif light_strip:
                        dispatcher.publish('special', f'STRIP:Light, 0.3,{players[actual_player].color}', limit=['TARGET', 'STRIP', 'OTHER'])

                    if rpi.target_leds != '':
                        dispatcher.publish('goal', rpi.target_leds, limit=['TARGET', 'STRIP', 'OTHER'])
                    if rpi.target_leds_blink != '':
                        dispatcher.publish('blink', rpi.target_leds_blink, limit=['TARGET', 'STRIP', 'OTHER'])

                    # The player plays !
                    if net_status is None or players[actual_player].name in local_players:
                        # If its a local game or our turn to play in a net game : We read inputs.

                        while True:

                            if dart_stroke is not None and isinstance(dart_stroke, str):
                                # Backup this dart_stroke for next round
                                prev_dart_stroke = dart_stroke.upper()
                            else:
                                prev_dart_stroke = dart_stroke

                            # If there is cheating in progress
                            if len(magickey) > 0:
                                ktype = ['num', 'alpha']
                            else:
                                ktype = []

                            ##### INPUT #######
                            if players[actual_player].computer:
                                # PNJ
                                dart_stroke = rpi.listen_inputs(ktype,
                                     ['PLAYERBUTTON', 'GAMEBUTTON', 'BACKUPBUTTON',
                                      'TOGGLEFULLSCREEN', 'resize', 'JOKER', 'CHEAT', 'double-click', 'MISS',
                                      'VOLUME-UP', 'VOLUME-DOWN', 'VOLUME-MUTE', 'enter', 'single-click', 'escape', 'space'],
                                      context='game', timeout=pnj_time, video_process=played_video, sound_process=played_sound)
                                if dart_stroke is False :    # Time out reached : PNJ has to play
                                    PnJ = game.pnj_score(players, actual_player, players[actual_player].level, player_launch)
                                    if PnJ == 'PNE' or PnJ == 'TB' :    # Simplier to treate TB here than on each game, considered as MISS
                                        dart_stroke = 'MISS'
                                    else:
                                        dart_stroke = PnJ
                            elif game.time > 0:
                                dart_stroke = rpi.listen_inputs(ktype,
                                     ['PLAYERBUTTON', 'GAMEBUTTON', 'BACKUPBUTTON',
                                      'TOGGLEFULLSCREEN', 'resize', 'JOKER', 'CHEAT', 'double-click', 'MISS',
                                      'VOLUME-UP', 'VOLUME-DOWN', 'VOLUME-MUTE', 'enter', 'single-click', 'escape', 'space', 'special'],
                                      context='game', timeout=game.time, video_process=played_video, sound_process=played_sound)

                                if dart_stroke is False:
                                    logs.debug(f"Timeout {game.time}")
                                    pre_dart = game.pre_dart_check(players, actual_round, actual_player, player_launch)
                                    ClickZones = game.refresh_game_screen(players, actual_round, game.max_round, game.nb_darts - player_launch + 1,
                                                game.nb_darts, game.logo, game.headers, actual_player, OnScreenButtons=config_globals['onscreenbuttons'],
                                                Set=Set, MaxSet=nb_sets)
                                    if light_target and game_is_ok_for_color:
                                        dispatcher.publish('Background', limit=['TARGET', 'STRIP', 'OTHER'])
                                    else:
                                        dispatcher.publish('off', limit=['TARGET', 'STRIP', 'OTHER'])

                                    if rpi.target_leds != '':
                                        dispatcher.publish('goal', rpi.target_leds, limit=['TARGET', 'STRIP', 'OTHER'])
                                    if rpi.target_leds_blink != '':
                                        dispatcher.publish('blink', rpi.target_leds_blink, limit=['TARGET', 'STRIP', 'OTHER'])

                                    continue
                            else:
                                dart_stroke = rpi.listen_inputs(ktype,
                                     ['PLAYERBUTTON', 'GAMEBUTTON', 'BACKUPBUTTON',
                                      'TOGGLEFULLSCREEN', 'resize', 'JOKER', 'CHEAT', 'DEBUG', 'double-click', 'MISS',
                                      'VOLUME-UP', 'VOLUME-DOWN', 'VOLUME-MUTE', 'enter', 'single-click', 'escape', 'space', 'special'],
                                      context='game',
                                      events=[(wait_event_time, 'LIGHT', ['LIGHT_NEXTPLAYER']), \
                                              (wait_event_time * 2, 'SOUND', 'snoring'), \
                                              (wait_event_time * 2, 'DMD', 'insults')],
                                      firstname=players[actual_player].name, video_process=played_video, sound_process=played_sound)

                                # Unexpected button pressed
                                if dart_stroke in ('BTN_LEFT', 'BTN_RIGHT', 'BTN_UP', 'BTN_DOWN', 'BTN_CPTPLAYER'):
                                    rpi.strobe_toys(['LIGHT_NAVIGATE', 'LIGHT_VALIDATE'], iterations=2)
                                    continue
                                if dart_stroke == 'BTN_VALIDATE':
                                    dart_stroke = 'MISS'

                            ##### INPUT #######

                            # Check Mouse input first
                            if ClickZones:
                                Clicked = display.is_clicked(ClickZones[0], dart_stroke)
                                if Clicked:
                                    dart_stroke = Clicked

                            # If at this stage dart_stroke is still a tuple, we loop again (clicked on screen)
                            if isinstance(dart_stroke, tuple):
                                logs.debug("Stop clicking nowhere !")
                                continue

                            # Backup turn on first round => NO !!
                            #if dart_stroke in ['BTN_BACK', 'BACKUPBUTTON'] and actual_player == 0 and actual_round == 1 and player_launch == 1:
                            #    logs.warning("Backup Turn is disabled on first round of first player ! Naughty you !")
                            #    continue

                            # Toggle full-screen or resize
                            elif dart_stroke in ['TOGGLEFULLSCREEN', 'resize']:
                                if dart_stroke == 'TOGGLEFULLSCREEN':
                                    display.create_screen(True, Font=config_globals['font'])
                                else:
                                    display.create_screen(False, rpi.newresolution)
                                ClickZones = game.refresh_game_screen(players, actual_round, game.max_round,
                                                game.nb_darts - player_launch + 1, game.nb_darts,
                                                game.logo, game.headers, actual_player, OnScreenButtons=config_globals['onscreenbuttons'],
                                                Set=Set, MaxSet=nb_sets)

                            # Adjust volume
                            elif dart_stroke in ['BTN_PLUS', 'VOLUME-UP', 'VOLUME-MUTE', 'BTN_VOLUME_UP', 'BTN_MINUS', 'VOLUME-DOWN', 'BTN_VOLUME_DOWN', 'BTN_VOLUME_MUTE']:
                                display.adjust_volume(dart_stroke)
                            # If you hit on keyboard a value, like T20, it is stored in a variable "magickey".
                            # This is great for debugging pyDarts. Or cheating !
                            elif dart_stroke == 'CHEAT':
                                magickey = 'MAGIC!'
                            elif magickey == 'MAGIC!' and dart_stroke in ['S', 'D', 'T', 'R', 's', 'd', 't', 'r' ]:
                                magickey = str(dart_stroke)
                            # Try to override backup button when trying to press a bullseye
                            elif magickey and magickey != 'MAGIC!' and dart_stroke in ['BTN_BACK', 'BACKUPBUTTON', 'BTN_CANCEL']:
                                magickey += 'B'
                            elif magickey and magickey != 'MAGIC!' and str(dart_stroke) in ['b', 'B', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']:
                                magickey += str(dart_stroke)
                            else:
                                # S18, D20... BTN_*
                                break

                        if dart_stroke == 'DEBUG': # by Manu enterring game debug mode
                            logs.debug(f"Using 'd' key for sending game debug property")
                            # mode debug game uniquement si develloper et game ready
                            if not hasattr(game, 'debug_info'):
                                logs.debug(f"game not ready for using debug mode")
                                continue
                            if game.debug_info is True:
                                logs.debug(f"game use debug mode (True)")
                                if hasattr(game, 'actual_round'):
                                    logs.error(f"game overwrite: actual_round ({actual_round}) = {game.actual_round}")
                                    actual_round = game.actual_round #overwrite actual_round
                                if hasattr(game, 'player_launch'):
                                    logs.error(f"game overwrite: player_launch ({player_launch}) = {game.player_launch}")
                                    player_launch = game.player_launch #overwrite player_launch
                                if hasattr(game,'actual_player'):
                                    logs.error(f"game overwrite: actual_player ({actual_player}) = {game.actual_player}")
                                    actual_player = game.actual_player #overwrite actual_player
                                continue
                            else:
                                logs.debug(f"game don't use debug mode (False)")
                        # If magickey is set and you hit enter - it's validated - similar to JOKER but without random
                        if dart_stroke == 'enter' and len(magickey) > 0:
                            # If you hit R21, it jump directly to round 21, for instance
                            if magickey[:1] in ['r', 'R']:
                                actual_round = int(magickey[1:])
                                logs.debug(f"Jumping to round : {actual_round}")
                                magickey = ''
                                continue
                            # Otherwise we keep what you pressed as a valid hit (cheating)
                            dart_stroke = magickey.upper()
                            logs.debug(f"Not fair to cheat nasty boy ! Get this : {dart_stroke}")
                            magickey = ''

                        # Rewrite by a random hit (when pressing 'r' Joker key)
                        if dart_stroke == 'JOKER':
                            # Transfer ConfigKeys to new list
                            RandList = list(ConfigKeys)
                            # remove buttons from list to prevent missing dart, going back a turn,
                            # skipping a turn or closing game (pop with None arg remove only if exists)
                            if 'PLAYERBUTTON' in RandList:RandList.remove('PLAYERBUTTON')
                            if 'GAMEBUTTON' in RandList:RandList.remove('GAMEBUTTON')
                            if 'BACKUPBUTTON' in RandList:RandList.remove('BACKUPBUTTON')
                            if 'EXTRABUTTON' in RandList:RandList.remove('EXTRABUTTON')
                            if 'SHOCKSENSOR' in RandList:RandList.remove('SHOCKSENSOR')
                            if 'MISSDART' in RandList:RandList.remove('MISSDART')
                            RandList.append('MISS')
                            # Try to choose random value from ConfigKeys
                            try:
                                dart_stroke = random.choice(list(RandList)).upper()
                                logs.debug(f"Looking up for a random hit... Lucky guy ! {dart_stroke}")
                            except Exception as e:
                                dart_stroke = 'S20'
                                logs.warning(f"Unable to get a random hit. Your board is probably not calibrated ! I give you a {dart_stroke}.")
                                logs.debug(f"Looking up for a random hit... Lucky guy ! {dart_stroke}")

                        # What did we play ?
                        logs.debug(f"Input restrained is : {dart_stroke}")

                        # Send dart_stroke to server if player has played
                        if net_status is not None:
                            ret = net_client.play(actual_round, actual_player, player_launch, dart_stroke)
                            if ret is not None:
                                dart_stroke = 'TIMEOUT'

                    else:
                        # Else its a net game and it's our turn to wait from network !
                        logs.debug("Waiting for remote player (Player {} and Round {})...".format(actual_player, actual_round))
                        dart_stroke = str(net_client.wait_someone_play(actual_round, actual_player, player_launch))
                        while dart_stroke is False:
                            sleep(0.2)
                            dart_stroke = net_client.wait_someone_play(actual_round, actual_player, player_launch)

                        if dart_stroke == 'FINALPLAYERBUTTON':
                            dart_stroke = 'PLAYERBUTTON'
                        elif light_segment:
                            dispatcher.publish('stroke', dart_stroke.upper(), limit=['TARGET', 'STRIP', 'OTHER', 'LIGHT', 'STROBE'])

                    if dart_stroke in ['BTN_BACK', 'BACKUPBUTTON'] and back_count < 3:
                        # Simulate BTN_CANCEL or BTN_GAMEBUTTON
                        # 2 x BTN_BACK = BTN_CANCEL
                        # 3 x BTN_BACK = BTN_GAMEBUTTON
                        if actual_round == 1 and actual_player == 0 and player_launch == 1:
                            back_count = 3
                        else:
                            back_count += 1
                        dart_stroke = f"BTN_BACK{back_count}"

                    # GAMEBUTTON button pressed : game interrupted
                    if dart_stroke in ['escape', 'GAMEBUTTON', 'BTN_CANCEL', 'BTN_GAMEBUTTON', 'BTN_BACK3', 'BTN_CANCEL2', 'TIMEOUT']:
                        if dart_stroke == 'TIMEOUT':
                            logs.debug(f"Timeout from player {actual_player}")
                            # Dispacth messages
                            dispatcher.publish('timeout', limit=['TARGET', 'STRIP', 'OTHER'])
                            dmd.send_text(Lang.translate('timeout'))

                            display.message([Lang.translate('timeout')], None, 'menu-ko', 'middle', 'big')
                        else:
                            logs.debug("Who has pushed the Game Button ?")

                            # Dispacth messages
                            dispatcher.publish('interrupt', limit=['TARGET', 'STRIP', 'OTHER'])
                            dmd.send_text(Lang.translate('Game interrupted'))

                            display.message([Lang.translate('Game interrupted')], None, 'menu-white', 'middle', 'big', bg_color='menu-warning')

                        # Terminate match
                        match_done = True
                        set_done = True
                        interrupted = True
                        last_game_screen = None
                        cupdate.send_infos(logs, Game, players_count, game_options, Config.rpi_version, Config.rpi_serial, "canceled", competition_mode, play_id, version=version)
                        continue

                    # CANCEL button ppressed : back to 1st dart of same player
                    if dart_stroke in ['BTN_CANCEL', 'BTN_BACK2']:
                        logs.debug("Who has pushed the Cancel Button ?")

                        # Dispacth messages
                        dispatcher.publish('round_cancel', limit=['TARGET', 'STRIP', 'OTHER'])
                        dmd.send_text(Lang.translate('Backup Turn !'))
                        display.message([Lang.translate('Backup Turn !')], None, None, 'middle', 'big')

                        try :
                            RestoreSession = game.restore_round(1)
                        except:
                            RestoreSession = None

                        if RestoreSession is not None:
                            players = deepcopy(RestoreSession)
                            game.refresh_stats(players, actual_round)

                        player_launch = 1
                        continue

                    # BACK button ppressed : back to previous dart
                    if dart_stroke in ['BTN_BACK1']:
                        logs.debug("Who has pushed the Back Button ?")
                        # Impossible cases
                        if player_launch == 1 and actual_round == 1 and actual_player == 0:
                            pass

                        try:
                            RestoreSession = game.restore_round(1 + (player_launch + 1) % 3)
                            if RestoreSession is not None:
                                players = deepcopy(RestoreSession)
                                game.refresh_stats(players, actual_round)

                                # Dispacth messages
                                dispatcher.publish('bounce_out', limit=['TARGET', 'STRIP', 'OTHER'])
                                dmd.send_text(Lang.translate('Bounce out !'))
                                display.message([Lang.translate('Bounce out !')], None, None, 'middle', 'big')

                                logs.debug("restore_round {}, player_launch={}, actual_player={}, actual_round={}".format(1 + (actual_round + 1) % 3,player_launch,actual_player,actual_round))
                                if player_launch == 1:
                                    # Back to last round of previous player
                                    # player_launch = 3
                                    if actual_player == 0:
                                        # Back to previous round
                                        actual_round -= 1
                                        actual_player = players_count - 1
                                    else:
                                        actual_player -= 1
                                else :
                                    player_launch -= 1

                                del RestoreSession
                        except:
                            dmd.send_text(Lang.translate('Not available !'))
                            display.message([Lang.translate('Not available !')], None, None, 'middle', 'big')
                            logs.error("restore_round unavailable for this game !")
                        continue

                    # INFO : From here the dart_stroke should be something included in config file keys, or it loop again.
                    # Print error and loop again if key has not been found in config file
                    if dart_stroke not in ConfigKeys and dart_stroke not in ('MISS', 'PLAYERBUTTONFIRST', 'PLAYERBUTTON', 'BTN_NEXTPLAYER'):
                        logs.error(f"Key \"{dart_stroke}\" must exists in your local config file and it has not been found. We recommand you to calibrate your board again.")
                        logs.debug("Jumping back to start of the loop.")
                        continue

                    # EARLY PLAYERBUTTON PRESSED
                    if dart_stroke in ['BTN_NEXTPLAYER', 'PLAYERBUTTON'] and player_launch <= game.nb_darts:
                        logs.debug("You pushed Playerbutton early... Hum !")
                        try:
                            early_player_button = game.early_player_button(players, actual_player, actual_round)
                        except Exception as error:
                            logs.error(f"EARLYPLAYERBUTTON is not handled properly by this game. Error was {error}")
                            early_player_button = 1

                        for i in range(0, game.nb_darts - player_launch):
                            try :
                                game.backup_round(players, player_launch)
                            except:
                                pass

                        if early_player_button != 0 and post_dart != 3:
                            if releasedartstime == 0:
                                dart_stroke = 'PLAYERBUTTONFIRST'
                                dart_stroke = 'PLAYERBUTTON'

                    # Other button than BACKUP : reinit counter
                    back_count = 0

                    # Post Darts Checks (len()< 4 : To avoid buttons) / Miss allowed
                    if dart_stroke in ConfigKeys and len(dart_stroke) < 5:
                        threads = []
                        logs.debug(f"You pushed {dart_stroke}")

                        players[actual_player].add_histo(dart_stroke)
                        # POST DART CHECKS
                        #
                        # Return codes are:
                        #  1 - Jump to next player immediately
                        #  2 - Game is over
                        #  3 - There is a winner (self.winner must hold winner id)
                        #  4 - The player is not allowed to play (jump to next player)
                        logs.debug(f"Key {dart_stroke} found in config file.")
                        #handler = {'return_code': 0, 'message': None, 'show': None, 'sound': None, 'lights': None,
                        #           'strobe': None, 'speech': None, 'speech_speed': None, 'announcement': None, 'take_shot': None}
                        handler = game.post_dart_check(dart_stroke.upper(), players, actual_round, actual_player, player_launch)
                        logs.debug(f"handler received : {handler}")

                        if not hasattr(game, "refresh_game_screen"):
                            display.refresh_scores(players, actual_player, refresh=True)

                        if type(handler) is int:
                            post_dart = handler
                            handler = game.init_handler()
                            handler['post_dart'] = post_dart
                        else:
                            post_dart = handler['return_code']

                        played_sound = None
                        played_video = None

                        if handler['take_shot'] is not None:
                            # Cheeeeese
                            if camera is not None:
                                try:
                                    camera.action(f"{Game}_{play_id}", f"{players[actual_player].name}_r{actual_round}d{player_launch}_{dart_stroke}")
                                except Exception as ex:
                                    print(f"{ex}")

                        if game.display_dmd():
                            if handler['dmd'] is not None:
                                logs.debug(f"Send dmd : {handler['dmd']}")
                                dmd.send_text(handler['dmd'])
                            else:
                                logs.debug(f"Send dmd : {player_launch},{dart_stroke}")
                                dmd.send_score(player_launch, dart_stroke)

                        next_handler = True
                        if handler['event'] is not None:
                            next_handler = False
                            threads += dispatcher.publish(handler['event'])
                        else:
                            event = None
                            dartStroke = dart_stroke.upper()
                            if handler['show'] is not None:
                                if all(x == 'T20' for x in handler['show'][0]):
                                    dartStroke = '180'
                            if post_dart in [0, 1, 2] and light_segment:
                                threads += dispatcher.publish('stroke', dartStroke, limit=['TARGET', 'STRIP', 'OTHER', 'STROBE', 'LIGHT'])

                        if handler['video'] is not None:    # and not competition_mode:
                            logs.debug(f"video_player.play_video({handler['video']}")
                            if not image_player.show_image(handler['video'], handler['sound']):     
                                played_video = video_player.play_video(File.get_full_filename(handler['video'], 'videos'))
                                # Gere le son après la vidéo muette
                                if handler['sound'] is not None:
                                    logs.debug(f"display.play_sound({handler['sound']})")
                                    played_sound = display.play_sound(handler['sound'])

                        elif handler['show'] is not None and not competition_mode:
                            logs.debug(f"video_player.play_show({handler['show'][0]}, {handler['show'][1]}, {handler['show'][2]})")
                            if not image_player.show_image(handler['show'][1], handler['sound']):                                
                                played_video = video_player.play_show(handler['show'][0], handler['show'][1], handler['show'][2])
                                if played_video is None:
                                    if handler['sound'] is not None:
                                        played_sound = display.play_sound(handler['sound'])
                        else:
                            if handler['message'] is not None and len(handler['message']) > 0:
                                display.message([handler['message']], 0, None, 'middle', 'big')

                            if handler['sound'] is not None:
                                logs.debug(f"display.play_sound({handler['sound']})")
                                played_sound = display.play_sound(handler['sound'])
                            elif handler['speech'] is not None:
                                logs.debug(f"speech {handler['speech']} ({handler['speech_speed']})")
                                if handler['speech_speed'] is not None:
                                    display.speech(handler['speech'], speed=handler['speech_speed'])
                                else:
                                    display.speech(handler['speech'])
                        

                        if post_dart != 1:
                            # Winner
                            # Display score in differents ways depending on options
                            if hasattr(game, "display_hit") and callable(game.display_hit) :
                                game.display_hit(ClickZones, players, actual_player, player_launch, dart_stroke)
                            else:
                                if player_launch == game.nb_darts:
                                    ClickZones = game.refresh_game_screen(players, actual_round, game.max_round,
                                                game.nb_darts - player_launch, game.nb_darts, game.logo,
                                                game.headers, actual_player, OnScreenButtons=config_globals['onscreenbuttons'],
                                                Set=Set, MaxSet=nb_sets)

                                # Useless if winner or not wanted for the game
                                if print_dartstroke and game.display_segment() and post_dart < 3:
                                    if os.path.isfile('{}/{}'.format(Config.dartsStrokeDir, dart_stroke)):
                                        display.message(' ', None, None, 'middle', 'huge', f'valeurs/{dart_stroke}.png')
                                    else:
                                        display.message([dart_stroke], None, None, 'middle', 'huge')

                        if threads is not None and len(threads) > 0:
                            for thread in threads:
                                thread.join()
                    # MISSDART BUTTON PRESSED
                    # early_player_button for Golf
                    elif early_player_button != 4 or dart_stroke == 'MISS':
                        logs.debug(f"Missed that dart : {early_player_button}!")
                        # Show message on Raspydarts dmd
                        dmd.send_text(Lang.translate('Missed !'))
                        if light_segment:
                            dispatcher.publish('miss', dart_stroke.upper(), limit=['TARGET', 'STRIP', 'OTHER'])

                        try:
                            missed_dart = game.miss_button(players, actual_player, actual_round, player_launch)
                            if hasattr(game, "display_hit") and callable(game.display_hit):
                                game.display_hit(ClickZones, players, actual_player, player_launch, 'MISS')

                            if early_player_button > 0 and post_dart != 3:
                                for i in range(1, game.nb_darts - player_launch + 1):
                                    game.miss_button(players, actual_player, actual_round, player_launch + i)
                                    if hasattr(game, "display_hit") and callable(game.display_hit):
                                        game.display_hit(ClickZones, players, actual_player, player_launch, 'MISS')
                                player_launch = game.nb_darts
                            if player_launch == game.nb_darts:
                                ClickZones = game.refresh_game_screen(players, actual_round, game.max_round,
                                            game.nb_darts - player_launch, game.nb_darts, game.logo,
                                            game.headers, actual_player, OnScreenButtons=config_globals['onscreenbuttons'],
                                            Set=Set, MaxSet=nb_sets)

                        except Exception as e:
                            logs.error("MISSDART is not handled properly by this game. Error was {}".format(e))
                            # Show message on screen
                            display.message([Lang.translate('Missed !')], None, None, 'middle', 'big')
                    else:
                        # Go to next_player
                        player_launch = game.nb_darts

                    # DISPLAY RELEASE DARTS IF SOLO ENABLED
                    if  (releasedartstime > 0
                            and (player_launch == game.nb_darts or (dart_stroke in ('BTN_NEXTPLAYER', 'PLAYERBUTTON') and player_launch < game.nb_darts))
                            and post_dart not in (2,3)):
                        rpi.light_toys(['LIGHT_LASER'], False)
                        dispatcher.publish('release', limit=['TARGET', 'STRIP', 'OTHER'])
                        if releasedartstime > 0:
                            dmd.send_text(Lang.translate("release-darts"))
                            display.message([Lang.translate('release-darts')], releasedartstime, None, 'middle', 'big')

                    """
                    Need a bit of clarification
                    """
                    # WAIT For Player Button... (MISS AND PLAYERBUTTON are voluntarily absent of this list)
                    if (
                          (net_status is None or players[actual_player].name in local_players)
                          and releasedartstime == 0
                          and (player_launch == game.nb_darts or post_dart == 1 or early_player_button == 1)
                          and post_dart != 2
                          and post_dart != 3
                          or dart_stroke == 'PLAYERBUTTONFIRST'
                       ):
                        dart_stroke = 'PLAYERBUTTONFIRST'
                        rpi.light_toys(['LIGHT_NEXTPLAYER', 'LIGHT_BACK'], False)
                        ClickZones = game.refresh_game_screen(players, actual_round, game.max_round, 0, game.nb_darts, game.logo, game.headers,
                                    actual_player, OnScreenButtons=config_globals['onscreenbuttons'],
                                    Set=Set, MaxSet=nb_sets)

                        if net_status is None:
                            display.press_player(Lang.translate('release-darts-and-press-player'))
                            dispatcher.publish('release', limit=['TARGET', 'STRIP', 'OTHER'])
                        rpi.light_toys(['LIGHT_LASER'], False)

                        # Game context, wait for PLAYERBUTTON only...
                        while dart_stroke not in ('PLAYERBUTTON', 'BTN_NEXTPLAYER', 'BTN_VALIDATE') and net_status is None:
                            logs.debug("Waiting for player to push PLAYERBUTTON...")
                            if players[actual_player].computer:
                                logs.debug("Player is computer...")
                                dart_stroke = rpi.listen_inputs(['num', 'alpha', 'fx', 'arrows'],
                                            ['escape', 'GAMEBUTTON', 'PLAYERBUTTON', 'single-click'],
                                                context='game',
                                                timeout=pnj_time, video_process=played_video, sound_process=played_sound
                                            )
                                if dart_stroke is False:
                                    dart_stroke = 'PLAYERBUTTON'
                            else:
                                dart_stroke = rpi.listen_inputs(['num', 'alpha', 'fx', 'arrows'],
                                            ['PLAYERBUTTON', 'single-click'],
                                            context='game',
                                            events=[(350, 'STROBE', ['LIGHT_NEXTPLAYER']), (wait_event_time, 'EVENT', 'wait'), \
                                                    (wait_event_time * 2, 'SOUND', 'snoring')], video_process=played_video, sound_process=played_sound)

                            logs.debug(f'dart_stroke = {dart_stroke}')
                            logs.debug(f'ClickZones = {ClickZones}')
                            if ClickZones:
                                Clicked = display.is_clicked(ClickZones[0], dart_stroke)
                                if Clicked:
                                    dart_stroke = Clicked

                            # L'utilisateur demande la fin de la partie sur le joueur ordinateur
                            if dart_stroke in ('BTN_GAMEBUTTON', 'GAMEBUTTON', 'BTN_CANCEL', 'TIMEOUT'):
                                break

                        if net_status is not None:
                            if net_client.play(actual_round, actual_player, player_launch, 'FINALPLAYERBUTTON') == 'TIMEOUT':
                                break

                    # OR Wait that the REMOTE player has pushed PLAYERBUTTON (Net game only) (MISS AND PLAYERBUTTON are voluntarily absent of this list)
                    elif (
                             net_status is not None
                             and players[actual_player].name not in local_players
                             and releasedartstime == 0
                             and (player_launch == game.nb_darts or post_dart == 1 or early_player_button == 1)
                             and post_dart != 2
                             and post_dart != 3
                             or dart_stroke == 'PLAYERBUTTONFIRST'
                          ):
                        #game.refresh_game_screen(players, actual_round, game.max_round, 0, game.nb_darts, game.logo, game.headers,
                        #        actual_player, OnScreenButtons=config_globals['onscreenbuttons'],
                        #        Set=Set, MaxSet=nb_sets)
                        display.press_player(Lang.translate('press-player-remote'), 'menu-alternate')
                        # Else its a net game and it's our turn to wait from network !
                        logs.debug("Waiting for remote player to push the FINALPLAYERBUTTON...")
                        # Wait to receive PLAYERBUTTON
                        #net_client.wait_someone_play(actual_round, actual_player, player_launch, 'FINALPLAYERBUTTON')
                        # If received, rewrite to PLAYERBUTTON for client
                        dart_stroke = 'PLAYERBUTTON'

                else:
                    # If not allowed to play (pre_dart = 4)
                    # Force BACKUPBUTTON again (double BACKUPTURN) if someone pressed BackupButton and that the previous player is not allowed to play neither
                    if prev_dart_stroke in ['BTN_BACK', 'BACKUPBUTTON']:
                        dart_stroke = prev_dart_stroke
                    else:
                        dart_stroke = 'PLAYERBUTTON'

                dispatcher.publish('off', limit=['TARGET', 'STRIP', 'OTHER'])
                #
                # Step 2 : All the differents possibilities
                #

                logs.debug(f"At this stage, post_dart returns {post_dart}, early_player_button is {early_player_button}, and missed_dart is {missed_dart}")
                logs.debug("Memo: 0: nothing special, 1: jump to next player,  2: game over, 3: victory, 4: current player not allowed to play")

                # Is there a winner after this round ?
                if actual_player + 1 >= players_count and (player_launch >= game.nb_darts or pre_dart == 4):
                    # post_round_check return id of winner
                    post_round_handler = game.post_round_check(players, actual_round, actual_player)
                    logs.debug(f"At this stage, post_round returns {post_round_handler}")
                    if type(post_round_handler) is int:
                        post_round = post_round_handler
                        post_round_handler = game.init_handler()
                        post_round_handler['post_round'] = post_round
                    else:
                        post_round = post_round_handler['return_code']

                # Maybe draw
                if post_round is None:
                    best_scores = []
                    set_winner = ""
                    # Find max score
                    for player in players: best_scores.append(player.score)
                    for player in players:
                        if player.score == max(best_scores):
                            set_winner += ("," if set_winner != "" else "") + str(player.name)
                    set_done = True                    
                        
                # Victory
                elif post_round >= 0:
                    # Set win
                    players[actual_player].sets += 1
                    set_winner = post_round
                    set_done = True
                    Sets[Set][3] = game.get_player_name(players, set_winner)
                    Sets[Set][5] = game.get_darts_thrown(players, set_winner)

                elif post_dart == 3 or early_player_button == 3 or missed_dart == 3:
                    # Set win
                    players[actual_player].sets += 1
                    set_winner = game.winner
                    logs.debug("Set won by {}".format(set_winner))
                    set_done = True
                    Sets[Set][3] = game.get_player_name(players, set_winner)
                    Sets[Set][5] = game.get_darts_thrown(players, set_winner)

                # Game Over
                elif post_dart == 2 or early_player_button == 2 or missed_dart == 2 or post_round == -1:
                    logs.debug("Last round reached. No winner ...")

                    # Dispacth messages
                    dispatcher.publish('gameover', limit=['TARGET', 'STRIP', 'OTHER'])
                    dmd.send_text(Lang.translate('last-round-reached'))

                    display.play_sound('whatamess')
                    display.message([Lang.translate('last-round-reached')], None, None, 'middle', 'big')

                    # Terminate match
                    set_done = True
                elif post_round_handler['announcement'] is not None:
                    dmd.send_text(post_round_handler['announcement'])
                    display.message([post_round_handler['announcement']], 0, None, 'middle', 'big')
                    display.speech(post_round_handler['announcement'], speed=post_round_handler['speech_speed'])

                if not match_done and not set_done:
                    # Next hit, please !
                    if not game.free_launch:
                        player_launch += 1

                    # Next Player ?
                    if player_launch > game.nb_darts or post_dart in (1, 4) or dart_stroke == 'PLAYERBUTTON':
                        if played_sound is not None:
                            logs.debug(f"Waif for end of sound")
                            display.wait_end_sound(played_sound)

                        if not players[actual_player].computer:
                            rpi.light_toys(['LIGHT_LASER'])
                        # dont show/play next player if a player is not allowed to play
                        if pre_dart != 4:
                            dispatcher.publish('nextplayer', players[actual_player].name, limit=['TARGET', 'STRIP', 'OTHER', 'LIGHT', 'STROBE'])
                            if handler['announcement'] is not None:
                                logs.debug(f"announcement {handler['announcement']} ({handler['speech_speed']})")
                                dmd.send_text(handler['announcement'])
                                display.message([handler['announcement']], 0, None, 'middle', 'big')
                                display.speech(handler['announcement'], speed=handler['speech_speed'])
                            else:
                                played_sound = display.play_sound('next_player', wait_finish=wait_finish, duration=sound_duration)

                        actual_player += 1
                        player_launch = 1

                    # Next Round ? - Only jump to next round if there is no victory, no match end (give more accurate stats)
                    if actual_player >= players_count:
                        actual_player = 0
                        actual_round += 1

                elif not interrupted:
                    cupdate.send_infos(logs, Game, players_count, game_options, Config.rpi_version, Config.rpi_serial, "finished", competition_mode, play_id, version=version)
                else:
                    cupdate.send_infos(logs, Game, players_count, game_options, Config.rpi_version, Config.rpi_serial, "interrupt", competition_mode, play_id, version=version)
                    last_game_screen = None

            # Set Done
            rpi.light_toys(['LIGHT_LASER'], False)
            i = 0
            Sets[Set][2] = datetime.datetime.now()
            Sets[Set][4] = actual_round

            if nb_sets == 1:
                match_done = True
            else:
                for player in players:
                    if player.sets == nb_sets:
                        match_done = True
                        game.winner = player.ident
                    i += 1

            if not interrupted:
                if set_winner is not None:
                    if type(set_winner) is str and set_winner.find(',') > 0:
                        logs.debug("Draw by {}".format(set_winner))
                    else:
                        Sets[Set][5] = game.get_darts_thrown(players, set_winner)
                        logs.debug("Set {} won by {}".format(Set, game.get_player_name(players, set_winner)))

                if match_done or nb_sets == 1:
                    if set_winner is not None:
                        logs.debug("And the winner is...")
                        if type(set_winner) is str and set_winner.find(',') > 0:
                            txtwinner = "{} : {}".format(Lang.translate('winner'), set_winner)
                        else:
                            txtwinner = "{} : {}".format(Lang.translate('winner'), game.get_player_name(players, set_winner))

                        #display.message([txtwinner], None, None, 'middle', 'big', bg_color='menu-ok')
                        display.set_end_of_game_winner(txtwinner)
                        dmd.send_text(txtwinner)
                        dispatcher.publish('winner', limit=['TARGET', 'STRIP', 'OTHER', 'LIGHT', 'STROBE'])
                        rpi.light_toys(['LIGHT_CELEBRATION'], delay=int(config_advanced['victory-celebration-delay']))
                        if type(set_winner) is str and set_winner.find(',') > 0:
                            display.sound_end_game(set_winner)
                        else:
                            display.sound_end_game(game.get_player_name(players, set_winner))
                    else:
                        logs.debug("No winner")
                        txtwinner = Lang.translate('nowinner')
                        #display.message([txtwinner], None, None, 'middle', 'big', bg_color='menu-warning')
                        display.set_end_of_game_winner(txtwinner)
                        dmd.send_text(txtwinner)
                        
                    camera.show_qr_code_for_pictures_videos()
                          
                    if nb_sets > 1:
                        last_game_screen = display.display_sets(Sets, end_of_game=match_done)
                    else:
                        last_game_screen = game.refresh_game_screen(players, actual_round, game.max_round, game.nb_darts - player_launch + 1,
                                game.nb_darts, game.logo, game.headers, actual_player, OnScreenButtons=config_globals['onscreenbuttons'], end_of_game=True)
                    logs.debug(f"You choosed {last_game_screen} nb_sets={nb_sets}")
                    if last_game_screen == 'startagain':
                        stats_screen = 'startagain'
                    else:
                        if net_status in ('YOUARESLAVE', 'YOUAREMASTER') or competition_mode:
                            video_player.set_level(Config.get_value('SectionGlobals', 'videos'))
                            image_player.set_level(Config.get_value('SectionGlobals', 'videos'))

                else:
                    if set_winner is not None:
                        # Set won by ...set_winner
                        txtwinner = f"{Lang.translate('setwinneris')} {game.get_player_name(players, set_winner)}"
                        logs.debug(f"txtwinner = {txtwinner}")
                        dispatcher.publish('setwinner', limit=['TARGET', 'STRIP', 'OTHER', 'LIGHT', 'STROBE'])
                        dmd.send_text(txtwinner)
                        rpi.light_toys(['LIGHT_CELEBRATION'], delay=int(config_advanced['set-celebration-delay']))
                        display.set_end_of_game_winner(txtwinner)
                        display.speech(txtwinner)

                        display.play_sound('set_victory', duration=sound_duration)
                        
                        camera.show_qr_code_for_pictures_videos()

                        last_game_screen = game.refresh_game_screen(players, actual_round, game.max_round, game.nb_darts - player_launch + 1,
                            game.nb_darts, game.logo, game.headers, actual_player, OnScreenButtons=config_globals['onscreenbuttons'], endOfSet=[Sets, players[set_winner].name],
                            Set=Set, MaxSet=nb_sets)
                    else:         
                        camera.show_qr_code_for_pictures_videos()
                        
                        last_game_screen = game.refresh_game_screen(players, actual_round, game.max_round, game.nb_darts - player_launch + 1,
                            game.nb_darts, game.logo, game.headers, actual_player, OnScreenButtons=config_globals['onscreenbuttons'], Set=Set, MaxSet=nb_sets)

                    logs.debug(f"You choosed {last_game_screen} nb_sets={nb_sets}")

                    if net_status == 'YOUAREMASTER':
                        display.display_sets(Sets, end_of_game=match_done)
                    elif net_status == 'YOUARESLAVE':
                        display.display_sets(Sets, end_of_game=match_done, wait=False)
                    else:
                        display.display_sets(Sets, end_of_game=match_done)


                    set_done = False
                    set_winner = None
                    interrupted = False
                    # Round init
                    actual_round = 1
                    # Player Launch Init
                    player_launch = 1
                    # Actual Player Init
                    actual_player = 0
                    # Shutown leds
                    rpi.target_leds = ''
                    rpi.target_leds_blink = ''
                    # Dart Stroke Init
                    dart_stroke = None
                    # Increment the number of Match done
                    match_qty += 1
                    # Backup of the Hit for a usage in following round
                    prev_dart_stroke = None
                    # Increase set
                    Set += 1
                    Sets.append([Set + 1, datetime.datetime.now(), None, -1, 0, 0])

                    logs.debug("config_globals['keeporder']={}".format(config_globals['keeporder']))
                    if not config_globals['keeporder'] or net_status is not None:
                        try:
                            game.next_set_order(players)
                        except Exception as exception:
                            logs.error("Unable to order players from previous results. Error was {exception}")

                    for player in players:
                        player.new_set()
                    if net_status == 'YOUAREMASTER':
                        net_client.next_set(",".join([player.name for player in players]))
                    elif net_status == 'YOUARESLAVE':
                        all_players = net_client.wait_next_set(Set)

            else:
                if net_status in ('YOUARESLAVE', 'YOUAREMASTER') or competition_mode:
                    video_player.set_level(Config.get_value('SectionGlobals', 'videos'))
                    image_player.set_level(Config.get_value('SectionGlobals', 'videos'))
                  
        camera.close_qr_popup()                    
        
        display.file_class.reset_theme(Config.get_value('SectionGlobals', 'colorset'))
        display.define_constants(True, Font=config_globals['font'])
        display.init_colorset()
        display.reset_background()
        # Match Done
        if game_type not in ('restart', 'quit', 'shutdown'):
            ###############
            # MATCH IS OVER
            ###############

            # Quit if it was a network game
            logs.debug("This game is over")
            if net_status is not None:
                net_client.close_host()

            # On eteint la cible si besoin
            dispatcher.publish('off', limit=['TARGET', 'STRIP', 'OTHER'])

            # Grab stats from the game and write them in local DB
            if last_game_screen == 'stats':
                rpi.light_toys(['LIGHT_NEXTPLAYER', 'LIGHT_BACK'], False)
                rpi.light_toys(['LIGHT_NAVIGATE'])

                for player in players :
                    try:
                        display.heat_map(player.name, player.get_histo())
                    except Exception as e:
                        logs.error("Problem displaying stats")
                try:
                    game.game_stats(players, actual_round, scores)
                except Exception as e:
                    logs.error("Problem inserting stats")

                try:
                    first = True
                    for record in game.game_records:
                        # Get Stats for this game only
                        stats_data = scores.get_score_table(record, game.game_records[record], True)
                        # Display stats for this game
                        stats_screen = display.display_records(stats_data, record, scores.game_name, scores.game_options, True)
                        # Quit menu
                        if stats_screen in ('startagain', 'menu'):
                            break
                        # Get Stats for this type of game (with same options)
                        stats_data = scores.get_score_table(record, game.game_records[record])
                        # Display stats for this kind of game
                        stats_screen = display.display_records(stats_data, record, scores.game_name, scores.game_options)
                        # Quit menu
                        if stats_screen in ('startagain', 'menu'):
                            break
                except Exception as exception:
                    stats_screen = 'escape'
                    logs.error(f"Problem displaying Stats table with screen.")
                    logs.error(f"DisplayRecords method : {exception}")

            # Exiting if it was direct_play mode and that the user pressed escape
            if stats_screen == 'escape' and direct_play:
                direct_play = False

finally:
    rpi.gpio_flush()
    # Quit or restart
    if dispatcher.target_leds and p_target.poll() is not None:
        dispatcher.target_leds = False

    if dispatcher.strip_leds and p_strip.poll() is not None:
        dispatcher.strip_leds = False

    rpi.light_toys(['LIGHT_NEXTPLAYER', 'LIGHT_BACK', 'LIGHT_CELEBRATION', 'LIGHT_NAVIGATE'], \
            False)

    display.message(["Shutting down servers"], wait=0, refresh=True)

    logs.debug("Sending quit signal to external servers")
    if game_type == 'shutdown':
        # Volontary exit : play leds animation
        dispatcher.publish('quit', ack=True, limit=['TARGET', 'STRIP', 'DMD', 'OTHER'])
        sleep(1)

    #if display.thread is not None:
     #   display.thread.join()

    if game_type == 'quit':
        if display.fullscreen and debuglevel == 2:
             display.create_screen(True, False)
             display.display_background()
             display.update_screen()
             logs.debug("Actived by debuglevel == 2 : no FULLSCREEN when EXIT")
        dispatcher.publish('quit', ack=True, limit=['TARGET', 'STRIP'])
        sleep(1)
        logs.debug("Stop TARGETLEDS and STRIPLEDS when EXIT")
        logs.debug("Exit")
    elif game_type == 'shutdown':
        import subprocess
        logs.debug("Shutdown")
        dmd.shutdown()
        subprocess.call(['poweroff'], shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elif game_type == 'restart':
        try:
            f = open("restart", "w", encoding="utf-8")
            f.write("")
            f.close()
            logs.debug("Restart")
        except:
            logs.debug("Unable to create restart file")
