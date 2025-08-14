# -*- coding: utf-8 -*-
# Game by ... laDite!
########
import random
from include import cplayer
from include import cgame
#


### PISTOLET - BOUCLIER NE VA PAS -- VOIR SI C EST PAS A CAUSE DE LA CONDITION LIGNE 80


############
# Game Variables
############
OPTIONS = {'theme': 'default', 'max_round': 8, 'simple50': False}
GAME_RECORDS = {'Points Per Round': 'DESC', 'Points Per Dart': 'DESC'}
NB_DARTS = 3  # Total darts the player has to play
LOGO = 'Treasure.png'
HEADERS = ['D1', 'D2', 'D3', '', 'Tr1', 'Tr2', 'Tr3'] # Columns headers - Must be a string
VERSION = '1.00'

def check_players_allowed(nb_players):
    """
    Check if number of players is ok according to options
    """
    return nb_players >= 2 and nb_players <= 12, VERSION, 12
    
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
        #self.multiplicateur = 1 

class Game(cgame.Game):
    """
    Treasure game class
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

        #self.leds = True
        self.grid = []
        self.items = ''
        self.index = 0
  
    def pre_dart_check(self, players, actual_round, actual_player, player_launch):
        """
        Actions done before each dart throw - for example, check if the player is allowed to play
        """
        return_code = 0
        
        self.display.specialbg = 'bg_treasure'
        self.display.display_background(image='bg_treasure.jpg') 
        
        if player_launch == 1 :
            players[actual_player].reset_darts()
            ### Desactive le bouclier du joueur lors de son premier lance
            players[actual_player].bouclier = False   
        
        
        ### ajout player_launch 2 et 3 pour recharger les cadeaux et avoir la possibilite de toucher plusieurs fois le mm tresor          
        if player_launch == 1 or player_launch == 2 or player_launch == 3 :
            #players[actual_player].reset_darts()
            ### Desactive le bouclier du joueur lors de son premier lance
            #players[actual_player].bouclier = False
            
            if False :
                ### POUR FAIRE TESTS METTRE TRUE
                items = [['boite_x10', 1], ['boite_x2', 2], ['boite_x3', 3], ['boite_x4', 4], ['boite_x5', 5],
                    ['diamant', 6], ['lingot', 7], ['crane_jaune', 8], ['crane_violet', 9],
                    ['crane_rouge', 10], ['crane_bleu', 11], ['grenade', 12], ['couteau', 13], ['epee', 14], ['bouclier', 15],
                    ['rubis', 16], ['pistolet', 17], ['coffre', 18], ['boite_x25', 19], ['bombe', 20]]

                self.grid = items
            else:
                items = ['boite_x10', 'boite_x2', 'boite_x3', 'boite_x4', 'boite_x5',
                    'diamant', 'lingot', 'crane_jaune', 'crane_violet',
                    'crane_rouge', 'crane_bleu', 'grenade', 'couteau', 'epee', 'bouclier',
                    'rubis', 'pistolet', 'coffre', 'boite_x25', 'bombe']
                
                chiffre = [i for i in range(1, 21)]

                grid = []

                for k in items:
                    h = random.choice(chiffre)
                    grid.append([k, int(h)])
                    chiffre.remove(h)
        
                self.grid = grid 

        # Set score at startup
        if actual_round == 1 and player_launch == 1 and actual_player == 0:
            try:
                self.check_handicap(players)
            except Exception as exception: # pylint: disable=broad-except
                self.logs.error(f"Handicap failed : {exception}")

            for player in players:
                # Init score
                player.score = 0
                player.bouclier = False
                # Lives

        # Each new player
        if player_launch == 1:
            players[actual_player].round_points = 0
            players[actual_player].pre_play_score = players[actual_player].score

            #Reset display Table
            players[actual_player].columns = []
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

    def post_dart_check(self, hit, players, actual_round, actual_player, player_launch):
        """
        Function run after each dart throw - for example, add points to player
        """
        
        handler = self.init_handler()
        
        ### dit le chiffre touche
        self.display.sound_for_touch(hit)

        score = 0
        ### SI ON TOUCHE SB OU DB, ON CHOISI UN SEGME?T AU HASARD 
        if hit == 'SB' :
                print ('bull')
                i = random.randrange(20) + 1
                print('i - sb')
                print(i)
                for k, v in enumerate(self.grid):
                        if i == int(v[1]) : 
                                self.items = v[0]
                                print('v0 = ')
                                print(v[0])
                
        if hit == 'DB' :
                print('dbull')
                i = random.randrange(20) + 1
                print('i - db')
                print(i)
                for k, v in enumerate(self.grid):
                        if i == int(v[1]) : 
                                self.items = v[0]
                                print('v0 = ')
                                print(v[0])
    
        if hit[1:] != 'B' :
        ### TEST SI LE CHIFFRE TOUCHE EST DANS LA LISTE "self.grid"  --- PLUS NECESSAIRE CAR REATTRIBUE A CHAQUE FLECHE
                for k, v in enumerate(self.grid):
                        if int(hit[1:]) == int(v[1]) : 
                                self.items = v[0]
                                ### recupere l index du tresor a supprimer
                                test = [v[0],v[1]]
                                index = self.grid.index(test)

                                del(self.grid[index])
                                
        
        ### SELON LE CONTENU TROUVE DANS LA LISTE, ON EFFECTUE LES TACHES ASSOCIEES      
        ### changement des boites bonus x2,x3,x4,x5,x10 par x12,x14,x16,x18,x20 pour augmenter les points car les malus font perdre bcp          
        ### SEUL LES POINTS ET MESSAGE DMD SONT MODIFIES POUR EVITER TROP DE CHANGEMENT

## test pour ennuyer sacha
                '''
                print('name')
                print(players[actual_player].name) 
                if players[actual_player].name == 'Sacha' :
                        
                        if player_launch == 1 :
                                self.items = 'grenade'
                        elif player_launch == 2 :
                                self.items = 'bombe'
                        elif player_launch == 3 :
                                self.items = 'crane_rouge'
                '''        
        if self.items == 'boite_x25' :
                print('boite x25 trouvee')
                #self.dmd.send_text("Segment X25")
                handler['dmd'] = 'Segment X25'
                #self.display.play_sound('treasure_boite_x25')
                handler['sound'] = 'treasure_boite_x25'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/boite_x25', 'videos'))
                handler['video'] = 'treasure/boite_x25'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/boite_x25', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/boite_x25', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/boite_x25', 'image']        
                score = self.score_map[hit] * 25
                self.items = ''
        elif self.items == 'rubis' :
                print('rubis trouvee')
                #self.display.play_sound('treasure_rubis')
                handler['sound'] = 'treasure_rubis'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/rubis', 'videos'))
                handler['video'] = 'treasure/rubis'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/rubis', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/rubis', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/rubis', 'image']        
                #self.dmd.send_text("Rubis Trouvé")
                handler['dmd'] = 'Rubis Trouvé'
                score = 750
                self.items = ''
        elif self.items == 'coffre' : 
                print('coffre trouve')
                #self.display.play_sound('treasure_coffre')
                handler['sound'] = 'treasure_coffre'
                
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/coffre', 'videos'))
                handler['video'] = 'treasure/coffre'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/coffre', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/coffre', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/coffre', 'image']        
                #self.dmd.send_text("Coffre Trouvé")
                handler['dmd'] = 'Coffre Trouvé'
                #score = 2000 

                if players[actual_player].score <= 0 :
                        score1 = players[actual_player].score
                        score = abs(score1) + (abs(round(score1 /2))) 
                        #score2 = score-score1

                else:
                        score1 = players[actual_player].score
                        score = score1 + round((score1 /2))

                        #score *= 2
                
                self.items = ''               
        elif self.items == 'bombe' :
                print('bombe trouvee')
                #self.display.play_sound('treasure_bombe')
                handler['sound'] = 'treasure_bombe'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/bombe', 'videos'))
                handler['video'] = 'treasure/bombe'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/bombe', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/bombe', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/bombe', 'image'] 
                #self.dmd.send_text("Bombe Trouvée")
                handler['dmd'] = 'Bombe Trouvée'
                ### condition si joueur a un bouclier
                if players[actual_player].bouclier :
                        score = self.score_map[hit]
                        self.display.message([self.display.lang.translate('Treasure-protect')], 1000, None, 'middle', 'big')
                else:
                       
                        if players[actual_player].score <= 0 :
                                score1 = players[actual_player].score 
                                score = score1 - round(score1 /2) 
                                #score2 = score-score1
        
                        else:
                                score1 = players[actual_player].score #/2
                                score = round(- score1 /2)
                                
                self.items = ''        
        
        elif self.items == 'pistolet' :
                print('pistolet trouve') 
                #self.display.play_sound('treasure_pistolet')
                handler['sound'] = 'treasure_pistolet'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/pistolet', 'videos'))
                handler['video'] = 'treasure/pistolet'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/pistolet', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/pistolet', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/pistolet', 'image'] 
                #self.dmd.send_text("Pistolet Trouvé")
                handler['dmd'] = 'Pistolet Trouvé'
                
                ### vole 750 points a un joueur 
                index_joueur = []
                points_vole = 0
                for player in players :
                        if player.ident != players[actual_player].ident :
                                #index_joueur.append(player.ident)
                                if not player.bouclier :
                                        player.score -= 250
                                        points_vole += 250
                                        #score = 750

                                else:
                                        self.display.message([self.display.lang.translate('Treasure-protect2')], 1000, None, 'middle', 'big')
                                        points_vole += 0
                                        #score = 0
                score = points_vole
                '''
                choix_joueur = random.choice(index_joueur)    
        
                for player in players :
                        if player.ident == choix_joueur :
                                if not player.bouclier :
                                        player.score -= 750
                                        score = 750

                                else:
                                        self.display.message([self.display.lang.translate('Treasure-protect2')], 1000, None, 'middle', 'big')
                                        score = 0
                '''
                self.items = ''        
              
        elif self.items == 'boite_x10' :
                print('boite x20 trouvee')
                #self.dmd.send_text("Segment X20")
                handler['dmd'] = 'Segment X20'
                #self.display.play_sound('treasure_boite_x10')
                handler['sound'] = 'treasure_boite_x10'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/boite_x10', 'videos'))
                handler['video'] = 'treasure/boite_x10'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/boite_x10', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/boite_x10', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/boite_x10', 'image']        
                score = self.score_map[hit] * 20
                self.items = ''
                
        elif self.items == 'boite_x2' :
                print('boite x12 trouvee')
                #self.display.play_sound('treasure_boite_x2')
                handler['sound'] = 'treasure_boite_x2'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/boite_x2', 'videos'))
                handler['video'] = 'treasure/boite_x2'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/boite_x2', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/boite_x2', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/boite_x2', 'image']        
                #self.dmd.send_text("Segment X12")
                handler['dmd'] = 'Segment X12'
                score = self.score_map[hit] * 12
                self.items = ''
                
        elif self.items == 'boite_x3' : 
                print('boite x3 trouvee')
                #self.display.play_sound('treasure_boite_x3')
                handler['sound'] = 'treasure_boite_x3'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/boite_x3', 'videos'))
                handler['video'] = 'treasure/boite_x3'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/boite_x3', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/boite_x3', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/boite_x3', 'image']        
                #self.dmd.send_text("Segment X14")
                handler['dmd'] = 'Segment X14'
                score = self.score_map[hit] * 14
                self.items = ''
                
        elif self.items == 'boite_x4' :
                print('boite x4 trouvee') 
                #self.display.play_sound('treasure_boite_x4')
                handler['sound'] = 'treasure_boite_x4'
                #self.dmd.send_text("Segment X16")
                handler['dmd'] = 'Segment X16'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/boite_x4', 'videos')) 
                handler['video'] = 'treasure/boite_x4'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/boite_x4', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/boite_x4', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/boite_x4', 'image']        
                score = self.score_map[hit] * 16
                self.items = ''
                      
        elif self.items == 'boite_x5' : 
                print('boite x5 trouvee')
                #self.display.play_sound('treasure_boite_x5')
                handler['sound'] = 'treasure_boite_x5'
                #self.dmd.send_text("Segment X18")
                handler['dmd'] = 'Segment X18'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/boite_x5', 'videos'))
                handler['video'] = 'treasure/boite_x5'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/boite_x5', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/boite_x5', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/boite_x5', 'image']        
                score = self.score_map[hit] * 18
                self.items = ''
                
        elif self.items == 'diamant' :
                print('diamant trouvee')
                #self.display.play_sound('treasure_diamant')
                handler['sound'] = 'treasure_diamant'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/diamant', 'videos'))
                handler['video'] = 'treasure/diamant'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/diamant', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/diamant', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/diamant', 'image']        
                #self.dmd.send_text("Diamant Trouvé")
                handler['dmd'] = 'Diamant Trouvé'
                score = 1000
                self.items = ''
                
        elif self.items == 'lingot' : 
                print('lingot trouvee')
                #self.display.play_sound('treasure_lingot')
                handler['sound'] = 'treasure_lingot'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/lingot', 'videos'))
                handler['video'] = 'treasure/lingot'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/lingot', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/lingot', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/lingot', 'image']        
                #self.dmd.send_text("Lingot Trouvé")
                handler['dmd'] = 'Lingot Trouvé'
                #score = 0 
                for player in players :
                        if player.ident == players[actual_player].ident :
                                if player.score <= 0 :
                                        score = abs(player.score)
                                        #player.score = 0
                                else:
                                        score = player.score  
                                        #player.score *= 2
                self.items = ''
                
        elif self.items == 'crane_jaune' :
                print('crane jaune trouve') 
                #self.display.play_sound('treasure_crane_jaune')
                handler['sound'] = 'treasure_crane_jaune'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/crane_jaune', 'videos'))
                handler['video'] = 'treasure/crane_jaune'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/crane_jaune', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/crane_jaune', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/crane_jaune', 'image']        
                #self.dmd.send_text("Crane Jaune Trouvé")
                handler['dmd'] = 'Crane Jaune Trouvé'
                
                ### condition si joueur a un bouclier
                if players[actual_player].bouclier :
                        score = self.score_map[hit]
                        self.display.message([self.display.lang.translate('Treasure-protect')], 1000, None, 'middle', 'big')
                else:
                        score = - 100
                self.items = ''
                
        elif self.items == 'crane_bleu' :
                print('crane bleu trouve')    
                #self.display.play_sound('treasure_crane_bleu') 
                handler['sound'] = 'treasure_crane_bleu'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/crane_bleu', 'videos')) 
                handler['video'] = 'treasure/crane_bleu'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/crane_bleu', 'image']
                        players[actual_player].columns[0] = ['-' , 'txt']
                        players[actual_player].columns[1] = ['-' , 'txt']
                        players[actual_player].columns[2] = ['-' , 'txt']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/crane_bleu', 'image']
                        players[actual_player].columns[1] = ['-' , 'txt']
                        players[actual_player].columns[2] = ['-' , 'txt']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/crane_bleu', 'image'] 
                        players[actual_player].columns[2] = ['-' , 'txt']
                #self.dmd.send_text("Crane Bleu Trouvé")  
                handler['dmd'] = 'Crane Bleu Trouvé'
                
                ### condition si joueur a un bouclier
                if players[actual_player].bouclier :
                        score = self.score_map[hit]
                        self.display.message([self.display.lang.translate('Treasure-protect')], 1000, None, 'middle', 'big')
                elif actual_round >= self.max_round and actual_player == self.nb_players - 1:
                    self.winner = self.check_winner(players)
                    if self.winner is not None:
                        return_code = 3
                    else:
                        # No winner : last round reached
                        return_code = 2
                else:
                        return 1
                        score = 0
                self.items = ''
                
        elif self.items == 'crane_violet' :
                print('crane violet trouve')
                #self.display.play_sound('treasure_crane_violet')
                handler['sound'] = 'treasure_crane_violet'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/crane_violet', 'videos'))
                handler['video'] = 'treasure/crane_violet'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/crane_violet', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/crane_violet', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/crane_violet', 'image'] 
                #self.dmd.send_text("Crane Violet Trouvé")
                handler['dmd'] = 'Crane Violet Trouvé'
                ### condition si joueur a un bouclier
                if players[actual_player].bouclier :
                        score = self.score_map[hit]
                        self.display.message([self.display.lang.translate('Treasure-protect')], 1000, None, 'middle', 'big')
                else:
                        score = - 300
                self.items = ''
                
        elif self.items == 'crane_rouge' :
                print('crane rouge trouve')
                #self.display.play_sound('treasure_crane_rouge')
                handler['sound'] = 'treasure_crane_rouge'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/crane_rouge', 'videos'))
                handler['video'] = 'treasure/crane_rouge'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/crane_rouge', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/crane_rouge', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/crane_rouge', 'image'] 
                #self.dmd.send_text("Crane Rouge Trouvé")
                handler['dmd'] = 'Crane Rouge Trouvé'
                ### condition si joueur a un bouclier
                if players[actual_player].bouclier :
                        score = self.score_map[hit]
                        self.display.message([self.display.lang.translate('Treasure-protect')], 1000, None, 'middle', 'big')
                else:
                        score = - 500
                self.items = ''
                
        elif self.items == 'grenade' :
                print('grenade trouve')
                #self.display.play_sound('treasure_grenade')
                handler['sound'] = 'treasure_grenade'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/grenade', 'videos'))
                handler['video'] = 'treasure/grenade'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/grenade', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/grenade', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/grenade', 'image'] 
                #self.dmd.send_text("grenade Trouvée")
                handler['dmd'] = 'Grenade Trouvée'
                ### condition si joueur a un bouclier
                if players[actual_player].bouclier :
                        score = self.score_map[hit]
                        self.display.message([self.display.lang.translate('Treasure-protect')], 1000, None, 'middle', 'big')
                else:
                        score = - 1000
                self.items = ''
                
        elif self.items == 'couteau' :
                print('couteau trouve') 
                #self.display.play_sound('treasure_couteau')
                handler['sound'] = 'treasure_couteau'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/couteau', 'videos'))
                handler['video'] = 'treasure/couteau'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/couteau', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/couteau', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/couteau', 'image'] 
                #self.dmd.send_text("Couteau Trouvé")
                handler['dmd'] = 'Couteau Trouvé'
                
                ### vole 300 points a un joueur 
                index_joueur = []
                for player in players :
                        if player.ident != players[actual_player].ident :
                                index_joueur.append(player.ident)

                choix_joueur = random.choice(index_joueur)    
        
                for player in players :
                        if player.ident == choix_joueur :
                                if not player.bouclier :
                                        player.score -= 300
                                        score = 300

                                else:
                                        self.display.message([self.display.lang.translate('Treasure-protect2')], 1000, None, 'middle', 'big')
                                        score = 0
                self.items = ''
                
        elif self.items == 'epee' :
                print('epee trouve')
                #self.display.play_sound('treasure_epee')
                handler['sound'] = 'treasure_epee'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/epee', 'videos'))
                handler['video'] = 'treasure/epee'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/epee', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/epee', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/epee', 'image'] 
                #self.dmd.send_text("Epée Trouvée")
                handler['dmd'] = 'Epée Trouvée'
                
                ### vole 600 points a un joueur
                index_joueur = []
                for player in players :
                        if player.ident != players[actual_player].ident :
                                index_joueur.append(player.ident)
   
                choix_joueur = random.choice(index_joueur)    
        
                for player in players :
                        if player.ident == choix_joueur :
                                if not player.bouclier :
                                        player.score -= 600
                                        score = 600
                                        bouclier = False
                                else:
                                        self.display.message([self.display.lang.translate('Treasure-protect2')], 1000, None, 'middle', 'big')
                                        score = 0
                self.items = ''
                
        elif self.items == 'bouclier' :
                print('bouclier trouve')
                #self.display.play_sound('treasure_bouclier')
                handler['sound'] = 'treasure_bouclier'
                #self.video_player.play_video(self.display.file_class.get_full_filename(f'treasure/bouclier', 'videos'))
                handler['video'] = 'treasure/bouclier'
                if player_launch == 1 :
                        players[actual_player].columns[4] = [f'treasure/bouclier', 'image']
                elif player_launch == 2 :
                        players[actual_player].columns[5] = [f'treasure/bouclier', 'image']
                elif player_launch == 3 :
                        players[actual_player].columns[6] = [f'treasure/bouclier', 'image'] 
                #self.dmd.send_text("Bouclier Trouvé")
                handler['dmd'] = 'Bouclier Trouvé'
                score = self.score_map[hit] 
                ### ajoute bouclier au joueur pour neutraliser les effets negatif pendant un tour
                players[actual_player].bouclier = True
                self.items = ''
                
        else :
                score = self.score_map[hit]
                print('self.items vide car pas dans la liste')
        
        
        return_code = 0
        
        players[actual_player].add_dart(actual_round, player_launch, hit, score=score)

        players[actual_player].score += score
        players[actual_player].round_points += score
        players[actual_player].points += score
        
        

        # Store what he played in the table
        players[actual_player].columns[player_launch - 1] = (score, 'int')

        # Record total dart thrown, total hits (S=1, D=2, T=3) and refresh players stats
        players[actual_player].darts_thrown += 1
        players[actual_player].increment_hits(hit)
        self.refresh_stats(players, actual_round)

        # Check for end of game (no more rounds to play)
        if player_launch == self.nb_darts and actual_round >= self.max_round \
                and actual_player == len(players) - 1:
            self.winner = self.check_winner(players)
            if self.winner is not None:
                return_code = 3
            else:
                # No winner : last round reached
                return_code = 2
                
        # Time for shot or video ?
        handler['take_shot'] = self.time_to_take_shot_or_video(hit)
        handler['return_code'] = return_code
        return handler

        #return return_code

    def post_round_check(self, players, actual_round, actual_player):
        """
        Post round checks
        When PLAYER BUTTON is pressed on last round of last player
        """

        if actual_round >= self.max_round and actual_player == len(players) - 1:
            # Last round, last player
            return self.check_winner(players)
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

    def miss_button(self, players, actual_player, actual_round, player_launch):
        '''
        Miss button
        '''
        players[actual_player].columns[player_launch-1] = ('MISS', 'str')
        self.display.play_sound('miss')
        players[actual_player].darts_thrown += 1

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
