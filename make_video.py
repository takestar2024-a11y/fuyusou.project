"""
審美眼 プロモーション動画ジェネレーター
出力: promo.mp4 (75秒, 1920x1080, 30fps)
"""

from moviepy import *
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import os

W, H = 1920, 1080
FPS = 30
BG_COLOR = (10, 10, 10)       # #0a0a0a
GOLD = (212, 175, 55)          # #d4af37
WHITE = (229, 229, 229)        # #e5e5e5
MUTED = (163, 163, 163)        # #a3a3a3

FONT_GOTHIC = "/usr/share/fonts/truetype/fonts-japanese-gothic.ttf"
FONT_PATH = FONT_GOTHIC

def load_font(size):
    return ImageFont.truetype(FONT_PATH, size)

def make_frame(texts, duration, fade_in=1.0, fade_out=0.8, hold=None):
    """
    texts: list of (text, color, font_size, y_offset_from_center)
    Returns a moviepy ImageClip with fade in/out.
    """
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    center_y = H // 2
    for text, color, size, y_off in texts:
        font = load_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        y = center_y + y_off - (bbox[3] - bbox[1]) // 2
        draw.text((x, y), text, font=font, fill=color)

    arr = np.array(img)

    clip = ImageClip(arr, duration=duration)

    # Fade in / fade out
    clip = clip.with_effects([
        vfx.FadeIn(fade_in),
        vfx.FadeOut(fade_out),
    ])
    return clip

def make_divider(duration=0.4):
    """Gold horizontal line"""
    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    line_w = 120
    x1 = (W - line_w) // 2
    x2 = x1 + line_w
    draw.line([(x1, H // 2), (x2, H // 2)], fill=GOLD, width=2)
    arr = np.array(img)
    return ImageClip(arr, duration=duration)

# ── シーン定義 ─────────────────────────────────────────────
# (texts_list, duration_sec)

scenes = [
    # 0: オープニング — 無音暗転
    ([], 2.0),

    # 1: フック前半
    ([
        ("年収1,000万を超えても、", WHITE, 52, -70),
    ], 3.0),

    # 2: フック後半
    ([
        ("年収1,000万を超えても、", MUTED, 44, -90),
        ("なぜか「この判断、合ってるのか」と", WHITE, 52, -10),
        ("夜中に考えてしまう。", WHITE, 52, 60),
    ], 4.5),

    # 3: 転換
    ([
        ("それは、知識が足りないからじゃない。", GOLD, 56, 0),
    ], 3.5),

    # 4: テロップ風
    ([
        ("情報が、多すぎるから。", WHITE, 72, 0),
    ], 3.0),

    # 5: 時代の説明
    ([
        ("AIが毎日、何千もの「答え」を生成する時代。", MUTED, 44, -60),
        ("情報は、もう武器にならない。", WHITE, 52, 20),
    ], 4.5),

    # 6: 価値の定義
    ([
        ("本当に価値があるのは——", MUTED, 44, -60),
        ("何を切り捨てるか、を決める目。", GOLD, 60, 30),
    ], 4.5),

    # 7: プログラム説明
    ([
        ("このプログラムは、投資の正解を教えません。", WHITE, 48, -80),
        ("月2回のテキスト配信を通じて、", MUTED, 40, -10),
        ("あなたの判断の軸そのものを、", WHITE, 48, 50),
        ("静かに、鍛えます。", GOLD, 52, 110),
    ], 6.0),

    # 8: 気づき
    ([
        ("3ヶ月後、あなたは気づく。", MUTED, 44, -70),
    ], 3.0),

    # 9: 対比
    ([
        ("「騙されていた」のではなく、", WHITE, 52, -50),
        ("「選ぶ基準がなかった」だけだったと。", GOLD, 56, 30),
    ], 5.0),

    # 10: 形式説明
    ([
        ("顔出しなし。通話なし。", MUTED, 44, -50),
        ("あなたの時間は、奪いません。", WHITE, 52, 30),
    ], 4.0),

    # 11: 価格テロップ
    ([
        ("¥49,800（税込）", GOLD, 80, 0),
    ], 3.5),

    # 12: 価値訴求
    ([
        ("一度の誤った判断が、", WHITE, 48, -80),
        ("何百万円を消す世界で生きているなら——", WHITE, 48, -10),
    ], 4.5),

    # 13: クロージング
    ([
        ("この3ヶ月は、保険じゃない。", MUTED, 52, -50),
        ("資産です。", GOLD, 88, 40),
    ], 5.0),

    # 14: ロゴ
    ([
        ("審美眼", GOLD, 96, -30),
    ], 5.5),

    # 15: エンド暗転
    ([], 2.5),
]

def build_clip(texts, duration):
    if not texts:
        img = Image.new("RGB", (W, H), BG_COLOR)
        arr = np.array(img)
        return ImageClip(arr, duration=duration)

    img = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)
    center_y = H // 2
    for text, color, size, y_off in texts:
        font = load_font(size)
        bbox = draw.textbbox((0, 0), text, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2
        y = center_y + y_off - (bbox[3] - bbox[1]) // 2
        draw.text((x, y), text, font=font, fill=color)

    arr = np.array(img)
    clip = ImageClip(arr, duration=duration)

    fade_in = min(0.8, duration * 0.25)
    fade_out = min(0.6, duration * 0.2)
    clip = clip.with_effects([
        vfx.FadeIn(fade_in),
        vfx.FadeOut(fade_out),
    ])
    return clip

print("シーンを生成中...")
clips = []
for i, (texts, dur) in enumerate(scenes):
    print(f"  シーン {i+1}/{len(scenes)} ({dur}s)")
    clips.append(build_clip(texts, dur))

print("動画を結合・エンコード中...")
final = concatenate_videoclips(clips, method="compose")

out_path = "/home/user/fuyusou.project/promo.mp4"
final.write_videofile(
    out_path,
    fps=FPS,
    codec="libx264",
    audio=False,
    logger="bar",
    threads=4,
)
print(f"\n完成: {out_path}")
print(f"尺: {final.duration:.1f}秒")
