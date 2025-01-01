import sys
import argparse
from workflow_processor import WorkflowProcessor

def run_test_mode():
    """运行测试模式"""
    processor = WorkflowProcessor()
    test_topics = [
        "苏州男生脱单",
        "微软与OpenAI的合作",
        "人工智能的发展趋势"
    ]
    
    for topic in test_topics:
        print("\n==================================================")
        print(f"测试主题: {topic}")
        print("==================================================\n")
        result = processor.process_workflow(topic, mode="1")
        
        if "error" in result:
            print(f"\n处理失败: {result['error']}")
        else:
            print(f"\n选择的视频: {result['video']['title']}")
            print(f"视频链接: {result['video']['url']}")
            print(f"文章已保存: {result.get('saved_path', '')}")
            
            if not result['validation_result']['is_valid']:
                print(f"\n注意：{result['validation_result']['reason']}")
        
        user_input = input("\n按Enter继续下一个测试，输入q退出...")
        if user_input.lower() == 'q':
            break

def run_interactive_mode():
    """运行交互模式"""
    processor = WorkflowProcessor()
    
    while True:
        print("\n欢迎使用 YouTube 视频转文章服务！\n")
        print("==================================================")
        topic = input("请输入要处理的主题（输入q退出，输入test进入测试模式）: ").strip()
        
        if topic.lower() == 'q':
            break
        elif topic.lower() == 'test':
            run_test_mode()
            continue
            
        mode = input("请选择处理模式（1: 生成公众号文章，2: 生成文本草稿）: ").strip()
        if mode not in ['1', '2']:
            print("无效的模式选择，请输入1或2")
            continue
            
        result = processor.process_workflow(topic, mode)
        
        if "error" in result:
            print(f"\n处理失败: {result['error']}")
        else:
            print(f"\n选择的视频: {result['video']['title']}")
            print(f"视频链接: {result['video']['url']}")
            print(f"文章已保存: {result.get('saved_path', '')}")
            
            if not result['validation_result']['is_valid']:
                print(f"\n注意：{result['validation_result']['reason']}")
        
        user_input = input("\n按Enter继续，输入q退出...")
        if user_input.lower() == 'q':
            break

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='YouTube视频转文章工具')
    parser.add_argument('--test', action='store_true', help='运行测试模式')
    args = parser.parse_args()
    
    if args.test:
        print("\n进入测试模式...")
        run_test_mode()
    else:
        run_interactive_mode()

if __name__ == "__main__":
    main()