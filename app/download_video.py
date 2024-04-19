import asyncio
import io
import glob
import os
import urllib.request
from os import path

import aiohttp
from tiktokapipy.async_api import AsyncTikTokAPI
from tiktokapipy.models.video import Video
import time

# link = "https://www.tiktok.com/@tranquynh3679/video/7326893066634399022"
# link = "https://www.tiktok.com/@quynhonwithngan/video/7220695498028616986"
# link = "https://www.tiktok.com/@emlyreview/video/7358018140036467975"
# link = "https://www.tiktok.com/@tranquynh3679/video/7358112644764699950"
# link = "https://www.tiktok.com/@emlyreview/video/7358388448648088853"
# link = "https://www.tiktok.com/@irishlian4/video/7218714410846522629?q=image&t=1713407819977"
# link = "https://www.tiktok.com/@xasicam/video/7256375237875354886?q=image&t=1713407819977"
link = "https://www.tiktok.com/@babuimagep/video/7351634217236794632?q=image&t=1713407819977"
directory = "/home/j3s/NghiaND/TikTokPy/outputs"

async def save_slideshow(video: Video):
    # this filter makes sure the images are padded to all the same size
    vf = "\"scale=iw*min(1080/iw\,1920/ih):ih*min(1080/iw\,1920/ih)," \
         "pad=1080:1920:(1080-iw)/2:(1920-ih)/2," \
         "format=yuv420p\""

    for i, image_data in enumerate(video.image_post.images):
        url = image_data.image_url.url_list[-1]
        # this step could probably be done with asyncio, but I didn't want to figure out how
        urllib.request.urlretrieve(url, path.join(directory, f"temp_{video.id}_{i:02}.jpg"))

    urllib.request.urlretrieve(video.music.play_url, path.join(directory, f"temp_{video.id}.mp3"))

    # use ffmpeg to join the images and audio
    command = [
        "ffmpeg",
        "-r 2/5",
        f"-i {directory}/temp_{video.id}_%02d.jpg",
        f"-i {directory}/temp_{video.id}.mp3",
        "-r 30",
        f"-vf {vf}",
        "-acodec copy",
        f"-t {len(video.image_post.images) * 2.5}",
        f"{directory}/temp_{video.id}.mp4",
        "-y"
    ]
    ffmpeg_proc = await asyncio.create_subprocess_shell(
        " ".join(command),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await ffmpeg_proc.communicate()
    generated_files = glob.glob(path.join(directory, f"temp_{video.id}*"))

    if not path.exists(path.join(directory, f"temp_{video.id}.mp4")):
        # optional ffmpeg logging step
        # logging.error(stderr.decode("utf-8"))
        for file in generated_files:
            os.remove(file)
        raise Exception("Something went wrong with piecing the slideshow together")

    with open(path.join(directory, f"temp_{video.id}.mp4"), "rb") as f:
        ret = io.BytesIO(f.read())

    for file in generated_files:
        os.remove(file)

    return ret

async def save_video(video, user, music, api):
    # Carrying over this cookie tricks TikTok into thinking this ClientSession was the Playwright instance
    # used by the AsyncTikTokAPI instance
    async with aiohttp.ClientSession(cookies={cookie["name"]: cookie["value"] for cookie in await api.context.cookies() if cookie["name"] == "tt_chain_token"}) as session:
        # Creating this header tricks TikTok into thinking it made the request itself
        async with session.get(video.video.play_addr, headers={"referer": "https://www.tiktok.com/"}) as resp:
            downloaded_video_play_addr = io.BytesIO(await resp.read())
            with open(directory + '/video_unwattermark.mp4', 'wb') as f:
                f.write(downloaded_video_play_addr.getbuffer())
                
        async with session.get(video.video.download_addr, headers={"referer": "https://www.tiktok.com/"}) as resp:
            downloaded_video_addr = io.BytesIO(await resp.read())
            with open(directory + '/video_wattermark.mp4', 'wb') as f:
                f.write(downloaded_video_addr.getbuffer())
        
        async with session.get(music.get("playUrl"), headers={"referer": "https://www.tiktok.com/"}) as resp:
            downloaded_music_play_url = io.BytesIO(await resp.read())
            with open(directory + '/audio.mp3', 'wb') as f:
                f.write(downloaded_music_play_url.getbuffer())

        async with session.get(user.get("avatarMedium")) as resp:
            downloaded_avatar_larger =  io.BytesIO(await resp.read())
            with open(directory + '/avatar_medium.jpeg', 'wb') as f:
                f.write(downloaded_avatar_larger.getbuffer())
        
                
        num_comments = video.stats.comment_count
        num_likes = video.stats.digg_count
        num_views = video.stats.play_count
        num_shares = video.stats.share_count

        print(video.desc) 
        print("Num comment: ", num_comments)
        print("Num like: ", num_likes)
        print("Num share: ", num_shares)
        print("Num view: ", num_views)


async def save_audio(music):
    async with aiohttp.ClientSession() as session:
        async with session.get(music.get("playUrl")) as resp:
            downloaded = io.BytesIO(await resp.read())
            with open(directory + '/audio.wav', 'wb') as f:
                f.write(downloaded.getbuffer())


async def download_video():
    async with AsyncTikTokAPI() as api:
        start_time = time.time()
        video, user, music = await api.video_user_music(link)
        if video.image_post:
            downloaded = await save_slideshow(video)
            
        else: 
            await save_video(video, user, music, api)
            print(user.get("nickname"))
            print(user.get("uniqueId"))
        print("--- %s seconds ---" % (time.time() - start_time))
        
if __name__ == "__main__":
    asyncio.run(download_video())