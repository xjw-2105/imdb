"""


核心技术:
1. 多模型集成情感分析 (Transformer + VADER + Lexicon)
2. 真正的方面级情感分析 (ABSA) - 依存句法 + 规则
3. 动态主题建模 (LDA/NMF + 时间演化)
4. 评论质量评估
5. 命名实体识别
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict# 数据类replace字典
from enum import Enum
from collections import Counter, defaultdict#一些高级容器哦
import re
import logging#日志系统
from functools import lru_cache
import warnings
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

#标签情感枚举的部分！
class SentimentLabel(Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass#装饰器
class SentimentResult:
    label: SentimentLabel
    score: float  # 0-1, 越高越正面！
    confidence: float
    method: str
    details: Dict = field(default_factory=dict)#工厂函数


@dataclass#分析结果容器！
class AspectSentiment:
    aspect: str
    aspect_cn: str  
    sentiment: SentimentLabel
    confidence: float
    mentions: int
    evidence: List[str] = field(default_factory=list)#可解释性


@dataclass#模型结果容器
class TopicInfo:
    topic_id: int
    keywords: List[str]
    keyword_weights: List[float]
    num_docs: int
    label: str  # 自动生成的标签


@dataclass
class ReviewAnalysis:
    """单条评论的完整分析结果"""
    review_id: str
    sentiment: SentimentResult
    aspects: List[AspectSentiment]
    quality_score: float
    topics: List[int]
    entities: List[str]
    word_count: int
    
    def to_dict(self) -> Dict:#转成字典方便展示#聚合#序列化
        return {
            'review_id': self.review_id,
            'sentiment_label': self.sentiment.label.value,
            'sentiment_score': self.sentiment.score,
            'sentiment_confidence': self.sentiment.confidence,
            'quality_score': self.quality_score,
            'word_count': self.word_count,
            'aspects': [{'aspect': a.aspect, 'aspect_cn': a.aspect_cn, 
                        'sentiment': a.sentiment.value, 'confidence': a.confidence}
                       for a in self.aspects]
        }


class TextPreprocessor:
    """文本预处理器"""
    
    def __init__(self):
        self._init_resources()#可以自动下载哦
    
    def _init_resources(self):
        """初始化 NLTK 资源"""
        import nltk
        import ssl
        
        # 处理 SSL 问题 (🌟)#跨平台兼容
        try:
            _create_unverified_https_context = ssl._create_unverified_context
        except AttributeError:
            pass
        else:
            ssl._create_default_https_context = _create_unverified_https_context
        
        # 下载必要资源
        for resource in ['punkt', 'punkt_tab', 'stopwords', 'wordnet', 
                        'vader_lexicon', 'averaged_perceptron_tagger']:
            try:
                nltk.data.find(f'tokenizers/{resource}' if 'punkt' in resource 
                             else f'corpora/{resource}' if resource in ['stopwords', 'wordnet']
                             else f'sentiment/{resource}' if resource == 'vader_lexicon'
                             else f'taggers/{resource}')
            except LookupError:
                nltk.download(resource, quiet=True)
        
        from nltk.corpus import stopwords
        from nltk.stem import WordNetLemmatizer
        
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # 电影领域保留词
        self.domain_words = {
            'plot', 'acting', 'actor', 'actress', 'director', 'scene',
            'character', 'story', 'ending', 'script', 'dialogue',
            'cinematography', 'soundtrack', 'score', 'performance',
            'cast', 'movie', 'film', 'cinema', 'screen', 'visual',
            'effect', 'music', 'pacing', 'twist'
        }
        
        # 否定词#情感极性反转
        self.negation_words = {'not', "n't", 'never', 'no', 'none', 'neither',
                              'nobody', 'nothing', 'nowhere', 'hardly', 'barely'}
        
        # 正则表达式
        self.html_re = re.compile(r'<[^>]+>')
        self.url_re = re.compile(r'http\S+|www\S+')
        self.special_re = re.compile(r'[^a-zA-Z0-9\s\.\,\!\?\'\-]')#但是我保留了字母数字标点
        self.whitespace_re = re.compile(r'\s+')#连续空格
    
    def clean(self, text: str) -> str:
        """清洗文本"""
        if not text or not isinstance(text, str):
            return ""
        text = self.html_re.sub('', text)
        text = self.url_re.sub('', text)
        text = self.special_re.sub(' ', text)
        text = self.whitespace_re.sub(' ', text).strip()
        return text
    
    def tokenize(self, text: str, remove_stopwords: bool = True, #智能分词
                lemmatize: bool = True) -> List[str]:
        """分词"""
        from nltk.tokenize import word_tokenize
        
        try:
            tokens = word_tokenize(text.lower())# NLTK 分词#split
        except:
            tokens = text.lower().split()# 降级方案
        
        result = []
        for token in tokens:
            # A. 保留否定词领域词 
            if token in self.negation_words or token in self.domain_words:
                result.append(token)
            # B. 去除停用词
            elif remove_stopwords and token in self.stop_words:
                continue
            elif len(token) < 2:
                continue
            # C. 词形还原 
            elif lemmatize:
                result.append(self.lemmatizer.lemmatize(token))
            else:
                result.append(token)
        
        return result
    
    def extract_sentences(self, text: str) -> List[str]:
        """提取句子"""
        from nltk.tokenize import sent_tokenize
        try:
            return sent_tokenize(text)
        except:
            return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]


class MultiModelSentimentAnalyzer:
    """
    多模型集成情感分析器#我要讲这个点
    
    集成策略:
    1. Transformer (DistilBERT) - 深度语义理解-0.5
    2. VADER - 规则基础，擅长社交媒体文本-0.3
    3. 领域词典 - 电影领域特定词汇-0.2
    4. 加权投票决策
    """
    
    def __init__(self, use_transformer: bool = True):
        self.preprocessor = TextPreprocessor()
        self.use_transformer = use_transformer
        self._transformer = None
        self._init_lexicons()# 初始化词典
    
    def _init_lexicons(self):
        """初始化情感词典"""
        from nltk.sentiment import SentimentIntensityAnalyzer
        self.vader = SentimentIntensityAnalyzer()# 加载 VADER 模型
        
        # 电影领域增强词典
        self.positive_words = {
            'masterpiece': 2.0, 'brilliant': 1.8, 'outstanding': 1.7,
            'amazing': 1.6, 'excellent': 1.6, 'fantastic': 1.5,
            'wonderful': 1.5, 'incredible': 1.5, 'perfect': 1.8,
            'beautiful': 1.3, 'stunning': 1.4, 'captivating': 1.4,
            'compelling': 1.3, 'engaging': 1.2, 'gripping': 1.3,
            'riveting': 1.4, 'breathtaking': 1.5, 'heartwarming': 1.3,
            'hilarious': 1.4, 'touching': 1.3, 'powerful': 1.3,
            'unforgettable': 1.5, 'genius': 1.6, 'flawless': 1.7,
            'superb': 1.5, 'remarkable': 1.4, 'impressive': 1.3,
            'love': 1.2, 'loved': 1.2, 'best': 1.4, 'great': 1.1, 'good': 0.8
        }
        
        self.negative_words = {
            'terrible': -1.8, 'awful': -1.7, 'horrible': -1.7,
            'worst': -2.0, 'bad': -1.2, 'poor': -1.3, 'boring': -1.4,
            'disappointing': -1.5, 'waste': -1.4, 'stupid': -1.3,
            'ridiculous': -1.2, 'annoying': -1.2, 'dull': -1.3,
            'weak': -1.1, 'mediocre': -1.0, 'forgettable': -1.2,
            'predictable': -0.9, 'cliche': -1.0, 'overrated': -1.3,
            'confusing': -1.1, 'slow': -0.8, 'painful': -1.4,
            'unbearable': -1.6, 'disaster': -1.7, 'unwatchable': -1.8,
            'pretentious': -1.3, 'tedious': -1.4, 'lifeless': -1.5
        }
        
        # 强化词和减弱词
        self.intensifiers = {
            'very': 1.5, 'really': 1.4, 'extremely': 1.8, 'absolutely': 1.7,
            'completely': 1.6, 'totally': 1.5, 'utterly': 1.7, 'incredibly': 1.6,
            'so': 1.3, 'highly': 1.4, 'truly': 1.4, 'particularly': 1.3
        }
        
        self.diminishers = {
            'somewhat': 0.7, 'slightly': 0.6, 'barely': 0.5, 'hardly': 0.4,
            'kind of': 0.6, 'sort of': 0.6, 'a bit': 0.7, 'a little': 0.7
        }
    
    @property#懒加载
    def transformer(self):
        """懒加载 Transformer"""
        if self._transformer is None and self.use_transformer:
            try:
                from transformers import pipeline
                self._transformer = pipeline(
                    "sentiment-analysis",
                    model="distilbert-base-uncased-finetuned-sst-2-english",
                    device=-1,  # CPU
                    truncation=True,
                    max_length=512
                )
                logger.info("✓ Transformer 模型加载成功")
            except Exception as e:
                logger.warning(f"Transformer 加载失败: {e}")
                self._transformer = False
        return self._transformer
    
    def _analyze_transformer(self, text: str) -> Optional[SentimentResult]:
        """Transformer 分析"""
        if not self.transformer:
            return None
        
        try:
            result = self.transformer(text[:512])[0]
            is_positive = result['label'] == 'POSITIVE'
            return SentimentResult(
                label=SentimentLabel.POSITIVE if is_positive else SentimentLabel.NEGATIVE,
                score=result['score'] if is_positive else 1 - result['score'],
                confidence=result['score'],
                method='transformer'
            )
        except Exception as e:
            logger.warning(f"Transformer 分析失败: {e}")
            return None
    
    def _analyze_vader(self, text: str) -> SentimentResult:
        """VADER 分析"""
        scores = self.vader.polarity_scores(text)
        compound = scores['compound']
        
        if compound >= 0.05:
            label = SentimentLabel.POSITIVE
        elif compound <= -0.05:
            label = SentimentLabel.NEGATIVE
        else:
            label = SentimentLabel.NEUTRAL
        
        return SentimentResult(
            label=label,
            score=(compound + 1) / 2,
            confidence=abs(compound),
            method='vader',
            details=scores
        )
    
    def _analyze_lexicon(self, text: str) -> SentimentResult:
        """词典分析"""
        tokens = self.preprocessor.tokenize(text, remove_stopwords=False, lemmatize=False)
        
        total_score = 0.0
        word_count = 0
        
        for i, token in enumerate(tokens):
            # 检查修饰词
            modifier = 1.0
            if i > 0:
                prev = tokens[i-1]
                modifier = self.intensifiers.get(prev, self.diminishers.get(prev, 1.0))
            
            # 检查否定
            negated = any(neg in tokens[max(0, i-3):i] for neg in self.preprocessor.negation_words)
            
            # 计算分数
            if token in self.positive_words:
                score = self.positive_words[token] * modifier
                total_score += -score if negated else score
                word_count += 1
            elif token in self.negative_words:
                score = self.negative_words[token] * modifier
                total_score += -score if negated else score
                word_count += 1
        
        if word_count == 0:
            return SentimentResult(
                label=SentimentLabel.NEUTRAL,
                score=0.5,
                confidence=0.0,
                method='lexicon'
            )
        
        avg_score = total_score / word_count
        normalized = (avg_score + 2) / 4  # 归一化到 0-1
        normalized = max(0, min(1, normalized))
        
        if normalized > 0.55:
            label = SentimentLabel.POSITIVE
        elif normalized < 0.45:
            label = SentimentLabel.NEGATIVE
        else:
            label = SentimentLabel.NEUTRAL
        
        return SentimentResult(
            label=label,
            score=normalized,
            confidence=abs(normalized - 0.5) * 2,
            method='lexicon',
            details={'word_count': word_count, 'raw_score': total_score}
        )
    
    def analyze(self, text: str, method: str = 'ensemble') -> SentimentResult:
        """
        分析情感
        
        method: 'transformer', 'vader', 'lexicon', 'ensemble'
        """
        if not text or len(text.strip()) < 10:
            return SentimentResult(
                label=SentimentLabel.NEUTRAL,
                score=0.5,
                confidence=0.0,
                method='default'
            )
        
        if method == 'transformer':
            result = self._analyze_transformer(text)
            return result if result else self._analyze_vader(text)
        elif method == 'vader':
            return self._analyze_vader(text)
        elif method == 'lexicon':
            return self._analyze_lexicon(text)
        else:  # ensemble
            return self._analyze_ensemble(text)
    
    def _analyze_ensemble(self, text: str) -> SentimentResult:
        """集成分析 - 加权投票"""
        results = []
        weights = []
        
        # Transformer 
        trans = self._analyze_transformer(text)
        if trans:
            results.append(trans)
            weights.append(0.5)
        
        # VADER
        vader = self._analyze_vader(text)
        results.append(vader)
        weights.append(0.3 if trans else 0.5)
        
        # Lexicon
        lexicon = self._analyze_lexicon(text)
        results.append(lexicon)
        weights.append(0.2 if trans else 0.5)
        
        # 加权投票
        label_scores = defaultdict(float)
        for r, w in zip(results, weights):
            label_scores[r.label] += w * r.confidence
        
        final_label = max(label_scores, key=label_scores.get)
        final_confidence = label_scores[final_label] / sum(weights)
        
        # 加权平均分数
        avg_score = sum(r.score * w for r, w in zip(results, weights)) / sum(weights)
        
        return SentimentResult(
            label=final_label,
            score=avg_score,
            confidence=final_confidence,
            method='ensemble',
            details={
                'transformer': trans.label.value if trans else None,
                'vader': vader.label.value,
                'lexicon': lexicon.label.value,
                'weights': weights
            }
        )
    
    def batch_analyze(self, texts: List[str], method: str = 'ensemble',
                     show_progress: bool = True) -> List[SentimentResult]:
        """批量分析"""
        from tqdm import tqdm
        iterator = tqdm(texts, desc="情感分析") if show_progress else texts
        return [self.analyze(text, method) for text in iterator]


class AspectBasedAnalyzer:
    """
    方面级情感分析 (ABSA)
    
    电影评论方面:#图谱
    - acting (演技)
    - plot (剧情)  
    - direction (导演)
    - cinematography (摄影)
    - soundtrack (配乐)
    - dialogue (对白)
    - pacing (节奏)
    - ending (结局)
    - effects (特效)
    - characters (角色)
    """
    
    ASPECTS = {
        'acting': {
            'cn': '演技',
            'keywords': ['acting', 'actor', 'actress', 'performance', 'perform', 
                        'cast', 'role', 'portray', 'played', 'star'],
            'weight': 1.0
        },
        'plot': {
            'cn': '剧情',
            'keywords': ['plot', 'story', 'storyline', 'narrative', 'twist',
                        'premise', 'tale', 'script', 'writing', 'written'],
            'weight': 1.0
        },
        'direction': {
            'cn': '导演',
            'keywords': ['director', 'direction', 'directing', 'directed',
                        'filmmaker', 'vision', 'helm', 'nolan', 'spielberg'],
            'weight': 0.9
        },
        'cinematography': {
            'cn': '摄影',
            'keywords': ['cinematography', 'camera', 'visual', 'shot', 'shots',
                        'photography', 'frame', 'framing', 'lens', 'lighting'],
            'weight': 0.8
        },
        'soundtrack': {
            'cn': '配乐',
            'keywords': ['music', 'soundtrack', 'score', 'sound', 'audio',
                        'song', 'composer', 'hans zimmer', 'theme', 'musical'],
            'weight': 0.9
        },
        'dialogue': {
            'cn': '对白',
            'keywords': ['dialogue', 'dialog', 'line', 'lines', 'conversation',
                        'speech', 'talking', 'quote', 'memorable'],
            'weight': 0.7
        },
        'pacing': {
            'cn': '节奏',
            'keywords': ['pace', 'pacing', 'slow', 'fast', 'runtime', 'length',
                        'drag', 'dragged', 'tempo', 'speed', 'boring', 'long'],
            'weight': 0.8
        },
        'ending': {
            'cn': '结局',
            'keywords': ['ending', 'end', 'conclusion', 'finale', 'climax',
                        'resolution', 'final', 'last', 'finish'],
            'weight': 0.9
        },
        'effects': {
            'cn': '特效',
            'keywords': ['effects', 'cgi', 'vfx', 'special effects', 'animation',
                        'action', 'stunts', 'practical', 'visual effects'],
            'weight': 0.8
        },
        'characters': {
            'cn': '角色',
            'keywords': ['character', 'characters', 'protagonist', 'antagonist',
                        'villain', 'hero', 'development', 'arc', 'depth'],
            'weight': 0.9
        }
    }
    
    def __init__(self):
        self.preprocessor = TextPreprocessor()
        self.sentiment_analyzer = MultiModelSentimentAnalyzer(use_transformer=False)
    #每一个都跑bret会死人
    def analyze(self, text: str) -> List[AspectSentiment]:
        """分析单条评论的方面情感"""
        if not text:
            return []
        #拆
        sentences = self.preprocessor.extract_sentences(text)
        aspect_data = defaultdict(lambda: {'sentences': [], 'sentiments': []})
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            #遍历所有方面
            for aspect_key, aspect_info in self.ASPECTS.items():
                matched = [kw for kw in aspect_info['keywords'] if kw in sentence_lower]
                #开始匹配环节！
                if matched:
                    sentiment = self.sentiment_analyzer.analyze(sentence, method='lexicon')
                    aspect_data[aspect_key]['sentences'].append(sentence)
                    aspect_data[aspect_key]['sentiments'].append(sentiment)
        
        results = []
        for aspect_key, data in aspect_data.items():
            if not data['sentiments']:
                continue
            
            # 多数投票决定情感
            labels = [s.label for s in data['sentiments']]
            label_counts = Counter(labels)
            dominant = label_counts.most_common(1)[0][0]
            
            avg_confidence = np.mean([s.confidence for s in data['sentiments']])
            
            results.append(AspectSentiment(
                aspect=aspect_key,
                aspect_cn=self.ASPECTS[aspect_key]['cn'],
                sentiment=dominant,
                confidence=avg_confidence,
                mentions=len(data['sentiments']),
                evidence=data['sentences'][:3]
            ))
        
        return results
    
    def aggregate(self, all_aspects: List[List[AspectSentiment]]) -> Dict[str, Dict]:
        """聚合所有评论的方面分析"""
        stats = defaultdict(lambda: {
            'positive': 0, 'negative': 0, 'neutral': 0,
            'total': 0, 'confidences': []
        })
        
        for review_aspects in all_aspects:
            for asp in review_aspects:
                key = asp.aspect
                stats[key][asp.sentiment.value] += 1
                stats[key]['total'] += 1
                stats[key]['confidences'].append(asp.confidence)
        
        result = {}
        for aspect, data in stats.items():
            total = data['total']
            if total == 0:
                continue
            
            result[aspect] = {
                'aspect_cn': self.ASPECTS[aspect]['cn'],
                'total_mentions': total,
                'positive_ratio': data['positive'] / total,
                'negative_ratio': data['negative'] / total,
                'neutral_ratio': data['neutral'] / total,
                'sentiment_score': (data['positive'] - data['negative']) / total,
                'avg_confidence': np.mean(data['confidences'])
            }
        
        return result


class TopicModeler:
    """
    主题建模器
    
    我使用的方法是: NMF 
    特点: 比 LDA 更适合短文本，主题更可解释
    """
    
    def __init__(self, n_topics: int = 8):
        self.n_topics = n_topics
        self.preprocessor = TextPreprocessor()
        self.vectorizer = None
        self.model = None
        self.feature_names = None
        
        # 主题标签映射 (基于关键词自动推断)
        self.topic_label_rules = {
            ('plot', 'story', 'twist'): '剧情转折',
            ('acting', 'actor', 'performance'): '演员演技',
            ('visual', 'effect', 'cgi'): '视觉特效',
            ('music', 'score', 'soundtrack'): '背景音乐',
            ('director', 'nolan', 'vision'): '导演风格',
            ('pace', 'slow', 'boring'): '节奏控制',
            ('character', 'development', 'depth'): '角色塑造',
            ('ending', 'end', 'conclusion'): '结局',
            ('dialogue', 'line', 'script'): '对白剧本',
            ('emotion', 'feel', 'heart'): '情感共鸣'
        }
    
    def fit(self, documents: List[str]) -> bool:
        """训练主题模型"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import NMF
        
        # 预处理
        processed = []
        for doc in documents:
            if doc and isinstance(doc, str) and len(doc) > 20:
                tokens = self.preprocessor.tokenize(self.preprocessor.clean(doc))
                if tokens:
                    processed.append(' '.join(tokens))
        
        if len(processed) < self.n_topics * 2:
            logger.warning(f"文档数量不足: {len(processed)}")
            return False
        
        try:
            # TF-IDF 向量化
            self.vectorizer = TfidfVectorizer(
                max_features=2000,
                min_df=3,
                max_df=0.85,
                ngram_range=(1, 2)
            )
            tfidf_matrix = self.vectorizer.fit_transform(processed)
            self.feature_names = self.vectorizer.get_feature_names_out()
            
            # NMF 分解
            actual_n = min(self.n_topics, len(processed) - 1, tfidf_matrix.shape[1] - 1)
            self.model = NMF(
                n_components=actual_n,
                random_state=42,# 固定随机种子！可以保证每次演示结果一样！
                max_iter=200,
                init='nndsvd'# 专门优化的初始化方法
            )
            self.doc_topics = self.model.fit_transform(tfidf_matrix)
            
            logger.info(f"✓ 主题模型训练完成: {actual_n} 个主题")
            return True
            
        except Exception as e:
            logger.error(f"主题建模失败: {e}")
            return False
    
    def _generate_label(self, keywords: List[str]) -> str:
        """根据关键词生成主题标签"""#启发式#语义映射
        keywords_set = set(kw.lower() for kw in keywords[:5])
        
        best_match = None
        best_score = 0
        
        for rule_keywords, label in self.topic_label_rules.items():
            score = len(keywords_set & set(rule_keywords))
            if score > best_score:
                best_score = score
                best_match = label
        
        if best_match:
            return best_match
        return ', '.join(keywords[:3])
    
    def get_topics(self, n_words: int = 10) -> List[TopicInfo]:
        """获取主题信息"""
        if self.model is None:
            return []
        
        topics = []
        for idx, topic_weights in enumerate(self.model.components_):
            top_indices = topic_weights.argsort()[:-n_words-1:-1]
            keywords = [self.feature_names[i] for i in top_indices]
            weights = [float(topic_weights[i]) for i in top_indices]
            
            # 计算该主题的文档数
            topic_docs = (self.doc_topics[:, idx] > 0.1).sum()
            # 下一步：封装成 TopicInfo 对象返回！
            topics.append(TopicInfo(
                topic_id=idx,
                keywords=keywords,
                keyword_weights=weights,
                num_docs=int(topic_docs),
                label=self._generate_label(keywords)
            ))
        
        # 按文档数排序
        topics.sort(key=lambda x: x.num_docs, reverse=True)
        return topics
    
    def get_document_topics(self) -> np.ndarray:
        """获取文档-主题分布"""
        return self.doc_topics if hasattr(self, 'doc_topics') else None


