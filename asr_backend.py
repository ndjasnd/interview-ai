"""
腾讯云 ASR 后端
使用腾讯云实时语音识别 API
"""

import numpy as np
from typing import Optional


class TencentASR:
    """
    腾讯云 ASR 后端
    使用腾讯云实时语音识别 API
    """
    
    def __init__(self, secret_id: str, secret_key: str, app_id: str,
                 engine_model_type: str = "16k_zh", region: str = "ap-shanghai"):
        """
        初始化腾讯云 ASR
        
        Args:
            secret_id: 腾讯云 SecretId
            secret_key: 腾讯云 SecretKey
            app_id: 腾讯云 AppId
            engine_model_type: 引擎模型类型
            region: 地域
        """
        print("初始化腾讯云 ASR...")
        
        # 检查 API key
        if secret_id == "YOUR_SECRET_ID_HERE" or not secret_id:
            raise ValueError(
                "请在 config.py 中配置腾讯云 SecretId！\n"
                "获取地址: https://console.cloud.tencent.com/cam/capi"
            )
        
        if secret_key == "YOUR_SECRET_KEY_HERE" or not secret_key:
            raise ValueError(
                "请在 config.py 中配置腾讯云 SecretKey！\n"
                "获取地址: https://console.cloud.tencent.com/cam/capi"
            )
        
        if app_id == "YOUR_APP_ID_HERE" or not app_id:
            raise ValueError(
                "请在 config.py 中配置腾讯云 AppId！\n"
                "获取地址: https://console.cloud.tencent.com/asr"
            )
        
        # 条件导入：只在使用腾讯云时才导入 SDK（关键！）
        try:
            from tencentcloud.common import credential
            from tencentcloud.common.profile.client_profile import ClientProfile
            from tencentcloud.common.profile.http_profile import HttpProfile
            from tencentcloud.asr.v20190614 import asr_client
        except ImportError:
            raise ImportError(
                "请先安装腾讯云 SDK:\n"
                "pip install tencentcloud-sdk-python"
            )
        
        # 创建认证对象
        cred = credential.Credential(secret_id, secret_key)
        
        # 配置 HTTP 选项
        httpProfile = HttpProfile()
        httpProfile.endpoint = "asr.tencentcloudapi.com"
        
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        
        # 创建客户端
        self.client = asr_client.AsrClient(cred, region, clientProfile)
        self.engine_model_type = engine_model_type
        self.app_id = app_id
        
        print(f"  地域: {region}")
        print(f"  模型: {engine_model_type}")
        print("✓ 腾讯云 ASR 初始化完成")
    
    def recognize(self, audio_data: np.ndarray) -> Optional[str]:
        """
        调用腾讯云 API 识别
        
        使用一句话识别（适合短音频）
        """
        try:
            from tencentcloud.asr.v20190614 import models
            import base64
            import io
            import wave
            
            # 将 float32 音频转为 16bit PCM WAV
            audio_int16 = (audio_data * 32768).astype(np.int16)
            
            # 写入 WAV 格式的内存缓冲区
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16bit
                wav_file.setframerate(16000)  # 16kHz
                wav_file.writeframes(audio_int16.tobytes())
            
            # 获取 WAV 数据并 Base64 编码
            wav_data = wav_buffer.getvalue()
            audio_base64 = base64.b64encode(wav_data).decode('utf-8')
            
            # 构造请求
            req = models.SentenceRecognitionRequest()
            
            # 设置参数
            params = {
                "ProjectId": 0,
                "SubServiceType": 2,  # 一句话识别
                "EngSerViceType": self.engine_model_type,
                "SourceType": 1,  # 语音数据来源，1 表示音频 URL，0 表示音频数据（此处实际用 Data 字段）
                "VoiceFormat": "wav",
                "UsrAudioKey": "session_" + str(int(np.random.random() * 1000000)),
                "Data": audio_base64,  # Base64 编码的音频数据
            }
            req.from_json_string(str(params).replace("'", '"'))
            
            # 发送请求
            resp = self.client.SentenceRecognition(req)
            
            # 解析结果
            result = resp.Result
            if result:
                return result.strip()
            
            return None
        
        except Exception as e:
            print(f"❌ 腾讯云识别失败: {e}")
            # 不打印完整堆栈，避免刷屏
            return None
    
    def close(self):
        """释放资源"""
        self.client = None

