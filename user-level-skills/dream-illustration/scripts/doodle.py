"""Tiny hand-drawn SVG kit for the Dream Bot Team illustrations."""
import random

INK = "#1d1b3a"
CREAM = "#f7f0df"
VIOLET = "#7c4dff"
PINK = "#ff6fb1"
MINT = "#35d6a0"
SUN = "#ffc933"
SKY = "#7cc8ff"
RED = "#ff5a5f"
GREEN = "#7fd46b"
WHITE = "#ffffff"

W, H = 1360, 768


def head(title):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">
<title>{title}</title>
<defs>
<filter id="wob" x="-5%" y="-5%" width="110%" height="110%"><feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="2" seed="4" result="n"/><feDisplacementMap in="SourceGraphic" in2="n" scale="4.5"/></filter>
<filter id="paper"><feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="2" seed="2"/><feColorMatrix values="0 0 0 0 0.45  0 0 0 0 0.38  0 0 0 0 0.25  0 0 0 0.09 0"/></filter>
<filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="6"/></filter>
<style>
.t{{font-family:'Caveat Brush','Patrick Hand',cursive;fill:{INK}}}
.h{{font-family:'Patrick Hand','Caveat Brush',cursive;fill:{INK}}}
.s{{stroke:{INK};stroke-width:4;stroke-linecap:round;stroke-linejoin:round}}
.f{{fill:none}}
</style>
</defs>
<rect width="{W}" height="{H}" fill="{CREAM}"/>
<rect width="{W}" height="{H}" filter="url(#paper)"/>
'''


def foot():
    return "</svg>\n"


def text(x, y, s, size=40, cls="t", anchor="middle", fill=None, rot=0, extra=""):
    st = f' style="fill:{fill}"' if fill else ""
    tr = f' transform="rotate({rot} {x} {y})"' if rot else ""
    return f'<text x="{x}" y="{y}" class="{cls}" font-size="{size}" text-anchor="{anchor}"{st}{tr} {extra}>{s}</text>'


def underline(x1, x2, y, color=VIOLET, w=7):
    mid = (x1 + x2) / 2
    return f'<path d="M{x1} {y} Q{mid} {y+9} {x2} {y-3}" class="f" stroke="{color}" stroke-width="{w}" stroke-linecap="round" filter="url(#wob)"/>'


def title(s, sub=None, color=VIOLET):
    out = text(W / 2, 96, s, 72)
    tw = len(s) * 30
    out += underline(W / 2 - tw / 2, W / 2 + tw / 2, 118, color)
    # little sparkles
    out += spark(W / 2 - tw / 2 - 40, 70, 16, SUN) + spark(W / 2 + tw / 2 + 40, 72, 16, PINK)
    return out


def caption(s):
    return text(W / 2, H - 42, s, 46, "t", fill=VIOLET)


def spark(x, y, r=14, color=SUN):
    return (f'<path d="M{x} {y-r} L{x+r*0.28} {y-r*0.28} L{x+r} {y} L{x+r*0.28} {y+r*0.28} L{x} {y+r} '
            f'L{x-r*0.28} {y+r*0.28} L{x-r} {y} L{x-r*0.28} {y-r*0.28} Z" fill="{color}" class="s" stroke-width="3" filter="url(#wob)"/>')


def arrow(x1, y1, x2, y2, color=INK, bend=30, w=5):
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - bend
    import math
    ang = math.atan2(y2 - my, x2 - mx)
    a1 = ang + 2.7
    a2 = ang - 2.7
    hx1, hy1 = x2 + 20 * math.cos(a1), y2 + 20 * math.sin(a1)
    hx2, hy2 = x2 + 20 * math.cos(a2), y2 + 20 * math.sin(a2)
    return (f'<g filter="url(#wob)" class="f" stroke="{color}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="M{x1} {y1} Q{mx} {my} {x2} {y2}"/><path d="M{hx1} {hy1} L{x2} {y2} L{hx2} {hy2}"/></g>')


def box(x, y, w, h, fill=WHITE, r=18, stroke=INK, sw=4):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" filter="url(#wob)"/>'


def cloud(cx, cy, w, h, fill=WHITE):
    # thought cloud made of circles
    out = f'<g filter="url(#wob)" fill="{fill}" stroke="{INK}" stroke-width="4">'
    n = 9
    import math
    for i in range(n):
        a = 2 * math.pi * i / n
        out += f'<circle cx="{cx + (w/2-40)*math.cos(a)}" cy="{cy + (h/2-36)*math.sin(a)}" r="{46}"/>'
    out += f'</g><ellipse cx="{cx}" cy="{cy}" rx="{w/2-34}" ry="{h/2-30}" fill="{fill}" />'
    return out


# ---------------------------------------------------------------- characters
def chicken(x, y, s=1.0, flip=False, wing=PINK):
    f = -1 if flip else 1
    return f'''<g transform="translate({x} {y}) scale({f*s} {s})" filter="url(#wob)">
