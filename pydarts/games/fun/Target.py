# -*- coding: utf-8 -*-
# Game by ... LaDite - 
########
import random
from include import cplayer
from include import cgame
#

############
# Game Variables
############

OPTIONS = {'theme': 'default', 'max_round': 10, 'winscore': 10, 'simple50' : False}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'Target.png'
HEADERS = ['D1', 'D2', 'D3', '', 'Round', '', 'Target'] # Columns headers - Must be a string
VERSION = '1.00'

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return nb_players >= 1 and nb_players <= 12, VERSION, 12
    
class CPlayerExtended(cplayer.Player):
    '''
    Exetended player class
    '''
    def __init__(self, ident, config):
        super(CPlayerExtended, self).__init__(ident, config)
        # Extend the basic players property with your own here
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record] = '0'

class Game(cgame.Game):
    '''
    Target game class
    '''
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.game_records = GAME_RECORDS
        self.nb_darts = NB_DARTS
        self.logo = LOGO
        self.headers = HEADERS
        self.options = options
        #  Get the maximum round number
        self.max_round = int(options['max_round'])
        if self.max_round > 15 :
                self.max_round = 15
        
        self.simple = options['simple50']

        if self.simple:
            self.score_map.update({'SB': 50})
        else:
            self.score_map.update({'SB': 25})

        self.winner = None
        self.dart = 0
        self.translate = self.display.lang.translate
        self.winscore = int(options['winscore'])
        self.target = [30,32,33,34,36,38,39,40,42,45,48,51,54,57,60,50]
        self.cible = random.shuffle(self.target)  ### melange la liste
        self.test = 0
         
    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        '''
        Actions done before each dart throw - for example, check if the player is allowed to play
        '''
        return_code = 0

        if player_launch == 1:
            players[actual_player].reset_darts()

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.log('ERROR', f'Handicap failed : {exception}')

            for player in players:
                # Init score
                player.score = 0
                player.reset_rounds(self.max_round)   
                

        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            players[actual_player].pre_play_score = players[actual_player].score

            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0, 7):
                players[actual_player].columns.append(['', 'int'])
              
            if actual_player == 0:
                ## supprime le dernier element de la liste target 
                self.cible = self.target[-1]     
                self.target.pop()

            players[actual_player].columns[6] = (self.cible, 'int')
                        
        # Clean next boxes
        for i in range(player_launch - 1, self.nb_darts):
            players[actual_player].columns[i] = ('', 'int')
            
        reste = self.cible - players[actual_player].round_points
        self.possible_hits = self.search_possibilities(reste, player_launch)
        print(f"pre_dart : possible_hits = {self.possible_hits}")

        # Display if there is a suggestion to display 
        if len(self.possible_hits) >= 1:
            players[actual_player].columns[player_launch - 1] = (self.possible_hits[0], 'str', 'game-silver')
        if len(self.possible_hits) >= 2:
            players[actual_player].columns[player_launch] = (self.possible_hits[1], 'str', 'game-silver')
        if len(self.possible_hits) >= 3:
            players[actual_player].columns[player_launch + 1] = (self.possible_hits[2], 'str', 'game-silver')

        self.rpi.set_target_leds('|'.join([f'{key}#{self.colors[0]}' \
                    for key in self.possible_hits]))
        
        players[actual_player].columns[6] = (self.cible, 'int')
        
            
            #self.early_player_button(players, actual_player, actual_round)
            #return 1

        # Print debug output
        self.logs.log('DEBUG', self.infos)
        return return_code

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        '''
        Function run after each dart throw - for example, add points to player
        '''

        handler = self.init_handler()
        handler['show'] = (players[actual_player].darts, hit, True)
        handler['sound'] = hit

        score = self.score_map[hit]
        
        players[actual_player].add_dart(actual_round, player_launch, hit, score=score)
        
        #players[actual_player].score += score
        players[actual_player].round_points += score
        
        #teste si le round_points EST EGAL A cible
        if player_launch == 1 :
                print('player_launch == 1 - ajoute un bonus +2')
                if players[actual_player].round_points == self.cible :
                        players[actual_player].score += 3
                        handler['sound'] = 'target_hit'
                        handler['return_code'] = 1
                elif players[actual_player].round_points > self.cible and actual_round <= self.max_round and actual_player != self.nb_players - 1 :
                        handler['sound'] = 'target_toohigh'
                        handler['return_code'] = 1
                ### ajout + "and actual_round <= self.max_round and actual_player != self.nb_players - 1 :" a la ligne precedente
                elif players[actual_player].round_points > self.cible and actual_round == self.max_round and actual_player == self.nb_players - 1 :
                        handler['sound'] = 'target_toohigh'
                        handler['return_code'] = 3
        elif player_launch == 2 :
                print('player_launch == 2 - ajoute un bonus +1')
                if players[actual_player].round_points == self.cible :
                        players[actual_player].score += 2
                        handler['sound'] = 'target_hit'
                        handler['return_code'] = 1
                elif players[actual_player].round_points > self.cible and actual_round <= self.max_round and actual_player != self.nb_players - 1 :
                        handler['sound'] = 'target_toohigh'
                        handler['return_code'] = 1
                ### ajout + "and actual_round <= self.max_round and actual_player != self.nb_players - 1 :" a la ligne precedente
                elif players[actual_player].round_points > self.cible and actual_round == self.max_round and actual_player == self.nb_players - 1 :
                        handler['sound'] = 'target_toohigh'
                        handler['return_code'] = 3        
        elif player_launch == 3 :
                print('player_launch == 3 - pas de bonus')
                if players[actual_player].round_points == self.cible :
                        players[actual_player].score += 1
                        handler['sound'] = 'target_hit'
                        handler['return_code'] = 1
                elif players[actual_player].round_points > self.cible :
                        handler['sound'] = 'target_toohigh'
                        handler['return_code'] = 1  
                elif players[actual_player].round_points < self.cible :
                        handler['sound'] = 'target_rate'
                        handler['return_code'] = 1  

        
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')
        players[actual_player].columns[player_launch - 1] = (score, 'int')

        if players[actual_player].round_points > self.cible :
                players[actual_player].columns[6] = ('cross-mark', 'image')
        elif players[actual_player].round_points == self.cible :
                players[actual_player].columns[6] = ('check-mark', 'image')
        elif players[actual_player].round_points < self.cible and player_launch == 3 :
                players[actual_player].columns[6] = ('cross-mark', 'image')
        
                
        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)
        self.refresh_stats(players, actual_round)

        # test for a winner
        if players[actual_player].score >= self.winscore :
            self.winner =  players[actual_player].ident
            handler['return_code'] = 3
            
       
        # Check for end of game (no more rounds to play)
        if actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and player_launch == int(self.nb_darts):
            self.infos += f"Last round reached ({actual_round}){self.lf}"
            handler['return_code'] = 2
        
        reste = self.cible - players[actual_player].round_points
        self.possible_hits = self.search_possibilities(reste, player_launch + 1)
         ### test en cas ou pas de possibilite de gagner avec la 3eme fleches
        print(f"post_dart possible_hits = {self.possible_hits}")
        if len(self.possible_hits) <= 0 and handler['return_code'] != 2 and handler['return_code'] != 3:
            print('possible hit = 0')
            handler['return_code'] = 1 #nextplayer

        return handler

    def miss_button(self, players, actual_player, actual_round, player_launch):
        '''
        Miss button
        '''
        return_code = 0
        print('miss')
        # Il faudra checker le vainqueur ici aussi
        if players[actual_player].score >= self.winscore :
            self.winner =  players[actual_player].ident
            return_code = 3
        elif actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and player_launch == int(self.nb_darts):
            self.infos += f"Last round reached ({actual_round}){self.lf}"
            return_code = 2
        elif players[actual_player].round_points < self.cible :
            self.display.play_sound('target_rate')
            players[actual_player].columns[player_launch-1] = ('MISS', 'str')
            self.display.play_sound('treasure_crane_jaune')
            players[actual_player].darts_thrown += 1
            self.display.message(['Fléchette suivante'], None, None, 'middle', 'big')
        
        return return_code

    def early_player_button(self, players, actual_player, actual_round):
        '''
        Function launched when the  put player button before having launched all his darts
        '''
        return 0
        # Jump to next player by default
