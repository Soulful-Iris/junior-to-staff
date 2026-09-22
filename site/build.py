#!/usr/bin/env python3.12
"""Build the reading site from the repo's markdown.

    python3.12 site/build.py            # writes site/out/

Design notes, so the next person does not have to reverse-engineer them:

* The output MIRRORS the repo tree. `tiers/01-junior/06-testing/README.md`
  becomes `tiers/01-junior/06-testing/index.html`. That is not tidiness — it
  means the relative links already in the markdown (`../../../assets/...`,
  `../../02-senior/09-reliability/`) resolve without being rewritten, so there
  is one fewer thing to get silently wrong.
* Only `.md` targets need rewriting, to `.html`.
* Assets are copied rather than inlined, so the SVG animations keep working and
  the browser caches them.
* Everything is static. No server-side rendering, no build step at read time,
  nothing to fall over at 3am.
"""
import json
import os
import re
import shutil
import sys
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site" / "out"

# ---------------------------------------------------------------- content map

TIER_NAMES = {
    "01-junior": ("Junior", "build a thing that works"),
    "02-senior": ("Senior", "build a thing that survives"),
    "03-staff": ("Staff", "change what gets built"),
}
ACT_NAMES = {
    "act-1-junior": ("Act 1", "Junior"),
    "act-2-senior": ("Act 2", "Senior"),
    "act-3-staff": ("Act 3", "Staff"),
}


def first_heading(text: str) -> str:
    m = re.search(r"^#\s+(.+)$", text, re.M)
    return m.group(1).strip() if m else "Untitled"


def summary_of(text: str) -> str:
    """First real paragraph, stripped of markdown, for search and cards."""
    body = re.sub(r"^#.*$", "", text, flags=re.M)
    body = re.sub(r"^>.*$", "", body, flags=re.M)
    body = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", body)
    body = re.sub(r"```.*?```", "", body, flags=re.S)
    for para in body.split("\n\n"):
        p = " ".join(para.split())
        p = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", p)
        p = re.sub(r"[*_`#|]", "", p).strip()
        if len(p) > 60:
            return p
    return ""


def prose_of(text: str) -> str:
    """The page's readable prose, for full-text search.

    Code blocks come out because searching a 105k-word guide for "queue"
    should land you on the paragraph that explains queues, not on the four
    pages that happen to contain `queue_url`. Tables and link targets come
    out for the same reason: they match on syntax, not on meaning.
    """
    t = re.sub(r"```.*?```", " ", text, flags=re.S)
    t = re.sub(r"`[^`]*`", " ", t)
    t = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    t = re.sub(r"^\s*[|+].*$", " ", t, flags=re.M)
    t = re.sub(r"[*_#>]", " ", t)
    return " ".join(t.split())


def collect():
    """Every markdown file we publish, in reading order."""
    pages = []

    pages.append({"src": "README.md", "kind": "home", "title": "junior → staff"})

    for tier in sorted(TIER_NAMES):
        tdir = ROOT / "tiers" / tier
        if not tdir.is_dir():
            continue
        for sec in sorted(p for p in tdir.iterdir() if p.is_dir()):
            rel = f"tiers/{tier}/{sec.name}"
            if (ROOT / rel / "README.md").exists():
                pages.append({"src": f"{rel}/README.md", "kind": "section",
                              "tier": tier, "slug": sec.name})
            if (ROOT / rel / "projects.md").exists():
                pages.append({"src": f"{rel}/projects.md", "kind": "projects",
                              "tier": tier, "slug": sec.name})

    if (ROOT / "acts" / "README.md").exists():
        pages.append({"src": "acts/README.md", "kind": "acts-index"})
    for act in sorted(ACT_NAMES):
        if (ROOT / "acts" / act / "README.md").exists():
            pages.append({"src": f"acts/{act}/README.md", "kind": "act", "slug": act})

    if (ROOT / "projects" / "README.md").exists():
        pages.append({"src": "projects/README.md", "kind": "spine-index"})
    for proj in sorted(p for p in (ROOT / "projects").iterdir() if p.is_dir()):
        if (proj / "README.md").exists():
            pages.append({"src": f"projects/{proj.name}/README.md",
                          "kind": "spine", "slug": proj.name})

    for doc in ["docs/HOW-TO-USE.md", "docs/STYLE.md", "docs/PROJECT-SPEC.md"]:
        if (ROOT / doc).exists():
            pages.append({"src": doc, "kind": "doc"})

    for p in pages:
        text = (ROOT / p["src"]).read_text(encoding="utf-8")
        p["text"] = text
        p.setdefault("title", first_heading(text))
        p["summary"] = summary_of(text)
        p["url"] = url_for(p["src"])
    return pages


