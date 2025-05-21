import json
import shutil
from pathlib import Path

def handle_json(file_name, data=None, base_path='data'):
    """处理 JSON 文件的读取和安全写入。

    Args:
        file_name (str): JSON 文件名 (不含.json后缀，除非已包含完整路径)。
        data (dict, optional): 要写入的数据。如果为 None，则为读取模式。
        base_path (str): JSON 文件存放的基础目录名，默认为 'data'。

    Returns:
        dict or None: 读取时返回解析后的字典，写入时无返回值。
                      如果文件不存在且为读取模式，则返回空字典。
    """
    # 构造文件路径，使其相对于当前脚本的父目录下的 base_path
    current_script_path = Path(__file__).parent
    # 如果 file_name 已经是绝对路径或包含路径分隔符，则直接使用
    if Path(file_name).is_absolute() or Path(file_name).parent != Path('.'):
        target_file_path = Path(file_name)
    else:
        # 否则，认为是相对于 base_path 的文件名
        # 我们需要 WZ/data/file_name.json
        # current_script_path 是 WZ/utils/
        # current_script_path.parent 是 WZ/
        # current_script_path.parent / base_path 是 WZ/data/
        target_file_path = current_script_path.parent / base_path / f'{file_name}.json'

    if not data:
        # 读取模式
        if not target_file_path.exists():
            return {}
        try:
            with open(target_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"错误: 文件 {target_file_path} 不是有效的JSON格式。")
            return {}
    else:
        # 写入模式
        # 确保目标目录存在
        target_file_path.parent.mkdir(parents=True, exist_ok=True)

        # 安全写入，防止在写入过程中中断程序导致数据丢失
        temp_file_path = target_file_path.with_suffix('.json.tmp')
        try:
            with open(temp_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            shutil.move(temp_file_path, target_file_path)
        except Exception as e:
            print(f"写入JSON文件 {target_file_path} 失败: {e}")
        finally:
            if temp_file_path.exists():
                temp_file_path.unlink() # 删除临时文件 