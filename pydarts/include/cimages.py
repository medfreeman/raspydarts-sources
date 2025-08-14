#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Class used to show images
"""
import pygame
#import tkinter as tk
#import threading
import time

class Images():
    """
    Module used to show images
    """

    def __init__(self, logs, c_file, level=0, display=None):
        self.logs = logs
        self.level = int(level)
        self.file = c_file
        self.display = display

    def set_level(self, level):
        """
        Set image level (same as video)
        """
        self.logs.debug(f"Set image level to {level}")
        self.level = int(level)

    def set_display(self, display):
        self.display = display
        
    def show_image(self, hit, sound, wait=1000):
        image = self.display.file_class.get_full_filename(hit, 'images')
        if image is not None :
            screen_width, screen_height = self.display.screen.get_size()
            self.display.display_image(image, 0, 0, screen_width, screen_height, Scale=True, center_x=True, center_y=True)
            self.display.update_screen()
            self.display.play_sound(sound)
            pygame.time.wait(wait)
            self.display.display_background()
            return True
        return False

    def play_show(self, darts, hit, play_special=False):
        if self.level < 1:
            return None
        
        image = None
        if 'X' not in darts and None not in darts:
            image = self.special_move(darts[0], darts[1], darts[2], play_special)
            if image is not None:
                self.show_image(self.file.get_full_filename(image, 'images'))

        if image is None:   # and hit in ('SB', 'DB'):
            image = self.file.get_full_filename(file_name=hit, file_type='videos')

        if image is None and hit in ('SB', 'DB', 'T20', 'T19', 'T18', 'T17'):
            image = self.file.get_full_filename(file_name='big_score', file_type='images')

        return None

    def dart_value(self, dart, mult=False):
        """
        Extract number from dart stroke
        """
        if dart == 'SB':
            return 25

        if dart == 'DB':
            return 50

        multiplier = 1
        if mult:
            if dart[0] == 'D':
                multiplier = 2
            elif dart[0] == 'T':
                multiplier = 3

        return int(dart[1::]) * multiplier

    def special_move(self, dart1, dart2, dart3, play_special):
        """
        Is ther any special video according to special move ?
        """
        special_move = None
        darts = [dart1.upper(), dart2.upper(), dart3.upper()]
        try:
            sorted_darts = darts
            sorted_darts.sort(key=self.dart_value)
        except: # pylint: disable=bare-except
            sorted_darts = []

        somme = 0
        for dart in darts:
            if dart == 'SB':
                somme += 25
            elif dart == 'DB':
                somme += 50
            elif dart is not None and dart[0] in ['S', 'D', 'T']:
                somme += self.dart_value(dart, True)

        self.logs.debug(f"Search for move ({play_special}/{self.level}) : {sorted_darts}")

        if all(x == 'T20' for x in darts):
            special_move = 'MAXIMUM_TON_80'

        elif play_special and self.level == 2:

            # DEVIL = S6 - S6 - S6
            if all(x == 'S6' for x in darts):
                special_move = 'DEVIL'

            # TRIPLE DEVIL = T6 - T6 - T6
            elif all(x == 'T6' for x in darts):
                special_move = 'DEVIL_TRIPLE'

            # BREAKFAST (CHIPS/CLASSIC) = S5 - S20 - S1 (peu importe l'ordre)
            elif sorted_darts == ['S1', 'S5', 'S20']:
                special_move = 'BREAKFAST'

            # CHAMPAGNE BREAKFAST (GRAND SLAM) = T5 - T1 - T20 (peu importe l'ordre)
            elif sorted_darts == ['T1', 'T5', 'T20']:
                special_move = 'CHAMPAGNE_BREAKFAST'

            # ROUND OF TERMS = T1 - T1 - T1
            elif dart1[0:1] == 'T' and dart2[0:1] == 'T' and dart3[0:1] == 'T':
                special_move = 'ROUND_OF_TERMS'

            # BAG (BUCKET) OF NAIL = S1 - S1- S1
            elif all(x == 'S1' for x in darts):
                special_move = 'BUCKET_OF_NAIL'

            # NOT OLD = S5 - S20 - S12 (peu importe l'ordre)
            elif sorted_darts == ['S5', 'S12', 'S20']:
                special_move = 'NOT_OLD'

        if special_move is not None:
            return special_move

        if all(x is None for x in darts):
            special_move = 'WHITE_HORSE'

        # BLACK HAT = DB - DB - DB
        elif all(x == 'DB' for x in darts):
            special_move = 'BLACK_HAT_THREE_IN_THE_BLACK'

        # RED HAT = SB - SB - SB
        elif all(x == 'SB' for x in darts):
            special_move = 'RED_HAT'

        # HAT TRICK = SB - DB - SB (3 bulls peu importe lesquelles)
        elif dart1 in ['SB', 'DB'] and dart2 in ['SB', 'DB'] and dart3 in ['SB', 'DB']:
            special_move = 'HAT_TRICK'

        # THREE IN A BED = 3 fois le meme segment
        elif all(x == dart1 for x in darts):
            special_move = 'THREE_IN_A_BED'

        # LOW TON = tot >= 100 & <= 150
        elif 99 < somme < 151:
            special_move = 'LOW_TON'

        # HIGH TON = tot >= 151 & <= 179
        elif 150 < somme < 180:
            special_move = 'HIGH_TON'

        # BAIL OUT = La 3eme flechette marque un triple eleve
        elif dart3 in ['T20', 'T19', 'T18', 'T17'] and play_special and self.level == 2:
            special_move = 'BAIL_OUT'

        return special_move
