# -*- coding: utf-8 -*-
# Game by ... laDite!
########
import random
from include import cplayer
from include import cgame
#

############
# Game Variables
############
OPTIONS = {'theme': 'default', 'max_round': 10, 'oper1': True, 'simple50': False}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'Chaos.png'
HEADERS = ['D1', 'D2', 'D3', '', 'Round', '', ''] # Columns headers - Must be a string
VERSION = '1.00'

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return nb_players >= 1 and nb_players <= 12, VERSION, 12
    
class CPlayerExtended(cplayer.Player):
    """
    Exetended player class
    """
    def __init__(self, ident, config):
        super(CPlayerExtended, self).__init__(ident, config)
        # Extend the basic players property with your own here
        # Init Player Records to zero
        for record in GAME_RECORDS:
            self.stats[record] = '0'

class Game(cgame.Game):
    """
    Chaos game class
    """
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

        self.winner = None
        self.video_player = video_player
        self.targets = ''
        self.leds = True
        #  Penality points for a missing dart
        self.penality = 0 ###int(options['penalite']) 
        self.oper1 = options['oper1']
        self.dart1 = 'plus'
        self.dart2 = 'moins'
        self.dart3 = 'fois'
        self.div0 = 0
        self.div1 = 0
        self.div2 = 0
        self.multi0 = 0
        self.multi1 = 0
        self.multi2 = 0
        self.moins0 = 0
        self.moins1 = 0
        self.moins2 = 0
  
    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0
        
        if player_launch == 1:
            players[actual_player].reset_darts()
        
        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.error(f"Handicap failed : {exception}")

            for player in players:
                # Init score
                player.score = 0
        
        if player_launch == 1 and actual_player == 0:  
            ### tire au sort les headers          
            listedarts = ['plus', 'moins', 'fois', 'div']    
            
            self.headers[2] = random.choice(listedarts)
            if self.oper1 :
                listedarts.remove(self.headers[2])

            self.headers[1] = random.choice(listedarts)
            if self.oper1 :
                listedarts.remove(self.headers[1])

            self.headers[0] = random.choice(listedarts)
            if self.oper1 :
                listedarts.remove(self.headers[0])
            
            ### tire au sort le multiplicateur du headers
            if self.headers[0] == 'fois' :
                    multi = [2,3,4]
                    self.headers[0] = '* ' + str(random.choice(multi))
                    self.multi0 = int(self.headers[0][-1])
            if self.headers[1] == 'fois' :
                    multi = [2,3,4]
                    self.headers[1] = '* ' + str(random.choice(multi))
                    self.multi1 = int(self.headers[1][-1])
            if self.headers[2] == 'fois' :
                    multi = [2,3,4]
                    self.headers[2] = '* ' + str(random.choice(multi))
                    self.multi2 = int(self.headers[2][-1])
            
            ### tire au sort le diviseur du headers        
            if self.headers[0] == 'div' :
                    multi = [2,3,4]
                    self.headers[0] = '/ ' + str(random.choice(multi))
                    self.div0 = int(self.headers[0][-1])
            if self.headers[1] == 'div' :
                    multi = [2,3,4]
                    self.headers[1] = '/ ' + str(random.choice(multi))
                    self.div1 = int(self.headers[1][-1])
            if self.headers[2] == 'div' :
                    multi = [2,3,4]
                    self.headers[2] = '/ ' + str(random.choice(multi))
                    self.div2 = int(self.headers[2][-1])

            ### tire au sort le multiplicateur de "MOINS' du headers        
            if self.headers[0] == 'moins' :
                    multi = [1,1,2,3,4]
                    self.headers[0] = ' -*' + str(random.choice(multi))
                    self.moins0 = int(self.headers[0][-1]) *-1
                    if self.headers[0] == ' -*1':
                        self.headers[0] = 'Moins'
                    
            if self.headers[1] == 'moins' :
                    multi = [1,1,2,3,4]
                    self.headers[1] = ' -*' + str(random.choice(multi))
                    self.moins1 = int(self.headers[1][-1]) *-1
                    if self.headers[1] == ' -*1': 
                        self.headers[1] = 'Moins'
                        
            if self.headers[2] == 'moins' :
                    multi = [1,1,2,3,4]
                    self.headers[2] = ' -*' + str(random.choice(multi))
                    self.moins2 = int(self.headers[2][-1]) *-1
                    if self.headers[2] == ' -*1':
                        self.headers[2] = 'Moins'

        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            players[actual_player].pre_play_score = players[actual_player].score

            
            # Clean all next boxes
            for i in range(0,7):
                players[actual_player].columns.append(['', 'int'])
            
            if actual_round == 1 and actual_player == 0:
                for player in players:
                    player.reset_rounds(self.max_round)
 
        # Clean next boxes
        for i in range(player_launch - 1,self.nb_darts):
            players[actual_player].columns[i] = ('', 'int')
        
        # Print debug output
        self.logs.debug(self.infos)
        
        #self.rpi.set_target_leds('|'.join(self.targets))
        
        return return_code

    def pnj_score(self, players, actual_player, level, player_launch):
        """
        pnj score
        """
        letters = 'SDT'
        value = random.randint(1, 20)
        multi = ''.join(random.choice(letters) for _ in range(1))
        bull = random.randint(0, 100)
        if 85 < bull <= 95:
            return 'SB'
        if bull > 95:
            return 'DB'
        return f'{multi}{value}'

    def best_score(self, players):
        """
        Find the winner
        Only one player with best score
        """
        best_player = None
        best_score = None
        best_count = 0
        for player in players:
            if best_score is None or player.score > best_score:
                best_score = player.score
                best_player = player.ident
                best_count = 1
                self.logs.debug(\
                        f"Best found : {best_score} / Count={best_count} / player = {best_player}")
            elif player.score == best_score:
                best_count += 1

        self.logs.debug(\
                f"Best score : {best_score} / Count={best_count} / Player = {best_player}")

        if best_count == 1:
            return best_player
        return -1

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Function run after each dart throw - for example, add points to player
        """
        handler = self.init_handler()
        
        self.display.sound_for_touch(hit)

        score = 0
         
        #if (hit and actual_round < self.max_round) or (hit and actual_round == self.max_round and player_launch < 3) : 
        if (hit) :
                print('condition  1-2 fleche')
                if player_launch == 1 :
                        operat = self.headers[0][-3]
                        if operat == 'l' :
                                score = score + self.score_map[hit] 
                        elif operat == '-' or operat == 'i' :
                                score = self.score_map[hit] * self.moins0
                        elif operat == '*' :
                                score = self.score_map[hit] * self.multi0
                        elif operat == '/' :
                                score = round(self.score_map[hit] / self.div0)  
             
                if player_launch == 2 :
                        operat = self.headers[1][-3]
                        if operat == 'l' :
                                score = score + self.score_map[hit] 
                        elif operat == '-' or operat == 'i' :
                                score = self.score_map[hit] * self.moins1
                        elif operat == '*' :
                                score = self.score_map[hit] * self.multi1
                                
                        elif operat == '/' :
                                score = round(self.score_map[hit] / self.div1)     
                                
                if player_launch == 3 :
                        operat = self.headers[2][-3]
                        if operat == 'l' :
                                score = score + self.score_map[hit] 
                        elif operat == '-' or operat == 'i' :
                                score = self.score_map[hit] * self.moins2
                        elif operat == '*' :
                                score = self.score_map[hit] * self.multi2
                        elif operat == '/' :
                                score = round(self.score_map[hit] / self.div2)     

###" DERNIER TOUR
        '''
        if hit and actual_round == self.max_round and player_launch == 3 :   
                print('condition dernier tour derniere fleche')
                if player_launch == 3 :
                        operat = self.headers[2][-3]
                        if operat == 'l' :
                                score = score + self.score_map[hit] 
                        elif operat == '-' or operat == 'i' :
                                #score = self.score_map[hit] * self.moins2
                                score = self.score_map[hit] * self.moins2
                                players[actual_player].score = players[actual_player].score * self.moins2
                        elif operat == '*' :
                                #score = self.score_map[hit] * self.multi2
                                players[actual_player].score = players[actual_player].score * self.score_map[hit]
                                score = self.score_map[hit] * self.multi2
                        elif operat == '/' :
                                #score = round(self.score_map[hit] / self.div2)    
                                players[actual_player].score = players[actual_player].score / self.score_map[hit]
                                score = round(self.score_map[hit] / self.div2)   
        '''



        return_code = 0

        players[actual_player].add_dart(actual_round, player_launch, hit, score=score)
        if actual_round < self.max_round and player_launch < 3 :
            players[actual_player].score += score
        else :
            players[actual_player].score += score
        players[actual_player].round_points += score
        players[actual_player].points += score

        
        # Store what he played in the table
        players[actual_player].columns[player_launch - 1] = (score, 'int', 'game-silver')
        # Store total for the round in column 6 (start from 0)
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int', 'game-silver')
        
        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)
        self.refresh_stats(players, actual_round)
        
        # Check last round
        if player_launch == self.nb_darts and actual_round >= self.max_round \
                and actual_player == len(players) - 1:
            self.winner = self.check_winner(players)
            self.infos += f"Last round reached ({actual_round}){self.lf}"
            return_code = 2


        if self.winner is not None:
            return_code = 3

        self.logs.debug(self.infos)

        # Time for shot or video ?
        handler['take_shot'] = self.time_to_take_shot_or_video(hit)
        handler['return_code'] = return_code
        return handler
        
        #return return_code

    def miss_button(self, players, actual_player, actual_round, player_launch):
        '''
        Miss button
        '''
        if player_launch == 1 :
                operat = self.headers[0][-3]
                if operat == 'l' :
                        score = 0
                elif operat == '-' or operat == 'i' :
                        score = 20 * self.moins0
                elif operat == '*' :
                        score = 0  ##1 * self.multi0
                elif operat == '/' :
                        score = 0  
             
        if player_launch == 2 :
                operat = self.headers[1][-3]
                if operat == 'l' :
                        score = 0
                elif operat == '-' or operat == 'i' :
                        score = 20 * self.moins1
                elif operat == '*' :
                        score = 0  ##1 * self.multi1
                                
                elif operat == '/' :
                        score = 0
                                
        if player_launch == 3 :
                operat = self.headers[2][-3]
                if operat == 'l' :
                        score = 0
                elif operat == '-' or operat == 'i' :
                        score = 20 * self.moins2
                elif operat == '*' :
                        score = 0  ##1 * self.multi2
                elif operat == '/' :
                        score = 0  
        
        self.penality = score
         
        players[actual_player].score += self.penality
        #players[actual_player].columns[5] = ('MISS', 'str')
        players[actual_player].columns[player_launch-1] = (score, 'int', 'game-red')
        self.display.play_sound('miss')
        players[actual_player].darts_thrown += 1
        #self.refresh_stats(players, actual_round)
        self.display.message([self.display.lang.translate('Color-miss')], 1000, None, 'middle', 'big')
        
                           
        # play penality sound
        #self.display.play_sound('penality')

            # anim leds for the penality
            #Event.Publish('penalty')
        
#    def early_player_button(self, players, actual_player, actual_round):
#        '''
#        EMPTY
#        '''
    
    def post_round_check(self, players, actual_round, actual_player):
        """
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        """

        if actual_round >= self.max_round and actual_player == len(players) - 1:
            # Last round, last player
            return self.best_score(players)
        return -2
    
    def get_score(self, player):
        """
        Return score of player
        """
        return player.score

    def next_set_order(self, players):
        """
        Sort players for next set
        """
        players.sort(key=self.get_score)

    def refresh_stats(self, players, actual_round):
        """
        refresh players' stats
        """
        for player in players:
            player.stats['Points Per Round'] = player.avg(actual_round)
            player.stats['Points Per Dart'] = player.show_ppd()

    def display_segment(self):
       """
       Set if a message is shown to indicate the segment hitted !
       """
       return False
