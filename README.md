# OnchainHunter · 链上异动猎手

> 一个基于 **Binance Agent OS** 数据能力搭建的「链上异动/聪明钱」数据分析 Agent。**只读、不碰真实交易。**
> 它像猎手一样扫链上，把"正在异动"的代币、聪明钱标记、风险点捞出来给你看。

## 它干什么

加密市场里真正值得盯的不是大盘，而是**链上正在发生什么**：
- 哪些代币**24h 暴涨/暴跌**（异动）
- 哪些被 **DexScreener 推上 boost / 新上**
- 哪些被 **ChainRadar 标记为 sniper / smart（聪明钱）**
- 哪些**流动性极低、纯属赌博**（风险）

OnchainHunter 把这些捞出来，算一个**异动评分**，输出一份**链上异动榜**。

## 分析逻辑

```
DexScreener (boost榜/新币)  ┐
                            ├─> 取每 token 数据(价格/24h量/流动性/FDV/涨幅/交易数)
ChainRadar 链上信号(sniper/smart) ┘   ─> 异动评分(涨幅 + 量/流动比 + 聪明钱 + 新币标记) ─> report.md
```

异动评分 = 加权：`|24h涨幅| + 成交量/流动性比×15 + 聪明钱标记 +5 + 新币标记 +2`，带四个标记：
- 🔍**聪明钱**（ChainRadar sniper/smart）
- 🔥**异动**（涨幅>20% 或 量/流动比>3）
- 🆕**新币**（创建 <7 天）
- ⚠️**低流动性**（< $50k，风险高）

## 快速开始

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# 网络受限时: export HTTPS_PROXY=http://127.0.0.1:7890
python3 agent.py
# → output/report.md (异动榜) + output/analysis.json (结构化)
```

## 展示

```bash
python3 make_demo.py   # 生成可视化 HTML/PNG
python3 make_video.py  # 生成演示视频 demo.mp4
```

## 目录

```
agent.py         # 主 agent：扫链上→取数据→算异动分→出报告
make_demo.py     # 报告渲染 HTML/PNG
make_video.py    # 演示视频
requirements.txt
```

## 免责声明

本 Agent 输出由程序自动生成，仅供研究速览，**不构成投资建议**。链上新币/低流动性代币风险极高（rug 高发），请自行判断（DYOR）。
