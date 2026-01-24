import time
import math
import numpy as np
import re
from srsinst.sr860 import SR860, Keys

class SR865AHighSpeedCapture:
    """
    Stanford Research Systems SR865A 高速數據擷取控制器
    基於官方 srsinst.sr860 程式庫封裝。
    """
    
    def __init__(self, resource_address):
        """
        初始化控制器
        :param resource_address: VISA 資源位址 (例如 'USB0::0xB506::...')
        """
        self.resource_address = resource_address
        self.inst = None
        
    def connect(self):
        """建立儀器連線"""
        try:
            self.inst = SR860()
            self.inst.connect('visa', self.resource_address)
            print(f"已連線至 SR865A: {self.inst.query_text('*IDN?').strip()}")
        except Exception as e:
            print(f"連線失敗: {e}")
            raise

    def disconnect(self):
        """關閉儀器連線"""
        if self.inst:
            try:
                self.inst.disconnect()
            except:
                pass
            self.inst = None
            print("已斷開儀器連線")

    def set_parameters(self, time_constant=None, sensitivity=None):
        """
        設定時間常數與靈敏度
        :param time_constant: 字串 (如 '100ms', '30us') 或 浮點數 (秒)
        :param sensitivity: 字串 (如 '1V', '500uV') 或 浮點數 (伏特)
        """
        if not self.inst:
            raise RuntimeError("儀器未連接")

        settle_needed = False

        if time_constant:
            if isinstance(time_constant, str):
                tc_val = self._parse_si_unit(time_constant)
            else:
                tc_val = float(time_constant)
                
            print(f"設定時間常數: {tc_val} s")
            # srsinst 會自動尋找最接近的 Key
            self.inst.signal.time_constant = tc_val
            settle_needed = True

        if sensitivity:
            if isinstance(sensitivity, str):
                sens_val = self._parse_si_unit(sensitivity)
            else:
                sens_val = float(sensitivity)
                
            print(f"設定靈敏度: {sens_val} V")
            self.inst.signal.voltage_sensitivity = sens_val
            settle_needed = True

        # 如果有更改參數，建議等待濾波器穩定
        if settle_needed:
            print("等待 1 秒讓濾波器穩定...")
            time.sleep(1.0)

    def capture(self, duration_sec, rate_index=9):
        """
        執行高速擷取 (R, Theta)
        :param duration_sec: 擷取時間 (秒)
        :param rate_index: 採樣率等級 n (0-20), Rate = MaxRate / 2^n
        :return: (time_axis, r_data, theta_data, actual_rate_hz)
        """
        if not self.inst:
            raise RuntimeError("儀器未連接")

        # 1. 停止目前的擷取
        self.inst.capture.stop()
        
        # 2. 設定擷取模式: R, Theta
        self.inst.capture.config = Keys.RT
        
        # 3. 設定採樣率
        self.inst.capture.rate_divisor_exponent = rate_index
        max_rate = self.inst.capture.max_rate
        actual_rate = max_rate / (2 ** rate_index)
        
        # 4. 計算 Buffer
        buffer_kb = self._calculate_buffer_kb(duration_sec, actual_rate)
        self.inst.capture.buffer_size_in_kilobytes = buffer_kb
        
        real_duration = (buffer_kb * 1024) / 8 / actual_rate # 8 bytes per sample (R+Theta)
        
        print(f"開始擷取: 預計 {real_duration:.4f} 秒 (Rate: {actual_rate:.2f} Hz)")

        # 5. 開始擷取 (OneShot, Immediate)
        # capture.start(run_mode, trigger_mode) -> 0=Once, 0=Immediate
        self.inst.capture.start(0, 0)
        
        # 6. 等待完成
        start_time = time.time()
        while True:
            # 檢查 Capture Status Bit 0 (In Progress)
            if not (self.inst.capture.state & 1):
                break
            
            if (time.time() - start_time) > (real_duration + 5):
                print("擷取逾時，強制停止")
                self.inst.capture.stop()
                break
            time.sleep(0.1)

        # 7. 下載數據
        print("下載數據中...")
        raw_data = self.inst.capture.get_all_data()
        
        # srsinst 回傳格式為 (columns, rows)，針對 RT 模式：
        # raw_data[0] = R array
        # raw_data[1] = Theta array
        r_data = raw_data[0]
        theta_data = raw_data[1]
        
        # 產生時間軸
        time_axis = np.arange(len(r_data)) / actual_rate
        
        return time_axis, r_data, theta_data, actual_rate

    @staticmethod
    def _calculate_buffer_kb(duration_sec, sample_rate_hz):
        """計算所需的 Buffer KB (偶數, Max 4MB)"""
        bytes_per_sample = 8 # R(4) + Theta(4)
        total_bytes = duration_sec * sample_rate_hz * bytes_per_sample
        kb_needed = math.ceil(total_bytes / 1024)
        
        if kb_needed % 2 != 0:
            kb_needed += 1
            
        return max(2, min(4096, int(kb_needed)))

    @staticmethod
    def _parse_si_unit(value_str):
        """解析帶單位的字串 (如 100ms -> 0.1)"""
        if not value_str: return None
        units = {'n': 1e-9, 'u': 1e-6, 'm': 1e-3, 'k': 1e3, 'M': 1e6, 'G': 1e9}
        
        # 簡單的正則表達式提取數值與前綴
        match = re.match(r"([0-9\.]+)\s*([a-zA-Z]*)", value_str)
        if not match:
            try:
                return float(value_str)
            except:
                raise ValueError(f"無法解析數值: {value_str}")
        
        val = float(match.group(1))
        unit_part = match.group(2)
        
        multiplier = 1.0
        if unit_part:
            prefix = unit_part[0]
            if prefix in units:
                multiplier = units[prefix]
            elif 'ms' in unit_part: # 特別修正 ms 被誤判為 m
                multiplier = 1e-3
                
        return val * multiplier