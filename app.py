from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS, cross_origin

import io
import os
import boto3
import uuid
import time
import glob
import json
import asyncio
import aiohttp
import aioboto3
import botocore

from os import path
from tiktokapipy.async_api import AsyncTikTokAPI
from tiktokapipy.models.video import Video
import boto3.s3.transfer as s3transfer
from boto3.s3.transfer import TransferConfig

import nest_asyncio
nest_asyncio.apply()


app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

root = "/home/j3s/NghiaND/TikTokPy/static/tiktokdownload"
                
async def save_video(url_video, path_save, cookies, start_time):
    async with aiohttp.ClientSession(cookies=cookies) as session:
        async with session.get(url_video, headers={"referer": "https://www.tiktok.com/"}) as resp:
            downloaded_video_play_addr = io.BytesIO(await resp.read())
            with open(path_save, 'wb') as f:
                f.write(downloaded_video_play_addr.getbuffer())
        
    print("--- %s video ---" % (time.time() - start_time))


async def save_audio(music_info, path_save, start_time):
    async with aiohttp.ClientSession() as session:
        async with session.get(music_info.get("playUrl"), headers={"referer": "https://www.tiktok.com/"}) as resp:
            downloaded_music_play_url = io.BytesIO(await resp.read())
            with open(path_save, 'wb') as f:
                f.write(downloaded_music_play_url.getbuffer())
    
    print("--- %s music ---" % (time.time() - start_time))

async def save_avatar(user_info, path_save, start_time):
    async with aiohttp.ClientSession() as session:
        async with session.get(user_info.get("avatarMedium")) as resp:
            downloaded_avatar_larger =  io.BytesIO(await resp.read())
            with open(path_save, 'wb') as f:
                f.write(downloaded_avatar_larger.getbuffer())
    
    print("--- %s avatar ---" % (time.time() - start_time))

async def save_cover(video_info, path_save, start_time):
    async with aiohttp.ClientSession() as session:
        async with session.get(video_info.get("cover")) as resp:
            downloaded_cover =  io.BytesIO(await resp.read())
            with open(path_save, 'wb') as f:
                f.write(downloaded_cover.getbuffer())
                
    print("--- %s image video cover ---" % (time.time() - start_time))

async def crawl_info(link):
    async with AsyncTikTokAPI() as api:
        start_time = time.time()
        video, user_info, music_info, video_info, all_info = await api.video_user_music(link)
        id_video = video_info.get("id")
        id_music = music_info.get("id")
        id_user = user_info.get("id")
        format_video = video_info.get("format")
        format_audio = "mp3"
        format_avatar = "jpeg"
        
        os.makedirs(f"{root}/{id_user}/video/watermark", exist_ok=True)
        os.makedirs(f"{root}/{id_user}/video/unwatermark", exist_ok=True)
        os.makedirs(f"{root}/{id_user}/audio",exist_ok=True)
        os.makedirs(f"{root}/{id_user}/avatar", exist_ok=True)
        os.makedirs(f"{root}/{id_user}/cover", exist_ok=True)
            
        key_video_unwatermark_normal = f"{root}/{id_user}/video/unwatermark/{id_video}.{format_video}"
        key_video_unwatermark_fullhd = f"{root}/{id_user}/video/unwatermark/{id_video}_fullhd.{format_video}"
        key_audio = f"{root}/{id_user}/audio/{id_music}.{format_audio}"
        key_avatar = f"{root}/{id_user}/avatar/{id_user}.{format_avatar}"
        key_cover = f"{root}/{id_user}/cover/{id_video}.{format_avatar}"
        
        
        dict_aws = {
            "key_video_unwatermark_normal": key_video_unwatermark_normal,
            "key_video_unwatermark_fullhd": key_video_unwatermark_fullhd,
            "key_audio": key_audio,
            "key_avatar": key_avatar,
            "key_cover": key_cover,
            "format_video": format_video,
            "format_audio": format_audio,
            "format_avatar": format_avatar
        }
        
        cookies={cookie["name"]: cookie["value"] for cookie in await api.context.cookies() if cookie["name"] == "tt_chain_token"}
        
    print("--- %s Crawl info ---" % (time.time() - start_time))
    return video, user_info, music_info, video_info, all_info, dict_aws, cookies    
 
