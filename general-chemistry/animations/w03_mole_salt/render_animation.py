#!/usr/bin/env python3
from __future__ import annotations
import json, math, subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1280, 720, 24
AUDIO = ROOT / 'narration.wav'
OUT = ROOT / 'w03_mole_salt_animation.mp4'
FONT = '/mnt/c/Windows/Fonts/msjh.ttc'
BOLD = '/mnt/c/Windows/Fonts/msjhbd.ttc'
if not Path(FONT).exists():
    FONT = BOLD = '/mnt/c/Windows/Fonts/mingliu.ttc'

def ft(n, bold=False): return ImageFont.truetype(BOLD if bold else FONT, n)
F = {k: ft(v[0], bool(v[1])) for k, v in {
    'title':(54,1),'h1':(42,1),'h2':(34,1),'body':(30,0),'small':(23,0),'tiny':(18,0),'formula':(38,1),'num':(56,1)
}.items()}
BG=(246,251,255); BLUE=(42,117,181); DARK=(26,44,64); CYAN=(91,192,222); TEAL=(33,166,153)
ORANGE=(244,151,64); RED=(213,79,93); GREEN=(74,166,88); PURPLE=(126,97,195); GRAY=(88,104,120); LIGHT=(221,238,250); YELLOW=(255,235,153)
CAPS=[(0,7,'泡麵標示「鈉 1800 mg」\n不等於 1.8 g 食鹽'),(7,16,'標示的是元素鈉 Na\n食鹽是化合物 NaCl'),(16,25,'第一步：1800 mg Na\n= 1.8 g Na'),(25,39,'第二步：用莫耳質量比例\nNaCl / Na = 58.44 / 22.99'),(39,50,'1.8 g × 2.54\n約 4.6 g 食鹽'),(50,60,'1800 / 2400 = 75%\n一包約吃掉四分之三上限'),(60,70,'鈉不是鹽；元素到化合物\n要靠化學式與莫耳質量')]
STORY=[{'t':[a,b],'caption':c} for a,b,c in CAPS]

def dur(path):
    r=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(path)],capture_output=True,text=True,check=True)
    return float(r.stdout.strip())
TOTAL=max(70.0, dur(AUDIO)+0.2)

def cl(x): return max(0,min(1,x))
def sm(x): x=cl(x); return x*x*(3-2*x)
def prog(t,a,b): return sm((t-a)/(b-a))
def rr(d,xy,r,fill,outline=None,w=2): d.rounded_rectangle(xy,radius=r,fill=fill,outline=outline,width=w)
def center(d,xy,text,fnt,fill=DARK,sp=8): d.multiline_text(xy,text,font=fnt,fill=fill,anchor='mm',align='center',spacing=sp)
def bbox(d,text,fnt):
    b=d.multiline_textbbox((0,0),text,font=fnt,spacing=6); return b[2]-b[0],b[3]-b[1]
def pill(d,x,y,text,fill,fg=(255,255,255),pad=20,fnt=None):
    fnt=fnt or F['small']; tw,th=bbox(d,text,fnt); rr(d,(x,y,x+tw+2*pad,y+th+18),24,fill); d.text((x+pad,y+9),text,font=fnt,fill=fg)

def header(d,t):
    d.text((42,28),'普通化學 W03｜莫耳與化學式',font=F['small'],fill=BLUE)
    d.text((42,60),'從營養標示：鈉 1800 mg 到 食鹽幾克？',font=F['h2'],fill=DARK)
    rr(d,(42,104,W-42,116),7,(226,238,247)); rr(d,(42,104,42+(W-84)*cl(t/TOTAL),116),7,BLUE)

