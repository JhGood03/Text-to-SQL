from pathlib import Path


def load_prompt(file_name):
    """
    根据文件名加载提示文本内容
    参数:
        file_name (str): 提示词文本文件的名称
    返回:
        str: 提示文本文件的内容
    说明:
        该函数会从项目根目录下的prompts文件夹中加载指定名称的文件
    """
    # 构建提示文本文件的完整路径
    # __file__表示当前文件路径，parents[2]表示向上两级目录
    prompt_path = Path(__file__).parents[2] / "prompts" / f"{file_name}.prompt"
    # 读取并返回文件内容，使用utf-8编码
    prompt = prompt_path.read_text(encoding="utf-8")

    return prompt



if __name__ == '__main__':
    prompt1 = load_prompt("extend_keywords_for_column_recall")
    print(prompt1)