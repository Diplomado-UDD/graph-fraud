#!/usr/bin/env python3
"""Generate contextual plots for the MARP presentation.

Produces:
 - docs/images/risk_hist.png
 - docs/images/top_users.png
 - docs/images/device_sharing.png

This script uses only common plotting libs available in the repo venv (matplotlib, pandas).
"""
import sys
from pathlib import Path
import glob
import pandas as pd
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / 'docs' / 'images'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Ensure repo root is on sys.path so `import config` works when running the script directly
sys.path.insert(0, str(ROOT))
import config


def latest_risk_file():
    files = sorted(glob.glob(str(ROOT / 'outputs' / 'risk_scores_*.csv')))
    if not files:
        raise FileNotFoundError('No risk_scores CSV found in outputs/')
    return files[-1]


def check_inputs():
    """Check that required input files exist and print friendly messages if not."""
    missing = []
    # check outputs risk file
    files = sorted(glob.glob(str(ROOT / 'outputs' / 'risk_scores_*.csv')))
    if not files:
        missing.append("No risk_scores CSV found in 'outputs/'. Run the training or batch_scoring scripts first.")

    # check raw data files
    required = ['users.csv', 'devices.csv', 'user_devices.csv', 'transactions.csv']
    missing_raw = [f for f in required if not (ROOT / 'data' / 'raw' / f).exists()]
    if missing_raw:
        missing.append(f"Missing raw data files under data/raw/: {', '.join(missing_raw)}")

    if missing:
        print('\nInput check failed:')
        for m in missing:
            print(' -', m)
        print("\nTo fix: ensure the dataset is generated (see docs/REPRODUCE.md) or run scripts/generate_data.py / training pipeline to create the outputs.")
        sys.exit(3)


def plot_risk_hist(df):
    plt.figure(figsize=(6,4))
    scores = df['risk_score'].clip(0,1)
    plt.hist(scores, bins=20, color='#2b8cbe', edgecolor='k')
    # mark risk threshold
    try:
        thr = config.RISK_THRESHOLD
        plt.axvline(thr, color='red', linestyle='--', linewidth=1)
        plt.text(thr + 0.01, plt.gca().get_ylim()[1]*0.9, f'Threshold={thr}', color='red')
    except Exception:
        pass
    plt.title('Distribution of risk scores')
    plt.xlabel('Risk score')
    plt.ylabel('Number of users')
    plt.grid(axis='y', alpha=0.4)
    p = OUT_DIR / 'risk_hist.png'
    plt.tight_layout()
    plt.savefig(p, dpi=150)
    plt.close()
    print('Wrote', p)


def plot_top_users(df, n=10):
    top = df.sort_values('risk_score', ascending=False).head(n)
    plt.figure(figsize=(6,4))
    bars = plt.barh(top['user_id'].astype(str)[::-1], top['risk_score'][::-1], color='#f46d43')
    plt.xlabel('Risk score')
    plt.title(f'Top {n} highest-risk users')
    # annotate bar values
    for bar in bars:
        w = bar.get_width()
        plt.text(w + 0.005, bar.get_y() + bar.get_height()/2, f'{w:.2f}', va='center')
    # highlight the top user
    try:
        top_user = str(top.iloc[0]['user_id'])
        plt.gca().yaxis.get_ticklabels()[-1].set_weight('bold')
    except Exception:
        pass
    plt.tight_layout()
    p = OUT_DIR / 'top_users.png'
    plt.savefig(p, dpi=150)
    plt.close()
    print('Wrote', p)


def plot_device_sharing():
    # Read user_devices to compute how many users share the same device
    ud = pd.read_csv(ROOT / 'data' / 'raw' / 'user_devices.csv')
    # columns expected: user_id, device_id
    counts = ud.groupby('device_id')['user_id'].nunique().sort_values(ascending=False)
    top = counts.head(10)
    plt.figure(figsize=(6,4))
    plt.barh(top.index.astype(str)[::-1], top.values[::-1], color='#7fc97f')
    plt.xlabel('Number of distinct users')
    plt.title('Top devices by number of associated users')
    plt.tight_layout()
    p = OUT_DIR / 'device_sharing.png'
    plt.savefig(p, dpi=150)
    plt.close()
    print('Wrote', p)


def main():
    try:
        file = latest_risk_file()
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    df = pd.read_csv(file)
    # Ensure required columns exist
    if 'risk_score' not in df.columns or 'user_id' not in df.columns:
        print('risk_scores CSV missing expected columns')
        sys.exit(1)

    plot_risk_hist(df)
    plot_top_users(df, n=10)
    try:
        plot_device_sharing()
    except Exception as e:
        print('Could not plot device sharing (missing file or columns):', e)


if __name__ == '__main__':
    main()
