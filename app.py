from flask import abort, Flask, jsonify, request, send_from_directory
from flask_cors import CORS, cross_origin

import io
import os
import re
import boto3
import uuid
import time
import glob
import json
import shutil
import asyncio
import aiohttp
import aioboto3
import botocore
import requests

import jwt
import AppConfig

from os import path
import boto3.s3.transfer as s3transfer
from boto3.s3.transfer import TransferConfig

from tiktokapipy.api import TikTokAPI
from tiktokapipy.async_api import AsyncTikTokAPI
from tiktokapipy.models.video import Video

from utils.util_tiktokdownload import download_video
from utils.util_jwt import decode_jwt

import nest_asyncio
nest_asyncio.apply()


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# Config request
session_requests = requests.Session()
headers_requests = {'Accept-Encoding': 'gzip'}

root = "/home/j3s/NghiaND/TikTokPy/static/tiktokdownload"
directory_tmp = "/home/j3s/NghiaND/TikTokPy/outputs"

@app.route("/tiktok/download_authorization", methods=['POST'])
async def download_author():
    global session_requests, headers_requests
    
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        abort(401)
        
    try:
        bearer, token = auth_header.split()
        if bearer.lower() != 'bearer':
            abort(401)
    except ValueError:
        abort(401)
    
    payload = decode_jwt(token, "tiktokdownload_jwt_secret_job3s")    
    username = payload.get('username')
    password = payload.get('password')

    if username != AppConfig.USERNAME or password != AppConfig.PASSWORD:
        abort(401)
    
    link_tiktok = request.form['link']
    
    if "www.tiktok.com" not in link_tiktok:
        s_convert = time.time()
        body = session_requests.get(link_tiktok, headers=headers_requests)
    
        link_tiktok = body.url   
        
        link_tiktok = re.sub('\/\?', '?', link_tiktok)
        
        print("Time convert: %s second" % (time.time() - s_convert))
    
    response = asyncio.run(download_video(link_tiktok))
    
    return jsonify(response)

@app.route("/tiktok/download", methods=['POST'])
async def download():
    global session_requests, headers_requests
    
    link_tiktok = request.form['link']
    
    if "www.tiktok.com" not in link_tiktok:
        s_convert = time.time()
        body = session_requests.get(link_tiktok, headers=headers_requests)
    
        link_tiktok = body.url   
        
        link_tiktok = re.sub('\/\?', '?', link_tiktok)
        
        print("Time convert: %s second" % (time.time() - s_convert))
    
    response = asyncio.run(download_video(link_tiktok))
    
    return jsonify(response)


@app.route('/file/<path:filename>', methods=['GET'])
def serve_static(filename):
    # Đường dẫn đến thư mục chứa tệp tin tĩnh
    static_folder = 'static'
    
    return send_from_directory(static_folder, filename)

@app.route('/tiktok/token/generate', methods=['POST'])
def generate_jwt():
    username = request.form['username']
    password = request.form['password']
    
    payload = {
        "username": username,
        "password": password
    }

    token = jwt.encode(payload, AppConfig.SECRET_KEY, algorithm='HS256')
    return jsonify({"jwt_token": token})

if __name__ == '__main__':
    # app.run(debug = True, host='0.0.0.0', port=2312)
    app.run(debug = False, host='0.0.0.0', port=8000, use_reloader=False)