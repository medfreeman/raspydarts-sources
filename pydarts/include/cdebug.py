# -*- coding: utf-8 -*-
"""
Debug by Manu
"""

import pygame
from pygame import gfxdraw
from math import sqrt
from include import cgame

seg_pos = {'E': (143,151),'D' : (133,141), 'S' : (81,131,20,70), 'T':(72,79), 'SB' : (10,18), 'DB' : (0,8)}
        
code = {'20': (0,0), '1' : (1,0), '18': (0,1), '4': (1,1), '13': (0,2), '6': (1,2), \
        '10': (0,3), '15': (1,3), '2' : (0,4), '17':(1,4), '3' : (0,5), '19':(1,5), \
        '7' : (0,6), '16': (1,6), '8' : (0,7), '11':(1,7), '14': (0,8), '9': (1,8), \
        '12': (0,9), '5' : (1,9)}
    
class Debug(cgame.Game):
    def __init__(self, display, game, nb_players, options, config, logs, rpi, dmd, video_player):
        super().__init__(display, game, nb_players, options, config, logs, rpi, dmd, video_player)
        self.L = 200
        self.H = 400
        self.nb_players = nb_players
        self.root_dir = '/pydarts'
        self.logsDir = f'{self.root_dir}/logs'
        self.name = game
        self.gameDebugFile = f'{self.logsDir}/{self.name}-{nb_players}.dbg'
        self.Ffile = None
        self.rpi = rpi

    def press_x(self):
        pygame.event.clear()
        new_event = pygame.event.Event(pygame.KEYDOWN, unicode ='x', key=pygame.K_x)
        pygame.event.post(new_event)
        new_event = pygame.event.Event(pygame.KEYUP, unicode ='x', key=pygame.K_x)
        pygame.event.post(new_event)
        
        
    def record(self,data = f"Empty data\n"):
        print (f"Debug file : {self.gameDebugFile}")
        if self.Ffile is None:
            try:
                self.Ffile = open(self.gameDebugFile, 'w')
                self.Ffile.write(f"#{self.name}\n")
            except:
                print(f"Unable to write debug game file {self.gameDebugFile}. Please check permissions. Exiting.\n")
                exit(1)
        else:
            try:
                print(f"writing data : {data}")
                self.Ffile.write(data)
                self.Ffile.flush() # assume data is writing on file
            except:
                print("Unable to write data {data}\n")
    
    def closeFile(self):
        if self.Ffile is not None:
