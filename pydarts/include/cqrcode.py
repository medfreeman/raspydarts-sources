#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
qrcode generator by Manu
"""

import pygame
try:
    faulty = False
    import qrcode
except:
    faulty = True
    from include import clogs
    from subprocess import Popen
    qr_log = open('logs/Qr.log', "w", 1)
    try:
        cmd = ['sudo', 'pip3', '--no-input', 'install','qrcode']
        print("Install qrcode library with pip3 ...")
        process = Popen(cmd, stdout=qr_log)
        process.wait()
        faulty = False
    except Exception as error:
        print("Error pip3 , try pip")
        print("Install qrcode library with pip ...")
        try:
            #maybe pip
            cmd = ['sudo', 'pip', 'install','qrcode']
            process = Popen(cmd, stdout=qr_log)
            process.wait()
            faulty = False
        except Exception as error:
            print("Error pip")
    if not faulty: #vient d'etre installé on ouvre la librairie sinon on reboot
        try:
            import qrcode
        except Exception as error:
            print("Error try to reboot or see logs\Qr.log")
            #cmd = ['sudo', 'reboot']
            #print("Rebooting...")
            #subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
from PIL import Image

URL_BASE = "https://raspydarts.wordpress.com/"
LISTE_GAMES = {\
    "321_ZLIP" : "2023/07/26/321-zlip/", \
    "BIG6" : "2023/10/05/big-6/", \
    "BOB27" : "2023/07/26/bob-27/", \
    "BY_FIVES" : "2023/07/26/by-fives/", \
    "COLOR" : "2023/10/05/color/", \
    "CRICKET" : "2023/07/26/cricket/", \
    "HIGH_SCORE" : "2023/07/26/high-score/", \
    "HO_ONE" : "2023/07/26/ho-one/", \
    "KAPITAL" : "2023/07/26/kapital/", \
    "KILLER" : "2023/07/26/killer/", \
    "KINITO" : "2023/07/26/kinito/", \
    "BATARD" : "2023/07/26/le-batard/", \
    "LOW_SCORE" : "2023/07/26/low-score/", \
    "PRACTICE" : "2023/07/26/practice/", \
    "ROUND_THE_CLOCK" : "2023/07/26/round-the-clock/", \
    "SCRAM_CRICKET" : "2023/07/26/scram-cricket/", \
    "SHANGHAI" : "2023/07/26/shanghai/", \
    "BERMUDA_TRIANGLE" : "2023/07/26/triangle-des-bermudes/", \
    "UP_AND_DOWN_COUNT_UP" : "2023/07/26/up-and-down-count-up/", \
    "BINGO" : "2023/11/24/bingo/", \
    "CASTLE" : "2023/07/26/castle/", \
    "CHALLENGE" : "2023/11/24/challenge/", \
    "CONQUER" : "2023/07/26/conquer/", \
    "FIGHTERS" : "2023/07/26/fighters/", \
    "GAMEOFGOOSE" : "2023/11/24/jeu-de-loie/", \
    "PURSUIT" : "2023/07/26/pursuit/", \
    "RISK" : "2023/08/22/risk/", \
    "ROBIN_DRINK" : "2023/07/26/robin-des-boissons/", \
    "ROBIN_STRIP" : "2023/07/26/robin-stripteaseur/", \
    "SIMON" : "2023/07/26/simon/", \
    "SLIDER" : "2023/07/26/slider/", \
    "TOWER" : "2023/07/26/tower/", \
    "VOLEUR" : "2023/10/05/voleur/", \
    "BALLTRAP" : "2023/07/26/balltrap/", \
    "BASEBALL" : "2023/07/26/baseball/", \
    "BOWLING" : "2023/07/26/bowling/", \
    "FOOTBALL" : "2023/07/26/football/", \
    "GOLF" : "2023/07/26/golf/", \
    "PUNCH-OUT" : "2023/07/26/punch-out/", \
    "SNOOKER" : "2023/07/26/snooker/", \
    "TENNIS" : "2023/07/26/tennis/", \
    "HORSE" : "2024/03/06/horse/", \
    "TREASURE" : "2024/03/06/treasure-hunt/", \
    "MORPION" : "2023/07/26/tic-tac-toe/", \
    "OTHELLO" : "2024/03/06/Othello/", \
    "PUISSANCE4" : "2024/03/06/puissance-4/", \
    "TARGET" : "2024/03/06/target/", \
    "SABOTAGE" : "2024/03/06/sabotage/", \
    "PINGPONG" : "2024/03/05/ping-pong/" \
    }
# Jeux absents : Treasure, 
    
class Qrcoder:
    def __init__(self,url = None, color = 'black', bgcolor = 'white' ):
        self.logo = None
        self.url = url
        self.color = color
        self.bgcolor = bgcolor
        self.qrsize = 150
        self.transparent = False
        self.tcolor = (5,5,5)
        

        
    def set_transparent(self, choix = False):
        self.transparent = choix
        
    def set_qrsize(self,taille = 150):
        self.qrsize = taille
        
    def set_color(self,color = 'black', bgcolor = 'white'):
        self.color = color
        self.bgcolor = bgcolor
        
    def scale_logo(self,taille = 60):
        width_pcent = taille/ float(self.logo.size[0])
        heigth = int( float(self.logo.size[1]) * float(width_pcent) )
        self.logo = self.logo.resize((taille, heigth), Image.ANTIALIAS)
            
    def set_url(self,game = None):
        if game is None :
            return None
        returned = None    
        for k in LISTE_GAMES:    
            if  game.upper() == k:
                returned =  URL_BASE + LISTE_GAMES[k]
                break
        if returned is None:
            print(f"game = {game.upper()} not found in the class cqrcode")
        return returned

    def generate(self,game = None, logo = None, size = 3, bordure = 4):
#        print(f"{game} - {logo}")
        #initialise qrcode avec ERROR_CORRECT_H car le logo va cacher une partie du code
        self.QRcode = qrcode.QRCode(box_size = int(size),border = int(bordure), error_correction=qrcode.constants.ERROR_CORRECT_H)
        if logo is not None:
            try:
                self.logo = Image.open(logo)
            except:
                self.logo = None
                
            
        self.url = self.set_url(game)
        if self.url is not None:
            self.QRcode.add_data(self.url)
        self.QRcode.make(fit = True)
        if self.transparent:    
            qrImage = self.QRcode.make_image(fill_color=self.color, back_color=self.tcolor).convert('RGB')
        else:
            qrImage = self.QRcode.make_image(fill_color=self.color, back_color=self.bgcolor).convert('RGB')
            
#        print(f"qrImage : {qrImage}")
        if qrImage.size[0] != self.qrsize :
            qrImage = qrImage.resize((self.qrsize,self.qrsize))
#            print(f"resized qrImage : {qrImage}")
        
        if self.logo is not None: #resize et centre le logo dans le qrcode
            self.scale_logo(int(self.qrsize / 2.6))
            pos = ((qrImage.size[0] - self.logo.size[0]) // 2, (qrImage.size[1] - self.logo.size[1]) // 2)
            qrImage.paste(self.logo, pos)
        Surface = pygame.image.fromstring(qrImage.tobytes(), qrImage.size, qrImage.mode).convert()
        if self.transparent:
            Surface.set_colorkey(self.tcolor)
        else:
            Surface.set_colorkey(None)            
        del qrImage #libere la memoire de l'image
        self.transparent = False #ne pas memoriser le choix
        return Surface
        