from abc import ABC, abstractmethod
import numpy as np

class Instrument(ABC):
    """
    儀器抽象基底類別 (Abstract Base Class)。
    
    這個類別定義了所有儀器應具備的基本功能，包含初始化、
    即時資料擷取以及一段時間的資料擷取。
    """

    def __init__(self, **kwargs):
        """
        初始化儀器。
        """
        pass

    # --- 即時資料擷取 ---
    
    @abstractmethod
    def set_real_time_acquisition_params(self, **params):
        """
        設定即時資料擷取的參數。
        
        Args:
            **params: 任意數量的參數，具體內容由子類別定義。
        """
        raise NotImplementedError

    @abstractmethod
    def acquire_real_time_data(self) -> float | np.ndarray:
        """
        即時擷取並返回單筆資料。子類別必須實作此方法。
        
        Returns:
            擷取到的單筆資料。
        """
        raise NotImplementedError

    # --- 一段時間的資料擷取 ---

    @abstractmethod
    def set_timed_acquisition_params(self, **params):
        """
        設定擷取一段時間資料的參數。
        
        Args:
            duration_s: 擷取資料的持續時間，單位為秒。
            **params: 任意數量的參數，具體內容由子類別定義。
        """
        raise NotImplementedError

    @abstractmethod
    def acquire_timed_data(self) -> np.ndarray:
        """
        在設定的時間內擷取資料。
        
        此方法會呼叫 acquire_real_time_data 並持續擷取直到時間結束。
        
        Returns:
            包含所有擷取資料的列表。
        """
        raise NotImplementedError