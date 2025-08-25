import threading
import time
from sr865a import SR865a
from daq import DAQ

daq_config = {
    'DAQ_NAME': 'Dev1',
    'DAQ_CHANNEL': 'ai3',
}

daq_param = {
    'SAMPLE_RATE': 39,  # 每秒採樣點數
    'MEASUREMENT_DURATION': 10  # 量測持續時間(秒)
}

sr865a_config = {
    'interface_type': 'visa',  # 或 'serial'
    'port': 'USB0::0xB506::0x2000::004937::INSTR',  # 根據實際情況修改
}

sr865a_param = {
    'time_constant': 300e-6,  # 時間常數，參考SR865a說明書
    'rate_divisor_exponent': 12,  # 速率除數指數，範圍介於0~20
    'measurement_time': 5  # 量測時間，單位為秒
}

def daq_thread(event:threading.Event, results:list, thread_id, daq_config, daq_param):
    """
    子線程工作函數：等待訊號後執行任務並回傳結果。
    """
    daq = DAQ(**daq_config)
    daq.set_timed_acquisition_params(**daq_param)
    print(f"Thread {thread_id}: 等待主線程發出訊號...")
    event.wait() # 阻塞，直到收到訊號
    print(f"Thread {thread_id}: 收到訊號，開始工作...")
    
    # 這裡執行實際的任務
    result = daq.acquire_timed_data()
    
    # 使用鎖來確保資料安全
    with lock:
        results.append(result)

    daq.close_task()
        
    print(f"Thread {thread_id}: 任務完成，結果已回傳。")

def sr865a_thread(event:threading.Event, results:list, thread_id, sr865a_config, sr865a_param):
    """
    子線程工作函數：等待訊號後執行任務並回傳結果。
    """
    sr865a = SR865a(**sr865a_config)
    sr865a.set_timed_acquisition_params(**sr865a_param)
    print(f"Thread {thread_id}: 等待主線程發出訊號...")
    event.wait() # 阻塞，直到收到訊號
    print(f"Thread {thread_id}: 收到訊號，開始工作...")
    
    # 這裡執行實際的任務
    result = sr865a.acquire_timed_data()
    
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
    daq_results = []
    sr865a_results = []
    
    threads = []

    daq_t = threading.Thread(target=daq_thread, args=(event, daq_results, 1, daq_config, daq_param))
    threads.append(daq_t)
    daq_t.start()

    sr865a_t = threading.Thread(target=sr865a_thread, args=(event, sr865a_results, 2, sr865a_config, sr865a_param))
    threads.append(sr865a_t)
    sr865a_t.start()
        
    print("\n主線程: 所有子線程已啟動，等待幾秒鐘後發出訊號...")
    print("\n主線程: 發出訊號！")
    event.set() # 發出訊號，讓所有子線程開始執行
    
    # 等待所有子線程完成
    for t in threads:
        t.join()
        
    print("\n主線程: 所有子線程已結束，開始收集結果...")
    
    print("DAQ收集到的結果:")
    for res in daq_results:
        print(f"- {res}")

    print("SR865a收集到的結果:")
    for res in sr865a_results:
        print(f"- {res}")
        
    print("\n主線程: 任務完成。")

if __name__ == "__main__":
    print("--- 執行 threading 範例 ---")
    main_threading()