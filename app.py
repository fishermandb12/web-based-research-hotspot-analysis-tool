# 数据源：OpenAlex（免费开放获取）

import streamlit as st
from datetime import date
import requests
import os
from openai import OpenAI
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.figure
from dotenv import load_dotenv
import json

# Note: No longer using .env file, API key configured in UI

# Application version
APP_VERSION = "3.0"
VERSION_FILE = ".app_version.json"

# Configure matplotlib to support Chinese characters
import matplotlib.font_manager as fm
import sys

def setup_chinese_font():
    """
    Setup Chinese font for matplotlib with multiple fallback options.
    """
    # Try to find available Chinese fonts
    available_fonts = [f.name for f in fm.fontManager.ttflist]
    
    # List of Chinese fonts to try (in order of preference)
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
    
    # Find first available Chinese font
    found_font = None
    for font in chinese_fonts:
        if font in available_fonts:
            found_font = font
            break
    
    if found_font:
        plt.rcParams['font.sans-serif'] = [found_font] + chinese_fonts
        plt.rcParams['axes.unicode_minus'] = False
        return found_font
    else:
        # If no Chinese font found, use default and warn user
        plt.rcParams['font.sans-serif'] = chinese_fonts + ['DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False
        return None

# Setup Chinese font
detected_font = setup_chinese_font()


def check_version_upgrade() -> tuple[bool, str]:
    """
    Check if the application has been upgraded from a previous version.
    
    Returns:
        Tuple of (is_upgrade, previous_version)
        - is_upgrade: True if this is an upgrade from a previous version
        - previous_version: The previous version string, or empty string if new install
    """
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
                previous_version = version_data.get('version', '')
                
                # Check if version has changed
                if previous_version and previous_version != APP_VERSION:
                    return True, previous_version
                else:
                    return False, previous_version
        else:
            # First time running, no version file exists
            return False, ''
    except Exception:
        # If there's any error reading the version file, treat as new install
        return False, ''


def save_current_version():
    """
    Save the current application version to file.
    """
    try:
        version_data = {
            'version': APP_VERSION,
            'updated_at': date.today().isoformat()
        }
        with open(VERSION_FILE, 'w', encoding='utf-8') as f:
            json.dump(version_data, f, indent=2)
    except Exception:
        # Silently fail if we can't write the version file
        pass


def clear_cache_on_upgrade():
    """
    Clear cache if the application has been upgraded.
    Display migration notice to user.
    
    Returns:
        True if cache was cleared due to upgrade, False otherwise
    """
    is_upgrade, previous_version = check_version_upgrade()
    
    if is_upgrade:
        # Clear all cached data
        st.cache_data.clear()
        
        # Display migration notice
        st.info(f"""
        🔄 **检测到版本升级: v{previous_version} → v{APP_VERSION}**
        
        缓存已自动清除以确保兼容性。
        
        **v{APP_VERSION} 主要变化：**
        - ⚠️ API Key 现在是必需的（LLM-Only 模式）
        - ✅ 所有关键词提取均使用 LLM
        - ✅ 1区期刊筛选默认启用
        - ❌ 不再支持基于规则的关键词提取
        
        请在左侧边栏配置 API Key 后开始使用。
        """)
        
        # Save the new version
        save_current_version()
        
        return True
    else:
        # Not an upgrade, just save current version if not already saved
        if not os.path.exists(VERSION_FILE):
            save_current_version()
        
        return False


def test_openalex_connection() -> bool:
    """
    Test connection to OpenAlex API.
    
    Returns:
        True if connection successful, False otherwise
    """
    try:
        response = requests.get("https://api.openalex.org/", timeout=10)
        return response.status_code == 200
    except:
        return False


def parse_comma_separated(text: str) -> list[str]:
    """
    Parse comma-separated string supporting both "," and "，" delimiters.
    
    Args:
        text: Comma-separated string
        
    Returns:
        List of non-empty trimmed strings
    """
    # Replace Chinese comma with regular comma for uniform processing
    normalized = text.replace("，", ",")
    # Split by comma, strip whitespace, and filter empty strings
    return [item.strip() for item in normalized.split(",") if item.strip()]


def validate_api_key(api_key: str) -> bool:
    """
    Validates that API key is present and non-empty.
    
    Args:
        api_key: User-provided API key
        
    Returns:
        True if valid, False otherwise
    """
    # Check if API key is non-empty and not just whitespace
    if not api_key or not api_key.strip():
        return False
    return True


def validate_date_range(start_date: date, end_date: date) -> bool:
    """
    Validate that start date precedes or equals end date.
    
    Args:
        start_date: Beginning of time range
        end_date: End of time range
        
    Returns:
        True if start_date <= end_date, False otherwise
    """
    return start_date <= end_date


def identify_top_journals(domain: str, api_key: str, endpoint: str) -> list[str]:
    """
    Invokes LLM to generate top-tier journal names (Q1 journals).
    
    Args:
        domain: Research field keyword
        api_key: LLM API key
        endpoint: LLM API endpoint
        
    Returns:
        List of journal names (e.g., ["Nature", "Science"])
    """
    try:
        # If no API key is provided, return empty list
        if not api_key:
            st.warning("⚠️ 未配置 LLM API 密钥，跳过期刊筛选")
            return []
        
        # Initialize OpenAI client (compatible with Qwen API)
        client = OpenAI(api_key=api_key, base_url=endpoint)
        
        # Create LLM prompt for Q1 journals
        prompt = f"""请列出"{domain}"领域的中科院1区或SCI Q1期刊。

要求：
1. 只输出英文期刊名称
2. 用逗号分隔
3. 不要其他解释文字
4. 列出5-10个顶级期刊

示例输出格式：Nature, Science, Cell, Nature Communications, Advanced Materials"""
        
        # Call LLM
        response = client.chat.completions.create(
            model="qwen-plus",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=300,
            timeout=15
        )
        
        # Extract response text
        llm_output = response.choices[0].message.content.strip()
        
        # Parse comma-separated journal names
        journals = parse_comma_separated(llm_output)
        
        return journals
        
    except Exception as e:
        # Log error and continue without journal filtering
        st.warning(f"⚠️ 期刊识别失败: {str(e)}")
        return []


def reconstruct_abstract_from_inverted_index(inverted_index: dict) -> str:
    """
    Convert OpenAlex inverted index format to full text.
    
    OpenAlex stores abstracts as inverted indices where each word maps to 
    a list of positions where it appears. This function reconstructs the 
    original text by placing words at their correct positions.
    
    Args:
        inverted_index: Dictionary mapping words to position lists
                       e.g., {"hello": [0], "world": [1]}
        
    Returns:
        Reconstructed full text string, or empty string if index is empty
    """
    if not inverted_index:
        return ""
    
    # Create a list to hold words at their positions
    # First, find the maximum position to determine list size
    max_position = 0
    for positions in inverted_index.values():
        if positions:
            max_position = max(max_position, max(positions))
    
    # Initialize list with empty strings
    words = [""] * (max_position + 1)
    
    # Place each word at its positions
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    
    # Join words with spaces
    return " ".join(words)


def extract_keywords_with_llm_single(papers: list[dict], api_key: str, endpoint: str) -> list[list[str]]:
    """
    Extract keywords using LLM exclusively (no fallback).
    Processes papers one by one for better reliability.
    
    Args:
        papers: List of paper dictionaries
        api_key: LLM API key (required)
        endpoint: LLM API endpoint
        
    Returns:
        List of keyword lists, one per paper
        
    Raises:
        Exception if LLM extraction fails for all papers
    """
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key, base_url=endpoint)
    
    all_keywords = []
    failed_count = 0
    success_count = 0
    failed_papers = []  # Track failed papers for reporting
    
    # Process papers one by one for better reliability
    for i, paper in enumerate(papers, 1):
        try:
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")[:800]  # Limit abstract length
            
            # Skip if no content
            if not title:
                failed_count += 1
                failed_papers.append((i, "无标题"))
                continue
            
            # Create LLM prompt
            prompt = f"""从以下论文的标题和摘要中提取3-5个核心关键词。

要求：
1. 提取具体的技术、方法、模型名称（如"Transformer Architecture"、"Quantum Error Correction"）
2. 避免宽泛概念（如"Machine Learning"、"Computer Science"）
3. 优先提取多词专业术语（2-4个词）
4. 不要输出完整的论文标题
5. 只输出关键词，用逗号分隔

标题: {title}
摘要: {abstract if abstract else "无摘要"}

输出格式：关键词1, 关键词2, 关键词3
"""
            
            # Call LLM with timeout
            response = client.chat.completions.create(
                model="qwen-plus",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
                timeout=10  # 10 second timeout per paper
            )
            
            # Parse response
            llm_output = response.choices[0].message.content.strip()
            
            # Split keywords by comma
            keywords = [kw.strip() for kw in llm_output.split(',') if kw.strip()]
            
            # Filter out overly long "keywords" (likely full titles)
            # Keep only phrases with 1-5 words
            keywords = [kw for kw in keywords if 1 <= len(kw.split()) <= 5]
            
            # Filter out generic terms
            generic_terms = {'machine learning', 'deep learning', 'artificial intelligence', 
                            'computer science', 'data science', 'neural network'}
            keywords = [kw for kw in keywords if kw.lower() not in generic_terms]
            
            if keywords:
                all_keywords.append(keywords[:6])  # Limit to 6 per paper
                success_count += 1
            else:
                # No valid keywords extracted
                failed_count += 1
                failed_papers.append((i, "未提取到有效关键词"))
                
        except Exception as e:
            # Skip this paper if LLM fails, continue with others
            failed_count += 1
            error_reason = str(e)
            # Simplify error message for display
            if "timeout" in error_reason.lower():
                error_reason = "处理超时"
            elif "api" in error_reason.lower() or "auth" in error_reason.lower():
                error_reason = "API调用失败"
            else:
                error_reason = "提取失败"
            
            failed_papers.append((i, error_reason))
            
            # Display warning for failed paper (only show first few to avoid spam)
            if failed_count <= 3:
                st.warning(f"⚠️ 论文 {i} {error_reason}，已跳过")
            elif failed_count == 4:
                st.warning(f"⚠️ 更多论文处理失败，将继续处理剩余论文...")
            
            continue
    
    # If all papers failed, raise exception with clear error message in Chinese
    if not all_keywords:
        error_msg = f"❌ 所有论文的关键词提取均失败\n\n成功: {success_count}/{len(papers)}\n失败: {failed_count}/{len(papers)}"
        raise Exception(error_msg)
    
    # If some papers failed but we have results, display summary and continue
    if failed_count > 0:
        st.info(f"ℹ️ 关键词提取完成：成功 {success_count}/{len(papers)} 篇，跳过 {failed_count} 篇失败的论文")
    
    return all_keywords