<path d="M-6 26 L-10 42 M8 26 L12 42" class="f s" stroke="{SUN}" stroke-width="5"/>
<path d="M-18 42 L-4 42 M4 42 L20 42" class="f s" stroke="{SUN}" stroke-width="5"/>
<ellipse cx="0" cy="6" rx="30" ry="24" fill="{WHITE}" class="s"/>
<path d="M-22 6 Q-34 -6 -24 -16 Q-12 -8 -14 4 Z" fill="{WHITE}" class="s" stroke-width="3"/>
<path d="M-6 2 Q8 -6 18 6 Q10 18 -6 14 Z" fill="{wing}" class="s" stroke-width="3"/>
<circle cx="22" cy="-18" r="15" fill="{WHITE}" class="s"/>
<path d="M18 -34 Q22 -44 26 -34 Q30 -44 34 -32" fill="{RED}" class="s" stroke-width="3"/>
<path d="M34 -20 L48 -15 L34 -10 Z" fill="{SUN}" class="s" stroke-width="3"/>
<circle cx="26" cy="-21" r="3.5" fill="{INK}"/>
</g>'''


def robot(x, y, s=1.0, color=VIOLET, prop=None, eyes="happy", label=None, lab_color=INK):
    """Robot ~ 120 wide, 190 tall, origin at feet centre."""
    out = f'<g transform="translate({x} {y}) scale({s})">'
    body = f'''<g filter="url(#wob)">
<path d="M-18 -4 L-18 -22 M18 -4 L18 -22" class="f s"/>
<rect x="-30" y="-8" width="26" height="12" rx="6" fill="{INK}" class="s" stroke-width="3"/>
<rect x="4" y="-8" width="26" height="12" rx="6" fill="{INK}" class="s" stroke-width="3"/>
<rect x="-34" y="-82" width="68" height="62" rx="16" fill="{color}" class="s"/>
<rect x="-18" y="-66" width="36" height="22" rx="8" fill="{WHITE}" class="s" stroke-width="3"/>
<path d="M-8 -34 L8 -34" class="f s" stroke="{WHITE}" stroke-width="5"/>
<path d="M-34 -62 Q-56 -60 -56 -40" class="f s"/>
<path d="M34 -62 Q56 -60 56 -40" class="f s"/>
<circle cx="-56" cy="-36" r="9" fill="{WHITE}" class="s" stroke-width="3"/>
<circle cx="56" cy="-36" r="9" fill="{WHITE}" class="s" stroke-width="3"/>
<rect x="-30" y="-154" width="60" height="56" rx="18" fill="{WHITE}" class="s"/>
<path d="M0 -154 L0 -176" class="f s"/>
<circle cx="0" cy="-182" r="8" fill="{SUN}" class="s" stroke-width="3"/>
</g>'''
    # face
    if eyes == "happy":
        face = f'''<g><circle cx="-12" cy="-130" r="7" fill="{INK}"/><circle cx="12" cy="-130" r="7" fill="{INK}"/>
<circle cx="-10" cy="-132" r="2.4" fill="{WHITE}"/><circle cx="14" cy="-132" r="2.4" fill="{WHITE}"/>
<path d="M-12 -112 Q0 -100 12 -112" class="f s" stroke-width="4"/></g>'''
    elif eyes == "focus":
        face = f'''<g><path d="M-19 -134 L-5 -130 M19 -134 L5 -130" class="f s" stroke-width="4"/><circle cx="-12" cy="-126" r="5" fill="{INK}"/><circle cx="12" cy="-126" r="5" fill="{INK}"/>
<path d="M-8 -111 L8 -111" class="f s" stroke-width="4"/></g>'''
    elif eyes == "wow":
        face = f'''<g><circle cx="-12" cy="-130" r="9" fill="{WHITE}" class="s" stroke-width="3"/><circle cx="12" cy="-130" r="9" fill="{WHITE}" class="s" stroke-width="3"/>
