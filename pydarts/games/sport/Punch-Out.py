################  RESTE A FAIRE

#### afficher une nouvelle image pour le vainqueur

################


# -*- coding: utf-8 -*-
# Game by David ! - modification par Ladite
######
from include import cplayer
from include import cgame
import random
import time
#
VERSION = '1.00'
DEBUG = {'debug-extra_info': False}
# Dictionnay of options - Text format only
OPTIONS = {'theme': 'default', 'max_round': '20', 'number_of_lives': '15', 'points':False}
# background image - relative to images folder - Name it like the game itself
LOGO = 'Punch-Out.png' # background image
# Columns headers - Better as a string
HEADERS = [ 'D1', 'D2', 'D3', '', 'Hit', '', 'PPR']
# How many darts per player and per round ? Yes ! this is a feature :)
NB_DARTS = 3
# Dictionary of stats and display order (For example : Points Per Darts and avg are displayed in ascending order)
GAME_RECORDS = {'Points Per Round': 'DESC'}

def check_players_allowed(nb_players):
   """
   Return the player number max for a game.
   """
   return 1 < nb_players < 8, VERSION, 8

class CPlayerExtended(cplayer.Player):
   """
   Extend the basic player
   """
   def __init__(self, ident, nb_columns, interior=False):
      super().__init__(ident, nb_columns, interior)

      self.character = 0
      self.targets = []
      self.lives = 0
      self.segments = []
      self.alive = True
      # Init Player Records to zero
      for record in GAME_RECORDS:
         self.stats[record]='0'