# Rule-based extraction removed in v3.0 - LLM-only mode


@st.cache_data
def fetch_openalex_by_journals(domain: str, start_year: int, end_year: int, journals: list[str], max_total_papers: int = 100) -> list[dict]:
    """
    Queries OpenAlex API directly for each Q1 journal to get substantial paper volume.
    v3.1 Update: Direct journal search with total paper limit for performance.
    
    Args:
        domain: Search keyword (used to filter papers within each journal)
        start_year: Beginning of time range (YYYY)
        end_year: End of time range (YYYY)
        journals: List of Q1 journal names to query
        max_total_papers: Maximum total papers to fetch (default: 100 for performance)
        
    Returns:
        List of paper dictionaries aggregated from all journals (up to max_total_papers)
    """
    # Calculate papers per journal based on total limit
    papers_per_journal = max(5, max_total_papers // len(journals)) if journals else 10
    all_papers = []
    total_journals = len(journals)
    failed_journals = []
    
    # Create a progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    st.info(f"📊 将从 {total_journals} 个期刊中获取论文，每个期刊约 {papers_per_journal} 篇，总计不超过 {max_total_papers} 篇")
    
    for i, journal in enumerate(journals):
        # Check if we've reached the limit
        if len(all_papers) >= max_total_papers:
            st.info(f"✅ 已达到论文数量上限 ({max_total_papers} 篇)，停止查询")
            break
        try:
            # Update progress
            progress = (i + 1) / total_journals
            progress_bar.progress(progress)
            status_text.text(f"🔍 正在查询期刊 [{i+1}/{total_journals}]: {journal}")
            
            # Construct API endpoint
            url = "https://api.openalex.org/works"
            
            # Construct query parameters
            # Note: OpenAlex doesn't support direct journal name filtering in filter parameter
            # We'll search with domain keyword and filter results by journal name
            params = {
                "filter": f"publication_year:{start_year}-{end_year}",
                "search": domain,
                "per_page": papers_per_journal * 3,  # Fetch more to account for filtering
                "select": "id,title,publication_year,keywords,concepts,abstract_inverted_index,primary_location"
            }
            
            # Make API request with retry mechanism
            max_retries = 3
            retry_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = requests.get(url, params=params, timeout=60)
                    response.raise_for_status()
                    break  # Success
                except (requests.exceptions.Timeout, requests.exceptions.ConnectionError, requests.exceptions.RequestException) as e:
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(retry_delay)
                    else:
                        raise
            
            # Parse JSON response
            data = response.json()
            results = data.get("results", [])
            
            # Process results and filter by journal name
            journal_papers = []
            for result in results:
                title = result.get("title", "")
                if not title:
                    continue
                
                # Get journal name
                journal_name = ""
                primary_location = result.get("primary_location", {})
                if primary_location and isinstance(primary_location, dict):
                    source = primary_location.get("source", {})
                    if source and isinstance(source, dict):
                        journal_name = source.get("display_name", "")
                
                # Filter by journal name (flexible matching)
                if journal_name:
                    journal_lower = journal.lower().strip()
                    journal_name_lower = journal_name.lower().strip()
                    
                    # Check if this paper is from the target journal
                    is_match = False
                    
                    # Strategy 1: Exact match
                    if journal_lower == journal_name_lower:
                        is_match = True
                    # Strategy 2: Substring match
                    elif journal_lower in journal_name_lower or journal_name_lower in journal_lower:
                        is_match = True
                    # Strategy 3: Word-level matching
                    else:
                        journal_words = [w for w in journal_lower.split() if len(w) > 3]
                        if journal_words:
                            matches = sum(1 for word in journal_words if word in journal_name_lower)
                            if matches >= len(journal_words) * 0.5:
                                is_match = True
                    
                    if not is_match:
                        continue  # Skip papers not from this journal
                
                # Get abstract
                abstract_inverted_index = result.get("abstract_inverted_index", {})
                abstract = ""
                if abstract_inverted_index:
                    abstract = reconstruct_abstract_from_inverted_index(abstract_inverted_index)
                
                # Get keywords and concepts
                keywords = result.get("keywords", [])
                concepts = result.get("concepts", [])
                
                paper = {
                    "id": result.get("id", ""),
                    "title": title,
                    "abstract": abstract,
                    "keywords": keywords,
                    "concepts": concepts,
                    "publication_year": result.get("publication_year", 0),
                    "journal": journal_name
                }
                journal_papers.append(paper)
                
                # Stop if we have enough papers for this journal
                if len(journal_papers) >= papers_per_journal:
                    break
            
            # Add papers from this journal to the total
            all_papers.extend(journal_papers)
            
            # Display result for this journal
            if journal_papers:
                st.success(f"  ✅ {journal}: 获取 {len(journal_papers)} 篇论文")
            else:
                st.warning(f"  ⚠️ {journal}: 未找到论文")
                failed_journals.append(journal)
        
        except Exception as e:
            st.error(f"  ❌ {journal}: 查询失败 ({str(e)})")
            failed_journals.append(journal)
            continue
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Display summary statistics
    successful_journals = total_journals - len(failed_journals)
    st.info(f"📊 查询完成：成功 {successful_journals}/{total_journals} 个期刊，共获取 {len(all_papers)} 篇论文")
    
    if failed_journals:
        st.warning(f"⚠️ 以下期刊未能获取论文：{', '.join(failed_journals[:5])}" + 
                  (f" 等 {len(failed_journals)} 个期刊" if len(failed_journals) > 5 else ""))
    
    return all_papers


@st.cache_data
def fetch_openalex_data(domain: str, start_year: int, end_year: int, journals: list[str] = None, max_papers: int = 100) -> list[dict]:
    """
    Queries OpenAlex API for publications.
    v3.1 Update: If journals provided, use direct journal search; otherwise use traditional search.
    
    Args:
        domain: Search keyword
        start_year: Beginning of time range (YYYY)
        end_year: End of time range (YYYY)
        journals: Optional list of journal names (if provided, use direct journal search)
        max_papers: Maximum total papers to fetch (default: 100)
        
    Returns:
        List of paper dictionaries with metadata
    """
    # v3.1: If journals provided, use direct journal search
    if journals:
        return fetch_openalex_by_journals(domain, start_year, end_year, journals, max_total_papers=max_papers)
    
    # Otherwise, use traditional domain keyword search (fallback mode when Q1 filtering disabled)
    try:
        st.info(f"ℹ️ 使用传统搜索模式（未启用1区期刊筛选），将获取最多 {max_papers} 篇论文")
        # Construct API endpoint
        url = "https://api.openalex.org/works"
        
        # Construct query parameters (limit to max_papers)
        params = {
            "search": domain,
            "filter": f"publication_year:{start_year}-{end_year}",
            "per_page": min(max_papers, 100),  # OpenAlex max is 100 per page
            "select": "id,title,publication_year,keywords,concepts,abstract_inverted_index,primary_location"
        }
        
        # Make API request with retry mechanism
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Display retry progress to user
                if attempt > 0:
                    st.info(f"🔄 正在进行第 {attempt + 1} 次尝试...")
                
                response = requests.get(url, params=params, timeout=60)  # 60-second timeout per request
                response.raise_for_status()
                break  # Success, exit retry loop
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    st.warning(f"⚠️ 连接超时，正在重试 ({attempt + 1}/{max_retries})...")
                    import time
                    time.sleep(retry_delay)
                else:
                    raise
            except requests.exceptions.ConnectionError:
                if attempt < max_retries - 1:
                    st.warning(f"⚠️ 连接失败，正在重试 ({attempt + 1}/{max_retries})...")
                    import time
                    time.sleep(retry_delay)
                else:
                    raise
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    st.warning(f"⚠️ 请求失败，正在重试 ({attempt + 1}/{max_retries})...")
                    import time
                    time.sleep(retry_delay)
                else:
                    raise
        
        # Parse JSON response
        data = response.json()
        results = data.get("results", [])
        
        # Handle empty results
        if not results:
            # Don't display detailed message here, will be handled in main()
            return []
        
        # Extract relevant fields from results
        papers = []
        filtered_count = 0
        total_results = len(results)
        
        for result in results:
            # Extract title (required)
            title = result.get("title", "")
            if not title:
                continue
            
            # Get journal name for filtering
            journal_name = ""
            primary_location = result.get("primary_location", {})
            if primary_location and isinstance(primary_location, dict):
                source = primary_location.get("source", {})
                if source and isinstance(source, dict):
                    journal_name = source.get("display_name", "")
            
            # Filter by journals if provided (flexible matching)
            if journals and journal_name:
                # Check if paper is from one of the target journals
                # Use flexible matching for journal names
                is_from_target_journal = False
                matched_journal = None
                
                for journal in journals:
                    journal_lower = journal.lower().strip()
                    journal_name_lower = journal_name.lower().strip()
                    
                    # Strategy 1: Exact match
                    if journal_lower == journal_name_lower:
                        is_from_target_journal = True
                        matched_journal = journal
                        break
                    
                    # Strategy 2: Substring match (either direction)
                    if journal_lower in journal_name_lower or journal_name_lower in journal_lower:
                        is_from_target_journal = True
                        matched_journal = journal
                        break
                    
                    # Strategy 3: Word-level matching (for multi-word journal names)
                    # Match if significant words (>3 chars) from target journal appear in actual journal name
                    journal_words = [w for w in journal_lower.split() if len(w) > 3]
                    if journal_words:
                        # Check if at least 50% of significant words match
                        matches = sum(1 for word in journal_words if word in journal_name_lower)
                        if matches >= len(journal_words) * 0.5:
                            is_from_target_journal = True
                            matched_journal = journal
                            break
                
                if not is_from_target_journal:
                    filtered_count += 1
                    continue  # Skip papers not from target journals
            
            # Get abstract (optional, but preferred)
            abstract_inverted_index = result.get("abstract_inverted_index", {})
            abstract = ""
            if abstract_inverted_index:
                abstract = reconstruct_abstract_from_inverted_index(abstract_inverted_index)
            
            # Get keywords (OpenAlex keywords)
            keywords = result.get("keywords", [])
            
            # Get concepts (OpenAlex topic classification)
            concepts = result.get("concepts", [])
            
            paper = {
                "id": result.get("id", ""),
                "title": title,
                "abstract": abstract,
                "keywords": keywords,
                "concepts": concepts,
                "publication_year": result.get("publication_year", 0),
                "journal": journal_name
            }
            papers.append(paper)
        
        # Display filtering statistics if journals were provided
        if journals:
            if len(papers) > 0:
                # Successfully filtered papers
                filter_rate = (len(papers) / total_results * 100) if total_results > 0 else 0
                st.info(f"📊 期刊筛选统计：从 {total_results} 篇论文中筛选出 {len(papers)} 篇来自1区期刊的论文（保留率: {filter_rate:.1f}%，过滤了 {filtered_count} 篇）")
            else:
                # No papers matched - will fall back to all papers
                st.warning(f"⚠️ 在指定的 {len(journals)} 个1区期刊中未找到论文（共检索到 {total_results} 篇论文）")
                st.info("💡 将返回空结果，主程序会自动重试搜索所有论文")
        
        return papers
        
    except requests.exceptions.Timeout:
        st.error("❌ 连接 OpenAlex API 超时")
        st.info("""
        **可能的原因：**
        - 网络连接较慢
        - OpenAlex 服务器响应慢
        
        **解决方案：**
        - 检查网络连接
        - 稍后重试
        - 尝试使用 VPN
        """)
        return []
    except requests.exceptions.ConnectionError:
        st.error("❌ 无法连接到 OpenAlex API")
        st.info("""
        **可能的原因：**
        - 网络连接问题
        - 防火墙阻止
        - DNS 解析失败
        
        **解决方案：**
        - 检查网络连接
        - 检查防火墙设置
        - 尝试使用 VPN
        - 检查是否能访问 https://api.openalex.org
        """)
        return []
    except requests.exceptions.RequestException as e:
        st.error(f"❌ OpenAlex API 请求失败: {str(e)}")
        return []
    except Exception as e:
        st.error(f"❌ 处理 OpenAlex 数据时出错: {str(e)}")
        return []


def build_cooccurrence_matrix(keyword_lists: list[list[str]], max_keywords: int = 50) -> pd.DataFrame:
    """
    Constructs keyword co-occurrence matrix.
    
    Args:
        keyword_lists: Keywords extracted from each paper
        max_keywords: Maximum number of keywords to include (default: 50)
        
    Returns:
        DataFrame with keywords as both index and columns
    """
    # Count keyword frequencies
    keyword_freq = {}
    for keywords in keyword_lists:
        for keyword in keywords:
            keyword_freq[keyword] = keyword_freq.get(keyword, 0) + 1
    
    # Sort keywords by frequency and take top N
    sorted_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)
    top_keywords = [kw for kw, _ in sorted_keywords[:max_keywords]]
    
    # Convert to sorted list for consistent ordering
    unique_keywords = sorted(top_keywords)
    
    # Initialize N×N matrix with zeros
    n = len(unique_keywords)
    matrix = [[0 for _ in range(n)] for _ in range(n)]
    
    # Create keyword to index mapping for efficient lookup
    keyword_to_idx = {keyword: idx for idx, keyword in enumerate(unique_keywords)}
    
    # For each paper's keyword list, increment counts for all keyword pairs
    for keywords in keyword_lists:
        # Get unique keywords in this paper (to avoid counting duplicates)
        # Only keep keywords that are in our top keywords list
        unique_paper_keywords = [kw for kw in set(keywords) if kw in keyword_to_idx]
        
        # For each pair (k1, k2) where k1 ≠ k2
        for i, k1 in enumerate(unique_paper_keywords):
            for k2 in unique_paper_keywords[i+1:]:  # Only iterate over remaining keywords to avoid duplicates
                idx1 = keyword_to_idx[k1]
                idx2 = keyword_to_idx[k2]
                
                # Increment both matrix[k1][k2] and matrix[k2][k1] for symmetry
                matrix[idx1][idx2] += 1
                matrix[idx2][idx1] += 1
    
    # Return symmetric matrix as DataFrame
    return pd.DataFrame(matrix, index=unique_keywords, columns=unique_keywords)


