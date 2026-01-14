"""
数据管理模块
Data Management Module

功能:
1. 加载本地 JSON/CSV 数据
2. 加载 Kaggle 数据集
3. 数据验证和清洗
4. 数据持久化 (SQLite)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import sqlite3
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MovieData:
    """电影数据结构"""
    movie_id: str
    title: str
    year: Optional[int]
    rating: Optional[float]
    genres: List[str]
    director: Optional[str]
    plot: Optional[str]
    reviews: pd.DataFrame
    
    @property
    def num_reviews(self) -> int:
        return len(self.reviews)
    
    def to_dict(self) -> Dict:
        return {
            'movie_id': self.movie_id,
            'title': self.title,
            'year': self.year,
            'rating': self.rating,
            'genres': self.genres,
            'director': self.director,
            'plot': self.plot,
            'num_reviews': self.num_reviews
        }


class DataLoader:
    """
    数据加载器
    
    支持格式:
    - JSON (单个电影)
    - CSV (评论表格)
    - SQLite 数据库
    """
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._movies_cache = {}
    
    def load_json(self, filepath: str) -> Optional[MovieData]:
        """加载 JSON 格式的电影数据"""
        path = Path(filepath)
        if not path.exists():
            logger.error(f"文件不存在: {filepath}")
            return None
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            movie_info = data.get('movie', {})
            reviews_list = data.get('reviews', [])
            
            # 转换评论为 DataFrame
            reviews_df = pd.DataFrame(reviews_list) if reviews_list else pd.DataFrame()
            
            return MovieData(
                movie_id=movie_info.get('movie_id', path.stem),
                title=movie_info.get('title', 'Unknown'),
                year=movie_info.get('year'),
                rating=movie_info.get('rating'),
                genres=movie_info.get('genres', []),
                director=movie_info.get('director'),
                plot=movie_info.get('plot'),
                reviews=reviews_df
            )
            
        except Exception as e:
            logger.error(f"加载 JSON 失败: {e}")
            return None
    
    def load_csv(self, filepath: str, movie_info: Dict = None) -> Optional[MovieData]:
        """加载 CSV 格式的评论数据"""
        path = Path(filepath)
        if not path.exists():
            logger.error(f"文件不存在: {filepath}")
            return None
        
        try:
            # 尝试不同编码
            for encoding in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                logger.error("无法解码 CSV 文件")
                return None
            
            # 标准化列名
            df = self._standardize_columns(df)
            
            movie_info = movie_info or {}
            return MovieData(
                movie_id=movie_info.get('movie_id', path.stem),
                title=movie_info.get('title', path.stem),
                year=movie_info.get('year'),
                rating=movie_info.get('rating'),
                genres=movie_info.get('genres', []),
                director=movie_info.get('director'),
                plot=movie_info.get('plot'),
                reviews=df
            )
            
        except Exception as e:
            logger.error(f"加载 CSV 失败: {e}")
            return None
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化列名"""
        column_mapping = {
            # 评论内容
            'review': 'content',
            'text': 'content',
            'review_text': 'content',
            'comment': 'content',
            
            # 评分
            'score': 'rating',
            'stars': 'rating',
            'star_rating': 'rating',
            
            # 情感
            'sentiment': 'sentiment_label',
            'label': 'sentiment_label',
            
            # ID
            'id': 'review_id',
            'review_id': 'review_id',
            
            # 日期
            'review_date': 'date',
            'timestamp': 'date',
            'created_at': 'date',
        }
        
        df = df.rename(columns={k: v for k, v in column_mapping.items() 
                               if k in df.columns})
        
        # 确保有 review_id
        if 'review_id' not in df.columns:
            df['review_id'] = [f'r_{i}' for i in range(len(df))]
        
        return df
    
    def load_all_movies(self) -> Dict[str, MovieData]:
        """加载 data 目录下所有电影数据"""
        movies = {}
        
        # 加载 JSON 文件
        for json_file in self.data_dir.glob("*.json"):
            movie = self.load_json(json_file)
            if movie:
                movies[movie.movie_id] = movie
                logger.info(f"✓ 加载 {movie.title}: {movie.num_reviews} 条评论")
        
        # 加载 CSV 文件
        for csv_file in self.data_dir.glob("*.csv"):
            # 跳过已有 JSON 的电影
            if csv_file.stem not in movies:
                movie = self.load_csv(csv_file)
                if movie:
                    movies[movie.movie_id] = movie
                    logger.info(f"✓ 加载 {movie.title}: {movie.num_reviews} 条评论")
        
        self._movies_cache = movies
        return movies
    
    def load_kaggle_imdb50k(self, filepath: str) -> Optional[MovieData]:
        """
        加载 Kaggle IMDB 50K 数据集
        
        数据集结构: review, sentiment
        """
        try:
            df = pd.read_csv(filepath)
            
            # 标准化
            df = df.rename(columns={'review': 'content', 'sentiment': 'sentiment_label'})
            df['review_id'] = [f'imdb50k_{i}' for i in range(len(df))]
            
            # 情感标签标准化
            df['sentiment_label'] = df['sentiment_label'].str.lower()
            
            return MovieData(
                movie_id='imdb_50k',
                title='IMDB 50K Dataset',
                year=None,
                rating=None,
                genres=[],
                director=None,
                plot='IMDB 50K Movie Reviews Dataset from Kaggle',
                reviews=df
            )
            
        except Exception as e:
            logger.error(f"加载 Kaggle 数据集失败: {e}")
            return None
    
    def get_cached_movies(self) -> Dict[str, MovieData]:
        """获取缓存的电影数据"""
        if not self._movies_cache:
            self.load_all_movies()
        return self._movies_cache