class Game(cgame.Game):
   """
   Class of the real game
   """
   def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
      super().__init__(display, game, nb_players, options, config, logs,rpi, dmd, video_player)
      # For rpi
      self.rpi = rpi
      self.logo = LOGO
      self.headers = HEADERS
      self.nb_darts = NB_DARTS
      self.nb_players = nb_players
      self.debug_info = False
      self.options = options
      #  Get the maximum round number
      self.max_round = int(self.options['max_round'])
      # GameRecords is the dictionnary of stats (see above)
      self.game_records = GAME_RECORDS
      
      # DEBUG dictionnary special for developer
      self.debuglevel = int(config.get_value('SectionGlobals', 'debuglevel', 0))
      if self.debuglevel == 2: #Ajouter les options du dictionnaire DEBUG
          #on charge les options (le dictionnaire DEBUG est inclus dans OPTIONS lorsque l'on est en debuglevel 2
          self.debug_info = options['debug-extra_info']
      
      self.points = options['points']
      print('self.point ests')
      print(self.points)
     

      
 ### determine les index et noms des joueurs     
      self.num_joueur = 0
      self.nom_joueur = ''
      self.joueur_actif = ''
      self.joueur_medic = ''
      self.index_joueur_medic = 0
      self.index_joueur_actif = 0    


      
   def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        if self.debug_info:
            info1=f"pre_dart_check players: actual_round, actual_player, player_launch"
            info2=f"pre_dart_check players: {actual_round: ^12}, {actual_player: ^13}, {player_launch: ^13}"
            self.affiche_info(info1, info2)
            
        return_code = 0
        if not players[actual_player].alive:
            return 4

        # gestion de l'affichage du segment
        self.show_hit = True

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                LST = self.check_handicap(players)
            except Exception as e:
                self.logs.error(f"Handicap failed : {e}")
            for player in players:
                # Init score
                player.score = 0
                # nb lives
                
                if self.points :
                    print('dans if self.points true')
                    self.lives = 300
                elif len(players) == 7 : 
                    self.lives = int(self.options['number_of_lives']) + 3
                else :
                    self.lives = int(self.options['number_of_lives'])
                player.lives = self.lives
                player.alive = True

            #change background
            self.display.display_background('bg_fighters')

            # random character defined
            characters = []
            for player in players:
                if self.display.file_class.get_full_filename(f'punch-out/{player.name}-1', 'images') is not None:
                    player.character = player.name
                else :
                    character = random.randint(1, 23)
                    while character in characters :
                        character = random.randint(1, 23)
                    player.character = f'j{character}'
                    characters.append(character)

        
        # Each new player
        if player_launch == 1:
            players[actual_player].segments = ['__','__','__']
            players[actual_player].round_points = 0
            self.save_turn(players)
            players[actual_player].pre_play_score = players[actual_player].score # Backup current score

            # change all others players hitbox
            medic = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
            for player in players:
                player.targets.clear()
                if actual_player != player.ident and player.lives > 0:
                    hits = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
                    for _ in range (0, 3) :
                        header = random.randint(0, len(hits) - 1)
                        player.targets.append(hits[header])
                        if hits[header] in medic :
                            medic.remove(hits[header])
                        hits.pop(header)

            # set medic hitbox of the actual player
            h = random.randint(0, len(medic) - 1)
            players[actual_player].targets.append(medic[h])

        # this player is game over
        if players[actual_player].alive :
            # Display target color of players
            segments = {}
            blinks = {}
            for player in players:
                if player.ident == actual_player:
                    color = 'green'
                    segments[f'S{player.targets[0]}'] = str(color)
                    segments[f'D{player.targets[0]}'] = str(color)
                    segments[f'T{player.targets[0]}'] = str(color)
                    segments[f'E{player.targets[0]}'] = str(color)
                else:
                    for header in player.targets:
                        color = 'red'
                        if segments.get(f'S{header}', None) is not None \
                                or blinks.get(f'S{header}', None) is not None:
                            blinks[f'S{header}'] = str(color)
                            blinks[f'D{header}'] = str(color)
                            blinks[f'T{header}'] = str(color)
                            blinks[f'E{header}'] = str(color)
                            if segments.get(f'S{header}', None) is not None:
                                segments.pop(f'S{header}')
                                segments.pop(f'D{header}')
                                segments.pop(f'T{header}')
                                segments.pop(f'E{header}')
                        else:
                            segments[f'S{header}'] = str(color)
                            segments[f'D{header}'] = str(color)
                            segments[f'T{header}'] = str(color)
                            segments[f'E{header}'] = str(color)

            segmentsAsStr = "|".join("{}#{}".format(*s) for s in segments.items()) #convertion du dict segments en string
            self.rpi.set_target_leds(segmentsAsStr)
            self.rpi.set_target_leds_blink("|".join("{}#{}".format(*s) for s in blinks.items()))

        return return_code

   def post_dart_check(self,hit,players,actual_round,actual_player,player_launch):
        """
        Post dart actions
        """
        
        handler = self.init_handler()
        
        if self.debug_info:
            info1 = f"post_dart_check : hit, players, actual_round, actual_player, player_launch"
            info2 = f"post_dart_check : {hit: ^3}, players, {actual_round: ^12}, {actual_player: ^13}, {player_launch: ^13}"
            self.affiche_info(info1, info2)
            
        return_code = 0 #même joueur

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += self.score_map[hit] ###1

        # stock the segment hitted
        players[actual_player].columns[player_launch - 1] = (hit[1:], 'int')
        players[actual_player].segments[player_launch - 1] = hit

        multi = self.get_hit_unit(hit)

        # test SB ou DB
        if hit == 'SB' or hit == 'DB' :
            #self.display.play_sound('punch-out_bull')
            handler['sound'] = 'punch-out_bull'
            liste = []
### BOUCLE pour determiner les joueur touches et le joueur qui frappe
            for index, player in enumerate(players):
                
### JOUEURS QUI ONT ETE TOUCHES
                if index != actual_player and players[index].alive:
                    self.num_joueur = index
                    self.nom_joueur = player.character ###player.name
                    if self.debug_info:
                        info1=f'Index du joueur touche par {hit} - {self.num_joueur}'
                        info2=f'nom joueur touche par {hit} - {self.nom_joueur}'
                        self.affiche_info(info1, info2)
  
### AJOUT des joueurs touches dans la liste
                    liste.append(self.num_joueur)
                    liste.append(self.nom_joueur)            
  
 ### JOUEUR QUI A TOUCHE LE SEGMENT HIT - joueur actuel                    
                if index == actual_player :
                    self.joueur_actif = player.character ### player.name
                    self.index_joueur_actif = actual_player
                    if self.debug_info:
                        info1=f'Nom du joueur qui a touche {hit} - {self.joueur_actif}'
                        info2=f'Index du joueur qui a touche {hit} - {self.index_joueur_actif}'
                        self.affiche_info(info1, info2)

                    
            if hit =='SB':
                multi = 1
            else:
                multi = 2
            playerHitted = True

            for player in players :
                if player.ident != actual_player and player.lives > 0:
                    if self.points :
                         player.lives -= self.score_map[hit] ###multi
                    else: 
                         player.lives -= multi
                    
            if self.points :
                players[actual_player].score += self.score_map[hit]    ####(len(players))*5
            else: 
                players[actual_player].score+=(len(players)) * multi
            self.show_hit = False
            
        else :
            # check d'un segment medic
            if int(hit[1:]) in players[actual_player].targets :
