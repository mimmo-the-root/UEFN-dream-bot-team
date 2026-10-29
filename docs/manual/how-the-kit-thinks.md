# How the kit thinks

**Do not make the question better. Make the place around it better.**

![Tell it your dream](01-tell-it-your-dream.png)

*Hacking*, in its first and best meaning, is making a system better, again and again, until it is quietly perfect. You find the small clever change that makes a whole family of problems disappear. Dream Bot Team is that, aimed at one question:

**How can an AI build a real Fortnite map, and be trusted with it?**

This page is the whole answer. You can read it in five minutes.

---

## 1. Three jobs, and a ladder

Most "self-driving" AI setups hide a secret: **you are the loop.** It writes, you read. It says "done", you check. It breaks something, you explain. Then you type again.

A person is quietly doing three jobs the system should do:

- **Give it a place to work.** This is the *harness*: what the helper **can** do.
- **Tell it if it was right.** This is the *loop*: what is **true**.
- **Decide what happens next.** This is the *graph*: what comes **next**.

They are not three tools on a shelf. They are a ladder, and each step exists because the step below it breaks in a predictable way.

| Step | What it gives | What breaks, so you need the next step |
|---|---|---|
| 0. Chat | Nothing: you are the whole program | You are the bottleneck |
| 1. Hands | The helper can act: files, tools, the editor | It acts with no memory and no walls |
| 2. Memory and walls | Notes that outlive the chat, and limits that hold even when the helper is wrong | It says "fixed, should pass now" and nothing checks |
| 3. The check | A test that can fail, written before the work | A red light is a verdict, not a direction |
| 4. Feedback | "I expected this, I saw that, stay inside this fence, this was already tried" | Every piece is right, the whole is slow and serial |
| 5. Shape | The work cut into pieces that run side by side | One failure means redoing everything |
| 6. Gates | Passed work is frozen; you only step in where undo is impossible | The same mistake comes back next week |
| 7. Learning | A mistake becomes a rule, on the right step of the ladder | The same mistake never comes back |

A wish is "please do not touch that file". A **wall** is a permission the helper does not have. We build walls.

The check is the strongest idea on the ladder. Rank every proof by how hard it is to fake: a build that passes and a value read back from the editor are strong; "I am confident" is the weakest. And a check that already passes before the work proves nothing: you must see it fail once. If you cannot say what "green" means, writing that down *is* the spec.

![Four steps to magic](06-four-steps-to-magic.png)

### Where Dream Bot Team stands, honestly

- **Hands, memory and walls (steps 1 and 2):** strong. Every editor tool is mapped; the plan, notes and decisions are files; nothing is ever deleted; a mailbox separates the planner from the worker.
- **Check and feedback (steps 3 and 4):** strong on checks (build, read-back from the editor, scans, two reviewers). Growing on feedback: a failure should say what was expected, what was seen and what was already tried, and the same failure twice means stop and ask you.
- **Shape and gates (steps 5 and 6):** the path from idea to delivery is already a graph with one human gate. Next: more work side by side, and gates sized by the price of undo (see below).
- **Learning (step 7):** lessons are proposed, approved by you and kept. Next: each lesson says which step of the ladder it fixes.

**A new question changes one try. A better workshop changes every try.**

---

## 2. The whole idea in one picture

1. **You** bring the dream, the choices and what only a person can do.
2. **The plan** says what "done" means, written first.
3. **The team** of 22 helpers does the work, one job each.
4. **The editor** is the place where every tool is known and every trick was tried for real.
5. **Proof** comes from the editor: built, read back, checked, played.
6. **Your yes**: only you tick the box.
7. **Lessons** are kept for the next map, and the next plan starts from them.

In one sentence: **you say what "done" means, the team builds, the editor proves it, you say yes, and the kit remembers.**

![Meet your dream team](02-meet-your-dream-team.png)

---

## 3. The choices, and why each one is simple

Every choice below removes a problem. It does not just manage it.

### "Done" has to be shown, not said

A helper can say "finished" and be wrong. So nothing counts as done until the editor itself shows it: the code builds, the value is read back, the check finds nothing wrong. The team proposes. The editor decides.

![Done is not proof](08-done-is-not-proof.png)

### Whoever builds never checks

