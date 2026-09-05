#!/usr/bin/env python3
"""
OnchainHunter — 链上异动猎手 (Binance Agent OS 数据分析 Agent)。
角度：链上异动 / 聪明钱监控（只读，不碰真实交易）。
数据源：DexScreener 公开 API（boost 榜/新币/token 数据）+ ChainRadar 链上信号(sniper/smart)。
输出：链上异动榜报告 report.md + 结构化 analysis.json。
"""
import json, os, sys, time, sqlite3, urllib.request
from datetime import datetime, timezone

DS = "https://api.dexscreener.com"
PROXY = os.environ.get("HTTPS_PROXY", "")
UA = "Mozilla/5.0 (OnchainHunter/Binance Agent OS)"
CACHE = "output/cache.json"

def http_get(url, timeout=20, retry=3):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    ph = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}) if PROXY else None
    op = urllib.request.build_opener(ph) if ph else urllib.request.build_opener()
    for a in range(retry):
        try:
            return json.loads(op.open(req, timeout=timeout).read().decode())
        except Exception as e:
            if a == retry - 1:
                return None
            time.sleep(1.2 * (a + 1))

def boost_tokens(limit=15):
    d = http_get(f"{DS}/token-boosts/latest/v1?limit={limit}")
    if not isinstance(d, list): return []
    out = []
    for t in d:
        out.append({"address": t.get("tokenAddress"), "chainId": t.get("chainId"),
                    "description": (t.get("description") or "")[:120], "boost": True})
    return out

def new_tokens(limit=10):
    d = http_get(f"{DS}/token-profiles/latest/v1")
    if not isinstance(d, list): return []
    out = []
    for t in d[:limit]:
        out.append({"address": t.get("tokenAddress"), "chainId": t.get("chainId"),
                    "description": "", "boost": False})
    return out

def _f(v):
    try:
        x = float(v)
        return x if x == x else 0.0  # 过滤 NaN
    except Exception:
        return 0.0

def token_data(address):
    d = http_get(f"{DS}/latest/dex/tokens/{address}")
    pairs = ((d or {}).get("pairs") or [])
    if not pairs: return None
    # 选流动性最大的 pair
    p = max(pairs, key=lambda x: (x.get("liquidity") or {}).get("usd", 0) or 0)
    bt = p.get("baseToken") or {}
    liq = (p.get("liquidity") or {}).get("usd", 0) or 0
    vol = (p.get("volume") or {}).get("h24", 0) or 0
    pc = (p.get("priceChange") or {}).get("h24", 0) or 0
    tx = (p.get("txns") or {}).get("h24", {}) or {}
    return {
        "address": address, "chainId": p.get("chainId"), "dexId": p.get("dexId"),
        "symbol": bt.get("symbol"), "name": bt.get("name"),
        "priceUsd": _f(p.get("priceUsd")), "change24": _f(p.get("priceChange", {}).get("h24")),
        "vol24": vol, "liq": liq, "fdv": (p.get("fdv") or 0),
        "mcap": (p.get("marketCap") or 0),
        "txns24": (tx.get("buys", 0) or 0) + (tx.get("sells", 0) or 0),
        "created": (p.get("pairCreatedAt") or 0),
    }

def load_chain_signals():
    """读 ChainRadar 链上信号库(若存在): 返回 按地址/名称 的 smart/sniper 标记。"""
    db = os.path.expanduser("~/chainradar/data/signals.db")
    if not os.path.exists(db): return []
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        rows = con.execute("SELECT chain,source,name,address,vol24,liq,change24,mcap,fdv,pool FROM signals ORDER BY CAST(change24 AS REAL) DESC LIMIT 60")
        out = [{"chain": r[0], "source": r[1], "name": r[2], "address": r[3],
                "vol24": r[4], "liq": r[5], "change24": r[6], "mcap": r[7], "fdv": r[8], "pool": r[9]}
               for r in rows.fetchall()]
        con.close()
        return out
    except Exception:
        return []