<circle cx="-12" cy="-130" r="4" fill="{INK}"/><circle cx="12" cy="-130" r="4" fill="{INK}"/><ellipse cx="0" cy="-110" rx="7" ry="8" fill="{INK}"/></g>'''
    else:
        face = ""
    props = {
        "pencil": f'<g filter="url(#wob)"><path d="M62 -52 L96 -118" class="f s" stroke-width="12"/><path d="M62 -52 L96 -118" class="f" stroke="{SUN}" stroke-width="6"/><path d="M58 -44 L62 -52 L66 -50 Z" fill="{INK}"/></g>',
        "magnifier": f'<g filter="url(#wob)"><circle cx="86" cy="-96" r="22" fill="#d6f1ff" class="s"/><path d="M70 -60 L58 -42" class="f s" stroke-width="8"/></g>',
        "clip": f'<g filter="url(#wob)"><rect x="60" y="-100" width="44" height="58" rx="6" fill="{WHITE}" class="s"/><path d="M70 -86 L94 -86 M70 -74 L94 -74 M70 -62 L86 -62" class="f s" stroke-width="3"/><rect x="72" y="-106" width="20" height="10" rx="3" fill="{SUN}" class="s" stroke-width="3"/></g>',
        "shield": f'<g filter="url(#wob)"><path d="M62 -100 L98 -100 L98 -68 Q98 -48 80 -40 Q62 -48 62 -68 Z" fill="{MINT}" class="s"/><path d="M71 -74 L79 -64 L92 -84" class="f s" stroke-width="5" stroke="{WHITE}"/></g>',
        "wrench": f'<g filter="url(#wob)"><path d="M62 -46 L98 -104" class="f s" stroke-width="10"/><circle cx="100" cy="-108" r="14" fill="{SUN}" class="s"/><path d="M96 -116 L104 -104" class="f s" stroke-width="4"/></g>',
        "bulb": f'<g filter="url(#wob)"><circle cx="84" cy="-104" r="20" fill="{SUN}" class="s"/><rect x="76" y="-86" width="16" height="12" rx="3" fill="{WHITE}" class="s" stroke-width="3"/></g>',
        "ask": f'<g filter="url(#wob)"><circle cx="84" cy="-100" r="24" fill="{PINK}" class="s"/></g>' + text(84, -90, "?", 38, "t", fill=WHITE),
    }
    out += body + face + props.get(prop, "") + "</g>"
    if label:
        out += text(x, y + 38 * s + 16, label, 30, "h", fill=lab_color)
    return out


def kid(x, y, s=1.0):
    return f'''<g transform="translate({x} {y}) scale({s})" filter="url(#wob)">
<path d="M-26 -4 L-26 -34 M26 -4 L26 -34" class="f s"/>
<rect x="-38" y="-8" width="32" height="14" rx="7" fill="{INK}" class="s" stroke-width="3"/>
<rect x="6" y="-8" width="32" height="14" rx="7" fill="{INK}" class="s" stroke-width="3"/>
<path d="M-42 -112 Q-42 -36 -34 -34 L34 -34 Q42 -36 42 -112 Z" fill="{VIOLET}" class="s"/>
<path d="M-12 -112 L-12 -82 M12 -112 L12 -82" class="f s" stroke="{WHITE}" stroke-width="4"/>
<path d="M-42 -100 Q-70 -86 -66 -62" class="f s"/><path d="M42 -100 Q70 -88 70 -66" class="f s"/>
<circle cx="-66" cy="-58" r="9" fill="#ffd9b0" class="s" stroke-width="3"/><circle cx="70" cy="-62" r="9" fill="#ffd9b0" class="s" stroke-width="3"/>
<circle cx="0" cy="-150" r="42" fill="#ffd9b0" class="s"/>
<path d="M-44 -156 Q-40 -200 -6 -196 Q8 -212 30 -194 Q50 -186 44 -156 Q30 -176 8 -170 Q-20 -178 -44 -156 Z" fill="{INK}" class="s" stroke-width="3"/>
<path d="M-44 -150 Q-56 -150 -54 -128 M44 -150 Q56 -150 54 -128" class="f s" stroke-width="7"/>
<rect x="-64" y="-146" width="14" height="26" rx="7" fill="{PINK}" class="s" stroke-width="3"/><rect x="50" y="-146" width="14" height="26" rx="7" fill="{PINK}" class="s" stroke-width="3"/>
<circle cx="-14" cy="-146" r="5" fill="{INK}"/><circle cx="14" cy="-146" r="5" fill="{INK}"/>
<path d="M-12 -128 Q0 -114 12 -128" class="f s" stroke-width="4"/>
</g>'''


def tree(x, y, s=1.0):
    return f'''<g transform="translate({x} {y}) scale({s})" filter="url(#wob)">
