#!/usr/bin/env python3
"""index.html 의 대학 데이터로 검색 유입용 정적 페이지를 만든다.

왜 필요한가: index.html 은 46개 학교가 한 페이지에 들어 있고 내용도 자바스크립트로
그려진다. 그래서 "홍익대 2027 논술 최저" 같은 검색어에 구글이 보여줄 페이지가 없다.
학교마다 주소를 따로 주고, 제목/설명/본문을 HTML에 그대로 박아 넣는다.

  python3 build_seo.py        → u/<학교명>.html 46개 + sitemap.xml + robots.txt
                                 index.html 에 description/canonical/학교 링크 목록 주입

※ 네이버는 외부 사이트를 잘 안 올려준다. 이건 구글용이다.
"""
import re, os, json, html, unicodedata

BASE = 'https://remindlabkr.github.io/remind_univ2027'
SIGNUP = 'https://remind-final-schedule.onrender.com/'
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'index.html')


def load_schools(src):
    """index.html 안의 const D = [...] 를 그대로 읽는다 (데이터를 두 벌 관리하지 않기 위해)."""
    s = open(src, encoding='utf-8').read()
    m = re.search(r'(?m)^\s*const\s+D\s*=\s*(\[)', s)
    i = m.start(1)
    depth, j = 0, i
    while j < len(s):
        if s[j] == '[': depth += 1
        elif s[j] == ']':
            depth -= 1
            if depth == 0: break
        j += 1
    return json.loads(s[i:j + 1]), s


def slug(name):
    """URL에 쓸 이름. 괄호와 공백만 정리하고 한글은 그대로 둔다(검색어와 일치하는 게 유리)."""
    return unicodedata.normalize('NFC', name).replace('(', '-').replace(')', '').replace(' ', '')


def strip_tags(v):
    # 데이터의 <br> 는 항목 구분자다. 그냥 지우면 항목이 붙어버리니 쉼표로 바꾼다.
    t = re.sub(r'<br\s*/?>', ', ', str(v or ''))
    t = re.sub(r'<[^>]+>', ' ', t).replace('&nbsp;', ' ')
    return re.sub(r'\s+', ' ', t).strip()


def row(k, v):
    return f'<tr><th>{html.escape(k)}</th><td>{v}</td></tr>' if v else ''


