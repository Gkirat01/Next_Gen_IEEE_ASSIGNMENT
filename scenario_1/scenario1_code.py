import pandas as pd
import matplotlib.pyplot as plt
import os
import glob

# ─────────────────────────────────────────────
# CONFIGURATION — edit paths if needed
# ─────────────────────────────────────────────
DATA_FOLDER   = r"D:\Masters\2nd sem\IEEE_online\scenario1_simulations"          # folder where your 36 CSVs are
OUTPUT_FOLDER = "figures"       # folder where figures will be saved
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

SIMULATION_TIME = 1             # seconds (your max sim time)
PAYLOADS        = [200, 800, 1400, 2000]   # bytes
STATIONS        = [5, 10, 15]
GI_VALUES       = ["0.8", "1.6", "3.2"]       # as they appear in filenames
GI_LABELS       = {"0.8": "0.8 µs", "1.6": "1.6 µs", "3.2": "3.2 µs"}

COLORS = ["#e63946", "#2a9d8f", "#e9c46a", "#457b9d"]  # one per payload

# ─────────────────────────────────────────────
# STEP 1 — Read all 36 CSV files into one dataframe
# ─────────────────────────────────────────────
all_data = []

csv_files = glob.glob(os.path.join(DATA_FOLDER, "*.csv"))

if not csv_files:
    raise FileNotFoundError(
        f"No CSV files found in '{DATA_FOLDER}/'. "
        "Make sure the folder exists and contains your 36 CSV files."
    )

for filepath in csv_files:
    filename = os.path.basename(filepath).replace(".csv", "")

    # Parse parameters from filename e.g. GI08_P200_S5
    try:
        parts   = filename.split("_")
        gi      = parts[0].replace("GI", "")        # "08", "16", "32"
        payload = int(parts[1].replace("P", ""))     # 200, 800, 1400, 2000
        stas    = int(parts[2].replace("S", ""))     # 5, 10, 15
    except Exception:
        print(f"  ⚠ Skipping file with unexpected name format: {filename}")
        continue

    df = pd.read_csv(filepath)

    # ── Throughput calculation ──────────────────────────────────────────
    # Throughput (Mbps) = (successful packets × payload bytes × 8 bits)
    #                     / (simulation time × 1e6)
    # Only 2.4 GHz band is active (NumSuccessfulPackets24)
    df["Throughput_Mbps"] = (
        df["NumSuccessfulPackets24"] * payload * 8
    ) / (SIMULATION_TIME * 1e6)

    # ── MAC Delay (convert seconds → milliseconds) ──────────────────────
    df["MACDelay_ms"] = df["MACDly"] * 1000

    # ── Average across all realizations in this file ────────────────────
    avg_throughput = df["Throughput_Mbps"].mean()
    avg_mac_delay  = df["MACDelay_ms"].mean()

    all_data.append({
        "GI":           gi,
        "Payload":      payload,
        "STAs":         stas,
        "Throughput":   avg_throughput,
        "MACDelay":     avg_mac_delay,
    })

combined = pd.DataFrame(all_data)
print(f"✅ Loaded {len(combined)} simulation runs successfully.\n")
print(combined.sort_values(["GI", "Payload", "STAs"]).to_string(index=False))
print()

# ─────────────────────────────────────────────
# STEP 2 — Plot 6 figures (3 GI × 2 metrics)
# ─────────────────────────────────────────────

for gi in GI_VALUES:
    gi_data = combined[combined["GI"] == gi]

    if gi_data.empty:
        print(f"⚠ No data found for GI={gi}, skipping.")
        continue

    gi_label = GI_LABELS[gi]

    # ── Figure A: Throughput vs Number of Stations ────────────────────
    fig, ax = plt.subplots(figsize=(8, 5))

    for idx, payload in enumerate(PAYLOADS):
        subset = gi_data[gi_data["Payload"] == payload].sort_values("STAs")
        if subset.empty:
            continue
        ax.plot(
            subset["STAs"],
            subset["Throughput"],
            marker="o",
            linewidth=2,
            markersize=7,
            color=COLORS[idx],
            label=f"{payload} bytes"
        )

    ax.set_title(f"Throughput vs Number of Stations\nGuard Interval = {gi_label}", fontsize=13, fontweight="bold")
    ax.set_xlabel("Number of Stations", fontsize=12)
    ax.set_ylabel("Throughput (Mbps)", fontsize=12)
    ax.set_xticks(STATIONS)
    ax.legend(title="Payload Size", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    fname = os.path.join(OUTPUT_FOLDER, f"Fig_Throughput_GI{gi}.png")
    plt.savefig(fname, dpi=150)
    plt.close()
    print(f"✅ Saved: {fname}")

    # ── Figure B: MAC Delay vs Number of Stations ─────────────────────
    fig, ax = plt.subplots(figsize=(8, 5))

    for idx, payload in enumerate(PAYLOADS):
        subset = gi_data[gi_data["Payload"] == payload].sort_values("STAs")
        if subset.empty:
            continue
        ax.plot(
            subset["STAs"],
            subset["MACDelay"],
            marker="s",
            linewidth=2,
            markersize=7,
            color=COLORS[idx],
            label=f"{payload} bytes"
        )

    ax.set_title(f"MAC Delay vs Number of Stations\nGuard Interval = {gi_label}", fontsize=13, fontweight="bold")
    ax.set_xlabel("Number of Stations", fontsize=12)
    ax.set_ylabel("MAC Delay (ms)", fontsize=12)
    ax.set_xticks(STATIONS)
    ax.legend(title="Payload Size", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    fname = os.path.join(OUTPUT_FOLDER, f"Fig_MACDelay_GI{gi}.png")
    plt.savefig(fname, dpi=150)
    plt.close()
    print(f"✅ Saved: {fname}")

print("\n🎉 All 6 figures generated successfully in the 'figures/' folder!")