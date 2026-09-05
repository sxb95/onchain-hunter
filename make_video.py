#!/usr/bin/env python3
"""OnchainHunter 演示视频: 链上异动榜 柱状动画(风格A bars)."""
import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from demo_lib import style_bars
data = json.load(open("output/analysis.json"))
rows = []
for t in data[:12]:
    sym = (t.get("symbol") or "?")
    rows.append((sym, round(t.get("score", 0)), f"{t.get('change24',0):+.0f}%"))
n = style_bars(rows, "output/demo.mp4", "OnchainHunter · 链上异动榜",
               accent=(255,122,69), dur=9.5)
print("demo.mp4 saved, frames", n)