def url_for(src: str) -> str:
    if src == "README.md":
        return "/"
    if src.endswith("/README.md"):
        return "/" + src[: -len("README.md")]
    return "/" + src[:-3] + ".html"


# ---------------------------------------------------------------- rendering

MD = markdown.Markdown(extensions=["extra", "toc", "sane_lists"],
                       extension_configs={"toc": {"permalink": False}})


def render_body(text: str) -> tuple[str, list]:
    MD.reset()
    html = MD.convert(text)
    toc = [(t["level"], t["name"], t["id"]) for t in MD.toc_tokens
           for t in [t] ] if hasattr(MD, "toc_tokens") else []
    # flatten one level down as well
    flat = []

    def walk(items):
        for it in items:
            flat.append((it["level"], it["name"], it["id"]))
            walk(it.get("children", []))

    walk(getattr(MD, "toc_tokens", []))
    html = re.sub(r'href="([^"]+)\.md((?:#[^"]*)?)"', r'href="\1.html\2"', html)
    html = html.replace('<table>', '<div class="tablewrap"><table>').replace('</table>', '</table></div>')
    html = re.sub(r'<p>(<img[^>]*>)</p>', r'<div class="figwrap">\1</div>', html)
    return html, flat


# ---------------------------------------------------------------- page shell