async def download_video(link):
    start_time = time.time()
    video, user_info, music_info, video_info, all_info, dict_aws, cookies = await crawl_info(link)
    
    print("======= crawl info: %s second " % (time.time() - start_time))
    
    key_video_unwatermark_normal = dict_aws.get("key_video_unwatermark_normal")
    key_video_unwatermark_fullhd = dict_aws.get("key_video_unwatermark_fullhd")
    key_audio = dict_aws.get("key_audio")
    key_avatar = dict_aws.get("key_avatar")
    key_cover = dict_aws.get("key_cover")
    
    flash_fullhd = False
    url_video_normal = video.get("normal")
    url_video_fullhd = video.get("fullhd")
    url_video_hd = video.get("hd")
    
    with open("/home/j3s/NghiaND/TikTokPy/outputs/response.json", 'w', encoding='utf-8') as f:
        json.dump(all_info, f, indent=4)
    
    if url_video_fullhd is not None:
        flash_fullhd = True
    elif url_video_hd is not None:
        flash_fullhd = True
        url_video_fullhd = url_video_hd
    
    if not os.path.exists(key_video_unwatermark_normal) \
        or not os.path.exists(key_video_unwatermark_fullhd) \
        or not os.path.exists(key_audio) \
        or not os.path.exists(key_avatar) \
        or not os.path.exists(key_cover):

        if flash_fullhd:
            await asyncio.gather(save_video(url_video_normal, dict_aws.get("key_video_unwatermark_normal"), cookies, start_time),
                                save_video(url_video_fullhd, dict_aws.get("key_video_unwatermark_fullhd"), cookies, start_time),
                                save_avatar(user_info, dict_aws.get("key_avatar"), start_time),
                                save_audio(music_info, dict_aws.get("key_audio"), start_time),
                                save_cover(video_info, dict_aws.get("key_cover"), start_time))
        
        else:
            await asyncio.gather(save_video(url_video_normal, dict_aws.get("key_video_unwatermark_normal"), cookies, start_time),
                                save_avatar(user_info, dict_aws.get("key_avatar"), start_time),
                                save_audio(music_info, dict_aws.get("key_audio"), start_time),
                                save_cover(video_info, dict_aws.get("key_cover"), start_time))
            
            key_video_unwatermark_fullhd = key_video_unwatermark_normal
        
        # async with aioboto3.Session().client(service_name='s3', region_name=REGION_NAME, aws_access_key_id=AWS_ACCESS_KEY_ID, aws_secret_access_key=AWS_SECRET_ACCESS_KEY) as client:
        #     await client.upload_fileobj(downloaded_video_play_addr, bucket_name, dict_aws.get("key_video_unwatermark"),
        #                             ExtraArgs={ 'ACL': 'public-read', 'ContentType': f'video/{dict_aws.get("format_video")}', 'CacheControl': 'public, max-age=2592000'},
        #                             Config=config)
        #     await client.upload_fileobj(downloaded_video_addr, bucket_name, dict_aws.get("key_video_watermark"),
        #                         ExtraArgs={ 'ACL': 'public-read', 'ContentType': f'video/{dict_aws.get("format_video")}', 'CacheControl': 'public, max-age=2592000'},
        #                         Config=config)
        #     await client.upload_fileobj(downloaded_music_play_url, bucket_name, dict_aws.get("key_audio"),
        #                             ExtraArgs={ 'ACL': 'public-read', 'ContentType': f'audio/{dict_aws.get("format_audio")}', 'CacheControl': 'public, max-age=2592000'},
        #                             Config=config)
        #     await client.upload_fileobj(downloaded_avatar_larger, bucket_name, dict_aws.get("key_avatar"),
        #                             ExtraArgs={ 'ACL': 'public-read', 'ContentType': f'image/{dict_aws.get("format_avatar")}', 'CacheControl': 'public, max-age=2592000'},
        #                             Config=config)
            
    response = {
        "video": {
            "id": video_info.get("id"),
            "like": video.get("stats").get("diggCount"),
            "comment": video.get("stats").get("commentCount"),
            "view": video.get("stats").get("playCount"),
            "share": video.get("stats").get("shareCount"),
            "description": video.get("desc"),
            "duration": video_info.get("duration"),
            "createtime": all_info.get("itemInfo").get("itemStruct").get("createTime"),
            # "link_watermark": f"https://cdn.ssstik.cx/{key_video_watermark}",
            # "link_unwatermark": f"https://cdn.ssstik.cx/{key_video_unwatermark}"
            # "link_watermark": key_video_watermark.replace(root, "https://api2-download.ssstik.cx/static/tiktokdownload"),
            "link_unwatermark_normal": key_video_unwatermark_normal.replace(root, "https://api2-download.ssstik.cx/static/tiktokdownload"),
            "link_unwatermark_fullhd": key_video_unwatermark_fullhd.replace(root, "https://api2-download.ssstik.cx/static/tiktokdownload"),
            "link_cover": key_cover.replace(root, "https://api2-download.ssstik.cx/static/tiktokdownload")
        },
        "user": {
            "id": user_info.get("id"),
            "nickname": user_info.get("nickname"),
            "uniqueId": user_info.get("uniqueId"),
            "signature": user_info.get("signature"),
            # "link_avatar": f"https://cdn.ssstik.cx/{key_avatar}" 
            "link_avatar": key_avatar.replace(root, "https://api2-download.ssstik.cx/static/tiktokdownload")
        },
        "music": {
            "id": music_info.get("id"),
            "authorname": music_info.get("authorName"),
            "title": music_info.get("title"),
            "duration": music_info.get("duration"),
            # "link_music": f"https://cdn.ssstik.cx/{key_audio}"
            "link_music": key_audio.replace(root, "https://api2-download.ssstik.cx/static/tiktokdownload")
        }
    }
    print("--- %s seconds ---" % (time.time() - start_time))
    
    return response


@app.route("/tiktok/download", methods=['POST'])
def download():
    link_tiktok = request.form['link']
    
    response = asyncio.run(download_video(link_tiktok))
    
    return jsonify(response)


@app.route('/file/<path:filename>', methods=['GET'])
def serve_static(filename):
    # Đường dẫn đến thư mục chứa tệp tin tĩnh
    static_folder = 'static'
    
    return send_from_directory(static_folder, filename)

if __name__ == '__main__':
    app.run(debug = True, host='0.0.0.0', port=2312)
    # app.run(debug = False, host='0.0.0.0', port=8000, use_reloader=False)