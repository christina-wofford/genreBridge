from flask import Flask, render_template, request
from db_handler import db, Book
from api_call import get_book_data, get_playlist_data

app = Flask(__name__)