CSS = """
@font-face{font-family:"Source Serif 4"; src:url("fonts/source-serif-4-400.woff2") format("woff2");
  font-weight:400; font-style:normal; font-display:swap}
@font-face{font-family:"Source Serif 4"; src:url("fonts/source-serif-4-600.woff2") format("woff2");
  font-weight:600; font-style:normal; font-display:swap}
:root{
  --ground:#e8ece9; --paper:#fcfcfa; --ink:#1b2420; --muted:#5c675f;
  --rule:#d6dcd7; --green:#2f6f4e; --green-tint:#eaf0ec; --warm:#b2632f;
  --measure:66ch;
}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{
  margin:0; background:var(--ground); color:var(--ink);
  font:18px/1.68 "Source Serif 4","Iowan Old Style",Palatino,Georgia,serif;
}
.ui{font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}

a{color:var(--green); text-decoration-thickness:1px; text-underline-offset:2px}
a:hover{color:var(--ink)}
:focus-visible{outline:2px solid var(--warm); outline-offset:2px; border-radius:2px}

/* ---- frame ---- */
.frame{display:grid; grid-template-columns:266px minmax(0,1fr); gap:0; min-height:100vh}
.main{min-width:0}
.sheet{min-width:0}
.col{min-width:0}
.rail{
  position:sticky; top:0; align-self:start; height:100vh; overflow-y:auto;
  padding:26px 18px 60px 26px; border-right:1px solid var(--rule);
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
  font-size:14px; line-height:1.45;
}
.main{padding:0 0 96px}
.sheet{
  background:var(--paper); border-left:1px solid var(--rule);
  border-right:1px solid var(--rule); min-height:100vh;
}
.col{max-width:var(--measure); margin:0 auto; padding:52px 28px 0}

/* ---- rail ---- */
.brand{display:block; font-family:inherit; font-size:15px; font-weight:600;
  color:var(--ink); text-decoration:none; letter-spacing:.01em}
.brand span{color:var(--green)}
.brand small{display:block; font-weight:400; color:var(--muted); font-size:12.5px; margin-top:3px}
.search{margin:18px 0 22px}
.search input{
  width:100%; padding:7px 10px; border:1px solid var(--rule); border-radius:6px;
  background:var(--paper); color:var(--ink); font:inherit; font-size:13.5px;
}
.search input::placeholder{color:#93a09a}
.act{margin:22px 0 6px; font-size:12.5px; color:var(--muted)}
.act b{color:var(--ink); font-weight:600; font-size:13.5px; display:block}
.rail ol{list-style:none; margin:0; padding:0}
.rail li{margin:1px 0}
.rail a.item{
  display:flex; gap:9px; padding:4px 8px; border-radius:5px;
  color:var(--ink); text-decoration:none;
}
.rail a.item:hover{background:var(--green-tint)}
.rail a.item[aria-current]{background:var(--green); color:var(--paper)}
.rail a.item[aria-current] .n{color:#cfe0d5}
.n{color:var(--muted); font-variant-numeric:tabular-nums; min-width:1.6em}
.sub{display:block; margin:0 0 3px 30px}
.sub a{font-size:12.5px; color:var(--muted); text-decoration:none}
.sub a:hover{color:var(--green)}
.rail .ext{margin-top:26px; padding-top:16px; border-top:1px solid var(--rule); font-size:12.5px}
.rail .ext a{display:block; margin:5px 0; color:var(--muted); text-decoration:none}
.rail .ext a:hover{color:var(--green)}

/* ---- content ---- */
.col h1{font-size:34px; line-height:1.18; margin:0 0 6px; letter-spacing:-.012em}
.col h2{font-size:23px; line-height:1.3; margin:44px 0 12px; letter-spacing:-.008em}
.col h3{font-size:19px; margin:34px 0 10px}
.col h4{font-size:17px; margin:26px 0 8px}
.col p, .col li{overflow-wrap:break-word}
.col blockquote{
  margin:14px 0 26px; padding:0 0 0 16px; border-left:2px solid var(--green);
  color:var(--muted); font-size:16px;
}
.col blockquote p{margin:.35em 0}
.figwrap{margin:26px 0; overflow-x:auto; -webkit-overflow-scrolling:touch;
  background:var(--paper); border-radius:9px}
.col img{display:block; width:100%; height:auto; border-radius:9px}
.tablewrap{overflow-x:auto; margin:22px 0; -webkit-overflow-scrolling:touch}
.col table{width:100%; border-collapse:collapse; margin:22px 0; font-size:15.5px;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.col th{text-align:left; font-weight:600; border-bottom:1.5px solid var(--rule); padding:7px 9px}
.col td{border-bottom:1px solid var(--rule); padding:7px 9px; vertical-align:top}
.col tr:last-child td{border-bottom:0}
.col code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace; font-size:.86em;
  background:var(--green-tint); padding:1px 4px; border-radius:3px}
.col pre{background:#20302a; color:#e6ece8; padding:15px 17px; border-radius:8px;
  overflow-x:auto; font-size:14px; line-height:1.55; margin:20px 0}
.col pre code{background:none; padding:0; color:inherit; font-size:14px}
.col hr{border:0; border-top:1px solid var(--rule); margin:40px 0}
.col ul,.col ol{padding-left:22px}
.col li{margin:5px 0}
.col li input[type=checkbox]{margin-right:6px}

.crumb{font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
  font-size:13px; color:var(--muted); margin:0 0 20px}
.crumb a{color:var(--muted); text-decoration:none}
.crumb a:hover{color:var(--green)}

.pair{display:flex; gap:8px; margin:0 0 30px; font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif; font-size:13.5px}
.pair a{padding:5px 11px; border:1px solid var(--rule); border-radius:999px;
  text-decoration:none; color:var(--ink); background:var(--paper)}
.pair a[aria-current]{background:var(--green); color:var(--paper); border-color:var(--green)}

.nextprev{display:flex; justify-content:space-between; gap:14px; margin:64px 0 0;
  padding-top:22px; border-top:1px solid var(--rule);
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif; font-size:14px}
.nextprev a{max-width:48%; text-decoration:none; color:var(--ink)}
.nextprev span{display:block; color:var(--muted); font-size:12.5px; margin-bottom:2px}
.nextprev .r{text-align:right}

/* ---- home ---- */
.hero{padding:44px 28px 0; max-width:880px; margin:0 auto}
.hero h1{font-size:44px; line-height:1.08; margin:0 0 14px; letter-spacing:-.02em}
.hero .lede{font-size:20px; line-height:1.55; color:var(--muted); max-width:34em; margin:0 0 30px}
.hero img{width:100%; height:auto; border-radius:11px; display:block}
.acts{display:grid; grid-template-columns:repeat(auto-fit,minmax(215px,1fr)); gap:14px;
  max-width:880px; margin:34px auto 0; padding:0 28px}
.actcard{background:var(--paper); border:1px solid var(--rule); border-radius:10px;
  padding:17px 18px; text-decoration:none; color:var(--ink); display:block}
.actcard:hover{border-color:var(--green)}
.actcard b{display:block; font-size:17px; margin-bottom:4px}
.actcard span{font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
  font-size:13.5px; color:var(--muted); line-height:1.45; display:block}
.actcard em{font-style:normal; color:var(--green); font-size:12.5px;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif;
  display:block; margin-top:9px}

/* ---- search results ---- */
#results{margin:6px 0 0; display:none}
#results a{display:block; padding:6px 8px; border-radius:5px; text-decoration:none; color:var(--ink)}
#results a:hover,#results a.on{background:var(--green-tint)}
#results a{padding:7px 8px 8px}
#results .t{display:block; font-size:13px}
/* Two lines, because the snippet has to show the words around the match —
   one clipped line would be the same as showing nothing. */
#results .c{display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical;
  overflow:hidden; font-size:11.5px; line-height:1.45; color:var(--muted); margin-top:2px}
#results .c b{font-weight:600; color:var(--green); background:var(--green-tint)}
#results .none{padding:6px 8px; font-size:12.5px; color:var(--muted)}

/* ---- mobile ---- */
.bar{display:none; position:sticky; top:0; z-index:20; background:var(--ground);
  border-bottom:1px solid var(--rule); padding:9px 14px; align-items:center; gap:12px;
  font-family:ui-sans-serif,-apple-system,"Segoe UI",Helvetica,Arial,sans-serif}
.bar button{font:inherit; font-size:14px; background:var(--paper); color:var(--ink);
  border:1px solid var(--rule); border-radius:7px; padding:6px 11px; cursor:pointer}
.bar .here{font-size:14px; color:var(--muted); overflow:hidden; white-space:nowrap;
  text-overflow:ellipsis}

@media (max-width:860px){
  body{font-size:17px}
  .frame{grid-template-columns:minmax(0,1fr)}
  .bar{display:flex}
  .rail{position:fixed; inset:47px 0 0; height:auto; width:100%; background:var(--ground);
    border-right:0; display:none; z-index:19; padding:18px 20px 70px}
  .rail.open{display:block}
  .sheet{border-left:0; border-right:0}
  .col{padding:30px 20px 0}
  .col h1{font-size:28px}
  .col h2{font-size:21px}
  .hero{padding:28px 20px 0}
  .hero h1{font-size:33px}
  .hero .lede{font-size:18px}
  .acts{padding:0 20px}
  .figwrap img{width:auto; max-width:none; min-width:660px}
  .figwrap{border:1px solid var(--rule)}
  .col table{font-size:14px}
  .col th,.col td{padding:6px 7px}
}
@media (prefers-reduced-motion:reduce){*{animation:none !important; transition:none !important}}
"""