class DatabaseManager:
    """
    数据库管理器 - SQLite
    
    用于持久化存储分析结果
    """
    
    def __init__(self, db_path: str = "data/imdb_analysis.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS movies (
                    movie_id TEXT PRIMARY KEY,
                    title TEXT,
                    year INTEGER,
                    rating REAL,
                    genres TEXT,
                    director TEXT,
                    plot TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id TEXT PRIMARY KEY,
                    movie_id TEXT,
                    content TEXT,
                    rating INTEGER,
                    date TEXT,
                    author TEXT,
                    sentiment_label TEXT,
                    sentiment_score REAL,
                    quality_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (movie_id) REFERENCES movies(movie_id)
                );
                
                CREATE TABLE IF NOT EXISTS analysis_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    movie_id TEXT,
                    analysis_type TEXT,
                    result_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (movie_id) REFERENCES movies(movie_id)
                );
                
                CREATE INDEX IF NOT EXISTS idx_reviews_movie ON reviews(movie_id);
                CREATE INDEX IF NOT EXISTS idx_reviews_sentiment ON reviews(sentiment_label);
            """)
    
    def save_movie(self, movie: MovieData):
        """保存电影信息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO movies 
                (movie_id, title, year, rating, genres, director, plot)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                movie.movie_id,
                movie.title,
                movie.year,
                movie.rating,
                json.dumps(movie.genres),
                movie.director,
                movie.plot
            ))
    
    def save_reviews(self, movie_id: str, reviews_df: pd.DataFrame):
        """保存评论数据"""
        with sqlite3.connect(self.db_path) as conn:
            for _, row in reviews_df.iterrows():
                conn.execute("""
                    INSERT OR REPLACE INTO reviews 
                    (review_id, movie_id, content, rating, date, author,
                     sentiment_label, sentiment_score, quality_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    row.get('review_id', ''),
                    movie_id,
                    row.get('content', ''),
                    row.get('rating'),
                    row.get('date'),
                    row.get('author'),
                    row.get('sentiment_label'),
                    row.get('sentiment_score'),
                    row.get('quality_score')
                ))
    
    def save_analysis(self, movie_id: str, analysis_type: str, result: Dict):
        """保存分析结果"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO analysis_results (movie_id, analysis_type, result_json)
                VALUES (?, ?, ?)
            """, (movie_id, analysis_type, json.dumps(result, default=str)))
    
    def load_movie(self, movie_id: str) -> Optional[MovieData]:
        """加载电影数据"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            movie_row = conn.execute(
                "SELECT * FROM movies WHERE movie_id = ?", (movie_id,)
            ).fetchone()
            
            if not movie_row:
                return None
            
            reviews_rows = conn.execute(
                "SELECT * FROM reviews WHERE movie_id = ?", (movie_id,)
            ).fetchall()
            
            reviews_df = pd.DataFrame([dict(r) for r in reviews_rows])
            
            return MovieData(
                movie_id=movie_row['movie_id'],
                title=movie_row['title'],
                year=movie_row['year'],
                rating=movie_row['rating'],
                genres=json.loads(movie_row['genres'] or '[]'),
                director=movie_row['director'],
                plot=movie_row['plot'],
                reviews=reviews_df
            )
    
    def get_all_movie_ids(self) -> List[str]:
        """获取所有电影 ID"""
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute("SELECT movie_id FROM movies").fetchall()
            return [r[0] for r in rows]
    
    def get_latest_analysis(self, movie_id: str, analysis_type: str) -> Optional[Dict]:
        """获取最新分析结果"""
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("""
                SELECT result_json FROM analysis_results 
                WHERE movie_id = ? AND analysis_type = ?
                ORDER BY created_at DESC LIMIT 1
            """, (movie_id, analysis_type)).fetchone()
            
            return json.loads(row[0]) if row else None


