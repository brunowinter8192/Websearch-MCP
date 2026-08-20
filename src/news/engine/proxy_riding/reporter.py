# INFRASTRUCTURE

import math
import statistics
from datetime import datetime, timezone
from pathlib import Path

# From state.py: shared riding state shape + constants
from src.news.engine.proxy_riding.state import RiderState, FAIL_THRESHOLD

_BACKFILL_TOTAL = 61_000


# ORCHESTRATOR

# Write job.md + cumulative.png + success_load_hist.png + connect_fail_hist.png for a proxy-riding scrape run to job_dir.
def write_riding_report(state: RiderState, job_dir: Path, t_job_start: datetime) -> None:
    job_dir.mkdir(parents=True, exist_ok=True)
    stats = _compute_stats(state, t_job_start)
    _write_cumulative_plot(job_dir, stats)
    if stats["load_perc"] is not None:
        _write_load_hist(job_dir, stats)
    if stats["cf_perc"] is not None:
        _write_cf_hist(job_dir, stats)
    _write_md(job_dir, state, stats, t_job_start)


# FUNCTIONS

# Derive all metrics from RiderState and job start time.
def _compute_stats(state: RiderState, t_job_start: datetime) -> dict:
    jobs  = state.job_records
    rides = state.ride_records

    n_total_fetches   = len(jobs)
    n_ok              = sum(1 for j in jobs if j.status == "ok")
    n_regwall_fetches = sum(1 for j in jobs if j.status == "regwall")
    n_failed          = sum(1 for j in jobs if j.status in ("failed", "empty"))
    n_connect_fail    = state.n_connect_fail

    elapsed_values = [j.elapsed_s for j in jobs if j.elapsed_s is not None]
    mean_s   = statistics.mean(elapsed_values)   if elapsed_values else None
    median_s = statistics.median(elapsed_values) if elapsed_values else None

    wall_s       = (datetime.now(timezone.utc) - t_job_start).total_seconds()
    urls_per_min = (n_ok / wall_s * 60) if wall_s > 0 and n_ok else None

    ok_completion_s = sorted(
        (j.t_start - t_job_start).total_seconds() + (j.elapsed_s or 0)
        for j in jobs if j.status == "ok" and j.elapsed_s is not None
    )

    ride_lengths   = [r.n_urls_attempted for r in rides]
    ride_ok_counts = [r.n_ok             for r in rides]
    ride_len_stats = _distribution_stats(ride_lengths)
    n_proxies_burned     = len(rides)
    proxies_for_backfill = round(n_proxies_burned / max(n_ok, 1) * _BACKFILL_TOTAL)
    n_fail_rotations     = sum(1 for r in rides if r.n_failed >= FAIL_THRESHOLD)

    n_urls_with_regwall, retried_ok, retried_failed = _compute_retry_outcome(jobs)
    wasted_ratio = n_regwall_fetches / max(n_total_fetches, 1)

    pool_total, pool_windows = _compute_pool_windows(state)
    page_timeout_s = state.page_timeout_ms / 1000
    load_times, load_perc = _compute_load_percentiles(jobs)
    cf_times, cf_perc, cf_subtype_counts = _compute_connect_fail_stats(state)

    return {
        "n_ok": n_ok, "n_regwall_fetches": n_regwall_fetches,
        "n_failed": n_failed, "n_connect_fail": n_connect_fail,
        "n_total_fetches": n_total_fetches,
        "wall_s": wall_s, "mean_s": mean_s, "median_s": median_s,
        "urls_per_min": urls_per_min,
        "ok_completion_s": ok_completion_s,
        "ride_ok_counts": ride_ok_counts,
        "ride_len_stats": ride_len_stats,
        "n_proxies_burned": n_proxies_burned,
        "proxies_for_backfill": proxies_for_backfill,
        "n_fail_rotations": n_fail_rotations,
        "retried_ok": retried_ok, "retried_failed": retried_failed,
        "n_urls_with_regwall": n_urls_with_regwall,
        "wasted_ratio": wasted_ratio,
        "termination": state.termination,
        "pool_total": pool_total, "pool_windows": pool_windows,
        "page_timeout_s": page_timeout_s,
        "load_times": load_times,
        "load_perc": load_perc,
        "cf_times": cf_times,
        "cf_perc": cf_perc,
        "cf_subtype_counts": cf_subtype_counts,
    }