### BOUCLE pour determiner le joueur qui touche le segment MEDIC                
                for index, player in enumerate(players):
                    if index == actual_player :
                        self.joueur_medic = player.character ###player.name
                        self.index_joueur_medic = actual_player   ###index
                        if self.debug_info:
                            print ('Nom du joueur qui a touche le segment MEDIC')
                            print(self.joueur_medic)
                            print ('Index du joueur qui a touche le segment MEDIC')
                            print (self.index_joueur_medic)
                            
                    self.show_hit = False
                        
### definition de la taille des images 
                    if len(players) == 7 :
                        scalex = 268 * self.display.res['x'] / 1920
                        scaley = 488 * self.display.res['y'] / 1080
                    elif len(players) == 6 :
                        scalex = 300 * self.display.res['x'] / 1920
                        scaley = 546 * self.display.res['y'] / 1080
                    else :
                        scalex = 368 * self.display.res['x'] / 1920
                        scaley = 670 * self.display.res['y'] / 1080              

    
                    y = self.display.res['y'] / 2 - scaley / 2
                    marge = int((self.display.res['x'] - len(players) * scalex) / (len(players) + 1))
                    x = marge
                    
                    if self.index_joueur_medic > 0 :
                        x += (scalex + marge) * int(self.index_joueur_medic)
                    index99 = x
                        
### AJOUTE les points, JOUE le son medic                           
                #self.display.play_sound('punch-out_medic')
                handler['sound'] = 'punch-out_medic'
                if self.points :
                    players[actual_player].lives += self.score_map[hit] ###multi
                else: 
                    players[actual_player].lives += multi
                if players[actual_player].lives > self.lives :
                    players[actual_player].lives = self.lives
                    
### AFFICHE l'image RECUPERATION VIE
                self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{self.joueur_medic}-vie1', 'images'),index99, y, scalex, scaley, True, False, False)
                self.display.update_screen()
                time.sleep(0.9)

            # check d'un segment adversaire
            #self.show_hit = False
            playerHitted = False   
            
            liste = []
### BOUCLE pour determiner les joueur touches et le joueur qui frappe
            for index, player in enumerate(players):
                
### JOUEURS QUI ONT ETE TOUCHES
                if index != actual_player and int(hit[1:]) in player.targets :
                    self.num_joueur = index
                    self.nom_joueur = player.character ###player.name
                    if self.debug_info:
                        print ('Index du joueur touche - self.num_joueur')
                        print (self.num_joueur)
                        print ('nom joueur touche - self.nom_joueur')
                        print (self.nom_joueur)
                    
### AJOUT des joueurs touches dans la liste des animations uniquement si score > 0
                    if player.alive and player.lives > 0:
                        liste.append(self.num_joueur)
                        liste.append(self.nom_joueur)
### AJOUTE/SUPPRIME les points des joueurs 
                    if self.points :
                        players[actual_player].score += self.score_map[hit] ###multi
                        player.lives -= self.score_map[hit] ###multi
                    else: 
                        players[actual_player].score += multi
                        player.lives -= multi


                    players[actual_player].increment_hits(hit)
                    playerHitted = True
                    self.show_hit = False

### JOUEUR QUI A TOUCHE LE SEGMENT HIT - joueur actuel                    
                if index == actual_player :
                    self.joueur_actif = player.character ###player.name
                    self.index_joueur_actif = actual_player
                    if self.debug_info:
                        print ('Nom du joueur qui a touche le segment HIT - joueur actuel')
                        print(self.joueur_actif)
                        print ('Index du joueur qui a touche le segment HIT - joueur actuel')
                        print (self.index_joueur_actif)


        # test for a player KO
        for player in players:
            if player.lives <= 0 and player.alive:
                player.targets.clear()
                player.alive = False
                if self.points :
                         players[actual_player].lives += 30   ### test : ajout 1/10 des points de vies du depart a la place d augmenter le score
                else: 
                         players[actual_player].score += 5
                #self.display.play_sound('punch-out_ko')
                handler['sound'] = 'punch-out_ko'

