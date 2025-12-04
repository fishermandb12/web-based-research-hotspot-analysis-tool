"""
检查系统中可用的中文字体
"""
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt

def check_chinese_fonts():
    """检查系统中所有可用的字体"""
    print("=" * 60)
    print("检查系统字体...")
    print("=" * 60)
    
    # 获取所有字体
    all_fonts = [f.name for f in fm.fontManager.ttflist]
    
    # 中文字体列表
    chinese_fonts = [
        'SimHei',           # 黑体 (Windows)
        'Microsoft YaHei',  # 微软雅黑 (Windows)
        'STHeiti',          # 华文黑体 (Mac)
        'Arial Unicode MS', # (Mac)
        'PingFang SC',      # 苹方 (Mac)
        'Heiti SC',         # 黑体-简 (Mac)
        'WenQuanYi Micro Hei',  # 文泉驿微米黑 (Linux)
        'WenQuanYi Zen Hei',    # 文泉驿正黑 (Linux)
        'Noto Sans CJK SC',     # 思源黑体 (Linux)
        'Droid Sans Fallback',  # Android fallback
    ]
    
    print("\n✅ 已安装的中文字体:")
    found_fonts = []
    for font in chinese_fonts:
        if font in all_fonts:
            print(f"  ✓ {font}")
            found_fonts.append(font)
    
    if not found_fonts:
        print("  ❌ 未找到任何中文字体！")
    
    print("\n❌ 未安装的中文字体:")
    for font in chinese_fonts:
        if font not in all_fonts:
            print(f"  ✗ {font}")
    
    print("\n" + "=" * 60)
    print("字体测试")
    print("=" * 60)
    
    if found_fonts:
        # 测试第一个找到的字体
        test_font = found_fonts[0]
        print(f"\n使用字体: {test_font}")
        
        # 配置字体
        plt.rcParams['font.sans-serif'] = [test_font]
        plt.rcParams['axes.unicode_minus'] = False
        
        # 创建测试图
        fig, ax = plt.subplots(figsize=(8, 6))
        test_text = ['量子计算', '机器学习', '深度学习', '神经网络', '自然语言处理']
        values = [5, 8, 6, 7, 4]
        
        ax.bar(test_text, values)
        ax.set_title('中文字体测试', fontsize=16)
        ax.set_xlabel('关键词', fontsize=12)
        ax.set_ylabel('频次', fontsize=12)
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        # 保存图片
        output_file = 'font_test_result.png'
        plt.savefig(output_file, dpi=100, bbox_inches='tight')
        print(f"✅ 测试图片已保存: {output_file}")
        print("   请打开图片检查中文是否正常显示")
        
        return True
    else:
        print("\n❌ 无法进行字体测试，因为没有找到中文字体")
        print("\n📥 安装建议:")
        print("\nWindows:")
        print("  - 系统通常已预装 SimHei 或 Microsoft YaHei")
        print("  - 如果没有，请从控制面板安装中文语言包")
        
        print("\nLinux (Ubuntu/Debian):")
        print("  sudo apt-get install fonts-wqy-zenhei")
        print("  或")
        print("  sudo apt-get install fonts-noto-cjk")
        
        print("\nMac:")
        print("  - 系统自带中文字体")
        print("  - 如有问题，请检查系统语言设置")
        
        return False

def list_all_fonts():
    """列出系统中所有字体（可选）"""
    print("\n" + "=" * 60)
    print("系统中所有可用字体（前50个）:")
    print("=" * 60)
    
    all_fonts = sorted(set([f.name for f in fm.fontManager.ttflist]))
    for i, font in enumerate(all_fonts[:50], 1):
        print(f"{i:3d}. {font}")
    
    if len(all_fonts) > 50:
        print(f"\n... 还有 {len(all_fonts) - 50} 个字体未显示")
    
    print(f"\n总计: {len(all_fonts)} 个字体")

if __name__ == "__main__":
    success = check_chinese_fonts()
    
    # 询问是否显示所有字体
    print("\n" + "=" * 60)
    response = input("是否显示所有系统字体？(y/n): ").strip().lower()
    if response == 'y':
        list_all_fonts()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ 字体检查完成！")
        print("   如果测试图片显示正常，说明字体配置成功")
    else:
        print("❌ 需要安装中文字体")
        print("   请按照上面的说明安装字体后重试")
    print("=" * 60)
