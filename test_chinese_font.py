"""
测试 matplotlib 中文字体配置
"""
import matplotlib.pyplot as plt
import matplotlib

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 创建简单的测试图
fig, ax = plt.subplots(figsize=(8, 6))

# 测试中文文本
test_keywords = ['量子计算', '机器学习', '深度学习', '神经网络', '自然语言处理']
values = [5, 8, 6, 7, 4]

ax.bar(test_keywords, values)
ax.set_title('中文字体测试', fontsize=16)
ax.set_xlabel('关键词', fontsize=12)
ax.set_ylabel('频次', fontsize=12)

plt.xticks(rotation=45, ha='right')
plt.tight_layout()

# 保存图片
plt.savefig('chinese_font_test.png', dpi=100, bbox_inches='tight')
print("✅ 中文字体测试完成！")
print(f"📊 图片已保存为: chinese_font_test.png")
print(f"🔤 当前字体: {matplotlib.rcParams['font.sans-serif']}")
