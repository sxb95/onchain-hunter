#!/usr/bin/env python3
"""#2 OnchainHunter demo: 浅色产品报告·截图滚动(真·产品UI感觉, 非扁平动画)."""
import os
from PIL import Image, ImageDraw, ImageFont
import imageio.v2 as imageio
def F(sz):
    for p in ["/System/Library/Fonts/PingFang.ttc","/System/Library/Fonts/STHeiti Medium.ttc","/System/Library/Fonts/Menlo.ttc"]:
        if os.path.exists(p):
            try: return ImageFont.truetype(p,sz)
            except: pass
    return ImageFont.load_default()
W,H,FPS=1280,720,28
def main():
    rep=Image.open("output/demo.png").convert("RGB")
    sc=(W-90)/rep.width; ri=rep.resize((int(rep.width*sc),int(rep.height*sc)))
    rw,rh=ri.size; frames=[]
    steps=int(9.0*FPS)
    # 顶部页面滚动(产品报告滚动)
    for k in range(steps):
        top=0
        if rh>(H-70):
            top=int((rh-(H-70))*(k/steps))
        crop=ri.crop((0,top,rw,min(rh,top+(H-70))))
        img=Image.new("RGB",(W,H),(245,247,250))
        img.paste(crop,((W-rw)//2,52))
        d=ImageDraw.Draw(img)
        d.rectangle([0,0,W,52],fill=(13,125,216))
        d.text((18,14),"OnchainHunter · 链上异动榜",font=F(22),fill=(255,255,255))
        d.text((W-250,16),"数据分析 Agent",font=F(15),fill=(215,235,255))
        frames.append(img)
    imageio.mimsave("output/demo.mp4",frames,fps=FPS)
    print("demo.mp4 saved, frames",len(frames))
main()
