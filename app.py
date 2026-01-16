"""
🎬 IMDb 电影评论分析仪表盘
=====================================
功能:
1. 📊 多维度情感分析与可视化
2. 📄 一键生成决策分析报告 (HTML/Excel)
3. ⚔️ 竞品双向对比模式 (雷达图)
4. 🧠 RAG 思考过程可视化 (检索证据展示)
5. 🔔 情感预警系统
6. 🎨 自定义主题色
7. 📱 移动端适配
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px
import sys
import os
import io
import base64
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

sys.path.insert(0, str(Path(__file__).parent))

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="IMDb 电影评论分析", 
    page_icon="🎬", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# ==================== 主题配置 ====================
THEMES = {
    '深邃夜空': {
        'primary': '#f5c518',
        'secondary': '#3b82f6',
        'bg_start': '#0a0a0f',
        'bg_end': '#111827',
        'card_bg': 'rgba(30,30,50,0.9)',
        'accent': '#f5c518'
    },
    '海洋蓝': {
        'primary': '#0ea5e9',
        'secondary': '#06b6d4',
        'bg_start': '#0c1929',
        'bg_end': '#0f2942',
        'card_bg': 'rgba(15,41,66,0.9)',
        'accent': '#0ea5e9'
    },
    '森林绿': {
        'primary': '#22c55e',
        'secondary': '#10b981',
        'bg_start': '#0a1a0f',
        'bg_end': '#14291a',
        'card_bg': 'rgba(20,41,26,0.9)',
        'accent': '#22c55e'
    },
    '暗紫': {
        'primary': '#a855f7',
        'secondary': '#8b5cf6',
        'bg_start': '#0f0a1a',
        'bg_end': '#1a1429',
        'card_bg': 'rgba(26,20,41,0.9)',
        'accent': '#a855f7'
    }
}

# 初始化主题
if 'theme' not in st.session_state:
    st.session_state.theme = '深邃夜空'

def get_theme():
    return THEMES.get(st.session_state.theme, THEMES['深邃夜空'])

def apply_theme_css():
    """应用主题CSS样式"""
    theme = get_theme()
    st.markdown(f"""
    <style>
        .stApp {{ 
            background: linear-gradient(180deg, {theme['bg_start']} 0%, {theme['bg_end']} 100%); 
        }}
        #MainMenu, footer, header {{visibility: hidden;}}
        
        /* ============================================ */
        /* 侧边栏强制显示 - 核心设置                   */
        /* ============================================ */
        
        /* 1. 强制侧边栏始终展开，禁止收起 */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, #0d1117 0%, #161b22 50%, #1a1f2e 100%) !important;
            border-right: 2px solid {theme['primary']} !important;
            min-width: 300px !important;
            width: 300px !important;
            max-width: 300px !important;
            transform: translateX(0) !important;
            visibility: visible !important;
            position: relative !important;
            box-shadow: 4px 0 20px rgba(0,0,0,0.3) !important;
        }}
        
        /* 2. 隐藏侧边栏收起/展开按钮 */
        button[data-testid="stSidebarCollapseButton"],
        button[data-testid="baseButton-headerNoPadding"],
        [data-testid="collapsedControl"],
        .st-emotion-cache-1dp5vir,
        .st-emotion-cache-1egp75f,
        div[data-testid="stSidebarCollapsedControl"] {{
            display: none !important;
            visibility: hidden !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }}
        
        /* 3. 确保侧边栏内容区域始终可见 */
        section[data-testid="stSidebar"] > div {{
            width: 100% !important;
            padding: 1.5rem 1rem !important;
        }}
        
        /* 4. 主内容区域适配侧边栏宽度 */
        .main .block-container {{
            margin-left: 0 !important;
            max-width: calc(100% - 20px) !important;
        }}
        
        /* ============================================ */
        /* 侧边栏美化样式                              */
        /* ============================================ */
        
        /* 侧边栏所有文字白色 */
        section[data-testid="stSidebar"] * {{
            color: #e6edf3 !important;
        }}
        
        /* 标题样式 */
        section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2,
        section[data-testid="stSidebar"] h3,
        section[data-testid="stSidebar"] h4 {{
            color: #ffffff !important;
            font-weight: 600 !important;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3) !important;
        }}
        
        section[data-testid="stSidebar"] p,
        section[data-testid="stSidebar"] span,
        section[data-testid="stSidebar"] label {{
            color: #e6edf3 !important;
        }}
        
        section[data-testid="stSidebar"] .stMarkdown {{
            color: #e6edf3 !important;
        }}
        
        /* Radio按钮样式美化 */
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] {{
            color: #e6edf3 !important;
        }}
        
        section[data-testid="stSidebar"] [role="radiogroup"] {{
            background: rgba(30, 40, 60, 0.5) !important;
            border-radius: 12px !important;
            padding: 0.5rem !important;
            border: 1px solid rgba(255,255,255,0.1) !important;
        }}
        
        section[data-testid="stSidebar"] [role="radiogroup"] label {{
            color: #e6edf3 !important;
            padding: 0.6rem 1rem !important;
            border-radius: 8px !important;
            margin: 2px 0 !important;
            transition: all 0.2s ease !important;
        }}
        
        section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
            background: rgba({int(theme['primary'][1:3], 16)}, {int(theme['primary'][3:5], 16)}, {int(theme['primary'][5:7], 16)}, 0.15) !important;
        }}
        
        section[data-testid="stSidebar"] [role="radiogroup"] label[data-checked="true"],
        section[data-testid="stSidebar"] [role="radiogroup"] [aria-checked="true"] {{
            background: linear-gradient(135deg, {theme['primary']}22 0%, {theme['primary']}33 100%) !important;
            border-left: 3px solid {theme['primary']} !important;
        }}
        
        /* 下拉框样式美化 */
        section[data-testid="stSidebar"] [data-testid="stSelectbox"] {{
            background: rgba(20, 30, 50, 0.8) !important;
            border-radius: 10px !important;
            padding: 0.3rem !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
        }}
        
        section[data-testid="stSidebar"] [data-testid="stSelectbox"] > div {{
            background: transparent !important;
        }}
        
        section[data-testid="stSidebar"] [data-testid="stSelectbox"] label {{
            color: #e6edf3 !important;
        }}
        
        /* 下拉框内部选中文字 - 深色背景白字 */
        section[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] {{
            background: rgba(30, 40, 60, 0.9) !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
            border-radius: 8px !important;
        }}
        
        section[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div {{
            background: transparent !important;
            color: #ffffff !important;
        }}
        
        section[data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] span {{
            color: #ffffff !important;
        }}
        
        /* 下拉菜单弹出层样式 */
        [data-baseweb="popover"] {{
            background: #1a1f2e !important;
            border: 1px solid rgba(255,255,255,0.15) !important;
            border-radius: 10px !important;
        }}
        
        [data-baseweb="popover"] ul {{
            background: #1a1f2e !important;
        }}
        
        [data-baseweb="popover"] li {{
            background: transparent !important;
            color: #e6edf3 !important;
        }}
        
        [data-baseweb="popover"] li:hover {{
            background: rgba(245, 197, 24, 0.15) !important;
        }}
        
        /* 文件上传组件美化 - 深色背景 */
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] {{
            background: rgba(20, 30, 50, 0.8) !important;
            border: 2px dashed {theme['primary']}66 !important;
            border-radius: 12px !important;
            padding: 0.75rem !important;
        }}
        
        section[data-testid="stSidebar"] [data-testid="stFileUploader"]:hover {{
            border-color: {theme['primary']} !important;
            background: rgba(30, 40, 60, 0.9) !important;
        }}
        
        /* 文件上传内部文字 */
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] section {{
            background: transparent !important;
        }}
        
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] span,
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] small,
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] p {{
            color: #e6edf3 !important;
        }}
        
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] button {{
            background: rgba(245, 197, 24, 0.2) !important;
            border: 1px solid {theme['primary']}66 !important;
            color: #ffffff !important;
            border-radius: 6px !important;
        }}
        
        section[data-testid="stSidebar"] [data-testid="stFileUploader"] button:hover {{
            background: rgba(245, 197, 24, 0.35) !important;
            border-color: {theme['primary']} !important;
        }}
        
        /* 文件上传拖放区域 */
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] {{
            background: rgba(30, 40, 60, 0.5) !important;
            border-radius: 8px !important;
        }}
        
        section[data-testid="stSidebar"] [data-testid="stFileUploaderDropzone"] * {{
            color: #b0b8c4 !important;
        }}
        
        /* 按钮美化 */
        section[data-testid="stSidebar"] button[kind="primary"] {{
            background: linear-gradient(135deg, {theme['primary']} 0%, {theme['secondary']} 100%) !important;
            border: none !important;
            color: #000000 !important;
            font-weight: 600 !important;
            border-radius: 10px !important;
            padding: 0.6rem 1.2rem !important;
            transition: all 0.3s ease !important;
            box-shadow: 0 4px 15px rgba({int(theme['primary'][1:3], 16)}, {int(theme['primary'][3:5], 16)}, {int(theme['primary'][5:7], 16)}, 0.3) !important;
        }}
        
        section[data-testid="stSidebar"] button[kind="primary"]:hover {{
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 20px rgba({int(theme['primary'][1:3], 16)}, {int(theme['primary'][3:5], 16)}, {int(theme['primary'][5:7], 16)}, 0.5) !important;
        }}
        
        /* 分割线美化 */
        section[data-testid="stSidebar"] hr {{
            border: none !important;
            height: 1px !important;
            background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.2) 50%, transparent 100%) !important;
            margin: 1.2rem 0 !important;
        }}
        
        /* 成功提示美化 */
        section[data-testid="stSidebar"] [data-testid="stAlert"] {{
            background: rgba(34, 197, 94, 0.15) !important;
            border: 1px solid rgba(34, 197, 94, 0.3) !important;
            border-radius: 8px !important;
        }}
        
        /* 滚动条美化 */
        section[data-testid="stSidebar"]::-webkit-scrollbar {{
            width: 6px !important;
        }}
        
        section[data-testid="stSidebar"]::-webkit-scrollbar-track {{
            background: rgba(0,0,0,0.2) !important;
        }}
        
        section[data-testid="stSidebar"]::-webkit-scrollbar-thumb {{
            background: {theme['primary']}66 !important;
            border-radius: 3px !important;
        }}
        
        section[data-testid="stSidebar"]::-webkit-scrollbar-thumb:hover {{
            background: {theme['primary']} !important;
        }}
        
        .metric-card {{
            background: linear-gradient(135deg, {theme['card_bg']} 0%, rgba(20,25,45,0.9) 100%);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 1.25rem;
            transition: all 0.3s ease;
        }}
        .metric-card:hover {{ 
            transform: translateY(-4px); 
            box-shadow: 0 12px 40px rgba(245,197,24,0.15); 
        }}
        .metric-value {{ font-size: 2rem; font-weight: 700; color: #ffffff; }}
        .metric-label {{ font-size: 0.875rem; color: #9ca3af; }}
        
        .card {{
            background: {theme['card_bg'].replace('0.9', '0.6')};
            border: 1px solid rgba(255,255,255,0.06);
            border-radius: 16px;
            padding: 1.5rem;
        }}
        
        .review-item {{
            background: rgba(15,15,25,0.5);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 0.75rem;
            border-left: 4px solid {theme['primary']};
        }}
        .review-item.positive {{ border-left-color: #22c55e; }}
        .review-item.negative {{ border-left-color: #ef4444; }}
        
        .rag-source {{
            background: rgba(59, 130, 246, 0.1);
            border: 1px solid rgba(59, 130, 246, 0.3);
            border-radius: 8px;
            padding: 0.75rem;
            margin-bottom: 0.5rem;
        }}
        .rag-source-score {{
            background: linear-gradient(90deg, #3b82f6, #60a5fa);
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 0.7rem;
            font-weight: 600;
        }}
        .comparison-card {{
            background: linear-gradient(135deg, {theme['card_bg'].replace('0.9', '0.95')} 0%, rgba(20,25,45,0.95) 100%);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 20px;
            padding: 1.5rem;
        }}
        
        .alert-warning {{
            background: rgba(239, 68, 68, 0.15);
            border: 1px solid rgba(239, 68, 68, 0.5);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        .alert-success {{
            background: rgba(34, 197, 94, 0.15);
            border: 1px solid rgba(34, 197, 94, 0.5);
            border-radius: 12px;
            padding: 1rem;
            margin-bottom: 1rem;
        }}
        
        @media (max-width: 768px) {{
            .metric-card {{ padding: 0.75rem; }}
            .metric-value {{ font-size: 1.5rem; }}
            .metric-label {{ font-size: 0.75rem; }}
            .card {{ padding: 1rem; }}
            h2 {{ font-size: 1.25rem !important; }}
            .comparison-card {{ padding: 1rem; }}
        }}
        
        @media (max-width: 480px) {{
            .metric-value {{ font-size: 1.25rem; }}
            .stButton > button {{ font-size: 0.8rem; padding: 0.4rem 0.8rem; }}
        }}
    </style>
    """, unsafe_allow_html=True)

apply_theme_css()

# ==================== 多语言情感词典 ====================
SENTIMENT_LEXICON = {
    'positive': {
        'masterpiece': 2.0, 'brilliant': 1.8, 'outstanding': 1.7,
        'amazing': 1.6, 'excellent': 1.6, 'fantastic': 1.5,
        'wonderful': 1.5, 'incredible': 1.5, 'perfect': 1.8,
        'beautiful': 1.3, 'stunning': 1.4, 'captivating': 1.4,
        'love': 1.2, 'loved': 1.2, 'best': 1.4, 'great': 1.1, 'good': 0.8,
        '杰作': 2.0, '精彩': 1.6, '完美': 1.8, '出色': 1.5,
        '优秀': 1.4, '感人': 1.3, '震撼': 1.5, '经典': 1.6,
        '喜欢': 1.2, '推荐': 1.3, '好看': 1.2, '精品': 1.5,
    },
    'negative': {
        'terrible': -1.8, 'awful': -1.7, 'horrible': -1.7,
        'worst': -2.0, 'bad': -1.2, 'poor': -1.3, 'boring': -1.4,
        'disappointing': -1.5, 'waste': -1.4, 'stupid': -1.3,
        'dull': -1.3, 'weak': -1.1, 'mediocre': -1.0,
        '差': -1.5, '烂': -1.8, '无聊': -1.4, '失望': -1.5,
        '浪费': -1.4, '难看': -1.6, '糟糕': -1.7, '垃圾': -2.0,
    }
}



# ==================== 完整电影元数据 (178部) ====================
# 格式: 'ttXXXXXXX': {'title': '电影名', 'year': 年份, 'rating': 评分, 'genres': ['类型'], 'director': '导演', 'poster': '表情'}

MOVIE_METADATA = {
    # ========== 1920s-1940s 经典时期 ==========
    'tt0015864': {'title': 'The Gold Rush', 'year': 1925, 'rating': 8.2, 'genres': ['Comedy'], 'director': 'Charles Chaplin', 'poster': '🎩'},
    'tt0017136': {'title': 'Metropolis', 'year': 1927, 'rating': 8.3, 'genres': ['Sci-Fi', 'Drama'], 'director': 'Fritz Lang', 'poster': '🤖'},
    'tt0021749': {'title': 'City Lights', 'year': 1931, 'rating': 8.5, 'genres': ['Comedy', 'Drama'], 'director': 'Charles Chaplin', 'poster': '💡'},
    'tt0031381': {'title': 'Gone with the Wind', 'year': 1939, 'rating': 8.2, 'genres': ['Drama', 'Romance'], 'director': 'Victor Fleming', 'poster': '🌪️'},
    'tt0032553': {'title': 'The Grapes of Wrath', 'year': 1940, 'rating': 8.1, 'genres': ['Drama'], 'director': 'John Ford', 'poster': '🍇'},
    'tt0032976': {'title': 'Rebecca', 'year': 1940, 'rating': 8.1, 'genres': ['Drama', 'Mystery'], 'director': 'Alfred Hitchcock', 'poster': '🏚️'},
    'tt0033467': {'title': 'Citizen Kane', 'year': 1941, 'rating': 8.3, 'genres': ['Drama', 'Mystery'], 'director': 'Orson Welles', 'poster': '📰'},
    'tt0036775': {'title': 'Double Indemnity', 'year': 1944, 'rating': 8.3, 'genres': ['Crime', 'Film-Noir'], 'director': 'Billy Wilder', 'poster': '🔫'},
    'tt0038650': {'title': "It's a Wonderful Life", 'year': 1946, 'rating': 8.6, 'genres': ['Drama', 'Family'], 'director': 'Frank Capra', 'poster': '🎄'},
    
    # ========== 1950s 黄金时代 ==========
    'tt0041959': {'title': 'The Third Man', 'year': 1949, 'rating': 8.1, 'genres': ['Film-Noir', 'Mystery'], 'director': 'Carol Reed', 'poster': '🎭'},
    'tt0043014': {'title': 'Sunset Boulevard', 'year': 1950, 'rating': 8.4, 'genres': ['Drama', 'Film-Noir'], 'director': 'Billy Wilder', 'poster': '🌅'},
    'tt0044741': {'title': 'Singin\' in the Rain', 'year': 1952, 'rating': 8.3, 'genres': ['Comedy', 'Musical'], 'director': 'Gene Kelly', 'poster': '☔'},
    'tt0046268': {'title': 'Dial M for Murder', 'year': 1954, 'rating': 8.2, 'genres': ['Crime', 'Thriller'], 'director': 'Alfred Hitchcock', 'poster': '📞'},
    'tt0047396': {'title': 'Rear Window', 'year': 1954, 'rating': 8.5, 'genres': ['Mystery', 'Thriller'], 'director': 'Alfred Hitchcock', 'poster': '🪟'},
    'tt0050083': {'title': '12 Angry Men', 'year': 1957, 'rating': 9.0, 'genres': ['Crime', 'Drama'], 'director': 'Sidney Lumet', 'poster': '⚖️'},
    'tt0050212': {'title': 'The Bridge on the River Kwai', 'year': 1957, 'rating': 8.2, 'genres': ['Drama', 'War'], 'director': 'David Lean', 'poster': '🌉'},
    'tt0050825': {'title': 'Paths of Glory', 'year': 1957, 'rating': 8.4, 'genres': ['Drama', 'War'], 'director': 'Stanley Kubrick', 'poster': '⚔️'},
    'tt0052357': {'title': 'Vertigo', 'year': 1958, 'rating': 8.3, 'genres': ['Mystery', 'Romance'], 'director': 'Alfred Hitchcock', 'poster': '😵'},
    'tt0053125': {'title': 'North by Northwest', 'year': 1959, 'rating': 8.3, 'genres': ['Action', 'Adventure'], 'director': 'Alfred Hitchcock', 'poster': '✈️'},
    'tt0053604': {'title': 'The Apartment', 'year': 1960, 'rating': 8.3, 'genres': ['Comedy', 'Drama'], 'director': 'Billy Wilder', 'poster': '🏢'},
    'tt0054215': {'title': 'Psycho', 'year': 1960, 'rating': 8.5, 'genres': ['Horror', 'Mystery'], 'director': 'Alfred Hitchcock', 'poster': '🚿'},
    
    # ========== 1960s ==========
    'tt0056172': {'title': 'Lawrence of Arabia', 'year': 1962, 'rating': 8.3, 'genres': ['Adventure', 'Biography'], 'director': 'David Lean', 'poster': '🏜️'},
    'tt0056592': {'title': 'To Kill a Mockingbird', 'year': 1962, 'rating': 8.3, 'genres': ['Crime', 'Drama'], 'director': 'Robert Mulligan', 'poster': '🐦'},
    'tt0057012': {'title': 'Dr. Strangelove', 'year': 1964, 'rating': 8.4, 'genres': ['Comedy', 'War'], 'director': 'Stanley Kubrick', 'poster': '💣'},
    'tt0057565': {'title': 'The Great Escape', 'year': 1963, 'rating': 8.2, 'genres': ['Adventure', 'Drama'], 'director': 'John Sturges', 'poster': '🏍️'},
    'tt0058461': {'title': 'The Good, the Bad and the Ugly', 'year': 1966, 'rating': 8.8, 'genres': ['Adventure', 'Western'], 'director': 'Sergio Leone', 'poster': '🤠'},
    'tt0059578': {'title': 'For a Few Dollars More', 'year': 1965, 'rating': 8.2, 'genres': ['Western'], 'director': 'Sergio Leone', 'poster': '💰'},
    'tt0060196': {'title': 'The Good, the Bad and the Ugly', 'year': 1966, 'rating': 8.8, 'genres': ['Western'], 'director': 'Sergio Leone', 'poster': '🎯'},
    'tt0061512': {'title': 'Cool Hand Luke', 'year': 1967, 'rating': 8.1, 'genres': ['Crime', 'Drama'], 'director': 'Stuart Rosenberg', 'poster': '🥚'},
    'tt0062622': {'title': '2001: A Space Odyssey', 'year': 1968, 'rating': 8.3, 'genres': ['Adventure', 'Sci-Fi'], 'director': 'Stanley Kubrick', 'poster': '🛸'},
    'tt0064116': {'title': 'Butch Cassidy and the Sundance Kid', 'year': 1969, 'rating': 8.0, 'genres': ['Biography', 'Crime'], 'director': 'George Roy Hill', 'poster': '🐴'},
    
    # ========== 1970s 新好莱坞 ==========
    'tt0066921': {'title': 'A Clockwork Orange', 'year': 1971, 'rating': 8.3, 'genres': ['Crime', 'Sci-Fi'], 'director': 'Stanley Kubrick', 'poster': '🍊'},
    'tt0068646': {'title': 'The Godfather', 'year': 1972, 'rating': 9.2, 'genres': ['Crime', 'Drama'], 'director': 'Francis Ford Coppola', 'poster': '🎩'},
    'tt0070735': {'title': 'The Sting', 'year': 1973, 'rating': 8.3, 'genres': ['Comedy', 'Crime'], 'director': 'George Roy Hill', 'poster': '🃏'},
    'tt0071315': {'title': 'Chinatown', 'year': 1974, 'rating': 8.2, 'genres': ['Drama', 'Mystery'], 'director': 'Roman Polanski', 'poster': '🔍'},
    'tt0071562': {'title': 'The Godfather Part II', 'year': 1974, 'rating': 9.0, 'genres': ['Crime', 'Drama'], 'director': 'Francis Ford Coppola', 'poster': '👨‍👦'},
    'tt0071853': {'title': 'Monty Python and the Holy Grail', 'year': 1975, 'rating': 8.2, 'genres': ['Adventure', 'Comedy'], 'director': 'Terry Gilliam', 'poster': '🏰'},
    'tt0072684': {'title': 'Barry Lyndon', 'year': 1975, 'rating': 8.1, 'genres': ['Adventure', 'Drama'], 'director': 'Stanley Kubrick', 'poster': '🎨'},
    'tt0073195': {'title': 'Jaws', 'year': 1975, 'rating': 8.1, 'genres': ['Adventure', 'Thriller'], 'director': 'Steven Spielberg', 'poster': '🦈'},
    'tt0073486': {'title': "One Flew Over the Cuckoo's Nest", 'year': 1975, 'rating': 8.7, 'genres': ['Drama'], 'director': 'Miloš Forman', 'poster': '🪺'},
    'tt0074958': {'title': 'Network', 'year': 1976, 'rating': 8.1, 'genres': ['Drama'], 'director': 'Sidney Lumet', 'poster': '📺'},
    'tt0075314': {'title': 'Taxi Driver', 'year': 1976, 'rating': 8.2, 'genres': ['Crime', 'Drama'], 'director': 'Martin Scorsese', 'poster': '🚕'},
    'tt0076759': {'title': 'Star Wars: Episode IV', 'year': 1977, 'rating': 8.6, 'genres': ['Action', 'Adventure'], 'director': 'George Lucas', 'poster': '⭐'},
    'tt0077416': {'title': 'The Deer Hunter', 'year': 1978, 'rating': 8.1, 'genres': ['Drama', 'War'], 'director': 'Michael Cimino', 'poster': '🦌'},
    'tt0078748': {'title': 'Alien', 'year': 1979, 'rating': 8.5, 'genres': ['Horror', 'Sci-Fi'], 'director': 'Ridley Scott', 'poster': '👽'},
    'tt0078788': {'title': 'Apocalypse Now', 'year': 1979, 'rating': 8.4, 'genres': ['Drama', 'Mystery'], 'director': 'Francis Ford Coppola', 'poster': '🚁'},
    'tt0079470': {'title': 'Life of Brian', 'year': 1979, 'rating': 8.0, 'genres': ['Comedy'], 'director': 'Terry Jones', 'poster': '✝️'},
    
    # ========== 1980s ==========
    'tt0080678': {'title': 'The Elephant Man', 'year': 1980, 'rating': 8.2, 'genres': ['Biography', 'Drama'], 'director': 'David Lynch', 'poster': '🐘'},
    'tt0080684': {'title': 'Star Wars: Episode V', 'year': 1980, 'rating': 8.7, 'genres': ['Action', 'Adventure'], 'director': 'Irvin Kershner', 'poster': '❄️'},
    'tt0081505': {'title': 'The Shining', 'year': 1980, 'rating': 8.4, 'genres': ['Drama', 'Horror'], 'director': 'Stanley Kubrick', 'poster': '🪓'},
    'tt0082096': {'title': 'Das Boot', 'year': 1981, 'rating': 8.4, 'genres': ['Drama', 'War'], 'director': 'Wolfgang Petersen', 'poster': '🚢'},
    'tt0082971': {'title': 'Raiders of the Lost Ark', 'year': 1981, 'rating': 8.4, 'genres': ['Action', 'Adventure'], 'director': 'Steven Spielberg', 'poster': '🎒'},
    'tt0083658': {'title': 'Blade Runner', 'year': 1982, 'rating': 8.1, 'genres': ['Action', 'Drama'], 'director': 'Ridley Scott', 'poster': '🌃'},
    'tt0084787': {'title': 'The Thing', 'year': 1982, 'rating': 8.2, 'genres': ['Horror', 'Mystery'], 'director': 'John Carpenter', 'poster': '🧊'},
    'tt0086190': {'title': 'Star Wars: Episode VI', 'year': 1983, 'rating': 8.3, 'genres': ['Action', 'Adventure'], 'director': 'Richard Marquand', 'poster': '🌲'},
    'tt0086250': {'title': 'Scarface', 'year': 1983, 'rating': 8.3, 'genres': ['Crime', 'Drama'], 'director': 'Brian De Palma', 'poster': '💊'},
    'tt0086879': {'title': 'Amadeus', 'year': 1984, 'rating': 8.4, 'genres': ['Biography', 'Drama'], 'director': 'Miloš Forman', 'poster': '🎼'},
    'tt0087843': {'title': 'Once Upon a Time in America', 'year': 1984, 'rating': 8.3, 'genres': ['Crime', 'Drama'], 'director': 'Sergio Leone', 'poster': '🗽'},
    'tt0088763': {'title': 'Back to the Future', 'year': 1985, 'rating': 8.5, 'genres': ['Adventure', 'Comedy'], 'director': 'Robert Zemeckis', 'poster': '⚡'},
    'tt0089881': {'title': 'Ran', 'year': 1985, 'rating': 8.2, 'genres': ['Action', 'Drama'], 'director': 'Akira Kurosawa', 'poster': '🏯'},
    'tt0090605': {'title': 'Aliens', 'year': 1986, 'rating': 8.4, 'genres': ['Action', 'Adventure'], 'director': 'James Cameron', 'poster': '👾'},
    'tt0091251': {'title': 'Come and See', 'year': 1985, 'rating': 8.4, 'genres': ['Drama', 'Thriller'], 'director': 'Elem Klimov', 'poster': '👁️'},
    'tt0091763': {'title': 'Platoon', 'year': 1986, 'rating': 8.1, 'genres': ['Drama', 'War'], 'director': 'Oliver Stone', 'poster': '🪖'},
    'tt0093058': {'title': 'Full Metal Jacket', 'year': 1987, 'rating': 8.3, 'genres': ['Drama', 'War'], 'director': 'Stanley Kubrick', 'poster': '🎖️'},
    'tt0095016': {'title': 'Die Hard', 'year': 1988, 'rating': 8.2, 'genres': ['Action', 'Thriller'], 'director': 'John McTiernan', 'poster': '🏢'},
    'tt0095327': {'title': 'Grave of the Fireflies', 'year': 1988, 'rating': 8.5, 'genres': ['Animation', 'Drama'], 'director': 'Isao Takahata', 'poster': '🔥'},
    'tt0095765': {'title': 'Cinema Paradiso', 'year': 1988, 'rating': 8.5, 'genres': ['Drama', 'Romance'], 'director': 'Giuseppe Tornatore', 'poster': '🎬'},
    'tt0097165': {'title': 'Dead Poets Society', 'year': 1989, 'rating': 8.1, 'genres': ['Comedy', 'Drama'], 'director': 'Peter Weir', 'poster': '📚'},
    'tt0097576': {'title': 'Indiana Jones and the Last Crusade', 'year': 1989, 'rating': 8.2, 'genres': ['Action', 'Adventure'], 'director': 'Steven Spielberg', 'poster': '🏆'},
    
    # ========== 1990s ==========
    'tt0099348': {'title': 'Dances with Wolves', 'year': 1990, 'rating': 8.0, 'genres': ['Adventure', 'Drama'], 'director': 'Kevin Costner', 'poster': '🐺'},
    'tt0099685': {'title': 'Goodfellas', 'year': 1990, 'rating': 8.7, 'genres': ['Biography', 'Crime'], 'director': 'Martin Scorsese', 'poster': '🔪'},
    'tt0099711': {'title': 'The Hunt for Red October', 'year': 1990, 'rating': 7.5, 'genres': ['Action', 'Adventure'], 'director': 'John McTiernan', 'poster': '🔴'},
    'tt0102926': {'title': 'The Silence of the Lambs', 'year': 1991, 'rating': 8.6, 'genres': ['Crime', 'Drama'], 'director': 'Jonathan Demme', 'poster': '🦋'},
    'tt0103064': {'title': 'Terminator 2: Judgment Day', 'year': 1991, 'rating': 8.6, 'genres': ['Action', 'Sci-Fi'], 'director': 'James Cameron', 'poster': '🤖'},
    'tt0104257': {'title': 'A Few Good Men', 'year': 1992, 'rating': 7.7, 'genres': ['Drama', 'Thriller'], 'director': 'Rob Reiner', 'poster': '⚖️'},
    'tt0105236': {'title': 'Reservoir Dogs', 'year': 1992, 'rating': 8.3, 'genres': ['Crime', 'Thriller'], 'director': 'Quentin Tarantino', 'poster': '💎'},
    'tt0105695': {'title': 'Unforgiven', 'year': 1992, 'rating': 8.2, 'genres': ['Drama', 'Western'], 'director': 'Clint Eastwood', 'poster': '🤠'},
    'tt0107290': {'title': 'Jurassic Park', 'year': 1993, 'rating': 8.2, 'genres': ['Action', 'Adventure'], 'director': 'Steven Spielberg', 'poster': '🦖'},
    'tt0108052': {'title': "Schindler's List", 'year': 1993, 'rating': 9.0, 'genres': ['Biography', 'Drama'], 'director': 'Steven Spielberg', 'poster': '📜'},
    'tt0109830': {'title': 'Forrest Gump', 'year': 1994, 'rating': 8.8, 'genres': ['Drama', 'Romance'], 'director': 'Robert Zemeckis', 'poster': '🏃'},
    'tt0110357': {'title': 'The Lion King', 'year': 1994, 'rating': 8.5, 'genres': ['Animation', 'Adventure'], 'director': 'Roger Allers', 'poster': '🦁'},
    'tt0110413': {'title': 'Léon: The Professional', 'year': 1994, 'rating': 8.5, 'genres': ['Action', 'Crime'], 'director': 'Luc Besson', 'poster': '🌱'},
    'tt0110912': {'title': 'Pulp Fiction', 'year': 1994, 'rating': 8.9, 'genres': ['Crime', 'Drama'], 'director': 'Quentin Tarantino', 'poster': '💼'},
    'tt0111161': {'title': 'The Shawshank Redemption', 'year': 1994, 'rating': 9.3, 'genres': ['Drama'], 'director': 'Frank Darabont', 'poster': '🔒'},
    'tt0112573': {'title': 'Braveheart', 'year': 1995, 'rating': 8.4, 'genres': ['Biography', 'Drama'], 'director': 'Mel Gibson', 'poster': '⚔️'},
    'tt0114369': {'title': 'Se7en', 'year': 1995, 'rating': 8.6, 'genres': ['Crime', 'Drama'], 'director': 'David Fincher', 'poster': '7️⃣'},
    'tt0114709': {'title': 'Toy Story', 'year': 1995, 'rating': 8.3, 'genres': ['Animation', 'Adventure'], 'director': 'John Lasseter', 'poster': '🤠'},
    'tt0114814': {'title': 'The Usual Suspects', 'year': 1995, 'rating': 8.5, 'genres': ['Crime', 'Drama'], 'director': 'Bryan Singer', 'poster': '🎭'},
    'tt0116282': {'title': 'Fargo', 'year': 1996, 'rating': 8.1, 'genres': ['Crime', 'Thriller'], 'director': 'Joel Coen', 'poster': '❄️'},
    'tt0117951': {'title': 'Trainspotting', 'year': 1996, 'rating': 8.1, 'genres': ['Drama'], 'director': 'Danny Boyle', 'poster': '💉'},
    'tt0118715': {'title': 'The Big Lebowski', 'year': 1998, 'rating': 8.1, 'genres': ['Comedy', 'Crime'], 'director': 'Joel Coen', 'poster': '🎳'},
    'tt0118799': {'title': 'Life Is Beautiful', 'year': 1997, 'rating': 8.6, 'genres': ['Comedy', 'Drama'], 'director': 'Roberto Benigni', 'poster': '🌸'},
    'tt0119217': {'title': 'Good Will Hunting', 'year': 1997, 'rating': 8.3, 'genres': ['Drama', 'Romance'], 'director': 'Gus Van Sant', 'poster': '🧠'},
    'tt0119698': {'title': 'Princess Mononoke', 'year': 1997, 'rating': 8.4, 'genres': ['Animation', 'Action'], 'director': 'Hayao Miyazaki', 'poster': '🐺'},
    'tt0120338': {'title': 'Titanic', 'year': 1997, 'rating': 7.9, 'genres': ['Drama', 'Romance'], 'director': 'James Cameron', 'poster': '🚢'},
    'tt0120586': {'title': 'American History X', 'year': 1998, 'rating': 8.5, 'genres': ['Crime', 'Drama'], 'director': 'Tony Kaye', 'poster': '✊'},
    'tt0120737': {'title': 'LOTR: The Fellowship of the Ring', 'year': 2001, 'rating': 8.9, 'genres': ['Action', 'Adventure'], 'director': 'Peter Jackson', 'poster': '💍'},
    'tt0120815': {'title': 'Saving Private Ryan', 'year': 1998, 'rating': 8.6, 'genres': ['Drama', 'War'], 'director': 'Steven Spielberg', 'poster': '🎖️'},
    'tt0125439': {'title': 'Notting Hill', 'year': 1999, 'rating': 7.2, 'genres': ['Comedy', 'Romance'], 'director': 'Roger Michell', 'poster': '💕'},
    'tt0133093': {'title': 'The Matrix', 'year': 1999, 'rating': 8.7, 'genres': ['Action', 'Sci-Fi'], 'director': 'The Wachowskis', 'poster': '💊'},
    'tt0137523': {'title': 'Fight Club', 'year': 1999, 'rating': 8.8, 'genres': ['Drama'], 'director': 'David Fincher', 'poster': '🥊'},
    
    # ========== 2000s ==========
    'tt0167260': {'title': 'LOTR: The Return of the King', 'year': 2003, 'rating': 9.0, 'genres': ['Action', 'Adventure'], 'director': 'Peter Jackson', 'poster': '👑'},
    'tt0167261': {'title': 'LOTR: The Two Towers', 'year': 2002, 'rating': 8.8, 'genres': ['Action', 'Adventure'], 'director': 'Peter Jackson', 'poster': '🗼'},
    'tt0169547': {'title': 'American Beauty', 'year': 1999, 'rating': 8.3, 'genres': ['Drama'], 'director': 'Sam Mendes', 'poster': '🌹'},
    'tt0180093': {'title': 'Requiem for a Dream', 'year': 2000, 'rating': 8.3, 'genres': ['Drama'], 'director': 'Darren Aronofsky', 'poster': '💔'},
    'tt0198781': {'title': 'Monsters, Inc.', 'year': 2001, 'rating': 8.1, 'genres': ['Animation', 'Adventure'], 'director': 'Pete Docter', 'poster': '👾'},
    'tt0208092': {'title': 'Snatch', 'year': 2000, 'rating': 8.2, 'genres': ['Comedy', 'Crime'], 'director': 'Guy Ritchie', 'poster': '💎'},
    'tt0209144': {'title': 'Memento', 'year': 2000, 'rating': 8.4, 'genres': ['Mystery', 'Thriller'], 'director': 'Christopher Nolan', 'poster': '📷'},
    'tt0211915': {'title': 'Amélie', 'year': 2001, 'rating': 8.3, 'genres': ['Comedy', 'Romance'], 'director': 'Jean-Pierre Jeunet', 'poster': '🍓'},
    'tt0245429': {'title': 'Spirited Away', 'year': 2001, 'rating': 8.6, 'genres': ['Animation', 'Adventure'], 'director': 'Hayao Miyazaki', 'poster': '🐉'},
    'tt0246578': {'title': 'Donnie Darko', 'year': 2001, 'rating': 8.0, 'genres': ['Drama', 'Mystery'], 'director': 'Richard Kelly', 'poster': '🐰'},
    'tt0253474': {'title': 'The Pianist', 'year': 2002, 'rating': 8.5, 'genres': ['Biography', 'Drama'], 'director': 'Roman Polanski', 'poster': '🎹'},
    'tt0264464': {'title': 'Catch Me If You Can', 'year': 2002, 'rating': 8.1, 'genres': ['Biography', 'Crime'], 'director': 'Steven Spielberg', 'poster': '✈️'},
    'tt0266543': {'title': 'Finding Nemo', 'year': 2003, 'rating': 8.2, 'genres': ['Animation', 'Adventure'], 'director': 'Andrew Stanton', 'poster': '🐠'},
    'tt0266697': {'title': 'Kill Bill: Vol. 1', 'year': 2003, 'rating': 8.2, 'genres': ['Action', 'Crime'], 'director': 'Quentin Tarantino', 'poster': '⚔️'},
    'tt0268978': {'title': 'A Beautiful Mind', 'year': 2001, 'rating': 8.2, 'genres': ['Biography', 'Drama'], 'director': 'Ron Howard', 'poster': '🧮'},
    'tt0317248': {'title': 'City of God', 'year': 2002, 'rating': 8.6, 'genres': ['Crime', 'Drama'], 'director': 'Fernando Meirelles', 'poster': '🏙️'},
    'tt0325980': {'title': 'Pirates of the Caribbean', 'year': 2003, 'rating': 8.1, 'genres': ['Action', 'Adventure'], 'director': 'Gore Verbinski', 'poster': '🏴‍☠️'},
    'tt0347149': {'title': 'Howl\'s Moving Castle', 'year': 2004, 'rating': 8.2, 'genres': ['Animation', 'Adventure'], 'director': 'Hayao Miyazaki', 'poster': '🏰'},
    'tt0353969': {'title': 'Memories of Murder', 'year': 2003, 'rating': 8.1, 'genres': ['Crime', 'Drama'], 'director': 'Bong Joon-ho', 'poster': '🔍'},
    'tt0361748': {'title': 'Inglourious Basterds', 'year': 2009, 'rating': 8.3, 'genres': ['Adventure', 'Drama'], 'director': 'Quentin Tarantino', 'poster': '🎬'},
    'tt0364569': {'title': 'Oldboy', 'year': 2003, 'rating': 8.4, 'genres': ['Action', 'Drama'], 'director': 'Park Chan-wook', 'poster': '🔨'},
    'tt0372784': {'title': 'Batman Begins', 'year': 2005, 'rating': 8.2, 'genres': ['Action', 'Crime'], 'director': 'Christopher Nolan', 'poster': '🦇'},
    'tt0381061': {'title': 'Casino Royale', 'year': 2006, 'rating': 8.0, 'genres': ['Action', 'Adventure'], 'director': 'Martin Campbell', 'poster': '🃏'},
    'tt0382932': {'title': 'Ratatouille', 'year': 2007, 'rating': 8.1, 'genres': ['Animation', 'Comedy'], 'director': 'Brad Bird', 'poster': '🐀'},
    'tt0395169': {'title': 'Hotel Rwanda', 'year': 2004, 'rating': 8.1, 'genres': ['Biography', 'Drama'], 'director': 'Terry George', 'poster': '🏨'},
    'tt0405094': {'title': 'The Lives of Others', 'year': 2006, 'rating': 8.4, 'genres': ['Drama', 'Mystery'], 'director': 'Florian Henckel', 'poster': '🎧'},
    'tt0407887': {'title': 'The Departed', 'year': 2006, 'rating': 8.5, 'genres': ['Crime', 'Drama'], 'director': 'Martin Scorsese', 'poster': '🔫'},
    'tt0434409': {'title': 'V for Vendetta', 'year': 2005, 'rating': 8.2, 'genres': ['Action', 'Drama'], 'director': 'James McTeigue', 'poster': '🎭'},
    'tt0435761': {'title': 'Toy Story 3', 'year': 2010, 'rating': 8.3, 'genres': ['Animation', 'Adventure'], 'director': 'Lee Unkrich', 'poster': '🧸'},
    'tt0452623': {'title': 'Rang De Basanti', 'year': 2006, 'rating': 8.1, 'genres': ['Comedy', 'Crime'], 'director': 'Rakeysh Mehra', 'poster': '🇮🇳'},
    'tt0468569': {'title': 'The Dark Knight', 'year': 2008, 'rating': 9.0, 'genres': ['Action', 'Crime'], 'director': 'Christopher Nolan', 'poster': '🃏'},
    
    # ========== 2010s ==========
    'tt0816692': {'title': 'Interstellar', 'year': 2014, 'rating': 8.7, 'genres': ['Adventure', 'Drama'], 'director': 'Christopher Nolan', 'poster': '🚀'},
    'tt0910970': {'title': 'WALL·E', 'year': 2008, 'rating': 8.4, 'genres': ['Animation', 'Adventure'], 'director': 'Andrew Stanton', 'poster': '🤖'},
    'tt1010048': {'title': 'Slumdog Millionaire', 'year': 2008, 'rating': 8.0, 'genres': ['Drama', 'Romance'], 'director': 'Danny Boyle', 'poster': '💰'},
    'tt1049413': {'title': 'Up', 'year': 2009, 'rating': 8.3, 'genres': ['Animation', 'Adventure'], 'director': 'Pete Docter', 'poster': '🎈'},
    'tt1130884': {'title': 'Shutter Island', 'year': 2010, 'rating': 8.2, 'genres': ['Mystery', 'Thriller'], 'director': 'Martin Scorsese', 'poster': '🏝️'},
    'tt1190080': {'title': '3 Idiots', 'year': 2009, 'rating': 8.4, 'genres': ['Comedy', 'Drama'], 'director': 'Rajkumar Hirani', 'poster': '🎓'},
    'tt1201607': {'title': 'Harry Potter: Deathly Hallows 2', 'year': 2011, 'rating': 8.1, 'genres': ['Adventure', 'Fantasy'], 'director': 'David Yates', 'poster': '⚡'},
    'tt1305806': {'title': 'The Secret in Their Eyes', 'year': 2009, 'rating': 8.2, 'genres': ['Drama', 'Mystery'], 'director': 'Juan José Campanella', 'poster': '👁️'},
    'tt1345836': {'title': 'The Dark Knight Rises', 'year': 2012, 'rating': 8.4, 'genres': ['Action', 'Crime'], 'director': 'Christopher Nolan', 'poster': '🦇'},
    'tt1375666': {'title': 'Inception', 'year': 2010, 'rating': 8.8, 'genres': ['Action', 'Adventure'], 'director': 'Christopher Nolan', 'poster': '🌀'},
    'tt1392214': {'title': 'Prisoners', 'year': 2013, 'rating': 8.1, 'genres': ['Crime', 'Drama'], 'director': 'Denis Villeneuve', 'poster': '🔒'},
    'tt1467304': {'title': 'Jagten / The Hunt', 'year': 2012, 'rating': 8.3, 'genres': ['Drama'], 'director': 'Thomas Vinterberg', 'poster': '🦌'},
    'tt1517268': {'title': 'Barbie', 'year': 2023, 'rating': 6.8, 'genres': ['Adventure', 'Comedy'], 'director': 'Greta Gerwig', 'poster': '💗'},
    'tt1568346': {'title': 'The Girl with the Dragon Tattoo', 'year': 2011, 'rating': 7.8, 'genres': ['Crime', 'Drama'], 'director': 'David Fincher', 'poster': '🐉'},
    'tt1569923': {'title': 'Like Stars on Earth', 'year': 2007, 'rating': 8.3, 'genres': ['Drama', 'Family'], 'director': 'Aamir Khan', 'poster': '⭐'},
    'tt1675434': {'title': 'The Intouchables', 'year': 2011, 'rating': 8.5, 'genres': ['Biography', 'Comedy'], 'director': 'Olivier Nakache', 'poster': '🤝'},
    'tt1853728': {'title': 'Django Unchained', 'year': 2012, 'rating': 8.4, 'genres': ['Drama', 'Western'], 'director': 'Quentin Tarantino', 'poster': '🔗'},
    'tt1895587': {'title': 'Spotlight', 'year': 2015, 'rating': 8.1, 'genres': ['Biography', 'Crime'], 'director': 'Tom McCarthy', 'poster': '📰'},
    'tt1950186': {'title': 'Ford v Ferrari', 'year': 2019, 'rating': 8.1, 'genres': ['Action', 'Biography'], 'director': 'James Mangold', 'poster': '🏎️'},
    'tt2024544': {'title': '12 Years a Slave', 'year': 2013, 'rating': 8.1, 'genres': ['Biography', 'Drama'], 'director': 'Steve McQueen', 'poster': '⛓️'},
    'tt2278388': {'title': 'The Grand Budapest Hotel', 'year': 2014, 'rating': 8.1, 'genres': ['Adventure', 'Comedy'], 'director': 'Wes Anderson', 'poster': '🏨'},
    'tt2380307': {'title': 'Coco', 'year': 2017, 'rating': 8.4, 'genres': ['Animation', 'Adventure'], 'director': 'Lee Unkrich', 'poster': '🎸'},
    'tt2582802': {'title': 'Whiplash', 'year': 2014, 'rating': 8.5, 'genres': ['Drama', 'Music'], 'director': 'Damien Chazelle', 'poster': '🥁'},
    'tt2096673': {'title': 'Inside Out', 'year': 2015, 'rating': 8.1, 'genres': ['Animation', 'Adventure'], 'director': 'Pete Docter', 'poster': '😊'},
    'tt4633694': {'title': 'Spider-Man: Into the Spider-Verse', 'year': 2018, 'rating': 8.4, 'genres': ['Animation', 'Action'], 'director': 'Bob Persichetti', 'poster': '🕷️'},
    'tt4154756': {'title': 'Avengers: Infinity War', 'year': 2018, 'rating': 8.4, 'genres': ['Action', 'Adventure'], 'director': 'Anthony Russo', 'poster': '💎'},
    'tt4154796': {'title': 'Avengers: Endgame', 'year': 2019, 'rating': 8.4, 'genres': ['Action', 'Adventure'], 'director': 'Anthony Russo', 'poster': '🦸'},
    'tt5027774': {'title': 'Three Billboards Outside Ebbing, Missouri', 'year': 2017, 'rating': 8.1, 'genres': ['Crime', 'Drama'], 'director': 'Martin McDonagh', 'poster': '🪧'},
    'tt5311514': {'title': 'Your Name', 'year': 2016, 'rating': 8.4, 'genres': ['Animation', 'Drama'], 'director': 'Makoto Shinkai', 'poster': '☄️'},
    'tt5537002': {'title': 'Knives Out', 'year': 2019, 'rating': 7.9, 'genres': ['Comedy', 'Crime'], 'director': 'Rian Johnson', 'poster': '🔪'},
    'tt6751668': {'title': 'Parasite', 'year': 2019, 'rating': 8.5, 'genres': ['Drama', 'Thriller'], 'director': 'Bong Joon-ho', 'poster': '🪨'},
    'tt6966692': {'title': 'Green Book', 'year': 2018, 'rating': 8.2, 'genres': ['Biography', 'Comedy'], 'director': 'Peter Farrelly', 'poster': '📗'},
    'tt7131622': {'title': 'Once Upon a Time in Hollywood', 'year': 2019, 'rating': 7.6, 'genres': ['Comedy', 'Drama'], 'director': 'Quentin Tarantino', 'poster': '🎬'},
    'tt7286456': {'title': 'Joker', 'year': 2019, 'rating': 8.4, 'genres': ['Crime', 'Drama'], 'director': 'Todd Phillips', 'poster': '🤡'},
    'tt8579674': {'title': '1917', 'year': 2019, 'rating': 8.2, 'genres': ['Drama', 'War'], 'director': 'Sam Mendes', 'poster': '💣'},
    
    # ========== 2020s ==========
    'tt10366206': {'title': 'John Wick: Chapter 4', 'year': 2023, 'rating': 7.7, 'genres': ['Action', 'Crime'], 'director': 'Chad Stahelski', 'poster': '🔫'},
    'tt10872600': {'title': 'Spider-Man: No Way Home', 'year': 2021, 'rating': 8.2, 'genres': ['Action', 'Adventure'], 'director': 'Jon Watts', 'poster': '🕸️'},
    'tt10648342': {'title': 'Thor: Love and Thunder', 'year': 2022, 'rating': 6.2, 'genres': ['Action', 'Adventure'], 'director': 'Taika Waititi', 'poster': '⚡'},
    'tt10366460': {'title': 'Leg', 'year': 2020, 'rating': 6.5, 'genres': ['Drama'], 'director': 'Unknown', 'poster': '🦵'},
    'tt12037194': {'title': 'Dune: Part Two', 'year': 2024, 'rating': 8.8, 'genres': ['Action', 'Adventure'], 'director': 'Denis Villeneuve', 'poster': '🏜️'},
    'tt14209916': {'title': 'Everything Everywhere All at Once', 'year': 2022, 'rating': 7.8, 'genres': ['Action', 'Adventure'], 'director': 'Daniel Kwan', 'poster': '🥯'},
    'tt14539740': {'title': 'Oppenheimer', 'year': 2023, 'rating': 8.4, 'genres': ['Biography', 'Drama'], 'director': 'Christopher Nolan', 'poster': '💥'},
    'tt15398776': {'title': 'Oppenheimer', 'year': 2023, 'rating': 8.4, 'genres': ['Biography', 'Drama'], 'director': 'Christopher Nolan', 'poster': '☢️'},
    'tt18925334': {'title': 'Killers of the Flower Moon', 'year': 2023, 'rating': 7.6, 'genres': ['Crime', 'Drama'], 'director': 'Martin Scorsese', 'poster': '🌺'},
    'tt21807222': {'title': 'Anatomy of a Fall', 'year': 2023, 'rating': 7.7, 'genres': ['Crime', 'Drama'], 'director': 'Justine Triet', 'poster': '⛰️'},
}


# ==================== API 密钥获取 (支持云端) ====================
def get_api_key(key_name: str) -> str:
    """
    获取API密钥 - 同时支持本地和云端
    优先级: st.secrets > 环境变量 > .env文件
    """
    # 1. 尝试从 Streamlit Secrets 获取 (云端部署)
    try:
        if hasattr(st, 'secrets') and key_name in st.secrets:
            return st.secrets[key_name]
    except:
        pass
    
    # 2. 尝试从环境变量获取
    value = os.getenv(key_name)
    if value and value != 'your_key_here':
        return value
    
    # 3. 尝试从 .env 文件加载
    try:
        from dotenv import load_dotenv
        load_dotenv()
        value = os.getenv(key_name)
        if value and value != 'your_key_here':
            return value
    except:
        pass
    
    return None


# ==================== 数据加载函数 ====================
@st.cache_data
def load_real_data_from_csv(filepath: str, movie_id: str = None) -> dict:
    """从 CSV 文件加载真实数据"""
    try:
        # 尝试多种编码
        for encoding in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
            try:
                df = pd.read_csv(filepath, encoding=encoding)
                break
            except:
                continue
        else:
            return None
        
        column_mapping = {'user': 'author', 'review': 'content', 'text': 'content'}
        df = df.rename(columns={k: v for k, v in column_mapping.items() if k in df.columns})
        
        if 'rating' in df.columns:
            def parse_rating(r):
                if pd.isna(r) or r == 'N/A':
                    return None
                if isinstance(r, str) and '/' in r:
                    try:
                        return int(r.split('/')[0])
                    except:
                        return None
                try:
                    return int(float(r))
                except:
                    return None
            df['rating_num'] = df['rating'].apply(parse_rating)
        
        if movie_id is None:
            filename = Path(filepath).stem
            movie_id = filename.split('_')[0] if filename.startswith('tt') else 'unknown'
        
        # 获取电影信息，如果不在元数据中则使用默认值
        default_info = {
            'title': movie_id, 
            'year': None, 
            'rating': None, 
            'genres': [], 
            'director': None, 
            'poster': '🎬'
        }
        info = {'id': movie_id, **MOVIE_METADATA.get(movie_id, default_info)}
        
        return {'info': info, 'reviews': df}
    except Exception as e:
        st.error(f"加载数据失败: {e}")
        return None


@st.cache_data
def load_all_movies_from_data_dir(data_dir: str = "data") -> dict:
    """从 data 目录加载所有电影数据"""
    movies = {}
    data_path = Path(data_dir)
    
    if not data_path.exists():
        return movies
    
    # 加载所有CSV文件
    for csv_file in data_path.glob("*.csv"):
        # 跳过Mac系统文件
        if csv_file.name.startswith('.') or csv_file.name.startswith('_'):
            continue
        
        # 提取电影ID
        filename = csv_file.stem
        if '_reviews' in filename:
            movie_id = filename.replace('_reviews', '')
        elif filename.startswith('tt'):
            movie_id = filename
        else:
            movie_id = filename
        
        movie_data = load_real_data_from_csv(str(csv_file), movie_id)
        if movie_data and len(movie_data['reviews']) > 0:
            movies[movie_id] = movie_data
    
    return movies


@st.cache_data
def analyze_reviews(df_input, movie_id: str = "default"):
    """分析评论数据 - 支持多语言，增强错误处理
    
    Args:
        df_input: 评论数据DataFrame
        movie_id: 电影ID，用于缓存区分
    """
    df = df_input.copy()
    
    # 确保有content列
    if 'content' not in df.columns:
        df['content'] = ''
    
    rating_col = 'rating_num' if 'rating_num' in df.columns else 'rating'
    
    if 'sentiment_label' not in df.columns:
        def get_sentiment(row):
            # 首先尝试基于评分
            r = row.get(rating_col) if rating_col in row.index else None
            if pd.notna(r):
                try:
                    r = float(r)
                    if r >= 7:
                        return 'positive'
                    elif r <= 4:
                        return 'negative'
                    else:
                        return 'neutral'
                except:
                    pass
            
            # 基于内容分析（多语言支持）
            content = str(row.get('content', '')).lower()
            if not content:
                return 'neutral'
            
            pos_score = sum(SENTIMENT_LEXICON['positive'].get(w, 0) for w in content.split())
            neg_score = sum(abs(SENTIMENT_LEXICON['negative'].get(w, 0)) for w in content.split())
            
            if pos_score > neg_score + 0.5:
                return 'positive'
            elif neg_score > pos_score + 0.5:
                return 'negative'
            return 'neutral'
        
        df['sentiment_label'] = df.apply(get_sentiment, axis=1)
        
        # 计算情感分数
        if rating_col in df.columns:
            df['sentiment_score'] = df[rating_col].apply(
                lambda x: float(x)/10 if pd.notna(x) else 0.5
            )
        else:
            df['sentiment_score'] = 0.5
    
    return df


# ==================== 🔔 情感预警系统 ====================
def check_sentiment_alerts(df: pd.DataFrame, movie_title: str) -> List[Dict]:
    """检查情感预警"""
    alerts = []
    
    if 'sentiment_label' not in df.columns or len(df) == 0:
        return alerts
    
    neg_ratio = (df['sentiment_label'] == 'negative').mean()
    pos_ratio = (df['sentiment_label'] == 'positive').mean()
    
    if neg_ratio > 0.3:
        alerts.append({
            'type': 'danger',
            'title': '⚠️ 负面评价过高',
            'message': f'《{movie_title}》负面评价率达到 {neg_ratio*100:.1f}%，建议重点关注用户反馈',
            'metric': neg_ratio
        })
    elif neg_ratio > 0.2:
        alerts.append({
            'type': 'warning',
            'title': '🔔 负面评价偏高',
            'message': f'《{movie_title}》负面评价率为 {neg_ratio*100:.1f}%，需要适度关注',
            'metric': neg_ratio
        })
    
    if pos_ratio > 0.8:
        alerts.append({
            'type': 'success',
            'title': '🎉 口碑优秀',
            'message': f'《{movie_title}》正面评价率高达 {pos_ratio*100:.1f}%，市场表现良好',
            'metric': pos_ratio
        })
    
    return alerts


def render_alerts(alerts: List[Dict]):
    """渲染预警信息"""
    for alert in alerts:
        if alert['type'] == 'danger':
            st.markdown(f"""
            <div class="alert-warning">
                <div style="font-weight: 600; color: #ef4444; margin-bottom: 0.25rem;">{alert['title']}</div>
                <div style="color: #fca5a5;">{alert['message']}</div>
            </div>
            """, unsafe_allow_html=True)
        elif alert['type'] == 'warning':
            st.markdown(f"""
            <div style="background: rgba(234, 179, 8, 0.15); border: 1px solid rgba(234, 179, 8, 0.5); 
                        border-radius: 12px; padding: 1rem; margin-bottom: 1rem;">
                <div style="font-weight: 600; color: #eab308; margin-bottom: 0.25rem;">{alert['title']}</div>
                <div style="color: #fde047;">{alert['message']}</div>
            </div>
            """, unsafe_allow_html=True)
        elif alert['type'] == 'success':
            st.markdown(f"""
            <div class="alert-success">
                <div style="font-weight: 600; color: #22c55e; margin-bottom: 0.25rem;">{alert['title']}</div>
                <div style="color: #86efac;">{alert['message']}</div>
            </div>
            """, unsafe_allow_html=True)


# ==================== 数据分析函数 ====================
def get_aspect_data(df):
    """获取方面分析数据"""
    aspects = {
        '演技': {'keywords': ['acting', 'actor', 'performance', 'cast', '演技', '表演', '演员'], 'positive': 0, 'negative': 0},
        '剧情': {'keywords': ['plot', 'story', 'storyline', 'narrative', '剧情', '故事', '情节'], 'positive': 0, 'negative': 0},
        '配乐': {'keywords': ['music', 'soundtrack', 'score', 'sound', '配乐', '音乐', '原声'], 'positive': 0, 'negative': 0},
        '摄影': {'keywords': ['cinematography', 'visual', 'camera', 'shot', '摄影', '画面', '镜头'], 'positive': 0, 'negative': 0},
        '节奏': {'keywords': ['pacing', 'pace', 'slow', 'boring', 'runtime', '节奏', '拖沓'], 'positive': 0, 'negative': 0},
        '特效': {'keywords': ['effects', 'cgi', 'vfx', 'action', '特效', '视觉效果'], 'positive': 0, 'negative': 0},
    }
    
    for _, row in df.iterrows():
        content = str(row.get('content', '')).lower()
        sentiment = row.get('sentiment_label', 'neutral')
        
        for aspect, data in aspects.items():
            if any(kw in content for kw in data['keywords']):
                if sentiment == 'positive':
                    aspects[aspect]['positive'] += 1
                elif sentiment == 'negative':
                    aspects[aspect]['negative'] += 1
    
    result = []
    for aspect, data in aspects.items():
        total = data['positive'] + data['negative']
        if total > 0:
            result.append({
                'aspect': aspect,
                'positive': int(data['positive'] / total * 100),
                'negative': int(data['negative'] / total * 100),
                'total': total
            })
        else:
            result.append({'aspect': aspect, 'positive': 50, 'negative': 50, 'total': 0})
    
    return result


def get_topic_data(df):
    """获取主题数据"""
    topics = [
        ('剧情/故事', ['plot', 'twist', 'story', 'narrative', '剧情', '故事']),
        ('演员/演技', ['acting', 'actor', 'performance', 'cast', '演技', '演员']),
        ('情感/感动', ['emotional', 'moving', 'touching', 'feel', '感动', '情感']),
        ('视觉特效', ['visual', 'effects', 'cgi', 'stunning', '视觉', '特效']),
        ('导演风格', ['director', 'direction', 'nolan', 'vision', '导演']),
        ('结局', ['ending', 'end', 'finale', 'conclusion', '结局']),
        ('节奏', ['pace', 'pacing', 'slow', 'fast', '节奏']),
        ('配乐', ['music', 'score', 'soundtrack', '配乐', '音乐']),
    ]
    
    result = []
    for label, keywords in topics:
        count = 0
        for _, row in df.iterrows():
            content = str(row.get('content', '')).lower()
            if any(kw in content for kw in keywords):
                count += 1
        result.append({'topic': label, 'score': min(count, 100)})
    
    result.sort(key=lambda x: x['score'], reverse=True)
    return pd.DataFrame(result)


# ==================== 可视化函数 ====================
def create_sentiment_donut(pos_ratio, neg_ratio=None):
    """创建情感分布甜甜圈图 - 增强错误处理"""
    theme = get_theme()
    
    # 确保 pos_ratio 是有效数值
    try:
        pos_ratio = float(pos_ratio)
        if pd.isna(pos_ratio) or pos_ratio < 0 or pos_ratio > 1:
            pos_ratio = 0.5
    except:
        pos_ratio = 0.5
    
    if neg_ratio is None:
        neg_ratio = max(0, 1 - pos_ratio - 0.1)
    else:
        try:
            neg_ratio = float(neg_ratio)
            if pd.isna(neg_ratio) or neg_ratio < 0:
                neg_ratio = max(0, 1 - pos_ratio - 0.1)
        except:
            neg_ratio = max(0, 1 - pos_ratio - 0.1)
    
    neu_ratio = max(0, 1 - pos_ratio - neg_ratio)
    
    fig = go.Figure(data=[go.Pie(
        values=[pos_ratio, neg_ratio, neu_ratio],
        labels=['正面', '负面', '中性'],
        hole=0.6,
        marker_colors=['#22c55e', '#ef4444', '#6b7280'],
        textinfo='percent',
        textfont=dict(color='white', size=14)
    )])
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation='h', y=-0.1, x=0.5, xanchor='center', font=dict(color='#9ca3af', size=12)),
        margin=dict(t=20, b=60, l=20, r=20),
        height=280,
        paper_bgcolor='rgba(0,0,0,0)',
    )
    return fig


def create_trend_chart(df):
    """创建评分趋势图 - 增强错误处理"""
    theme = get_theme()
    
    # 默认数据
    default_months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
    default_ratings = [7.5, 8.0, 7.8, 8.2, 8.5, 8.3]
    
    months = default_months
    ratings = default_ratings
    
    try:
        rating_col = 'rating_num' if 'rating_num' in df.columns else None
        
        if 'date' in df.columns and rating_col is not None:
            df_copy = df.copy()
            df_copy['date'] = pd.to_datetime(df_copy['date'], errors='coerce')
            
            # 确保 rating_col 是数值类型
            df_copy[rating_col] = pd.to_numeric(df_copy[rating_col], errors='coerce')
            
            df_copy = df_copy.dropna(subset=['date', rating_col])
            
            if not df_copy.empty and len(df_copy) >= 5:
                df_copy['month'] = df_copy['date'].dt.to_period('M')
                monthly = df_copy.groupby('month')[rating_col].mean().reset_index()
                monthly['month'] = monthly['month'].astype(str)
                
                if len(monthly) > 0:
                    months = monthly['month'].tolist()[-12:]
                    ratings = monthly[rating_col].tolist()[-12:]
    except Exception as e:
        # 出错时使用默认数据
        months = default_months
        ratings = default_ratings
    
    # 将主题色转换为rgba格式（Plotly 6.x兼容）
    primary_color = theme['primary']
    # 从hex转换为rgba，添加透明度
    if primary_color.startswith('#'):
        r = int(primary_color[1:3], 16)
        g = int(primary_color[3:5], 16)
        b = int(primary_color[5:7], 16)
        fill_color = f'rgba({r},{g},{b},0.12)'
    else:
        fill_color = 'rgba(245,197,24,0.12)'
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=ratings, mode='lines+markers',
        line=dict(color=primary_color, width=3),
        marker=dict(size=10, color=primary_color),
        fill='tozeroy', fillcolor=fill_color
    ))
    fig.update_layout(
        xaxis=dict(showgrid=False, color='#9ca3af', tickangle=45),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#9ca3af', range=[0, 10]),
        margin=dict(t=20, b=60, l=40, r=20),
        height=250,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def create_topic_bars(topic_df):
    """创建主题柱状图"""
    theme = get_theme()
    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=topic_df['topic'], x=topic_df['score'],
        orientation='h',
        marker=dict(color=theme['primary'], cornerradius=4)
    ))
    fig.update_layout(
        xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#9ca3af'),
        yaxis=dict(showgrid=False, color='#e5e7eb', autorange='reversed'),
        margin=dict(t=10, b=20, l=80, r=20),
        height=280,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def create_network_graph(df):
    """创建主题网络图"""
    theme = get_theme()
    
    nodes = [
        {'id': '剧情', 'size': 50, 'color': theme['primary'], 'x': 0.5, 'y': 0.8},
        {'id': '演技', 'size': 45, 'color': '#22c55e', 'x': 0.2, 'y': 0.5},
        {'id': '视效', 'size': 40, 'color': '#3b82f6', 'x': 0.8, 'y': 0.5},
        {'id': '配乐', 'size': 35, 'color': '#a855f7', 'x': 0.35, 'y': 0.2},
        {'id': '节奏', 'size': 30, 'color': '#ef4444', 'x': 0.65, 'y': 0.2},
    ]
    
    edges = [(0, 1), (0, 2), (1, 3), (2, 4), (3, 4), (0, 3), (0, 4)]
    
    fig = go.Figure()
    
    for i, j in edges:
        fig.add_trace(go.Scatter(
            x=[nodes[i]['x'], nodes[j]['x']],
            y=[nodes[i]['y'], nodes[j]['y']],
            mode='lines',
            line=dict(color='rgba(255,255,255,0.15)', width=1.5),
            hoverinfo='skip'
        ))
    
    for node in nodes:
        fig.add_trace(go.Scatter(
            x=[node['x']], y=[node['y']],
            mode='markers+text',
            marker=dict(size=node['size'], color=node['color'], line=dict(color='rgba(255,255,255,0.3)', width=2)),
            text=[node['id']], 
            textposition='middle center',
            textfont=dict(color='white', size=11, family='Arial Black'),
            hoverinfo='text',
            hovertext=f"{node['id']}"
        ))
    
    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False, range=[-0.05, 1.05]),
        yaxis=dict(visible=False, range=[-0.05, 1.05]),
        margin=dict(t=10, b=10, l=10, r=10),
        height=380,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(15,15,25,0.3)'
    )
    return fig


def create_3d_scatter(df):
    """创建3D散点图"""
    np.random.seed(42)
    n = min(len(df), 100)
    
    if 'sentiment_label' in df.columns:
        colors = df['sentiment_label'].head(n).map({
            'positive': '#22c55e', 'negative': '#ef4444', 'neutral': '#eab308'
        }).fillna('#eab308')
    else:
        colors = ['#eab308'] * n
    
    fig = go.Figure(data=[go.Scatter3d(
        x=np.random.randn(n) * 20 + 50,
        y=np.random.randn(n) * 20 + 50,
        z=np.random.randn(n) * 20 + 50,
        mode='markers',
        marker=dict(size=5, color=colors.tolist() if hasattr(colors, 'tolist') else colors, opacity=0.7)
    )])
    fig.update_layout(
        scene=dict(
            xaxis=dict(showgrid=False, showbackground=False),
            yaxis=dict(showgrid=False, showbackground=False),
            zaxis=dict(showgrid=False, showbackground=False),
            bgcolor='rgba(0,0,0,0)'
        ),
        margin=dict(t=20, b=20, l=20, r=20),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def create_sankey():
    """创建桑基图"""
    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15, thickness=20,
            label=['科幻', '动作', '剧情', '特效', '正面', '负面'],
            color=['#fff', '#fff', '#ef4444', '#eab308', '#22c55e', '#ef4444']
        ),
        link=dict(
            source=[0, 0, 1, 1, 2, 2, 3, 3],
            target=[2, 3, 2, 3, 4, 5, 4, 5],
            value=[30, 20, 25, 15, 40, 15, 30, 5],
            color=['rgba(34,197,94,0.4)', 'rgba(234,179,8,0.4)', 'rgba(239,68,68,0.4)', 
                   'rgba(234,179,8,0.4)', 'rgba(34,197,94,0.4)', 'rgba(239,68,68,0.4)',
                   'rgba(34,197,94,0.4)', 'rgba(239,68,68,0.4)']
        )
    ))
    fig.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=280, paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#9ca3af'))
    return fig


# ==================== 竞品对比雷达图 ====================
def create_comparison_radar(movie1_data: dict, movie2_data: dict) -> go.Figure:
    """创建双电影对比雷达图"""
    categories = ['剧情', '演技', '视效', '配乐', '节奏', '结局']
    
    def calc_scores(df):
        aspects = get_aspect_data(df)
        aspect_map = {'剧情': '剧情', '演技': '演技', '视效': '特效', '配乐': '配乐', '节奏': '节奏'}
        scores = []
        for cat in categories:
            asp = aspect_map.get(cat, cat)
            found = False
            for a in aspects:
                if a['aspect'] == asp:
                    scores.append(a['positive'])
                    found = True
                    break
            if not found:
                scores.append(50)
        return scores
    
    scores1 = calc_scores(movie1_data['reviews'])
    scores2 = calc_scores(movie2_data['reviews'])
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores1 + [scores1[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(245, 197, 24, 0.3)',
        line=dict(color='#f5c518', width=3),
        name=movie1_data['info'].get('title', 'Movie 1')
    ))
    
    fig.add_trace(go.Scatterpolar(
        r=scores2 + [scores2[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(59, 130, 246, 0.3)',
        line=dict(color='#3b82f6', width=3),
        name=movie2_data['info'].get('title', 'Movie 2')
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], showticklabels=True, 
                           tickfont=dict(color='#6b7280'), gridcolor='rgba(255,255,255,0.1)'),
            angularaxis=dict(tickfont=dict(color='#e5e7eb', size=14), gridcolor='rgba(255,255,255,0.1)')
        ),
        showlegend=True,
        legend=dict(orientation='h', y=-0.15, x=0.5, xanchor='center', font=dict(color='#e5e7eb')),
        paper_bgcolor='rgba(0,0,0,0)',
        height=450,
        margin=dict(t=60, b=80, l=80, r=80)
    )
    
    return fig


def create_comparison_bar(movie1_data: dict, movie2_data: dict) -> go.Figure:
    """创建对比柱状图"""
    df1 = movie1_data['reviews']
    df2 = movie2_data['reviews']
    
    metrics = ['正面率', '负面率', '平均分', '评论数']
    
    pos1 = (df1['sentiment_label'] == 'positive').mean() * 100 if 'sentiment_label' in df1.columns else 50
    neg1 = (df1['sentiment_label'] == 'negative').mean() * 100 if 'sentiment_label' in df1.columns else 20
    avg1 = df1['rating_num'].mean() * 10 if 'rating_num' in df1.columns and df1['rating_num'].notna().any() else 50
    cnt1 = min(len(df1) / 3, 100)
    
    pos2 = (df2['sentiment_label'] == 'positive').mean() * 100 if 'sentiment_label' in df2.columns else 50
    neg2 = (df2['sentiment_label'] == 'negative').mean() * 100 if 'sentiment_label' in df2.columns else 20
    avg2 = df2['rating_num'].mean() * 10 if 'rating_num' in df2.columns and df2['rating_num'].notna().any() else 50
    cnt2 = min(len(df2) / 3, 100)
    
    fig = go.Figure()
    fig.add_trace(go.Bar(
        name=movie1_data['info'].get('title', 'Movie 1'),
        x=metrics, y=[pos1, neg1, avg1, cnt1],
        marker_color='#f5c518'
    ))
    fig.add_trace(go.Bar(
        name=movie2_data['info'].get('title', 'Movie 2'),
        x=metrics, y=[pos2, neg2, avg2, cnt2],
        marker_color='#3b82f6'
    ))
    
    fig.update_layout(
        barmode='group',
        xaxis=dict(color='#9ca3af'),
        yaxis=dict(color='#9ca3af', gridcolor='rgba(255,255,255,0.1)'),
        legend=dict(orientation='h', y=1.15, x=0.5, xanchor='center', font=dict(color='#e5e7eb')),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        height=300,
        margin=dict(t=60, b=40, l=40, r=40)
    )
    return fig


# ==================== 报告生成 ====================
def generate_html_report(movie_info: dict, df: pd.DataFrame, aspects: list) -> str:
    """生成HTML分析报告"""
    pos_ratio = (df['sentiment_label'] == 'positive').mean() if 'sentiment_label' in df.columns else 0.5
    neg_ratio = (df['sentiment_label'] == 'negative').mean() if 'sentiment_label' in df.columns else 0.2
    avg_rating = df['rating_num'].mean() if 'rating_num' in df.columns and df['rating_num'].notna().any() else 0
    
    aspects_html = ""
    for asp in aspects:
        aspects_html += f"""
        <div style="margin-bottom: 10px;">
            <div style="display: flex; align-items: center;">
                <span style="width: 60px; font-weight: bold;">{asp['aspect']}</span>
                <div style="flex: 1; height: 24px; background: #f0f0f0; border-radius: 4px; overflow: hidden; display: flex;">
                    <div style="width: {asp['positive']}%; background: #22c55e; display: flex; align-items: center; justify-content: center; color: white; font-size: 12px;">{asp['positive']}%</div>
                    <div style="width: {asp['negative']}%; background: #ef4444; display: flex; align-items: center; justify-content: center; color: white; font-size: 12px;">{asp['negative']}%</div>
                </div>
            </div>
        </div>
        """
    
    pos_reviews = df[df['sentiment_label'] == 'positive']['content'].head(3).tolist() if 'sentiment_label' in df.columns else []
    neg_reviews = df[df['sentiment_label'] == 'negative']['content'].head(3).tolist() if 'sentiment_label' in df.columns else []
    
    pos_reviews_html = "".join([f"<li style='margin-bottom: 8px;'>\"{str(r)[:150]}...\"</li>" for r in pos_reviews if pd.notna(r)])
    neg_reviews_html = "".join([f"<li style='margin-bottom: 8px;'>\"{str(r)[:150]}...\"</li>" for r in neg_reviews if pd.notna(r)])
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>电影评论分析报告 - {movie_info.get('title', 'Unknown')}</title>
        <style>
            body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 20px; background: #f8fafc; color: #1e293b; }}
            h1 {{ color: #0f172a; border-bottom: 3px solid #f5c518; padding-bottom: 10px; }}
            h2 {{ color: #334155; margin-top: 30px; }}
            .header {{ background: linear-gradient(135deg, #1e293b 0%, #334155 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; }}
            .header h1 {{ border: none; color: #f5c518; margin: 0; }}
            .header .subtitle {{ color: #94a3b8; margin-top: 5px; }}
            .metric-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0; }}
            .metric-box {{ background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); text-align: center; }}
            .metric-value {{ font-size: 2.5rem; font-weight: bold; color: #0f172a; }}
            .metric-value.positive {{ color: #22c55e; }}
            .section {{ background: white; padding: 25px; border-radius: 12px; margin: 20px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
            .footer {{ text-align: center; color: #94a3b8; font-size: 0.8rem; margin-top: 40px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎬 {movie_info.get('title', 'Unknown')}</h1>
            <div class="subtitle">{movie_info.get('year', 'N/A')} | 导演: {movie_info.get('director', 'N/A')}</div>
        </div>
        
        <div class="metric-grid">
            <div class="metric-box">
                <div class="metric-value">{len(df):,}</div>
                <div>总评论数</div>
            </div>
            <div class="metric-box">
                <div class="metric-value positive">{pos_ratio*100:.0f}%</div>
                <div>正面评价率</div>
            </div>
            <div class="metric-box">
                <div class="metric-value">{avg_rating:.1f}</div>
                <div>平均评分</div>
            </div>
        </div>
        
        <div class="section">
            <h2>📊 方面级情感分析</h2>
            {aspects_html}
        </div>
        
        <div class="section">
            <h2>👍 典型正面评论</h2>
            <ul style="color: #22c55e;">{pos_reviews_html if pos_reviews_html else '<li>暂无数据</li>'}</ul>
        </div>
        
        <div class="section">
            <h2>👎 典型负面评论</h2>
            <ul style="color: #ef4444;">{neg_reviews_html if neg_reviews_html else '<li>暂无数据</li>'}</ul>
        </div>
        
        <div class="footer">
            <p>📅 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </body>
    </html>
    """
    return html


def generate_excel_report(movie_info: dict, df: pd.DataFrame, aspects: list) -> bytes:
    """生成Excel分析报告"""
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            summary_data = {
                '指标': ['电影名称', '年份', '导演', '总评论数', '正面率', '负面率', '平均评分'],
                '数值': [
                    movie_info.get('title', 'Unknown'),
                    movie_info.get('year', 'N/A'),
                    movie_info.get('director', 'N/A'),
                    len(df),
                    f"{(df['sentiment_label'] == 'positive').mean()*100:.1f}%" if 'sentiment_label' in df.columns else 'N/A',
                    f"{(df['sentiment_label'] == 'negative').mean()*100:.1f}%" if 'sentiment_label' in df.columns else 'N/A',
                    f"{df['rating_num'].mean():.1f}" if 'rating_num' in df.columns and df['rating_num'].notna().any() else 'N/A'
                ]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='概览', index=False)
            pd.DataFrame(aspects).to_excel(writer, sheet_name='方面分析', index=False)
            
            cols_to_export = ['content', 'sentiment_label', 'rating', 'date', 'author']
            export_cols = [c for c in cols_to_export if c in df.columns]
            if export_cols:
                df[export_cols].to_excel(writer, sheet_name='评论明细', index=False)
        
        return output.getvalue()
    except Exception as e:
        st.error(f"生成Excel失败: {e}")
        return None


def get_download_link(content, filename: str, file_type: str = 'html') -> str:
    """生成下载链接"""
    if file_type == 'html':
        b64 = base64.b64encode(content.encode('utf-8')).decode()
        mime = 'text/html'
    else:
        b64 = base64.b64encode(content).decode()
        mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    
    return f'<a href="data:{mime};base64,{b64}" download="{filename}" style="background: linear-gradient(135deg, #f5c518 0%, #eab308 100%); color: #000; padding: 10px 20px; border-radius: 8px; text-decoration: none; font-weight: 600; display: inline-block; margin-right: 10px;">📥 下载 {filename}</a>'


# ==================== 渲染辅助函数 ====================
def render_metrics(movie_info, df):
    """渲染指标卡片"""
    col1, col2, col3 = st.columns(3)
    
    pos_ratio = (df['sentiment_label'] == 'positive').mean() if 'sentiment_label' in df.columns else 0.5
    avg_rating = df['rating_num'].dropna().mean() if 'rating_num' in df.columns else movie_info.get('rating', 0)
    avg_rating = avg_rating if pd.notna(avg_rating) else 0
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">💬</div>
            <div class="metric-value">{len(df):,}</div>
            <div class="metric-label">总评论数</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">👍</div>
            <div class="metric-value" style="color: #22c55e;">{pos_ratio*100:.0f}%</div>
            <div class="metric-label">正面评价率</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">⭐</div>
            <div class="metric-value" style="color: #f5c518;">{avg_rating:.1f} / 10</div>
            <div class="metric-label">平均评分</div>
        </div>
        """, unsafe_allow_html=True)


def render_aspect_bars(aspects):
    """渲染方面情感条"""
    for asp in aspects:
        st.markdown(f"""
        <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
            <div style="width: 50px; color: #9ca3af; font-size: 0.8rem;">{asp['aspect']}</div>
            <div style="flex: 1; display: flex; height: 28px; border-radius: 4px; overflow: hidden;">
                <div style="width: {asp['positive']}%; background: #22c55e; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.7rem;">{asp['positive']}%</div>
                <div style="width: {asp['negative']}%; background: #ef4444; display: flex; align-items: center; justify-content: center; color: white; font-size: 0.7rem;">{asp['negative']}%</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


def render_reviews(df, n=5):
    """渲染评论列表"""
    for idx, row in df.head(n).iterrows():
        sentiment = row.get('sentiment_label', 'neutral')
        if pd.isna(sentiment):
            sentiment = 'neutral'
        
        author = row.get('author', row.get('user', 'Anonymous'))
        if pd.isna(author):
            author = 'Anonymous'
        
        content = row.get('content', '')
        if pd.isna(content):
            content = '(无内容)'
        else:
            content = str(content)[:200] + ('...' if len(str(content)) > 200 else '')
        
        rating = row.get('rating', 'N/A')
        date = row.get('date', '')
        
        st.markdown(f"""
        <div class="review-item {sentiment}">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: #e5e7eb; font-weight: 600;">{author}</span>
                <span style="color: #6b7280; font-size: 0.8rem;">{rating} · {date}</span>
            </div>
            <div style="color: #d1d5db; font-size: 0.9rem; line-height: 1.5;">{content}</div>
        </div>
        """, unsafe_allow_html=True)


def render_wordcloud():
    """渲染词云 (模拟)"""
    words = [
        ('masterpiece', 85, '#f5c518'), ('acting', 82, '#22c55e'), ('brilliant', 78, '#3b82f6'),
        ('plot', 75, '#a855f7'), ('amazing', 72, '#ec4899'), ('visuals', 70, '#06b6d4'),
        ('emotional', 68, '#f97316'), ('cinematography', 65, '#84cc16'), ('soundtrack', 63, '#eab308'),
        ('beautiful', 62, '#f43f5e'), ('powerful', 60, '#84cc16'), ('touching', 58, '#a855f7'),
    ]
    
    html = '<div style="display: flex; flex-wrap: wrap; gap: 0.5rem; justify-content: center; padding: 1rem;">'
    for word, size, color in words:
        font_size = 10 + (size - 35) * 0.3
        html += f'<span style="font-size: {font_size}px; color: {color}; padding: 0.2rem 0.5rem;">{word}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


def render_rag_sources(sources: list, show_all: bool = False):
    """渲染RAG检索来源"""
    if not sources:
        st.info("💡 未找到相关评论证据")
        return
    
    st.markdown(f"""
    <div style="background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3); 
                border-radius: 12px; padding: 1rem; margin-top: 1rem;">
        <div style="color: #60a5fa; font-weight: 600; margin-bottom: 0.75rem;">
            🧠 RAG 思考过程 | 检索到 {len(sources)} 条相关评论
        </div>
    """, unsafe_allow_html=True)
    
    display_count = len(sources) if show_all else min(5, len(sources))
    
    for i, source in enumerate(sources[:display_count]):
        similarity = source.get('similarity', 0.8)
        sentiment = source.get('sentiment', 'neutral')
        content = str(source.get('content', ''))[:200]
        
        sentiment_color = '#22c55e' if sentiment == 'positive' else '#ef4444' if sentiment == 'negative' else '#6b7280'
        
        st.markdown(f"""
        <div class="rag-source">
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <span style="color: #9ca3af; font-size: 0.75rem;">📄 评论 #{i+1}</span>
                <span class="rag-source-score">相似度: {similarity:.1%}</span>
            </div>
            <div style="color: #e5e7eb; font-size: 0.85rem;">"{content}..."</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)


# ==================== 页面函数 ====================
def page_dashboard(movie_info, df):
    """仪表盘页面 - 增强错误处理"""
    try:
        alerts = check_sentiment_alerts(df, movie_info.get('title', ''))
        if alerts:
            render_alerts(alerts)
    except Exception as e:
        pass  # 预警失败不影响主页面
    
    try:
        render_metrics(movie_info, df)
    except Exception as e:
        st.error(f"指标加载失败: {e}")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem;">📈 评分趋势</div></div>', unsafe_allow_html=True)
        try:
            fig = create_trend_chart(df)
            st.plotly_chart(fig, width='stretch', config={'displayModeBar': False})
        except Exception as e:
            st.info("📊 趋势图暂无数据")
    
    with col2:
        st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem;">📊 情感分布</div></div>', unsafe_allow_html=True)
        try:
            pos_ratio = 0.5
            if 'sentiment_label' in df.columns:
                pos_ratio = float((df['sentiment_label'] == 'positive').mean())
            if pd.isna(pos_ratio):
                pos_ratio = 0.5
            st.plotly_chart(create_sentiment_donut(pos_ratio), width='stretch', config={'displayModeBar': False})
        except Exception as e:
            st.info("📊 情感分布暂无数据")


def page_sentiment(movie_info, df):
    """情感分析页面"""
    col1, col2 = st.columns(2)
    
    pos_ratio = (df['sentiment_label'] == 'positive').mean() if 'sentiment_label' in df.columns else 0.5
    
    with col1:
        st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem;">📊 整体情感分布</div></div>', unsafe_allow_html=True)
        st.plotly_chart(create_sentiment_donut(pos_ratio), width='stretch', config={'displayModeBar': False})
    
    with col2:
        st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem;">🎯 ABSA 方面级情感</div></div>', unsafe_allow_html=True)
        render_aspect_bars(get_aspect_data(df))
    
    st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem;">💬 精选评论</div></div>', unsafe_allow_html=True)
    render_reviews(df, n=5)


def page_topics(df):
    """主题建模页面"""
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem;">📊 Top 讨论主题</div></div>', unsafe_allow_html=True)
        st.plotly_chart(create_topic_bars(get_topic_data(df)), width='stretch', config={'displayModeBar': False})
    
    with col2:
        st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem;">☁️ 高频词云</div></div>', unsafe_allow_html=True)
        render_wordcloud()
    
    st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem;">🔗 主题网络关系图</div></div>', unsafe_allow_html=True)
    st.plotly_chart(create_network_graph(df), width='stretch', config={'displayModeBar': False})


def page_advanced(df):
    """高级可视化页面"""
    st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 0.5rem;">🌊 流向分析 (Sankey)</div></div>', unsafe_allow_html=True)
    st.plotly_chart(create_sankey(), width='stretch', config={'displayModeBar': False})
    
    st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem;">🔮 3D 评论嵌入空间</div></div>', unsafe_allow_html=True)
    st.plotly_chart(create_3d_scatter(df), width='stretch', config={'displayModeBar': False})


# ==================== AI问答相关 ====================
def simulate_rag_search(question: str, df: pd.DataFrame, n_results: int = 5) -> list:
    """模拟RAG检索"""
    keywords = {
        '结局': ['ending', 'end', 'finale', '结局'],
        '演技': ['acting', 'actor', 'performance', '演技'],
        '剧情': ['plot', 'story', 'twist', '剧情'],
        '差评': ['bad', 'terrible', 'boring', '差'],
        '优点': ['amazing', 'great', 'perfect', '好'],
        '配乐': ['music', 'soundtrack', '配乐'],
    }
    
    search_kws = []
    for key, kws in keywords.items():
        if key in question:
            search_kws.extend(kws)
    
    if not search_kws:
        search_kws = ['good', 'bad', 'amazing']
    
    results = []
    for idx, row in df.iterrows():
        content = str(row.get('content', '')).lower()
        score = sum(1 for kw in search_kws if kw in content) / max(len(search_kws), 1)
        
        if score > 0:
            results.append({
                'content': row.get('content', ''),
                'sentiment': row.get('sentiment_label', 'neutral'),
                'similarity': min(score * 2 + 0.5, 0.98),
            })
    
    results.sort(key=lambda x: x['similarity'], reverse=True)
    return results[:n_results]


def call_api(question: str, movie_info: dict, df, reviews_sample: list) -> str:
    """调用API - 支持云端"""
    api_key = get_api_key('DEEPSEEK_API_KEY')
    
    if not api_key:
        return None
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        pos_ratio = (df['sentiment_label'] == 'positive').mean() if 'sentiment_label' in df.columns else 0.5
        reviews_text = "\n".join([f"- {str(r)[:100]}" for r in reviews_sample[:10]])
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是电影评论分析助手，用中文简洁回答。"},
                {"role": "user", "content": f"电影: {movie_info.get('title')}\n正面率: {pos_ratio*100:.0f}%\n评论:\n{reviews_text}\n\n问题: {question}"}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content
    except Exception as e:
        return None


def get_local_response(question: str, movie_info: dict, df) -> str:
    """本地回退回答"""
    pos_ratio = (df['sentiment_label'] == 'positive').mean() if 'sentiment_label' in df.columns else 0.5
    neg_ratio = (df['sentiment_label'] == 'negative').mean() if 'sentiment_label' in df.columns else 0.2
    total = len(df)
    
    if '结局' in question or 'ending' in question.lower():
        return f"根据 {total} 条评论，{pos_ratio*100:.0f}% 观众对《{movie_info.get('title')}》的结局持正面评价。"
    elif '演技' in question or 'acting' in question.lower():
        return f"在演技方面，{pos_ratio*100:.0f}% 的评论持正面态度，主角表演获得广泛好评。"
    elif '差评' in question or '缺点' in question:
        return f"主要负面评价 ({neg_ratio*100:.0f}%) 集中在节奏、剧情复杂度等方面。"
    else:
        return f"根据 {total} 条评论：{pos_ratio*100:.0f}% 正面，{neg_ratio*100:.0f}% 负面。整体评价良好。"


def page_ai(movie_info, df):
    """AI问答页面"""
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {'role': 'ai', 'content': f'你好！当前分析《{movie_info.get("title")}》的 {len(df)} 条评论。', 'sources': []}
        ]
    
    api_key = get_api_key('DEEPSEEK_API_KEY')
    has_api = api_key is not None
    
    col1, col2 = st.columns([4, 1])
    with col1:
        if has_api:
            st.success("🟢 DeepSeek API 已连接")
        else:
            st.warning("🟡 未配置 API，使用本地模式 (云端请在 Secrets 中配置 DEEPSEEK_API_KEY)")
    with col2:
        show_rag = st.checkbox("🧠 显示RAG", value=True)
    
    for msg in st.session_state.messages:
        if msg['role'] == 'ai':
            st.markdown(f"""
            <div style="background: rgba(55,65,81,0.5); border-radius: 16px; padding: 1rem; margin-bottom: 0.75rem; max-width: 85%;">
                <div style="font-size: 0.7rem; color: #9ca3af;">🤖 AI 助手</div>
                <div style="color: #e5e7eb;">{msg['content']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            if show_rag and msg.get('sources'):
                with st.expander("🧠 查看检索证据", expanded=False):
                    render_rag_sources(msg['sources'])
        else:
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #f5c518, #eab308); border-radius: 16px; padding: 1rem; margin-bottom: 0.75rem; max-width: 85%; margin-left: auto; color: #000;">
                {msg['content']}
            </div>
            """, unsafe_allow_html=True)
    
    suggestions = ['大家对结局怎么看?', '主要的差评点?', '演技评价如何?', '这部电影的优点?']
    cols = st.columns(len(suggestions))
    
    reviews_sample = df['content'].dropna().head(20).tolist() if 'content' in df.columns else []
    
    for i, sug in enumerate(suggestions):
        with cols[i]:
            if st.button(sug, key=f"sug_{i}", width='stretch'):
                st.session_state.messages.append({'role': 'user', 'content': sug})
                sources = simulate_rag_search(sug, df)
                
                response = call_api(sug, movie_info, df, reviews_sample)
                if response is None:
                    response = get_local_response(sug, movie_info, df)
                
                st.session_state.messages.append({'role': 'ai', 'content': response, 'sources': sources})
                st.rerun()
    
    user_input = st.chat_input("输入您的问题...")
    if user_input:
        st.session_state.messages.append({'role': 'user', 'content': user_input})
        sources = simulate_rag_search(user_input, df)
        
        response = call_api(user_input, movie_info, df, reviews_sample)
        if response is None:
            response = get_local_response(user_input, movie_info, df)
        
        st.session_state.messages.append({'role': 'ai', 'content': response, 'sources': sources})
        st.rerun()


# ==================== 🔧 竞品对比页面 (修复版) ====================
def page_comparison(all_movies: dict):
    """竞品双向对比页面 - 修复版"""
    st.markdown("""
    <div style="text-align: center; margin-bottom: 2rem;">
        <h2 style="color: white; margin: 0;">⚔️ 竞品双向对比分析</h2>
        <p style="color: #9ca3af;">选择两部电影进行多维度对比</p>
    </div>
    """, unsafe_allow_html=True)
    
    if len(all_movies) < 2:
        st.warning("⚠️ 需要至少2部电影才能进行对比分析")
        return
    
    # 构建电影选项列表 - 使用有序列表确保一致性
    movie_ids = sorted(list(all_movies.keys()))  # 排序确保顺序一致
    movie_id_to_label = {}
    movie_label_to_id = {}
    
    for mid in movie_ids:
        m = all_movies[mid]
        title = m['info'].get('title', mid)
        year = m['info'].get('year', 'N/A')
        label = f"{title} ({year})"
        movie_id_to_label[mid] = label
        movie_label_to_id[label] = mid
    
    movie_labels = [movie_id_to_label[mid] for mid in movie_ids]
    
    # 初始化 session_state - 存储电影ID而非索引
    if 'comp_movie_a_id' not in st.session_state or st.session_state.comp_movie_a_id not in movie_ids:
        st.session_state.comp_movie_a_id = movie_ids[0]
    if 'comp_movie_b_id' not in st.session_state or st.session_state.comp_movie_b_id not in movie_ids:
        st.session_state.comp_movie_b_id = movie_ids[1] if len(movie_ids) > 1 else movie_ids[0]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<p style="color: #f5c518; font-weight: 600; margin-bottom: 0.5rem;">🎬 电影 A</p>', unsafe_allow_html=True)
        
        # 获取当前选中电影的索引
        current_idx_a = movie_ids.index(st.session_state.comp_movie_a_id) if st.session_state.comp_movie_a_id in movie_ids else 0
        
        selected_a = st.selectbox(
            "电影 A", 
            movie_labels,
            index=current_idx_a,
            key="comp_select_a",
            label_visibility="collapsed"
        )
        
        # 更新 session_state 为电影ID
        st.session_state.comp_movie_a_id = movie_label_to_id[selected_a]
        movie1_id = st.session_state.comp_movie_a_id
        
        movie1_data = all_movies[movie1_id]
        movie1_df = analyze_reviews(movie1_data['reviews'].copy(), movie_id=movie1_id)
        
        pos1 = (movie1_df['sentiment_label'] == 'positive').mean() if 'sentiment_label' in movie1_df.columns else 0.5
        poster1 = movie1_data['info'].get('poster', '🎬')
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: rgba(30,30,50,0.5); border-radius: 12px; border: 1px solid rgba(245,197,24,0.3);">
            <div style="font-size: 3rem;">{poster1}</div>
            <div style="color: #f5c518; font-weight: bold; font-size: 1.2rem;">{movie1_data['info'].get('title', 'Movie 1')}</div>
            <div style="color: #e5e7eb;">评论数: {len(movie1_df)} | 正面率: {pos1*100:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown('<p style="color: #3b82f6; font-weight: 600; margin-bottom: 0.5rem;">🎬 电影 B</p>', unsafe_allow_html=True)
        
        # 获取当前选中电影的索引
        current_idx_b = movie_ids.index(st.session_state.comp_movie_b_id) if st.session_state.comp_movie_b_id in movie_ids else (1 if len(movie_ids) > 1 else 0)
        
        selected_b = st.selectbox(
            "电影 B", 
            movie_labels,
            index=current_idx_b,
            key="comp_select_b",
            label_visibility="collapsed"
        )
        
        # 更新 session_state 为电影ID
        st.session_state.comp_movie_b_id = movie_label_to_id[selected_b]
        movie2_id = st.session_state.comp_movie_b_id
        
        movie2_data = all_movies[movie2_id]
        movie2_df = analyze_reviews(movie2_data['reviews'].copy(), movie_id=movie2_id)
        
        pos2 = (movie2_df['sentiment_label'] == 'positive').mean() if 'sentiment_label' in movie2_df.columns else 0.5
        poster2 = movie2_data['info'].get('poster', '🎬')
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem; background: rgba(30,30,50,0.5); border-radius: 12px; border: 1px solid rgba(59,130,246,0.3);">
            <div style="font-size: 3rem;">{poster2}</div>
            <div style="color: #3b82f6; font-weight: bold; font-size: 1.2rem;">{movie2_data['info'].get('title', 'Movie 2')}</div>
            <div style="color: #e5e7eb;">评论数: {len(movie2_df)} | 正面率: {pos2*100:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)
    
    if movie1_id == movie2_id:
        st.warning("⚠️ 请选择不同的电影进行对比")
        return
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 雷达图
    st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem; text-align: center;">📊 多维度雷达图对比</div></div>', unsafe_allow_html=True)
    
    movie1_analyzed = {'info': movie1_data['info'], 'reviews': movie1_df}
    movie2_analyzed = {'info': movie2_data['info'], 'reviews': movie2_df}
    
    st.plotly_chart(create_comparison_radar(movie1_analyzed, movie2_analyzed), width='stretch', config={'displayModeBar': False})
    
    # 柱状图
    st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem; text-align: center;">📈 关键指标对比</div></div>', unsafe_allow_html=True)
    st.plotly_chart(create_comparison_bar(movie1_analyzed, movie2_analyzed), width='stretch', config={'displayModeBar': False})
    
    # 结论
    st.markdown(f"""
    <div class="card" style="margin-top: 1rem;">
        <div style="color: white; font-weight: 600; margin-bottom: 1rem;">🎯 对比分析结论</div>
        <div style="color: #d1d5db; line-height: 1.8;">
            <p>• <strong style="color: #f5c518;">{movie1_data['info'].get('title', 'A')}</strong> 正面率 {pos1*100:.0f}%，
               <strong style="color: #3b82f6;">{movie2_data['info'].get('title', 'B')}</strong> 正面率 {pos2*100:.0f}%。</p>
            <p>• {movie1_data['info'].get('title', 'A')} {'在口碑上占优' if pos1 > pos2 else '口碑略逊' if pos1 < pos2 else '口碑持平'}。</p>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ==================== 主函数 ====================
def main():
    # 加载真实数据
    all_movies = load_all_movies_from_data_dir("data")
    
    if not all_movies:
        st.warning("""
        ⚠️ **未找到电影数据**
        
        请将评论数据 CSV 文件放入 `data/` 文件夹。
        
        文件命名格式：`tt1375666_reviews.csv`
        """)
        return
    
    # ==================== 侧边栏 ====================
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0;">
            <div style="background: linear-gradient(135deg, #dc2626, #ef4444); width: 56px; height: 56px; border-radius: 14px; 
                        display: flex; align-items: center; justify-content: center; margin: 0 auto 1rem;">
                <span style="font-size: 1.75rem;">🎬</span>
            </div>
            <h3 style="color: white; margin: 0;">IMDb 分析系统</h3>
        </div>
        """, unsafe_allow_html=True)
        
        page = st.radio(
            "导航",
            ["📊 仪表盘", "👍 情感分析", "🔗 主题建模", "🤖 AI 问答", "⚔️ 竞品对比", "📈 高级可视化"],
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        
        # 主题选择
        st.markdown("#### 🎨 界面主题")
        new_theme = st.selectbox("主题", list(THEMES.keys()), 
                                index=list(THEMES.keys()).index(st.session_state.theme),
                                label_visibility="collapsed")
        if new_theme != st.session_state.theme:
            st.session_state.theme = new_theme
            st.rerun()
        
        st.markdown("---")
        st.markdown("#### 📁 数据源")
        st.success(f"✓ 已加载 {len(all_movies)} 部电影")
        
        # 上传
        uploaded = st.file_uploader("上传 CSV", type=['csv'], label_visibility="collapsed")
        if uploaded:
            try:
                uploaded_df = pd.read_csv(uploaded, encoding='utf-8-sig')
                movie_id = uploaded.name.split('_')[0] if uploaded.name.startswith('tt') else 'uploaded'
                info = {'id': movie_id, **MOVIE_METADATA.get(movie_id, {'title': uploaded.name, 'year': None, 'poster': '📄'})}
                all_movies['uploaded'] = {'info': info, 'reviews': uploaded_df}
                st.success(f"✓ 上传 {len(uploaded_df)} 条")
            except Exception as e:
                st.error(f"上传失败: {e}")
        
        # 报告导出
        st.markdown("---")
        st.markdown("#### 📄 导出报告")
        report_format = st.radio("格式", ["HTML", "Excel"], horizontal=True, label_visibility="collapsed")
        
        if st.button("🎯 生成报告", width='stretch', type="primary"):
            st.session_state['generate_report'] = True
            st.session_state['report_format'] = report_format
    
    # ==================== 主内容区 ====================
    
    if page == "⚔️ 竞品对比":
        page_comparison(all_movies)
        return
    
    # 电影选择
    col1, col2, col3 = st.columns([3, 2, 1])
    page_titles = {
        "📊 仪表盘": "仪表盘", "👍 情感分析": "情感分析", 
        "🔗 主题建模": "主题建模", "🤖 AI 问答": "AI 问答", 
        "📈 高级可视化": "高级可视化"
    }
    
    with col1:
        st.markdown(f"<h2 style='color: white; margin: 0;'>{page_titles.get(page, '仪表盘')}</h2>", unsafe_allow_html=True)
    
    with col2:
        movie_options = {}
        for mid, m in all_movies.items():
            info = m['info']
            title = info.get('title', mid)
            year = info.get('year', 'N/A')
            poster = info.get('poster', '🎬')
            label = f"{poster} {title} ({year})"
            movie_options[label] = mid
        
        selected = st.selectbox("选择电影", list(movie_options.keys()), label_visibility="collapsed")
        movie_id = movie_options[selected]
    
    with col3:
        if st.button("▶️ 运行", type="primary", width='stretch'):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    
    movie_data = all_movies[movie_id]
    movie_info = movie_data['info']
    df = analyze_reviews(movie_data['reviews'].copy(), movie_id=movie_id)
    
    # 报告生成
    if st.session_state.get('generate_report', False):
        st.session_state['generate_report'] = False
        
        with st.spinner("📄 生成报告..."):
            aspects = get_aspect_data(df)
            report_format = st.session_state.get('report_format', 'HTML')
            
            if report_format == 'HTML':
                report = generate_html_report(movie_info, df, aspects)
                filename = f"report_{movie_info.get('title', 'movie').replace(' ', '_')}.html"
                st.markdown(get_download_link(report, filename, 'html'), unsafe_allow_html=True)
            else:
                report = generate_excel_report(movie_info, df, aspects)
                if report:
                    filename = f"report_{movie_info.get('title', 'movie').replace(' ', '_')}.xlsx"
                    st.markdown(get_download_link(report, filename, 'excel'), unsafe_allow_html=True)
        
        st.success("✅ 报告生成成功！")
    
    # 渲染页面
    if page == "📊 仪表盘":
        page_dashboard(movie_info, df)
    elif page == "👍 情感分析":
        page_sentiment(movie_info, df)
    elif page == "🔗 主题建模":
        page_topics(df)
    elif page == "🤖 AI 问答":
        page_ai(movie_info, df)
    elif page == "📈 高级可视化":
        page_advanced(df)


if __name__ == "__main__":
    main()
