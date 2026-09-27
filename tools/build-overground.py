r"""Build overground/index.html from the newest Agent Lockhart clay-film build.

Usage:  python tools/build-overground.py [path-to-lockhart-clay-film-vNN.html]
With no argument it picks the newest D:\c\lockhart-clay-film-v*.html.

The hosted page is the game file plus four INFOSOUL-marked patches:
  1. the renderer, scene and camera are built synchronously before boot, so
     the sky modules (whose typeof guards otherwise race boot's rAF stages)
     always register;
  2. the page title;
  3. a loader that presses the menu's own OVERGROUND button once it exists,
     restarts Overground if anything closes it, hides the game HUD and the
     BACK TO THE RING exit, and benches every fighter so the deck is empty;
  4. Escape on the deck no longer leaves Overground;
  5. the flights are slower: the original hops between worlds in 3-10 s,
     the hosted tour takes 10-32 s, so the visitor can look around.
"""
import glob, io, os, re, sys

if len(sys.argv) > 1:
    src = sys.argv[1]
else:
    cands = glob.glob(r"D:\c\lockhart-clay-film-v*.html")
    cands = [c for c in cands if re.search(r"-v\d+\.html$", c)]
    src = max(cands, key=lambda p: int(re.search(r"-v(\d+)\.html$", p).group(1)))
dst = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "overground", "index.html")

g = io.open(src, encoding="utf-8", newline="").read()
nl = "\r\n" if "\r\n" in g[:20000] else "\n"
N = lambda s: s.replace("\n", nl)

def swap(old, new, what):
    global g
    old, new = N(old), N(new)
    n = g.count(old)
    assert n == 1, f"{what}: expected one match, found {n}"
    g = g.replace(old, new, 1)

swap('''    ["starting the projector", () => {
      initRenderer();
      initPost();''',
'''    ["starting the projector", () => {
      if (typeof renderer !== "undefined" && renderer) return;   /* INFOSOUL: already built, synchronously, before the modules below loaded */
      initRenderer();
      initPost();''', "stage 0")

swap('''} else if (window.THREE) boot();
else {''',
'''} else if (window.THREE) {
  /* INFOSOUL: boot runs its stages two frames apart, but the modules further
     down this file look for scene and camera the moment they load. Build the
     projector now, on this thread, so they always find it. */
  try {
    initRenderer(); initPost();
    POST.level = TOUCH ? "low" : (window.innerWidth * window.innerHeight > 2400000 ? "medium" : "high");
    setPostMode(true);
  } catch (e) { console.error("early projector", e); }
  boot();
}
else {''', "boot call")

swap("<title>Agent Lockhart — Clay Film Edition</title>",
     "<title>Overground — a tour of the Milky Way · Infosoul Laboratories</title>", "title")

hook = '''
<!-- INFOSOUL DEEP LINK START -->
<style>
/* infosoullaboratories.com hosts this page as OVERGROUND only: the sky, not the game. */
body:not(.overground) #overlay { visibility: hidden !important; }
#ogList button.home, #ogHint { display: none !important; }
body.overground .hud, body.overground #board, body.overground #pad, body.overground #boutCard { display: none !important; }
</style>
<script>
(() => {
 "use strict";
 let tries = 0;
 const t = setInterval(() => {
  const OG = window.LOCKHART_OVERGROUND, b = document.getElementById("overgroundBtn");
  if (OG && b) { clearInterval(t); try { b.click(); } catch (e) {} keep(OG); }
  else if (++tries > 1200) clearInterval(t);
 }, 250);
 /* The sky, not the bout: Overground starts a six-way on the deck so the
    board has names on it. Here the deck is cleared. Every fighter is
    benched the way the game benches its own hero -- out, and invisible --
    so the round never plays, nobody swings, and nothing is said. */
 function clearDeckForTheSky() {
  try {
   const list = (typeof FIGHTERS !== "undefined" && FIGHTERS) ? FIGHTERS : [];
   for (const f of list) {
    if (!f) continue;
    f.out = true; f.carried = true; f.ko = false; f.atk = null; f.cast = null; f.blocking = false; f._sayQ = null;
    if (f.rig) {
     if (f.rig.root) f.rig.root.visible = false;
     if (f.rig.contact) f.rig.contact.visible = false;
     if (f.rig.ring) f.rig.ring.visible = false;
    }
   }
  } catch (e) {}
 }
 /* ESC or the ring button would hand the visitor the game. Put them back on the deck instead. */
 function keep(OG) {
  clearDeckForTheSky();
  setInterval(() => {
   try { if (!OG.on && typeof OG.start === "function") OG.start(); } catch (e) {}
   clearDeckForTheSky();
  }, 600);
 }
 window.addEventListener("keydown", e => {
  const OG = window.LOCKHART_OVERGROUND;
  if (e.code === "Escape" && OG && OG.on && !(OG.journey && OG.journey.on) && OG.state === "deck") { e.stopImmediatePropagation(); e.preventDefault(); }
 }, true);
})();
</script>
<!-- INFOSOUL DEEP LINK END -->
</body>'''
assert g.count("</body>") == 1 and "INFOSOUL DEEP LINK" not in g
g = g.replace("</body>", N(hook), 1)

# 5. slower flights, inside the OVERGROUND module only
a = g.index("<!-- OVERGROUND START -->"); b = g.index("<!-- OVERGROUND END -->")
mod = g[a:b]
def swap_mod(old, new, what):
    global mod
    n = mod.count(old)
    assert n == 1, f"{what}: expected one match in the Overground module, found {n}"
    mod = mod.replace(old, new, 1)
swap_mod("dur: clamp(2.6 + dist / 320, 3, 10)",
         "dur: clamp(8 + dist / 100, 10, 32) /* INFOSOUL: a tour, not a dash */", "flight duration")
swap_mod("dur: clamp(2.6 + from.distanceTo(dest) / 320, 3, 9)",
         "dur: clamp(6 + from.distanceTo(dest) / 120, 8, 24) /* INFOSOUL */", "return flight duration")
swap_mod("OG.t += dt; const u = clamp(OG.t / 2.2, 0, 1);",
         "OG.t += dt; const u = clamp(OG.t / 4.5, 0, 1); /* INFOSOUL: a slower lift-off */", "lift-off")
swap_mod("OG.t += dt; const u = clamp(OG.t / 2.4, 0, 1);",
         "OG.t += dt; const u = clamp(OG.t / 6, 0, 1); /* INFOSOUL: a slower warp */", "warp")
swap_mod("OG.t += dt; const u = clamp(OG.t / 1.6, 0, 1);",
         "OG.t += dt; const u = clamp(OG.t / 3.2, 0, 1); /* INFOSOUL: a slower landing */", "landing")
g = g[:a] + mod + g[b:]

io.open(dst, "w", encoding="utf-8", newline="").write(g)
print("built", dst, "from", src, f"({len(g):,} bytes)")