# Retry outcome: among URLs that saw ≥1 regwall, final status (eventually ok vs stayed failed).
def _compute_retry_outcome(jobs: list) -> tuple[int, int, int]:
    url_final: dict[str, str] = {}
    url_rw:    set[str]       = set()
    for j in jobs:
        url_final[j.url] = j.status
        if j.status == "regwall":
            url_rw.add(j.url)
    retried_ok     = sum(1 for u in url_rw if url_final[u] == "ok")
    retried_failed = len(url_rw) - retried_ok
    return len(url_rw), retried_ok, retried_failed


# Eligible pool over time — bucket pool_samples into 10-min windows.
def _compute_pool_windows(state: RiderState) -> tuple[int, list[dict]]:
    pool_total   = len(state.proxy_pool)
    pool_windows: list[dict] = []
    if state.pool_samples:
        _WIN_S = 600
        max_win = int(state.pool_samples[-1][0] / _WIN_S)
        for k in range(max_win + 1):
            win = [(e, ne, nc) for e, ne, nc in state.pool_samples if int(e / _WIN_S) == k]
            if win:
                min_eligible  = min(ne for _, ne, _ in win)
                avg_eligible  = round(sum(ne for _, ne, _ in win) / len(win))
                peak_cooldown = max(nc for _, _, nc in win)
                pool_windows.append({
                    "window_min":    k * 10,
                    "min_eligible":  min_eligible,
                    "avg_eligible":  avg_eligible,
                    "peak_cooldown": peak_cooldown,
                })
    return pool_total, pool_windows


# OK-fetch load-time inclusive percentiles; None when fewer than 2 samples.
def _compute_load_percentiles(jobs: list) -> tuple[list[float], dict | None]:
    load_times = [j.load_s for j in jobs if j.status == "ok" and j.load_s is not None]
    if len(load_times) < 2:
        return load_times, None
    qs = statistics.quantiles(load_times, n=100, method="inclusive")
    return load_times, {
        "p50": round(qs[49], 3), "p90": round(qs[89], 3), "p95": round(qs[94], 3),
        "p99": round(qs[98], 3), "max": round(max(load_times), 3), "n": len(load_times),
    }


# Connect-fail elapsed-time inclusive percentiles + subtype counts.
def _compute_connect_fail_stats(state: RiderState) -> tuple[list[float], dict | None, dict[str, int]]:
    cf_times    = [r[0] for r in state.connect_fail_records]
    cf_subtypes = [r[1] for r in state.connect_fail_records]
    cf_perc: dict | None = None
    if len(cf_times) >= 2:
        qs = statistics.quantiles(cf_times, n=100, method="inclusive")
        cf_perc = {
            "p50": round(qs[49], 3), "p90": round(qs[89], 3), "p95": round(qs[94], 3),
            "p99": round(qs[98], 3), "max": round(max(cf_times), 3), "n": len(cf_times),
        }
    cf_subtype_counts: dict[str, int] = {}
    for st in cf_subtypes:
        cf_subtype_counts[st] = cf_subtype_counts.get(st, 0) + 1
    return cf_times, cf_perc, cf_subtype_counts


# Compute mean/median/min/max of a list; return None-filled dict if empty.
def _distribution_stats(values: list) -> dict:
    if not values:
        return {"mean": None, "median": None, "min": None, "max": None}
    return {
        "mean":   round(statistics.mean(values),   2),
        "median": round(statistics.median(values), 2),
        "min":    min(values),
        "max":    max(values),
    }


# Format v with spec+unit, or an em-dash when None.
def _fmt(v, spec="", unit="") -> str:
    return f"{format(v, spec)}{unit}" if v is not None else "—"


# Step-plot of cumulative OK fetches vs elapsed seconds; save as cumulative.png.
def _write_cumulative_plot(job_dir: Path, stats: dict) -> None:
    import matplotlib.pyplot as plt

    xs = stats["ok_completion_s"]
    x  = [0.0] + xs if xs else [0.0]
    y  = list(range(len(x)))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.step(x, y, where="post", linewidth=1.5)
    ax.set_xlabel("Elapsed (s)")
    ax.set_ylabel("Cumulative OK fetches")
    ax.set_title("Cumulative OK fetches over time")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(job_dir / "cumulative.png", dpi=100)
    plt.close(fig)