### CONDITIONS si au moins un joueur est touche            
        if playerHitted :
            self.animation(multi, liste, len(players))
            
        winner = self.check_winner(players, actual_round, player_launch, actual_player)
        if winner > -1:
            self.winner = winner
            return 3
        
        # Time for shot or video ?
        handler['take_shot'] = self.time_to_take_shot_or_video(hit)
        handler['return_code'] = return_code
        return handler

        #return return_code

   def post_round_check(self, players, actual_round, actual_player):
        if self.debug_info:
            info1=f"Post_round_check : players, actual_round, actual_player"
            info2=f"Post_round_check : players, {actual_round: ^12}, {actual_player: ^13}"
            self.affiche_info(info1, info2)
            
        check_winner = self.check_winner(players, actual_round, 3, actual_player)
        if check_winner >= 0:
            return check_winner
        if actual_round < self.max_round:
            return -2
        else:
            return -1

   def check_winner(self, players, actual_round, player_launch, actual_player):
        # test for a winner
        if self.debug_info:
            info1=f"check_winner : players, actual_round, player_launch, actual_player"
            info2=f"check_winner : players, {actual_round: ^12}, {player_launch: ^13}, {actual_player: ^13}"
            self.affiche_info(info1, info2)
            
        alive_players = []
        for player in players :
            if player.alive :
                alive_players.append(player.ident)

        # victory by KO
        if len(alive_players) == 1 :
            self.winner =  alive_players[0]
            players[self.winner].score += 100
            return self.winner
        
        elif len(alive_players) == 0 or (player_launch == self.nb_darts and \
                actual_round >= self.max_round and actual_player == self.nb_players - 1):
            # victory by points if all are ko or its the last turn
            bestscoreid = -1
            bestscore = 0
            for player in players:
                if player.score >= bestscore:
                    if player.score != bestscore:
                        bestscore = player.score
                        bestscoreid = player.ident
                    else:
                        bestscoreid =  -1 # égalité
            return bestscoreid
        return -1

   def refresh_stats(self, players, actual_round):
      """
      Method to frefresh player.stat - Adapt to the stats you want. They represent mathematical formulas used to calculate stats. Refreshed after every launch
      """
      for player in players:
         player.stats['Points Per Round'] = player.avg(actual_round)

   def display_segment(self):
       """
       Set if a message is shown to indicate the segment hitted !
       """
       return self.show_hit

   def refresh_game_screen(self, players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player,TxtOnlogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None):
      """
      Refresh In-game screen
      """
      if self.debug_info:
          info1 = f"refresh_game_screen : players, actual_round, max_round, RemDarts, nb_darts, logo, headers, actual_player,TxtOnlogo=False, Wait=False, OnScreenButtons=None, showScores=True, end_of_game=False, endOfSet=None, Set=None, MaxSet=None"
          info2 = f"refresh_game_screen : players, {actual_round: ^12}, {max_round: ^9}, {RemDarts: ^8}, {nb_darts: ^8}, logo, headers, {actual_player: ^13}, {TxtOnlogo: ^15}, {Wait: ^10}, {str(OnScreenButtons): ^20}, {showScores: ^15}, {end_of_game: ^17}, {str(endOfSet): ^13}, {str(Set): ^8}, {str(MaxSet): ^11}"
          self.affiche_info(info1, info2, 110) # 
      # do not show the table scores
      ClickZones = {}
      # Clear
      self.display.screen.fill( (0, 0, 0) )
      # background image
      self.display.display_background('bg_fighters')

      self.affichage_players(players, actual_player, actual_round, max_round, end_of_game)
      
      if end_of_game :
          ClickZones = self.display.end_of_game_menu(logo, stat_button=False)

          
      self.display.update_screen()

      return ClickZones
    
   def early_player_button(self, players, actual_player, actual_round):
       """
       Run when player push PLAYERBUTTON before last dart
       return code :
           0. To use miss_button instead early_player_button
           1. Next player
           2. Last round reach
           3. Winner is
       """
       if self.debug_info:
           info1=f"early_player_button : players, actual_player, actual_round"
           info2=f"early_player_button : players, {actual_player: ^13}, {actual_round: ^12}"
           self.affiche_info(info1, info2)
           
       return_code = 1
       win = self.check_winner(players, actual_round, self.nb_darts, actual_player)
       if win != -1:
           self.winner = win
           return_code = 3
       else :
           last_player = False
           if actual_player == self.nb_players - 1:
               last_player = True
           else:
               k = self.nb_players - 1
               while k > actual_player:
                   if not players[k].alive :
                       last_player = True
                   else:
                       last_player = False
                   k -=1
                   
           if (actual_round >= self.max_round and last_player):            
               return_code = 2
       return return_code
    
   def miss_button(self, players, actual_player, actual_round, player_launch):
       """
       MISSED BUTTON
       """
       if self.debug_info:
           info1=f"miss_button : players, actual_player, actual_round, player_launch"
           info2=f"miss_button : players, {actual_player: ^13}, {actual_round: ^12}, {player_launch: ^13}"
           self.affiche_info(info1, info2)
       
       players[actual_player].segments[player_launch - 1] = ('MISS')   
       self.display.play_sound('miss')  
       return_code = 0
       return return_code

