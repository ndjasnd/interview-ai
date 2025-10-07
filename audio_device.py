"""
音频设备检测和管理
职责：检测虚拟音频设备和麦克风，选择最佳设备
"""

import pyaudio
from dataclasses import dataclass
from typing import Optional, List, Tuple


@dataclass
class DeviceInfo:
    """设备信息 - 用 dataclass 而不是字典，类型安全"""
    index: int
    name: str
    channels: int
    sample_rate: int
    priority: int


class AudioDeviceManager:
    """音频设备管理器 - 单一职责"""
    
    # 设备类型关键字（优先级从高到低）
    SPEAKER_KEYWORDS = {
        'blackhole': 100,
        'loopback': 90,
        'soundflower': 50,
        'virtual': 50,
        'aggregate': 50
    }
    
    MICROPHONE_KEYWORDS = {
        'built-in': 100,
        'microphone': 80,
        'internal': 80,
        'usb': 80
    }
    
    @staticmethod
    def list_all_devices() -> Tuple[List[DeviceInfo], List[DeviceInfo]]:
        """
        列出所有可用的音频输入设备
        
        Returns:
            (speaker_devices, microphone_devices)
        """
        p = pyaudio.PyAudio()
        print("\n=== 可用音频输入设备 ===")
        
        speaker_devices = []
        microphone_devices = []
        
        info = p.get_host_api_info_by_index(0)
        numdevices = info.get('deviceCount')
        
        for i in range(numdevices):
            try:
                device_info = p.get_device_info_by_host_api_device_index(0, i)
                if device_info.get('maxInputChannels') <= 0:
                    continue
                
                name = device_info.get('name')
                channels = device_info.get('maxInputChannels')
                sample_rate = int(device_info.get('defaultSampleRate'))
                
                print(f"\n设备 {i}: {name}")
                print(f"  通道数: {channels}")
                print(f"  采样率: {sample_rate} Hz")
                
                # 检测设备类型
                device_type, priority = AudioDeviceManager._detect_device_type(name)
                
                device = DeviceInfo(
                    index=i,
                    name=name,
                    channels=channels,
                    sample_rate=sample_rate,
                    priority=priority
                )
                
                if device_type == 'speaker':
                    speaker_devices.append(device)
                    print(f"  🔊 虚拟音频设备（捕获扬声器）")
                elif device_type == 'microphone':
                    microphone_devices.append(device)
                    print(f"  🎙️  麦克风设备")
                else:
                    microphone_devices.append(device)
                    print(f"  ❓ 未知输入设备（可能是麦克风）")
                    
            except Exception as e:
                print(f"  ⚠️  无法读取设备 {i}: {e}")
        
        p.terminate()
        return speaker_devices, microphone_devices
    
    @staticmethod
    def _detect_device_type(device_name: str) -> Tuple[str, int]:
        """
        检测设备类型
        
        Returns:
            (device_type, priority) where device_type in ['speaker', 'microphone', 'unknown']
        """
        name_lower = device_name.lower()
        
        # 检查是否为扬声器设备
        for keyword, priority in AudioDeviceManager.SPEAKER_KEYWORDS.items():
            if keyword in name_lower:
                return ('speaker', priority)
        
        # 检查是否为麦克风设备
        for keyword, priority in AudioDeviceManager.MICROPHONE_KEYWORDS.items():
            if keyword in name_lower:
                return ('microphone', priority)
        
        # 未知设备，默认当作麦克风，低优先级
        return ('unknown', 30)
    
    @staticmethod
    def get_best_devices() -> Tuple[Optional[DeviceInfo], Optional[DeviceInfo]]:
        """
        自动选择最佳的扬声器和麦克风设备
        
        Returns:
            (speaker_device, microphone_device)
        """
        speaker_devices, microphone_devices = AudioDeviceManager.list_all_devices()
        
        # 检查扬声器设备（必需）
        if not speaker_devices:
            AudioDeviceManager._print_setup_instructions()
            return None, None
        
        # 选择最佳扬声器设备（按优先级排序）
        speaker_devices.sort(key=lambda x: x.priority, reverse=True)
        speaker_device = speaker_devices[0]
        
        print(f"\n✓ 扬声器捕获设备: {speaker_device.name} (索引 {speaker_device.index})")
        print(f"  采样率: {speaker_device.sample_rate} Hz → 将重采样到 16000 Hz")
        
        # 选择最佳麦克风设备
        microphone_device = None
        if microphone_devices:
            microphone_devices.sort(key=lambda x: x.priority, reverse=True)
            microphone_device = microphone_devices[0]
            print(f"\n✓ 麦克风捕获设备: {microphone_device.name} (索引 {microphone_device.index})")
            print(f"  采样率: {microphone_device.sample_rate} Hz → 将重采样到 16000 Hz")
        else:
            print("\n⚠️  未找到麦克风设备，将只捕获扬声器")
        
        return speaker_device, microphone_device
    
    @staticmethod
    def _print_setup_instructions():
        """打印 macOS 设置说明"""
        print("\n❌ 未找到虚拟音频设备（用于捕获扬声器）！")
        print("\n【macOS 配置步骤】")
        print("1. 安装 BlackHole:")
        print("   brew install blackhole-2ch")
        print("   或从官网下载: https://existential.audio/blackhole/")
        print("\n2. 配置音频路由:")
        print("   a. 打开「音频 MIDI 设置」(Audio MIDI Setup)")
        print("   b. 点击左下角 「+」，选择「创建多输出设备」")
        print("   c. 勾选「内建输出」和「BlackHole 2ch」")
        print("   d. 在「系统偏好设置 > 声音」中选择这个多输出设备")
        print("\n3. 重新运行此程序")

