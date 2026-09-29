#!/usr/bin/env python3
"""One self-contained HTML page with the film embedded (data URI) + poster, for hosts that take a single page and no video files.
Usage: embed_page.py <film.mp4> <poster.png|jpg> <out.html> --title "..." [--lead "..."] [--link URL --link-text "..."]"""
import argparse, base64, html, mimetypes, os, subprocess, tempfile
ap = argparse.ArgumentParser(); ap.add_argument('film'); ap.add_argument('poster'); ap.add_argument('out')
ap.add_argument('--title', required=True); ap.add_argument('--lead', default=''); ap.add_argument('--link'); ap.add_argument('--link-text', default='Все материалы')
a = ap.parse_args()
with tempfile.NamedTemporaryFile(suffix='.jpg') as t:
    subprocess.run(['ffmpeg', '-loglevel', 'error', '-y', '-i', a.poster, '-vf', 'scale=1280:-2', '-q:v', '5', t.name], check=True)
    poster = base64.b64encode(open(t.name, 'rb').read()).decode()
film = base64.b64encode(open(a.film, 'rb').read()).decode()
e = html.escape
link = f'<p style="margin-top:16px"><a href="{e(a.link)}" target="_blank" rel="noopener">{e(a.link_text)}</a></p>' if a.link else ''
page = f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(a.title)}</title>
<style>:root{{--bg:#f9f9f7;--tx:#0b0b0b;--tx2:#52514e;--acc:#2a78d6}}@media (prefers-color-scheme:dark){{:root{{--bg:#0d0d0d;--tx:#fff;--tx2:#c3c2b7;--acc:#6da7ec}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--tx);font:16px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}}main{{max-width:1100px;margin:0 auto;padding:32px 16px 56px}}
h1{{font-size:28px;margin:0 0 6px}}p{{color:var(--tx2);margin:0 0 18px}}video{{width:100%;border-radius:14px;background:#000;display:block}}a{{color:var(--acc)}}</style></head>
<body><main><h1>{e(a.title)}</h1><p>{e(a.lead)}</p><video controls playsinline preload="metadata" poster="data:image/jpeg;base64,{poster}" src="data:video/mp4;base64,{film}"></video>{link}</main></body></html>'''
open(a.out, 'w', encoding='utf-8').write(page); print(a.out, round(len(page) / 1e6, 2), 'MB')
