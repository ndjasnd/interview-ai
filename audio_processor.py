"""
音频处理工具
职责：音频重采样、归一化、格式转换
"""

import numpy as np
from dataclasses import dataclass
from typing import Literal

from config import INT16_MAX


@dataclass
class AudioChunk:
    """音频数据块 - 清晰的数据结构"""
    source: Literal['speaker', 'microphone']
    audio_data: np.ndarray  # float32 格式，归一化到 [-1, 1]
    timestamp: float
    duration: float


class AudioProcessor:
    """音频处理器 - 无状态工具类"""
    
    @staticmethod
    def resample(audio_data: np.ndarray, original_rate: int, target_rate: int) -> np.ndarray:
        """
        线性重采样
        
        注意：这是简单实现，生产环境应使用 librosa 或 scipy
        但对于语音识别场景足够了
        """
        if original_rate == target_rate:
            return audio_data
        
        duration = len(audio_data) / original_rate
        target_length = int(duration * target_rate)
        
        indices = np.linspace(0, len(audio_data) - 1, target_length)
        resampled = np.interp(indices, np.arange(len(audio_data)), audio_data)
        
        return resampled.astype(audio_data.dtype)
    
    @staticmethod
    def to_mono(audio_data: np.ndarray, channels: int) -> np.ndarray:
        """
        转换为单声道 - 只取第一个通道
        
        为什么只取第一个通道而不是平均？
        1. 对于虚拟音频设备，所有通道通常是相同的
        2. 更快，无需额外计算
        3. 对语音识别结果没有实质影响
        """
        if channels == 1:
            return audio_data
        
        return audio_data.reshape(-1, channels)[:, 0]
    
    @staticmethod
    def normalize(audio_data: np.ndarray) -> np.ndarray:
        """
        归一化到 [-1, 1]
        输入：int16 格式
        输出：float32 格式
        """
        return audio_data.astype(np.float32) / INT16_MAX
    
    @staticmethod
    def calculate_volume(audio_data: np.ndarray) -> float:
        """
        计算音量（归一化后的最大绝对值）
        """
        return float(abs(audio_data).max())
    
    @staticmethod
    def is_silent(audio_data: np.ndarray, threshold: float) -> bool:
        """
        检测是否为静音
        """
        volume = AudioProcessor.calculate_volume(audio_data)
        return volume < threshold
    
    @staticmethod
    def validate_audio(audio_data: np.ndarray) -> bool:
        """
        验证音频数据是否有效
        
        Returns:
            True if valid, False otherwise
        """
        if audio_data is None or len(audio_data) == 0:
            return False
        
        if np.isnan(audio_data).any() or np.isinf(audio_data).any():
            return False
        
        return True

