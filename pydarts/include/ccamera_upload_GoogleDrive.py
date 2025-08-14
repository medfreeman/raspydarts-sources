#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
import pathlib
import argparse
import qrcode
import threading
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth.exceptions import RefreshError, GoogleAuthError

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']

#
# Start of Camera Upload Google Drive Class
#
class CameraUploadGoogleDrive:          
    def __init__(self, config, log, credentials):
        self.logs = log
        self.googleDriveDirectoryMainName = str(config.read_file('Camera')['path_google_drive'])
        self.token_path = os.path.join(os.path.dirname(credentials), "token.json")
        self.credential_path = credentials
        self.folder_id = None
        self.service = None
        self.parent_folder_id = None
        if os.path.exists(self.credential_path):
            self.logs.debug(f"Credentials found to upload via Google Drive!!")
            self.service = self.authenticate_google_drive()
            self.parent_folder_id = self.get_google_drive_parent_folder_id()
            if self.parent_folder_id is None and self.googleDriveDirectoryMainName != '':
                self.parent_folder_id = self.create_new_folder_in_google_drive_root_get_id(self.googleDriveDirectoryMainName)

    def authenticate_google_drive(self):
        credentials = None

        if os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'r') as token_file:
                    token_data = json.load(token_file)
                    credentials = Credentials.from_authorized_user_info(token_data, SCOPES)
            except Exception as e:
                self.logs.error(f"- [authenticate_google_drive] Erreur lors du chargement de '{self.token_path}' : {e}")
                try:
                    os.remove(self.token_path)
                    self.logs.warning(f"- [authenticate_google_drive] Fichier '{self.token_path}' supprimé suite à une erreur.")
                except Exception as remove_error:
                    self.logs.error(f"- [authenticate_google_drive] Impossible de supprimer '{self.token_path}' : {remove_error}")
                credentials = None

        try:
            if not credentials or not credentials.valid:
                if credentials and credentials.expired and credentials.refresh_token:
                    try:
                        credentials.refresh(Request())
                        self.logs.warning("- [authenticate_google_drive] Token rafraîchi avec succès.")
                    except (RefreshError, GoogleAuthError) as refresh_error:
                        self.logs.error(f"- [authenticate_google_drive] Échec du rafraîchissement du token : {refresh_error}")
                        credentials = None
                if not credentials or not credentials.valid:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credential_path),
                        SCOPES
                    )
                    credentials = flow.run_local_server(port=0)

                with open(self.token_path, 'w') as token_file:
                    token_file.write(credentials.to_json())
                    self.logs.warning(f"- [authenticate_google_drive] Nouveau token enregistré dans '{self.token_path}'.")

            return build('drive', 'v3', credentials=credentials)

        except Exception as ex:
            self.logs.error(f"Error in ccamera_upload authenticate_google_drive() : {ex}")
            return None

    def get_google_drive_parent_folder_id(self):
        try:
            if self.service is not None:
                query = f"name='{self.googleDriveDirectoryMainName}' and mimeType='application/vnd.google-apps.folder'"
                results = self.service.files().list(q=query, spaces='drive').execute()
                folders = results.get('files', [])
                if not folders:
                    self.logs.debug(f"Le dossier '{self.googleDriveDirectoryMainName}' est introuvable dans Google Drive, on le crée!!")
                    return self.create_new_folder_in_google_drive_root_get_id(self.googleDriveDirectoryMainName)
                return folders[0]['id']
            return None
        
        except Exception as ex:
            self.logs.error(f"Error in ccamera_upload get_google_drive_parent_folder_id() : {ex}")
            return None
        
    def create_new_folder_in_google_drive_root_get_id(self, name):
        try:
            if self.service is not None:
                metadata = {
                    'name': name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': ''
                }
                folder = self.service.files().create(body=metadata, fields='id').execute()
                return folder.get('id')
            return None
        
        except Exception as ex:
            self.logs.error(f"Error in ccamera_upload create_new_folder_in_google_drive_root_get_id() : {ex}")
            return None
        
    def reinit_folder_id(self):
        try:
            self.folder_id = None
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera_upload reinit_folder_id() : {ex}")
        
    def get_folder_id(self):
        try:
            # return None si pas de folder_id
            return self.folder_id
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera_upload get_folder_id() : {ex}")

    def create_new_folder_in_google_drive(self, folder_name):
        try:                
            if self.search_folder_id(folder_name) is None:
                self.folder_id = self.create_new_folder_in_google_drive_get_id(folder_name)
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera_upload create_new_folder_in_google_drive() : {ex}")
            
    def search_folder_id(self, folder_name):
        try:
            if self.service is not None:
                query = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and '{self.parent_folder_id}' in parents"
                results = self.service.files().list(q=query, spaces='drive', fields="files(id, name)").execute()
                folders = results.get('files', [])
                if folders:
                    return folders[0]['id']
            return None
        
        except Exception as ex:
            self.logs.error(f"Error in ccamera_upload search_folder_id() : {ex}")
        
    def create_new_folder_in_google_drive_get_id(self, name):
        try:
            if self.service is not None:
                metadata = {
                    'name': name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [self.parent_folder_id]
                }
                folder = self.service.files().create(body=metadata, fields='id').execute()
                return folder.get('id')
            return None
        
        except Exception as ex:
            self.logs.error(f"Error in ccamera_upload create_new_folder_in_google_drive_get_id() : {ex}")
            return None
        
    def get_qrcode_to_new_google_drive_folder(self):
        try:    
            if self.folder_id is not None:
                linkToGoogleDriveFolder = self.get_link_to_new_folder_google_drive()
                if linkToGoogleDriveFolder is not None:
                    return qrcode.make(linkToGoogleDriveFolder)
            return None
        
        except Exception as ex:
            self.logs.error(f"Error in ccamera_upload get_qrcode_to_new_google_drive_folder() : {ex}")  
            return None

    def get_link_to_new_folder_google_drive(self):
        try:   
            if self.service is not None:
                if self.folder_id is not None:             
                    permission = {
                        'type': 'anyone',
                        'role': 'reader'
                    }
                    self.service.permissions().create(fileId=self.folder_id, body=permission).execute()
                    return self.service.files().get(fileId=self.folder_id, fields='webViewLink').execute()['webViewLink']
            return None
        
        except Exception as ex:
            self.logs.error(f"Error in ccamera_upload get_link_to_new_folder_google_drive() : {ex}")
            return None

    def upload_one_picture_video_to_GD(self, image_video_path):
        try:
            if self.service is not None:
                if self.folder_id is not None:
                    file_name = os.path.basename(image_video_path)
                    metadata = {
                        'name': file_name,
                        'parents': [self.folder_id]
                    }
                    media = MediaFileUpload(image_video_path, resumable=True)
                    self.service.files().create(body=metadata, media_body=media, fields='id').execute()
                    self.logs.debug(f"File {file_name} loaded!!")
        
        except Exception as ex:
            self.logs.error(f"Error in ccamera_upload upload_one_picture_video_to_GD() : {ex}")

    def upload_all_pictures_videos_to_GD(self, image_folder_path):
        try:
            if self.service is not None:
                if self.folder_id is not None:
                    for file_name in os.listdir(image_folder_path):
                        if file_name.lower().endswith(('.jpg', '.jpeg', '.png', '.mp4')):
                            file_path = os.path.join(image_dir, file_name)
                            metadata = {
                                'name': file_name,
                                'parents': [self.folder_id]
                            }
                            media = MediaFileUpload(file_path, resumable=True)
                            self.service.files().create(body=metadata, media_body=media, fields='id').execute()
                            self.logs.debug(f"File {file_name} loaded!!")
        
        except Exception as ex:
            self.logs.error(f"Error in ccamera_upload upload_all_pictures_videos_to_google_drive() : {ex}")          
        
    def create_folder_upload_return_QrImage(self, googleDriveNameDirectory, picturesVideosPathDirectory):
        try:
            new_folder_id = self.create_new_folder_in_google_drive_get_id(googleDriveNameDirectory)

            self.upload_all_pictures_videos_to_google_drive(new_folder_id, picturesVideosPathDirectory)

            return self.get_qrcode_to_new_google_drive_folder(new_folder_id)
        
        except Exception as ex:
            self.logs.error(f"Error in ccamera_upload create_folder_upload_return_QrImage() : {ex}")
            
    def upload_one_picture_video_to_google_drive(self, fileName):
        try:
            threading.Thread(target=self.upload_one_picture_video_to_GD, args=(fileName,), daemon=True).start()
        
        except Exception as ex:
            self.logs.error(f"Error in ccamera_upload upload_one_picture_video_to_google_drive() : {ex}")
    
    def upload_all_pictures_videos_to_google_drive(self, folderPath):
        try:
            threading.Thread(target=self.upload_all_pictures_videos_to_GD, args=(folderPath,), daemon=True).start()
            
        except Exception as ex:
            self.logs.error(f"Error in ccamera_upload upload_all_pictures_videos_to_google_drive() : {ex}") 
    
