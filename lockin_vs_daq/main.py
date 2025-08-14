import threading
import time
import numpy as np

def worker_thread(event:threading.Event, results:list, thread_id):
    """
    子線程工作函數：等待訊號後執行任務並回傳結果。
    """
    print(f"Thread {thread_id}: 等待主線程發出訊號...")
    event.wait() # 阻塞，直到收到訊號
    print(f"Thread {thread_id}: 收到訊號，開始工作...")
    
    # 這裡執行實際的任務
    time.sleep(1) # 模擬耗時的 I/O 操作
    result = f"Thread {thread_id} 的工作已完成，結果為 {thread_id * 5}"
    
    # 使用鎖來確保資料安全
    with lock:
        results.append(result)
        
    print(f"Thread {thread_id}: 任務完成，結果已回傳。")

def main_threading():
    """
    主線程：創建子線程，發出訊號，並收集結果。
    """
    # 創建一個 Event 物件，用來同步
    event = threading.Event()
    
    # 創建一個 Lock 物件，用來保護共用資料
    global lock
    lock = threading.Lock()
    
    # 創建一個列表，用來收集所有線程的結果
    results = []
    
    threads = []
    num_threads = 2
    
    # 創建並啟動子線程
    for i in range(num_threads):
        t = threading.Thread(target=worker_thread, args=(event, results, i+1))
        threads.append(t)
        t.start()
        
    print("\n主線程: 所有子線程已啟動，等待幾秒鐘後發出訊號...")
    time.sleep(2) # 模擬一些準備工作
    
    print("\n主線程: 發出訊號！")
    event.set() # 發出訊號，讓所有子線程開始執行
    
    # 等待所有子線程完成
    for t in threads:
        t.join()
        
    print("\n主線程: 所有子線程已結束，開始收集結果...")
    
    print("收集到的結果:")
    for res in results:
        print(f"- {res}")
        
    print("\n主線程: 任務完成。")

if __name__ == "__main__":
    print("--- 執行 threading 範例 ---")
    main_threading()