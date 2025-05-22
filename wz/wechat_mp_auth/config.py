"""
微信公众平台认证模块的配置管理
"""
import os
from pathlib import Path

# 默认数据目录相对路径
DEFAULT_DATA_DIR = "data"

# 默认凭据文件名(不含扩展名)
DEFAULT_ID_INFO_FILENAME = "id_info"

# 配置项类
class Config:
    """配置管理类，存储模块运行所需的各种配置项"""
    
    def __init__(self, data_dir=None, id_info_filename=None):
        """
        初始化配置
        
        参数:
            data_dir (str): 数据目录路径，默认为WZ/data
            id_info_filename (str): 凭据信息文件名，默认为id_info
        """
        # 获取WZ目录的路径
        self.wz_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        # 设置数据目录
        if data_dir:
            self.data_dir = Path(data_dir)
        else:
            self.data_dir = self.wz_dir / DEFAULT_DATA_DIR
        
        # 确保数据目录存在
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 设置凭据文件名
        self.id_info_filename = id_info_filename or DEFAULT_ID_INFO_FILENAME
        
        # 完整的凭据文件路径
        self.id_info_path = self.data_dir / f"{self.id_info_filename}.json"
    
    def get_id_info_path(self):
        """获取凭据信息文件的完整路径"""
        return self.id_info_path
    
    def get_data_dir(self):
        """获取数据目录路径"""
        return self.data_dir

# 默认配置实例
default_config = Config() 