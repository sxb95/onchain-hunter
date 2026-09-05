#!/usr/bin/env python3
"""OnchainHunter 演示视频: 链上异动榜柱状动画(独立实现, 不含外部样式库)."""
import json, os
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio

def F(sz):
    for p in ["/System/Library/Fonts/PingFang.ttc","/System/Library/Fonts/STHeiti Medium.ttc",
              "/System/Library/Fonts/Hiragino Sans GB.ttc","/System/Library/Fonts/Menlo.ttc"]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p, sz)
            except: pass
    return ImageFont.load_default()

W,H,FPS = 1280,720,28
BG=(15,13,13); FG=(239,227,214); ACC=(255,122,69)
f_small, f_big = F(20), F(26)

data = json.load(open("output/analysis.json"))
rows = [( (t.get("sym") or "?"), round(t.get("pts",0)), f"{t.get('chg',0):+.0f}%" ) for t in data[:12]]
maxv = max([v for _,v,_ in rows]+[1])
steps = int(9.5*FPS); frames=[]
for k in range(steps):
    r = k/steps
    img=Image.new("RGB",(W,H),BG); d=ImageDraw.Draw(img)
    d.rectangle([0,0,W,52],fill=(24,19,19)); d.text((18,13),"OnchainHunter · 链上异动榜",font=f_big,fill=ACC)
    d.text((W-230,13),f"Top {len(rows)} 异动榜",font=f_small,fill=(200,150,110))
    y=76; bw=int((W-360)*r)
    for i,(lab,val,note) in enumerate(rows):
        frac=min(r*1.8,(val/maxv)*0.95+r*0.05) if r>0 else 0
        w=int(bw*frac)
        d.rectangle([40,y-16,40+w,y+16],fill=ACC)
        d.text((44,y-26),f"{i+1}. {lab}",font=f_small,fill=FG)
        d.text((52+w,y-46),f"${val:,.0f}  {note}",font=F(14),fill=(200,150,110))
        y+=58
    frames.append(img)
imageio.mimsave("output/demo.mp4",frames,fps=FPS)
print("demo.mp4 saved, frames", len(frames))
