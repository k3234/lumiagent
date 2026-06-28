import time       # 导入时间模块，用于sleep延时
import json       # 导入JSON模块，用于构造和解析JSON数据
import requests   # 导入HTTP请求库，用于调用Ollama API


class LumiAgent:
    """LumiAgent类：为老旧设备而生的AI编程调度器"""

    def __init__(self):
        """初始化方法：设置Ollama API的地址"""
        # ⚠️ 使用前请修改：将地址改为你的 Ollama 服务地址（默认 http://localhost:11434）
        self.url = "http://192.168.2.137:11434/api/generate"  # Ollama本地API地址
        # ⚠️ 使用前请修改：将模型名改为你已拉取的模型（如 qwen2.5:7b / llama3.2:1b 等）
        self.model = "deepseek-r1:1.5b"  # 默认模型：deepseek-r1:1.5b（约 4GB 内存）

    def process(self, user_input):
        """处理用户输入：发送请求到Ollama，解析并返回回答"""
        # 构造JSON请求体：包含模型名、用户问题和是否流式输出
        payload = {
            "model": self.model,  # 指定要调用的模型
            "prompt": user_input,  # 用户的输入问题
            "stream": False  # 关闭流式输出，等待完整响应
        }
        try:
            # 发送POST请求，超时时间设为60秒
            response = requests.post(self.url, json=payload, timeout=60)
            # 解析返回的JSON数据
            data = response.json()
            # 提取response字段，即模型的回答内容
            return data.get("response", "未获取到回答")
        except requests.exceptions.ConnectionError:
            # 捕获连接失败的异常：Ollama服务未启动或地址错误
            return "错误：无法连接到Ollama，请确认服务已启动"
        except json.JSONDecodeError:
            # 捕获JSON解析失败的异常：返回内容不是合法JSON
            return "错误：收到无效的响应数据"
        except Exception:
            # 捕获其他所有未预期的异常，防止程序崩溃
            return "错误：请求处理时发生未知问题"

    def rest(self):
        """休息机制：等待30秒后打印休眠提示，模拟卸载模型释放内存"""
        print("\n💤 为节省资源，Agent进入休眠状态...")  # 提示进入休眠
        time.sleep(30)  # 暂停30秒，让老旧设备喘息
        print("✓ 模型已卸载，内存已释放 — 你的设备辛苦了")  # 提示休眠结束


def main():
    """主函数：CLI交互循环，接收输入、调用process和rest"""
    # 打印体现算力平权理念的欢迎语，标注 LumiAI-Ecosystem
    print("=" * 50)
    print("  LumiAgent — LumiAI-Ecosystem 调度核心")
    print("  算力平权，让老设备也能用AI")
    print("=" * 50)

    agent = LumiAgent()  # 创建LumiAgent实例

    while True:  # 无限循环，持续接收用户输入
        user_input = input("\n📝 请输入问题: ").strip()  # 读取用户输入并去除首尾空格

        if user_input.lower() in ("exit", "quit", "退出"):
            # 如果输入是退出命令，打印告别语并结束循环
            print("\n👋 再见！设备休息一下~")
            break

        # === /help 命令 ===
        if user_input.lower() == "/help":
            print("\n" + "=" * 50)
            print("  LumiAgent — LumiAI-Ecosystem 调度核心")
            print("  为老旧设备而生的AI编程调度器")
            print("=" * 50)
            print("  核心理念：算力平权，让所有设备平等获得AI编程辅助")
            print("  核心创新：休息机制 — 任务完成后卸载模型释放内存")
            print("  使用方法：")
            print("    - 直接输入编程问题，获取AI回答")
            print("    - 输入 /help 查看此帮助")
            print("    - 输入 exit / quit / 退出 结束程序")
            print("  GitHub: https://github.com/k3234/lumiagent ")
            print("  © 2026 Lumi by Kai")
            print("=" * 50)
            continue
        # ========================

        if not user_input:
            # 如果输入为空，跳过不请求模型
            continue

        # 调用process方法获取模型回答并打印
        answer = agent.process(user_input)
        print(f"\n🤖 AI: {answer}")

        # 调用rest方法进入30秒休眠
        agent.rest()


if __name__ == "__main__":
    # 当直接运行此文件时，调用main函数启动交互循环
    main()
