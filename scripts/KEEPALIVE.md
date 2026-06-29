# Keep-warm (kill the cold-start wait)

The site runs on Render's **free** web-service tier, which **sleeps after ~15
minutes** with no traffic. The next visit then pays a **1–3 minute cold start**
(the container boots and re-opens the Neon database connection). That's bad for
visitors *and* for SEO — slow first-byte hurts crawling and Core Web Vitals.

The fix: ping the site on a schedule so it never goes idle. **The ping is the
"visitor."** We hit `GET /api/services` (not `/api/health`) on purpose, because
`/api/services` runs a real database query — so a single request warms **both the
web app and the Neon DB**.

There are three ways to run it. **You only need one.** The GitHub Action is the
recommended default because it's free and needs no machine of yours.

---

## 1. GitHub Actions (recommended — free, serverless, always on)

`.github/workflows/keepalive.yml` runs `scripts/keepalive.py` from GitHub's
servers about every **13 minutes**, 24/7. Nothing of yours has to be running.

**Setup:** nothing required — it works as-is once pushed (the script defaults to
`https://smarnb.onrender.com`). To point it elsewhere, add a repository
**variable** `KEEPALIVE_URL` under *Settings → Secrets and variables → Actions →
Variables*.

**Trigger it manually** any time from the **Actions** tab → *keepalive* → *Run
workflow*.

**GitHub's caveats (built into the workflow comments too):**

- **Cron drift.** The smallest interval GitHub allows is 5 minutes, but scheduled
  runs are *best-effort* and can be **delayed or skipped** when GitHub is busy.
  We ask for ~13 min so that even with drift we stay under the 15-min idle window.
- **60-day inactivity pause.** GitHub **disables** scheduled workflows in a repo
  with **no commits for ~60 days**. The pings themselves don't count as activity.
  Re-enable by pushing any commit, or clicking *Enable workflow* / *Run workflow*
  in the Actions tab. (A tiny monthly commit, or just using the repo, avoids this.)
- Scheduled runs only execute from the file on your **default branch**.

---

## 2. Fallback — Windows Task Scheduler (your PC, when it's on)

Good if you'd rather not rely on GitHub, but note it only pings while your machine
is awake and online.

**Option A — let the script loop itself:**

```
python C:\Users\alira\Documents\portfolio\scripts\keepalive.py --loop --interval 600
```

Leave that running (it pings every 10 minutes). To start it at logon:

1. Open **Task Scheduler** → *Create Task…*
2. **Triggers:** *At log on*.
3. **Actions:** *Start a program* →
   - Program: `python`
   - Arguments: `C:\Users\alira\Documents\portfolio\scripts\keepalive.py --loop`
4. **Settings:** tick *Run task as soon as possible after a scheduled start is
   missed*.

**Option B — let Task Scheduler do the timing** (single-shot every 10 min):

- **Triggers:** *Daily*, then *Repeat task every 10 minutes for a duration of 1
  day* (and set it to recur daily).
- **Actions:** Program `python`, Arguments
  `C:\Users\alira\Documents\portfolio\scripts\keepalive.py`.

The script needs no dependencies (standard library only), so any Python 3 works.

---

## 3. Fallback — a free external uptime pinger (no machine, no GitHub)

Services like **[cron-job.org](https://cron-job.org)** or **[UptimeRobot](https://uptimerobot.com)**
will fetch a URL on a schedule from their servers for free.

- Create a monitor / cron job hitting **`https://smarnb.onrender.com/api/services`**
  every **10 minutes** (UptimeRobot's free plan is 5-minute intervals — even
  better).
- This is a **pure external pinger** — it makes an HTTP request like any visitor.
  It does **not** embed any third-party script, tag, or code into the site, so it
  is fully compatible with the site's first-party / no-third-party-scripts policy.
  (That rule is about what runs *in the page*; an outside service requesting a URL
  is just traffic.)

---

## Is keeping it warm still free? Yes.

Render's free tier gives roughly **750 instance-hours per month**, shared across
your free web services. A month is about **730 hours** (24 × ~30.4), so keeping
**one** free web service awake 24/7 costs ~**730 h** — comfortably **under the
~750 h** allowance. So this single always-on service stays on the free plan.

Caveats to keep it that way:

- The math only works for **one** always-on free service. A second always-on free
  service would roughly double the hours and blow past 750 h.
- The keep-alive traffic itself is trivial (one tiny request every ~13 min). Bandwidth
  is not the constraint — instance-hours are.
- This keeps the **app** free; the **Neon** database is on its own free plan and is
  unaffected by the pings (a light query every few minutes is negligible).

---

## Quick test

```
# one ping, verbose
python scripts/keepalive.py

# ping a different site
python scripts/keepalive.py https://example.com/api/services

# run the self-looping warmer locally
python scripts/keepalive.py --loop --interval 600
```

A healthy run logs `OK … -> HTTP 200 in 0.4s`. The first ping after the site has
been asleep may log a slow time (and a note that it was asleep) — that's the cold
start you just absorbed so a real visitor didn't have to.
