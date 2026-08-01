"""
把 _source/ 裡的三個頁面組成「單檔即可開啟」的 HTML。

外部的 course.css / data.js / interactive.js / img/*.png 會被直接嵌進檔案裡，
所以單獨把一個 .html 寄給別人、或在任何預覽器裡打開，樣式、互動與圖都還在。
這也是 raman-food-analysis/teaching.html 的作法（單檔內含 <style>）。

    python build.py
"""
import base64
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "_source")

css = open(os.path.join(SRC, "course.css"), encoding="utf-8").read()
data_js = open(os.path.join(SRC, "data.js"), encoding="utf-8").read()
inter_js = open(os.path.join(SRC, "interactive.js"), encoding="utf-8").read()


def img_b64(rel):
    with open(os.path.join(HERE, rel), "rb") as f:
        return "data:image/png;base64," + base64.b64encode(f.read()).decode()


def build(name):
    html = open(os.path.join(SRC, name), encoding="utf-8").read()

    html = html.replace('<link rel="stylesheet" href="course.css">',
                        "<style>\n" + css + "\n</style>")
    html = html.replace('<script src="data.js"></script>\n<script src="interactive.js"></script>',
                        "<script>\n" + data_js + "\n</script>\n<script>\n" + inter_js + "\n</script>")

    used = sorted(set(re.findall(r'src="(img/[^"]+)"', html)))
    for rel in used:
        html = html.replace('src="%s"' % rel, 'src="%s"' % img_b64(rel))

    out = os.path.join(HERE, name)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    size = os.path.getsize(out) / 1024
    print("  %-14s %6.0f KB   內嵌圖 %d 張" % (name, size, len(used)))
    return html


print("組裝單檔頁面：")
for page in ["index.html", "teaching.html", "quiz.html"]:
    h = build(page)
    leftovers = re.findall(r'(?:href|src)="(?:course\.css|data\.js|interactive\.js|img/[^"]+)"', h)
    if leftovers:
        print("    ⚠ 仍有未內嵌的外部參照：", leftovers)
print("完成。這三個檔案現在可以單獨開啟。")
