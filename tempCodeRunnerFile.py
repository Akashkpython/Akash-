from flask import Flask, request, render_template, redirect, url_for, session, flash, jsonify
from pymongo import MongoClient, ASCENDING
from bson.objectid import ObjectId
from werkzeug.utils import secure_filename
import os
from datetime import datetime
from functools import wraps
from decorators import login_required
from dotenv import load_dotenv
import bcrypt

from api.item_routes import item_routes, init_item_routes