The helper that writes the work never reviews it. Two others try to find what is wrong with it. Checking is an honest attempt to break the work, not a friendly second look.

### You stay in charge, only where it matters

The gate depends on **the price of undo**, not on how sure the helper feels. If a change can be undone in one click, it ships when the checks are green. If undoing it means cleaning up, it needs proof and a second opinion. If it cannot be undone at all (publishing, deleting), a person signs, and there is no score the helper can argue with. Reading is free. Changing is shown to you. Publishing needs your yes. Deleting never happens: things are parked in a safe folder, and you decide. You are the slowest and most valuable part of the system, so we put you only where a mistake cannot be taken back.


![You stay in charge](09-you-stay-in-charge.png)

### Everything is a file

The plan, the notes, the checklist, the decisions are plain text files. You can open every one. There is no hidden memory and nothing important lives only in a chat. What the team knows, you can read. What you tick, the team reads.

![Everything is a file](07-everything-is-a-file.png)

### One mailbox between two places

The planner can sit far away. The worker sits next to the editor. Between them is a folder, like a mailbox: one side drops a letter, the other answers. It is the simplest thing that works across a network, a laptop and a phone.

![A mailbox between two worlds](10-a-mailbox-between-two-worlds.png)

### The same mistake never twice

When something goes wrong, the kit proposes a lesson. You approve it. It stays private by default. A corrected answer helps one run. A corrected system helps every run.

![It grows with you](05-it-grows-with-you.png)

### The screen is alive

A still screen cannot tell you if the system is working or stuck. So the screens *pulse*. Each helper lights up while it works, the arrows breathe, a finished step turns green by itself. You trust what you can see living. The pulse is cheap and gentle, and it stops for anyone who asks for less motion.

![A system that breathes](03-a-system-that-breathes.png)

---

## 4. The way we work

We do not write a giant plan and build for months. We work in short loops on a real map, and let the map teach the kit.

1. **Run it on a real map.** The farm map is our experiment.
2. **Watch where it hurts.** If the owner cannot tell how to play, the game has a flaw. If the owner reads a word he does not understand, the kit has a flaw.
3. **Fix the workshop, not the symptom.** The fix becomes a rule, a check or a lesson, so it cannot come back.
4. **Keep it small.** What no longer earns its place goes away. The best workshop is the smallest one that closes the gap between what you meant and what was proven.

This is *lean*, one level higher. Lean Startup builds, measures and learns on the **product**. Here the same loop runs on the **factory that builds the product**: every map is an experiment on the workshop. From the Toyota line we keep the habit of stopping at the first defect and building quality in, instead of checking at the end. From the hacker world we keep the taste: a good fix is small, clear, and kills a whole family of problems.

A demo is the smallest honest proof: one clean run through every phase, with nothing left for you to repair.

---

## 5. What we are, and what we are not

Others took one slice of this idea and went deep: a layer that writes its own skills from real sessions, a method that measures before it simplifies a team of agents, a library of design taste turned into skills. Good work. We learned from all of it.

Dream Bot Team is **the whole loop, in one place, with a person in the loop**: agree what done means, build, prove, ask you, learn. For Fortnite maps.

We are also honest about the limits. It does not yet score itself on a fixed set of tests. Learning needs your approval. Some editor settings cannot be reached by the tools, so a person sets them by hand. Every release says what was really run on a live editor and what was only checked offline.

---

## 6. Where to go next

*The ladder above follows an article by @m4lkxx on harnesses, loops and graphs, which we read after building the kit and found very close to what we do. We wrote our own words and our own picture.*


- **Read the story:** [the manifesto](https://github.com/mimmo-the-root/UEFN-dream-bot-team/blob/main/docs/MANIFESTO.md).
- **Try it in ten minutes:** [quick start](ch:quick-start).
- **From idea to a playable game:** [the walk-through](ch:from-idea-to-game).
- **Watch it work:** [the console](ch:the-console).
- **How it learns:** [skills and lessons](ch:skills-and-lessons).
- **Why a rule exists:** [decision records](https://github.com/mimmo-the-root/UEFN-dream-bot-team/tree/main/docs/adr).

The goal was never a system that does not need you. It is a system that needs you once, at the right place.

*The model brings the intelligence. The workshop brings the structure. Together they build maps you can trust.*
