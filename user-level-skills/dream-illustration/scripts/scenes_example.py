import os
from doodle import *


def s1_hero():
    o = head("Tell it your dream. Watch a team build it.")
    o += confetti(5, 36)
    o += title("TELL IT YOUR DREAM")
    # kid + dream cloud
    o += kid(190, 640, 1.35)
    o += f'<circle cx="300" cy="420" r="12" fill="{WHITE}" class="s" stroke-width="3"/><circle cx="340" cy="370" r="18" fill="{WHITE}" class="s" stroke-width="3"/>'
    o += cloud(470, 280, 330, 230)
    o += farm(335, 190, 270, 190)
    o += text(470, 428, "my map!", 34, "h", fill=VIOLET, rot=-3)
    # arrow to team
    o += arrow(640, 300, 760, 300, VIOLET, 40, 7)
    # robot team
    cols = [VIOLET, PINK, MINT, SUN, SKY]
    props = ["pencil", "magnifier", "clip", "shield", "wrench"]
    xs = [800, 880, 960, 1040, 1120]
    for i in range(5):
        o += robot(xs[i], 540 + (i % 2) * 24, 0.62, cols[i], props[i], "focus" if i % 2 == 0 else "happy")
    o += text(960, 625, "22 little specialists", 38, "h", fill=INK)
    # result
    o += farm(840, 160, 400, 230)
    o += text(1120, 148, "PLAYABLE!", 44, "t", fill=PINK, rot=3)
    o += spark(1262, 170, 20, SUN) + spark(820, 395, 14, MINT)
    o += caption("...and watch it come alive.")
    return o + foot()


def s2_team():
    o = head("Meet your Dream Team")
    o += title("MEET YOUR DREAM TEAM", color=PINK)
    people = [
        (VIOLET, "pencil", "happy", "writes the code"),
        (PINK, "magnifier", "focus", "tries to break it"),
        (SKY, "magnifier", "focus", "...and so does she"),
        (SUN, "clip", "happy", "keeps the plan"),
        (MINT, "shield", "happy", "guards the rules"),
        (VIOLET, "wrench", "happy", "knows every tool"),
    ]
    xs = [150, 360, 570, 780, 990, 1200]
    for i, (c, p, e, lab) in enumerate(people):
        o += robot(xs[i], 430, 1.05, c, p, e)
        o += text(xs[i], 500, lab, 32, "h")
    # you
    o += robot(420, 640, 0.62, PINK, "ask", "wow")
    o += text(500, 610, "and when in doubt, it asks YOU", 46, "t", anchor="start", fill=VIOLET)
    o += arrow(1000, 650, 745, 676, VIOLET, 20, 5) if False else ""
    o += spark(70, 190, 16, SUN) + spark(1290, 200, 16, MINT)
    o += caption("One job each. Nothing slips through.")
    return o + foot()


def s3_alive():
    o = head("A system that breathes")
    o += title("A SYSTEM THAT BREATHES", color=MINT)
    # monitor
    o += box(180, 160, 1000, 470, fill="#241f4d", r=26, sw=6)
    o += f'<rect x="206" y="186" width="948" height="418" rx="14" fill="#2f2960"/>'
    # step arrows
    steps = ["Idea", "Spec", "Genre", "Plan", "Build", "Audit", "Deliver"]
    done = 4
    o += pulse(232 + done * 128 + 62, 236, 30, SUN)
    for i, s in enumerate(steps):
        x = 232 + i * 128
        col = MINT if i < done else (SUN if i == done else "#4b4580")
        o += f'<path d="M{x} 206 L{x+104} 206 L{x+124} 236 L{x+104} 266 L{x} 266 L{x+20} 236 Z" fill="{col}" stroke="{INK}" stroke-width="4" filter="url(#wob)"/>'
        o += text(x + 62, 245, s, 24, "h", fill=INK if i <= done else WHITE)
    # agents row with pulsing lights
    cols = [VIOLET, PINK, SKY, SUN, MINT, VIOLET]
    for i in range(6):
        cx = 300 + i * 150
        o += pulse(cx, 420, 34, MINT if i != 2 else SUN)
        o += f'<g transform="translate({cx} 470) scale(0.42)">{robot(0,0,1,cols[i],None,"happy")}</g>'
    o += f'<rect x="230" y="545" width="900" height="26" rx="13" fill="#4b4580"/><rect x="230" y="545" width="610" height="26" rx="13" fill="{MINT}"/>'
    o += text(1060, 566, "68%", 26, "h", fill=WHITE)
    # stand
    o += f'<path d="M620 630 L600 700 L760 700 L740 630" fill="#3c3670" class="s" filter="url(#wob)"/>'
    o += f'<path d="M230 330 L560 330 L590 290 L630 372 L665 306 L690 330 L1130 330" fill="none" style="stroke:{PINK};stroke-width:6;stroke-linecap:round;stroke-linejoin:round" filter="url(#wob)"/>'
    o += caption("You can SEE it working. That is why you can trust it.")
    return o + foot()