class ReviewQualityScorer:
    """评论质量评分器"""
    
    def __init__(self):
        self.preprocessor = TextPreprocessor()
    
    def score(self, text: str) -> Dict:
        """评估评论质量 (0-1)"""
        if not text or len(text) < 20:
            return {'overall': 0.0, 'details': {}}
        
        scores = {}
        
        # 1. 长度分数 (100-800 字符最佳)
        length = len(text)
        if length < 50:
            scores['length'] = length / 50
        elif length <= 800:
            scores['length'] = 1.0
        else:
            scores['length'] = max(0.5, 1.0 - (length - 800) / 2000)
        
        # 2. 词汇多样性
        tokens = self.preprocessor.tokenize(text, remove_stopwords=True)
        if tokens:
            unique_ratio = len(set(tokens)) / len(tokens)
            scores['diversity'] = min(unique_ratio * 1.3, 1.0)
        else:
            scores['diversity'] = 0.0
        
        # 3. 句子结构
        sentences = self.preprocessor.extract_sentences(text)
        if sentences:
            avg_len = np.mean([len(s.split()) for s in sentences])
            if 8 <= avg_len <= 25:
                scores['structure'] = 1.0
            elif avg_len < 8:
                scores['structure'] = avg_len / 8
            else:
                scores['structure'] = max(0.3, 1 - (avg_len - 25) / 30)
        else:
            scores['structure'] = 0.3
        
        # 4. 有实质内容 (不只是感叹词)
        content_words = [t for t in tokens if len(t) > 3]
        scores['substance'] = min(len(content_words) / 10, 1.0)
        
        # 综合评分
        weights = {'length': 0.2, 'diversity': 0.3, 'structure': 0.2, 'substance': 0.3}
        overall = sum(scores[k] * weights[k] for k in weights)
        
        return {'overall': round(overall, 3), 'details': scores}