def render_heatmap(matrix: pd.DataFrame) -> matplotlib.figure.Figure:
    """
    Generates heatmap visualization.
    
    Args:
        matrix: Co-occurrence matrix
        
    Returns:
        Matplotlib figure object
    """
    # Set dynamic figure size based on matrix dimensions
    # Limit maximum size to prevent memory issues
    n = len(matrix)
    
    # Calculate appropriate figure size (max 20 inches to prevent huge images)
    base_size = 0.4  # inches per keyword
    figsize = min(20, max(8, n * base_size))
    
    # Adjust font sizes based on matrix size
    if n > 30:
        title_fontsize = 14
        label_fontsize = 10
        annot_fontsize = 6
        show_annot = False  # Don't show numbers if too many keywords
    elif n > 20:
        title_fontsize = 15
        label_fontsize = 11
        annot_fontsize = 7
        show_annot = True
    else:
        title_fontsize = 16
        label_fontsize = 12
        annot_fontsize = 8
        show_annot = True
    
    # Create figure and axis with constrained layout
    fig, ax = plt.subplots(figsize=(figsize, figsize), dpi=100)
    
    # Generate heatmap using seaborn
    sns.heatmap(
        matrix,
        cmap="YlGnBu",      # Yellow-Green-Blue color scheme
        annot=show_annot,    # Enable annotations only for smaller matrices
        fmt='g',             # Format for annotations (general format)
        ax=ax,               # Use the created axis
        cbar_kws={'label': '共现次数'},
        annot_kws={'fontsize': annot_fontsize} if show_annot else {}
    )
    
    # Set title and labels with dynamic font sizes
    ax.set_title('关键词共现热力图', fontsize=title_fontsize, pad=20)
    ax.set_xlabel('关键词', fontsize=label_fontsize)
    ax.set_ylabel('关键词', fontsize=label_fontsize)
    
    # Rotate labels for better readability
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    # Adjust layout to prevent label cutoff
    plt.tight_layout()
    
    return fig


