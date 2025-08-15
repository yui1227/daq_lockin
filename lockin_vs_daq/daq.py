import nidaqmx
from nidaqmx.constants import AcquisitionType, TerminalConfiguration
import numpy as np
from abc_instrument import Instrument


class DAQ(Instrument):
    """
    DAQ (Data Acquisition) 類別，繼承自 Instrument。
    用於控制數據採集儀器的行為。
    """

    def __init__(self, **kwargs):
        """
        設定DAQ名稱與通道。

        Args:
            DAQ_NAME: DAQ的名字，如Dev1，參考nidaqmx。
            DAQ_CHANNEL: DAQ的通道號，如ai0。
        """
        super().__init__()
        self.config = kwargs
        self.DAQ_NAME = kwargs.get('DAQ_NAME')
        self.DAQ_CHANNEL = kwargs.get('DAQ_CHANNEL')
        self.task = nidaqmx.Task()

    def set_real_time_acquisition_params(self, **params):
        """
        設定即時資料擷取的參數。

        Args:
            SAMPLE_RATE: 取樣率(Hz)。
            SAMPLES_PER_READ: 每次讀取點數。
        """
        self.SAMPLE_RATE = params.get('SAMPLE_RATE')       # 每秒採樣點數
        self.SAMPLES_PER_READ = params.get(
            'SAMPLES_PER_READ')   # 每次從 DAQ 讀取的數據點數
        self.task = nidaqmx.Task()
        self.task.ai_channels.add_ai_voltage_chan(
            f"{self.DAQ_NAME}/{self.DAQ_CHANNEL}")
        # 配置採樣時序
        self.task.timing.cfg_samp_clk_timing(
            rate=self.SAMPLE_RATE,
            sample_mode=AcquisitionType.CONTINUOUS,  # 連續採樣
            samps_per_chan=self.SAMPLES_PER_READ  # 每次讀取點數
        )

    def acquire_real_time_data(self) -> float | np.ndarray:
        """
        獲取即時資料
        """
        new_data = self.task.read(
            number_of_samples_per_channel=self.SAMPLES_PER_READ)
        if not isinstance(new_data, (list, np.ndarray)):
            new_data = [new_data]
        new_data = np.array(new_data)
        return new_data

    def close_task(self):
        if self.task:
            try:
                self.task.stop()
                self.task.close()
                print("DAQ Task closed.")
            except Exception as e:
                print(f"Error closing DAQ task: {e}")
            self.task = None

    def set_timed_acquisition_params(self, **params):
        """
        設定定時資料擷取的參數。

        Args:
            SAMPLE_RATE: 取樣率(Hz)。
            SAMPLES_PER_READ: 每次讀取點數。
        """
        self.SAMPLE_RATE = params.get("SAMPLE_RATE")             # 採樣率 (Hz)
        self.MEASUREMENT_DURATION = params.get(
            "MEASUREMENT_DURATION")     # 量測持續時間 (秒)

        # 計算需要採集的總樣本數
        self.number_of_samples = int(
            self.SAMPLE_RATE * self.MEASUREMENT_DURATION)
        self.task = nidaqmx.Task()
        self.task.timing.cfg_samp_clk_timing(
            rate=self.SAMPLE_RATE,
            sample_mode=AcquisitionType.FINITE,
            samps_per_chan=self.number_of_samples
        )

    def acquire_timed_data(self) -> np.ndarray:
        """
        定時資料擷取。
        """
        # 啟動 Task
        self.task.start()

        # 等待數據採集完成
        print("\n開始量測... 請稍候...")
        self.task.wait_until_done(
            timeout=self.MEASUREMENT_DURATION + 2.0)  # 給予額外的時間裕度

        # 讀取所有採集到的數據
        acquired_data = self.task.read(
            number_of_samples_per_channel=self.number_of_samples)

        # 將數據轉換為 numpy 陣列，方便後續處理
        data_array = np.array(acquired_data)
        return data_array