def s4_proof():
    o = head("Do not believe us. Watch.")
    o += confetti(9, 30)
    o += title("DON'T BELIEVE US. WATCH.", color=VIOLET)
    # terminal
    o += box(70, 210, 380, 190, fill=INK, r=20, sw=5)
    o += f'<circle cx="100" cy="238" r="7" fill="{RED}"/><circle cx="124" cy="238" r="7" fill="{SUN}"/><circle cx="148" cy="238" r="7" fill="{MINT}"/>'
    o += text(100, 320, "&gt; /demo --auto", 44, "h", anchor="start", fill=MINT)
    o += f'<rect x="100" y="340" width="26" height="8" fill="{MINT}"/>'
    o += arrow(460, 310, 560, 310, VIOLET, 30, 7)
    # game screen
    o += box(570, 150, 740, 470, fill="#2f2960", r=26, sw=6)
    o += farm(594, 196, 692, 394)
    # HUD
    o += box(616, 168, 130, 52, fill=WHITE, r=14, sw=4)
    o += text(681, 206, "SCORE 7", 32, "h")
    o += box(1136, 168, 130, 52, fill=SUN, r=14, sw=4)
    o += text(1201, 206, "0:30", 34, "h")
    # winner banner
    o += f'<g transform="rotate(-3 940 470)">' + box(760, 440, 360, 74, fill=PINK, r=20, sw=5) + text(940, 490, "THE WINNER IS: YOU!", 40, "t", fill=WHITE) + "</g>"
    o += spark(1280, 150, 22, SUN) + spark(580, 610, 16, MINT)
    # tiny robots cheering
    o += robot(140, 600, 0.6, MINT, None, "wow") + robot(290, 612, 0.52, PINK, None, "happy")
    o += text(250, 655, "zero lines of code written by you", 32, "h")
    o += caption("A game appears. You just watched it happen.")
    return o + foot()


def s5_grow():
    o = head("It grows with you")
    o += title("IT GROWS WITH YOU", color=SUN)
    o += farm(80, 520, 200, 110)
    o += farm(420, 490, 280, 150)
    o += farm(840, 440, 400, 200)
    o += robot(180, 522, 0.5, VIOLET, "pencil", "happy")
    o += robot(560, 492, 0.78, PINK, "clip", "happy")
    o += robot(1040, 442, 1.0, MINT, "bulb", "wow")
    for i, l in enumerate(["map 1", "map 2", "map 3"]):
        o += text([180, 560, 1040][i], 672, l, 34, "h", fill=VIOLET)
    for bx, by in [(300, 360), (700, 300), (770, 240), (1190, 270), (1250, 340), (1130, 190)]:
        o += f'<g filter="url(#wob)"><circle cx="{bx}" cy="{by}" r="22" fill="{SUN}" class="s"/><rect x="{bx-9}" y="{by+20}" width="18" height="12" rx="3" fill="{WHITE}" class="s" stroke-width="3"/></g>'
        o += f'<path d="M{bx-34} {by-30} L{bx-44} {by-40} M{bx+34} {by-30} L{bx+44} {by-40} M{bx} {by-34} L{bx} {by-48}" class="f s" style="stroke:{SUN}" stroke-width="4"/>'
    o += text(700, 190, "every map = new lessons", 40, "h", fill=INK)
    o += caption("Every map makes the team smarter. Day after day.")
    return o + foot()