def page(u):
    n = html.escape(u['n'])
    date = strip_tags(u.get('date')) or '2027 수시 요강 발표 기준 (확인 필요)'
    ex = strip_tags(u.get('ex'))
    desc = f"{u['n']} 2027 수시 논술 전형 정리. 논술 고사일 {date}. 수능 최저 {strip_tags(u.get('mj'))}. 반영비율 {strip_tags(u.get('no'))}. 모집인원과 동점자 처리 기준까지 한눈에."
    desc = re.sub(r'\s+', ' ', desc)[:155]

    dept = ''
    if u.get('dept'):
        rows = ''.join(f"<tr><td>{html.escape(str(d[0]))}</td><td>{d[1]}</td></tr>" for d in u['dept'])
        total = sum(d[1] for d in u['dept'])
        dept = (f'<h2>{n} 2027 인문 논술 학과별 모집인원</h2>'
                f'<table><thead><tr><th>모집단위</th><th>모집인원</th></tr></thead>'
                f'<tbody>{rows}<tr><td><b>합계</b></td><td><b>{total}</b></td></tr></tbody></table>')
    elif u.get('enr'):
        dept = f'<h2>{n} 2027 모집인원</h2><p>{html.escape(strip_tags(u["enr"]))}</p>'

    cta = ''
    if not (u.get('noclass') or u.get('noclassmsg')):
        su = SIGNUP + '?u=' + html.escape(u['n'])
        cta = (f'<div class="cta-wrap">'
               f'<a class="cta cta1" href="{su}">🏫 <b>{n} 수업 신청하러가기</b> (첫 결제 50% 할인) →</a></div>')

    pre = '<p class="pre">🔴 수능 전 논술 실시</p>' if u.get('pre') else ''
    body = ''.join([
        row('논술, 내신 반영', html.escape(strip_tags(u.get('no')))),
        row('수능 최저 (인문)', html.escape(strip_tags(u.get('mn')))),
        row('논술 고사일 (2027)', html.escape(date)),
        row('출제 유형, 고사시간', html.escape(ex)),
        row('2026 → 2027 변경', html.escape(strip_tags(u.get('ch'))) if u.get('ch') not in ('','없음','') else '주요 변경 없음'),
        row('동점자 처리 기준', html.escape(strip_tags(u.get('tie')))),
    ])
    return f'''<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{n} 2027 논술 일정, 수능최저, 모집인원, 리마인드 논술</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{BASE}/u/{slug(u['n'])}.html">
<meta property="og:title" content="{n} 2027 수시 논술 전형 정리">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:type" content="article">
<style>
:root{{--g:#1E7A44;--gd:#12482a;--mut:#7b7b7b}}
*{{box-sizing:border-box}}
body{{margin:0;padding:20px 16px 48px;max-width:720px;margin:0 auto;font:15px/1.75 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo",sans-serif;color:#222;background:#fff}}
h1{{font-size:22px;line-height:1.4;margin:0 0 6px}}
h2{{font-size:17px;margin:26px 0 8px;color:var(--gd)}}
table{{width:100%;border-collapse:collapse;margin:8px 0}}
th,td{{border:1px solid #e3e3e3;padding:9px 10px;text-align:left;font-size:14px;vertical-align:top}}
th{{background:#f6f8f7;width:34%;color:var(--gd);font-weight:700}}
.pre{{color:#D64545;font-weight:800;margin:2px 0 10px}}
.cta-wrap{{display:flex;flex-direction:column;gap:8px;margin:18px 0}}
.cta{{display:block;text-align:center;text-decoration:none;border-radius:12px;padding:14px;font-weight:800;font-size:14px}}
.cta1{{background:var(--g);color:#fff}}
.cta2{{background:#fff;color:var(--gd);border:1.5px solid var(--g)}}
.back{{display:inline-block;margin-top:26px;color:var(--gd);font-weight:700}}
.disc{{color:var(--mut);font-size:12.5px;margin-top:18px;line-height:1.7}}
</style>
</head>
<body>
<h1>{n} 2027 수시 논술 전형 정리</h1>
{pre}
<p>{html.escape(desc)}</p>
{cta}
<h2>{n} 논술 한눈에 보기</h2>
<table><tbody>{body}</tbody></table>
{dept}
<div class="disc">최종 지원 전 {n} 입학처의 2027 수시 모집요강을 반드시 확인하세요. 이 페이지는 리마인드 논술이 정리한 자료이며 오류가 있을 수 있습니다.</div>
<a class="back" href="{BASE}/">← 2027 대입논술 지원 전략집 전체 보기</a>
</body>
</html>
'''


def main():
    schools, src = load_schools(SRC)
    out = os.path.join(HERE, 'u')
    os.makedirs(out, exist_ok=True)
    urls = [f'{BASE}/']
    for u in schools:
        f = os.path.join(out, slug(u['n']) + '.html')
        open(f, 'w', encoding='utf-8').write(page(u))
        urls.append(f"{BASE}/u/{slug(u['n'])}.html")
    print(f'학교 페이지 {len(schools)}개 생성')

    open(os.path.join(HERE, 'sitemap.xml'), 'w', encoding='utf-8').write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + ''.join(f'<url><loc>{html.escape(x)}</loc></url>\n' for x in urls) + '</urlset>\n')
    open(os.path.join(HERE, 'robots.txt'), 'w', encoding='utf-8').write(
        f'User-agent: *\nAllow: /\nSitemap: {BASE}/sitemap.xml\n')
    print('sitemap.xml, robots.txt 생성')

    # index.html: 설명문 + canonical + 학교별 페이지로 가는 링크 목록(구글이 타고 들어갈 통로)
    s = src
    if 'name="description"' not in s:
        s = s.replace('<title>', '<meta name="description" content="2027 대입 논술 46개 대학 정리. 대학별 논술 고사일, 수능 최저학력기준, 반영비율, 모집인원, 동점자 처리 기준을 한눈에. 리마인드 논술.">\n<link rel="canonical" href="' + BASE + '/">\n<title>', 1)
    if 'class="seonav"' not in s:
        links = ' '.join(f'<a href="u/{slug(u["n"])}.html">{html.escape(u["n"])} 논술</a>' for u in schools)
        nav = f'<nav class="seonav"><b>대학별 2027 논술 정리</b><br>{links}</nav>'
        s = s.replace('</body>', nav + '\n</body>', 1)
    open(SRC, 'w', encoding='utf-8').write(s)
    print('index.html 에 description/canonical/학교 링크 주입')


if __name__ == '__main__':
    main()
