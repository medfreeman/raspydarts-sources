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

OPTIONS = {'theme': 'default', 'max_round': 8, 'simple50' : False, 'alea' : False, 'flch3' : False}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'Sabotage.png'
HEADERS = ['D1', 'D2', 'D3', '', 'Round', '', '-ADVS'] # Columns headers - Must be a string
VERSION = '1.00'

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return nb_players >= 2 and nb_players <= 12, VERSION, 12
    
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
    Sabotage game class
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
        self.simple = options['simple50']

        if self.simple:
            self.score_map.update({'SB': 50})
        else:
            self.score_map.update({'SB': 25})

        self.alea = options['alea']
        self.flch3 = options['flch3']
        self.winner = None
        self.dart = 0
        self.moyenne = 0
        self.translate = self.display.lang.translate
         
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
                self.logs.error(f'Handicap failed : {exception}')

            for player in players:
                # Init score
                player.score = 0
                #player.alive = True

        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            players[actual_player].pre_play_score = players[actual_player].score

            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0, 7):
                players[actual_player].columns.append(['', 'int'])
            if actual_round == 1 and actual_player == 0:
                for player in players:
                    player.reset_rounds(self.max_round)
            self.moyenne = 0

        # Clean next boxes
        for i in range(player_launch - 1, self.nb_darts):
            players[actual_player].columns[i] = ('', 'int')

        # Print debug output
        self.logs.debug(self.infos)
        return return_code

    def best_score(self, players):
        '''
        Find the winner
        Only one player with best score
        '''
        best_player = None
        best_score = None
        best_count = 0
        for player in players:
            if best_score is None or player.score > best_score:
                best_score = player.score
                best_player = player.ident
                best_count = 1
                self.logs.debug(\
                        f'Best found : {best_score} / Count={best_count} / player = {best_player}')
            elif player.score == best_score:
                best_count += 1

        self.logs.debug(\
                f'Best score : {best_score} / Count={best_count} / Player = {best_player}')

        if best_count == 1:
            return best_player
        return -1

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        '''
        Function run after each dart throw - for example, add points to player
        '''

        handler = self.init_handler()
        handler['show'] = (players[actual_player].darts, hit, True)
        self.display.sound_for_touch(hit)
        
        #handler['sound'] = hit

        score = self.score_map[hit]
        
        players[actual_player].add_dart(actual_round, player_launch, hit, score=score)
        
        players[actual_player].score += score
        players[actual_player].round_points += score
        players[actual_player].points += score
        
        if self.flch3 :
                ### calcul la moyenne des points        
                self.moyenne = int(round(players[actual_player].round_points /3))
        elif not self.flch3 :
                if player_launch == 3 :
                        ### score de la 3eme fleche a decompter      
                        self.moyenne = self.score_map[hit]
                else : 
                        ### fixe la variable a 0 si pas la 3eme fleche
                        self.moyenne = 0
                
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')
        players[actual_player].columns[player_launch - 1] = (score, 'int')
        players[actual_player].columns[6] = (self.moyenne, 'int')
                
        if player_launch == 3 and not self.alea :
                ### retire les points a tous les advs
                for player in players :
                        if player.ident != actual_player :
                                handler['sound'] = 'sabotage_hahaha'
                                player.score = player.score - self.moyenne
                                
        elif player_launch == 3 and self.alea :
                ### retire les points a un joueur choisi aleatoirement
                index_joueur = []
                for player in players :
                        if player.ident != players[actual_player].ident :
                                index_joueur.append(player.ident)
      
                choix_joueur = random.choice(index_joueur)  
                ### recupere le nom du joueur choisi
                for player in players :
                        if player.ident == choix_joueur :
                                name = player.name
             
                for player in players :
                        if player.ident == choix_joueur :
                                player.score = player.score - self.moyenne

                self.display.message([
                    f"{name} : {self.translate('Sabotage-penalite')}"], 1000, None, 'middle', 'big') 
                handler['sound'] = 'sabotage_hahaha'
                      

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)
        self.refresh_stats(players, actual_round)

        # Check for end of game (no more rounds to play)
        if player_launch == self.nb_darts and actual_round >= self.max_round \
                and actual_player == len(players) - 1:
            winner = self.best_score(players)
            if winner > 0:
                self.winner = winner
                handler['return_code'] = 3
            else:
                # No winner : last round reached
                handler['return_code'] = 2

        # Time for shot or video ?
        handler['take_shot'] = self.time_to_take_shot_or_video(hit)
        #handler['return_code'] = return_code

        return handler

    def miss_button(self, players, actual_player, actual_round, player_launch):
        '''
        Miss button
        '''
        print('miss')
        players[actual_player].columns[6] = (self.moyenne, 'int')
        players[actual_player].columns[player_launch-1] = ('MISS', 'str')
        self.display.play_sound('miss')
        players[actual_player].darts_thrown += 1

    def early_player_button(self, players, actual_player, actual_round):
        '''
        Function launched when the  put player button before having launched all his darts
        '''
        # Jump to next player by default
        return_code = 1

        if self.moyenne > 0:
            if not self.alea :
                # deduit self.moyenne aux advs 
                for player in players :
                    if player.ident != actual_player :
                        player.score = player.score - self.moyenne
            elif self.alea :
                index_joueur = []
                for player in players :
                        if player.ident != players[actual_player].ident :
                                index_joueur.append(player.ident)
      
                choix_joueur = random.choice(index_joueur)  
                ### recupere le nom du joueur choisi
                for player in players :
                        if player.ident == choix_joueur :
                                name = player.name
                                        
                for player in players :
                        if player.ident == choix_joueur :
                                player.score = player.score - self.moyenne
            
                self.display.message([
                    f"{name} : {self.translate('Sabotage-penalite')}"], 1000, None, 'middle', 'big')            
            # play sound
            #self.display.play_sound('sabotage_hahaha')
            handler['sound'] = 'sabotage_hahaha'


    def post_round_check(self, players, actual_round, actual_player):
        '''
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        '''
        if actual_round >= self.max_round:
            self.winner = self.check_winner(players)
            if self.winner is not None:
                self.logs.debug(f'winner is {winner}')
                return self.winner
            elif actual_round >= self.max_round:
                # Last round, last player
                return self.best_score(players)
        return -2

    def check_winner(self, players):
        nb_winner = 0
        winner = None
        for i in range(0, len(players)):
            if players[i].alive:
                winner = i
                nb_winner += 1

        if nb_winner == 1:
            return winner
        return None

    def get_score(self, player):
        '''
        Return score of player
        '''
        return player.score

    def next_set_order(self, players):
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
