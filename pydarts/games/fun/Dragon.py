# -*- coding: utf-8 -*-
"""
Game by LaDite
"""

import random
from include import cplayer
from include import cgame

#
VERSION = '1.00'
LOGO = 'Dragon.png' # Background image - relative to images folder
HEADERS = ['D1', 'D2', 'D3', '', 'Round', '', ''] # Columns headers - Must be a string
OPTIONS = {'theme': 'default', 'max_round': 8, 'Time': 500} # Dictionnay of options
NB_DARTS = 3
GAME_RECORDS = {'Score': 'DESC', 'Reached Score': 'DESC', 'Hits': 'DESC'}

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return nb_players <= 12, VERSION, 12

class CPlayerExtended(cplayer.Player):
    """
    Extended Player class
    """
    def __init__(self, ident, nb_columns, interior=False):
        super().__init__(ident, nb_columns, interior)
        #The score the player has to hit
        self.actual_hit = 1
        self.next = 1
        self.next1 = 0
        self.next2 = 0
        self.next3 = 0
        self.next4 = 0
        self.targets_list = []
        self.leds_blink = []
        # Init Player Records to zero
        for game_record in GAME_RECORDS:
            self.stats[game_record] = '0'

class Game(cgame.Game):
    """
    dragon game class
    """
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.logo = LOGO
        self.headers = HEADERS
        self.game_records = GAME_RECORDS
        self.nb_darts = NB_DARTS
        self.options = options
        self.nb_players = nb_players
        self.max_round = int(options['max_round'])
        #  Get the maximum round number
        # For rpi
        self.rpi = rpi
        self.dmd = dmd

        self.time = int(options['Time'])

        self.first = True
        
    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        After eah row : valid launch ? winner ? ...
        """
        score = 0
        
        play_hit = False
        players[actual_player].add_dart(actual_round, player_launch, hit)

        return_code = 0
        self.infos = ''

       
        if hit[:1] == 'S' :
            multi = 1
        elif hit[:1] == 'D' :
            multi = 2
        elif hit[:1] == 'T' :
            multi = 3
        
        if hit+'#green' in self.targets_list :
            ### voir si necessaire
            #players[actual_player].increment_hits(hit)
            
            ### Quelle partie du corps du dragon touchee
            if str(hit[1:]) == str(self.corps[0]) :
                score = 1 * multi
            
            elif str(hit[1:]) == str(self.corps[1]) :
                score = 2 * multi 

            elif str(hit[1:]) == str(self.corps[2]) :
                score = 3 * multi    

            elif str(hit[1:]) == str(self.corps[3]) :
                score = 5 * multi   
                
            self.display.play_sound('pan-touche')
                        
                        
        elif hit+'#green' in self.targets_list_tete :            
            ### voir si necessaire
            #players[actual_player].increment_hits(hit)
            
            score = 10 * multi  

            self.display.play_sound('pan-cloche')

        else :
            self.display.play_sound('plouf')    
        
        players[actual_player].score += score
        players[actual_player].round_points += score
        players[actual_player].points += score

        # Store what he played in the table
        players[actual_player].columns[player_launch - 1] = (score, 'int')
        # Store total for the round in column 6 (start from 0)
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')
        
        if play_hit:
            if super().play_show(players[actual_player].darts, hit, play_special=True):
                self.display.sound_for_touch(hit) # Play hit sound

        # Last round
        if actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and ((player_launch == self.nb_darts and return_code <= 1) or return_code == -1):
            self.infos += rf"\n/!\ Last round reached ({actual_round})\n"
            self.winner = self.check_winner(players)
            if self.winner != -1:
                self.infos += "Here is a winner"
                return_code = 3
            else:
                self.infos += "No winner"
                return_code = 2
        if return_code == -1:
            return_code = 1


        # You may want to count darts played
        players[actual_player].darts_thrown += 1

        # It is recommanded to update stats every dart thrown
        self.refresh_stats(players, actual_round)

        self.logs.log("DEBUG", self.infos)

        return return_code

    def post_round_check(self, players, actual_round, actual_player):

        if actual_round >= self.max_round and actual_player == self.nb_players - 1:
            self.infos += rf"\n/!\ Last round reached ({actual_round})\n"
            self.winner = self.check_winner(players)
            return self.winner
        else:
            return -2

    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Before each throw - update screen, display score, etc...
        """
        return_code = None
        self.infos = ''

        if player_launch == 1 :
            # Clean all next boxes
            for i in range(0, 7):
                players[actual_player].columns[i] = ('', 'txt')   
                
        # First round, first player, first dart
        if player_launch == 1 and actual_round == 1 and actual_player == 0 and self.first:
            for player in players:
                # DETERMINE LE CHIFFRE DE DEPART DES JOUEURS
                start = random.choice(self.target_order)
                player.goals = self.target_order[::]
                #index pour goals
                player.next = random.randint(0, 19)
                player.next1 = player.next - 1
                player.next2 = player.next1 - 1
                player.next3 = player.next2 - 1
                player.next4 = player.next3 - 1
               
                player.reset_darts()
                player.reset_rounds(self.max_round)


        ### passe au chiffre suivant
        players[actual_player].next += 1
        
        ### ATTRIBUE LE CORPS DU DRAGON SUIVANT LA POSITION DE SA TETE
        players[actual_player].next1 = players[actual_player].next -1
        players[actual_player].next2 = players[actual_player].next1 -1
        players[actual_player].next3 = players[actual_player].next2 -1
        players[actual_player].next4 = players[actual_player].next3 -1
        if players[actual_player].next >= len(self.target_order):
            players[actual_player].next = 0

        self.corps = [players[actual_player].goals[players[actual_player].next4] , players[actual_player].goals[players[actual_player].next3] , players[actual_player].goals[players[actual_player].next2] , players[actual_player].goals[players[actual_player].next1]]          
        self.tete = [players[actual_player].goals[players[actual_player].next]]
        
        
        led = [f'{mult}{hit}#{self.colors[0]}' for hit in self.corps for mult in ['S', 'D', 'T']]
        ledblink = [f'{mult}{hit}#{self.colors[0]}' for hit in self.tete for mult in ['S', 'D', 'T']]
        
        players[actual_player].actual_hit = players[actual_player].goals[players[actual_player].next]
        
        self.targets_list = led 
        self.targets_list_tete = ledblink

        self.rpi.set_target_leds('|'.join([f'{value}#{self.colors[0]}' \
                for value in self.targets_list]))
                
        self.rpi.set_target_leds_blink('|'.join([f'{value}#{self.colors[0]}' \
                for value in self.targets_list_tete]))        
                  

        if self.first:
            self.first = False

        return return_code

    def check_winner(self, players):
        """
        Last round : who is the winner ?
        """
        deuce = False
        best_score = -1
        best_player = -1
        for player in players:
            if player.score > best_score:
                best_score = player.score
                deuce = False #necessary to reset deuce if there is a deuce with a higher score !
                best_player = player.ident
            elif player.score == best_score:
                deuce = True
                best_player = -1
        return best_player

    def early_player_button(self, players, actual_player, actual_round):
        """
        Pushed Player Early
        """

        return_code = 1
        self.first = True
        if actual_round == self.max_round and actual_player == self.nb_players - 1:
            self.winner = self.check_winner(players)
            if self.winner != -1:
                self.infos += rf"Current winner is Player {self.winner}"
                return_code = 3
            else:
                return_code = 2
        return return_code

    def refresh_stats(self, players, actual_round):
        """
        Method to refresh players' stats
        """

        for player in players:
            player.stats['Score'] = player.score
            player.stats['Reached Score'] = player.actual_hit
            player.stats['Hits'] = player.get_total_hit()
            
    def miss_button(self, players, actual_player, actual_round, player_launch):

        players[actual_player].columns[player_launch-1] = ('MISS', 'str')
        self.display.play_sound('treasure_crane_jaune')
          
        players[actual_player].darts_thrown += 1