<rect x="-7" y="-30" width="14" height="30" fill="#a9733a" class="s" stroke-width="3"/>
<circle cx="0" cy="-58" r="30" fill="{GREEN}" class="s"/><circle cx="-18" cy="-42" r="18" fill="{GREEN}" class="s" stroke-width="3"/><circle cx="18" cy="-44" r="18" fill="{GREEN}" class="s" stroke-width="3"/>
</g>'''


def barn(x, y, s=1.0):
    return f'''<g transform="translate({x} {y}) scale({s})" filter="url(#wob)">
<rect x="-46" y="-62" width="92" height="62" fill="{RED}" class="s"/>
<path d="M-54 -60 L0 -102 L54 -60 Z" fill="#d93f44" class="s"/>
<rect x="-16" y="-38" width="32" height="38" fill="{WHITE}" class="s" stroke-width="3"/>
<path d="M-16 -38 L16 0 M16 -38 L-16 0" class="f s" stroke-width="3"/>
</g>'''


def fence(x, y, w, n=6, s=1.0):
    out = f'<g transform="translate({x} {y}) scale({s})" filter="url(#wob)" class="f s" stroke-width="5">'
    out += f'<path d="M0 -14 L{w} -14 M0 -32 L{w} -32"/>'
    step = w / (n - 1)
    for i in range(n):
        out += f'<path d="M{i*step} 0 L{i*step} -42"/>'
    out += "</g>"
    return out


def farm(x, y, w, h, flock=True, pen=True):
    """Little farm scene inside a rounded green field; everything scales with the width."""
    k = max(0.42, min(1.0, w / 460))
    out = f'<g transform="translate({x} {y})">'
    out += f'<rect x="0" y="0" width="{w}" height="{h}" rx="26" fill="#c8f0a8" stroke="{INK}" stroke-width="4" filter="url(#wob)"/>'
    out += f'<circle cx="{w-50*k-10}" cy="{44*k+14}" r="{24*k}" fill="{SUN}" class="s" stroke-width="3" filter="url(#wob)"/>'
    out += tree(w * 0.09, h - 18, 0.95 * k) + barn(w - 62 * k - 14, h - 14, 0.95 * k)
    if pen:
        out += f'<rect x="{w*0.36}" y="{h*0.36}" width="{w*0.26}" height="{h*0.40}" rx="8" fill="#e7fbd7" stroke="{INK}" stroke-width="4" stroke-dasharray="14 10" filter="url(#wob)"/>'
    if flock:
        cs = 0.8 * k
        out += chicken(w * 0.22, h * 0.62, cs) + chicken(w * 0.27, h * 0.30, cs * 0.9, True) + chicken(w * 0.43, h * 0.62, cs * 0.9) + chicken(w * 0.54, h * 0.55, cs * 0.85, True) + chicken(w * 0.70, h * 0.36, cs * 0.95) + chicken(w * 0.15, h * 0.40, cs * 0.8, True)
    out += "</g>"
    return out


def confetti(seed=3, n=40, x0=0, x1=W, y0=0, y1=H):
    random.seed(seed)
    cols = [VIOLET, PINK, MINT, SUN, SKY]
    out = ""
    for _ in range(n):
        x = random.uniform(x0, x1)
        y = random.uniform(y0, y1)
        c = random.choice(cols)
        k = random.choice(["c", "s", "t"])
        if k == "c":
            out += f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{random.uniform(4,8):.0f}" fill="{c}"/>'
        elif k == "s":
            out += f'<rect x="{x:.0f}" y="{y:.0f}" width="14" height="6" rx="3" fill="{c}" transform="rotate({random.uniform(0,180):.0f} {x:.0f} {y:.0f})"/>'
        else:
            out += f'<path d="M{x:.0f} {y:.0f} l8 14 l-16 0 Z" fill="{c}" transform="rotate({random.uniform(0,180):.0f} {x:.0f} {y:.0f})"/>'
    return out


def pulse(x, y, r=40, color=MINT):
    """Concentric rings suggesting a living, pulsing light."""
    return (f'<circle cx="{x}" cy="{y}" r="{r*1.9}" fill="none" stroke="{color}" stroke-width="3" opacity="0.35"/>'
            f'<circle cx="{x}" cy="{y}" r="{r*1.4}" fill="none" stroke="{color}" stroke-width="4" opacity="0.6"/>'
            f'<circle cx="{x}" cy="{y}" r="{r}" fill="{color}" opacity="0.9" filter="url(#glow)"/>')