def create_sample_data() -> Dict[str, MovieData]:
    """
    创建示例数据（用于演示）
    
    生成 5 部热门电影的模拟评论数据
    """
    import random
    
    movies_info = [
        {'movie_id': 'tt1375666', 'title': 'Inception', 'year': 2010, 
         'rating': 8.8, 'genres': ['Sci-Fi', 'Action'], 'director': 'Christopher Nolan'},
        {'movie_id': 'tt0111161', 'title': 'The Shawshank Redemption', 'year': 1994,
         'rating': 9.3, 'genres': ['Drama'], 'director': 'Frank Darabont'},
        {'movie_id': 'tt0068646', 'title': 'The Godfather', 'year': 1972,
         'rating': 9.2, 'genres': ['Crime', 'Drama'], 'director': 'Francis Ford Coppola'},
        {'movie_id': 'tt0468569', 'title': 'The Dark Knight', 'year': 2008,
         'rating': 9.0, 'genres': ['Action', 'Crime'], 'director': 'Christopher Nolan'},
        {'movie_id': 'tt0133093', 'title': 'The Matrix', 'year': 1999,
         'rating': 8.7, 'genres': ['Sci-Fi', 'Action'], 'director': 'The Wachowskis'},
    ]
    
    positive_templates = [
        "This movie is absolutely {adj}! The {aspect} is incredible. A must-watch masterpiece.",
        "One of the best films I've ever seen. The {aspect} blew me away. {adj} performance!",
        "Brilliant {aspect}! {adj} storytelling and direction. Highly recommended.",
        "The {aspect} in this film is {adj}. Every scene is perfectly crafted.",
        "I loved every minute. The {aspect} is simply {adj}. 10/10 would watch again.",
        "Outstanding {aspect}! The {adj} execution makes this a timeless classic.",
        "{adj} movie! The {aspect} alone is worth watching. Pure cinema magic.",
    ]
    
    negative_templates = [
        "Very disappointing. The {aspect} was {adj}. Expected much better.",
        "Overrated film. The {aspect} is {adj} at best. Couldn't finish it.",
        "The {aspect} ruined this movie. {adj} and poorly executed.",
        "Waste of time. {adj} {aspect} throughout. Don't bother watching.",
        "I don't understand the hype. The {aspect} is {adj}. Very let down.",
        "The {adj} {aspect} made this unwatchable. Huge disappointment.",
    ]
    
    neutral_templates = [
        "Mixed feelings about this one. The {aspect} was okay, nothing special.",
        "Average film. The {aspect} has moments but also weaknesses.",
        "It's decent. The {aspect} could be better but it's watchable.",
        "Neither great nor terrible. The {aspect} is just average.",
    ]
    
    positive_adj = ['amazing', 'brilliant', 'outstanding', 'incredible', 'fantastic', 
                   'excellent', 'stunning', 'masterful', 'perfect', 'breathtaking']
    negative_adj = ['terrible', 'poor', 'weak', 'boring', 'disappointing', 
                   'mediocre', 'awful', 'dull', 'confusing', 'pretentious']
    aspects = ['acting', 'plot', 'direction', 'cinematography', 'soundtrack', 
              'dialogue', 'pacing', 'ending', 'visual effects', 'character development']
    
    users = [f"User{i}" for i in range(1, 101)] + ['MovieBuff99', 'CinemaLover', 
             'FilmCritic', 'CasualViewer', 'HardcoreFan', 'FirstTimeWatcher']
    
    movies = {}
    
    for info in movies_info:
        # 根据评分决定正负面比例
        rating = info['rating']
        pos_prob = 0.85 if rating >= 9 else (0.7 if rating >= 8.5 else 0.55)
        
        reviews = []
        num_reviews = random.randint(150, 300)
        
        for i in range(num_reviews):
            rand = random.random()
            if rand < pos_prob:
                template = random.choice(positive_templates)
                adj = random.choice(positive_adj)
                sentiment = 'positive'
                user_rating = random.randint(8, 10)
            elif rand < pos_prob + 0.15:
                template = random.choice(neutral_templates)
                adj = 'decent'
                sentiment = 'neutral'
                user_rating = random.randint(5, 7)
            else:
                template = random.choice(negative_templates)
                adj = random.choice(negative_adj)
                sentiment = 'negative'
                user_rating = random.randint(1, 4)
            
            aspect = random.choice(aspects)
            content = template.format(adj=adj, aspect=aspect)
            
            # 添加更多细节让评论更真实
            if random.random() > 0.5:
                extras = [
                    f" {info['director']}'s vision is clear throughout.",
                    f" This is definitely one of the best {info['genres'][0]} movies.",
                    " The runtime felt just right.",
                    " Would recommend to anyone who appreciates good cinema.",
                    " Not sure why this has such high ratings.",
                ]
                content += random.choice(extras)
            
            reviews.append({
                'review_id': f"{info['movie_id']}_{i}",
                'movie_id': info['movie_id'],
                'content': content,
                'rating': user_rating,
                'author': random.choice(users),
                'date': f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                'helpful_votes': random.randint(0, 200),
            })
        
        movies[info['movie_id']] = MovieData(
            movie_id=info['movie_id'],
            title=info['title'],
            year=info['year'],
            rating=info['rating'],
            genres=info['genres'],
            director=info['director'],
            plot=f"A {info['genres'][0].lower()} masterpiece directed by {info['director']}.",
            reviews=pd.DataFrame(reviews)
        )
        
        logger.info(f"✓ 生成 {info['title']}: {len(reviews)} 条评论")
    
    return movies
