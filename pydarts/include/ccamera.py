#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import pygame
from pygame.locals import *
import pygame.camera
import pygame.font
import datetime
import time
import subprocess
from PIL import Image
import threading
import time
from operator import itemgetter
import random
import tkinter as tk
from time import sleep

#resolution_width_ex = [ 320, 320, 640, 720, 854, 768, 800, 1024, 1280, 1280, 1280, 1400, 1680, 1600, 1920, 1920, 2048, 2048, 2560, 2560, 2560, 2560, 3440, 3840, 4096, 7680 ]
#resolution_height_ex= [ 200, 240, 480, 480, 480, 576, 600, 768 , 720 ,  800, 1024, 1050, 1050, 1200, 1080, 1200, 1080, 1536, 1080, 1440, 1600, 2048, 1440, 2160, 2160, 4320 ]
resolution_width_ex = [ 320, 640, 720, 768, 800, 1024, 1280, 1280, 1280, 1400, 1600, 1920, 2048, 2560, 3440, 3840, 7680 ]
resolution_height_ex= [ 240, 480, 480, 576, 600, 768 , 720 ,  800, 1024, 1050, 1200, 1080, 1536, 1440, 1440, 2160, 4320 ]

#
# Start of Camera Class
#
class Camera:
    def __init__(self, config, display, log, show_in_parametrage=False):
        self.camera = None
        self.update_filter = 0
        self.logs = log
        self.userDirectory = f"{config.user_dir}"
        self.photo_filter_directory = "images/photo_filter"
        self.theme = str(config.get_value('SectionGlobals', 'colorset'))
        try:
            pygame.camera.init()
        except Exception as ex:
            self.logs.Log("ERROR", f"Error in ccamera __init__ : {ex}")
        self.display = display
        self.path_of_filter = None
        self.incr_filter = 0
        self.path_of_filters_directory = None
        self.list_of_filter = []
        self.init_list_of_filters()
        self.init_var(config.read_file("Camera"), show_in_parametrage)
        self.work_in_progress = False
        self.showing_in_progress = False
        self.qrPopThread = None
        self.qrPopWindow = None
        self.runningQRPop = False
        self.credentialsPath = "/home/pi/.pydarts/credentials.json"
        self._uploadToGoogleDrive = None
        try:
            if os.path.exists(self.credentialsPath) and self.upload_cloud:
                from include import ccamera_upload_GoogleDrive
                self._uploadToGoogleDrive = ccamera_upload_GoogleDrive.CameraUploadGoogleDrive(config, self.logs, self.credentialsPath)
            else:
                self.logs.debug(f"No credentials found to upload via Google Drive")
        except Exception as ex:
            self.logs.error(f"Error in ccamera __init__() : {ex}")
        
    def init_var(self, config_camera, show_in_parametrage=False):
        self.camera_id = str(config_camera['camera_id'])
        self.picture_path = str(config_camera['picture_path'])
        self.video_path = str(config_camera['video_path'])
        self.directory_order = int(config_camera['directory_order'])
        self.choice_of_memories = int(config_camera['choice_of_memories'])
        self.pict_res_width = int(config_camera['picture_res_width'])
        self.pict_res_height = int(config_camera['picture_res_height'])
        self.vid_res_width = int(config_camera['video_res_width'])
        self.vid_res_height = int(config_camera['video_res_height'])
        self.flip_horizontal = bool(config_camera['flip_horizontal'] == '1')
        self.flip_vertical = bool(config_camera['flip_vertical'] == '1')
        self.nb_picture = int(config_camera['nb_picture'])
        self.video_duration = int(config_camera['video_duration'])
        self.fps = int(config_camera['fps'])
        self.events = str(config_camera['events'])
        self.upload_cloud = bool(config_camera['upload_cloud'] == '1')
        self.fullscreen = bool(config_camera['fullscreen_pop'] == '1')
        self.duree = int(config_camera['duree_ms'])
        if self.is_connected():
            if show_in_parametrage:
                # On bride sinon l'interface rame
                self.camera = pygame.camera.Camera(f"/dev/video{self.camera_id}", (800, 600))
            else:
                self.camera = pygame.camera.Camera(f"/dev/video{self.camera_id}", (self.pict_res_width, self.pict_res_height))
    
    def init_list_of_filters(self):
        try:
            files = []
            if self.theme in ('', 'clear', 'dark'):
                self.path_of_filters_directory = f"{self.userDirectory}/{self.photo_filter_directory}"
            else:
                self.path_of_filters_directory = f"{self.userDirectory}/themes/{self.theme}/{self.photo_filter_directory}"
            if os.path.exists(self.path_of_filters_directory):
                files = os.listdir(self.path_of_filters_directory)
                if files:
                    self.list_of_filter = []
                    for f in files:
                        self.list_of_filter.append((f, False))
            else:
                self.list_of_filter = None
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera init_list_of_filters() : {ex}")
        
    def is_connected(self):
        try:
            if(self.camera_id != '-1'):
                camera_list = pygame.camera.list_cameras()
                if camera_list :
                    return f"/dev/video{self.camera_id}" in camera_list
            return False
        except Exception as ex:
            self.logs.error(f"Error in ccamera is_connected() : {ex}")
    
    def camera_start(self):
        '''
        We start the USB camera, to be done before each use        
        '''
        try:
            if self.is_connected():
                self.camera.start()
        except Exception as ex:
            self.logs.error(f"Error in ccamera camera_start() : {ex}")
        
    def camera_stop(self): 
        '''
        We stop the USB camera, to be done after each use        
        '''
        try:
            if self.is_connected():
                self.camera.stop()
        except Exception as ex:
            self.logs.error(f"Error in ccamera camera_stop() : {ex}")
    
    def find_camera(self):
        '''
        We will browse c4l2-ctl to find the information of our USB camera
        There is "pygame.camera.list_cameras() but the responses don't tell us enough
        Return None if not find        
        '''
        try:
            cam_with_resolution = {}
            resolutions = []
            lines = []
            
            # On va recuperer les id des "USB Camera"... mais on ne retournera que le premier
            cmd = "v4l2-ctl --list-devices 2> /dev/null | grep '(usb-' -A1 | grep '/dev/video' | sed -e 's/^[ \t]*//' | sort > /home/pi/.pydarts/.all_cam.txt"
            os.system(cmd)
            
            if (os.path.exists("/home/pi/.pydarts/.all_cam.txt")):
                with open("/home/pi/.pydarts/.all_cam.txt", "r") as file:
                    line = file.readline()
                    while line:
                        lines.append(line)
                        line = file.readline()
                    
            if lines:
                for cam in lines:
                    cam_id = cam.strip()[-1:]
                    #On en a trouve un, on va maintenant recuperer ses resolutions et faire le tri dans les doublons (OSEF les FPS)
                    cmd = f"v4l2-ctl -d {cam_id} --list-formats-ext | grep 'Size: Discrete' > /home/pi/.pydarts/.cam.txt"
                    os.system(cmd)
                    lines = []
                    with open("/home/pi/.pydarts/.cam.txt", "r") as file:
                        line = file.readline()
                        while line:
                            lines.append(line)
                            line = file.readline()
                    
                    if lines:
                        resolutions = []
                        resolutions_returned = []
                        for resFind in lines:
                            resFindClean = resFind.strip().replace("Size: Discrete ", "")
                            key_exists = next(iter([i[1] for i in resolutions if int(i[0]) == int(resFindClean.split('x')[0]) \
                                                                                and int(i[1]) == int(resFindClean.split('x')[1])]), None) is not None
                            if not key_exists :
                                resolutions.append((int(resFindClean.split('x')[0]), int(resFindClean.split('x')[1])))
                        resolutions = sorted(resolutions, key=itemgetter(0,1), reverse=True)
                        for good_width, good_height in resolutions:
                            resolutions_returned.append((f"{good_width}x{good_height}",f"{good_width}x{good_height}"))
                        cam_with_resolution[cam_id] = resolutions_returned
            
            if (os.path.exists("/home/pi/.pydarts/.all_cam.txt")):
                os.remove("/home/pi/.pydarts/.all_cam.txt")
            if (os.path.exists("/home/pi/.pydarts/.cam.txt")):
                os.remove("/home/pi/.pydarts/.cam.txt")
                
            return cam_with_resolution
        
        except Exception as ex:
            self.logs.error(f"Error in ccamera find_camera() : {ex}")
    
    def resolutions_only_width(self, resolution):
        return int(resolution.split('x')[0])
    
    def resolutions_only_height(self, resolution):
        return int(resolution.split('x')[1])
    
    def resize_camera_image(self, screen, posXecran, posYecran, resWcamera, resHcamera):
        '''
        Resize the image so that it does not overflow the screen
        '''
        try:
            indexWidthRes = -1
            screen_width, screen_height = screen.get_size()
            widthEnd = posXecran + resWcamera
            heightEnd = posYecran + resHcamera
            
            # si on detecte une largeur trop grande alors on reajuste et on modifiera la hauteur
            if widthEnd > screen_width:
                possibleWidth = screen_width - posXecran - 100
                possibleWidth = (possibleWidth - min((possibleWidth - a for a in resolution_width_ex), key = abs))
                indexWidthRes = resolution_width_ex.index(possibleWidth)
            else:
                possibleWidth = resWcamera
                
            # on a deja detecte une largeur trop grande
            if indexWidthRes != -1:
                possibleHeight = resolution_height_ex[indexWidthRes]
            # si on detecte une hauteur trop grande alors on reajuste et on modifiera la largeur
            elif heightEnd > screen_height:
                possibleHeight = screen_height - posYecran - 100
                possibleHeight = (possibleHeight - min((possibleHeight - a for a in resolution_height_ex), key = abs))
                possibleWidth = resolution_height_ex[resolution_height_ex.index(possibleHeight)]
            else:
                possibleHeight = resHcamera
            
            return possibleWidth, possibleHeight
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera resize_camera_image() : {ex}")     
    
    def get_photo_filter(self):
        try:
            path_of_filter = ""
            self.list_of_filters()
            
            if self.list_of_filter:   
                # Find not show
                nb_filter_not_show = list((file[0], file[1]) for file in self.list_of_filter if file[1] == False)
                nb_files = len(nb_filter_not_show)
                rand_file = random.randint(0, nb_files - 1)
                             
                # Test if path or directory always exist (change value dynamically)
                path_of_filter =f"{self.path_of_filters_directory}/{nb_filter_not_show[rand_file][0]}"
                
                # No surprise ?
                if not self.filter_always_exist(path_of_filter):
                    self.list_of_filter.remove(nb_filter_not_show[rand_file])
                    self.get_photo_filter()
                    
                # next(ind for ind, tup in enumerate(self.list_of_filter) if nb_filter_not_show[rand_file][0] in tup)
                self.list_of_filter = self.update_list_of_filter_value(self.list_of_filter, str(nb_filter_not_show[rand_file][0]), True)
                
                # Reinit if all show
                if sum(1 for file in self.list_of_filter if file[1] == False) == 0:
                    newList = []
                    for f, aff in self.list_of_filter:
                        newList.append((f, False))
                    self.list_of_filter = newList
                     
            return path_of_filter if self.list_of_filter else None
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera get_photo_filter() : {ex}")
    
    def list_of_filters(self):
        try:
            filter_finded = []
            if os.path.exists(self.path_of_filters_directory):
                filter_finded = os.listdir(self.path_of_filters_directory)
            #
            if (filter_finded and len(filter_finded) > 0) and not self.list_of_filter:
                self.init_list_of_filters()
            elif (filter_finded and len(filter_finded) > 0) and len(filter_finded) != len(self.list_of_filter):
                self.populate_list_of_filter(filter_finded, self.list_of_filter)
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera list_of_filters() : {ex}")
    
    def filter_always_exist(self, filter_path):
        try:
            return (filter_path != None and os.path.isfile(filter_path))
                
        except Exception as ex:
            self.logs.error(f"Error in ccamera filter_always_exist() : {ex}")
            
    def populate_list_of_filter(self, new_list_of_filter, list_of_filter):
        try:
            for filt in new_list_of_filter:
                list_of_filter.append((filt, False)) if (filt, True) not in list_of_filter and (filt, False) not in list_of_filter else None
                    
        
        except Exception as ex:
            self.logs.error(f"Error in ccamera populate_list_of_filter() : {ex}")
            
    def update_list_of_filter_value(self, list_of_filter, key, value):
        try:
            return [(ke,va) if (ke != key) else (ke, value) for (ke, va) in list_of_filter]
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera update_list_of_filter_value() : {ex}")
            
    def show_camera(self, screen, posX=0, posY=0, resW=0, resH=0):
        '''
        Display camera
        '''
        try:
            screen_width, screen_height = screen.get_size()
            if resW == 0:
                resW = self.pict_res_width
            if resH == 0:
                resH = self.pict_res_height
            # centrage automatique si posX = 0 ou posY = 0
            if posX == 0:
                posX = ((screen_width - resW) / 2)
            if posY == 0:
                posY = ((screen_height - resH) / 2)
                
            # on va eviter tout debordement du preview
            resW, resH = self.resize_camera_image(screen, posX, posY, resW, resH)
            
            camera_picture = Rect(posX, posY, resW, resH)
                  
            if self.is_connected():
                # 
                if self.camera is None:
                    # On reinitialise
                    self.camera = pygame.camera.Camera(f"/dev/video{self.camera_id}")
                    self.camera_start()
                # get a preview picture
                image = self.camera.get_image()
                # upscale image
                image = pygame.transform.scale(image, (resW, resH))
                # flip 
                image = pygame.transform.flip(image, self.flip_horizontal, self.flip_vertical)
                
                if self.incr_filter == 0:
                    self.path_of_filter = self.get_photo_filter()
                    
                self.incr_filter += 1
                if self.incr_filter == 30:
                    self.incr_filter = 0                    
                
                # certains aiment supprimer les filtres en cours
                if not self.filter_always_exist(self.path_of_filter):
                    self.path_of_filter = self.get_photo_filter()
                
                #path_of_filter = self.get_photo_filter()
                #if path_of_filter is not None:
                if self.path_of_filter is not None:
                    # On charge le calque
                    #calque = pygame.image.load(path_of_filter).convert_alpha()
                    calque = pygame.image.load(self.path_of_filter).convert_alpha()
                    # On resize le calque
                    calque = pygame.transform.scale(calque, (resW, resH))
                    # On applique le calque
                    image.blit(calque,(0, 0))
                    
                # display the preview
                screen.blit(image,(posX, posY))
                
            else:
                pygame.draw.rect(screen, pygame.Color(100, 100, 100), camera_picture)
                pygame.draw.line(screen, (255, 255, 255), (posX, posY), (posX + resW, posY + resH), 10)
                pygame.draw.line(screen, (255, 255, 255), (posX , posY + resH), (posX + resW, posY), 10)
                
            # refresh
            pygame.display.update(camera_picture)                    
                
        except Exception as ex:
            self.logs.error(f"Error in ccamera show_camera() : {ex}")             
     
    def folder_tree(self, directory_name, game):
        try:
            if self.directory_order == 0:
                # /home/pi/Pictures_Videos/Date/Jeux/Photos_Videos
                return f"{directory_name}/{game}"
            elif self.directory_order == 1:                
                # /home/pi/Pictures_Videos/Jeux/Date/Photos_Videos
                return f"{game}/{directory_name}"
                
        except Exception as ex:
            self.logs.error(f"Error in ccamera folder_tree() : {ex}")
                
    def action(self, directory_name_of_game, file_name):
        try:
            if not self.work_in_progress:
                self.work_in_progress = True
                if self.choice_of_memories != 0:     
                    choice = self.choice_of_memories
                    # On prepare les dossiers et les nom de fichiers
                    filename = f"{file_name}"
                    directory_game_name = f"{directory_name_of_game}"
                    
                    if (choice == 3):
                        choice = random.randint(1,2)
                    
                    if (choice == 1):
                        # Photos
                        # Cheeeeeeze
                        self.take_shot(game=directory_game_name,picture_name=filename)
                    elif (choice == 2):
                        # Videos
                        # Lights... Camera... ...aaaaannnnnddd Action !
                        self.take_video(game=directory_game_name,video_name=filename)          
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera action() : {ex}")
    
    def take_shot(self, start_stop=True, game="Test", picture_name=None):
        '''
        Here we take a shot in thread mode
        '''
        try:
            threading.Thread(target=self.take_a_shot, args=(start_stop,game,picture_name,), daemon=True).start()
        except Exception as ex:
            self.logs.error(f"Error in ccamera take_shot() : {ex}") 
        
    def take_a_shot(self, start_stop=True, game="Test", picture_name=None):
        '''
        Here we take a shot of the current event
        '''
        try:
            if self.is_connected():
                # Create folder in Google Drive if it not exists
                if self._uploadToGoogleDrive is not None:
                    if self._uploadToGoogleDrive.get_folder_id() is None:
                        self._uploadToGoogleDrive.create_new_folder_in_google_drive(game)  
                # start engine...
                if start_stop:
                    self.camera_start()
                nbCapture = 0
                while (nbCapture < self.nb_picture):                    
                    # get a preview picture
                    picture_shot = self.camera.get_image().convert_alpha()
                    picture_shot = pygame.transform.scale(picture_shot, (1024, 765))
                    nbCapture += 1
                    # flip 
                    picture_shot = pygame.transform.flip(picture_shot, self.flip_horizontal, self.flip_vertical)  
                    # name and other 
                    now = datetime.datetime.now()
                    if None is picture_name:
                        pictureName =  now.strftime("%H:%M:%S.%f")
                    else:
                        pictureName =  picture_name                        
                    directory_name = now.strftime("%d_%m_%Y")
                    directory_default_name = f"{self.picture_path}/{self.folder_tree(directory_name,game)}"
                    if not os.path.exists(directory_default_name):
                        os.makedirs(directory_default_name)
                        
                    path_of_filter = self.get_photo_filter()
                    if path_of_filter is not None:
                        # On charge le calque
                        calque = pygame.image.load(path_of_filter).convert_alpha()
                        # On applique le calque
                        picture_shot.blit(calque,(0, 0))
                    
                    # save             
                    pygame.image.save(picture_shot,f"{directory_default_name}/{pictureName}.png")
                    
                    # Load picture in Google Drive
                    if self._uploadToGoogleDrive is not None:
                        if self._uploadToGoogleDrive.get_folder_id() is not None:
                            self._uploadToGoogleDrive.upload_one_picture_video_to_google_drive(f"{directory_default_name}/{pictureName}.png")  
                    
                    # Look at me !
                    self.show_image_popup(f"{directory_default_name}/{pictureName}.png", fullscreen=self.fullscreen, duree=self.duree)
                    
                # ...stop engine
                if start_stop:
                    self.camera_stop()
                
                self.work_in_progress = False
                    
        except Exception as ex:
            self.logs.error(f"Error in ccamera take_a_shot() : {ex}") 
           
    def take_video(self, game="Test", video_name=None):
        '''
        Here we take a video in thread mode
        '''
        try:
            threading.Thread(target=self.take_a_video, args=(None,False,game,video_name,), daemon=True).start()
        except Exception as ex:
            self.logs.error(f"Error in ccamera take_video() : {ex}") 
            
    def take_a_video(self, screen_with_all_information=None, stop_start=True, game="Test", video_name=None):
        '''
        Here we take a video of the current event
        '''
        # screen_with_all_information : (screen, defaultfontpath, posX_camera, posY_camera, resW, resH)
        try:
            if self.is_connected():
                # Create folder in Google Drive if it not exists
                if self._uploadToGoogleDrive is not None:
                    if self._uploadToGoogleDrive.get_folder_id() is None:
                        self._uploadToGoogleDrive.create_new_folder_in_google_drive(game)  
                # stop engine...
                if stop_start:
                    self.camera_stop()
                # warn user (for exemple : parameters screen)
                if (None is not screen_with_all_information):
                    # on va eviter tout debordement du preview
                    resW, resH = self.resize_camera_image(screen_with_all_information[0], screen_with_all_information[2], screen_with_all_information[3],\
                                                          self.vid_res_width, self.vid_res_height)
                    camera_picture = Rect(screen_with_all_information[2], screen_with_all_information[3], resW, resH)                    
                    pygame.draw.rect(screen_with_all_information[0], pygame.Color(100, 100, 100), camera_picture)
                    font = pygame.font.Font(screen_with_all_information[1], 30)
                    text = font.render("Recording in progress..", True, (255, 255, 255))       
                    screen_with_all_information[0].blit(text,(screen_with_all_information[2] + 100, screen_with_all_information[3] + 100))
                    # refresh
                    pygame.display.update(camera_picture)
                # name and other 
                now = datetime.datetime.now()
                if None is video_name:
                    video_name = now.strftime("%H:%M:%S.%f")
                directory_name = now.strftime("%d_%m_%Y")
                directory_default_name = f"{self.video_path}/{self.folder_tree(directory_name,game)}"
                if not os.path.exists(directory_default_name):
                    os.makedirs(directory_default_name)
                vf = ""
                if bool(self.flip_horizontal == 1) and bool(self.flip_vertical == 1):
                    vf = "-vf 'hflip,vflip'"
                elif bool(self.flip_horizontal == 1) and bool(self.flip_vertical == 0):
                    vf = "-vf 'hflip'"
                elif bool(self.flip_horizontal == 0) and bool(self.flip_vertical == 1):
                    vf = "-vf 'vflip'"
                
                filter_on_video = ""
                path_of_filter = self.get_photo_filter()
                if path_of_filter is not None:
                    vf = vf.replace("-vf ","").replace("'","")
                    if vf == "":
                        # With sound
                        vf = "[1]"
                        ## Without sound
                        #vf = "[0]"
                    else:
                        # With sound
                        vf = f"[1:v]{vf}[video];[video]"
                        ## Without sound
                        #vf = f"[0:v]{vf}[video];[video]"
                        
                    # With sound
                    filter_on_video = f"-i {path_of_filter} -filter_complex '[2]scale={self.vid_res_width}:{self.vid_res_height}[png];{vf}[png]overlay'"
                    ## Without sound
                    #filter_on_video = f"-i {path_of_filter} -filter_complex '[1]scale={self.vid_res_width}:{self.vid_res_height}[png];[0:v]{vf}[video];[video][png]overlay'"
                    vf = ""
                
                # With sound
                cmd = f"ffmpeg -v 'quiet' "\
                       "-f alsa -ac 1 "\
                       f"-i default -f v4l2 -video_size {self.vid_res_width}x{self.vid_res_height} -vsync vfr -i /dev/video{self.camera_id} "\
                       f"{filter_on_video} -t 00:00:{self.video_duration:02d} '{directory_default_name}/{video_name}.mp4'"
                
                ##  Without sound
                #cmd = f"ffmpeg -v 'quiet' -f v4l2 -video_size {self.vid_res_width}x{self.vid_res_height} -vsync vfr "\
                #       f"-i /dev/video{self.camera_id} {filter_on_video} -t 00:00:{self.video_duration:02d} '{directory_default_name}/{video_name}.mp4'"
                            
                # run
                os.system(cmd)
                    
                # Load video in Google Drive
                if self._uploadToGoogleDrive is not None:
                    if self._uploadToGoogleDrive.get_folder_id() is not None:
                        self._uploadToGoogleDrive.upload_one_picture_video_to_google_drive(f"{directory_default_name}/{video_name}.mp4")  
                                
                # Tadaaaa
                self.show_action_video(f"{directory_default_name}/{video_name}.mp4")
                
                # ...start engine
                if stop_start:
                    self.camera_start()
                    
                self.work_in_progress = False
                    
        except Exception as ex:
            self.logs.error(f"Error in ccamera take_a_video() : {ex}")
            
    def show_action_video(self, video_path):
        try:
            # on cherche la resolution de l'ecran
            screen_size = os.popen("xrandr | head -n1 | cut -d, -f2 | cut -d' ' -f3-5")
            screen_size_width, screen_size_height = screen_size.read().split('x')
            
            right_corner_x = int(screen_size_width.strip()) - self.vid_res_width
            right_corner_y = int(screen_size_height.strip()) - self.vid_res_height
            
            subprocess.Popen(['omxplayer', '--win', f'{right_corner_x},-{right_corner_y},{int(screen_size_width.strip())},{int(screen_size_height.strip())}',
                              '--aspect-mode','letterbox','-o', 'alsa', f'{video_path}'],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        
        except Exception as ex:
            self.logs.error(f"Error in ccamera show_action_photo() : {ex}")

    def show_qr_code(self):   
            try:
                if self._uploadToGoogleDrive is not None:
                    if self._uploadToGoogleDrive.get_folder_id() is not None:
                        qrPop = self._uploadToGoogleDrive.get_qrcode_to_new_google_drive_folder()
                        if qrPop is not None:
                            while(self.showing_in_progress):
                                sleep(0.1)
                            self.show_qr_popup(qrPop)
                        
            except Exception as ex:
                self.logs.error(f"Error in ccamera show_qr_code() : {ex}") 

    def show_qr_code_for_pictures_videos(self):
            try:
                threading.Thread(target=self.show_qr_code).start()
                        
            except Exception as ex:
                self.logs.error(f"Error in ccamera get_qr_code_for_pictures_videos() : {ex}")
       
    def show_image_popup(self, image_path, fullscreen=False, duree=5000):
        try:
            def popup(): 
                temp_path = "/home/pi/Pictures/_resized_popup_temp.png"               
                while(self.showing_in_progress):
                    sleep(0.1)
                self.showing_in_progress = True
                pop = tk.Tk()
                pop.overrideredirect(True)
                
                if fullscreen:
                    pop.attributes("-fullscreen", True)
                                
                screen_width = pop.winfo_screenwidth()
                screen_height = pop.winfo_screenheight()
                
                photo = tk.PhotoImage(file=image_path)
                                
                if fullscreen:
                    img = Image.open(image_path)
                    #
                    scale = min(screen_width / img.width, screen_height / img.height)
                    new_w = int(img.width * scale)
                    new_h = int(img.height * scale)
                    resized_img = img.resize((new_w, new_h), Image.ANTIALIAS)
                    #
                    fond = Image.new("RGB", (screen_width, screen_height), (0, 0, 0))
                    x = (screen_width - new_w) // 2
                    y = (screen_height - new_h) // 2
                    fond.paste(resized_img, (x, y))
                    #
                    fond.save(temp_path)
                    photo = tk.PhotoImage(file=temp_path)
                    max_width = int(screen_width)
                    max_height = int(screen_height)
                else:                
                    max_width = screen_width // 3
                    max_height = screen_height // 3
                    photo = tk.PhotoImage(file=image_path)
                
                image_width = photo.width()
                image_height = photo.height()

                facteur = max(
                    image_width // max_width if image_width > max_width else 1,
                    image_height // max_height if image_height > max_height else 1,
                )
                
                if facteur > 1:
                    facteur = int(facteur + 0.5)
                    photo = photo.subsample(facteur, facteur)
                    
                image_width = photo.width()
                image_height = photo.height()

                label = tk.Label(pop, image=photo)
                label.pack()

                if fullscreen:
                    pos_x = (screen_width - image_width) // 2
                    pos_y = (screen_height - image_height) // 2
                else:
                    pos_x = screen_width - image_width
                    pos_y = 0                
                pop.geometry(f"{image_width}x{image_height}+{pos_x}+{pos_y}")
                pop.after(duree, pop.destroy)
                label.image = photo
                pop.mainloop()                
                if fullscreen:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                self.showing_in_progress = False

            threading.Thread(target=popup).start()
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera show_image_popup() : {ex}")
        
    def close_qr_popup(self):
        try:
            if self._uploadToGoogleDrive is not None:
                self.runningQRPop = False
                if self.qrPopWindow:
                    try:
                        self.qrPopWindow = None
                        self._uploadToGoogleDrive.reinit_folder_id()
                        self.showing_in_progress = False
                    except Exception as e:
                        self.logs.error(f"Error in ccamera close_qr_popup() : {e}")
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera close_qr_popup() : {ex}")
        
    def show_qr_popup(self, qr_img):
        try:
            def run():
                self.runningQRPop = True

                pop = tk.Tk()
                self.qrPopWindow = pop
                pop.overrideredirect(True)
                pop.attributes("-topmost", True)
                frame = tk.Frame(pop)
                frame.pack(expand=True, fill='both', padx=10, pady=10)

                label_text = tk.Label(
                    frame,
                    text="Vos souvenirs sont disponibles ici",
                    font=("Arial", 14)
                )
                label_text.pack(pady=(5, 2))
                label_arrow = tk.Label(frame, text="↓", font=("Arial", 24))
                label_arrow.pack(pady=(0, 5))
                
                tmp_path = "/home/pi/Pictures/temp_qr.png"
                qr_display_size = 200
                resized_qr = qr_img.resize((qr_display_size, qr_display_size), resample=Image.BICUBIC)
                resized_qr.save(tmp_path)
                qr_photo = tk.PhotoImage(file=tmp_path)
                qr_label = tk.Label(frame, image=qr_photo)
                qr_label.image = qr_photo
                qr_label.pack()

                pop.update_idletasks()
                w = pop.winfo_reqwidth()
                h = pop.winfo_reqheight()
                sw = pop.winfo_screenwidth()
                sh = pop.winfo_screenheight()
                x = sw - w  # Coin supérieur droit
                y = int(sh * 0.05)
                pop.geometry(f"{w}x{h}+{x}+{y}")
                
                gradient_colors = ["#ffffff", "#f0f8ff", "#e6f2ff", "#d9ecff", "#cce6ff", "#d9ecff", "#e6f2ff", "#f0f8ff"]
                color_index = 0

                def cycle_colors():
                    nonlocal color_index
                    if not self.runningQRPop or self.qrPopThread is None:
                        pop.after(0, pop.destroy)
                        return
                    new_color = gradient_colors[color_index]
                    pop.configure(bg=new_color)
                    for widget in pop.winfo_children():
                        widget.configure(bg=new_color)
                        for subwidget in widget.winfo_children():
                            subwidget.configure(bg=new_color)
                    color_index = (color_index + 1) % len(gradient_colors)
                    pop.after(300, cycle_colors)

                pop.after(100, cycle_colors)
                pop.mainloop()

            self.qrPopThread = threading.Thread(target=run, daemon=True)
            self.qrPopThread.start()

        except Exception as ex:
            self.logs.error(f"Error in ccamera show_qr_popup(): {ex}")
