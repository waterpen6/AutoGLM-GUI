"""Application configuration singleton."""

import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    """Global application configuration."""

    base_url: str = ""
    model_name: str = "autoglm-phone-9b"
    api_key: str = "EMPTY"

    def refresh_from_env(self):
        """从环境变量刷新配置（适用于 reload 模式）"""
        self.base_url = os.getenv("AUTOGLM_BASE_URL", self.base_url)
        self.model_name = os.getenv("AUTOGLM_MODEL_NAME", self.model_name)
        self.api_key = os.getenv("AUTOGLM_API_KEY", self.api_key)


# Global singleton instance
config = AppConfig()