def main():
    st.title("🔬 研究热点分析工具")
    st.write("分析学术领域的研究趋势和热点话题")
    
    # Check for version upgrade and clear cache if needed
    clear_cache_on_upgrade()
    
    # Show font detection result
    if detected_font:
        st.success(f"✅ 已检测到中文字体: {detected_font}")
    else:
        st.warning("⚠️ 未检测到中文字体，热力图可能显示方框。请参考侧边栏的字体安装说明。")
    
    # Add cache clearing mechanism in sidebar
    with st.sidebar:
        st.header("⚙️ 设置")
        
        # LLM API Configuration
        st.subheader("🔑 LLM API 配置")
        st.markdown("**⚠️ 必须配置 API Key 才能使用本工具**")
        
        # API Key input - prominent and required
        api_key_input = st.text_input(
            "API Key (必填)",
            value="",
            type="password",
            help="输入你的 Qwen API Key（必填项）",
            placeholder="sk-xxxxxxxxxxxxxxxxxxxxxxxx",
            key="api_key_input"
        )
        
        # Store API key in session state
        if 'api_key' not in st.session_state:
            st.session_state.api_key = ""
        
        # Update session state when API key changes
        if api_key_input:
            st.session_state.api_key = api_key_input
        
        # Endpoint input
        endpoint_input = st.text_input(
            "API Endpoint",
            value="https://dashscope.aliyuncs.com/compatible-mode/v1",
            help="API 端点地址",
            key="endpoint_input"
        )
        
        # Store endpoint in session state
        if 'endpoint' not in st.session_state:
            st.session_state.endpoint = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        
        if endpoint_input:
            st.session_state.endpoint = endpoint_input
        
        # Show configuration guide
        with st.expander("📖 如何获取 API Key"):
            st.markdown("""
            1. 访问 [阿里云 DashScope](https://dashscope.console.aliyun.com/)
            2. 注册/登录账号
            3. 创建 API Key
            4. 复制并粘贴到上方输入框
            """)
        
        # Validate API key and show appropriate status
        is_api_key_valid = validate_api_key(api_key_input)
        
        if is_api_key_valid:
            st.success("✅ API Key 已配置，可以开始分析")
        else:
            st.warning("⚠️ 请输入 API Key 才能开始分析")
            st.info("👉 点击下方「如何获取 API Key」查看获取方法")
        
        st.markdown("---")
        
        # LLM features toggle
        st.subheader("🤖 智能功能")
        
        use_journal_filter = st.checkbox(
            "识别1区期刊",
            value=True,
            help="使用 LLM 识别领域内的1区期刊，只保留这些期刊的论文，过滤其他论文（需要 API Key）",
            disabled=not bool(api_key_input)
        )
        
        if not api_key_input:
            st.warning("⚠️ 需要配置 API Key 才能使用智能功能")
        
        st.markdown("---")
        
        # Paper limit slider (v3.1 - Performance optimization)
        max_papers = st.slider(
            "最大论文数量",
            min_value=50,
            max_value=300,
            value=100,
            step=50,
            help="限制分析的论文总数，较少的论文处理更快（推荐100篇，约5-10分钟）"
        )
        
        # Keyword limit slider
        max_keywords = st.slider(
            "最大关键词数量",
            min_value=10,
            max_value=30,
            value=20,
            step=5,
            help="限制热力图中显示的关键词数量，避免图片过大"
        )
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("清除缓存", help="清除所有缓存数据，强制重新调用 API"):
                st.cache_data.clear()
                # Also update version file to prevent re-showing upgrade notice
                save_current_version()
                st.success("缓存已清除！")
        
        with col2:
            if st.button("测试网络", help="测试 OpenAlex API 连接"):
                with st.spinner("测试中..."):
                    if test_openalex_connection():
                        st.success("✅ 连接正常")
                    else:
                        st.error("❌ 连接失败")
                        st.info("请检查网络或使用 VPN")
        
        st.markdown("---")
        st.subheader("📖 使用说明")
        st.markdown("""
        **v3.1 优化版本**
        
        **使用步骤：**
        1. ⚠️ **必须配置 API Key**（所有分析都需要 LLM）
        2. 调整论文数量（推荐100篇，约5-10分钟）
        3. 输入研究领域关键词
        4. 选择时间范围
        5. 点击"开始分析"
        6. 查看热力图
        
        **功能说明：**
        - 🔑 **API Key**：必需，用于 LLM 智能关键词提取
        - 🔍 **识别1区期刊**：默认启用，直接在顶级期刊中搜索论文
        - 📊 **最大论文数量**：限制总论文数，减少处理时间
        - 📈 **最大关键词数量**：控制热力图大小
        
        **性能优化（v3.1）：** 
        - ⚡ 可调节论文数量：50-300篇（默认100篇）
        - ⚡ 100篇论文约需5-10分钟处理
        - ⚡ 直接在Q1期刊中搜索，无需过滤
        - ✅ 所有关键词提取均使用 LLM
        
        **处理时间估算：**
        - 50篇：约3-5分钟
        - 100篇：约5-10分钟（推荐）
        - 200篇：约10-20分钟
        - 300篇：约15-30分钟
        """)
        
        st.markdown("---")
        st.subheader("🔤 中文字体说明")
        if detected_font:
            st.success(f"当前使用: {detected_font}")
        else:
            st.warning("未检测到中文字体")
            with st.expander("📥 字体安装指南"):
                st.markdown("""
                **Windows 系统：**
                - 通常已预装中文字体
                - 如显示方框，请重启应用
                
                **Linux 系统：**
                ```bash
                # Ubuntu/Debian
                sudo apt-get install fonts-wqy-zenhei
                
                # 或安装思源黑体
                sudo apt-get install fonts-noto-cjk
                ```
                
                **Mac 系统：**
                - 系统自带中文字体
                - 如有问题请重启应用
                
                安装后请重启应用。
                """)
        
        st.markdown("---")
        st.caption("数据来源: OpenAlex (免费开放)")
    
    # Create text input field for domain keywords
    domain = st.text_input(
        "🔍 研究领域关键词",
        placeholder="例如：量子计算、机器学习、深度学习",
        help="输入关键词以搜索学术论文"
    )
    
    # Create date input selectors for start and end dates
    col1, col2 = st.columns(2)
    
    with col1:
        start_date = st.date_input(
            "📅 起始日期",
            value=date(2020, 1, 1),
            help="选择时间范围的开始日期"
        )
    
    with col2:
        end_date = st.date_input(
            "📅 结束日期",
            value=date.today(),
            help="选择时间范围的结束日期"
        )
    
    # Validate API key before allowing analysis
    is_api_key_valid = validate_api_key(api_key_input)
    
    # Show warning if API key is not configured
    if not is_api_key_valid:
        st.warning("⚠️ 请在左侧边栏配置 API Key 后才能开始分析")
    
    # Create submit button to trigger analysis (disabled if no valid API key in v3.0)
    submit_button = st.button(
        "🚀 开始分析", 
        type="primary",
        disabled=not is_api_key_valid,
        help="需要配置 API Key 才能开始分析" if not is_api_key_valid else "开始分析研究热点"
    )
    
    # Process form submission
    if submit_button:
        # API Key validation: ensure API key is configured
        if not validate_api_key(api_key_input):
            st.error("⚠️ 需要配置 API Key 才能使用")
            st.info("""
            **如何获取 API Key：**
            
            1. 访问 [阿里云 DashScope](https://dashscope.console.aliyun.com/)
            2. 注册/登录账号
            3. 在控制台创建 API Key
            4. 复制 API Key 并粘贴到左侧边栏的输入框中
            
            **帮助说明：**
            - API Key 是必需的，用于 LLM 智能关键词提取
            - 请确保 API Key 有效且有足够的配额
            - 如有问题，请查看阿里云文档或联系技术支持
            """)
        # Input validation: reject empty domain keywords
        elif not domain or not domain.strip():
            st.error("请输入研究领域关键词")
        # Date validation: ensure start_date ≤ end_date
        elif not validate_date_range(start_date, end_date):
            st.error("开始日期必须早于或等于结束日期")
        else:
            # All validations passed - proceed with analysis
            try:
                # Step 1: Identify top journals (if enabled)
                journals = []
                if use_journal_filter and api_key_input:
                    with st.spinner("🔍 正在识别1区期刊..."):
                        journals = identify_top_journals(domain, api_key_input, endpoint_input)
                    
                    if journals:
                        st.success(f"✅ 已识别 {len(journals)} 个1区期刊")
                        with st.expander("📋 查看期刊列表（只会保留这些期刊的论文）"):
                            st.markdown("**识别到的1区期刊：**")
                            for i, journal in enumerate(journals, 1):
                                st.write(f"{i}. {journal}")
                        st.info("💡 接下来将只保留来自这些1区期刊的论文，过滤其他论文")
                    else:
                        st.info("ℹ️ 未识别到期刊，将搜索所有论文")
                
                # Step 2: Fetch papers from OpenAlex
                with st.spinner("📚 正在从 OpenAlex 获取论文数据..."):
                    start_year = start_date.year
                    end_year = end_date.year
                    papers = fetch_openalex_data(domain, start_year, end_year, journals if journals else None, max_papers=max_papers)
                
                # If journal filtering resulted in no papers, try without filtering
                if not papers and journals:
                    st.warning("⚠️ 在指定期刊中未找到论文，尝试搜索所有论文...")
                    papers = fetch_openalex_data(domain, start_year, end_year, None, max_papers=max_papers)
                
                # Check if we got any papers
                if not papers:
                    # Display enhanced error message for empty results
                    st.error("❌ 未找到任何论文")
                    st.info("""
                    **可能的原因：**
                    - 🔍 关键词过于具体或拼写错误
                    - 📅 时间范围内没有相关论文
                    - 📚 1区期刊筛选过于严格
                    - 🌐 OpenAlex 数据库中没有相关数据
                    
                    **建议的解决方案：**
                    
                    1. **调整搜索关键词**
                       - 尝试使用更通用的关键词
                       - 使用英文关键词（OpenAlex 主要收录英文文献）
                       - 检查关键词拼写是否正确
                       - 示例：将 "quantum error correction" 改为 "quantum computing"
                    
                    2. **扩大时间范围**
                       - 尝试更长的时间跨度（如最近5年）
                       - 确认起始日期早于结束日期
                    
                    3. **禁用1区期刊筛选**
                       - 在左侧边栏取消勾选"识别1区期刊"
                       - 这将搜索所有期刊的论文，而不仅限于顶级期刊
                    
                    4. **尝试其他领域**
                       - 某些新兴领域可能数据较少
                       - 尝试相关但更成熟的研究领域
                    
                    **提示：** 如果问题持续，可以先禁用1区筛选，查看是否能找到论文。
                    """)
                    st.stop()
                
                st.success(f"✅ 已从 OpenAlex 获取 {len(papers)} 篇论文")
                
                # Step 3: Extract keywords from papers using LLM (mandatory in v3.0)
                with st.spinner("🤖 LLM 智能提取关键词..."):
                    try:
                        keyword_lists = extract_keywords_with_llm_single(
                            papers, 
                            api_key=api_key_input,
                            endpoint=endpoint_input
                        )
                    except Exception as e:
                        # Display clear error message in Chinese
                        error_msg = str(e)
                        st.error(f"❌ LLM 关键词提取失败")
                        
                        # Show the specific error details
                        if "所有论文" in error_msg:
                            st.error(error_msg)
                        else:
                            st.error(f"错误详情: {error_msg}")
                        
                        # Display detailed troubleshooting steps in Chinese
                        st.info("""
                        **可能的原因：**
                        - ❌ API Key 无效、过期或配额不足
                        - 🌐 网络连接问题或防火墙阻止
                        - 🔗 API 端点配置错误
                        - ⏱️ LLM 服务暂时不可用或响应超时
                        - 📄 论文内容格式问题
                        
                        **解决方案（请按顺序尝试）：**
                        
                        1. **检查 API Key**
                           - 在左侧边栏确认 API Key 已正确输入
                           - 访问 [阿里云控制台](https://dashscope.console.aliyun.com/) 验证 API Key 状态
                           - 确认 API Key 有足够的配额
                        
                        2. **检查网络连接**
                           - 点击左侧边栏的"测试网络"按钮
                           - 确认可以访问 OpenAlex API
                           - 如在国内，可能需要使用 VPN
                        
                        3. **检查 API 端点**
                           - 确认端点地址为: `https://dashscope.aliyuncs.com/compatible-mode/v1`
                           - 如使用其他 LLM 服务，请确认端点正确
                        
                        4. **调整搜索参数**
                           - 尝试缩短时间范围以减少论文数量
                           - 尝试更具体的关键词
                        
                        5. **稍后重试**
                           - LLM 服务可能暂时繁忙
                           - 等待几分钟后重新尝试
                        
                        **重要提示：** v3.0 版本仅支持 LLM 提取，无规则提取备选方案。必须解决 LLM 连接问题才能继续。
                        """)
                        st.stop()
                
                # Check if we got any keywords
                if not keyword_lists:
                    st.warning("⚠️ 无法从论文中提取关键词")
                    st.stop()
                
                st.success(f"✅ 已从 {len(keyword_lists)} 篇论文中提取关键词")
                
                # Count total unique keywords
                all_keywords = set()
                for keywords in keyword_lists:
                    all_keywords.update(keywords)
                total_keywords = len(all_keywords)
                
                # Show info if keywords will be limited
                if total_keywords > max_keywords:
                    st.info(f"ℹ️ 共提取 {total_keywords} 个关键词，将显示出现频率最高的前 {max_keywords} 个关键词")
                
                # Step 4: Build co-occurrence matrix
                with st.spinner("📊 正在构建共现矩阵..."):
                    matrix = build_cooccurrence_matrix(keyword_lists, max_keywords=max_keywords)
                
                # Check if matrix has data
                if matrix.empty or len(matrix) == 0:
                    st.warning("⚠️ 没有可用的共现数据进行可视化")
                    st.stop()
                
                st.success(f"✅ 已构建 {len(matrix)}×{len(matrix)} 共现矩阵")
                
                # Step 5: Render heatmap
                with st.spinner("🎨 正在生成热力图..."):
                    fig = render_heatmap(matrix)
                
                # Display final heatmap
                st.subheader("📈 关键词共现热力图")
                st.pyplot(fig)
                
                # Display summary statistics
                st.subheader("📊 分析摘要")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("分析论文数", len(papers))
                with col2:
                    st.metric("唯一关键词数", len(matrix))
                with col3:
                    total_cooccurrences = int(matrix.sum().sum() / 2)  # Divide by 2 because matrix is symmetric
                    st.metric("总共现次数", total_cooccurrences)
                
            except Exception as e:
                # Catch any unexpected errors and display user-friendly message
                st.error(f"❌ 分析过程中发生错误: {str(e)}")
                st.info("💡 应用程序仍在运行。请重试或调整搜索参数。")

if __name__ == "__main__":
    main()
