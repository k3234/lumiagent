import time       # 导入时间模块，用于sleep延时
import json       # 导入JSON模块，用于构造和解析JSON数据
import requests   # 导入HTTP请求库，用于调用Ollama API


class LumiAgent:
    """LumiAgent类：为老旧设备而生的AI编程调度器"""
    
    def __init__(self):
        """初始化方法：设置Ollama API的地址"""
        self.base_url = "http://lost:11434"  # Ollama API基础地址
        self.api_url = f"{self.base_url}/api/generate"  # 生成接口URL
        self.model = "qwen2.5:0.5b-q4_K_M"  # 使用最小模型（~600MB），降低内存占用
    
    def self_check(self, response: str) -> str:
        """
        回答自检函数（V1.2 新增）
        - 纯规则匹配，不调用模型，零成本
        - 检测空回答、Python2残留语法、术语矛盾等
        - 返回：原始回答 + 可选的自检提示
        """
        warnings = []  # 存储检测到的警告信息

        # 规则1：空回答/过短回答检测 — 去除空白后长度小于5视为异常
        # 注意：用字符长度而非 split() 词数，因为中文句子没有空格分词
        if len(response.strip()) < 5:
            warnings.append("回答为空或过短，模型可能未正确响应")

        # 规则2：Python2 残留语法 — print 缺少括号
        # 检测 "print " 后面不紧跟 "(" 的情况（如 "print hello"）
        if "print " in response and "print (" not in response:
            warnings.append("检测到Python2残留语法（print缺少括号）")

        # 规则3：Python 创建方式常见错误 — 用()创建列表
        if "用()创建列表" in response or "列表用()创建" in response:
            warnings.append("检测到常见错误：Python列表应使用[]创建，不是()")

        # 规则4：术语矛盾检测 — 列表可变性前后矛盾
        if "列表可变" in response and "列表不可变" in response:
            warnings.append("关于列表可变性的表述前后矛盾")

        # 拼接警告信息
        if warnings:
            warning_text = "\n\n⚠️ 自检提示：检测到以下可能问题：\n"
            for i, w in enumerate(warnings, 1):
                warning_text += f"  {i}. {w}\n"
            return response + warning_text
        return response  # 无问题直接返回原始回答

    def process(self, user_input):
        """处理用户输入：发送请求到Ollama，解析并返回回答和长度"""
        # 构造JSON请求体：包含模型名、用户问题和是否流式输出
        payload = {
            "model": self.model,  # 指定要调用的模型
            "prompt": user_input,  # 用户的输入问题
            "stream": False  # 关闭流式输出，等待完整响应
        }
        try:
            # 发送POST请求，超时时间设为60秒
            response = requests.post(self.api_url, json=payload, timeout=60)
            # 解析返回的JSON数据
            data = response.json()
            # 提取response字段，即模型的回答内容
            answer = data.get("response", "未获取到回答")
            # V1.2 新增：回答自检
            answer = self.self_check(answer)
            # 估算回答长度（词数），用于动态休眠
            response_length = len(answer.split())
            return answer, response_length  # 返回回答和长度
        except requests.exceptions.ConnectionError:
            # 捕获连接失败的异常：Ollama服务未启动或地址错误
            return "错误：无法连接到Ollama，请确认服务已启动", 0
        except json.JSONDecodeError:
            # 捕获JSON解析失败的异常：返回内容不是合法JSON
            return "错误：收到无效的响应数据", 0
        except Exception:
            # 捕获其他所有未预期的异常，防止程序崩溃
            return "错误：请求处理时发生未知问题", 0
    
    def unload_model(self):
        """卸载模型：释放内存，让老旧设备喘息"""
        try:
            # 调用Ollama API卸载模型（keep_alive=0 表示回答后立即从内存卸载，但保留模型文件）
            unload_payload = {"model": self.model, "keep_alive": 0}
            requests.post(self.api_url, json=unload_payload, timeout=5)
        except Exception:
            # 卸载失败不影响主流程（可能是模型已自动卸载）
            pass
    
    def rest(self, response_length):
        """动态休眠 + 卸载模型：根据回答长度调整休眠时间，释放内存"""
        # 根据词数决定休眠时间：短回答10秒，中等20秒，长回答30秒
        if response_length < 50:
            sleep_time = 10  # 短回答，快速恢复
            reason = "回答较短，快速恢复"
        elif response_length < 200:
            sleep_time = 20  # 中等回答，标准休息
            reason = "回答适中，标准休息"
        else:
            sleep_time = 30  # 长回答，充分休息
            reason = "回答较长，充分休息"

        print(f"\n💤 {reason}，休眠{sleep_time}秒...")  # 提示进入休眠
        # 卸载模型释放内存（关键优化：让4GB设备也能运行）
        self.unload_model()  # 从内存卸载模型，保留文件
        time.sleep(sleep_time)  # 按动态时间暂停
        print("✓ 模型已卸载，内存已释放 — 你的设备辛苦了")  # 提示休眠结束


def main():
    """主函数：CLI交互循环，接收输入、调用process和rest"""
    # 打印体现算力平权理念的欢迎语
    print("=" * 50)
    print("  LumiAgent — 算力平权，让老设备也能用AI")
    print("=" * 50)
    
    agent = LumiAgent()  # 创建LumiAgent实例
    
    while True:  # 无限循环，持续接收用户输入
        user_input = input("\n📝 请输入问题: ").strip()  # 读取用户输入并去除首尾空格
        
        if user_input.lower() in ("exit", "quit", "退出"):
            # 如果输入是退出命令，打印告别语并结束循环
            print("\n👋 再见！设备休息一下~")
            break
        
        # === /help 命令（新增）===
        if user_input.lower() == "/help":
            print("\n" + "=" * 50)
            print("  LumiAgent — 为老旧设备而生的AI编程调度器")
            print("=" * 50)
            print("  核心理念：算力平权，让所有设备平等获得AI编程辅助")
            print("  核心创新：休息机制 — 任务完成后卸载模型释放内存")
            print("  使用方法：")
            print("    - 直接输入编程问题，获取AI回答")
            print("    - 输入 /help 查看此帮助")
            print("    - 输入 exit / quit / 退出 结束程序")
            print("  GitHub: https://github.com/k3234/lumiagent ")
            print("=" * 50)
            continue
        # ========================
        
        if not user_input:
            # 如果输入为空，跳过不请求模型
            continue
        
        # 调用process方法获取模型回答和长度
        answer, length = agent.process(user_input)  # 返回 (回答, 词数)
        print(f"\n🤖 AI: {answer}")
        
        # 调用rest方法，传入回答长度用于动态休眠
        agent.rest(length)


if __name__ == "__main__":
    # 当直接运行此文件时，调用main函数启动交互循环
    main()