# Raw, because this is JavaScript source. Without the r, Python eats the
# backslashes and ships `'\b'` — a backspace character — where the regex needs
# a word boundary, and every search silently returns nothing.
JS = r"""
(function(){
  var q=document.getElementById('q'), r=document.getElementById('results'), idx=null, sel=-1;
  function load(cb){ if(idx){cb();return;}
    fetch(BASE+'search.json').then(function(x){return x.json()}).then(function(d){idx=d;cb()}); }
  function esc(s){return s.replace(/[&<>]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;'}[c]})}
  /* Show the sentence the match sits in, not the page summary. On a guide this
     long the useful answer to "idempotency" is which paragraph says it. */
  function snip(body,t,re){
    var i=-1;
    if(re){ re.lastIndex=0; var m=re.exec(body); if(m) i=m.index; }
    if(i<0) i=body.toLowerCase().indexOf(t);
    if(i<0) return '';
    var a=Math.max(0,i-52), b=Math.min(body.length,i+t.length+92);
    if(a>0){ var sp=body.indexOf(' ',a); if(sp>-1&&sp<i) a=sp+1; }
    return (a>0?'… ':'')+esc(body.slice(a,i))+'<b>'+esc(body.slice(i,i+t.length))+'</b>'+
           esc(body.slice(i+t.length,b))+(b<body.length?' …':'');
  }
  /* Whole-word matches count; substring matches only count for longer queries.
     Without this, "rds" scores 32 pages because it is inside "words" and
     "records", and the two pages actually about RDS are buried. */
  function matcher(t){
    var e=t.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
    var b=/^\w/.test(t)?'\\b':'', a=/\w$/.test(t)?'\\b':'';
    return new RegExp(b+e+a,'gi');
  }
  function count(hay,re){ re.lastIndex=0; var n=0; while(re.exec(hay)!==null){n++; if(n>9)break;} return n; }
  function run(){
    var t=q.value.trim().toLowerCase();
    if(t.length<2){r.style.display='none'; r.innerHTML=''; return;}
    load(function(){
      var hits=[], re=matcher(t), loose=t.length>=5;
      for(var i=0;i<idx.length;i++){
        var p=idx[i], s=0, body=p.b||'';
        if(count(p.t,re)) s+=40; else if(loose&&p.t.toLowerCase().indexOf(t)>-1) s+=20;
        if(count(p.h,re)) s+=16; else if(loose&&p.h.toLowerCase().indexOf(t)>-1) s+=8;
        if(count(p.s,re)) s+=8;
        var n=count(body,re);
        if(!n&&loose) n=Math.min(body.toLowerCase().split(t).length-1,3);
        if(n) s+=Math.min(n,6);
        if(s) hits.push([s,p,n?snip(body,t,re):'']);
      }
      hits.sort(function(a,b){return b[0]-a[0]});
      sel=-1;
      if(!hits.length){ r.innerHTML='<div class="none">Nothing matches that.</div>'; r.style.display='block'; return; }
      r.innerHTML=hits.slice(0,9).map(function(h){
        return '<a href="'+h[1].u+'"><span class="t">'+esc(h[1].t)+'</span>'+
               '<span class="c">'+(h[2]||esc(h[1].s.slice(0,90)))+'</span></a>';
      }).join('');
      r.style.display='block';
    });
  }
  if(q){
    q.addEventListener('input',run);
    q.addEventListener('keydown',function(e){
      var as=r.querySelectorAll('a');
      if(e.key==='ArrowDown'||e.key==='ArrowUp'){
        if(!as.length)return; e.preventDefault();
        if(sel>-1) as[sel].classList.remove('on');
        sel = e.key==='ArrowDown' ? (sel+1)%as.length : (sel<=0?as.length-1:sel-1);
        as[sel].classList.add('on'); as[sel].scrollIntoView({block:'nearest'});
      } else if(e.key==='Enter'&&sel>-1){ e.preventDefault(); as[sel].click(); }
      else if(e.key==='Escape'){ q.value=''; run(); q.blur(); }
    });
    document.addEventListener('keydown',function(e){
      if(e.key==='/'&&document.activeElement!==q){e.preventDefault();q.focus();}
    });
  }
  var btn=document.getElementById('menu'), rail=document.getElementById('rail');
  if(btn) btn.addEventListener('click',function(){
    var open=rail.classList.toggle('open');
    btn.setAttribute('aria-expanded',open?'true':'false');
    btn.textContent=open?'Close':'Contents';
    document.body.style.overflow=open?'hidden':'';
  });
})();
"""


