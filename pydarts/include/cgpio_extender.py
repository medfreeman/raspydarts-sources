
"""
Manage MCP2307 I/O

light_buttons and toys_buttons are a dictionnary of tuples:
        {
        'TOY1': ('C3', address, 4),
        'PIN_UP': ('B2', address, 10),
        ...
        }
"""

import time
import board
import busio

from digitalio import Direction, Pull
from adafruit_mcp230xx.mcp23017 import MCP23017
from threading import Thread

LAST_BUTTON = None
COUNT_BUTTON = 0

DEFAULTS = {
    'PIN_UP': 'A0',
    'PIN_DOWN': 'A1',
    'PIN_LEFT': 'A2',
    'PIN_RIGHT': 'A3',
    'PIN_PLUS': 'A4',
    'PIN_MINUS': 'A5',
    'PIN_VALIDATE': 'A6',
    'PIN_CANCEL':'A7',
    'PIN_NEXTPLAYER':'B0',
    'PIN_BACK':'B1',
    'PIN_GAMEBUTTON':'B2',
    'PIN_VOLUME_UP':'B3',
    'PIN_VOLUME_DOWN':'B4',
    'PIN_VOLUME_MUTE':'B5',
    'PIN_CPTPLAYER':'B6',
    'PIN_MISSDART':'B7',
    'LIGHT_NEXTPLAYER':'',
    'LIGHT_BACK':'',
    'LIGHT_NAVIGATE':'',
    'LIGHT_VALIDATE':'',
    'LIGHT_LASER':'',
    'LIGHT_FLASH':'',
    'LIGHT_PLAYERS':'',
    'LIGHT_CELEBRATION':'',
    'LIGHT_CELEBRATION2':'',
    'LIGHT_LIGHT':'',
    'TOY1':'C0',
    'TOY2':'C1',
    'TOY3':'C2',
    'TOY4':'C3',
    'TOY5':'C4',
    'TOY6':'C5',
    'TOY7':'C6',
    'TOY8':'C7',
    'TOY9':'D0',
    'TOY10':'D1',
    'TOY11':'D2',
    'TOY12':'D3',
    'TOY13':'D4',
    'TOY14':'D5',
    'TOY15':'D6',
    'TOY16':'D7'
}