def s6_ladder():
    o = head("From a prompt to a system that learns")
    o += title("FOUR STEPS TO MAGIC", color=PINK)
    steps = [("1", "PROMPT", "one try", SKY), ("2", "LOOP", "try, check, retry", MINT), ("3", "HARNESS", "the system around it", SUN), ("4", "IT LEARNS", "mistakes never come back", PINK)]
    base = 640
    for i, (n, t, sub, c) in enumerate(steps):
        x = 110 + i * 300
        h = 110 + i * 100
        o += f'<rect x="{x}" y="{base-h}" width="270" height="{h}" rx="10" fill="{c}" stroke="{INK}" stroke-width="5" filter="url(#wob)"/>'
        o += text(x + 135, base - h + 56, f"{n}. {t}", 44, "t")
        o += text(x + 135, base - h + 96, sub, 26, "h")
    o += robot(220, base - 110 - 10, 0.5, VIOLET, "pencil", "happy")
    o += robot(520, base - 210 - 10, 0.5, VIOLET, "magnifier", "focus")
    o += robot(820, base - 310 - 10, 0.5, VIOLET, "wrench", "happy")
    o += robot(1120, base - 410 - 10, 0.5, VIOLET, "bulb", "wow")
    o += arrow(250, 440, 480, 360, INK, 40, 5) if False else ""
    o += spark(1250, 140, 22, SUN) + spark(1180, 190, 12, PINK)
    o += text(680, 690, "Don't polish the prompt. Build the system.", 42, "t", fill=VIOLET)
    return o + foot()


SCENES = {
    "01-tell-it-your-dream": s1_hero,
    "02-meet-your-dream-team": s2_team,
    "03-a-system-that-breathes": s3_alive,
    "04-dont-believe-us-watch": s4_proof,
    "05-it-grows-with-you": s5_grow,
    "06-four-steps-to-magic": s6_ladder,
}



def paper(x, y, w=150, h=190, lines=5, title=None, color=WHITE, check=None):
    o = f'<g transform="translate({x} {y})" filter="url(#wob)"><rect x="0" y="0" width="{w}" height="{h}" rx="10" fill="{color}" class="s"/>'
    if title:
        o += f'</g>' + text(x + w / 2, y + 36, title, 28, "t") + f'<g transform="translate({x} {y})" filter="url(#wob)">'
    for i in range(lines):
        yy = 62 + i * 26
        if check is not None:
            on = i < check
            o += f'<rect x="16" y="{yy-14}" width="18" height="18" rx="4" fill="{WHITE}" class="s" stroke-width="3"/>'
            if on:
                o += f'<path d="M19 {yy-5} L25 {yy+1} L33 {yy-12}" class="f s" style="stroke:{MINT}" stroke-width="4"/>'
            o += f'<path d="M44 {yy-4} L{w-16} {yy-4}" class="f s" stroke-width="3"/>'
        else:
            o += f'<path d="M16 {yy-4} L{w-16-(i%3)*14} {yy-4}" class="f s" stroke-width="3"/>'
    return o + "</g>"


def s7_files():
    o = head("Files are the interface")
    o += title("EVERYTHING IS A FILE", color=SKY)
    names = [("the plan", VIOLET), ("the decisions", PINK), ("the lessons", MINT)]
    for i, (n, c) in enumerate(names):
        o += paper(470 + i * 180, 230, 150, 200, 4, None, WHITE)
        o += f'<rect x="{470+i*180+30}" y="214" width="90" height="24" rx="8" fill="{c}" class="s" filter="url(#wob)"/>'
        o += text(470 + i * 180 + 75, 470, n, 30, "h")
    o += robot(200, 520, 1.15, VIOLET, "pencil", "focus")
    o += kid(1190, 540, 1.1)
    o += arrow(330, 330, 450, 330, VIOLET, 20, 6)
    o += arrow(1020, 330, 900, 330, PINK, 20, 6)
    o += text(200, 590, "the team reads and writes", 32, "h")
    o += text(1190, 590, "you read the very same ones", 32, "h")
    o += text(680, 590, "no hidden memory, no secret database", 36, "t", fill=INK)
    o += caption("What the team knows, you can open.")
    return o + foot()


def s8_proof():
    o = head("Only the editor proves it")
    o += title("\"DONE\" IS NOT PROOF", color=MINT)
    o += robot(230, 520, 1.15, PINK, None, "happy")
    o += f'<g transform="rotate(-4 330 250)">' + box(300, 190, 150, 70, fill=WHITE, r=22, sw=4) + text(375, 238, "Done!", 40, "t") + "</g>"
    o += arrow(470, 300, 640, 300, INK, 10, 6)
    # gate with three checks
    o += box(650, 190, 380, 340, fill=WHITE, r=26, sw=6)
    o += text(840, 240, "THE EDITOR CHECKS", 34, "t", fill=VIOLET)
    for i, l in enumerate(["it builds clean", "every device is linked", "I read it back myself"]):
        yy = 300 + i * 70
        o += f'<rect x="690" y="{yy-26}" width="38" height="38" rx="8" fill="{WHITE}" class="s" filter="url(#wob)"/><path d="M696 {yy-6} L708 {yy+6} L724 {yy-22}" class="f s" style="stroke:{MINT}" stroke-width="7" filter="url(#wob)"/>'
        o += text(750, yy + 6, l, 32, "h", anchor="start")
    o += arrow(1050, 360, 1170, 360, INK, 10, 6)
    # stamp
    o += f'<g transform="rotate(-8 1230 330)"><circle cx="1230" cy="330" r="86" fill="none" style="stroke:{MINT}" stroke-width="8" filter="url(#wob)"/><circle cx="1230" cy="330" r="68" fill="none" style="stroke:{MINT}" stroke-width="3"/>' + text(1230, 322, "PROVEN", 40, "t", fill=MINT) + text(1230, 360, "by the editor", 24, "h", fill=MINT) + "</g>"
    o += caption("The team says it. The editor proves it.")
    return o + foot()