def analyze(tokens, chain):
    """计算异动评分与标记。"""
    for t in tokens:
        t["vol_liq"] = (t["vol24"] / t["liq"]) if t["liq"] else 0
        t["age_days"] = (datetime.now(timezone.utc).timestamp()*1000 - t["created"]) / 86400000 if t["created"] else None
        # 标记
        smart = [c for c in chain if c.get("address") and c["address"].lower() == (t.get("address") or "").lower()]
        if not smart:
            smart = [c for c in chain if c.get("name") and c["name"].lower() == (t.get("symbol") or "").lower()]
        t["smart"] = True if smart else False
        t["src"] = smart[0]["source"] if smart else None
        t["new"] = t["age_days"] is not None and t["age_days"] < 7
        t["risk"] = t["liq"] < 50000
        t["hot"] = t["change24"] > 20 or t["vol_liq"] > 3
        # 异动评分
        score = abs(t["change24"]) * 1.0 + t["vol_liq"] * 15 + (5 if t["smart"] else 0) + (2 if t["new"] else 0)
        t["score"] = round(score, 2)
    tokens.sort(key=lambda x: x["score"], reverse=True)
    return tokens

def build_report(tokens, chain_src, ts=None):
    ts = ts or datetime.now().strftime("%Y-%m-%d %H:%M")
    L = [f"# 链上异动榜 — OnchainHunter（Binance Agent OS 数据分析 Agent）",
         f"**生成时间**：{ts}  |  数据源：DexScreener + 链上信号(sniper/smart)  |  分析：OnchainHunter",
         "", "## 一、异动榜 Top", ""]
    for i, t in enumerate(tokens[:15], 1):
        flags = []
        if t["smart"]: flags.append(f"🔍聪明钱({t['src']})")
        if t["hot"]: flags.append("🔥异动")
        if t["new"]: flags.append("🆕新币")
        if t["risk"]: flags.append("⚠️低流动性")
        L.append(f"{i}. **{t['symbol']}** ({t['chainId']}/{t['dexId']})  ${t['priceUsd']:,.6g}  "
                 f"24h **{t['change24']:+.1f}%**  成交 ${t['vol24']:,.0f}  流动性 ${t['liq']:,.0f}")
        if flags: L.append(f"    {' '.join(flags)}")
        L.append(f"    FDV ${t['fdv']:,.0f} · 交易 {t['txns24']} · 异动分 {t['score']}")
    L.append("## 二、聪明钱 / 链上信号标记 (ChainRadar)"); L.append("")
    for c in chain_src[:12]:
        L.append(f"- [{c['chain']}] {c['name']}（{c['source']}） 24h **{c['change24']}%** 成交 ${c['vol24']:,.0f}")
    L.append("## 三、风险提示")
    L.append("> 本报告由 Binance Agent OS 数据分析 Agent 自动生成，仅供研究参考，不构成投资建议。低流动性/新币风险极高，请自行判断(DYOR)。")
    return "\n".join(L)

def main():
    print(">>> 拉取 DexScreener 异动候选 ...", file=sys.stderr)
    cand = boost_tokens(15) + new_tokens(12)
    print(f">>> 候选 {len(cand)} 个, 抓取每个 token 数据 ...", file=sys.stderr)
    tokens, seen = [], set()
    for c in cand:
        a = c.get("address")
        if not a or a.lower() in seen: continue
        seen.add(a.lower())
        d = token_data(a)
        if d: tokens.append(d)
        time.sleep(0.4)
    print(f">>> 成功取到 {len(tokens)} 个 token 数据", file=sys.stderr)
    chain = load_chain_signals()
    print(f">>> 链上信号 {len(chain)} 条", file=sys.stderr)
    tokens = analyze(tokens, chain)
    report = build_report(tokens, chain)
    os.makedirs("output", exist_ok=True)
    open("output/report.md", "w").write(report)
    json.dump(tokens, open("output/analysis.json", "w"), ensure_ascii=False, indent=2)
    print(report)

if __name__ == "__main__":
    main()
