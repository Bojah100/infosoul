r"""Build overground/index.html from the newest Agent Lockhart clay-film build.

Usage:  python tools/build-overground.py [path-to-lockhart-clay-film-vNN.html]
With no argument it picks the newest D:\c\overground-v*.html (the Overground
build, with its own LIFT OFF card and the hand-sculpted red explorer rocket),
falling back to the newest lockhart-clay-film-v*.html.

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
     the hosted tour takes 9-32 s (the moon ~10 s, Mars ~15 s, Pluto ~32 s),
     so the visitor can look around.
"""
import glob, io, os, re, sys

if len(sys.argv) > 1:
    src = sys.argv[1]
else:
    def newest(pattern):
        c = [x for x in glob.glob(pattern) if re.search(r"-v\d+\.html$", x)]
        return max(c, key=lambda p: int(re.search(r"-v(\d+)\.html$", p).group(1))) if c else None
    src = newest(r"D:\c\overground-v*.html") or newest(r"D:\c\lockhart-clay-film-v*.html")
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

# 2b. the loading card says OVERGROUND, not LOADING; the game's name bars stay out of sight
swap('''<div id="loading">
  <div>LOADING</div>
  <div id="loadTrack"><div id="loadFill"></div></div>
  <div id="loadLabel">warming up</div>''',
'''<div id="loading">
  <div>OVERGROUND</div>
  <div id="loadTrack"><div id="loadFill"></div></div>
  <div id="loadLabel">building the sky</div>''', "loading card")

locked = "<!-- OVERGROUND LOCK START -->" in g   # the source has its own front door: keep it
hook = '''
<!-- INFOSOUL DEEP LINK START -->
<style>
/* infosoullaboratories.com hosts this page as OVERGROUND only: the sky, not the game. */
body:not(.overground) #overlay, body:not(.overground) .hud, body:not(.overground) #pad { visibility: hidden !important; }
body.overground #ogSplash:not(.off) { display: none !important; }
body:not(.overgroundBuild) #ogList button.home, body:not(.overgroundBuild) #ogHint { display: none !important; }
body.overground .hud, body.overground #board, body.overground #pad, body.overground #boutCard { display: none !important; }
</style>
<script>
(() => {
 "use strict";
 const LOCKED = ''' + ("true" if locked else "false") + ''';   /* the build has its own LIFT OFF card */
 let tries = 0;
 const t = setInterval(() => {
  const OG = window.LOCKHART_OVERGROUND, b = document.getElementById("overgroundBtn");
  if (LOCKED) { if (OG) { clearInterval(t); setInterval(clearDeckForTheSky, 600); } else if (++tries > 1200) clearInterval(t); return; }
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
 if (!LOCKED) window.addEventListener("keydown", e => {
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
    """Apply a timing change, or accept it if the source build already carries it."""
    global mod
    n = mod.count(old)
    if n == 0 and new.split(" /*")[0] in mod:
        print(f"  {what}: already slow in the source build")
        return
    assert n == 1, f"{what}: expected one match in the Overground module, found {n}"
    mod = mod.replace(old, new, 1)
swap_mod("dur: clamp(2.6 + dist / 320, 3, 10)",
         "dur: clamp(8 + dist / 22, 9, 32) /* INFOSOUL: a tour, not a dash -- the moon in ten seconds, Pluto in half a minute */", "flight duration")
swap_mod("dur: clamp(2.6 + from.distanceTo(dest) / 320, 3, 9)",
         "dur: clamp(6 + from.distanceTo(dest) / 30, 8, 24) /* INFOSOUL */", "return flight duration")
swap_mod("OG.t += dt; const u = clamp(OG.t / 2.2, 0, 1);",
         "OG.t += dt; const u = clamp(OG.t / 4.5, 0, 1); /* INFOSOUL: a slower lift-off */", "lift-off")
swap_mod("OG.t += dt; const u = clamp(OG.t / 2.4, 0, 1);",
         "OG.t += dt; const u = clamp(OG.t / 6, 0, 1); /* INFOSOUL: a slower warp */", "warp")
swap_mod("OG.t += dt; const u = clamp(OG.t / 1.6, 0, 1);",
         "OG.t += dt; const u = clamp(OG.t / 3.2, 0, 1); /* INFOSOUL: a slower landing */", "landing")
g = g[:a] + mod + g[b:]

io.open(dst, "w", encoding="utf-8", newline="").write(g)
print("built", dst, "from", src, f"({len(g):,} bytes)")
