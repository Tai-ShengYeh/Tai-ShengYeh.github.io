# -*- coding: utf-8 -*-
"""把 storyboard.json 與各幕配音長度注入 player_template.html，輸出 ../animation.html。

用法（在 hplc-caffeine/animation 目錄下）:
    python build_animation.py

需要 ffprobe（量測 s1.mp3 … s6.mp3 的長度）。
配音：ElevenLabs，聲音 Door Chow，模型 eleven_v3，
產生後以 ffmpeg atempo=0.95 放慢 5%，並修掉開頭靜音。
"""
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "animation.html")
MARKER = "/*__META__*/null"


def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return round(float(r.stdout.strip()), 3)


def main():
    with open(os.path.join(HERE, "storyboard.json"), encoding="utf-8") as f:
        sb = json.load(f)
    scenes = [{k: s[k] for k in ("id", "title", "narration", "tts")} | {"pause": bool(s.get("pause")), "cues": s.get("cues")}
              for s in sb["scenes"]]
    durs = [duration(os.path.join(HERE, f"{s['id']}.mp3")) for s in scenes]
    meta = {"scenes": scenes, "durations": durs}
    with open(os.path.join(HERE, "player_template.html"), encoding="utf-8") as f:
        html = f.read()
    if MARKER not in html:
        raise SystemExit("模板中找不到 " + MARKER)
    html = html.replace(MARKER, json.dumps(meta, ensure_ascii=False))
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("寫出", os.path.normpath(OUT), "總長", round(sum(durs) + len(durs), 1), "秒", durs)


if __name__ == "__main__":
    main()