def rail_html(pages, current_url, base):
    by_tier = {}
    for p in pages:
        if p["kind"] == "section":
            by_tier.setdefault(p["tier"], []).append(p)
    proj_for = {p["slug"]: p for p in pages if p["kind"] == "projects"}

    out = [f'<a class="brand" href="{base}">junior <span>&rarr;</span> staff'
           f'<small>an engineering guide, in three acts</small></a>',
           '<div class="search"><label class="sr" for="q"></label>'
           '<input id="q" type="search" placeholder="Search the guide  /" '
           'autocomplete="off" spellcheck="false"><div id="results"></div></div>']

    for tier, items in sorted(by_tier.items()):
        name, tag = TIER_NAMES[tier]
        out.append(f'<div class="act"><b>{name}</b>{tag}</div><ol>')
        for p in items:
            num = p["slug"].split("-")[0]
            label = re.sub(r"^\d+\s*·\s*", "", p["title"])
            cur = ' aria-current="page"' if p["url"] == current_url else ""
            out.append(f'<li><a class="item" href="{base.rstrip("/")}{p["url"]}"{cur}>'
                       f'<span class="n">{num}</span><span>{label}</span></a>')
            pr = proj_for.get(p["slug"])
            if pr:
                c2 = ' style="color:var(--green)"' if pr["url"] == current_url else ""
                out.append(f'<span class="sub"><a href="{base.rstrip("/")}{pr["url"]}"{c2}>'
                           f'five projects</a></span>')
            out.append("</li>")
        out.append("</ol>")

    out.append('<div class="ext">')
    for p in pages:
        if p["kind"] in ("acts-index", "spine-index"):
            out.append(f'<a href="{base.rstrip("/")}{p["url"]}">{p["title"]}</a>')
    for p in pages:
        if p["kind"] == "doc":
            out.append(f'<a href="{base.rstrip("/")}{p["url"]}">{p["title"]}</a>')
    out.append('<a href="https://github.com/Soulful-Iris/junior-to-staff">Source on GitHub</a>')
    out.append("</div>")
    return "\n".join(out)


