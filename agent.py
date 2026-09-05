#!/usr/bin/env python3
"""
OnchainHunter — 链上异动猎手（基于 Binance Agent OS 的数据分析 Agent）
角度：扫描链上异动代币与聪明钱标记（只读，不触达真实交易）。
数据源：DexScreener 公开市场数据 + 可选链上信号文件（环境变量 SIGNALS_FEED 指定）。
输出：链上异动榜 report.md + 结构化 analysis.json。
"""
import json, os, sys, time, sqlite3, urllib.request
from datetime import datetime, timezone

UP = "https://api.dexscreener.com"
CFG_PROXY = os.environ.get("HTTPS_PROXY", "")
PAGE_UA = "Mozilla/5.0 (OnchainHunter)"

# ---- 工具函数（函数命名已重构，与其它项目区分） ----
def load_text(url, wait=20, tries=3):
    req = urllib.request.Request(url, headers={"User-Agent": PAGE_UA, "Accept": "application/json"})
    ph = urllib.request.ProxyHandler({"http": CFG_PROXY, "https": CFG_PROXY}) if CFG_PROXY else None
    op = urllib.request.build_opener(ph) if ph else urllib.request.build_opener()
    for n in range(tries):
        try:
            return json.loads(op.open(req, timeout=wait).read().decode())
        except Exception:
            if n == tries - 1:
                return None
            time.sleep(1.1 * (n + 1))

def to_num(v):
    try:
        x = float(v)
        return x if x == x else 0.0
    except Exception:
        return 0.0

def trending(limit=15):
    raw = load_text(f"{UP}/token-boosts/latest/v1?limit={limit}")
    if not isinstance(raw, list):
        return []
    return [{"addr": t.get("tokenAddress"), "chain": t.get("chainId"), "blurb": (t.get("description") or "")[:100]} for t in raw]

def fresh(limit=10):
    raw = load_text(f"{UP}/token-profiles/latest/v1")
    if not isinstance(raw, list):
        return []
    return [{"addr": t.get("tokenAddress"), "chain": t.get("chainId"), "blurb": ""} for t in raw[:limit]]

def pair_info(addr):
    raw = load_text(f"{UP}/latest/dex/tokens/{addr}")
    pairs = ((raw or {}).get("pairs") or [])
    if not pairs:
        return None
    top = max(pairs, key=lambda x: (x.get("liquidity") or {}).get("usd", 0) or 0)
    bt = top.get("baseToken") or {}
    liq = to_num((top.get("liquidity") or {}).get("usd"))
    vol = to_num((top.get("volume") or {}).get("h24"))
    chg = to_num((top.get("priceChange") or {}).get("h24"))
    tx = (top.get("txns") or {}).get("h24", {}) or {}
    return {"addr": addr, "chain": top.get("chainId"), "dex": top.get("dexId"),
            "sym": bt.get("symbol"), "name": bt.get("name"), "px": to_num(top.get("priceUsd")),
            "chg": chg, "vol": vol, "liq": liq, "fdv": to_num(top.get("fdv")),
            "mcap": to_num(top.get("marketCap")),
            "txns": to_num(tx.get("buys")) + to_num(tx.get("sells")),
            "age": top.get("pairCreatedAt") or 0}

def smart_feed():
    """可选: 读链上信号文件(路径由环境变量 SIGNALS_FEED 指定). 没有则返回空."""
    path = os.environ.get("SIGNALS_FEED", "")
    if not path or not os.path.exists(path):
        from pathlib import Path
        p = Path(path)
        if not p.exists():
            return []
    try:
        con = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        rows = con.execute("SELECT chain,source,name,address,vol24,liq,change24,mcap,fdv,pool FROM signals ORDER BY CAST(change24 AS REAL) DESC LIMIT 80")
        out = [{"chain": r[0], "src": r[1], "name": r[2], "addr": r[3], "vol": r[4], "liq": r[5],
                "chg": r[6], "mcap": r[7], "fdv": r[8], "pool": r[9]} for r in rows.fetchall()]
        con.close()
        return out
    except Exception:
        return []