def s9_you():
    o = head("You hold the key")
    o += title("YOU STAY IN CHARGE", color=PINK)
    steps = [("READ", "the team does it alone", MINT), ("CHANGE", "it shows you what it did", SKY), ("PUBLISH", "only with your yes", SUN), ("DELETE", "never. it parks it", PINK)]
    for i, (t_, s_, c) in enumerate(steps):
        x = 90 + i * 300
        h = 120 + i * 70
        o += f'<rect x="{x}" y="{600-h}" width="250" height="{h}" rx="10" fill="{c}" class="s" filter="url(#wob)"/>'
        o += text(x + 125, 600 - h + 50, t_, 40, "t") + text(x + 125, 600 - h + 86, s_, 24, "h")
    o += f'<g filter="url(#wob)"><rect x="880" y="200" width="60" height="50" rx="10" fill="{SUN}" class="s"/><path d="M892 200 Q892 160 910 160 Q928 160 928 200" class="f s"/></g>'
    o += robot(160, 480, 0.55, VIOLET, None, "happy") + robot(460, 410, 0.55, VIOLET, "pencil", "happy") + robot(760, 340, 0.55, VIOLET, "clip", "focus")
    o += kid(1130, 165, 0.7)
    o += text(1115, 235, "only YOU tick the box", 30, "h", fill=VIOLET)
    o += caption("The bigger the consequence, the harder the gate.")
    return o + foot()


def s10_mailbox():
    o = head("The mailbox")
    o += title("A MAILBOX BETWEEN TWO WORLDS", color=VIOLET)
    # cloud with planner
    o += cloud(250, 330, 340, 230)
    o += robot(250, 420, 0.6, PINK, "clip", "focus")
    o += text(250, 520, "the planner, far away", 30, "h")
    # mailbox
    o += f'<g filter="url(#wob)"><rect x="560" y="330" width="240" height="150" rx="40" fill="{SKY}" class="s"/><rect x="580" y="388" width="200" height="14" rx="7" fill="{INK}"/><path d="M800 350 L800 280 L850 280 L850 320 L800 320" fill="{RED}" class="s"/><rect x="600" y="480" width="16" height="90" fill="#a9733a" class="s" stroke-width="3"/></g>'
    o += f'<g transform="rotate(-10 640 300)">' + box(600, 250, 100, 62, fill=WHITE, r=8, sw=4) + f'<path d="M608 262 L650 290 L692 262" class="f s" stroke-width="3"/></g>'
    o += text(680, 610, "a plain folder", 34, "t", fill=VIOLET)
    # worker at editor
    o += box(980, 250, 300, 190, fill="#2f2960", r=20, sw=5)
    o += farm(998, 268, 264, 154)
    o += robot(1180, 540, 0.75, MINT, "wrench", "happy")
    o += text(1100, 600, "the worker, next to the editor", 30, "h")
    o += arrow(430, 340, 560, 380, VIOLET, 24, 6) + arrow(810, 400, 960, 360, VIOLET, 24, 6)
    o += caption("One file in, one answer out. Simple enough to work anywhere.")
    return o + foot()


SCENES.update({
    "07-everything-is-a-file": s7_files,
    "08-done-is-not-proof": s8_proof,
    "09-you-stay-in-charge": s9_you,
    "10-a-mailbox-between-two-worlds": s10_mailbox,
})

if __name__ == "__main__":
    import os
    os.makedirs("out", exist_ok=True)
    for k, f in SCENES.items():
        os.makedirs("out", exist_ok=True); open(f"out/{k}.svg", "w", encoding="utf-8").write(f())
    print("ok")