def label(d,x,y,s=1.0):
    w,h=int(340*s),int(250*s); rr(d,(x,y,x+w,y+h),int(26*s),(255,255,255),BLUE,4); d.rectangle((x,y,x+w,y+int(60*s)),fill=(229,244,253))
    d.text((x+24*s,y+16*s),'營養標示',font=ft(int(30*s), True),fill=DARK)
    yy=y+int(82*s)
    for k,v in [('熱量','410 kcal'),('蛋白質','9 g'),('脂肪','18 g'),('鈉','1800 mg')]:
        col=RED if k=='鈉' else GRAY; d.text((x+30*s,yy),k,font=ft(int(25*s), True),fill=col); d.text((x+w-int(34*s),yy),v,font=ft(int(25*s), True),fill=col,anchor='ra'); yy+=int(39*s)
    d.text((x+24*s,y+h-38*s),'重點：標的是鈉，不是鹽',font=ft(int(18*s), True),fill=RED)

def atom(d,cx,cy,text,color,r=48):
    d.ellipse((cx-r,cy-r,cx+r,cy+r),fill=color,outline=(255,255,255),width=5); d.text((cx,cy),text,font=F['h1'],fill=(255,255,255),anchor='mm'); d.ellipse((cx-r-8,cy-r-8,cx+r+8,cy+r+8),outline=color,width=2)

def caption(d,t):
    cap=''
    for a,b,c in CAPS:
        if a<=t<b: cap=c; break
    if cap:
        rr(d,(170,604,1110,694),24,(255,255,255),(197,221,238),2); center(d,(640,649),cap,F['body'])

def s1(d,t):
    p=prog(t,0,7); label(d,105+int(30*math.sin(t*1.4)),220,1.15); center(d,(820,250),'常見錯誤',F['h1'],RED)
    d.text((680,320),'1800 mg 鈉',font=F['formula'],fill=RED); d.text((815,385),'≠',font=ft(74, True),fill=DARK,anchor='mm'); d.text((680,435),'1.8 g 食鹽',font=F['formula'],fill=GRAY); d.line((670,460,1030,325),fill=RED,width=8)
    if p>.55: pill(d,725,535,'先問：標示的是哪一種物質？',BLUE)

def s2(d,t):
    p=prog(t,7,16); center(d,(640,170),'元素 Na  ≠  化合物 NaCl',F['title'])
    nx=330+int(130*p); cx=950-int(130*p); atom(d,nx,360,'Na',BLUE); atom(d,cx,360,'Cl',GREEN)
    if p>.55:
        d.line((nx+55,360,cx-55,360),fill=ORANGE,width=8); d.text((640,455),'NaCl',font=ft(68, True),fill=ORANGE,anchor='mm'); pill(d,418,515,'鹽的質量 = 鈉 + 氯',TEAL)

def s3(d,t):
    p=prog(t,16,25); center(d,(640,172),'第一步：單位先統一',F['title'])
    rr(d,(210,260,1070,450),28,(255,255,255),BLUE,4); d.text((270,318),'1800 mg Na',font=F['num'],fill=RED)
    d.text((625,330),'× 1 g / 1000 mg',font=F['formula'],fill=DARK); d.text((995,354),'=',font=ft(62, True),fill=GRAY,anchor='mm')
    if p>.45: d.text((780,405),'1.8 g Na',font=F['num'],fill=BLUE,anchor='mm')
    pill(d,380,505,'mg 消掉，留下 g',PURPLE)

def s4(d,t):
    p=prog(t,25,39); center(d,(640,160),'第二步：莫耳質量是橋',F['title'])
    for x,txt,col in [(270,'Na\n22.99 g/mol',BLUE),(1010,'NaCl\n58.44 g/mol',ORANGE)]:
        rr(d,(x-145,265,x+145,430),26,(255,255,255),col,5); center(d,(x,347),txt,F['h2'],col)
    d.line((420,350,860,350),fill=GRAY,width=5); d.polygon([(860,350),(830,332),(830,368)],fill=GRAY)
    ratio='58.44 / 22.99 = 2.54'; d.text((640,468),ratio,font=F['num'],fill=TEAL,anchor='mm')
    if p>.55: pill(d,420,535,'Na 只佔 NaCl 質量的 39.3%',RED)