class Gpio_extender:
    """
    Manage MCP2307 I/O
    """

    def __init__(self, logs, buttons=None):
        """
        Init self.mcp1 and buttons
        """
        self.logs = logs
        i2c = busio.I2C(board.SCL, board.SDA)
        self.mcp1 = None
        self.mcp2 = None
        self.all_io = None

        try:
            self.mcp1 = MCP23017(i2c, address=0x20)
            self.logs.info("MCP found at 0x20")
        except:
            self.logs.info("No MCP at 0x20")

        try:
            self.mcp2 = MCP23017(i2c, address=0x21)
            self.logs.info("MCP found at 0x21")
        except:
            self.logs.info("No MCP at 0x21")

        # Make a list of all the pins (a.k.a 0-16)
        pins = []
        if self.mcp1 is not None:
            for pin in range(0, 16):
                pins.append(self.mcp1.get_pin(pin))
                # Set pin to input
                pins[pin].direction = Direction.INPUT
                pins[pin].pull = Pull.UP
            self.all_io = [f"{chr}{num}" for chr in ['A', 'B'] for num in [0, 1, 2, 3, 4, 5, 6, 7]]

            if self.mcp2 is not None:
                for pin in range(0, 16):
                    pins.append(self.mcp2.get_pin(pin))
                    # Set pin to input
                    pins[pin].direction = Direction.OUTPUT
                    pins[pin].value = 0

                for letter in ['C', 'D']:
                    for number in [0, 1, 2, 3, 4, 5, 6, 7]:
                        self.all_io.append(f"{letter}{number}")

            # Apply configuration
            if buttons:
                self.set_io(buttons)
            else:
                self.buttons_list = {}
                self.toys_list = {}
                self.pin_switcher = {}

        self.banned_button = None

    def decode(self, value):
        """
        Decode string to numeric (B3 => mcp1, address of input/output)
        """
        if value not in self.all_io:
            return None, None

        try:
            if value[:1:] in ('A', 'B'):
                pin_number = (ord(value[:1:]) - 65) * 8 + int(value[1::])
                return self.mcp1.get_pin(pin_number), pin_number
            else:
                if value[:1:] in ('C', 'D'):
                    pin_number = (ord(value[:1:]) - 67) * 8 + int(value[1::])
                    return self.mcp2.get_pin(pin_number), pin_number
                else:
                    return None, None
        except: # pylint: disable=bare-except
            return None, None

    def set_io(self, buttons):
        """
        Init self.buttons_list (list of inputs)
        Init self.toys_list (list of outputs)

        {['TOY1', 'C3', address], [],...}
        """
        self.buttons_list = {}
        self.toys_list = {}
        self.pin_switcher = {}

        if self.mcp1 is None:
            return None

        for button in buttons:
            value = buttons[button].upper()
            address, pin_number = self.decode(value)
            if address is not None:
                if button.startswith('PIN_'):
                    self.buttons_list[button] = (value, address, pin_number)
                    self.pin_switcher[pin_number] = button
                    address.direction = Direction.INPUT
                    address.pull = Pull.UP

                elif button.startswith('LIGHT_') or button.startswith('TOY'):
                    self.toys_list[button] = (value, address, pin_number)
                    address.direction = Direction.OUTPUT
                    address.value = 0

        return True

    def get_defaults(self):
        """
        Get default configuration
        """
        return DEFAULTS

    def set_defaults(self):
        """
        Set default configuration
        """
        self.set_io(DEFAULTS)

    def read_entries(self):
        """
        Read self.mcp1
        """
        global LAST_BUTTON
        global COUNT_BUTTON
        # False/0 si appuie sur le bouton
        return_value = None
        ban_value = None
        value = hex(self.mcp1.gpio)

        for pin in self.pin_switcher:
            button = self.pin_switcher.get(pin, "")
            if ((not int(value, 16) & 2**pin and button != 'PIN_MISSDART')
                or (int(value, 16) & 2**pin and button == 'PIN_MISSDART')):
                if button != self.banned_button:
                    return_value = button
                else:
                    ban_value = button

        if return_value is not None and return_value == LAST_BUTTON:
            COUNT_BUTTON += 1
            if COUNT_BUTTON > 30:
                self.banned_button = return_value
                self.logs.warning(f"Button {self.banned_button} is banned !")
        elif ban_value is None:
            COUNT_BUTTON = 0
            LAST_BUTTON = return_value
            self.banned_button = None

        return return_value

    def test_entries(self):
        """
        Read self.mcp1 and returns list of pressed buttons ['A0'[,'B1']]
        """
        # False/0 si appuie sur le bouton
        pressed_buttons = []

        for button in self.buttons_list:
            # False/0 si appuie sur le bouton
            if not self.buttons_list[button][1].value:
                # Compute A0..B7
                pressed_buttons.append(self.buttons_list[button][0])

        return pressed_buttons

    def thread_toy(self, iterations, pin, delay_on, delay_off):
        """
        Light a toy
        """
        for iteration in range(iterations):

            pin.value = not(pin.value)
            time.sleep(delay_on / 1000)

            pin.value = not(pin.value)
            if iteration + 1 < iterations:
                time.sleep(delay_off / 1000)

    def strobe_toys(self, toys, iterations=3, delay_on=10, delay_off=100):
        """
        Strobe light
        Return an array of threads
        """
        threads = []
        for toy in toys:
            try:
                element = self.toys_list.get(toy, None)
                if element is not None:
                    threads += [Thread(target=self.thread_toy, args=(iterations, element[1], delay_on, delay_off))]
                else:
                    pass
            except Exception as error: # pylint: disable=bare-except
                self.logs.error(f"Decode error for {toy} : {error}")

        for thread in threads:
            thread.start()
        return threads

    def light_toys(self, toys, light=True):
        """
        Light a toy
        """
        pins = []
        for toy in toys:
            try:
                element = self.toys_list.get(toy, None)
                if element is not None:
                    pins.append(element[1])
            except Exception as error: # pylint: disable=bare-except
                self.logs.error(f"Error during light of {toy}")
                pass

        for pin in pins :
            if light:
                pin.value = 1
            else:
                pin.value = 0
