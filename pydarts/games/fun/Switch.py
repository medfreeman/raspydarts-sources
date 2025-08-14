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
OPTIONS = {'theme': 'default', 'max_round': 12, 'numerique' : False}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'switch.png'
HEADERS = ['D1', 'D2', 'D3', '', '', '', ''] # Columns headers - Must be a string
VERSION = '1.00'

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return nb_players >= 1 and nb_players <= 4, VERSION, 4
    
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
        self.segments = []
        
class Game(cgame.Game):
    """
    switch game class
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

        self.winner = None
        self.numerique = options['numerique']
        
        self.video_player = video_player
        self.targets = ''
        self.leds = True
        #  Penality points for a missing dart
        self.penality = 20
        
        #position + drapeau
        self.grid = []
                
        # Note : all positions are for 1920/1080. We will have to resize
        self.ratioX = self.display.res['x'] / 1920
        self.ratioY = self.display.res['y'] / 1080
  
    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        
        # Init
        handler = self.init_handler()
        handler['return_code'] = 0
        
        if player_launch == 1:
            players[actual_player].reset_darts()
        
        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.log("ERROR", f"Handicap failed : {exception}")
        
            for player in players:
                # Init score
                player.score = 0
            self.grid.clear()
            for player in players :
                 #self.grid.clear()
                 if not self.numerique :
                     hits = ['1', '18', '4', '13', '6', '10', '15', '2', '17', '3', '19', '7', '16', '8', '11', '14', '9', '12', '5', '20', 'SB', 'DB']
                 else :
                     hits = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', 'SB', 'DB']
                 pos = 340
                 for i in range (0, 22) :
                     self.grid.append((hits[i], pos, False, player.ident)) # segment, posX, etat, joueur
                     pos = pos + 71
            
        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            players[actual_player].pre_play_score = players[actual_player].score
            players[actual_player].segments = ['__','__','__']
            
            if actual_round == 1 and actual_player == 0:
                for player in players:
                    player.reset_rounds(self.max_round)
 
        
        #maj led via self.grid 
        if player_launch in (1,2,3) :
            testleds = []
            for k,v in enumerate(self.grid) :
                if v[2] == False and v[3] == players[actual_player].ident: 
                    testleds.append('s' + str(v[0]) + '#green')
                    testleds.append('S' + str(v[0]) + '#green')
                    testleds.append('D' + str(v[0]) + '#green')
                    testleds.append('T' + str(v[0]) + '#green')
                if v[0] == 'SB' and v[2] == False and v[3] == players[actual_player].ident: 
                    testleds.append('SB#green')
                if v[0] == 'DB' and v[2] == False and v[3] == players[actual_player].ident: 
                    testleds.append('DB#green')

        ### INFOS
        print('self.leds maj - predarts')
        print(testleds)
        print('self.grid - predarts')
        print(self.grid)
        
               
        # Print debug output
        self.logs.log("DEBUG",self.infos)
        
        
        leds = testleds
        self.rpi.set_target_leds ('')
        self.rpi.set_target_leds('|'.join(testleds))
      
        return handler

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
                self.logs.log("DEBUG", \
                        f"Best found : {best_score} / Count={best_count} / player = {best_player}")
            elif player.score == best_score:
                best_count += 1

        self.logs.log("DEBUG", \
                f"Best score : {best_score} / Count={best_count} / Player = {best_player}")

        if best_count == 1:
            return best_player
        return -1

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Function run after each dart throw - for example, add points to player
        """
        #self.display.sound_for_touch(hit)
        score = 0
        handler = self.init_handler()
        
        score = 0

        if hit : 
            
            if hit == 'SB' or hit == 'DB' :
                hit2 = '0'
                hit3 = '0'
            else :
                if self.numerique :
                    if hit[1:] == '19' :
                        hit2 = '20'   
                        hit3 = '18'  
                    
                    elif hit[1:] == '20' :
                       hit2 = '1'
                       hit3 = '19'
                    
                    elif hit[1:] == '1' :
                       hit2 = '2'
                       hit3 = '20'

                    elif hit[1:] not in ('1','20','19')  :      
                        hit2 = ''
                        hit3 = ''
                        for k,v in enumerate(self.grid) :
                            if v[0] == str(hit[1:]) :
                                hit2 = self.grid[k+1][0]
                                hit3 = self.grid[k-1][0]
                                break
                
                if not self.numerique :  
                    if hit[1:] == '5' :
                       hit2 = '20'   
                       hit3 = '12'   
                       
                    elif hit[1:] == '20' :
                       hit2 = '1'
                       hit3 = '5'
                    
                    elif hit[1:] == "1" :
                       hit2 = '18'
                       hit3 = '20'
                    
                    elif hit[1:] not in ('1','20','5')  : 
                        hit2 = ''
                        hit3 = ''
                        for k,v in enumerate(self.grid) :
                            if v[0] == str(hit[1:]) :
                                hit2 = self.grid[k+1][0]
                                hit3 = self.grid[k-1][0]
                                break                  

            
            for k,v in enumerate(self.grid) :  
                if hit == 'SB' :
                    if players[actual_player].ident == 0 :
                        x=21
                    elif players[actual_player].ident == 1 :
                        x=43
                    elif players[actual_player].ident == 2 :
                        x=65
                    elif players[actual_player].ident == 3 :
                        x=87  
                    
                    ### en cas de sb non active - active SB
                    if v[0] == 'SB' and v[2] == False and v[3] == players[actual_player].ident:
                        self.grid[k] = (v[0], v[1], True, players[actual_player].ident)
                        score = score + 25
                        handler['sound'] = 'switch_laser'
                        
                    ### en cas de sb et qu il est deja active - active DB   (grid = 22) 
                    elif v[0] == 'SB' and v[2] == True and v[3] == players[actual_player].ident and self.grid[x][2] == False and self.grid[x][3] == players[actual_player].ident:
                        self.grid[x] = ('DB', 1831, True, players[actual_player].ident)
                        score = score + 50
                        handler['sound'] = 'switch_laser'
              
                    ### en cas ou SB et DB sont actives - desactive SB
                    elif v[0] == 'SB' and v[2] == True and v[3] == players[actual_player].ident and self.grid[x][2] == True and self.grid[x][3] == players[actual_player].ident:
                        self.grid[x-1] = ('SB', 1760, False, players[actual_player].ident)
                        score = score - 25
                        handler['sound'] = 'switch_laser'
                            
                        
                if hit == 'DB' :
                    if players[actual_player].ident == 0 :
                        x=21
                    elif players[actual_player].ident == 1 :
                        x=43
                    elif players[actual_player].ident == 2 :
                        x=65
                    elif players[actual_player].ident == 3 :
                        x=87                     
                    
                    ## si DB et SB sont False - active DB et SB
                    if v[0] == str(hit) and v[2] == False and v[3] == players[actual_player].ident and self.grid[x-1][2] == False and self.grid[x-1][3] == players[actual_player].ident:
                        self.grid[k] = (v[0], v[1], True, players[actual_player].ident)
                        self.grid[x-1] = ('SB', 1760, True, players[actual_player].ident)
                        score = score + 75  ### 50+25
                        handler['sound'] = 'switch_laser'
                    
                    ## si DB est False et SB est True, active DB 
                    elif v[0] == 'DB' and v[2] == False and v[3] == players[actual_player].ident and  self.grid[x-1][2] == True and self.grid[x-1][3] == players[actual_player].ident:  
                        self.grid[x] = ('DB', 1831, True, players[actual_player].ident)
                        score = score + 50  ## DB = 50
                        handler['sound'] = 'switch_laser'
                        
                    ## si DB est True et SB est False - desactive DB et active le SB
                    elif v[0] == 'DB' and v[2] == True and v[3] == players[actual_player].ident and self.grid[x-1][2] == False and self.grid[x-1][3] == players[actual_player].ident:  
                        self.grid[x] = ('DB', 1831, False, players[actual_player].ident)
                        self.grid[x-1] = ('SB', 1760, True, players[actual_player].ident)
                        score = score - 25  ## DB - 50 SB + 25
                        handler['sound'] = 'switch_laser'
                    
                    ## si DB est True et SB est True - desactive DB et laisse le SB -- #### ACTIVE 1 si eteint (!!! suprimer !!!)
                    elif v[0] == 'DB' and v[2] == True and v[3] == players[actual_player].ident and self.grid[x-1][2] == True and self.grid[x-1][3] == players[actual_player].ident:   #and self.grid[x-20][2] == False:  
                        self.grid[x] = ('DB', 1831, False, players[actual_player].ident)
                        self.grid[x-1] = ('SB', 1760, True, players[actual_player].ident)
                        score = score - 50  ## DB - 50
                        handler['sound'] = 'switch_laser'
  
                ### passe de l etat FALSE a TRUE 
                if hit[:1] == 'T' :  ## si triple, le chiffre suivant (hit2) et precedent (hit3) sont impactes
                    if v[0] == str(hit[1:]) and v[2] == False and v[3] == players[actual_player].ident :
                        self.grid[k] = (v[0], v[1], True, players[actual_player].ident)
                        score = score + int(v[0])*3
                        handler['sound'] = 'switch_laser'
                    
                    if v[0] == str(hit2) and v[2] == False and v[3] == players[actual_player].ident:
                        self.grid[k] = (v[0], v[1], True, players[actual_player].ident)
                        score = score + int(hit2)
                        handler['sound'] = 'switch_laser'
                    
                    if v[0] == str(hit3) and v[2] == False and v[3] == players[actual_player].ident:
                        self.grid[k] = (v[0], v[1], True, players[actual_player].ident) 
                        score = score + int(hit3) 
                        handler['sound'] = 'switch_laser'      
                
                if hit[:1] == 'D' :  ## si double, le chiffre suivant est impacte
                    if v[0] == str(hit[1:]) and v[2] == False and v[3] == players[actual_player].ident:
                        self.grid[k] = (v[0], v[1], True, players[actual_player].ident)
                        score = score + int(v[0])*2
                        handler['sound'] = 'switch_laser'
                    
                    if v[0] == str(hit2) and v[2] == False and v[3] == players[actual_player].ident:
                        self.grid[k] = (v[0], v[1], True, players[actual_player].ident)
                        score = score + int(hit2)
                        handler['sound'] = 'switch_laser'
                    hit3 = 0    

                if hit[:1] == 'S' :
                    if v[0] == str(hit[1:]) and v[2] == False and v[3] == players[actual_player].ident:
                        self.grid[k] = (v[0], v[1], True, players[actual_player].ident)
                        score = score + int(v[0])
                        handler['sound'] = 'switch_laser'
                    hit2 = 0
                    hit3 = 0 
                
                ### passe de l etat TRUE a FALSE
                if hit[:1] == 'T' :  ## si triple, le chiffre suivant (hit2) et precedent (hit3) sont impactes
                    if v[0] == str(hit[1:]) and v[2] == True and v[3] == players[actual_player].ident:
                        self.grid[k] = (v[0], v[1], False, players[actual_player].ident)
                        score = score - int(v[0])*3
                        handler['sound'] = 'switch_laser2'
                    
                    if v[0] == str(hit2) and v[2] == True and v[3] == players[actual_player].ident:
                        self.grid[k] = (v[0], v[1], False, players[actual_player].ident)
                        score = score - int(hit2)
                        handler['sound'] = 'switch_laser2'
                    
                    if v[0] == str(hit3) and v[2] == True and v[3] == players[actual_player].ident :
                        self.grid[k] = (v[0], v[1], False, players[actual_player].ident)  
                        score = score - int(hit3) 
                        handler['sound'] = 'switch_laser2'     
                
                if hit[:1] == 'D' :  ## si double, le chiffre suivant est impacte
                    if v[0] == str(hit[1:]) and v[2] == True and v[3] == players[actual_player].ident:
                        self.grid[k] = (v[0], v[1], False, players[actual_player].ident)
                        score = score - int(v[0])*2
                    if v[0] == str(hit2) and v[2] == True and v[3] == players[actual_player].ident:
                        self.grid[k] = (v[0], v[1], False, players[actual_player].ident)
                        score = score - int(hit2)
                        handler['sound'] = 'switch_laser2'
                    hit3 = 0
                
                if hit[:1] == 'S' :
                    if v[0] == str(hit[1:]) and v[2] == True and v[3] == players[actual_player].ident:
                        self.grid[k] = (v[0], v[1], False, players[actual_player].ident)
                        score = score - int(v[0])
                        handler['sound'] = 'switch_laser2'
                    hit2 = 0
                    hit3 = 0
                    
            print('INFOS')
            print('self.grid - apres suppr')
            print(self.grid)  
        
        else :
            print('hit n est pas dans le target')
            #self.display.sounds('plouf')

        handler['return_code'] = 0

        players[actual_player].add_dart(actual_round, player_launch, hit, score=score)

        players[actual_player].score += score
        players[actual_player].round_points += score
        players[actual_player].points += score
        players[actual_player].segments[player_launch-1] = hit
        
        # Store what he played in the table
        players[actual_player].columns[player_launch - 1] = (score, 'int')
        # Store total for the round in column 6 (start from 0)
        players[actual_player].columns[4] = (players[actual_player].round_points, 'int')
        
        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)
        self.refresh_stats(players, actual_round)
        
        
        ### TEST pour victoire
        compte = 0
        print('compte')
        for k, v in enumerate(self.grid) :
            if v[2] == True and v[3] == players[actual_player].ident :
                compte = compte+1
                print(compte)
                if compte >= 22 :
                    self.winner = self.check_winner(players)
                    #handler['return_code'] = 1

        # Check last round
        if actual_round >= self.max_round and actual_player == self.nb_players - 1 \
                and (player_launch == self.nb_darts or handler['return_code'] == 1):
            self.winner = self.check_winner(players)
            self.infos += f"Last round reached ({actual_round}){self.lf}"
            handler['return_code'] = 2

        if self.winner is not None:
            handler['return_code'] = 3

        self.logs.log("DEBUG", self.infos)
        # Time for shot or video ?
        handler['take_shot'] = self.time_to_take_shot_or_video(hit)
        return handler

    def miss_button(self, players, actual_player, actual_round, player_launch):
        '''
        Miss button
        '''
        
        players[actual_player].segments[player_launch-1] = 'MISS'
        self.display.play_sound('miss')
        for k,v in enumerate(self.grid) :
            if v[2] == True and v[3] == players[actual_player].ident:
                self.grid[k] = (v[0], v[1], False, players[actual_player].ident)
                players[actual_player].score = players[actual_player].score - int(v[0]) 
                break
				
				
				
				 
        players[actual_player].darts_thrown += 1
                 


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

     ###############
   # Refresh In-game screen
   #
    def refresh_game_screen(self, Players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player,TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
       
        ClickZones={}
        
        # Background image
        if not self.numerique :
            self.display.display_background('/switch/bk_nonnumerique.jpg')
        else : 
            self.display.display_background('/switch/bk_numerique.jpg')

        posY = 292
        for player in Players:
            self.display.blit_text(player.name, 150 * self.ratioX, posY * self.ratioY, 150 * self.ratioX, 150 * self.ratioY, color=(255, 255, 255) if actual_player == player.ident else (0, 0, 0))
            self.display.blit_text(str(player.score), 50 * self.ratioX, posY * self.ratioY, 60 * self.ratioX, 60 * self.ratioY, color=(255, 255, 255) if actual_player == player.ident else (0, 0, 0))
            posY = posY + 147

        # Show round number 
        self.display.blit_text(f"Round", 100 * self.ratioX, 925 * self.ratioY, 150, 150, color=(246, 85, 41), dafont='Impact', align='Left', valign='top', margin=False)
        self.display.blit_text(f"{actual_round} / {max_round}", 100 * self.ratioX, 1000 * self.ratioY, 100, 100, color=(246, 85, 41), dafont='Impact', align='Right', valign='top', margin=False)
        
        # draw dart box
        self.display.blit_text("-".join(Players[actual_player].segments), 1600 * self.ratioX, 975 * self.ratioY, 350 * self.ratioX, 90 * self.ratioY, color=(255, 255, 255))

        ### Affiche les checks des joueurs       
        for player in Players :
            if player.ident == 0 :
                for k, v in enumerate(self.grid) :
                    if v[2] == True and v[3] == 0 :    
                        self.display.display_image(self.display.file_class.get_full_filename('switch/check-mark', 'images'),v[1] * self.ratioX, 337 * self.ratioY, 65 * self.ratioX, 64 * self.ratioY, True, False, False)
            
            if player.ident == 1 :
                for k, v in enumerate(self.grid) :
                    if v[2] == True and v[3] == 1 : 
                        self.display.display_image(self.display.file_class.get_full_filename('switch/check-mark', 'images'),v[1] * self.ratioX, 484 * self.ratioY, 65 * self.ratioX, 64 * self.ratioY, True, False, False)
                    
            if player.ident == 2 :
                for k, v in enumerate(self.grid) :
                    if v[2] == True and v[3] == 2 : 
                        self.display.display_image(self.display.file_class.get_full_filename('switch/check-mark', 'images'),v[1] * self.ratioX, 631 * self.ratioY, 65 * self.ratioX, 64 * self.ratioY, True, False, False)
                    
            if player.ident == 3 :
                for k, v in enumerate(self.grid) :
                    if v[2] == True and v[3] == 3 : 
                        self.display.display_image(self.display.file_class.get_full_filename('switch/check-mark', 'images'),v[1] * self.ratioX, 778 * self.ratioY, 65 * self.ratioX, 64 * self.ratioY, True, False, False)
      
        # Refresh screen
        if end_of_game:
            ClickZones = self.display.end_of_game_menu(logo, stat_button=False)

        self.display.update_screen()

        return [ClickZones]

    def refresh_stats(self, players, actual_round):
        """
        Method to frefresh player.stat - Adapt to the stats you want.
        They represent mathematical formulas used to calculate stats. Refreshed after every launch
        """
        for player in players:
            player.stats['Score Per Round'] = player.score_per_round(actual_round)
            
        
    def early_player_button(self, players, actual_player, actual_round):
        """
        Run when player push PLAYERBUTTON before last dart
        return code:
            1. Next player
            2. Last round reach
            3. Winner is
        """
        print('early')
        pass

        if actual_round == int(self.max_round) and actual_player == self.nb_players - 1:
            self.logs.log(
                "DEBUG", "At last round, default action is to return game over.")
            self.logs.log(
                "DEBUG", "If it's not what you expect, raise a bug please.")
            # If its a early_player_button just at the last round - return GameOver
            return_code = 2
        
        return return_code
        