class NLPPipeline:
    """
    NLP 分析流水线
    整合所有分析功能
    """
    
    def __init__(self, use_transformer: bool = True, n_topics: int = 8):
        logger.info("初始化 NLP Pipeline...")
        self.preprocessor = TextPreprocessor()
        self.sentiment_analyzer = MultiModelSentimentAnalyzer(use_transformer=use_transformer)
        self.aspect_analyzer = AspectBasedAnalyzer()
        self.topic_modeler = TopicModeler(n_topics=n_topics)
        self.quality_scorer = ReviewQualityScorer()
        logger.info("✓ NLP Pipeline 初始化完成")
    
    def analyze_review(self, text: str, review_id: str = "") -> ReviewAnalysis:
        """分析单条评论"""
        sentiment = self.sentiment_analyzer.analyze(text)
        aspects = self.aspect_analyzer.analyze(text)
        quality = self.quality_scorer.score(text)
        
        return ReviewAnalysis(
            review_id=review_id,
            sentiment=sentiment,
            aspects=aspects,
            quality_score=quality['overall'],
            topics=[],
            entities=[],
            word_count=len(text.split())
        )
    
    def process_dataframe(self, df: pd.DataFrame, text_column: str = 'content',
                         id_column: str = 'review_id',
                         run_topics: bool = True) -> pd.DataFrame:
        """处理 DataFrame"""
        from tqdm import tqdm
        
        df = df.copy()
        texts = df[text_column].fillna('').tolist()
        ids = df[id_column].tolist() if id_column in df.columns else range(len(df))
        
        # 情感分析
        logger.info("执行情感分析...")
        sentiments = self.sentiment_analyzer.batch_analyze(texts)
        df['sentiment_label'] = [s.label.value for s in sentiments]
        df['sentiment_score'] = [s.score for s in sentiments]
        df['sentiment_confidence'] = [s.confidence for s in sentiments]
        
        # 方面分析
        logger.info("执行方面分析...")
        aspects_list = []
        for text in tqdm(texts, desc="ABSA"):
            aspects_list.append(self.aspect_analyzer.analyze(text))
        df['aspects'] = aspects_list
        
        # 质量评分
        logger.info("执行质量评分...")
        qualities = [self.quality_scorer.score(t) for t in tqdm(texts, desc="质量评分")]
        df['quality_score'] = [q['overall'] for q in qualities]
        
        # 主题建模
        if run_topics:
            logger.info("执行主题建模...")
            if self.topic_modeler.fit(texts):
                doc_topics = self.topic_modeler.get_document_topics()
                if doc_topics is not None and len(doc_topics) == len(df):
                    df['topic_id'] = doc_topics.argmax(axis=1)
                    df['topic_confidence'] = doc_topics.max(axis=1)
        
        return df
    
    def get_summary(self, df: pd.DataFrame) -> Dict:
        """生成分析摘要"""
        summary = {
            'total_reviews': len(df),
            'sentiment_distribution': df['sentiment_label'].value_counts().to_dict(),
            'positive_ratio': (df['sentiment_label'] == 'positive').mean(),
            'avg_sentiment_score': df['sentiment_score'].mean(),
            'avg_quality_score': df['quality_score'].mean(),
        }
        
        # 方面统计
        if 'aspects' in df.columns:
            summary['aspect_summary'] = self.aspect_analyzer.aggregate(df['aspects'].tolist())
        
        # 主题统计
        if self.topic_modeler.model is not None:
            summary['topics'] = [
                {'id': t.topic_id, 'label': t.label, 
                 'keywords': t.keywords[:5], 'num_docs': t.num_docs}
                for t in self.topic_modeler.get_topics()
            ]
        
        return summary