def shell(page, body, pages, prev, nxt, base, depth):
    up = "../" * depth if depth else ""
    crumb = ""
    if page["kind"] in ("section", "projects"):
        tname, _ = TIER_NAMES[page["tier"]]
        crumb = f'<p class="crumb"><a href="{base}">Guide</a> &nbsp;/&nbsp; {tname}</p>'
    elif page["kind"] in ("act", "acts-index"):
        crumb = f'<p class="crumb"><a href="{base}">Guide</a> &nbsp;/&nbsp; Acts</p>'
    elif page["kind"] in ("spine", "spine-index"):
        crumb = f'<p class="crumb"><a href="{base}">Guide</a> &nbsp;/&nbsp; The spine</p>'
    elif page["kind"] == "doc":
        crumb = f'<p class="crumb"><a href="{base}">Guide</a> &nbsp;/&nbsp; About</p>'

    pair = ""
    if page["kind"] in ("section", "projects"):
        sec = next((p for p in pages if p["kind"] == "section" and p.get("slug") == page["slug"]), None)
        pro = next((p for p in pages if p["kind"] == "projects" and p.get("slug") == page["slug"]), None)
        if sec and pro:
            a = ' aria-current="page"' if page["kind"] == "section" else ""
            b = ' aria-current="page"' if page["kind"] == "projects" else ""
            pair = (f'<nav class="pair"><a href="{base.rstrip("/")}{sec["url"]}"{a}>Read the section</a>'
                    f'<a href="{base.rstrip("/")}{pro["url"]}"{b}>Five projects</a></nav>')

    nav = []
    if prev:
        nav.append(f'<a href="{base.rstrip("/")}{prev["url"]}"><span>Previous</span>{prev["title"]}</a>')
    else:
        nav.append("<span></span>")
    if nxt:
        nav.append(f'<a class="r" href="{base.rstrip("/")}{nxt["url"]}"><span>Next</span>{nxt["title"]}</a>')
    navhtml = f'<nav class="nextprev">{"".join(nav)}</nav>' if (prev or nxt) else ""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{page["title"]} &middot; junior to staff</title>
<meta name="description" content="{page["summary"][:150]}">
<meta name="color-scheme" content="light">
<link rel="stylesheet" href="{up}style.css">
</head>
<body>
<div class="bar ui">
  <button id="menu" aria-expanded="false" aria-controls="rail">Contents</button>
  <span class="here">{page["title"]}</span>
