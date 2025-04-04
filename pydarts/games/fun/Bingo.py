# -*- coding: utf-8 -*-
# Game by LaDite !
######
from include import cplayer
from include import cgame
import random
import subprocess
import pygame

# Dictionnay of options - Text format only
OPTIONS = {'win_points':'2', 'master':'1', 'block':False}
# background image - relative to images folder - Name it like the game itself
GAME_LOGO = 'Bingo.png' # background image
# Columns headers - Better as a string
HEADERS = [ "#","PTS" ] # Columns headers - Must be a string
# How many darts per player and per round ? Yes ! this is a feature :)
NB_DARTS = 3 # How many darts per player and per round
# Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in ascending order)
GAME_RECORDS = {'Points Per Round':'DESC'}
VERSION = '1.00'

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return nb_players >= 1 and nb_players <= 4, VERSION, 4

#Extend the basic player
class CPlayerExtended(cplayer.Player):
    def __init__(self, ident, nb_columns, interior=False):
      super().__init__(ident, nb_columns, interior)
      self.segments = []
      # Init Player Records to zero
      for record in GAME_RECORDS:
         self.stats[record] = '0'

# Class of the real game
class Game(cgame.Game):
   def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
      super(Game, self).__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
      # For rpi
      self.rpi = rpi
      self.logo = GAME_LOGO
      self.headers = HEADERS
      self.nb_darts = NB_DARTS
      self.nb_players = nb_players
      self.options = options
      # GameRecords is the dictionnary of stats (see above)
      self.GameRecords = GAME_RECORDS

      self.max_round = 100
      self.block = self.options['block']
      self.nb_block = 3
      self.winpoints = int(self.options['win_points'])
      self.master = int(self.options['master'])
      if self.master >= 5 : 
            self.master = 5
      
      self.segmentsLed = []
      self.grid = []
      self.bw = self.display.res['y'] * 5 / 6
      self.y = self.display.res['y'] / 12
      self.x = self.display.res['x'] / 2 - self.bw / 2
      case = self.bw / 5
      self.jw = self.bw / 5
      pad = (case - self.jw) / 2
      self.j_actif = 0
      self.pos = [
      (self.x + pad, self.y + pad ),
      (self.x + case + pad, self.y + pad),
      (self.x + case * 2 + pad, self.y + pad),
      (self.x + case * 3 + pad, self.y + pad),
      (self.x + case * 4 + pad, self.y + pad),
      #
      (self.x + pad, self.y + case + pad),
      (self.x + case + pad, self.y + case + pad),
      (self.x + case * 2 + pad, self.y + case + pad),
      (self.x + case * 3 + pad, self.y + case + pad),
      (self.x + case * 4 + pad, self.y + case + pad),
      #
      (self.x + pad, self.y + case * 2 + pad),
      (self.x + case + pad, self.y + case * 2 + pad),
      (self.x + case * 2 + pad, self.y + case * 2 + pad),
      (self.x + case * 3 + pad, self.y + case * 2 + pad),
      (self.x + case * 4 + pad, self.y + case * 2 + pad),
      #
      (self.x + pad, self.y + case * 3 + pad),
      (self.x + case + pad, self.y + case * 3 + pad),
      (self.x + case * 2 + pad, self.y + case * 3 + pad),
      (self.x + case * 3 + pad, self.y + case * 3 + pad),
      (self.x + case * 4 + pad, self.y + case * 3 + pad),
      #
      (self.x + pad, self.y + case * 4 + pad),
      (self.x + case + pad, self.y + case * 4 + pad),
      (self.x + case * 2 + pad, self.y + case * 4 + pad),
      (self.x + case * 3 + pad, self.y + case * 4 + pad),
      (self.x + case * 4 + pad, self.y + case * 4 + pad),
      ]

      # gestion de l'affichage du segment
      self.show_hit = True
      self.leds = []
      self.leds_blink = []
      
      
   # Actions done before each dart throw - for example, check if the player is allowed to play
   def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        return_code = 0

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                LST = self.check_handicap(players)
            except Exception as e:
                self.logs.Log("ERROR","Handicap failed : {}".format(e))
            for Player in players:
                # Init score
                Player.score = 0

            #change background
            self.display.display_background('bingo/background.jpg')

            # define the first grid
            self.creategrid()

        # Each new player
        if player_launch == 1:
            players[actual_player].segments = ['__','__','__']
            players[actual_player].round_points = 0
            self.save_turn(players)
            players[actual_player].pre_play_score = players[actual_player].score # Backup current score
            self.j_actif = actual_player
            #Reset display Table
            players[actual_player].columns = []
            # Clean all next boxes
            for i in range(0,2):
                players[actual_player].columns.append(['','int'])
        
        ### GESTION LEDS FIXES
        self.leds = []
        self.leds_blink = []
        for k,v in enumerate(self.grid) :
            if v[1] == 0 and v[2] != 2 :
                  self.leds.append(str(v[0])+'#green')
            elif v[1] == 1 and v[2] != 2 :
                  self.leds.append(str(v[0])+'#blue')
            elif v[1] == 2 and v[2] != 2 :
                  self.leds.append(str(v[0])+'#red')
            elif v[1] == 3 and v[2] != 2 :
                  self.leds.append(str(v[0])+'#yellow')
            elif v[3] == self.nb_block :     #### allume en blanc fixe si chiffre bloque 
                  self.leds.append(str(v[0])+'#white')
                  
            ### GESTION LEDS CLIGNOTANTES     
            if v[2] == 2 and v[1] == 0 and v[3] != self.nb_block :
                  self.leds_blink.append(str(v[0])+'#green')
            elif v[2] == 2 and v[1] == 1 and v[3] != self.nb_block : 
                  self.leds_blink.append(str(v[0])+'#blue')   
            elif v[2] == 2 and v[1] == 2 and v[3] != self.nb_block : 
                  self.leds_blink.append(str(v[0])+'#red')   
            elif v[2] == 2 and v[1] == 3 and v[3] != self.nb_block: 
                  self.leds_blink.append(str(v[0])+'#yellow')       

        self.rpi.set_target_leds('|'.join(f"{mult}{segment}" for mult in ('S', 'D', 'T') for segment in self.leds))         
        self.rpi.set_target_leds_blink('|'.join(f"{mult}{segment}" for mult in ('S', 'D', 'T') for segment in self.leds_blink)) 
        
        return return_code


   def post_dart_check(self,hit,players,actual_round,actual_player,player_launch):
        return_code = 0
        self.show_hit = True

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].segments[player_launch-1] = hit

        # test multiplicateur
        multi = 1
        if hit[:1] == 'D' :
            multi = 2
        if hit[:1] == 'T' :
            multi = 3

        # Melange a grille - SB doit toucher 2x (a faire) - DB touche 1x
        if hit == 'SB' :
            self.show_hit = False
            ### Melange la grille - toucher 2x - a codedr
            random.shuffle(self.grid)
            #self.video_player.play_video(self.display.file_class.get_full_filename('bingo/bingo_bulls', 'videos'))
            self.display.play_sound('bingo_SB')
        
        elif hit == 'DB' :
            self.show_hit = False
            #self.video_player.play_video(self.display.file_class.get_full_filename('bingo/bingo_bulls', 'videos'))
            self.display.play_sound('bingo_DB')
            for k,v in enumerate(self.grid):
                if v[1] == -1 :
                    self.grid[k] = (v[0], actual_player, 1, v[3]) 
                    break 
            ### Melange la grille - toucher 2x - a codedr
            random.shuffle(self.grid)

        else:
            for k,v in enumerate(self.grid):
                if v[0] == int(hit[1:]):
   
                    if v[2] <= 0 and v[1] == -1  : 
                        if multi == 3 :
                              multi = 2
                        self.grid[k] = (v[0], actual_player, multi, v[3])
                        self.display.play_sound('bingo_son1')

                    elif v[2] == 1 and v[1] == actual_player  :
                        self.grid[k] = (v[0], actual_player, 2, v[3]) 
                        self.display.play_sound('bingo_son2')
                  
                    elif v[2] == 2 and v[1] == actual_player and self.block :
                        multi += v[3]  
                        ### si v[3] > nb_block ==> force v[3] a nb_block  
                        if multi > self.nb_block :
                              self.grid[k] = (v[0], actual_player, 2, self.nb_block) 
                        else :
                              self.grid[k] = (v[0], actual_player, 2, multi)
                        self.display.play_sound('bingo_sonBLK')
   
                    elif v[1] != actual_player : 
                        niv = v[2] - multi
                        if v[2] == 2 and multi == 2 and v[3] < self.nb_block:
                            self.grid[k] = (v[0], -1, 0, v[3])    ### REMISE A 0 - v[3] pour advs garde ses blocks
                            self.display.play_sound('bingo_son0')
                            
                        elif v[2] == 2 and multi == 3 and v[3] < self.nb_block:
                            self.grid[k] = (v[0], actual_player, 1, 0)  ### v[3] REMIS A 0
                            self.display.play_sound('bingo_son1')
                            
                        elif v[2] == 2 and multi == 1 and v[3] < self.nb_block:
                            self.grid[k] = (v[0], v[1], 1, v[3])   ### pas REMIS A 0 - v[3] pour advs garde ses blocks
                            self.display.play_sound('bingo_son3')
   
                        elif v[2] == 1 and multi == 3 and v[3] < self.nb_block:
                            self.grid[k] = (v[0], actual_player, 2, 0)   ### v[3] REMIS A 0
                            self.display.play_sound('bingo_son2')
                            
                        elif v[2] == 1 and multi == 2 and v[3] < self.nb_block:
                            self.grid[k] = (v[0], actual_player, 1, 0)  ### v[3] REMIS A 0
                            self.display.play_sound('bingo_son1')
                            
                        elif v[2] == 1 and multi == 1 and v[3] < self.nb_block:
                            self.grid[k] = (v[0], -1, 0, v[3])      ### REMISE A 0 - v[3] pour advs garde ses blocks
                            self.display.play_sound('bingo_son0')  

                        else:
                            self.show_hit = False  
   
                    self.BlinkCase(k)
                    self.DrawCase(k, True)
                    self.display.update_screen()
                    self.display.play_sound('bingo_')
  
        # test recordille validée
        g = self.grid
        ### (257-261 lignes horizontales - 262-266 lignes verticales - 267-268 lignes diagonales)
        if (g[0][1] == actual_player and g[1][1] == actual_player and g[2][1] == actual_player and g[3][1] == actual_player and g[4][1] == actual_player) and (g[0][2] == 2 and g[1][2] == 2 and g[2][2] == 2 and g[3][2] == 2 and g[4][2] == 2) or \
           (g[5][1] == actual_player and g[6][1] == actual_player and g[7][1] == actual_player and g[8][1] == actual_player and g[9][1] == actual_player) and (g[5][2] == 2 and g[6][2] == 2 and g[7][2] == 2 and g[8][2] == 2 and g[9][2] == 2) or \
           (g[10][1] == actual_player and g[11][1] == actual_player and g[12][1] == actual_player and g[13][1] == actual_player and g[14][1] == actual_player) and (g[10][2] == 2 and g[11][2] == 2 and g[12][2] == 2 and g[13][2] == 2 and g[14][2] == 2) or \
           (g[15][1] == actual_player and g[16][1] == actual_player and g[17][1] == actual_player and g[18][1] == actual_player and g[19][1] == actual_player) and (g[15][2] == 2 and g[16][2] == 2 and g[17][2] == 2 and g[18][2] == 2 and g[19][2] == 2) or \
           (g[20][1] == actual_player and g[21][1] == actual_player and g[22][1] == actual_player and g[23][1] == actual_player and g[24][1] == actual_player) and (g[20][2] == 2 and g[21][2] == 2 and g[22][2] == 2 and g[23][2] == 2 and g[24][2] == 2) or \
           (g[0][1] == actual_player and g[5][1] == actual_player and g[10][1] == actual_player and g[15][1] == actual_player and g[20][1] == actual_player) and (g[0][2] == 2 and g[5][2] == 2 and g[10][2] == 2 and g[15][2] == 2 and g[20][2] == 2) or \
           (g[1][1] == actual_player and g[6][1] == actual_player and g[11][1] == actual_player and g[16][1] == actual_player and g[21][1] == actual_player) and (g[1][2] == 2 and g[6][2] == 2 and g[11][2] == 2 and g[16][2] == 2 and g[21][2] == 2) or \
           (g[2][1] == actual_player and g[7][1] == actual_player and g[12][1] == actual_player and g[17][1] == actual_player and g[22][1] == actual_player) and (g[2][2] == 2 and g[7][2] == 2 and g[12][2] == 2 and g[17][2] == 2 and g[22][2] == 2) or \
           (g[3][1] == actual_player and g[8][1] == actual_player and g[13][1] == actual_player and g[18][1] == actual_player and g[23][1] == actual_player) and (g[3][2] == 2 and g[8][2] == 2 and g[13][2] == 2 and g[18][2] == 2 and g[23][2] == 2) or \
           (g[4][1] == actual_player and g[9][1] == actual_player and g[14][1] == actual_player and g[19][1] == actual_player and g[24][1] == actual_player) and (g[4][2] == 2 and g[9][2] == 2 and g[14][2] == 2 and g[19][2] == 2 and g[24][2] == 2) or \
           (g[0][1] == actual_player and g[6][1] == actual_player and g[12][1] == actual_player and g[18][1] == actual_player and g[24][1] == actual_player) and (g[0][2] == 2 and g[6][2] == 2 and g[12][2] == 2 and g[18][2] == 2 and g[24][2] == 2) or \
           (g[4][1] == actual_player and g[8][1] == actual_player and g[12][1] == actual_player and g[16][1] == actual_player and g[20][1] == actual_player) and (g[4][2] == 2 and g[8][2] == 2 and g[12][2] == 2 and g[16][2] == 2 and g[20][2] == 2) :
           
             self.display.play_sound('bingo_win2',wait_finish = True)
             self.drawWin(actual_player)
             players[actual_player].score += 1
             self.creategrid()
        else:
            print('')  
            #self.display.sound_for_touch(hit) # Touched !

        # test for a winner
        if players[actual_player].score >= self.winpoints:
            self.winner =  players[actual_player].ident
            return_code = 3

        return return_code

   def creategrid(self):
      """
      create grid
      """
      self.grid.clear()
      ### 21,22,23,24,25 pour les token star
      hits = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]
      for i in range (0, 25) :
         h = random.randint(0, len(hits) - 1)
         self.grid.append((hits[h], -1, 0, 0)) # segment,joueur,etat, block=5 ou 3
         hits.pop(h)
         

   ###############
   # Method to frefresh player.stat - Adapt to the stats you want. They represent mathematical formulas used to calculate stats. Refreshed after every launch
   def refresh_stats(self, players, actual_round):
      for player in players:
         player.stats['Points Per Round'] = player.avg(actual_round)

   ###############
   # Set if a message is shown to indicate the segment hitted !
   #
   def display_segment(self):
      return False   ###self.show_hit
    
    
    
   def miss_button(self, players, actual_player, actual_round, player_launch):

      players[actual_player].segments[player_launch-1] = 'MISS'
      self.display.play_sound('treasure_crane_jaune')
          
      players[actual_player].darts_thrown += 1
   


     ###############
   # Refresh In-game screen
   #
   def refresh_game_screen(self, Players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player,TxtOnLogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
       # do not show the table scores
      ClickZones = {}

      # Clear
      self.display.screen.fill( (0,0,0) )
      # background image
      self.display.display_background('bingo/background.jpg')

      bw = self.bw
      y = self.y
      x = self.x
      jw= self.jw

      self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_board_back', 'images'),x, y, bw, bw, True, False, False)

      # show values in grid
      for k,v in enumerate(self.grid ):
         self.DrawCase(k)

      self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_board', 'images'),x, y, bw, bw, True, False, False)

      pad = bw/20
      pw = x-pad*2
      
      ### Affiche les segments touches
      self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_dartbg', 'images'),pad, self.display.res['y']-pw/4, pw, pw/4, True, False, False)
      self.display.blit_text(Players[actual_player].segments[0],pad, self.display.res['y']-pw/4, pw/3, pw/4, color=(255,255,255))
      self.display.blit_text(Players[actual_player].segments[1],pad+pw/3, self.display.res['y']-pw/4, pw/3, pw/4, color=(255,255,255))
      self.display.blit_text(Players[actual_player].segments[2],pad+pw/3*2, self.display.res['y']-pw/4, pw/3, pw/4, color=(255,255,255))
      
      ### Affiche les nb de tours
      self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_turnbg', 'images'),x+bw+pad, self.display.res['y']-pw/4, pw, pw/4, True, False, False)
      self.display.blit_text(str(self.display.lang.translate('round')) +' '+str(actual_round) ,x+bw+pad, self.display.res['y']-pw/4, pw, pw/4, color=(255,255,255))
      
      ### Affiche le nom du joueur 1
      self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_name0', 'images'),pad, y, pw,pw/4, True, False, False)
      self.display.blit_text(Players[0].name,pad, y, pw,pw/4, color=(255,255,255) if actual_player==0 else (0,0,0) )
      self.display.blit_text(str(Players[0].score),pad+pw*3/4, y+pw/4, pw/4,pw/4, color=(255,255,255) if actual_player==0 else (150,0,0) )
      
      ### Affiche le nom du joueur 2
      if len(Players) > 1:
        self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_name1', 'images'),x+bw+pad, y, pw,pw/4, True, False, False)
        self.display.blit_text(Players[1].name,x+bw+pad, y, pw,pw/4, color=(255,255,255) if actual_player==1 else(0,0,0))
        self.display.blit_text(str(Players[1].score),x+bw+pad+pw*3/4,y+pw/4, pw/4,pw/4, color=(255,255,255) if actual_player==1 else(150,0,0))
      
       ### Affiche le nom du joueur 3
      if len(Players) > 2:
        self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_name2', 'images'),pad, y+bw/2, pw,pw/4, True, False, False)
        self.display.blit_text(Players[2].name,pad, y+bw/2, pw,pw/4, color=(255,255,255) if actual_player==2 else(0,0,0))
        self.display.blit_text(str(Players[2].score),pad+pw*3/4, y+bw/2+pw/4 , pw/4,pw/4, color=(255,255,255) if actual_player==2 else (150,0,0) )
      
      ### Affiche le nom du joueur 4
      if len(Players) > 3:
        self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_name3', 'images'),x+bw+pad, y+bw/2, pw,pw/4, True, False, False)
        self.display.blit_text(Players[3].name,x+bw+pad, y+bw/2, pw,pw/4, color=(255,255,255) if actual_player==3 else(0,0,0))
        self.display.blit_text(str(Players[3].score),x+bw+pad+pw*3/4, y+bw/2+pw/4, pw/4,pw/4, color=(255,255,255) if actual_player==3 else(150,0,0))
        
      if end_of_game :
          ClickZones = self.display.end_of_game_menu(logo, stat_button=False)
          return ClickZones

      self.display.update_screen()

      return ClickZones

   #######################"
   def BlinkCase(self,case) :
      for i in range (0,4) :
        self.display.display_image(self.display.file_class.get_full_filename(f'bingo/bingo_j{self.grid[case][1]}', 'images'), self.pos[case][0], self.pos[case][1], self.jw, self.jw, True, False, False)
        self.display.update_screen(rect=(self.pos[case][0], self.pos[case][1], self.jw, self.jw))
        self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_empty', 'images'), self.pos[case][0], self.pos[case][1], self.jw, self.jw, True, False, False)
        self.display.update_screen(rect=(self.pos[case][0], self.pos[case][1], self.jw, self.jw))

   #######################"
   def DrawCase(self, case, redrawgrid = False) :

      ### AFFICHE LA CASE ACQUISE DU JOUEUR
      if self.grid[case][1] >= 0:
        self.display.display_image(self.display.file_class.get_full_filename(f'bingo/bingo_j{self.grid[case][1]}', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
      
      ### AFFICHE LA CASE BOUCLIER ACQUISE DU JOUEUR
      if self.grid[case][2] >= 2 and self.grid[case][3] == 0:
        self.display.display_image(self.display.file_class.get_full_filename(f'bingo/bingo_shield{self.grid[case][1]}', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
        self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+self.jw/6,self.pos[case][1]+self.jw/6, self.jw/1.5, self.jw/1.5, color=(0,0,0))
      elif self.grid[case][1] >= 0:
        self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+self.jw/4,self.pos[case][1]+self.jw/4, self.jw/2, self.jw/2, color=(230,250,230))
                                                                             #### pour afficher chiffre plus gros /6 - /1.5 a la place de /4 - /2
      else:
        self.display.blit_text(str(self.grid[case][0]),self.pos[case][0],self.pos[case][1], self.jw, self.jw, color=(255, 255, 255))
        self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+5,self.pos[case][1]+5, self.jw-10, self.jw-10, color=(230, 250, 230))

      # blocked
      if self.nb_block == 5 :
        if self.grid[case][2] >= 2 and self.grid[case][3] == 1 :
          self.display.display_image(self.display.file_class.get_full_filename(f'bingo/bingo_block{self.grid[case][1]}1', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
          self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+self.jw/4,self.pos[case][1]+self.jw/6, self.jw/2, self.jw/1.5, color=(0,0,0))
        
        elif self.grid[case][2] >= 2 and self.grid[case][3] == 2 :
          self.display.display_image(self.display.file_class.get_full_filename(f'bingo/bingo_block{self.grid[case][1]}2', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
          self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+self.jw/4,self.pos[case][1]+self.jw/6, self.jw/2, self.jw/1.5, color=(0,0,0))
        
        elif self.grid[case][2] >= 2 and self.grid[case][3] == 3 :
          self.display.display_image(self.display.file_class.get_full_filename(f'bingo/bingo_block{self.grid[case][1]}3', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
          self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+self.jw/4,self.pos[case][1]+self.jw/6, self.jw/2, self.jw/1.5, color=(0,0,0))
        
        elif self.grid[case][2] >= 2 and self.grid[case][3] == 4 :
          self.display.display_image(self.display.file_class.get_full_filename(f'bingo/bingo_block{self.grid[case][1]}4', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
          self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+self.jw/4,self.pos[case][1]+self.jw/6, self.jw/2, self.jw/1.5, color=(0,0,0))
        elif self.grid[case][2] >= 2 and self.grid[case][3] >= 5 :
          self.display.display_image(self.display.file_class.get_full_filename(f'bingo/bingo_block{self.grid[case][1]}5', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
      
      elif self.nb_block == 3 :
        if self.grid[case][2] >= 2 and self.grid[case][3] == 1 :
          self.display.display_image(self.display.file_class.get_full_filename(f'bingo/bingo_block{self.grid[case][1]}2', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
          self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+self.jw/4,self.pos[case][1]+self.jw/6, self.jw/2, self.jw/1.5, color=(0,0,0))
        
        elif self.grid[case][2] >= 2 and self.grid[case][3] == 2 :
          self.display.display_image(self.display.file_class.get_full_filename(f'bingo/bingo_block{self.grid[case][1]}4', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
          self.display.blit_text(str(self.grid[case][0]),self.pos[case][0]+self.jw/4,self.pos[case][1]+self.jw/6, self.jw/2, self.jw/1.5, color=(0,0,0))
        
        elif self.grid[case][2] >= 2 and self.grid[case][3] >= 3 :
          self.display.display_image(self.display.file_class.get_full_filename(f'bingo/bingo_block{self.grid[case][1]}5', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
              
      
      ### CASES ETOILES - AJOUT BOUCLIER
      if self.master == 0 :
         for k,v in enumerate(self.grid):
           if v[0] in (21,22,23,24,25) :
              self.grid[k] = (v[0], self.j_actif, 2, v[3])
      
      elif self.master == 1 :
         for k,v in enumerate(self.grid):
           if v[0] in (21,22,23,24) :
             self.grid[k] = (v[0], self.j_actif, 2, v[3])    
           if v[0] == 25 :
             self.grid[k] = (v[0], 99, 0, v[3])
      
      elif self.master == 2 :
         for k,v in enumerate(self.grid):   
           if v[0] in (21,22,23) :
             self.grid[k] = (v[0], self.j_actif, 2, v[3])    
           if v[0] in (24,25) :
             self.grid[k] = (v[0], 99, 0, v[3])
      
      elif self.master == 3 :
         for k,v in enumerate(self.grid):   
           if v[0] in (21,22) :
             self.grid[k] = (v[0], self.j_actif, 2, v[3])    
           if v[0] in (23,24,25) :
             self.grid[k] = (v[0], 99, 0, v[3])
      
      elif self.master == 4 :
         for k,v in enumerate(self.grid):   
           if v[0] == 21 :
             self.grid[k] = (v[0], self.j_actif, 2, v[3])    
           if v[0] in (22,23,24,25) :
             self.grid[k] = (v[0], 99, 0, v[3])
      
      elif self.master == 5 :
         for k,v in enumerate(self.grid):
           if v[0] in (21,22,23,24,25) :
             self.grid[k] = (v[0], 99, 0, v[3]) 
         
      
      ### AFFICHE LES ETOILES DANS LA COULEUR DU JOUEUR ACTIF
      if self.grid[case][0] in (21,22,23,24,25) and self.j_actif == 0 :
        self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_black', 'images'), self.pos[case][0], self.pos[case][1], self.jw, self.jw, True, False, False)
        self.display.display_image(self.display.file_class.get_full_filename('bingo/star_green', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
                  
      if self.grid[case][0] in (21,22,23,24,25) and self.j_actif == 1 :
        self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_black', 'images'), self.pos[case][0], self.pos[case][1], self.jw, self.jw, True, False, False)
        self.display.display_image(self.display.file_class.get_full_filename('bingo/star_blue', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
      
      if self.grid[case][0] in (21,22,23,24,25) and self.j_actif == 2 :
        self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_black', 'images'), self.pos[case][0], self.pos[case][1], self.jw, self.jw, True, False, False)
        self.display.display_image(self.display.file_class.get_full_filename('bingo/star_red', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
      
      if self.grid[case][0] in (21,22,23,24,25) and self.j_actif == 3 :
        self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_black', 'images'), self.pos[case][0], self.pos[case][1], self.jw, self.jw, True, False, False)
        self.display.display_image(self.display.file_class.get_full_filename('bingo/star_yellow', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
      ### star white
      if self.grid[case][0] in (21,22,23,24,25) and self.grid[case][1] == 99 :
        self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_black', 'images'), self.pos[case][0], self.pos[case][1], self.jw, self.jw, True, False, False)
        self.display.display_image(self.display.file_class.get_full_filename('bingo/star_white', 'images'),self.pos[case][0],self.pos[case][1], self.jw, self.jw, True, False, False)
               
      # REAFFICHE LA GRILLE
      if redrawgrid :
        self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_board', 'images'),self.x, self.y, self.bw, self.bw, True, False, False)

   #######################"
   def drawWin(self,actual_player) :

      g = self.grid
      ### horiz
      if (g[0][1] == actual_player and g[1][1] == actual_player and g[2][1] == actual_player and g[3][1] == actual_player and g[4][1] == actual_player) and (g[0][2] == 2 and g[1][2] == 2 and g[2][2] == 2 and g[3][2] == 2 and g[4][2] == 2) :
          win = [(0,'b'),(1,'i'),(2,'n'),(3,'g'),(4,'o')]
      if g[5][1] == actual_player and g[6][1] == actual_player and g[7][1] == actual_player and g[8][1] == actual_player and g[9][1] == actual_player :
          win = [(5,'b'),(6,'i'),(7,'n'),(8,'g'),(9,'o')]
      if g[10][1] == actual_player and g[11][1] == actual_player and g[12][1] == actual_player and g[13][1] == actual_player and g[14][1] == actual_player :
          win = [(10,'b'),(11,'i'),(12,'n'),(13,'g'),(14,'o')]
      if g[15][1] == actual_player and g[16][1] == actual_player and g[17][1] == actual_player and g[18][1] == actual_player and g[19][1] == actual_player : 
          win = [(15,'b'),(16,'i'),(17,'n'),(18,'g'),(19,'o')]
      if g[20][1] == actual_player and g[21][1] == actual_player and g[22][1] == actual_player and g[23][1] == actual_player and g[24][1] == actual_player :
          win = [(20,'b'),(21,'i'),(22,'n'),(23,'g'),(24,'o')]

      ### verti
      if g[0][1] == actual_player and g[5][1] == actual_player and g[10][1] == actual_player and g[15][1] == actual_player and g[20][1] == actual_player : 
          win = [(0,'b'),(5,'i'),(10,'n'),(15,'g'),(20,'o')]           
      if g[1][1] == actual_player and g[6][1] == actual_player and g[11][1] == actual_player and g[16][1] == actual_player and g[21][1] == actual_player : 
          win = [(1,'b'),(6,'i'),(11,'n'),(16,'g'),(21,'o')]         
      if g[2][1] == actual_player and g[7][1] == actual_player and g[12][1] == actual_player and g[17][1] == actual_player and g[22][1] == actual_player : 
          win = [(2,'b'),(7,'i'),(12,'n'),(17,'g'),(22,'o')]         
      if g[3][1] == actual_player and g[8][1] == actual_player and g[13][1] == actual_player and g[18][1] == actual_player and g[23][1] == actual_player : 
          win = [(3,'b'),(8,'i'),(13,'n'),(18,'g'),(23,'o')]       
      if g[4][1] == actual_player and g[9][1] == actual_player and g[14][1] == actual_player and g[19][1] == actual_player and g[24][1] == actual_player :
          win = [(4,'b'),(9,'i'),(14,'n'),(19,'g'),(24,'o')]            

      ### diagnal doite-gauche
      if g[0][1] == actual_player and g[6][1] == actual_player and g[12][1] == actual_player and g[18][1] == actual_player and g[24][1] == actual_player :
          win = [(0,'b'),(6,'i'),(12,'n'),(18,'g'),(24,'o')] 
      ### diagonal gauche-droite
      if g[4][1] == actual_player and g[8][1] == actual_player and g[12][1] == actual_player and g[16][1] == actual_player and g[20][1] == actual_player :
          win = [(20,'b'),(16,'i'),(12,'n'),(8,'g'),(4,'o')]

#### FAIRE AFFICHER BINGO 
      for v in win :
          self.display.display_image(self.display.file_class.get_full_filename(f'bingo/bingo_{actual_player}{v[1]}', 'images'),self.pos[v[0]][0],self.pos[v[0]][1], self.jw, self.jw, True, False, False)
          self.display.display_image(self.display.file_class.get_full_filename('bingo/bingo_board', 'images'),self.x, self.y, self.bw, self.bw, True, False, False)
          
          self.display.update_screen()
          
          self.display.play_sound(f'bingo_win1',wait_finish = True)
          
      #self.display.play_sound('bingo_win2')
      pygame.time.delay(1500)
