# DAQ Lockin

本專案為資料擷取與鎖相放大器相關工具。

## 環境建立

建議使用 [uv](https://github.com/astral-sh/uv) 來建立 Python 環境。

### 步驟

1. 安裝 uv（如尚未安裝）：
    ```bash
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

2. 建立虛擬環境並安裝依賴：
    ```bash
    uv venv
    uv pip install -r requirements.txt
    ```

3. 啟動虛擬環境：
    ```bash
    .venv\Scripts\activate
    ```

## 使用方式

請參考 `main.py` 或相關文件以瞭解如何執行本專案。

## 需求

- Python 3.8+