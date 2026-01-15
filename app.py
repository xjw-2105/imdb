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
        
        .metric-card {{
            background: linear-gradient(135deg, {theme['card_bg']} 0%, rgba(20,25,45,0.9) 100%);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 1.25rem;
            transition: all 0.3s ease;
        }}
        .metric-card:hover {{ 
            transform: translateY(-4px); 
            box-shadow: 0 12px 40px {theme['primary']}26; 
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


# ==================== 电影元数据 (扩展版) ====================
MOVIE_METADATA = {
    # 原有电影
    'tt0111161': {'title': 'The Shawshank Redemption', 'year': 1994, 'rating': 9.3, 
                  'genres': ['Drama'], 'director': 'Frank Darabont', 'poster': '🎭'},
    'tt1375666': {'title': 'Inception', 'year': 2010, 'rating': 8.8, 
                  'genres': ['Sci-Fi', 'Action'], 'director': 'Christopher Nolan', 'poster': '🌀'},
    'tt0068646': {'title': 'The Godfather', 'year': 1972, 'rating': 9.2, 
                  'genres': ['Crime', 'Drama'], 'director': 'Francis Ford Coppola', 'poster': '🎩'},
    'tt0468569': {'title': 'The Dark Knight', 'year': 2008, 'rating': 9.0, 
                  'genres': ['Action', 'Crime'], 'director': 'Christopher Nolan', 'poster': '🦇'},
    'tt0133093': {'title': 'The Matrix', 'year': 1999, 'rating': 8.7, 
                  'genres': ['Sci-Fi', 'Action'], 'director': 'The Wachowskis', 'poster': '💊'},
    'tt0109830': {'title': 'Forrest Gump', 'year': 1994, 'rating': 8.8, 
                  'genres': ['Drama', 'Romance'], 'director': 'Robert Zemeckis', 'poster': '🏃'},
    'tt0167260': {'title': 'LOTR: Return of the King', 'year': 2003, 'rating': 9.0, 
                  'genres': ['Fantasy', 'Adventure'], 'director': 'Peter Jackson', 'poster': '💍'},
    'tt0137523': {'title': 'Fight Club', 'year': 1999, 'rating': 8.8, 
                  'genres': ['Drama'], 'director': 'David Fincher', 'poster': '🥊'},
    'tt15398776': {'title': 'Oppenheimer', 'year': 2023, 'rating': 8.4,
                   'genres': ['Biography', 'Drama'], 'director': 'Christopher Nolan', 'poster': '💥'},
    'tt1517268': {'title': 'Barbie', 'year': 2023, 'rating': 6.8,
                  'genres': ['Comedy', 'Fantasy'], 'director': 'Greta Gerwig', 'poster': '💗'},
    
    # 🆕 新增电影元数据
    'tt0816692': {'title': 'Interstellar', 'year': 2014, 'rating': 8.7,
                  'genres': ['Sci-Fi', 'Drama'], 'director': 'Christopher Nolan', 'poster': '🚀'},
    'tt5697572': {'title': 'Three Billboards Outside Ebbing, Missouri', 'year': 2017, 'rating': 8.1,
                  'genres': ['Crime', 'Drama'], 'director': 'Martin McDonagh', 'poster': '🪧'},
    'tt0245429': {'title': 'Spirited Away', 'year': 2001, 'rating': 8.6,
                  'genres': ['Animation', 'Fantasy'], 'director': 'Hayao Miyazaki', 'poster': '🐉'},
    'tt1099212': {'title': 'Twilight', 'year': 2008, 'rating': 5.3,
                  'genres': ['Drama', 'Fantasy'], 'director': 'Catherine Hardwicke', 'poster': '🧛'},
    'tt0110912': {'title': 'Pulp Fiction', 'year': 1994, 'rating': 8.9,
                  'genres': ['Crime', 'Drama'], 'director': 'Quentin Tarantino', 'poster': '💼'},
    'tt4154796': {'title': 'Avengers: Endgame', 'year': 2019, 'rating': 8.4,
                  'genres': ['Action', 'Sci-Fi'], 'director': 'Russo Brothers', 'poster': '🦸'},
    'tt0120737': {'title': 'LOTR: Fellowship of the Ring', 'year': 2001, 'rating': 8.9,
                  'genres': ['Fantasy', 'Adventure'], 'director': 'Peter Jackson', 'poster': '💍'},
    'tt0172495': {'title': 'Gladiator', 'year': 2000, 'rating': 8.5,
                  'genres': ['Action', 'Drama'], 'director': 'Ridley Scott', 'poster': '⚔️'},
    'tt0993846': {'title': 'The Wolf of Wall Street', 'year': 2013, 'rating': 8.2,
                  'genres': ['Biography', 'Comedy'], 'director': 'Martin Scorsese', 'poster': '💰'},
    'tt0482571': {'title': 'The Prestige', 'year': 2006, 'rating': 8.5,
                  'genres': ['Drama', 'Mystery'], 'director': 'Christopher Nolan', 'poster': '🎩'},
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
def analyze_reviews(_df):
    """分析评论数据 - 支持多语言，增强错误处理"""
    df = _df.copy()
    
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
    """创建情感分布甜甜圈图"""
    theme = get_theme()
    if neg_ratio is None:
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
    """创建评分趋势图"""
    theme = get_theme()
    rating_col = 'rating_num' if 'rating_num' in df.columns else None
    
    if 'date' not in df.columns or rating_col is None:
        months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
        ratings = [7.5, 8.0, 7.8, 8.2, 8.5, 8.3]
    else:
        df_copy = df.copy()
        df_copy['date'] = pd.to_datetime(df_copy['date'], errors='coerce')
        df_copy = df_copy.dropna(subset=['date', rating_col])
        
        if df_copy.empty or len(df_copy) < 5:
            months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun']
            ratings = [7.5, 8.0, 7.8, 8.2, 8.5, 8.3]
        else:
            df_copy['month'] = df_copy['date'].dt.to_period('M')
            monthly = df_copy.groupby('month')[rating_col].mean().reset_index()
            monthly['month'] = monthly['month'].astype(str)
            months = monthly['month'].tolist()[-12:]  # 最近12个月
            ratings = monthly[rating_col].tolist()[-12:]
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months, y=ratings, mode='lines+markers',
        line=dict(color=theme['primary'], width=3),
        marker=dict(size=10, color=theme['primary']),
        fill='tozeroy', fillcolor=f"{theme['primary']}20"
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
    """仪表盘页面"""
    alerts = check_sentiment_alerts(df, movie_info.get('title', ''))
    if alerts:
        render_alerts(alerts)
    
    render_metrics(movie_info, df)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem;">📈 评分趋势</div></div>', unsafe_allow_html=True)
        st.plotly_chart(create_trend_chart(df), use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem;">📊 情感分布</div></div>', unsafe_allow_html=True)
        pos_ratio = (df['sentiment_label'] == 'positive').mean() if 'sentiment_label' in df.columns else 0.5
        st.plotly_chart(create_sentiment_donut(pos_ratio), use_container_width=True, config={'displayModeBar': False})


def page_sentiment(movie_info, df):
    """情感分析页面"""
    col1, col2 = st.columns(2)
    
    pos_ratio = (df['sentiment_label'] == 'positive').mean() if 'sentiment_label' in df.columns else 0.5
    
    with col1:
        st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem;">📊 整体情感分布</div></div>', unsafe_allow_html=True)
        st.plotly_chart(create_sentiment_donut(pos_ratio), use_container_width=True, config={'displayModeBar': False})
    
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
        st.plotly_chart(create_topic_bars(get_topic_data(df)), use_container_width=True, config={'displayModeBar': False})
    
    with col2:
        st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem;">☁️ 高频词云</div></div>', unsafe_allow_html=True)
        render_wordcloud()
    
    st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem;">🔗 主题网络关系图</div></div>', unsafe_allow_html=True)
    st.plotly_chart(create_network_graph(df), use_container_width=True, config={'displayModeBar': False})


def page_advanced(df):
    """高级可视化页面"""
    st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 0.5rem;">🌊 流向分析 (Sankey)</div></div>', unsafe_allow_html=True)
    st.plotly_chart(create_sankey(), use_container_width=True, config={'displayModeBar': False})
    
    st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem;">🔮 3D 评论嵌入空间</div></div>', unsafe_allow_html=True)
    st.plotly_chart(create_3d_scatter(df), use_container_width=True, config={'displayModeBar': False})


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
            if st.button(sug, key=f"sug_{i}", use_container_width=True):
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
    
    # 构建电影选项列表
    movie_ids = list(all_movies.keys())
    movie_labels = []
    for mid in movie_ids:
        m = all_movies[mid]
        title = m['info'].get('title', mid)
        year = m['info'].get('year', 'N/A')
        movie_labels.append(f"{title} ({year})")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="comparison-card">', unsafe_allow_html=True)
        # 使用 key 来避免状态问题
        idx1 = st.selectbox("🎬 电影 A", range(len(movie_labels)), 
                           format_func=lambda x: movie_labels[x],
                           index=0, key="comp_a_select")
        
        movie1_id = movie_ids[idx1]
        movie1_data = all_movies[movie1_id]
        movie1_df = analyze_reviews(movie1_data['reviews'].copy())
        
        pos1 = (movie1_df['sentiment_label'] == 'positive').mean() if 'sentiment_label' in movie1_df.columns else 0.5
        poster1 = movie1_data['info'].get('poster', '🎬')
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem;">{poster1}</div>
            <div style="color: #f5c518; font-weight: bold; font-size: 1.2rem;">{movie1_data['info'].get('title', 'Movie 1')}</div>
            <div style="color: #9ca3af;">评论数: {len(movie1_df)} | 正面率: {pos1*100:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="comparison-card">', unsafe_allow_html=True)
        # 默认选择第二部电影（如果有的话）
        default_idx2 = 1 if len(movie_labels) > 1 else 0
        # 如果第一个选了1，第二个默认选0
        if idx1 == 1:
            default_idx2 = 0
        
        idx2 = st.selectbox("🎬 电影 B", range(len(movie_labels)), 
                           format_func=lambda x: movie_labels[x],
                           index=default_idx2, key="comp_b_select")
        
        movie2_id = movie_ids[idx2]
        movie2_data = all_movies[movie2_id]
        movie2_df = analyze_reviews(movie2_data['reviews'].copy())
        
        pos2 = (movie2_df['sentiment_label'] == 'positive').mean() if 'sentiment_label' in movie2_df.columns else 0.5
        poster2 = movie2_data['info'].get('poster', '🎬')
        
        st.markdown(f"""
        <div style="text-align: center; padding: 1rem;">
            <div style="font-size: 3rem;">{poster2}</div>
            <div style="color: #3b82f6; font-weight: bold; font-size: 1.2rem;">{movie2_data['info'].get('title', 'Movie 2')}</div>
            <div style="color: #9ca3af;">评论数: {len(movie2_df)} | 正面率: {pos2*100:.0f}%</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    if movie1_id == movie2_id:
        st.warning("⚠️ 请选择不同的电影进行对比")
        return
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 雷达图
    st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem; text-align: center;">📊 多维度雷达图对比</div></div>', unsafe_allow_html=True)
    
    movie1_analyzed = {'info': movie1_data['info'], 'reviews': movie1_df}
    movie2_analyzed = {'info': movie2_data['info'], 'reviews': movie2_df}
    
    st.plotly_chart(create_comparison_radar(movie1_analyzed, movie2_analyzed), use_container_width=True, config={'displayModeBar': False})
    
    # 柱状图
    st.markdown('<div class="card"><div style="color: white; font-weight: 600; margin-bottom: 1rem; text-align: center;">📈 关键指标对比</div></div>', unsafe_allow_html=True)
    st.plotly_chart(create_comparison_bar(movie1_analyzed, movie2_analyzed), use_container_width=True, config={'displayModeBar': False})
    
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
        
        if st.button("🎯 生成报告", use_container_width=True, type="primary"):
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
        if st.button("▶️ 运行", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    st.markdown("---")
    
    movie_data = all_movies[movie_id]
    movie_info = movie_data['info']
    df = analyze_reviews(movie_data['reviews'].copy())
    
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