#            self.Ffile.write(f"# end \n")
            self.Ffile.close()
            self.Ffile = None
        
    def replayFile(self):
        line = None
        if self.Ffile is None:
            try:
                self.Ffile = open(self.gameDebugFile, "r")
                line = self.Ffile.readline()
                print (f"Debug replayfile: {self.gameDebugFile} open.")
            except:
                print(f"Debug replayfile: {self.gameDebugFile} not found or error.")
        else:
            try:
                line = self.Ffile.readline()
                if not line:
                    line = None
                else:                   
                    line = line.strip()
            except:
                print(f"error reading line")
        return line
    
    def open_debug(self,replay,record):
        if replay:
            if self.replayFile() is None:
                replay = False
                print (f"Pas de fichier à rejouer")
        elif record:
            self.record() #ouvre le log
        return replay
            
    def value_debug(self):
        test = self.replayFile()
        if test is not None:
            #hit = test
            who = test[:1]
            if who == '#':
                return None,None #skip commentaire
            hit = test[1:]
            return int(who),hit
        return None,None
    
    def load_debug(self, players,post_dart_check, nb_darts = 3, Sugestions_cible = None):
        match = 0
        launch = 1
        qui = ''
        avant = ''
        ligne = 0
        while qui is not None:
            qui,quoi = self.value_debug()
            value = 0
            if qui is None:
                break
            if launch > nb_darts:
                #problème on a dépasser le nb de flechettes
                avant = 33
            if qui != avant:
                players[qui].roundhits = 0
                players[qui].reset_darts()
                launch =  1
                if qui == 0:
                    match += 1
            ligne +=1
            if ligne == 50:
                print("break for debug")
            if quoi == 'D20':
                print("bloque moi ici pour tracer")
            if quoi != 'MB' and quoi != 'EPB':# and match < self.max_round: # pas Miss Button et pas Early Button
                print (f"ligne {ligne} [{quoi}]")
                valueX = post_dart_check(quoi,players,match,qui,launch)
                print (f"Post_dart_check returned : {valueX}")
                if isinstance(valueX, dict):
                    value = valueX['return_code']
                else:
                    value = valueX
            launch +=1
            avant = qui
            if quoi == 'EPB':
                #fin de tour pour le joueur
                avant = 33 #oblige a changer de joueur même si ce sera le même
            if value > 1 :#or match == self.max_round :
                qui = None
        if match < self.max_round:
            match += 1
        self.press_x()
        if Sugestions_cible is not None:
            leds = Sugestions_cible(players,0,1)
            self.rpi.set_target_leds(('|'.join(leds)))
            self.leds = [] 
            self.mickey_cible(leds, True)
        return match
    
    
    def mickey_cible(self, leds = [], affiche = False):
        #allume des segments virtuel
        #peut etre remis à zero via le jeu  avec : self.debug.leds=[]
        if len(leds) > 0:
            self.leds = leds
        if affiche and len(self.leds) > 0:
            for k in self.leds:
                cut = k.find("#")
                led = k[:cut]
                color = k[cut+1:]
                self.draw_segment(led,pygame.Color(color))
            self.display.save_background()
            self.display.update_screen()
            
    def ho_one_cible(self, leds = [], affiche = False):
        #allume des segments virtuel
        #peut etre remis à zero via le jeu  avec : self.debug.leds=[]
        if len(leds) > 0:
            self.leds = leds
        if affiche and len(self.leds) > 0:
            for k in self.leds:
                cut = k.find("#")
                led = k[:cut]
                color = k[cut+1:]
                color = color.replace(' ','').replace('(','').replace(')','')
                red = int(color.split(",")[0])
                green = int(color.split(",")[1])
                blue = int(color.split(",")[2])
                color = (red,green,blue,255)
                self.draw_segment(led,color)
            self.display.save_background()
            self.display.update_screen()
            
            
                
    def duplicated(self, leds_in = []):
        leds = leds_in
        leds_out = []
        if len(leds)>0:
            for k in leds:
                found = 0
                for l in leds_in:
                    if k == l:
                        found +=1
                if found > 1:
                    leds_out.append(f'{k}-{found}')
            return leds_out
    
    def dessine_arc(self, surface, center, radius, start_angle, stop_angle, color,pie=False):
        x,y = center
        start_angle = int((start_angle-90)%360)
        stop_angle = int((stop_angle-90)%360)
        if pie :
            if start_angle == stop_angle:
                gfxdraw.filled_circle(surface, x, y, radius, color)
            else:
                gfxdraw.pie(surface, x, y, radius, start_angle, stop_angle, color)
        else :
            if start_angle == stop_angle:
                gfxdraw.circle(surface, x, y, radius, color)
            else:
                gfxdraw.arc(surface, x, y, radius, start_angle, stop_angle, color)
    def Pos_cible(self,x=200,y=200):
        self.L = x
        self.H = y
        
    def draw_segment(self,num,color):
        L = self.L
        H = self.H
#        print(f"led = {num}, color = {color}")
        if num == 'B' or num == 'DB' or num =='SB':
            #cas special pour le bull et double bull
            for R in range(seg_pos[num][0],seg_pos[num][1]):
                for deg in range(10):
                    self.dessine_arc(self.display.screen, (L,H), R, 36*deg-9, 36*deg+9, color)
                    self.dessine_arc(self.display.screen, (L,H), R, 36*deg+9, 36*deg+27, color)
        elif (num[:1] in ('E','S', 'D', 'T')) and num[1:] not in ('T','D','B','S','E'):
            for R in range(seg_pos[num[:1]][0],seg_pos[num[:1]][1]):
                deg = code[num[1:]][1] * 36
#                print (f"num : {num} deg = {deg}  code = {code[num[1:]]}")
                if code[num[1:]][0] == 0:
                    self.dessine_arc(self.display.screen, (L,H), R, deg-8, deg+8, color)
                else:
                    self.dessine_arc(self.display.screen, (L,H), R, deg+10, deg+26, color)
                    
            if num[:1] == 'S': 
                for R in range(seg_pos[num[:1]][2],seg_pos[num[:1]][3]):
                    deg = code[num[1:]][1] * 36
                    if code[num[1:]][0] == 0:
                        self.dessine_arc(self.display.screen, (L,H), R, deg-8, deg+8, color)
                    else:
                        self.dessine_arc(self.display.screen, (L,H), R, deg+10, deg+26, color)
            
    def mickey_liste_colonne(self,head,actual_player,players,ind):
        
        chaine = "| Indice | segment | column_state |"
        for num in range(0,len(players)):
            chaine = chaine + f" colonne_value (J{players[num].ident}) |"
        z=''
        for m in range (0,len(chaine)):
            z += '='
        print(f"{z}")
        print (f"{chaine}")
        for header in head:
            chaine =""
            already_closed = 0
            test_player = 0
            for player in players:
                if test_player != actual_player:
                    chaine += f"         {player.get_col_value(ind):1}          |"
                else:
                    chaine += f"      >  {player.get_col_value(ind):1}  <       |"
                test_player += 1
            chaine = f"|   {ind:2}   |    {header:2}   |       {int(players[actual_player].get_col_value(ind))}      |" + chaine
            print (f"{chaine}")
            ind += 1
        print(f"{z}")
        print("")
            