# Histogram of OK-fetch load times; x-axis auto-ranges to data (load_s can exceed page_timeout_s
# due to post-nav processing); vertical line marks page_timeout_s so the nav cap is visible.
def _write_load_hist(job_dir: Path, stats: dict) -> None:
    import matplotlib.pyplot as plt

    load_times     = stats["load_times"]
    page_timeout_s = stats["page_timeout_s"]

    upper  = math.ceil(max(load_times) / 0.25) * 0.25
    n_bins = max(1, math.ceil(upper / 0.25))
    bins   = [i * 0.25 for i in range(n_bins + 1)]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(load_times, bins=bins, edgecolor="white", linewidth=0.5)
    ax.axvline(page_timeout_s, color="red", linewidth=1.2,
               label=f"page_timeout {page_timeout_s:.1f} s")
    ax.legend(fontsize=9)
    ax.set_xlim(0, upper)
    ax.set_xlabel("Load time (s)  [elapsed − DELAY_BEFORE_HTML 0.5 s]")
    ax.set_ylabel("OK fetches")
    ax.set_title("Success load-time distribution")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(job_dir / "success_load_hist.png", dpi=100)
    plt.close(fig)


# Histogram of connect-fail elapsed times; mirrors _write_load_hist style for direct comparability.
def _write_cf_hist(job_dir: Path, stats: dict) -> None:
    import matplotlib.pyplot as plt

    cf_times       = stats["cf_times"]
    page_timeout_s = stats["page_timeout_s"]

    upper  = math.ceil(max(cf_times) / 0.25) * 0.25
    n_bins = max(1, math.ceil(upper / 0.25))
    bins   = [i * 0.25 for i in range(n_bins + 1)]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(cf_times, bins=bins, edgecolor="white", linewidth=0.5)
    ax.axvline(page_timeout_s, color="red", linewidth=1.2,
               label=f"page_timeout {page_timeout_s:.1f} s")
    ax.legend(fontsize=9)
    ax.set_xlim(0, upper)
    ax.set_xlabel("Elapsed time (s)")
    ax.set_ylabel("Connect-fail fetches")
    ax.set_title("Connect-fail elapsed distribution")
    ax.grid(True, alpha=0.3, axis="y")
    fig.tight_layout()
    fig.savefig(job_dir / "connect_fail_hist.png", dpi=100)
    plt.close(fig)


# Write job.md with all metrics, tables, failure lists, and plot links.
def _write_md(
    job_dir: Path, state: RiderState, stats: dict, t_job_start: datetime,
) -> None:
    job_id  = t_job_start.strftime("%Y%m%dT%H%M%SZ")
    rw_rate = stats["n_regwall_fetches"] / max(stats["n_total_fetches"], 1)

    lines = _md_header_counts(state, stats, job_id)
    lines += _md_proxy_riding(stats)
    lines += _md_pool_windows(stats)
    lines += _md_regwall(stats, rw_rate)
    lines += _md_connect_fail(stats)
    lines += _md_load_time(stats)
    lines += _md_plots(stats)

    (job_dir / "job.md").write_text("\n".join(lines), encoding="utf-8")


# Header + Counts + Throughput sections.
def _md_header_counts(state: RiderState, stats: dict, job_id: str) -> list[str]:
    return [
        f"# CoinDesk riding job — {job_id}",
        "",
        "## Counts",
        "",
        "| Status | Count |",
        "|---|---|",
        f"| Target URLs | {state.total_urls} |",
        f"| Browsers | {state.n_browsers} |",
        f"| Contexts/browser | {state.n_slots // max(state.n_browsers, 1)} |",
        f"| Cooldown policy | {state.cooldown_mgr.policy} |",
        f"| OK | {stats['n_ok']} |",
        f"| Regwall fetches | {stats['n_regwall_fetches']} |",
        f"| Failed / Empty | {stats['n_failed']} |",
        f"| Failed rotations (2-strike) | {stats['n_fail_rotations']} |",
        f"| Connect-fail fetches | {stats['n_connect_fail']} |",
        f"| Total fetches | {stats['n_total_fetches']} |",
        f"| Termination | `{stats['termination']}` |",
        "",
        "## Throughput",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Wall-clock | {_fmt(stats['wall_s'], '.0f', 's')} |",
        f"| Mean s/fetch | {_fmt(stats['mean_s'], '.2f', 's')} |",
        f"| Median s/fetch | {_fmt(stats['median_s'], '.2f', 's')} |",
        f"| OK URLs/min | {_fmt(stats['urls_per_min'], '.1f')} |",
        "",
    ]


