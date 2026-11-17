"""Build the public study app demo from the real app's index.html.

Usage: python3 scripts/study-demo/build.py [path/to/app/index.html]
Writes public/demos/study-app/index.html. The demo uses only the made-up
sample content in sample-content.json, sends nothing over the network, and
syncs the live game between tabs of one browser (BroadcastChannel).
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path.home() / "gl45-review" / "index.html")
OUT = HERE.parent.parent / "public" / "demos" / "study-app" / "index.html"
sample = json.loads((HERE / "sample-content.json").read_text())
html = SRC.read_text()

FAKE_SB = r"""
  // Demo only: a stand-in for the realtime client. Rooms sync between tabs of
  // this browser with BroadcastChannel; nothing is sent over the network.
  var sb = (function () {
    function Chan(name, cfg) {
      var self = this;
      this.key = (cfg && cfg.config && cfg.config.presence && cfg.config.presence.key) || Math.random().toString(36).slice(2);
      this.hb = {}; this.hp = []; this.state = {}; this.mine = null;
      this.bc = ("BroadcastChannel" in window) ? new BroadcastChannel("studydemo:" + name) : null;
      if (this.bc) this.bc.onmessage = function (e) { self.recv(e.data); };
    }
    Chan.prototype.on = function (type, filt, cb) { if (type === "broadcast") this.hb[filt.event] = cb; else if (type === "presence") this.hp.push(cb); return this; };
    Chan.prototype.sync = function () { this.hp.forEach(function (cb) { cb(); }); };
    Chan.prototype.post = function (m) { if (this.bc) this.bc.postMessage(m); };
    Chan.prototype.recv = function (m) {
      if (m.k === "b") { var cb = this.hb[m.event]; if (cb) cb({ payload: m.payload }); }
      else if (m.k === "p") {
        if (m.payload) this.state[m.key] = [m.payload]; else if (m.key !== this.key) delete this.state[m.key];
        this.sync();
        if (m.ask && this.mine) this.post({ k: "p", key: this.key, payload: this.mine });
      }
    };
    Chan.prototype.subscribe = function (cb) { var s = this; setTimeout(function () { s.post({ k: "p", key: s.key, payload: null, ask: true }); cb("SUBSCRIBED"); }, 0); return this; };
    Chan.prototype.send = function (m) { this.post({ k: "b", event: m.event, payload: m.payload }); return Promise.resolve("ok"); };
    Chan.prototype.track = function (p) { this.mine = p; this.state[this.key] = [p]; this.post({ k: "p", key: this.key, payload: p }); this.sync(); return Promise.resolve("ok"); };
    Chan.prototype.presenceState = function () { return this.state; };
    Chan.prototype.close = function () { if (this.mine) this.post({ k: "p", key: this.key, payload: null }); if (this.bc) this.bc.close(); };
    var open = [];
    window.addEventListener("pagehide", function () { open.forEach(function (c) { try { c.close(); } catch (e) {} }); });
    return {
      channel: function (n, c) { var ch = new Chan(n, c); open.push(ch); return ch; },
      removeChannel: function (ch) { ch.close(); },
      auth: { signOut: function () { return Promise.resolve(); } }
    };
  })();
"""

BANNER = ('<div style="background:#fff7dd;color:#3a2f00;padding:8px 16px;font-size:14px;text-align:center">'
          'Demo with made-up sample content. Progress stays in this browser and nothing is sent anywhere. '
          '<a href="/work/gsi-study-app/" target="_top" style="color:#003262;font-weight:700">Back to the case study</a></div>\n')

def rep(old, new, count=1):
    global html
    n = html.count(old)
    if n != count:
        sys.exit(f"expected {count} match(es), found {n}: {old[:70]!r}")
    html = html.replace(old, new)

# Remove network pieces: Vercel analytics and the Supabase library.
rep('<script>window.va = window.va || function () { (window.vaq = window.vaq || []).push(arguments); };</script>\n', '')
rep('<script defer src="/_vercel/insights/script.js"></script>\n', '')
rep('<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js"></script>\n', '')
start = html.index('  var sb = window.supabase.createClient(')
end = html.index('});', start) + 3
html = html[:start] + FAKE_SB.strip("\n") + html[end:]
html = html.replace('var SUPABASE_URL = "https://qlctjklwxjqcnlekfsqg.supabase.co";', 'var SUPABASE_URL = "";')
html = html.replace('var SUPABASE_KEY = "sb_publishable_s601Z3UmPwAeZfzsGijiAA_4c-9rfEy";', 'var SUPABASE_KEY = "";')

# Always demo mode; tracking rows stay in memory (insert/beacon already honor DEMO).
rep('var DEMO = /^(localhost|127\\.0\\.0\\.1)$/.test(location.hostname) && /[?&]demo=1/.test(location.search);', 'var DEMO = true;')
start = html.index('  // Local preview only:')
end = html.index('  } else {\n    boot();\n  }', start) + len('  } else {\n    boot();\n  }')
html = html[:start] + '  var SAMPLE = ' + json.dumps(sample, ensure_ascii=False) + ';\n  start(SAMPLE, { email: "Demo visitor", id: "demo" });' + html[end:]
rep('    so.classList.remove("hidden");\n', '')

# Copy: no course name, no claims about the instructor seeing progress.
rep("Your progress is saved on this device. Your GSI can see your progress to help plan review. This is not graded.",
    "Demo: progress is saved in this browser only. To try the game, open this page in a second tab: host in one, join in the other.")
rep('<p class="small muted">Only @berkeley.edu accounts can sign in. Your GSI can see your study progress to help plan review. This is not graded.</p>', '')
rep('<p class="muted">Midterm review for GLOBAL 45. Sign in with your Berkeley Google account (@berkeley.edu) to continue.</p>', '')
html = html.replace("GL45 Review", "Study app demo").replace('GL45 <span>Review</span>', 'Study app <span>demo</span>')
html = html.replace('id="brand">Study app demo<', 'id="brand">Study app <span>demo</span><')
html = html.replace("gl45", "studydemo").replace("GL45", "Study")
rep('<main id="app">', BANNER + '<main id="app">')

for bad in ("GLOBAL 45", "supabase.co", "sb_publishable", "—"):
    if bad in html:
        sys.exit(f"demo still contains {bad!r}")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(html)
print(f"wrote {OUT} ({len(html):,} bytes)")
