"""
動画 + BGM を合成して promo_with_bgm.mp4 を生成
"""

from moviepy import VideoFileClip, AudioFileClip, CompositeAudioClip
from moviepy.audio.fx import AudioFadeOut, MultiplyVolume
import numpy as np

VIDEO = "/home/user/fuyusou.project/promo.mp4"
AUDIO = "/home/user/fuyusou.project/bgm.wav"
OUTPUT = "/home/user/fuyusou.project/promo_with_bgm.mp4"

print("Loading video and audio...")
video = VideoFileClip(VIDEO)
audio = AudioFileClip(AUDIO)

vid_dur = video.duration
aud_dur = audio.duration
print(f"Video: {vid_dur:.1f}s  Audio: {aud_dur:.1f}s")

# BGMをビデオの長さにトリム or ループ
if aud_dur < vid_dur:
    # ループして足りない分を補う
    loops = int(np.ceil(vid_dur / aud_dur))
    from moviepy import concatenate_audioclips
    audio = concatenate_audioclips([audio] * loops)

audio = audio.subclipped(0, vid_dur)

# 末尾2秒フェードアウト
audio = audio.with_effects([AudioFadeOut(2.0)])

# 音量調整（BGMなので少し下げる）
audio = audio.with_effects([MultiplyVolume(0.85)])

# 合成
final = video.with_audio(audio)

print("Encoding promo_with_bgm.mp4 ...")
final.write_videofile(
    OUTPUT,
    fps=30,
    codec="libx264",
    audio_codec="aac",
    audio_bitrate="192k",
    logger="bar",
    threads=4,
)

print(f"\n完成: {OUTPUT}")
print(f"尺: {final.duration:.1f}秒")

import os
print(f"サイズ: {os.path.getsize(OUTPUT)//1024}KB")
