import argparse
import os
def get_config_path():
    # 使用命令行参数指定配置文件路径
    parser = argparse.ArgumentParser(description="My application")
    parser.add_argument('--config', type=str, help='Path to the configuration file')
    args = parser.parse_args()

    # 如果指定了配置文件路径，则返回该路径，否则返回默认路径
    if args.config:
        print(f"------使用配置文件: {args.config}------")
        return args.config
    else:
    # 获取当前目录
        print(f"------动态获取配置文件: {os.path.join(os.getcwd(), 'config.ini')}------")
        return os.path.join(os.getcwd(), 'config.ini')
    # else:
    #     print(f"------默认配置文件: './config.ini'------")
    #     return './config.ini'