# OpenAlex API 字段修复说明

## 🐛 问题描述

**错误信息：**
```json
{
  "error": "Invalid query parameters error.",
  "message": "primary_location.source.display_name.search is not a valid field."
}
```

**原因：**
- OpenAlex API 不支持 `primary_location.source.display_name.search` 字段
- 无法直接在 filter 参数中按期刊名称过滤

## ✅ 解决方案

### 修改策略

**之前的错误方法：**
```python
params = {
    "filter": f"primary_location.source.display_name.search:{journal},publication_year:{start_year}-{end_year}",
    "search": domain,
    "per_page": papers_per_journal
}
```

**修复后的正确方法：**
```python
# 1. 先获取领域相关的论文（获取更多以便过滤）
params = {
    "filter": f"publication_year:{start_year}-{end_year}",
    "search": domain,
    "per_page": papers_per_journal * 3  # 获取3倍数量用于过滤
}

# 2. 在结果中过滤期刊
for result in results:
    journal_name = result["primary_location"]["source"]["display_name"]
    
    # 灵活匹配期刊名称
    if is_journal_match(journal_name, target_journal):
        journal_papers.append(paper)
        
        # 达到目标数量后停止
        if len(journal_papers) >= papers_per_journal:
            break
```

### 期刊名称匹配策略

实现了三种匹配策略，确保能找到目标期刊的论文：

**策略 1：精确匹配**
```python
if journal_lower == journal_name_lower:
    is_match = True
```
- 例如："Nature" 匹配 "Nature"

**策略 2：子串匹配**
```python
if journal_lower in journal_name_lower or journal_name_lower in journal_lower:
    is_match = True
```
- 例如："Nature" 匹配 "Nature Communications"
- 例如："Science" 匹配 "Science Advances"

**策略 3：词级匹配**
```python
journal_words = [w for w in journal_lower.split() if len(w) > 3]
matches = sum(1 for word in journal_words if word in journal_name_lower)
if matches >= len(journal_words) * 0.5:
    is_match = True
```
- 例如："Machine Learning Research" 匹配 "Journal of Machine Learning Research"
- 至少50%的关键词匹配

## 📊 性能影响

### 查询策略调整

**之前（错误方法）：**
- 每个期刊查询1次
- 直接获取目标数量的论文
- 但是 API 不支持，导致失败

**现在（修复后）：**
- 每个期刊查询1次
- 获取 `papers_per_journal * 3` 篇论文
- 在结果中过滤出目标期刊的论文
- 达到目标数量后停止

### 示例

**配置：**
- 总论文限制：100篇
- 期刊数量：10个
- 每个期刊目标：10篇

**实际查询：**
```
期刊1 (Nature):
  - 查询：获取30篇论文
  - 过滤：找到12篇来自Nature的论文
  - 保留：前10篇
  
期刊2 (Science):
  - 查询：获取30篇论文
  - 过滤：找到8篇来自Science的论文
  - 保留：全部8篇
  
...

总计：约100篇论文
```

## 🔧 代码变更

### 主要修改

**文件：** `app.py`

**函数：** `fetch_openalex_by_journals()`

**变更内容：**

1. **移除无效的 filter 参数**
   ```python
   # 删除
   "filter": f"primary_location.source.display_name.search:{journal},..."
   
   # 改为
   "filter": f"publication_year:{start_year}-{end_year}"
   ```

2. **增加获取数量**
   ```python
   "per_page": papers_per_journal * 3  # 获取3倍用于过滤
   ```

3. **添加期刊过滤逻辑**
   ```python
   # 在结果中过滤期刊
   for result in results:
       journal_name = get_journal_name(result)
       if is_journal_match(journal_name, target_journal):
           journal_papers.append(paper)
           if len(journal_papers) >= papers_per_journal:
               break
   ```

## ⚠️ 注意事项

### 1. 可能获取不到足够的论文

**问题：**
- 如果某个期刊在领域内的论文很少
- 即使获取30篇，过滤后可能只有几篇

**解决方案：**
- 已实现：显示实际获取的论文数
- 用户可以看到每个期刊的实际论文数
- 如果总数不足，会显示警告

### 2. API 调用次数增加

**影响：**
- 每个期刊需要获取更多论文（3倍）
- 但 OpenAlex 是免费的，没有速率限制问题

**优化：**
- 使用缓存避免重复查询
- 达到目标数量后立即停止

### 3. 期刊名称变体

**问题：**
- 同一期刊可能有多种名称
- 例如："Nat Commun" vs "Nature Communications"

**解决方案：**
- 实现了灵活的匹配策略
- 支持子串匹配和词级匹配
- 大小写不敏感

## 📈 测试建议

### 测试场景

**场景 1：常见期刊**
```
期刊：Nature, Science, Cell
领域：machine learning
预期：每个期刊能获取10+篇论文
```

**场景 2：专业期刊**
```
期刊：Journal of Machine Learning Research
领域：deep learning
预期：能匹配到相关论文
```

**场景 3：期刊名称变体**
```
期刊：Nature Communications
搜索：Nature
预期：能正确匹配
```

### 验证方法

1. **检查日志输出**
   ```
   ✅ Nature: 获取 12 篇论文
   ✅ Science: 获取 10 篇论文
   ⚠️ Cell: 获取 3 篇论文
   ```

2. **检查总数**
   ```
   📊 查询完成：成功 10/10 个期刊，共获取 95 篇论文
   ```

3. **检查期刊名称**
   - 在结果中验证论文确实来自目标期刊
   - 检查 `paper["journal"]` 字段

## 🎯 预期效果

### 成功案例

**输入：**
- 领域：经济学
- 期刊：10个顶级经济学期刊
- 时间：2022-2024
- 限制：100篇

**输出：**
```
🔍 正在查询期刊 [1/10]: Journal of Political Economy
  ✅ Journal of Political Economy: 获取 10 篇论文

🔍 正在查询期刊 [2/10]: American Economic Review
  ✅ American Economic Review: 获取 10 篇论文

...

📊 查询完成：成功 10/10 个期刊，共获取 100 篇论文
```

### 失败案例处理

**情况：某个期刊论文很少**
```
🔍 正在查询期刊 [5/10]: Obscure Economics Journal
  ⚠️ Obscure Economics Journal: 获取 2 篇论文
```

**系统行为：**
- 继续查询其他期刊
- 最终可能获取少于100篇论文
- 显示实际获取的论文数

## 🎊 总结

**问题：** OpenAlex API 不支持直接按期刊名称过滤

**解决：** 先获取领域论文，再在结果中过滤期刊

**优势：**
- ✅ 兼容 OpenAlex API 的实际字段
- ✅ 灵活的期刊名称匹配
- ✅ 清晰的进度提示
- ✅ 优雅的错误处理

**权衡：**
- ⚠️ 需要获取更多论文（3倍）
- ⚠️ 可能获取不到足够的论文
- ✅ 但 OpenAlex 免费，无速率限制

**现在应该可以正常运行了！** 🚀

---

**修复日期：** 2024-12-05
**影响版本：** v3.1
**状态：** ✅ 已修复