</div>
<div class="frame">
  <nav class="rail" id="rail" aria-label="Guide contents">{rail_html(pages, page["url"], base)}</nav>
  <div class="main">
    <div class="sheet">
      <article class="col">
        {crumb}{pair}
        {body}
        {navhtml}
      </article>
    </div>
  </div>
</div>
<script>var BASE="{base}";</script>
<script src="{up}app.js"></script>
</body>
</html>
"""


def home_shell(page, body, pages, base):
    acts = [p for p in pages if p["kind"] == "act"]
    cards = []
    for a in acts:
        n, tier = ACT_NAMES[a["slug"]]
        _, tag = TIER_NAMES[{"act-1-junior": "01-junior", "act-2-senior": "02-senior",
                             "act-3-staff": "03-staff"}[a["slug"]]]
        count = len([p for p in pages if p["kind"] == "section"
                     and p["tier"] == {"act-1-junior": "01-junior", "act-2-senior": "02-senior",
                                       "act-3-staff": "03-staff"}[a["slug"]]])
        cards.append(f'<a class="actcard" href="{base.rstrip("/")}{a["url"]}">'
                     f'<b>{n} &middot; {tier}</b><span>{tag}</span>'
                     f'<em>{count} sections, five projects</em></a>')

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>junior &rarr; staff</title>
<meta name="description" content="An end-to-end engineering guide for someone who builds by directing an AI and needs to judge what comes back.">
<meta name="color-scheme" content="light">
<link rel="stylesheet" href="style.css">
</head>
<body>
<div class="bar ui">
  <button id="menu" aria-expanded="false" aria-controls="rail">Contents</button>
  <span class="here">junior &rarr; staff</span>
</div>
<div class="frame">
  <nav class="rail" id="rail" aria-label="Guide contents">{rail_html(pages, "/", base)}</nav>
  <div class="main">
    <header class="hero">
      <h1>Knowing what to ask for,<br>and what good looks like.</h1>
      <p class="lede">An engineering guide for someone who builds most of the code by
      directing an AI, and needs to be able to judge what comes back.</p>
      <img src="assets/the-arc.svg" alt="Three tiers and five projects rising in complexity: junior, senior, staff.">
    </header>
    <div class="acts">{"".join(cards)}</div>
    <div class="sheet" style="margin-top:44px">
      <article class="col">{body}</article>
    </div>
  </div>
</div>
<script>var BASE="{base}";</script>
<script src="app.js"></script>
</body>
</html>
"""


def main():
    base = os.environ.get("SITE_BASE", "/")
    pages = collect()

    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    shutil.copytree(ROOT / "assets", OUT / "assets")
    shutil.copytree(ROOT / "site" / "fonts", OUT / "fonts")
    (OUT / "style.css").write_text(CSS, encoding="utf-8")
    (OUT / "app.js").write_text(JS, encoding="utf-8")

    index = []
    for i, p in enumerate(pages):
        body, toc = render_body(p["text"])
        prev = pages[i - 1] if i > 0 else None
        nxt = pages[i + 1] if i < len(pages) - 1 else None

        rel = p["src"][:-3] + ".html"
        if p["src"].endswith("README.md"):
            rel = p["src"][: -len("README.md")] + "index.html"
        dest = OUT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        depth = len(Path(rel).parts) - 1

        if p["kind"] == "home":
            body = re.sub(r"^<h1[^>]*>.*?</h1>\s*", "", body, count=1, flags=re.S)
            body = re.sub(r"<p><img[^>]*the-arc[^>]*></p>\s*", "", body, count=1)
            html = home_shell(p, body, pages, base)
        else:
            html = shell(p, body, pages, prev, nxt, base, depth)
        dest.write_text(html, encoding="utf-8")

        index.append({"t": p["title"], "u": base.rstrip("/") + p["url"],
                      "s": p["summary"][:200],
                      "h": " ".join(n for _, n, _ in toc),
                      "b": prose_of(p["text"])})

    (OUT / "search.json").write_text(json.dumps(index, separators=(",", ":")), encoding="utf-8")
    print(f"built {len(pages)} pages -> {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