# Proxy-riding summary + ride-length distribution + eligible-pool header.
def _md_proxy_riding(stats: dict) -> list[str]:
    rls = stats["ride_len_stats"]
    return [
        "## Proxy riding",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Proxies burned | {stats['n_proxies_burned']} |",
        f"| Rides with ≥1 ok | {sum(1 for c in stats['ride_ok_counts'] if c > 0)} |",
        f"| 61k proxy estimate | {stats['proxies_for_backfill']:,} |",
        "",
        "### Ride length (URLs attempted per proxy)",
        "",
        f"mean={_fmt(rls['mean'], '.1f')}  "
        f"median={_fmt(rls['median'], '.1f')}  "
        f"min={_fmt(rls['min'])}  "
        f"max={_fmt(rls['max'])}",
        "",
        "## Eligible proxy pool over time",
        "",
        f"Browser-eligible pool (loaded): {stats['pool_total']:,}",
        "",
    ]


# Eligible-pool-over-time table (or no-samples note).
def _md_pool_windows(stats: dict) -> list[str]:
    pw = stats["pool_windows"]
    if not pw:
        return ["No samples — run completed before first poll.", ""]
    lines = [
        "| t (min) | min eligible | avg eligible | peak in-cooldown |",
        "|---|---|---|---|",
    ]
    for w in pw:
        t_label = f"{w['window_min']}–{w['window_min'] + 10}"
        lines.append(
            f"| {t_label} | {w['min_eligible']:,} | {w['avg_eligible']:,}"
            f" | {w['peak_cooldown']:,} |"
        )
    lines += [""]
    return lines


# Regwall summary section.
def _md_regwall(stats: dict, rw_rate: float) -> list[str]:
    return [
        "## Regwall",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Regwall fetches | {stats['n_regwall_fetches']} |",
        f"| Wasted-fetch ratio | {rw_rate:.1%} |",
        f"| URLs with ≥1 regwall | {stats['n_urls_with_regwall']} |",
        f"| → eventually OK | {stats['retried_ok']} |",
        f"| → stayed failed | {stats['retried_failed']} |",
        "",
    ]


# Connect-fail breakdown: percentile table + subtype table.
def _md_connect_fail(stats: dict) -> list[str]:
    lines    = ["## Connect-fail breakdown", ""]
    cp       = stats["cf_perc"]
    n_cf_tot = len(stats["cf_times"])
    if cp is None:
        lines += [
            f"_Fewer than 2 connect-fail records (n={n_cf_tot}) — distribution not available._",
            "",
        ]
    else:
        lines += [
            f"n = {cp['n']} connect-fail fetches  ·  timeout = {stats['page_timeout_s']:.1f} s",
            "",
            "| Percentile | Elapsed (s) |",
            "|---|---|",
            f"| p50 | {cp['p50']:.3f} |",
            f"| p90 | {cp['p90']:.3f} |",
            f"| p95 | {cp['p95']:.3f} |",
            f"| p99 | {cp['p99']:.3f} |",
            f"| max | {cp['max']:.3f} |",
            "",
        ]
    sc = stats["cf_subtype_counts"]
    if sc:
        lines += ["### Subtypes", "", "| Subtype | Count | Share |", "|---|---|---|"]
        for label in ("page_timeout", "net_timed_out", "proxy_connect", "other"):
            count = sc.get(label, 0)
            if count:
                lines.append(f"| {label} | {count} | {count / max(n_cf_tot, 1):.1%} |")
        lines += [""]
    return lines


# Success load-time distribution: percentile table.
def _md_load_time(stats: dict) -> list[str]:
    lines = ["## Success load-time distribution", ""]
    lp = stats["load_perc"]
    if lp is None:
        lines += [
            f"_Fewer than 2 OK fetches (n={len(stats['load_times'])}) — distribution not available._",
            "",
        ]
    else:
        lines += [
            f"n = {lp['n']} OK fetches  ·  timeout = {stats['page_timeout_s']:.1f} s",
            "",
            "| Percentile | Load time (s) |",
            "|---|---|",
            f"| p50 | {lp['p50']:.3f} |",
            f"| p90 | {lp['p90']:.3f} |",
            f"| p95 | {lp['p95']:.3f} |",
            f"| p99 | {lp['p99']:.3f} |",
            f"| max | {lp['max']:.3f} |",
            "",
        ]
    return lines


# Plot links, conditional on which histograms were written.
def _md_plots(stats: dict) -> list[str]:
    lines = ["## Plots", "", "![Cumulative OK](cumulative.png)", ""]
    if stats["cf_perc"] is not None:
        lines += ["![Connect-fail histogram](connect_fail_hist.png)", ""]
    if stats["load_perc"] is not None:
        lines += ["![Success load-time histogram](success_load_hist.png)", ""]
    return lines
