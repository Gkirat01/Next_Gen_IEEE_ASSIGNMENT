import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

# ─────────────────────────────────────────────
# CONFIGURATION — edit paths if needed
# ─────────────────────────────────────────────
DATA_FOLDER      = r"D:\Masters\2nd sem\IEEE_online\Scenario_2\simulations"  # folder with your 45 CSVs
OUTPUT_FOLDER    = "figures_scenario2"                   # output folder for figures
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

SIMULATION_TIME  = 3            # seconds (your simulation time)
PAYLOAD          = 2000         # bytes (fixed for scenario 2)
STRATEGIES       = ["TBA", "ESA", "BPA"]
RETRY_LIMITS     = [1, 6, 12]
STATIONS         = [2, 4, 6, 8, 10]

# Colors — one per retry limit
COLORS           = ["#e63946", "#2a9d8f", "#457b9d"]
MARKERS          = ["o", "s", "^"]
JITTER           = [-0.15, 0.0, 0.15]
# ─────────────────────────────────────────────
# STEP 1 — Read all 45 CSV files into one dataframe
# ─────────────────────────────────────────────
all_data = []

csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))

if not csv_files:
    raise FileNotFoundError(
        f"No CSV files found in '{DATA_FOLDER}/'. "
        "Make sure the folder exists and contains your 45 CSV files."
    )

for filepath in csv_files:
    filename = os.path.basename(filepath).replace(".csv", "")

    # Parse parameters from filename e.g. TBA_R1_S2
    try:
        parts    = filename.split("_")
        strategy = parts[0]                          # TBA, ESA, BPA
        retry    = int(parts[1].replace("R", ""))    # 1, 6, 12
        stas     = int(parts[2].replace("S", ""))    # 2, 4, 6, 8, 10
    except Exception:
        print(f"  ⚠ Skipping file with unexpected name format: {filename}")
        continue

    df = pd.read_csv(filepath)

    # ── Throughput calculation across ALL 3 bands ──────────────────────
    # Total successful packets = sum across 2.4, 5, and 6 GHz bands
    # Throughput (Mbps) = (total packets × payload bytes × 8 bits)
    #                     / (simulation time × 1e6)
    df["TotalPackets"] = (
        df["NumSuccessfulPackets24"] +
        df["NumSuccessfulPackets5"]  +
        df["NumSuccessfulPackets6"]
    )

    df["Throughput_Mbps"] = (
        df["TotalPackets"] * PAYLOAD * 8
    ) / (SIMULATION_TIME * 1e6)

    # ── MAC Delay: convert seconds → milliseconds ──────────────────────
    df["MACDelay_ms"] = df["MACDly"] * 1000

    # ── Average across all realizations in this file ───────────────────
    avg_throughput = df["Throughput_Mbps"].mean()
    avg_mac_delay  = df["MACDelay_ms"].mean()

    all_data.append({
        "Strategy":   strategy,
        "Retry":      retry,
        "STAs":       stas,
        "Throughput": avg_throughput,
        "MACDelay":   avg_mac_delay,
    })

combined = pd.DataFrame(all_data)
print(f"✅ Loaded {len(combined)} simulation runs successfully.\n")
print(combined.sort_values(["Strategy", "Retry", "STAs"]).to_string(index=False))
print()

# ─────────────────────────────────────────────
# STEP 2 — Plot 6 figures (3 strategies × 2 metrics)
# ─────────────────────────────────────────────

for strategy in STRATEGIES:
    strat_data = combined[combined["Strategy"] == strategy]

    if strat_data.empty:
        print(f"⚠ No data found for Strategy={strategy}, skipping.")
        continue

    # ── Figure A: Throughput vs Number of Stations ────────────────────
    fig, ax = plt.subplots(figsize=(8, 5))

    for idx, retry in enumerate(RETRY_LIMITS):
        subset = strat_data[strat_data["Retry"] == retry].sort_values("STAs")
        if subset.empty:
            continue
        ax.plot(
            subset["STAs"] + JITTER[idx],
            subset["Throughput"],
            marker=MARKERS[idx],
            linewidth=2,
            markersize=7,
            color=COLORS[idx],
            label=f"Retry Limit = {retry}"
        )

    ax.set_title(
        f"Throughput vs Number of Stations\nAggregation Strategy = {strategy}",
        fontsize=13, fontweight="bold"
    )
    ax.set_xlabel("Number of Stations", fontsize=12)
    ax.set_ylabel("Throughput (Mbps)", fontsize=12)
    ax.set_xticks(STATIONS)
    ax.legend(title="Retry Limit", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    fname = os.path.join(OUTPUT_FOLDER, f"Fig_Throughput_{strategy}.png")
    plt.savefig(fname, dpi=150)
    plt.close()
    print(f"✅ Saved: {fname}")

    # ── Figure B: MAC Delay vs Number of Stations ─────────────────────
    fig, ax = plt.subplots(figsize=(8, 5))

    for idx, retry in enumerate(RETRY_LIMITS):
        subset = strat_data[strat_data["Retry"] == retry].sort_values("STAs")
        if subset.empty:
            continue
        ax.plot(
            subset["STAs"] + JITTER[idx],
            subset["MACDelay"],
            marker=MARKERS[idx],
            linewidth=2,
            markersize=7,
            color=COLORS[idx],
            label=f"Retry Limit = {retry}"
        )

    ax.set_title(
        f"MAC Delay vs Number of Stations\nAggregation Strategy = {strategy}",
        fontsize=13, fontweight="bold"
    )
    ax.set_xlabel("Number of Stations", fontsize=12)
    ax.set_ylabel("MAC Delay (ms)", fontsize=12)
    ax.set_xticks(STATIONS)
    ax.legend(title="Retry Limit", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    fname = os.path.join(OUTPUT_FOLDER, f"Fig_MACDelay_{strategy}.png")
    plt.savefig(fname, dpi=150)
    plt.close()
    print(f"✅ Saved: {fname}")

print("\n🎉 All 6 figures generated successfully in the 'figures_scenario2/' folder!")
