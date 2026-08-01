import numpy as np, matplotlib
from matplotlib import font_manager, gridspec
_cjk="/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"
font_manager.fontManager.addfont(_cjk)
matplotlib.rcParams["font.family"]=font_manager.FontProperties(fname=_cjk).get_name()
matplotlib.rcParams["axes.unicode_minus"]=False
import matplotlib.pyplot as plt

GRID=np.arange(120,1750,1.0)
def build(peaks,x,width):
    y=np.zeros_like(x,dtype=float)
    for cm,I,w in peaks: y+=I*np.exp(-0.5*((x-cm)/w)**2)
    return y/y.max()

# CoAl2O4 spinel: (cm-1, rel intensity, width)  positions from literature; intensities illustrative
COAL=[(203,0.55,13),(410,0.40,15),(514,0.80,15),(617,0.35,15),(755,1.00,16)]
# CuPc (molecular, sharper)
CUPC=[(232,0.50,9),(254,0.55,9),(480,0.34,9),(593,0.16,9),(677,0.54,9),(748,0.63,9),
      (773,0.13,9),(950,0.22,9),(1140,0.37,9),(1188,0.20,9),(1302,0.19,9),
      (1337,0.62,9),(1453,0.24,9),(1526,1.00,9)]
coal=build(COAL,GRID,None) if False else build([(c,i,w) for c,i,w in COAL],GRID,None)
def build2(peaks,x):
    y=np.zeros_like(x,dtype=float)
    for cm,I,w in peaks: y+=I*np.exp(-0.5*((x-cm)/w)**2)
    return y/y.max()
coal=build2(COAL,GRID); cupc=build2(CUPC,GRID)

def load(p):
    d=np.loadtxt(p,delimiter=','); x,y=d[:,0],d[:,1]; o=np.argsort(x); return x[o],y[o]
def modpoly(x,y,o=5,it=24):
    yw=y.copy()
    for _ in range(it): c=np.polyfit(x,yw,o); yw=np.minimum(yw,np.polyval(c,x))
    return np.polyval(np.polyfit(x,yw,o),x)
x3,y3=load('/mnt/user-data/uploads/cobltblue3.csv'); m=(x3>150)&(x3<=1650)
xf,yf=x3[m],y3[m]; base=modpoly(xf,yf); meas=np.clip(yf-base,0,None); meas=meas/meas.max()

BLUE,COBALT,COPPER="#0b7ba6","#274b8f","#b3703f"
fig=plt.figure(figsize=(11,7.8),dpi=140)
gs=gridspec.GridSpec(3,1,hspace=0.14)
CUPC4=[748,1337,1453,1526]

ax1=fig.add_subplot(gs[0])
ax1.plot(GRID,coal,color=COBALT,lw=1.6)
ax1.axvline(514,color='#d11',lw=1.6,ls='--',alpha=.85)
for c,i,w in COAL: ax1.annotate(f"{c}",(c,np.interp(c,GRID,coal)),textcoords="offset points",xytext=(0,3),ha="center",fontsize=8,color="#3f5a63")
ax1.text(0.01,0.83,"真鈷藍 CoAl₂O₄(PB28)— 合成參考",transform=ax1.transAxes,fontweight='bold',color=COBALT,fontsize=12)
ax1.text(514,0.5,"514 診斷峰",color='#d11',fontsize=8.5,rotation=90,va='center',ha='right')
ax1.set_xticklabels([])

ax2=fig.add_subplot(gs[1])
ax2.plot(GRID,cupc,color=BLUE,lw=1.5)
for r in CUPC4: ax2.axvspan(r-11,r+11,color=BLUE,alpha=.12)
for c,i,w in CUPC:
    if i>=0.3: ax2.annotate(f"{c}",(c,np.interp(c,GRID,cupc)),textcoords="offset points",xytext=(0,3),ha="center",fontsize=7.5,color="#3f5a63")
ax2.text(0.01,0.83,"銅酞菁 CuPc / PB15 — 合成參考(酞菁仿色的成分)",transform=ax2.transAxes,fontweight='bold',color=BLUE,fontsize=12)
ax2.set_xticklabels([])

ax3=fig.add_subplot(gs[2])
ax3.plot(xf,meas,color='#123',lw=1.0)
for r in CUPC4: ax3.axvspan(r-11,r+11,color=BLUE,alpha=.12)
ax3.axvline(514,color='#d11',lw=1.6,ls='--',alpha=.85)
ax3.text(0.01,0.83,"你的實測『cobalt blue』(File 3)",transform=ax3.transAxes,fontweight='bold',color='#123',fontsize=12)
ax3.annotate("對上 CuPc 四峰組",xy=(1526,0.95),xytext=(1250,0.9),fontsize=9,color=BLUE,arrowprops=dict(arrowstyle='->',color=BLUE))
ax3.annotate("514 缺",xy=(514,0.35),xytext=(560,0.6),fontsize=9,color='#d11',arrowprops=dict(arrowstyle='->',color='#d11'))
ax3.set_xlabel("Raman shift (cm$^{-1}$)",fontsize=11)

for ax in (ax1,ax2,ax3):
    ax.set_xlim(150,1650); ax.set_ylim(0,1.15); ax.set_ylabel("norm.")
    for s in ('top','right'): ax.spines[s].set_visible(False)
fig.suptitle("真鈷藍 vs 酞菁仿色 — 你的樣品是哪一個?",fontsize=13.5,y=0.955)
fig.text(0.5,0.005,"CoAl₂O₄ 峰位取自文獻(尖晶石五模,強度示意);CuPc 同前。實測 File 3 對上 CuPc 四峰組、缺 514 → 酞菁仿色。",ha="center",fontsize=7.5,color="#888")
plt.savefig('/mnt/user-data/outputs/cobalt_real_vs_imitation.png',dpi=150,bbox_inches='tight')
print("saved figure")

np.savetxt('/mnt/user-data/outputs/raman_CoAl2O4_reference.csv',
           np.column_stack([GRID,coal]),delimiter=',',
           header="wavenumber_cm-1,CoAl2O4",comments="",fmt="%.4f")
print("saved CoAl2O4 reference CSV")
