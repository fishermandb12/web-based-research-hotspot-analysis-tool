# Research Hotspot Analysis Tool

A web-based research hotspot analysis tool that enables researchers to analyze trending topics in academic fields by querying OpenAlex API, using LLM for intelligent keyword extraction, and visualizing keyword co-occurrence patterns through heatmaps.

## ⚠️ Version 3.0 - LLM-Only Mode

**Important:** v3.0 requires an LLM API Key for all operations. The system now uses LLM exclusively for keyword extraction to ensure consistent, high-quality semantic understanding across all analyses.

## Features

- 🔍 **OpenAlex Integration**: Query academic publications (free, no API key required)
- 🤖 **LLM-Powered Keyword Extraction** (⚠️ **API Key Required**): Intelligent semantic understanding using Large Language Models
  - Extracts specific research directions (e.g., "Transformer Architecture", "Quantum Error Correction")
  - Filters out broad parent domains (e.g., "Computer Science", "Physics")
  - Focuses on concrete technical terms and methodologies
  - Automatic filtering of overly long phrases and generic terms
  - **LLM-only mode**: No rule-based fallback, ensuring consistent quality
- 🎯 **Q1 Journal Filtering**: Automatically identifies and filters top-tier journals (default enabled, requires API Key)
- 📊 **Co-occurrence Matrix Visualization**: Interactive heatmaps showing keyword relationships
- ⚡ **Efficient Caching**: Improved performance with smart caching
- 🎨 **Chinese Font Support**: Automatic detection and configuration
- 🔧 **Robust Error Handling**: Detailed error messages and troubleshooting guidance

## Installation

### Prerequisites

- Python 3.8 or higher
- Internet connection for API access
- **LLM API Key** (required for v3.0)

### Steps

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Obtain an LLM API Key:
   - Visit [阿里云 DashScope](https://dashscope.console.aliyun.com/)
   - Register/login to your account
   - Create an API Key
   - Copy the API Key for use in the application

## Configuration

### Required: LLM API Key

**v3.0 requires an API Key for all operations.** The API Key is configured through the application interface:

1. Start the application (see Usage section below)
2. In the sidebar, find "🔑 LLM API 配置"
3. Paste your API Key in the input field
4. Confirm the API Endpoint (default value is usually correct)
5. You should see "✅ API Key 已配置" confirmation

**Note:** The API Key is stored in session state and is not persisted. You'll need to enter it each time you start the application.

### Optional: Chinese Font Configuration

The application automatically detects and uses Chinese fonts. If you see boxes instead of Chinese characters:

**Linux:**
```bash
sudo apt-get install fonts-wqy-zenhei
```

**Windows/Mac:**
Usually no configuration needed. Restart the application if needed.

## Usage

### Starting the Application

Run the application:
```bash
streamlit run app.py
```

The application will open in your default web browser.

### First-Time Setup

1. **Configure API Key** (required):
   - In the sidebar, find "🔑 LLM API 配置"
   - Enter your API Key
   - Confirm the API Endpoint
   - Wait for "✅ API Key 已配置" confirmation

2. **Adjust Settings** (optional):
   - "识别1区期刊" checkbox: Enabled by default (recommended)
   - "最大关键词数量" slider: Adjust keyword count (10-30, default 20)

### Running an Analysis

1. **Enter Research Domain**: Type your research field keyword (e.g., "quantum computing", "transformer architecture")
2. **Select Time Range**: Choose start and end dates for your analysis period
3. **Start Analysis**: Click "🚀 开始分析" button
4. **View Results**: 
   - Q1 journal list (if filtering enabled)
   - Processing progress
   - Generated heatmap showing keyword co-occurrence patterns
   - Statistics (papers analyzed, unique keywords, co-occurrences)

### Tips for Best Results

- **Use specific keywords**: "transformer architecture" is better than "AI"
- **Enable Q1 filtering**: Ensures high-quality papers (default enabled)
- **Adjust time range**: Recent 1-2 years for latest trends, 3-5 years for broader view
- **Tune keyword count**: 15-25 keywords usually provides the best visualization
- **Use caching**: Same queries will use cached results for faster performance

## Data Sources

- **OpenAlex API**: Free, open-access scholarly publication metadata (no API key required)
- **LLM Service**: Qwen via DashScope (API key required)

## Dependencies

### Core Dependencies
- `streamlit>=1.28.0`: Web application framework
- `seaborn>=0.12.0`: Statistical data visualization
- `pandas>=2.0.0`: Data manipulation and analysis
- `requests>=2.31.0`: HTTP library for API calls
- `matplotlib>=3.7.0`: Plotting library
- `openai>=1.0.0`: OpenAI-compatible API client (for Qwen)

### Development Dependencies
- `hypothesis>=6.92.0`: Property-based testing
- `pytest>=7.4.0`: Testing framework

## Troubleshooting

### Analysis Button Disabled

**Problem**: The "开始分析" button is grayed out.

**Solution**: 
- Ensure you have entered an API Key in the sidebar
- Check that the API Key field is not empty or whitespace only

### LLM Extraction Failed

**Problem**: Error message "LLM 关键词提取失败".

**Solutions**:
1. Check API Key validity (visit DashScope console)
2. Test network connection using "测试网络" button
3. Verify API Endpoint is correct
4. Check API quota/credits
5. Try again later if service is temporarily unavailable

### No Papers Found

**Problem**: "未找到 OpenAlex 数据" warning.

**Solutions**:
1. Try different or more general keywords
2. Adjust time range (expand the date range)
3. Disable Q1 filtering if too restrictive
4. Check network connection to OpenAlex

### Poor Quality Keywords

**Problem**: Keywords are too generic or not relevant.

**Solutions**:
1. Use more specific domain keywords
2. Enable Q1 journal filtering
3. Adjust time range to focus on recent papers
4. Reduce keyword count for better focus

## Version History

- **v3.0.0** (2024-12-05): LLM-Only Mode - Major architectural refactoring
- **v2.3.0** (2024-12-04): Journal filtering + Optional features
- **v2.2.0** (2024-12-04): LLM intelligent extraction
- **v2.1.0** (2024-12-04): Keyword extraction optimization
- **v2.0.0** (2024-12-04): Free mode with OpenAlex metadata
- **v1.x**: Initial releases

See `更新日志.md` for detailed changelog.

## Migration from v2.x

If you're upgrading from v2.x:

1. **Obtain API Key**: Required for v3.0 (see Installation section)
2. **Remove .env file**: No longer used for configuration
3. **Clear cache**: Use "清除缓存" button in the application
4. **Update workflow**: Q1 filtering is now enabled by default
5. **Expect slower processing**: LLM extraction is more thorough but takes longer

See `v3.0更新说明.md` for detailed migration guide.

## License

This project is provided as-is for research and educational purposes.

## Support

For issues, questions, or feedback:
- Check the troubleshooting section above
- Review `v3.0更新说明.md` for detailed documentation
- Check `更新日志.md` for version-specific information
