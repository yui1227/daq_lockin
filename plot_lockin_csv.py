"""
進階檔案: 使用 pandas 讀取 lockin 比較用的 CSV 並繪圖
- 手動定義 TC (時間常數) 與 FS (取樣率)
- 自動移除頭尾 5*TC 的尖波 (Transient Response)
- 顯示振幅 (R) 與相位 (Theta) 的時間序列比較圖
"""
import sys
import os
import glob
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# ==========================================
# 手動設定區：請在此修改你的實驗參數
# ==========================================
TC = 0.001       # 時間常數 (Time Constant, 單位: 秒)
FS = 10000       # 取樣率 (Sampling Rate, 單位: Hz)
# ==========================================


def load_lockin_csv(path):
    """單純讀取 CSV 資料"""
    df = pd.read_csv(path, comment='#', encoding='utf-8')
    df.columns = [str(c).strip() for c in df.columns]
    return df


def find_columns(df):
    cols = list(df.columns)

    def find(prefix):
        t = next((c for c in cols if prefix in c and 'Time' in c), None)
        r = next((c for c in cols if prefix in c and (
            'R(' in c or 'R' in c and 'Time' not in c)), None)
        th = next((c for c in cols if prefix in c and 'Theta' in c), None)
        return t, r, th

    soft = find('Soft')
    hard = find('Hard')
    return soft, hard


def to_numeric_series(df, col):
    if col is None or col not in df.columns:
        return None
    return pd.to_numeric(df[col], errors='coerce')


def trim_edge_effects(t, r, th, tc_val, fs_val):
    """
    根據 5*TC 邏輯切除頭尾尖波
    """
    if t is None or r is None or len(t) < 10:
        return t, r, th

    # 計算要切掉的點數 (5倍時間常數)
    settling_factor = 5
    n_cut = int(settling_factor * tc_val * fs_val)

    # 執行切片
    if n_cut > 0 and (2 * n_cut) < len(t):
        print(f"手動設定 TC={tc_val}s, FS={fs_val}Hz: 自動切除頭尾各 {n_cut} 點 (邊界修正)")
        return t.iloc[n_cut:-n_cut], r.iloc[n_cut:-n_cut], th.iloc[n_cut:-n_cut]

    return t, r, th


def plot_from_df(df, tc_val, fs_val, path=None):
    soft_cols, hard_cols = find_columns(df)

    # 讀取數據
    s_t = to_numeric_series(df, soft_cols[0])
    s_r = to_numeric_series(df, soft_cols[1])
    s_th = to_numeric_series(df, soft_cols[2])

    h_t = to_numeric_series(df, hard_cols[0])
    h_r = to_numeric_series(df, hard_cols[1])
    h_th = to_numeric_series(df, hard_cols[2])

    # --- 執行邊界切除 (使用上方定義的常數) ---
    s_t, s_r, s_th = trim_edge_effects(s_t, s_r, s_th, tc_val, fs_val)
    h_t, h_r, h_th = trim_edge_effects(h_t, h_r, h_th, tc_val, fs_val)

    plt.figure(figsize=(12, 9))

    # 1. 振幅比較 (Amplitude)
    ax1 = plt.subplot(2, 1, 1)
    if s_t is not None and s_r is not None:
        mask = s_t.notna() & s_r.notna()
        mean_v = s_r[mask].mean()
        ax1.plot(s_t[mask], s_r[mask],
                 label=f'Software (Mean: {mean_v:.4f}V)', color='blue', linewidth=1, alpha=0.6)
    if h_t is not None and h_r is not None:
        mask = h_t.notna() & h_r.notna()
        mean_v = h_r[mask].mean()
        ax1.plot(h_t[mask], h_r[mask],
                 label=f'Hardware (Mean: {mean_v:.4f}V)', color='orange', linewidth=1, alpha=0.8)

    ax1.set_ylabel('Amplitude R (V)')
    ax1.grid(True, linestyle='--', alpha=0.6)
    ax1.legend(loc='upper right')

    # 2. 相位比較 (Phase)
    ax2 = plt.subplot(2, 1, 2)
    if s_t is not None and s_th is not None:
        mask = s_t.notna() & s_th.notna()
        ax2.plot(s_t[mask], s_th[mask], label='Software',
                 color='blue', linewidth=1, alpha=0.6)
    if h_t is not None and h_th is not None:
        mask = h_t.notna() & h_th.notna()
        ax2.plot(h_t[mask], h_th[mask], label='Hardware',
                 color='orange', linewidth=1, alpha=0.8)

    ax2.set_ylabel('Phase Theta (deg)')
    ax2.set_xlabel('Time (s)')
    ax2.set_ylim(-180, 180)
    ax2.grid(True, linestyle='--', alpha=0.6)
    ax2.legend(loc='upper right')

    plt.tight_layout()
    title = 'Lock-in Data Analysis'
    if path:
        title += f" File: {os.path.basename(path)}"
    title += f' (TC: {tc_val}s, FS: {fs_val}Hz)'
    plt.suptitle(title, fontsize=12)
    plt.show()


if __name__ == '__main__':
    if len(sys.argv) >= 2:
        filename = sys.argv[1]
    else:
        # 找最新的 lockin_compare_*.csv
        files = glob.glob(os.path.join(os.path.dirname(
            __file__) or '.', 'lockin_compare_*.csv'))
        if not files:
            print('找不到 CSV 檔案。')
            sys.exit(1)
        files.sort(key=os.path.getmtime, reverse=True)
        filename = files[0]

    print(f'讀取檔案: {filename}')
    df_data = load_lockin_csv(filename)
    plot_from_df(df_data, TC, FS, filename)
