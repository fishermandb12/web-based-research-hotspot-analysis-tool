# Research Hotspot Analysis Tool

A web-based research hotspot analysis tool that enables researchers to analyze trending topics in academic fields by querying OpenAlex API, extracting keywords from papers, and visualizing keyword co-occurrence patterns through heatmaps.

## Features

- Query OpenAlex API for academic publications (free, no API key required)
- LLM-based journal identification and keyword extraction
- Co-occurrence matrix visualization with heatmaps
- Efficient caching for improved performance

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### LLM API Configuration (Required for Full Functionality)

For LLM-based journal identification and keyword extraction, you need to configure your API key.

#### Method 1: Using .env file (Recommended)

1. Copy the example environment file:
```bash
copy .env.example .env
```

2. Edit `.env` file and add your API credentials:
```
LLM_API_KEY=your_qwen_api_key_here
LLM_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
```

3. Get your Qwen API key from: https://dashscope.console.aliyun.com/

#### Method 2: Using Environment Variables

**Windows CMD:**
```cmd
set LLM_API_KEY=your_api_key_here
set LLM_ENDPOINT=https://dashscope.aliyuncs.com/compatible-mode/v1
streamlit run app.py
```

**Windows PowerShell:**
```powershell
$env:LLM_API_KEY="your_api_key_here"
$env:LLM_ENDPOINT="https://dashscope.aliyuncs.com/compatible-mode/v1"
streamlit run app.py
```

**Linux/Mac:**
```bash
export LLM_API_KEY="your_api_key_here"
export LLM_ENDPOINT="https://dashscope.aliyuncs.com/compatible-mode/v1"
streamlit run app.py
```

**Note:** The application will work without LLM configuration but with limited functionality (no journal filtering or keyword extraction).

## Usage

Run the application:
```bash
streamlit run app.py
```

The application will open in your default web browser.

## How to Use

1. Enter your research domain keyword (e.g., "quantum computing")
2. Select the start and end dates for your analysis period
3. Click submit to analyze research hotspots
4. View the generated heatmap showing keyword co-occurrence patterns

## Requirements

- Python 3.8 or higher
- Internet connection for API access

## Data Source

This tool uses OpenAlex (free open access) for publication metadata.

## Dependencies

- streamlit: Web application framework
- seaborn: Statistical data visualization
- pandas: Data manipulation and analysis
- requests: HTTP library for API calls
- matplotlib: Plotting library
- openai: OpenAI API client (compatible with Qwen)
- python-dotenv: Environment variable management
- hypothesis: Property-based testing (development)
- pytest: Testing framework (development)
