"""Build the profile's original SVG artwork. Python standard library only."""
from pathlib import Path
from html import escape
from math import sin, cos, pi

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'profile'
INK, PAPER, MUTED, LINE, LIME = '#101210', '#f1f2e9', '#9ba394', '#30372d', '#d1ff73'

CSS = '''
.orbit{animation:orbit 32s linear infinite;transform-box:fill-box;transform-origin:center}
.float{animation:float 7s ease-in-out infinite}
.flow{stroke-dasharray:12 180;animation:flow 10s linear infinite}
.breathe{animation:breathe 5s ease-in-out infinite}
@keyframes orbit{to{transform:rotate(360deg)}}
@keyframes float{50%{transform:translateY(-9px)}}
@keyframes flow{to{stroke-dashoffset:-384}}
@keyframes breathe{50%{opacity:.45}}
@media(prefers-reduced-motion:reduce){*{animation:none!important}}
'''


def text(x, y, value, size=20, color=PAPER, weight=400, extra=''):
    return f'<text x="{x}" y="{y}" fill="{color}" font-family="Arial,Helvetica,sans-serif" font-size="{size}" font-weight="{weight}" {extra}>{escape(value)}</text>'


def label(x, y, value, color=MUTED, size=13):
    return text(x, y, value, size, color, 400, 'letter-spacing="2"')


def line(x1, y1, x2, y2, color=LINE, extra=''):
    return f'<path d="M{x1} {y1}L{x2} {y2}" stroke="{color}" fill="none" {extra}/>'


def circle(x, y, r, color=LIME, extra=''):
    return f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" {extra}/>'


def svg(name, width, height, title, body, description=''):
    value = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(description or title)}</desc>
