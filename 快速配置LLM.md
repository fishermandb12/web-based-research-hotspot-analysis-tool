# 快速配置 LLM 指南

## 🎯 为什么要配置 LLM？

**使用 LLM 智能提取的优势：**
- ✅ 语义理解，提炼真正的关键词
- ✅ 自动过滤完整论文标题
- ✅ 识别隐含的技术和方法
- ✅ 更准确的研究热点识别

**不配置 LLM 也可以使用：**
- 📝 使用规则提取（基于标题和摘要）
- 📝 功能完整，但准确度略低

## 🚀 三种配置方式

### 方式 1：应用界面配置（推荐）⭐

**最简单！无需编辑文件！**

1. **启动应用**
   ```bash
   streamlit run app.py
   ```

2. **打开配置面板**
   - 在左侧边栏找到 **"🔑 LLM API 配置"**
   - 点击展开

3. **输入配置**
   - **API Key**: 粘贴你的 Qwen API Key
   - **API Endpoint**: 保持默认或修改
   ```
   https://dashscope.aliyuncs.com/compatible-mode/v1
   ```

4. **启用 LLM**
   - 勾选 **"🤖 使用 LLM 智能提取"**
   - 看到 ✅ "LLM 已配置" 提示

5. **开始使用**
   - 输入关键词，开始分析
   - 享受智能提取！

### 方式 2：使用 .env 文件

**适合长期使用，配置一次永久生效**

1. **创建 .env 文件**
   ```bash
   # 在项目根目录创建 .env 文件
   copy .env.example .env
   ```

2. **编辑 .env 文件**
   ```
   LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
   LLM_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
   ```

3. **保存并重启应用**
   ```bash
   streamlit run app.py
   ```

### 方式 3：环境变量

**适合临时测试**

**Windows PowerShell:**
```powershell
$env:LLM_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
$env:LLM_ENDPOINT="https://dashscope.aliyuncs.com/compatible-mode/v1"
streamlit run app.py
```

**Windows CMD:**
```cmd
set LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
set LLM_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
streamlit run app.py
```

**Linux/Mac:**
```bash
export LLM_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxx"
export LLM_ENDPOINT="https://dashscope.aliyuncs.com/compatible-mode/v1"
streamlit run app.py
```

## 🔑 获取 API Key

### 步骤 1: 访问阿里云

打开浏览器，访问：
```
https://dashscope.console.aliyun.com/
```

### 步骤 2: 注册/登录

- 如果没有账号，点击"注册"
- 如果有账号，直接登录

### 步骤 3: 创建 API Key

1. 进入控制台
2. 找到 "API Key 管理"
3. 点击 "创建 API Key"
4. 复制生成的 Key（格式：sk-xxxxxxxx）

### 步骤 4: 配置到应用

- 使用上面三种方式之一配置
- 推荐：直接在应用界面配置

## ✅ 验证配置

### 检查配置状态

启动应用后，在侧边栏查看：
- ✅ "LLM 已配置" → 配置成功
- ⚠️ "未配置 LLM API Key" → 需要配置

### 测试 LLM 提取

1. 勾选 "🤖 使用 LLM 智能提取"
2. 输入测试关键词（如"深度学习"）
3. 选择时间范围（如 2023-2024）
4. 点击 "🚀 开始分析"
5. 观察提示信息：
   - ✅ "🤖 使用 LLM 智能提取关键词..." → 成功
   - ⚠️ "LLM 关键词提取失败，使用备用方法" → 配置有误

## 🐛 常见问题

### Q1: 提示 "Connection error"

**原因：**
- API Key 错误
- 网络连接问题
- Endpoint 地址错误

**解决：**
1. 检查 API Key 是否正确
2. 检查网络连接
3. 确认 Endpoint 地址：
   ```
   https://dashscope.aliyuncs.com/compatible-mode/v1
   ```

### Q2: 提示 "未配置 LLM API Key"

**原因：**
- 没有输入 API Key
- .env 文件位置错误
- 环境变量未设置

**解决：**
- 使用应用界面配置（最简单）
- 检查 .env 文件是否在项目根目录
- 重启应用

### Q3: 配置后仍使用规则提取

**原因：**
- 没有勾选 "使用 LLM 智能提取"
- API Key 无效

**解决：**
1. 确保勾选了复选框
2. 检查 API Key 是否有效
3. 查看侧边栏状态提示

### Q4: LLM 提取很慢

**原因：**
- 逐篇处理需要时间
- 网络延迟

**说明：**
- 这是正常现象
- 100 篇论文约需 2-3 分钟
- 可以切换到规则提取（更快）

## 💡 使用建议

### 何时使用 LLM 提取？

**推荐使用：**
- ✅ 需要高质量关键词
- ✅ 论文标题复杂
- ✅ 需要识别研究热点
- ✅ 有充足时间

**可以不用：**
- 📝 快速测试
- 📝 论文数量很多（>200篇）
- 📝 网络不稳定
- 📝 没有 API Key

### 最佳实践

1. **首次使用**
   - 先用规则提取测试
   - 确认功能正常
   - 再配置 LLM

2. **正式分析**
   - 配置 LLM API Key
   - 启用 LLM 智能提取
   - 获得最佳效果

3. **批量分析**
   - 考虑使用规则提取
   - 或分批处理

## 🎊 总结

**最简单的配置方式：**
1. 启动应用：`streamlit run app.py`
2. 点击侧边栏 "🔑 LLM API 配置"
3. 输入 API Key
4. 勾选 "使用 LLM 智能提取"
5. 开始分析！

**无需配置也能用：**
- 不配置 LLM 也能正常使用
- 使用规则提取，功能完整
- 配置 LLM 后效果更好

---

**需要帮助？**
- 查看 `配置指南.md`
- 查看 `v2.2更新说明.md`
- 查看应用侧边栏的配置说明