def s5(d,t):
    p=prog(t,39,50); center(d,(640,160),'把鈉換算成食鹽',F['title'])
    d.text((190,300),'1.8 g Na',font=F['num'],fill=BLUE); d.text((500,300),'× 2.54',font=F['num'],fill=TEAL); d.text((760,300),'=',font=F['num'],fill=DARK)
    val=1.8*(1+1.54*p); d.text((850,300),f'{val:.1f} g',font=F['num'],fill=ORANGE)
    for i in range(34):
        x=210+(i%17)*48; y=430+(i//17)*55; a=cl((p*40-i)/8); col=(255,int(235-80*a),int(153-90*a)); d.ellipse((x,y,x+24,y+24),fill=col,outline=ORANGE)
    pill(d,430,530,'方向檢查：鹽一定比鈉重',BLUE)

def s6(d,t):
    p=prog(t,50,60); center(d,(640,160),'和每日鈉上限比較',F['title'])
    cx,cy,r=640,380,170; d.arc((cx-r,cy-r,cx+r,cy+r),180,360,fill=LIGHT,width=34); d.arc((cx-r,cy-r,cx+r,cy+r),180,180+180*.75*p,fill=RED,width=34)
    d.text((cx,cy-10),f'{int(75*p):d}%',font=ft(88, True),fill=RED,anchor='mm'); d.text((cx,cy+65),'1800 / 2400',font=F['h2'],fill=DARK,anchor='mm')
    pill(d,394,535,'一包泡麵約用掉 3/4 上限',ORANGE)

def s7(d,t):
    p=prog(t,60,70); center(d,(640,160),'帶走一句話',F['title'])
    center(d,(640,285),'鈉不是鹽',ft(82, True),RED)
    center(d,(640,390),'元素到化合物：看化學式，用莫耳質量',F['h1'],DARK)
    if p>.45:
        center(d,(640,500),'Na × 2.54 約等於 NaCl',F['num'],BLUE)
        d.text((640,560),'資料來源：普通化學 W03「莫耳與化學式」課程頁',font=F['small'],fill=GRAY,anchor='mm')

def bg(d):
    for i in range(0,W,80): d.line((i,126,i+160,H),fill=(237,246,252),width=1)
    for i in range(12):
        x=70+i*105; y=150+35*math.sin(i); d.ellipse((x,y,x+5,y+5),fill=(210,232,246))

def frame(t):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im); bg(d); header(d,t)
    if t<7: s1(d,t)
    elif t<16: s2(d,t)
    elif t<25: s3(d,t)
    elif t<39: s4(d,t)
    elif t<50: s5(d,t)
    elif t<60: s6(d,t)
    else: s7(d,t)
    caption(d,t)
    return im

def make_srt():
    def ts(x):
        h=int(x//3600); m=int((x%3600)//60); s=int(x%60); ms=int((x-int(x))*1000); return f'{h:02}:{m:02}:{s:02},{ms:03}'
    out=[]
    for i,(a,b,c) in enumerate(CAPS,1): out += [str(i),f'{ts(a)} --> {ts(min(b,TOTAL))}',c,'']
    (ROOT/'w03_mole_salt_animation.srt').write_text('\n'.join(out),encoding='utf-8')
    (ROOT/'storyboard.json').write_text(json.dumps({'title':'W03 sodium to salt animation','fps':FPS,'size':[W,H],'storyboard':STORY},ensure_ascii=False,indent=2),encoding='utf-8')

def render():
    make_srt(); n=int(TOTAL*FPS)
    cmd=['ffmpeg','-y','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-i',str(AUDIO),'-c:v','libx264','-preset','medium','-crf','24','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k','-shortest',str(OUT)]
    p=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    assert p.stdin
    for i in range(n): p.stdin.write(frame(i/FPS).tobytes())
    p.stdin.close(); rc=p.wait();
    if rc: raise SystemExit(rc)
    print(OUT)
if __name__=='__main__': render()
