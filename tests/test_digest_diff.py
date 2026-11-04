"""digest_diff.py finds what changed in the Verse API between two digests."""
import os, sys, tempfile
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "project-template", "Claude", "hooks"))
import digest_diff as D
fails = []
def check(n, c):
    print(("PASS " if c else "FAIL ") + n)
    if not c: fails.append(n)
OLD = """using { /Verse.org/Native }
button_device<public> := class<concrete><final>(creative_device_base):
    InteractedWithEvent<public>:listenable(agent) = external {}
    Enable<public>():void = external {}
    Gone<public>():void = external {}
tag_view<public> := class:
    Get<public>():[]creative_object = external {}
"""
NEW = """using { /Verse.org/Native }
button_device<public> := class<concrete><final>(creative_device_base):
    InteractedWithEvent<public>:listenable(agent) = external {}
    Enable<public>(?Agent:agent):void = external {}
    # experimental: may change
    NewThing<public>():void = external {}
timer<public> := class:
    Start<public>():void = external {}
tag_view<public> := class:
    Get<public>():[]creative_object = external {}
"""
with tempfile.TemporaryDirectory() as d:
    o, n = os.path.join(d, "o"), os.path.join(d, "n")
    os.makedirs(o); os.makedirs(n)
    open(os.path.join(o, "Fortnite.digest.verse"), "w").write(OLD)
    open(os.path.join(n, "Fortnite.digest.verse"), "w").write(NEW)
    text, c = D.report(o, n)
    check("an added class and its member are found", "timer" in text and c["added"] >= 2)
    check("a removed member is found", "Gone" in text.split("Members removed")[1].split("##")[0])
    check("a changed signature is shown old to new", "Enable" in text.split("signature changed")[1] and "?Agent:agent" in text)
    check("an experimental comment flags the member that follows", c["flagged"] == 1 and "NewThing" in text.split("Near experimental")[1])
    check("an unchanged member is not listed", "InteractedWithEvent" not in text)
print("ALL PASS" if not fails else "%d FAIL" % len(fails))
sys.exit(1 if fails else 0)
