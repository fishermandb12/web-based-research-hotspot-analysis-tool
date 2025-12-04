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

# Load environment variables from .env file
load_dotenv()

# Configure matplotlib to support Chinese characters
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # Fix minus sign display issue


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


@st.cache_data
def identify_top_journals(domain: str) -> list[str]:
    """
    Invokes LLM to generate top-tier journal names.
    
    Args:
        domain: Research field keyword
        
    Returns:
        List of journal names (e.g., ["Nature", "Science"])
    """
    try:
        # Get LLM configuration from environment variables
        api_key = os.environ.get("LLM_API_KEY", "")
        base_url = os.environ.get("LLM_ENDPOINT", None)
        
        # If no API key is configured, return empty list
        if not api_key:
            st.warning("未配置 LLM API 密钥，跳过期刊筛选")
            return []
        
        # Initialize OpenAI client (compatible with Qwen API)
        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        
        # Create LLM prompt
        prompt = f"输出 ONLY 逗号分隔的英文期刊名，不要其他内容。领域：{domain}"
        
        # Call LLM
        response = client.chat.completions.create(
            model="qwen-plus",  # Default Qwen model
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        # Extract response text
        llm_output = response.choices[0].message.content.strip()
        
        # Parse comma-separated journal names
        journals = parse_comma_separated(llm_output)
        
        return journals
        
    except Exception as e:
        # Log error and continue without journal filtering
        st.warning(f"LLM 服务暂时不可用，继续使用基础功能: {str(e)}")
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


@st.cache_data
def extract_keywords_batch(papers: list[dict]) -> list[list[str]]:
    """
    Extracts keywords from paper texts using LLM.
    
    Args:
        papers: List of paper dictionaries with 'title' and 'abstract' fields
        
    Returns:
        List of keyword lists, one per paper
    """
    try:
        # Get LLM configuration from environment variables
        api_key = os.environ.get("LLM_API_KEY", "")
        base_url = os.environ.get("LLM_ENDPOINT", None)
        
        # If no API key is configured, return empty list
        if not api_key:
            st.warning("未配置 LLM API 密钥，无法提取关键词")
            return []
        
        # Initialize OpenAI client (compatible with Qwen API)
        client = OpenAI(api_key=api_key, base_url=base_url) if base_url else OpenAI(api_key=api_key)
        
        keyword_lists = []
        
        # Process each paper
        for paper in papers:
            # Skip papers lacking title or abstract
            title = paper.get("title", "")
            abstract = paper.get("abstract", "")
            
            if not title or not abstract:
                continue
            
            # Create LLM prompt template
            prompt = f"从文本中提取3-5个核心关键词，用中文逗号分隔：\n标题：{title}\n摘要：{abstract}"
            
            try:
                # Call LLM
                response = client.chat.completions.create(
                    model="qwen-plus",  # Default Qwen model
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=200
                )
                
                # Extract response text
                llm_output = response.choices[0].message.content.strip()
                
                # Parse LLM output using comma-separated parsing function
                keywords = parse_comma_separated(llm_output)
                
                # Add to keyword lists if we got any keywords
                if keywords:
                    keyword_lists.append(keywords)
                    
            except Exception as e:
                # Log error for this paper and continue with others
                st.warning(f"提取论文关键词失败 '{title[:50]}...': {str(e)}")
                continue
        
        return keyword_lists
        
    except Exception as e:
        # Log error and return empty list
        st.warning(f"LLM 服务暂时不可用，无法提取关键词: {str(e)}")
        return []


@st.cache_data
def fetch_openalex_data(domain: str, start_year: int, end_year: int) -> list[dict]:
    """
    Queries OpenAlex API for publications.
    
    Args:
        domain: Search keyword
        start_year: Beginning of time range (YYYY)
        end_year: End of time range (YYYY)
        
    Returns:
        List of paper dictionaries with 'title', 'abstract', 'id' fields
    """
    try:
        # Construct API endpoint
        url = "https://api.openalex.org/works"
        
        # Construct query parameters
        params = {
            "search": domain,
            "filter": f"publication_year:{start_year}-{end_year}",
            "per_page": 100
        }
        
        # Make API request
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        # Parse JSON response
        data = response.json()
        results = data.get("results", [])
        
        # Handle empty results
        if not results:
            st.warning("未找到 OpenAlex 数据，请检查关键词或时间范围")
            return []
        
        # Extract relevant fields from results and reconstruct abstracts
        papers = []
        for result in results:
            # Get abstract inverted index
            abstract_inverted_index = result.get("abstract_inverted_index", {})
            
            # Skip papers without abstract
            if not abstract_inverted_index:
                continue
            
            # Reconstruct abstract from inverted index
            abstract = reconstruct_abstract_from_inverted_index(abstract_inverted_index)
            
            # Extract title
            title = result.get("title", "")
            
            # Skip papers without title or abstract
            if not title or not abstract:
                continue
            
            paper = {
                "id": result.get("id", ""),
                "title": title,
                "abstract": abstract,
                "publication_year": result.get("publication_year", 0)
            }
            papers.append(paper)
        
        return papers
        
    except requests.exceptions.RequestException as e:
        st.error(f"无法连接到 OpenAlex API，请检查网络连接: {str(e)}")
        return []
    except Exception as e:
        st.error(f"处理 OpenAlex 数据时出错: {str(e)}")
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
    
    # Add cache clearing mechanism in sidebar
    with st.sidebar:
        st.header("⚙️ 设置")
        
        # Keyword limit slider
        max_keywords = st.slider(
            "最大关键词数量",
            min_value=10,
            max_value=50,
            value=30,
            step=5,
            help="限制热力图中显示的关键词数量，避免图片过大"
        )
        
        st.markdown("---")
        
        if st.button("清除缓存", help="清除所有缓存数据，强制重新调用 API"):
            st.cache_data.clear()
            st.success("缓存已清除！")
        
        st.markdown("---")
        st.subheader("📖 使用说明")
        st.markdown("""
        1. 输入研究领域关键词
        2. 选择时间范围
        3. 调整最大关键词数量
        4. 点击"开始分析"按钮
        5. 查看关键词共现热力图
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
    
    # Create submit button to trigger analysis
    submit_button = st.button("🚀 开始分析", type="primary")
    
    # Process form submission
    if submit_button:
        # Input validation: reject empty domain keywords
        if not domain or not domain.strip():
            st.error("请输入研究领域关键词")
        # Date validation: ensure start_date ≤ end_date
        elif not validate_date_range(start_date, end_date):
            st.error("开始日期必须早于或等于结束日期")
        else:
            # All validations passed - proceed with analysis
            try:
                # Step 1: Identify top-tier journals (optional, for future filtering)
                with st.spinner("🔍 正在识别一区期刊..."):
                    journals = identify_top_journals(domain)
                    if journals:
                        st.info(f"✅ 已识别 {len(journals)} 个一区期刊")
                
                # Step 2: Fetch papers from OpenAlex
                with st.spinner("📚 正在从 OpenAlex 获取论文数据..."):
                    start_year = start_date.year
                    end_year = end_date.year
                    papers = fetch_openalex_data(domain, start_year, end_year)
                
                # Check if we got any papers
                if not papers:
                    # Warning already displayed by fetch_openalex_data
                    st.stop()
                
                st.success(f"✅ 已从 OpenAlex 获取 {len(papers)} 篇论文")
                
                # Step 3: Extract keywords from papers
                with st.spinner("🤖 正在使用 LLM 提取关键词..."):
                    keyword_lists = extract_keywords_batch(papers)
                
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
