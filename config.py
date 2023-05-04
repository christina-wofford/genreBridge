import psycopg2
from googleapiclient.discovery import build
import nltk
from nltk.corpus import stopwords
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import ssl
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

spotify_client_id = '1cd807f73d0442a8946b04796cd45c57'
spotify_client_secret = 'd59d8ca6c4574fa1adf241ff40f770b5'
spotify_credentials = SpotifyClientCredentials(client_id=spotify_client_id, client_secret=spotify_client_secret)
spotify_api = spotipy.Spotify(client_credentials_manager=spotify_credentials)

ssl._create_default_https_context = ssl._create_unverified_context
api_key = 'AIzaSyAS1ll-qIIwXodwRJZPln_k5mTzMMX7UrA'
google_books_api = build('books', 'v1', developerKey=api_key)

connection = psycopg2.connect("dbname=genrebridge user=christina password=dispute host=localhost")
cursor = connection.cursor()