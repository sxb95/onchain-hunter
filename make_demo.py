#!/usr/bin/env python3
import re, html, os
def inline(t):
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    return t
def md_to_html(md):
    lines, out, in_tbl = md.split("\n"), [], False
    for ln in lines:
        s = ln.rstrip()
        if s.startswith("|") and s.endswith("|"):
            cells = [inline(c.strip()) for c in s.strip("|").split("|")]
            if not in_tbl: out.append("<table>"); in_tbl = True
            if all(re.fullmatch(r":?-{2,}:?", html.unescape(c)) for c in cells): continue
            out.append("<tr>" + "".join(f"<td>{c}</td>" for c in cells) + "</tr>"); continue
        if in_tbl: out.append("</table>"); in_tbl = False
        if s.startswith("### "): out.append(f"<h3>{inline(s[4:])}</h3>")
        elif s.startswith("## "): out.append(f"<h2>{inline(s[3:])}</h2>")
        elif s.startswith("# "): out.append(f"<h1>{inline(s[2:])}</h1>")
        elif s.startswith("> "): out.append(f"<blockquote>{inline(s[2:])}</blockquote>")
        elif s == "": out.append("")
        else: out.append(f"<p>{inline(s)}</p>")
    if in_tbl: out.append("</table>")
    return "\n".join(out)
md = open("output/report.md").read()
css = "*{box-sizing:border-box}body{margin:0;font-family:-apple-system,'Helvetica Neue',sans-serif;background:#f5f7fa;color:#1c2733;padding:28px}.wrap{max-width:960px;margin:auto;background:#ffffff;border:1px solid #e3e8ef;border-radius:16px;padding:30px;box-shadow:0 4px 20px rgba(0,0,0,.06)}h1{color:#0d7dd8;font-size:22px;border-bottom:2px solid #e3e8ef;padding-bottom:12px}h2{color:#0d7dd8;font-size:16px;margin-top:24px;border-left:4px solid #0d7dd8;padding-left:10px}h3{color:#16a3b8}blockquote{border-left:3px solid #0d7dd8;margin:14px 0;padding:8px 14px;background:#f0f6fc;color:#3a4a5a;font-size:12px}table{width:100%;border-collapse:collapse;font-size:12.5px;margin:12px 0}td,th{border:1px solid #e3e8ef;padding:7px 10px;text-align:left}thead th{background:#f0f6fc}tr:nth-child(even){background:#fafbfd}p{font-size:13.5px;color:#2b3a4a}"
open("output/demo.html","w").write(f"<!doctype html><html><head><meta charset=utf-8><style>{css}</style></head><body><div class='wrap'>{md_to_html(md)}</div></body></html>")
print("demo.html size:", os.path.getsize("output/demo.html"))