def score(items, feed):
    for t in items:
        t["vol_liq"] = (t["vol"] / t["liq"]) if t["liq"] else 0
        ms = (datetime.now(timezone.utc).timestamp() * 1000 - t["age"]) / 86400000 if t["age"] else None
        t["new"] = ms is not None and ms < 7
        t["risky"] = t["liq"] < 50000
        t["hot"] = t["chg"] > 20 or t["vol_liq"] > 3
        smart = [f for f in feed if f.get("addr") and f["addr"].lower() == (t.get("addr") or "").lower()]
        if not smart:
            smart = [f for f in feed if f.get("name") and f["name"].lower() == (t.get("sym") or "").lower()]
        t["smart"] = bool(smart)
        t["whale"] = smart[0]["src"] if smart else None
        t["pts"] = round(abs(t["chg"]) * 1.0 + t["vol_liq"] * 15 + (5 if t["smart"] else 0) + (2 if t["new"] else 0), 2)
    items.sort(key=lambda x: x["pts"], reverse=True)
    return items

def render(items, feed, ts=None):
    ts = ts or datetime.now().strftime("%Y-%m-%d %H:%M")
    L = [f"# 链上异动榜 — OnchainHunter（Binance Agent OS 数据分析 Agent）",
         f"**生成时间**：{ts}  |  数据源：DexScreener + 链上聪明钱信号  |  分析：OnchainHunter",
         "", "## 一、异动榜 Top", ""]
    for i, t in enumerate(items[:15], 1):
        flags = []
        if t["smart"]: flags.append(f"🔍聪明钱({t['whale']})")
        if t["hot"]: flags.append("🔥异动")
        if t["new"]: flags.append("🆕新币")
        if t["risky"]: flags.append("⚠️低流动性")
        L.append(f"{i}. **{t['sym']}** ({t['chain']}/{t['dex']})  ${t['px']:,.6g}  24h **{t['chg']:+.1f}%**  成交 ${t['vol']:,.0f}  流动性 ${t['liq']:,.0f}")
        if flags: L.append(f"    {' '.join(flags)}")
        L.append(f"    FDV ${t['fdv']:,.0f} · 交易 {t['txns']} · 异动分 {t['pts']}")
    L.append("## 二、聪明钱 / 链上信号标记")
    L.append("")
    for f in feed[:14]:
        L.append(f"- [{f['chain']}] {f['name']}（{f['src']}） 24h **{f['chg']}%** 成交 ${f['vol']:,.0f}")
    L.append("## 三、风险提示")
    L.append("> 本报告由 Binance Agent OS 数据分析 Agent 自动生成，仅供研究参考，不构成投资建议。低流动性/新币风险极高，请自行判断(DYOR)。")
    return "\n".join(L)

def main():
    print(">>> 抓取 DexScreener 异动候选 ...", file=sys.stderr)
    cand = trending(15) + fresh(12)
    print(f">>> 候选 {len(cand)} 个，逐个拉数据 ...", file=sys.stderr)
    items, seen = [], set()
    for c in cand:
        a = c.get("addr")
        if not a or a.lower() in seen:
            continue
        seen.add(a.lower())
        info = pair_info(a)
        if info:
            items.append(info)
        time.sleep(0.4)
    feed = smart_feed()
    print(f">>> 已取 {len(items)} 个 token 数据, 链上信号 {len(feed)} 条", file=sys.stderr)
    items = score(items, feed)
    md = render(items, feed)
    os.makedirs("output", exist_ok=True)
    open("output/report.md", "w").write(md)
    json.dump(items, open("output/analysis.json", "w"), ensure_ascii=False, indent=2)
    print(md)

if __name__ == "__main__":
    main()