<defs>
<radialGradient id="halo"><stop stop-color="#384529" stop-opacity=".7"/><stop offset="1" stop-color="{INK}" stop-opacity="0"/></radialGradient>
<linearGradient id="metal" x1="0" y1="0" x2="1" y2="1"><stop stop-color="{PAPER}"/><stop offset=".5" stop-color="#85966b"/><stop offset="1" stop-color="{LIME}"/></linearGradient>
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#232a20" stroke-width=".65"/></pattern>
<clipPath id="bounds"><rect width="{width}" height="{height}" rx="20"/></clipPath>
</defs><style>{CSS}</style>
<g clip-path="url(#bounds)"><rect width="{width}" height="{height}" fill="{INK}"/>{body}</g>
<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="20" fill="none" stroke="{LINE}"/>
</svg>'''
    (OUT / name).write_text(value + '\n')


def torus(cx, cy, scale=1):
    """A projected wireframe torus: exact geometry, animated as vector artwork."""
    pieces = [f'<g transform="translate({cx} {cy}) scale({scale})">', '<circle r="260" fill="url(#halo)"/>']
    pieces.append('<g class="float">')
    paths = []
    def point(u, v):
        x, y, z = (133 + 48*cos(v))*cos(u), (133 + 48*cos(v))*sin(u), 48*sin(v)
        # Tilt the ring toward the viewer, then rotate the composition.
        yy = y*.51-z*.86
        return x*.90-yy*.43, x*.43+yy*.90
    for v in range(20):
        points = [point(i*2*pi/100, v*2*pi/20) for i in range(101)]
        d = 'M' + 'L'.join(f'{x:.1f} {y:.1f}' for x,y in points) + 'Z'
        paths.append(f'<path d="{d}" fill="none" stroke="url(#metal)" stroke-opacity=".55" stroke-width=".85"/>')
    for u in range(44):
        points = [point(u*2*pi/44, i*2*pi/32) for i in range(33)]
        d = 'M' + 'L'.join(f'{x:.1f} {y:.1f}' for x,y in points) + 'Z'
        paths.append(f'<path d="{d}" fill="none" stroke="url(#metal)" stroke-opacity=".46" stroke-width=".8"/>')
    pieces.extend(paths)
    pieces.append('</g><g class="orbit">')
    pieces.append('<circle r="203" fill="none" stroke="#697656" stroke-width=".8" stroke-dasharray="2 12"/>')
    pieces.append('<circle r="220" fill="none" stroke="#d1ff73" stroke-opacity=".6" stroke-dasharray="160 1222"/>')
    pieces.append(circle(203,0,4)+circle(-203,0,3,PAPER))
    pieces.append('</g>')
    pieces.append(text(0, 13, 'ZM', 39, PAPER, 700, 'text-anchor="middle" letter-spacing="-3"'))
    pieces.append('</g>')
    return ''.join(pieces)


def hero(mobile=False):
    w,h = (600,780) if mobile else (1200,570)
    b = f'<rect x="{0 if mobile else 700}" width="{w}" height="{h}" fill="url(#grid)"/>'
    b += text(36, 49, 'ZM', 23, LIME, 800, 'letter-spacing="-2"')
    b += label(89,47,'ZAIDMOEN / GITHUB',size=12)
    b += line(36,72,w-36,72)
    if mobile:
        b += label(36,119,'SOFTWARE DEVELOPER',LIME,14)
        b += text(30,209,'ZAID',106,PAPER,800,'letter-spacing="-7"')
        b += text(32,282,'MAYYALLEH',69,PAPER,800,'letter-spacing="-4"')
        b += text(36,332,'Thoughtful interfaces. Solid foundations.',21,MUTED)
        b += torus(300,525,.86)
        b += line(36,730,564,730)
        b += label(36,760,'PALESTINE',size=12)+label(347,760,'BUILD / LEARN / REFINE',size=10)
    else:
        b += label(830,47,'CODE. CRAFT. CURIOSITY.',size=12)
        b += label(42,137,'SOFTWARE DEVELOPER',LIME,14)
        b += text(34,260,'ZAID',144,PAPER,800,'letter-spacing="-9"')
        b += text(36,354,'MAYYALLEH',89,PAPER,800,'letter-spacing="-5"')
        b += text(42,412,'Thoughtful interfaces. Solid foundations.',25,MUTED)
        b += torus(930,289,.93)
        b += line(42,505,1158,505)
        b += label(42,542,'BASED IN PALESTINE',size=12)
        b += label(440,542,'FULL-STACK / BACKEND / APPLIED AI',size=12)
        b += label(976,542,'ALWAYS BUILDING',LIME,12)
    svg('hero-mobile.svg' if mobile else 'hero.svg',w,h,'Zaid Mayyalleh — Software developer in Palestine',b,
        'Thoughtful interfaces. Solid foundations. Full-stack development, backend systems and applied AI. A gently moving wireframe orbit surrounds the ZM monogram. Motion respects reduced-motion preferences.')


def cube(x,y,s=30):
    return f'<g transform="translate({x} {y})"><path d="M0 {-s}L{s} {-s/2} 0 0 {-s} {-s/2}Z" fill="#d1ff73"/><path d="M{-s} {-s/2}L0 0V{s}L{-s} {s/2}Z" fill="#667c40"/><path d="M0 0L{s} {-s/2}V{s/2}L0 {s}Z" fill="#a4cb65"/></g>'


def illustration(kind):
    # All illustrations occupy a 330 x 180 viewport.
    b = ''
    if kind == 'voxel':
        for i in range(6):
            b += line(55+i*22,95+i*11,165+i*22,40+i*11,'#323d29')
            b += line(55+i*22,95-i*11,165+i*22,150-i*11,'#323d29')
        b += cube(162,119,27)+cube(216,119,27)+cube(189,105,27)
        b += '<g class="float">'+cube(162,64,27)+'</g>'
        b += '<path d="M243 43h20V23M263 43l-31-31M82 128H62v20" fill="none" stroke="#d1ff73" stroke-width="2"/>'
    elif kind == 'api':
        for x,y,label_ in [(25,58,'API'),(131,58,'AUTH'),(237,58,'SQL')]:
            b += f'<rect x="{x}" y="{y}" width="70" height="64" rx="10" fill="#1c2318" stroke="#617344"/>'
            b += text(x+35,y+37,label_,15,LIME,600,'text-anchor="middle"')
        b += '<path d="M95 90H131M201 90H237M60 124v25H271v-25" fill="none" stroke="#54643f"/>'
        b += '<path class="flow" d="M60 149H272V90H60" fill="none" stroke="#d1ff73" stroke-width="2"/>'
        b += label(101,32,'REQUEST / RESPONSE',size=10)
    elif kind == 'web':
        b += '<g class="float"><rect x="48" y="20" width="240" height="148" rx="10" fill="#1b2118" stroke="#667a4c"/>'
        b += line(48,44,288,44)+circle(62,32,2)+circle(72,32,2,MUTED)+circle(82,32,2,MUTED)
        b += f'<rect x="203" y="58" width="65" height="7" rx="3" fill="{LIME}"/>'
        for yy,ww in [(76,94),(89,126)]:
            b += f'<rect x="{268-ww}" y="{yy}" width="{ww}" height="4" rx="2" fill="#6d7c5e"/>'
        for xx in [67,137,207]:
            b += f'<rect x="{xx}" y="108" width="61" height="42" rx="4" fill="#2c3921"/>'
        b += '</g><path class="flow" d="M48 179H288" stroke="#d1ff73" stroke-width="2"/>'
    elif kind == 'ml':
        for x,ys in [(65,[50,90,130]),(165,[28,70,112,154]),(265,[66,116])]:
            nx,nys=(165,[28,70,112,154]) if x==65 else (265,[66,116])
            if x<265:
                for y in ys:
                    for ny in nys:
                        b+=line(x,y,nx,ny,'#3b4b2d')
        for x,ys in [(65,[50,90,130]),(165,[28,70,112,154]),(265,[66,116])]:
            for y in ys:
                b+=circle(x,y,7,INK,'stroke="#d1ff73" stroke-width="1.5"')
        b+='<path class="flow" d="M65 90L165 70 265 116" stroke="#d1ff73" fill="none" stroke-width="2"/>'
    return b


PROJECTS = [
    ('api','01','Books Management API','BACKEND ENGINEERING','FastAPI / MySQL / JWT','Relational data. Explicit permissions. Raw SQL.'),
    ('voxel','02','Pinch Voxel Studio','COMPUTER VISION','Python / OpenCV / MediaPipe','A gesture-controlled canvas for building in 3D.'),
    ('web','03','Palestine Now','PRODUCT INTERFACE','React / Vite / Tailwind CSS','An Arabic-first web experience, designed in RTL.'),
    ('ml','04','Bank Marketing ML','APPLIED MACHINE LEARNING','Python / scikit-learn / Jupyter','From preprocessing to classification and evaluation.'),
]


def project(spec,mobile=False):
    kind,number,title,category,stack,desc=spec
    w,h=(600,368) if mobile else (1200,242)
    b = label(30,39,number+' / '+category,LIME,12)
    if mobile:
        b += '<g transform="translate(269 26) scale(.87)">'+illustration(kind)+'</g>'
        b += text(30,202,title,33,PAPER,700,'letter-spacing="-1"')
        b += text(30,241,desc,18,MUTED)
        b += line(30,273,570,273)
        b += text(30,313,stack,16,MUTED)
        b += text(538,317,'↗',28,LIME)
    else:
        b += text(30,101,title,42,PAPER,700,'letter-spacing="-1.5"')
        b += text(30,141,desc,21,MUTED)
        b += text(30,205,stack,16,LIME)
        b += '<g transform="translate(805 28)">'+illustration(kind)+'</g>'
        b += text(1142,205,'↗',30,LIME)
    svg(f'project-{kind}'+('-mobile' if mobile else '')+'.svg',w,h,title,b,desc+' '+stack+'. Decorative illustration; not a product screenshot.')


def stack(mobile=False):
    rows=[('01','LANGUAGES','Python / JavaScript / TypeScript / C++ / SQL'),
          ('02','WEB & BACKEND','React / FastAPI / Django / MySQL / Supabase'),
          ('03','AI & WORKFLOW','OpenCV / MediaPipe / scikit-learn / Git')]
    w,h=(600,360) if mobile else (1200,216)
    b=''
    for i,(n,area,tools) in enumerate(rows):
        y=47+i*(112 if mobile else 66)
        b+=label(28,y,n,LIME,12)+label(75,y,area,MUTED,12)
        b+=text(28 if mobile else 340,y+36 if mobile else y,tools,19 if mobile else 22,PAPER)
        if i<2: b+=line(28,y+(58 if mobile else 24),w-28,y+(58 if mobile else 24))
    svg('stack'+('-mobile' if mobile else '')+'.svg',w,h,'Tools I work with',b,
        'Languages: Python, JavaScript, TypeScript, C++, SQL. Web and backend: React, FastAPI, Django, MySQL, Supabase. AI and workflow: OpenCV, MediaPipe, scikit-learn, Git.')


def contact(mobile=False):
    w,h=(600,245) if mobile else (1200,224)
    b=label(30,43,'HAVE SOMETHING WORTH BUILDING?',LIME,12)
    b+=text(28,112 if mobile else 116,"Let's make it happen.",43 if mobile else 66,PAPER,700,'letter-spacing="-2"')
    b+=text(30,167 if mobile else 179,'Internships / Junior roles / Collaboration',20,MUTED)
    b+=text(530 if mobile else 1080,206 if mobile else 139,'↗',45 if mobile else 82,LIME,400,'class="float"')
    svg('connect'+('-mobile' if mobile else '')+'.svg',w,h,"Let's make it happen — contact Zaid",b)


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for mobile in (False,True):
        hero(mobile)
        stack(mobile)
        contact(mobile)
        for item in PROJECTS:
            project(item,mobile)
    print(f'Built {len(list(OUT.glob("*.svg")))} SVG assets in {OUT}')


if __name__=='__main__':
    main()