#        return_code = 1
#        print('early ')
     
#        if players[actual_player].round_points < self.cible :
#                self.display.play_sound('target_rate')
                #handler['sound'] = 'target_rate'
#        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')
        #players[actual_player].columns[player_launch - 1] = (score, 'int')    ### a remettre apres test
        #return 1

    def post_round_check(self, players, actual_round, actual_player):
        '''
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        '''
        if actual_round >= self.max_round:
            print('postround - fin des X tours')
        return -2
    

    def get_score(self, player):
        '''
        Return score of player
        '''
        return player.score

    def next_set_order(self, players, actual_player):
        '''
        Sort players for next set
        '''
        players.sort(key=self.get_score)

    def refresh_stats(self, players, actual_round):
        '''
        refresh players' stats
        '''
        for player in players:
            player.stats['Points Per Round'] = player.avg(actual_round)
            player.stats['Points Per Dart'] = player.show_ppd()


              
    def search_possibilities(self, score, player_launch):        
        '''
        Get possibilities in ordre to light leds
        '''
        #/!\return value must be iterable and must have at least 3 values
        return_value = []
        # 1 dart possibility
        for hit, key in self.score_map.items():
            if ((score == key)):
                return [hit.upper()]
               
        # 2 darts possibilities - Player must have at least two darts left
        if player_launch in (1, 2):
            for hit, key in self.score_map.items():
                if ((score > key and hit[:1] in ('D', 'T'))):
                    firstrest = score - key
                    for hit2, key in self.score_map.items():
                        if firstrest == key:
                            return [hit2.upper(), hit.upper()]
        # 3 darts possibilities - Player must have at least 3 darts left
        if player_launch == 1:
            for hit, key in self.score_map.items():
                if ((score > key and hit[:1] in ('D', 'T'))):
                    firstrest = score - key
                    for hit3, key3 in self.score_map.items():
                        if firstrest > key3:
                            secondrest = firstrest - key3
                            for hit4, key4 in self.score_map.items():
                                if secondrest == key4:
                                    return [hit3.upper(), hit4.upper(), hit.upper()]
        return return_value