### eclaircissement du code
   def affichage_players(self, players, actual_player, actual_round, max_round, fin):
      if self.debug_info:
          info1=f"affichage_players : players, actual_player, actual_round, max_round, fin"
          info2=f"affichage_players : players, {actual_player: ^13}, {actual_round: ^12}, {max_round: ^9}, {fin: ^3}"
          self.affiche_info(info1, info2)
      # show players pictures and state
      colorset = self.display.colorset
      #scale img 368 * 670
      if len(players) == 7 :
          scalex = 268 * self.display.res['x'] / 1920
          scaley = 488 * self.display.res['y'] / 1080
      elif len(players) == 6 :
          scalex = 300 * self.display.res['x'] / 1920
          scaley = 546 * self.display.res['y'] / 1080
      else :
          scalex = 368 * self.display.res['x'] / 1920
          scaley = 670 * self.display.res['y'] / 1080

      y = self.display.res['y'] / 2 - scaley / 2
      marge = int((self.display.res['x'] - len(players) * scalex) / (len(players) + 1))

### Determine qui est le gagant pour afficher une image WINNER
      
      alive_players = []
      for player in players:
        if player.lives <= 0 and player.alive:
            player.alive = False
            
      for player in players :
          if player.alive :
              alive_players.append(player.ident)
              alive_players.append(player.character)
              
