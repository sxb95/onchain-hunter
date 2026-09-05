#!/usr/bin/env python3
"""OnchainHunter demo styles library — 多风格演示生成器.
每套风格 = 不同画幅 + 不同动画形式 + 不同时长, 可灵活选用.
"""
import os
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio

def _font(sz):
    for p in ["/System/Library/Fonts/PingFang.ttc","/System/Library/Fonts/STHeiti Medium.ttc",
              "/System/Library/Fonts/Hiragino Sans GB.ttc","/System/Library/Fonts/Menlo.ttc"]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p,sz)
            except: pass
    return ImageFont.load_default()

# ---- 风格A: 榜单柱状图动画 (bars) 16:9 ----
def style_bars(rows, out, title, accent=(255,122,69), bg=(15,13,13), W=1280,H=720,FPS=28,dur=10.0):
    """rows: list of (label, value, note). 柱从0增长+排序跳变."""
    fs=_font(20); fb=_font(26); fsm=_font(14)
    frames=[]; steps=int(dur*FPS)
    maxv=max([v for _,v,_ in rows]+[1])
    for k in range(steps):
        r=k/steps
        img=Image.new("RGB",(W,H),bg); d=ImageDraw.Draw(img)
        d.rectangle([0,0,W,52],fill=(24,19,19)); d.text((18,13),title,font=fb,fill=accent)
        d.text((W-230,13),f"Top {len(rows)} 异动榜",font=fs,fill=(200,150,110))
        y=76; bw=int((W-360)*r)
        for i,(lab,val,note) in enumerate(rows[:len(rows)]):
            frac=min(r*1.8,(val/maxv)*0.95+r*0.05) if r>0 else 0
            w=int(bw*frac)
            d.rectangle([40,y-16,40+w,y+16],fill=accent)
            d.text((44,y-26),f"{i+1}. {lab}",font=fs,fill=(239,227,214))
            d.text((52+w,y-46+0),f"${val:,.0f}  {note}",font=fsm,fill=(200,150,110))
            y+=58
        frames.append(img)
    imageio.mimsave(out,frames,fps=FPS); return len(frames)

# ---- 风格B: 卡片逐个弹出 (cards) 16:9 ---- 不同动画形式
def style_cards(items, out, title, accent=(80,200,180), bg=(12,16,16), W=1280,H=720,FPS=28,per=0.35):
    fs=_font(23); fb=_font(28)
    frames=[]
    total=len(items)
    for i in range(total+1):
        img=Image.new("RGB",(W,H),bg); d=ImageDraw.Draw(img)
        d.rectangle([0,0,W,58],fill=(18,22,22)); d.text((18,15),title,font=fb,fill=accent)
        x,y=60,110
        for j,it in enumerate(items[:i]):
            w=360;h=110
            d.rounded_rectangle([x,y,x+w,y+h],radius=12,fill=(20,28,28),outline=accent if j==i-1 else (40,60,60),width=2)
            d.text((x+18,y+16),it[0],font=fs,fill=(240,240,240))
            d.text((x+18,y+56),it[1],font=_font(16),fill=(150,190,180))
            x+=w+24
            if x>W-360: x=60;y+=140
        frames.append(img)
        for _ in range(int(per*FPS)): frames.append(img)
    # 停留
    for _ in range(int(1.0*FPS)): frames.append(img)
    imageio.mimsave(out,frames,fps=FPS); return len(frames)

# ---- 风格C: 竖屏(9:16) 报告滚动 (vertical) ---- 不同画幅+时长
def style_vertical(rep_img, out, title, accent=(255,180,70), bg=(10,10,14), W=720,H=1280,FPS=28,dur=12.0):
    fs=_font(20); fb=_font(24)
    ri=rep_img.copy(); sc=(W-60)/ri.width; ri=ri.resize((int(ri.width*sc),int(ri.height*sc)))
    rw,rh=ri.size; tot=max(1,rh-(H-120)); steps=int(dur*FPS); frames=[]
    for k in range(steps):
        top=int((rh-(H-120))*(k/steps) if rh>(H-120) else 0)
        crop=ri.crop((0,top,rw,min(rh,top+(H-120))))
        img=Image.new("RGB",(W,H),bg); img.paste(crop,((W-rw)//2,60))
        d=ImageDraw.Draw(img); d.rectangle([0,0,W,56],fill=(16,16,20)); d.text((16,15),title,font=fs,fill=accent)
        frames.append(img)
    imageio.mimsave(out,frames,fps=FPS); return len(frames)

# ---- 风格D: 分屏 代码+输出 (split) 16:9 ---- 不同形式
def style_split(code_lines, out_img, out, title, accent=(120,160,255), bg=(10,12,18), W=1600,H=900,FPS=28,dur=11.0):
    fs=_font(17); fb=_font(22)
    frames=[]; steps=int(dur*FPS); code_col=[]
    for k in range(steps):
        r=k/steps; n=max(1,int(len(code_lines)*min(1,r*1.4)))
        img=Image.new("RGB",(W,H),bg); d=ImageDraw.Draw(img)
        d.rectangle([0,0,W,54],fill=(14,16,24)); d.text((16,13),title,font=fb,fill=accent)
        d.rectangle([16,66,W//2, H-20],fill=(13,15,22),outline=(50,60,90))
        d.text((28,80),"agent.py",font=_font(16),fill=(150,180,255))
        yy=112
        for ln in code_lines[:n]:
            c=(255,150,120) if ln.strip().startswith("#") else (210,210,220)
            d.text((30,yy),ln[:70],font=fs,fill=c); yy+=26
        # 右: 输出报告图像(fake)
        ri=out_img.copy(); sc=((W//2-40)/ri.width); ri=ri.resize((int(ri.width*sc),int(ri.height*sc)))
        img.paste(ri.crop((0,min(int(ri.height*r),ri.height-400),ri.width,min(ri.height,min((int(ri.height*r))+400,ri.height)))),(W//2+10,80))
        frames.append(img)
    imageio.mimsave(out,frames,fps=FPS); return len(frames)
