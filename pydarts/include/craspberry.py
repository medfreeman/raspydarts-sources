#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time
import subprocess
import pygame
# For GPIO Extender
from RPi import GPIO as gpio
from . import cgpio_extender

MAX_GPIO = 27
LAST_GPIO = None
COUNT_GPIO = 0
# pylint: disable=no-member
USEREVENT = pygame.USEREVENT
# pylint: enable=no-member

gamecontext = {
          'escape' : 'GAMEBUTTON'
         ,'space' : 'PLAYERBUTTON'
         ,'+' : 'VOLUME-UP'
         ,'-' : 'VOLUME-DOWN'
         ,'[+]' : 'VOLUME-UP'
         ,'[-]' : 'VOLUME-DOWN'
         ,'b' : 'BACKUPBUTTON'
         ,'j' : 'JOKER'
         ,'c' : 'CHEAT'
         ,'m' : 'MISS'
         ,'p' : 'BACK'
         ,'x' : 'DEBUG'
         ,'g' : 'GAMEBUTTON'
         ,'u' : 'VOLUME-MUTE'
         }

numbers = {
         '0' : '0'
        ,'1' : '1'
        ,'2' : '2'
        ,'3' : '3'
        ,'4' : '4'
        ,'5' : '5'
        ,'6' : '6'
        ,'7' : '7'
        ,'8' : '8'
        ,'9' : '9'
        }

shiftnumbers = {
         'world 64' : '0'
        ,'0'        : '0'
        ,'&'        : '1'
        ,'1'        : '1'
        ,'world 73' : '2'
        ,'"'        : '3'
        ,'3'        : '3'
        ,"'"        : '4'
        ,"4"        : '4'
        ,'('        : '5'
        ,'5'        : '5'
        ,'-'        : '6'
        ,'6'        : '6'
        ,'world 72' : '7'
        ,'_'        : '8'
        ,'8'        : '8'
        ,'world 71' : '9'
        }

shiftalpha = {
         'world 64' : 'à',
         'world 71' : 'ç',
         'world 72' : 'è',
         'world 73' : 'é',
         ';':'.'
        }

shiftmath = {
        ':':':',
        '=':'+'
        }

buttons_list = ['NEXTPLAYER', 'BACK', 'GAMEBUTTON', 'VALIDATE', 'CANCEL', 'UP',
            'DOWN', 'LEFT', 'RIGHT', 'PLUS', 'MINUS', 'VOLUME_UP',
            'VOLUME_DOWN', 'VOLUME_MUTE', 'MISSDART', 'SHOCKSENSOR', 'CPTPLAYER']

events_list = {
         'LIGHT_FLASH': 1,
         'LIGHT_CELEBRATION': 2,
         'LIGHT_CELEBRATION2': 3,
         'STROBE': 4,
         'EVENT': 5,
         'SOUND': 6,
         'DMD': 7
#         'SCREEN': 7
         }