### SI l INDEX du joueur correspond a la CASE 1 - index88 = position de l image a afficher
      x = marge
      index88 = x
      if len(alive_players) == 2 and alive_players[0] > 0:
          index88 = (scalex + marge) * int(alive_players[0])

      for i,p in enumerate(players):
          # find the good character picture to show
          ### New
          if not p.alive:
              level = 6 # Si on est ko on prend la 6
          else :
              #dans le cas ou on aurait des  images 1 à 5 différentes
              # 1 bonne santé --> 5 = défiguré --> 6 = KO 
              '''
              level = int(5 - (p.lives // (self.lives // 5)))
              print('level')
              print(level)
              if level < 1 :
                  level = 1
              elif level > 5:
                  level = 5
              '''    
              if actual_player == p.ident :
                  level = 5
              elif p.lives>self.lives-(self.lives / 4) :
                  level = 1
              else :
                  level = int(5 - ((p.lives // (self.lives / 5) )+1))        
                  
                  
                  
          
          self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{p.character}-{level}', 'images'),x, y, scalex, scaley, True, False, False)
          self.logs.debug(f"character img loaded : {p.character}-{level}.png")
          
          if self.debug_info:
              print(f"level = {level}")
              if fin: #special pour tracer le programme
                  fin = True
                  print(f"DEBUG - character img loaded : {p.character}-{level}.png")
                  print(f"{p.name} - {p.alive} - {p.targets} - {len(p.targets)}")

          if (i == actual_player and len(p.targets) == 1) or len(p.targets) == 1 :
              self.display.blit_text(p.name, x, y + scaley, scalex, scaley / 4, color=colorset['fighters-actual-player'])
              self.display.display_image(self.display.file_class.get_full_filename('punch-out/fighters_medic', 'images'),x + scalex / 2 - scalex / 6, y + scaley * 2 / 3, scalex / 3, scalex / 3, False, False, False)
              self.display.blit_text(str(p.targets[0]),x + scalex / 2 - scalex / 6, y + scaley * 2 / 3 + 20, scalex / 3, scalex / 3, color=colorset['fighters-medic'])
          elif p.alive :
              self.display.blit_text(p.name, x, y + scaley, scalex ,scaley / 4, color=colorset['fighters-alive-player'])
              self.display.display_image(self.display.file_class.get_full_filename('punch-out/hit', 'images'),x, y, scalex / 3, scalex / 3, True, False, False)
              self.display.blit_text(str(p.targets[0]),x, y,scalex / 3,scalex / 4, color=colorset['fighters-targets'])
              self.display.display_image(self.display.file_class.get_full_filename('punch-out/hit', 'images'),x + scalex - scalex / 3, y, scalex / 3, scalex / 3, True, False, False)
              self.display.blit_text(str(p.targets[1]),x + scalex - scalex / 3, y, scalex / 3, scalex / 4, color=colorset['fighters-targets'])
              self.display.display_image(self.display.file_class.get_full_filename('punch-out/hit', 'images'),x + scalex / 2 - scalex / 6, y, scalex / 3, scalex / 3, True, False, False)
              self.display.blit_text(str(p.targets[2]),x + scalex / 2 - scalex / 6, y, scalex / 3,scalex / 4, color=colorset['fighters-targets'])
#          elif colorset['fighters-dead-player'] is not None:
          elif len(p.targets) == 0 and not p.alive:
              self.display.blit_text(p.name, x, y + scaley, scalex ,scaley / 4, color=colorset['fighters-dead-player'])

          # show lives and score
          self.display.blit_text(str(p.lives),x + scalex / 5, y + scaley - scalex / 4, scalex / 3, scalex / 4, color=colorset['fighters-scores'])
          self.display.blit_text(str(p.score),x + scalex - scalex / 3, y + scaley - scalex / 4, scalex / 3, scalex / 4, color=colorset['fighters-scores'])

          #if not p.alive :
              #self.display.display_image(self.display.file_class.get_full_filename('punch-out/fighters_ko', 'images'),x, y, scalex, scaley, True, False, False)
              #print ('n affiche pas la croix')
          if self.winner >=0 and self.winner == i:
              self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{players[self.winner].character}-win', 'images'),x, y, scalex, scaley, True, False, False)
              print (f'punch-out/vainqueur')
          x += scalex + marge

### Affiche l'image du vainqueur
      #if len(alive_players) == 2 :
#          self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{alive_players[1]}-win', 'images'),index88, y, scalex, scaley, True, False, False)
#          print (f'punch-out/vainqueur') 
      # show round state
      self.display.blit_rect(self.display.res['x']/8 - scalex/2, 0, scalex,y*2/3, (0, 0, 0), Alpha=150)
      self.display.blit_text(f"{self.display.lang.translate('round')} {actual_round} / {max_round}" ,self.display.res['x']/8 - scalex/2,0,scalex, y/3, color=colorset['fighters-round'])
   
      # show segments hitted on the round
      self.display.blit_text(" / ".join(players[actual_player].segments) ,self.display.res['x']/8 - scalex/2,y/3,scalex,y/3, color=colorset['fighters-darts'])


   def build_liste_index(self, liste, marge, scalex):
### TEST AVEC BOUCLE - DETERMINE LES INDEX DES JOUEURS TOUCHES
       i = 0
       j = 0
       list_index = []
       for i in range(len(liste)) :
### SI l INDEX du joueur touche correspond a la CASE 1         
            x = marge
            if int(liste[j]) > 0:
                x += (scalex + marge ) * int(liste[j])
            list_index.append(x)
#            print ('variable I')
#            print (i) 
            i += 2
#            print ('variable J')
#            print (j)
            if j < len(liste) :
                j += 2
            if j >= len(liste) :
                j = len(liste)-2
#            print ('liste_index')
#            print (liste_index)
            
       return list_index
       
   def animation(self, nb_coups, liste, len_players):
       if self.debug_info:
           info1=f"animation : nb_coups, liste, len_players"
           info2=f"animation : {nb_coups: ^8}, {liste}, {len_players: ^11}"
           self.affiche_info(info1, info2)
           
       coups = 0
       len_liste = len(liste)
### definition de la taille des images 
       if len_players == 7 :
           scalex = 268 * self.display.res['x'] / 1920
           scaley = 488 * self.display.res['y'] / 1080
       elif len_players == 6 :
           scalex = 300 * self.display.res['x'] / 1920
           scaley = 546 * self.display.res['y'] / 1080
       else :
           scalex = 368 * self.display.res['x'] / 1920
           scaley = 670 * self.display.res['y'] / 1080  

       y = self.display.res['y'] / 2 - scaley / 2
       marge = int((self.display.res['x'] - len_players * scalex) / (len_players + 1))
       
       x = marge
       x += (scalex + marge) * int(self.index_joueur_actif)
       index99 = x       
       liste_index = []
       liste_index = self.build_liste_index(liste, marge, scalex)
       print (f'touche {nb_coups} fois')
#       if len_liste == 14 :
#                nom_joueur1 = liste[1]
#                nom_joueur2 = liste[3]
#                nom_joueur7 = liste[13]
       
       while coups < nb_coups:
           coups += 1
           image_hit = f'hit{coups}'
           image_touche = f'touche{coups}'
           if self.debug_info:
               print(f"image_hit = {image_hit}")
               print(f"image_touche = {image_touche}")
               test = f'punch-out/{self.joueur_actif}-{image_hit}'
               print(f" test = {test}")
           self.display.play_sound('punch-out_hit')                      
           ### joueur qui frappe
           self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{self.joueur_actif}-{image_hit}', 'images'),index99, y, scalex, scaley, True, False, False)
           ### joueur touche
           if len_liste == 2 :
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[1]}-{image_touche}', 'images'),liste_index[0], y, scalex, scaley, True, False, False)
           if len_liste == 4 :
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[1]}-{image_touche}', 'images'),liste_index[0], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[3]}-{image_touche}', 'images'),liste_index[1], y, scalex, scaley, True, False, False)
           if len_liste == 6 :
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[1]}-{image_touche}', 'images'),liste_index[0], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[3]}-{image_touche}', 'images'),liste_index[1], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[5]}-{image_touche}', 'images'),liste_index[2], y, scalex, scaley, True, False, False)
           if len_liste == 8 :
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[1]}-{image_touche}', 'images'),liste_index[0], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[3]}-{image_touche}', 'images'),liste_index[1], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[5]}-{image_touche}', 'images'),liste_index[2], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[7]}-{image_touche}', 'images'),liste_index[3], y, scalex, scaley, True, False, False)
           if len_liste == 10 :
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[1]}-{image_touche}', 'images'),liste_index[0], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[3]}-{image_touche}', 'images'),liste_index[1], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[5]}-{image_touche}', 'images'),liste_index[2], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[7]}-{image_touche}', 'images'),liste_index[3], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[9]}-{image_touche}', 'images'),liste_index[4], y, scalex, scaley, True, False, False)
           if len_liste == 12 :
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[1]}-{image_touche}', 'images'),liste_index[0], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[3]}-{image_touche}', 'images'),liste_index[1], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[5]}-{image_touche}', 'images'),liste_index[2], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[7]}-{image_touche}', 'images'),liste_index[3], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[9]}-{image_touche}', 'images'),liste_index[4], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[11]}-{image_touche}', 'images'),liste_index[5], y, scalex, scaley, True, False, False)
           if len_liste == 14 :
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[1]}-{image_touche}', 'images'),liste_index[0], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[3]}-{image_touche}', 'images'),liste_index[1], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[5]}-{image_touche}', 'images'),liste_index[2], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[7]}-{image_touche}', 'images'),liste_index[3], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[9]}-{image_touche}', 'images'),liste_index[4], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[11]}-{image_touche}', 'images'),liste_index[5], y, scalex, scaley, True, False, False)
               self.display.display_image(self.display.file_class.get_full_filename(f'punch-out/{liste[13]}-{image_touche}', 'images'),liste_index[6], y, scalex, scaley, True, False, False)
               
           self.display.update_screen()
           time.sleep(0.3)
           
   def affiche_info(self, info1, info2, split = 0, car = ','):
       if split > 0 and len(info1) > split :
           while (info1[split] != car) and (split > 0): #on va couper avant la variable
               split -= 1
           split += 1 #on saute car   
           info = info1[:split] + '\n' + info2[:split]
           info2 = info1[split:] + '\n' + info2[split:]
           info1 = info
       print(info1)
       print(info2)
       
       
        