SCREENSAVER = True
try:
    subprocess.Popen(['xscreensaver-command', '-deactivate'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
except:
    SCREENSAVER = False
    
def wake_up(video_process, sound_process):
    '''
    In order to wake-up from screen saver and stop running video
    '''

    if video_process is not None:
        # Stop running video
        try:
            video_process.stdin.write(b'q')
            video_process.stdin.flush()
            video_process.stdin.close()
        except Exception as error:
            print(f"exception is {error}")

    if SCREENSAVER:
        try:
            subprocess.Popen(['xscreensaver-command', '-deactivate'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as error:
            # Maybe xscreensaver is not installed
            print(f"exception is {error}")

    if sound_process is not None:
        try:
            sound_process.stop()
        except Exception as error:
            print(f"exception is {error}")

####################
# New Fresh class that handle raspberry GPIO created by Remi D. (Reredede)
####################

class Craspberry():
    """
    Raspberry class
    """
    def __init__(self, logs, config, conf_target_led, event, t_event=None):
        """
        Init class
        """
        self.logs = logs
        self.shift = False
        self.config = config
        self.event = event

        # Usefull for GPIO usage
        gpio.setwarnings(False)
        gpio.setmode(gpio.BCM)

        # Leds configuration
        self.pin_stripled = 0
        self.nbr_stripled = 0
        self.bri_stripled = 0.5
        self.pin_targetled = 0
        self.nbr_target_leds = 0
        self.bri_targetled = 0.5
        self.leds = config.leds
        self.conf_target_led = conf_target_led
        self.target_leds = ""
        self.target_leds_blink = ""

        # Inputs/Outputs
        self.inputs = []
        self.outputs = []

        # For target detection : S12 = 1310 (13 = in / 10 = out)
        self.keys = {}
        # For button detection : NEXTPLAYER / MISSDART ...
        self.pins = {}

        # MCP buttons
        self.buttons = config.config['Raspberry']
        # List of outputs
        self.conf_outputs = config.config['Raspberry_BoardPinsOuts']
        # List of inputs
        self.conf_inputs = config.config['Raspberry_BoardPinsIns']

        self.newresolution = []
        self.banned_gpio = None

        if config.file_exists:
            # Apply configuration
            for pin_gpio in [pin for pin in self.conf_inputs.values() if pin != '']:
                self.set_inputs(pin_gpio)

            for pin_gpio in [pin for pin in self.conf_outputs.values() if pin != '']:
                self.set_outputs(pin_gpio)

            # Compute number of leds on target
            for key, value in self.conf_target_led.items():
                for led in value.split(','):
                    if led != '' and int(led) >= self.nbr_target_leds:
                        self.nbr_target_leds = int(led) + 1

            for key, value in self.leds.items():
                if key == 'pin_stripled':
                    self.pin_stripled = int(value)
                elif key == 'nbr_stripled':
                    self.nbr_stripled = int(value)
                elif key == 'bri_stripled':
                    self.bri_stripled = float(value)
                elif key == 'pin_targetled':
                    self.pin_targetled = int(value)
                elif key == 'bri_targetled':
                    self.bri_targetled = float(value)

            for segment in config.config['SectionKeys']:
                if config.config['SectionKeys'][segment] == '':
                    continue
                if segment in config.GPIO_BUTTONS_CONFIG:
                        if 0 < int(config.config['SectionKeys'][segment]) <= MAX_GPIO:
                            self.pins[segment] = int(config.config['SectionKeys'][segment])
                        else:
                            self.logs.error("Unexpected GPIO pin : {config.config['SectionKeys'][segment]}")
                elif segment in config.default_SectionKeys:
                    self.keys[config.config['SectionKeys'][segment]] = segment
                else:
                    self.logs.error(f"Unknown {segment} configuration in [SectionKeys]")

            self.reset_gpio()

        self.gpio = cgpio_extender.Gpio_extender(self.logs, self.buttons)

        # Init MCP according to configuration

        self.set_io(self.buttons)
        self.play_sound = None
        self.send_insult = None
        self.t_event = t_event
        self.sleep = False
        self.old_detection = bool(config.config['SectionAdvanced']['richard-mode'])

    def set_play_sound(self, method):
        """
        In order to play sound from here
        """
        self.play_sound = method

    def set_send_insult(self, method):
        """
        In order to send text to DMD
        """
        self.send_insult = method

    def get_max_gpio():
        """
        Get max(GPIO)
        """
        return MAX_GPIO

    def reset_gpio(self):
        """
        Init target's GPIO
        """
        for pin in self.inputs:
            gpio.setup(pin, gpio.IN)

        for pin in self.outputs:
            gpio.setup(pin, gpio.OUT)

        for pin in [pin for pin in self.pins]:
            # default : NO button, connected between GPIO and GND
            if 0 < int(self.pins[pin]) <= MAX_GPIO:
                self.logs.debug(f"GPIO {pin} set to input NC")
                gpio.setup(self.pins[pin], gpio.IN, pull_up_down=gpio.PUD_UP)

    def init_gpio(self, pins, direction):
        """
        Init GPIO
        Used for initial configuration
        """
        for pin in pins:
            if direction == 'OUT':
                gpio.setup(int(pins[pin]), gpio.OUT)
            else:
                gpio.setup(int(pins[pin]), gpio.IN)

    def set_inputs(self, pin_gpio):
        """
        Set inputs configuration
        Used for initial configuration
        Required for target detection
        """
        if pin_gpio != '' and 0 < int(pin_gpio) <= MAX_GPIO:
            self.inputs.append(int(pin_gpio))

    def set_outputs(self, pin_gpio):
        """
        Set outputs configuration
        Used for initial configuration
        Required for target detection
        """
        if pin_gpio != '' and 0 < int(pin_gpio) <= MAX_GPIO:
            self.outputs.append(int(pin_gpio))

    def set_buttons_conf(self, conf_buttons):
        """
        Set buttons configuration
        Used for initial configuration
        """
        for key in conf_buttons:
            self.buttons[key] = conf_buttons[key]

    def set_keys_conf(self, conf_keys):
        """
        Set keys configuration
        Used for initial configuration
        """
        for key in conf_keys:
            self.keys[conf_keys[key]] = key

    def set_inputs_conf(self, conf_inputs):
        """
        Set input pin's configuration
        Used for initial configuration
        """
        for key in conf_inputs:
            self.conf_inputs[key] = conf_inputs[key]
            self.config.inputs[key] = conf_inputs[key]

        self.logs.debug(f"conf_inputs[key]={conf_inputs[key]}")
        self.logs.debug(f"self.conf_inputs[key]={self.conf_inputs[key]}")
        self.logs.debug(f"self.config.inputs[key]={self.config.inputs[key]}")

    def set_outputs_conf(self, conf_outputs):
        """
        Set output pin's configuration
        """
        for key in conf_outputs:
            self.conf_outputs[key] = conf_outputs[key]
            self.config.outputs[key] = conf_outputs[key]

    def set_leds_conf(self, config_leds):
        """
        Set leds configuration
        """
        self.pin_stripled = int(config_leds['PIN_STRIPLED'])
        self.nbr_stripled = int(config_leds['NBR_STRIPLED'])
        self.bri_stripled = int(config_leds['BRI_STRIPLED'])
        self.pin_targetled = int(config_leds['PIN_TARGETLED'])
        self.bri_targetled = int(config_leds['BRI_TARGETLED'])

        self.config.config['Raspberry_Leds'] = config_leds

    def set_io(self, buttons):
        """
        set buttons
        """
        return self.gpio.set_io(buttons)

    def set_target_leds(self, valeur):
        """
        Set target leds values
        """
        self.target_leds = valeur

    def set_target_leds_blink(self, valeur):
        """
        Set target leds to blink
        """
        self.target_leds_blink = valeur

    def gpio_flush(self):
        """
        Flush GPIO values
        """
        gpio.cleanup()

    def test_target(self):
        """
        Test GPIO inputs (Target's)
        """
        gpio_input = []
        # Read segments (S1, D2, T4...)
        if self.inputs and self.outputs:
            for pinout in self.outputs:
                gpio.output(pinout, gpio.HIGH)

                for pinin in self.inputs:
                    gpio.setup(pinin, gpio.IN, pull_up_down=gpio.PUD_DOWN)
                    if gpio.input(pinin):
                        gpio_input.append(f"{pinin}{pinout}")

                gpio.output(pinout, gpio.LOW)

        if gpio_input:
            # Return all possible values
            segments = []
            if self.keys.get(gpio_input[0], None) is not None:
                segments = [self.keys.get(gpio_input[0])]

            if len(segments) == 0:
                return [1, f'ERREUR : Code : {gpio_input[0]}']
            if len(segments) > 1:
                return [2, f"ATTENTION : {'/'.join(segments)}"]
            return [0, segments[0]]

        return gpio_input

    def read_target(self):
        """
        Read GPIO inputs (Target's)
        """
        gpio_input = None
        # Read segments (S1, D2, T4...)
        if self.inputs and self.outputs:
            # Make GPIO readable and value is False / Down / 0
            #for pinin in self.inputs:
            #    gpio.setup(pinin, gpio.IN, pull_up_down=gpio.PUD_DOWN)

            # Force output to False / Down / 0
            #gpio.output(self.outputs, gpio.LOW)

            if self.old_detection:
                for pinout in self.outputs:
                    gpio.output(pinout, gpio.HIGH)

                    for pinin in self.inputs:
                        gpio.setup(pinin, gpio.IN, pull_up_down=gpio.PUD_DOWN)
                        if gpio.input(pinin):
                            gpio_input = f'{pinin}{pinout}'

                    gpio.output(pinout, gpio.LOW)
            else:
                # Make GPIO readable and value is False / Down / 0
                for pinin in self.inputs:
                    gpio.setup(pinin, gpio.IN, pull_up_down=gpio.PUD_DOWN)

                # Force output to False / Down / 0
                gpio.output(self.outputs, gpio.LOW)

                for pinout in self.outputs:
                    gpio.output(pinout, gpio.HIGH)

                    for pinin in self.inputs:
                        if gpio.input(pinin):
                            gpio_input = f'{pinin}{pinout}'

                    gpio.output(pinout, gpio.LOW)

        return self.keys.get(gpio_input, None)

    def read_buttons(self):
        """
        Read GPIO (Button's)
        """
        global COUNT_GPIO
        global LAST_GPIO

        gpio_read = None
        p_key = None
        for key in self.pins:
            if ((gpio.input(self.pins[key]) == gpio.LOW and key != 'SHOCKSENSOR')
                or
                (key == 'SHOCKSENSOR' and gpio.input(self.pins[key]) == gpio.HIGH)):
                # NO Button pressed (connected between GPIO and GND)
                # NC Piezzo case (connected between GPIO and +5V)
                if key != self.banned_gpio:
                    gpio_read = key
                else:
                    p_key = key


        if gpio_read is not None:
            if gpio_read == LAST_GPIO:
                COUNT_GPIO += 1
                if COUNT_GPIO > 30:
                    self.banned_gpio = gpio_read
                    self.logs.warning(f"Gpio {gpio_read} is banned !")
                else:
                    return gpio_read.replace('PIN_','BTN_')
            elif self.banned_gpio is None:
                LAST_GPIO = gpio_read
                return gpio_read.replace('PIN_','BTN_')
        elif p_key is None:
            LAST_GPIO = None
            COUNT_GPIO = 0
            self.banned_gpio = None
        return None

    def test_buttons(self):
        """
        Return list of pressed buttons or key pressed if any
        Used in Test Buttons Menu
        """

        if self.gpio is None:
            return 'nogpio'

        key_pressed = None

        pygame.time.set_timer(USEREVENT, 0)
        pygame.time.set_timer(USEREVENT, 10000)

        while True:

            key_pressed = self.gpio.test_entries()

            if len(key_pressed) > 0:
                self.logs.debug(f"Input debug (MCP) : {key_pressed}")
                pygame.time.set_timer(USEREVENT, 0)
                return key_pressed

            key_pressed = self.read_buttons()
            if key_pressed is None:
                key_pressed = self.keyboard_mouse(['num', 'alpha', 'fx', 'arrows'],['enter', 'tab', 'backspace', 'left shift', 'escape', 'space', 'double-click', 'single-click', 'resize'],'menue')
            else:
                self.logs.debug(f"Input debug (GPIO) : {key_pressed}")
                pygame.time.set_timer(USEREVENT, 0)
                return key_pressed

            if key_pressed:
                self.logs.debug(f"Input debug (pyGame) : {key_pressed}")
                pygame.time.set_timer(USEREVENT, 0)
                return key_pressed

            if key_pressed is False:
                return False

    def reset_timers(self):
        """
        Called after key perssed
        """
        for index in (5, 6, 7):
            pygame.time.set_timer(USEREVENT + index, 0)

    def listen_inputs(self, k_type=['num', 'alpha', 'fx', 'arrows'], 
                      specials=['enter', 'tab', 'backspace', 'left shift', 'escape', 'space', 'double-click', 'single-click', 'resize'],
                      wait_for=None, context='menus', timeout=0, light=None, events=None, 
                      firstname=None, video_process=None, sound_process=None, camera=None):
        """
        Read input : MXP, GPIO, keyboard, mouse, ...
        """

        inputs = None

        if timeout > 0:
            pygame.time.set_timer(USEREVENT, 0)
            pygame.time.set_timer(USEREVENT,timeout)

        if events is not None:
            for event in events:
                if event[1] == 'STROBE' and self.gpio is not None and event[0] > 0:
                    self.logs.debug(f"Event {event[2]} initialized every {event[0]}ms")
                    pygame.time.set_timer(USEREVENT + events_list['STROBE'], event[0])
                elif event[1] in ('EVENT', 'SOUND', 'DMD') and event[0] > 0:
                    self.logs.debug(f"Event {event[2]} initialized every {event[0]}ms")
                    pygame.time.set_timer(USEREVENT + events_list[event[1]], event[0])

        if self.sleep:
            time.sleep(self.config.delay)
            self.sleep = False
        if self.gpio is not None and light is not None:
            self.gpio.light(light)

        count = 0
        miss = 0
        while True:
            count += 1
            if count % 1000 == 0:
                count = 0
                pygame.mouse.set_visible(False)

            # Read buttons connected to GPIO
            inputs = self.read_buttons()
            if inputs and miss == 0:
                self.logs.debug(f"Input debug (GPIO) : {inputs}")
                self.reset_timers()
                wake_up(video_process, sound_process)
                if inputs in ('MISSDART', 'SHOCKSENSOR'):
                    miss = 1
                else:
                    return inputs

            # Read buttons from MCP
            if self.gpio.mcp1 is not None and miss == 0:
                if context == 'test':
                    inputs = self.gpio.test_entries()
                else:
                    inputs = self.gpio.read_entries()

                if inputs:
                    self.logs.debug(f"Input debug (ext GPIO) : {(inputs.replace('PIN_', 'BTN_') if not isinstance(inputs, list) else inputs[0].replace('PIN_', 'BTN_'))}")
                    if timeout > 0:
                        pygame.time.set_timer(USEREVENT, 0)
                    if inputs in ('PIN_LEFT', 'PIN_RIGHT', 'PIN_UP', 'PIN_DOWN', 'PIN_VALIDATE'):
                        self.gpio.strobe_toys(['LIGHT_NAVIGATE'], iterations=2)
                    if inputs in ('PIN_PLUS', 'PIN_MINUS'):
                        self.gpio.strobe_toys(['LIGHT_PLAYERS'], iterations=2)
                    self.reset_timers()
                    self.sleep = True
                    wake_up(video_process, sound_process)
                    if inputs == 'PIN_MISSDART':
                        miss = 1
                    else:
                        return (inputs.replace('PIN_', 'BTN_') if not isinstance(inputs, list) else inputs[0].replace('PIN_', 'BTN_'))

            # Read target
            if context == 'test':
                inputs = self.test_target()
            else:
                inputs = self.read_target()

            if inputs:
                self.logs.debug(f"Input debug (Serial) : {inputs}")
                self.reset_timers()
                if self.gpio is None:
                    self.sleep = True
                wake_up(video_process, sound_process)
                return inputs

            # If serial returns false, try to read keyboard
            inputs = self.keyboard_mouse(k_type, specials, context, events, firstname)
            if inputs is not None:
                self.logs.debug(f"Input debug (pyGame) : {inputs}")
                if inputs is not False:
                    wake_up(video_process, sound_process)

            # Return Serial input if expected (or if nothing expected)
            if inputs is False or (inputs is not None and (wait_for is None or str(inputs) in wait_for)):
                self.reset_timers()
                return inputs
            
            # On affiche la camera a la zone que l'on veut avec la resolution d'affichage que l'on veut
            if camera is not None:
                # On ne choisit pas une dimension (dimension native de la webcam pour les photos)
                if len(camera) == 4:
                    camera[0].show_camera(camera[1], posX=camera[2], posY=camera[3])
                # On force la dimension de la webcam
                elif len(camera) == 6:                    
                    camera[0].show_camera(camera[1], posX=camera[2], posY=camera[3], resW=camera[4], resH=camera[5])

            if miss > 10:
                return 'MISS'
            if miss > 0:
                miss += 1

    def keyboard_mouse(self, k_type, specials, context=None, wait_events=None, firstname=None):
        """ KEYBOARD & MOUSE (from pygame)
        Context can be different, dependanding from where this method is used.  So
        far : 'menus' or 'game' or 'editing'

        pygame events are consumed here
        """
        realkey = -1
        events = pygame.event.get()

        # Look for events
        for event in events:

            if event.type == USEREVENT:
                pygame.time.set_timer(USEREVENT, 0)
                return False

            if event.type == USEREVENT + 1:
                self.light_toys(['LIGHT_FLASH'], False)

            #elif event.type == USEREVENT + events_list['SCREEN']:
            #    self.t_event.set()

            elif event.type == USEREVENT + 2:
                self.light_toys(['LIGHT_CELEBRATION'], False)

            elif event.type == USEREVENT + 3:
                self.light_toys(['LIGHT_CELEBRATION2'], False)

            elif event.type == USEREVENT + events_list['STROBE'] and wait_events is not None:
                for wait_event in wait_events:
                    if wait_event[1] == 'STROBE':
                        self.gpio.strobe_toys(wait_event[2], 1)

            elif event.type == USEREVENT + events_list['EVENT'] and wait_events is not None:
                for wait_event in wait_events:
                    if wait_event[1] == 'EVENT':
                        self.event.publish(wait_event[2])

            elif event.type == USEREVENT + events_list['SOUND'] and wait_events is not None:
                for wait_event in wait_events:
                    if wait_event[1] == 'SOUND':
                        self.play_sound(wait_event[2], duration=5000)

            elif event.type == USEREVENT + events_list['DMD'] and wait_events is not None:
                for wait_event in wait_events:
                    if wait_event[1] == 'DMD':
                        self.send_insult(firstname)

            # If pyGame return Exit
            elif event.type == pygame.QUIT:
                self.logs.debug("Please exit any network game before killing pyDarts :)")
                if context in ('game', 'waitcomputer'):
                    return 'GAMEBUTTON'
                return 'escape'
            # Case of Key UP
            if event.type == pygame.KEYUP:
                if pygame.key.name(event.key) == 'left shift':
                    self.shift = False

            # Case of key DOWN
            elif event.type == pygame.KEYDOWN:
                keyname = pygame.key.name(event.key)
                unicodekey = event.dict['unicode']
                if len(keyname) == 1 and unicodekey != '':
                    keycouple = self.real_key(unicodekey, context)
                else:
                    keycouple = self.real_key(keyname, context)
                realkey = keycouple[1]  # Get pydarts translation of key

                if realkey in specials or keycouple[0] in k_type: # return special key if allowed
                    return realkey
            # Case of resizing window - must be before click or click will take
            # precedence
            elif event.type == pygame.VIDEORESIZE:
                self.newresolution = [event.w, event.h]
                return 'resize'
            # Case of MOUSE BUTTON PRESSED
            elif (event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.FINGERDOWN):
                pygame.mouse.set_visible(True)
                #on click
                if 'single-click' in specials:
                    if(event.type == pygame.FINGERDOWN):
                        w, h = pygame.display.get_surface().get_size()
                        x_finger = event.x * w
                        y_finger = event.y * h
                        position = (int(x_finger), int(y_finger))
                    else:
                        position = pygame.mouse.get_pos()
                    return position
            elif (event.type == pygame.MOUSEMOTION or  event.type == pygame.FINGERMOTION):
                pygame.mouse.set_visible(True)
        # Everything above failed, return -1 (0 is a valid char)
        return None

    def real_key(self, key_pressed, context):
        """
        Return real key pressed from keyboard
        """
        if key_pressed[0:3:2] == '[]':
            key_pressed = key_pressed[1:2:1]

        #####################
        ## IN GAME CONTEXT ##
        #####################
        if context in ('game', 'waitcomputer'):
            # In-game context
            k_value = gamecontext.get(key_pressed, None)

            if k_value is not None:
                return ['special', k_value]
        ######################
        ## EDITING CONTEXT ###
        ######################
        if key_pressed == 'f' and context == 'editing':
            return ['alpha', 'f']
        #######################################
        ## NO CONTEXT SET (Default is menus) ##
        #######################################

        if not self.shift:
            k_value = numbers.get(key_pressed, None)
            if k_value is not None:
                return ['num', int(k_value)]
            k_value = shiftalpha.get(key_pressed, None)
            if k_value is not None:
                return ['alpha', k_value]

            if key_pressed in ('*', '+', '/', '-', '='):
                return ['math', key_pressed]
        else:
            # shift
            k_value = shiftnumbers.get(key_pressed, None)
            if k_value is not None:
                return ['num', int(k_value)]

            k_value = shiftmath.get(key_pressed, None)
            if k_value is not None:
                return ['num', k_value]

        if key_pressed in ('down', 'up', 'left', 'right'):
            k_value = key_pressed
            k_type = 'arrows'
        elif key_pressed in ('escape', 'space', 'backspace', 'tab', 'left shift', 'resize'): # All other context,  space means 'space'
            k_value = key_pressed
            k_type = 'special'
            if key_pressed == 'left shift':
                self.shift = True #Enable Shift !
        elif key_pressed in ('enter', 'return'): # Enter and Return are comfunded volontarily
            k_value = 'enter'
            k_type = 'special'
        elif key_pressed in ('f', 'double-click'): # Everywhere else, 'f' and double-click means "Fullscreen"
            k_value = 'TOGGLEFULLSCREEN'
            k_type = 'special'
        # Other special chars, need to be at the end (based on length)
        elif len(key_pressed) in (2,3) and key_pressed[:1] == 'f': # Detect Fx keys
            k_value = key_pressed.upper()
            k_type = 'fx'
        else:
        # Detect any other key (simple alpha keys)
            k_value = key_pressed
            k_type = 'alpha'

        return [k_type, k_value]

    def get_user_event(self, light):
        """
        Get USER_EVENT according to light
        """
        return events_list.get(light, None)

    def light_toys(self, buttons, state=True, delay=None):
        """
        Put OFF or ON a light, and, if applicable, start a timer to OFF the light
        """
        self.logs.debug(f"light_toys : {state} : {buttons}")
        self.logs.debug(f"buttons={buttons}")
        if self.gpio is not None and buttons:
            self.gpio.light_toys(buttons, state)

            for button in buttons:
                event = self.get_user_event(button)
                if event:
                    # Reset or cancel
                    pygame.time.set_timer(USEREVENT + event, 0)
                    if state and delay:
                        pygame.time.set_timer(USEREVENT + event, delay)

    def strobe_toys(self, buttons, iterations=3, delay_on=10, delay_off=100):
        """
        Make light strobe blink times
        Return the array of threads returned by gpio.strobe_toys
        """
        if self.gpio is not None and buttons:
            return self.gpio.strobe_toys(buttons, iterations, delay_on, delay_off)
        return []

    def get_defaults(self):
        """
        In case of no GPIO
        """
        return cgpio_extender.DEFAULTS
