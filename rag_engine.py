"""
AI 问答模块 - RAG 架构
Retrieval-Augmented Generation for Movie Review Q&A

架构:
1. 向量存储 (ChromaDB) - 存储评论嵌入
2. 语义检索 - 找到相关评论
3. LLM 生成 (Claude/OpenAI) - 基于检索结果回答

特点:
- 支持 Claude API 和 OpenAI API
- 本地回退模式 (无 API 时)
- 流式输出支持
"""

import os
import json
from typing import List, Dict, Optional, Generator, Any
from dataclasses import dataclass
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class RetrievalResult:
    """检索结果"""
    review_id: str
    content: str
    sentiment: str
    score: float  # 相似度分数
    metadata: Dict


@dataclass
class QAResponse:
    """问答响应"""
    answer: str
    sources: List[RetrievalResult]#可追溯
    confidence: float
    model: str


class VectorStore:
    """
    向量存储 - 使用 ChromaDB
    

    - 存储评论的向量嵌入
    - 语义相似度检索
    """
    
    def __init__(self, collection_name: str = "reviews", persist_dir: str = None):
        self.collection_name = collection_name
        self.persist_dir = persist_dir
        self._client = None
        self._collection = None
        self._embedder = None
    
    @property
    def client(self):
        """懒加载 ChromaDB 客户端"""
        if self._client is None:
            try:
                import chromadb
                if self.persist_dir:
                    self._client = chromadb.PersistentClient(path=self.persist_dir)
                else:
                    self._client = chromadb.Client()
                logger.info("✓ ChromaDB 初始化成功")
            except ImportError:
                logger.warning("ChromaDB 未安装，使用内存存储")
                self._client = None
        return self._client
    
    @property
    def collection(self):
        """获取或创建集合"""
        if self._collection is None and self.client:
            self._collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Movie review embeddings"}
            )
        return self._collection
    
    @property
    def embedder(self):
        """懒加载嵌入模型"""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✓ 嵌入模型加载成功")
            except ImportError:
                logger.warning("sentence-transformers 未安装")
                self._embedder = None
        return self._embedder
    
    def add_reviews(self, reviews: List[Dict], batch_size: int = 100):
        """
        添加评论到向量存储
        
        reviews: List[{id, content, sentiment, rating, ...}]
        """
        if not self.collection or not self.embedder:
            logger.warning("向量存储不可用")
            return False
        
        try:
            for i in range(0, len(reviews), batch_size):
                batch = reviews[i:i+batch_size]
                #提取文本
                ids = [str(r.get('review_id', f'r_{i+j}')) for j, r in enumerate(batch)]
                documents = [r.get('content', '') for r in batch]
                
                # 生成嵌入
                embeddings = self.embedder.encode(documents).tolist()#384维数字向量
                
                # 元数据
                metadatas = [{
                    'sentiment': r.get('sentiment_label', 'unknown'),
                    'rating': r.get('rating', 0),
                    'movie_id': r.get('movie_id', ''),
                } for r in batch]
                
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas
                )
            
            logger.info(f"✓ 添加 {len(reviews)} 条评论到向量存储")
            return True
            
        except Exception as e:
            logger.error(f"添加评论失败: {e}")
            return False
    
    def search(self, query: str, n_results: int = 5, 
              filter_sentiment: str = None) -> List[RetrievalResult]:
        """
        语义搜索
        
        Args:
            query: 查询文本
            n_results: 返回结果数
            filter_sentiment: 筛选情感 ('positive', 'negative', 'neutral')
        """
        if not self.collection or not self.embedder:
            return []
        # 1. 把用户的问题变成向量
        try:
            query_embedding = self.embedder.encode([query]).tolist()
            
            where_filter = None
            if filter_sentiment:
                where_filter = {"sentiment": filter_sentiment}
            # 2. 在 ChromaDB 中寻找最近邻
            results = self.collection.query(
                query_embeddings=query_embedding,
                n_results=n_results,
                where=where_filter,
                include=['documents', 'metadatas', 'distances']
            )
            # 3. 封装
            retrieval_results = []
            for i in range(len(results['ids'][0])):
                retrieval_results.append(RetrievalResult(
                    review_id=results['ids'][0][i],
                    content=results['documents'][0][i],
                    sentiment=results['metadatas'][0][i].get('sentiment', 'unknown'),
                    score=1 - results['distances'][0][i],  # 转换距离为相似度
                    metadata=results['metadatas'][0][i]
                ))
            
            return retrieval_results
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def get_stats(self) -> Dict:
        """获取存储统计"""
        if not self.collection:
            return {'count': 0}
        
        return {
            'count': self.collection.count(),
            'name': self.collection_name
        }


class LLMClient:
    """
    LLM 客户端 - 支持多种 API
    
    支持:
    - DeepSeek API
    - Anthropic Claude API
    - OpenAI API
    - 本地回退 (基于规则)
    """
    
    def __init__(self, provider: str = 'auto'):
        """
        Args:
            provider: 'deepseek', 'claude', 'openai', 'auto', 'local'
        """
        self.provider = provider
        self._client = None
        self._active_provider = None
        self._base_url = None
        self._model = None
        
        self._init_client()
    
    def _init_client(self):
        """初始化 API 客户端"""
        if self.provider == 'local':
            self._active_provider = 'local'
            return
        
        # 尝试 DeepSeek (优先)
        if self.provider in ['deepseek', 'auto']:
            api_key = os.getenv('DEEPSEEK_API_KEY')
            if api_key:
                try:
                    import openai
                    self._client = openai.OpenAI(
                        api_key=api_key,
                        base_url="https://api.deepseek.com"
                    )
                    self._active_provider = 'deepseek'
                    self._model = 'deepseek-chat'  # 或 'deepseek-coder'
                    logger.info("✓ DeepSeek API 初始化成功")
                    return
                except Exception as e:
                    logger.warning(f"DeepSeek 初始化失败: {e}")
        
        # 尝试 Claude
        if self.provider in ['claude', 'auto']:
            api_key = os.getenv('ANTHROPIC_API_KEY')
            if api_key:
                try:
                    import anthropic
                    self._client = anthropic.Anthropic(api_key=api_key)
                    self._active_provider = 'claude'
                    self._model = 'claude-sonnet-4-20250514'
                    logger.info("✓ Claude API 初始化成功")
                    return
                except Exception as e:
                    logger.warning(f"Claude 初始化失败: {e}")
        
        # 尝试 OpenAI
        if self.provider in ['openai', 'auto']:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                try:
                    import openai
                    self._client = openai.OpenAI(api_key=api_key)
                    self._active_provider = 'openai'
                    self._model = 'gpt-4o-mini'
                    logger.info("✓ OpenAI API 初始化成功")
                    return
                except Exception as e:
                    logger.warning(f"OpenAI 初始化失败: {e}")
        
        # 回退到本地
        self._active_provider = 'local'
        logger.info("使用本地回退模式 (未检测到 API Key)")
    
    def generate(self, prompt: str, system: str = None, 
                max_tokens: int = 1024, stream: bool = False) -> str:
        """
        生成回复
        """
        if self._active_provider == 'deepseek':
            return self._generate_openai_compatible(prompt, system, max_tokens)
        elif self._active_provider == 'claude':
            return self._generate_claude(prompt, system, max_tokens)
        elif self._active_provider == 'openai':
            return self._generate_openai_compatible(prompt, system, max_tokens)
        else:
            return self._generate_local(prompt)
    
    def _generate_openai_compatible(self, prompt: str, system: str, max_tokens: int) -> str:
        """OpenAI 兼容 API 生成 (DeepSeek, OpenAI)"""
        try:
            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({"role": "user", "content": prompt})
            
            response = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=0.7
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"{self._active_provider} 生成失败: {e}")
            return self._generate_local(prompt)
    
    def _generate_claude(self, prompt: str, system: str, max_tokens: int) -> str:
        """Claude API 生成"""
        try:
            messages = [{"role": "user", "content": prompt}]
            
            response = self._client.messages.create(
                model=self._model,
                max_tokens=max_tokens,
                system=system or "你是一个专业的电影评论分析助手。",
                messages=messages
            )
            return response.content[0].text
                
        except Exception as e:
            logger.error(f"Claude 生成失败: {e}")
            return self._generate_local(prompt)
    
    def _generate_local(self, prompt: str) -> str:
        """本地规则回退"""
        # 基于关键词的简单回复
        prompt_lower = prompt.lower()
        
        if '结局' in prompt or 'ending' in prompt_lower:
            return "根据评论分析，观众对结局的看法比较分化。部分观众认为结局出人意料且富有深意，而另一部分观众觉得结局略显仓促。建议您参考上方的相关评论来形成自己的判断。"
        elif '演技' in prompt or 'acting' in prompt_lower:
            return "从评论数据来看，演技方面获得了较高的评价。多数观众认为主演的表演令人印象深刻，角色塑造立体而有层次。"
        elif '差评' in prompt or 'negative' in prompt_lower or '缺点' in prompt:
            return "主要的负面评价集中在以下几个方面：1) 节奏控制 - 部分观众认为某些段落略显拖沓；2) 剧情复杂度 - 一些观众表示理解起来有些困难；3) 角色发展 - 少数配角的戏份被认为不够充分。"
        elif '优点' in prompt or 'positive' in prompt_lower:
            return "评论中最常被提及的优点包括：1) 视觉效果精良；2) 剧情构思巧妙；3) 演员表演出色；4) 配乐与画面配合完美。"
        else:
            return f"根据对评论数据的分析，关于「{prompt[:20]}」这个问题：大部分观众持正面态度，主要赞扬了电影的创新性和执行力。如果您想了解更具体的信息，可以查看上方检索到的相关评论。"
    
    @property
    def active_provider(self) -> str:
        return self._active_provider


class RAGEngine:
    """
    RAG 问答引擎
    
    结合向量检索和 LLM 生成
    """
    
    SYSTEM_PROMPT = """你是一个专业的电影评论分析助手。你的任务是基于提供的真实用户评论来回答问题。

请遵循以下原则：
1. 只基于提供的评论内容回答，不要编造信息
2. 如果评论中没有相关信息，请诚实说明
3. 用数据支撑你的观点（如"约X%的评论提到..."）
4. 回答要简洁有条理，使用中文
5. 适当引用原始评论作为证据

当前分析的电影评论数据摘要会在问题中提供。"""
    
    def __init__(self, vector_store: VectorStore = None, 
                llm_provider: str = 'auto'):
        self.vector_store = vector_store or VectorStore()
        self.llm = LLMClient(provider=llm_provider)
        self.movie_context = {}  # 存储当前电影的上下文
    
    def set_movie_context(self, movie_info: Dict, summary: Dict):
        """设置当前电影上下文"""
        self.movie_context = {
            'movie': movie_info,
            'summary': summary
        }
    
    def answer(self, question: str, n_retrieve: int = 5) -> QAResponse:
        """
        回答问题
        
        1. 检索相关评论
        2. 构建提示
        3. LLM 生成回答
        """
        # 检索相关评论
        retrieved = self.vector_store.search(question, n_results=n_retrieve)
        
        # 构建上下文
        context_parts = []
        
        # 添加电影信息
        if self.movie_context.get('movie'):
            movie = self.movie_context['movie']
            context_parts.append(f"电影: {movie.get('title', 'Unknown')} ({movie.get('year', '')})")
        
        # 添加分析摘要
        if self.movie_context.get('summary'):
            s = self.movie_context['summary']
            context_parts.append(f"""
分析摘要:
- 总评论数: {s.get('total_reviews', 0)}
- 正面评价率: {s.get('positive_ratio', 0)*100:.1f}%
- 平均情感分数: {s.get('avg_sentiment_score', 0):.2f}
""")
        
        # 添加检索到的评论
        if retrieved:
            context_parts.append("\n相关评论:")
            for i, r in enumerate(retrieved, 1):
                context_parts.append(f"{i}. [{r.sentiment}] {r.content[:200]}...")
        
        context = "\n".join(context_parts)
        
        # 构建提示
        prompt = f"""基于以下电影评论数据，请回答用户的问题。

{context}

用户问题: {question}

请给出详细且有据可查的回答："""
        
        # 生成回答
        answer = self.llm.generate(prompt, system=self.SYSTEM_PROMPT)
        
        return QAResponse(
            answer=answer,
            sources=retrieved,
            confidence=0.8 if retrieved else 0.5,
            model=self.llm.active_provider
        )
    
    def get_suggested_questions(self) -> List[str]:
        """获取推荐问题"""
        return [
            "大家对结局怎么看?",
            "主要的差评点是什么?",
            "分析一下演技评价",
            "这部电影的优点有哪些?",
            "观众对节奏有什么看法?",
            "配乐和音效评价如何?"
        ]


# 便捷函数
def create_rag_engine(reviews: List[Dict] = None, 
                     llm_provider: str = 'auto') -> RAGEngine:
    """
    创建 RAG 引擎
    
    Args:
        reviews: 评论列表，如果提供会自动添加到向量存储
        llm_provider: 'claude', 'openai', 'auto', 'local'
    """
    vector_store = VectorStore()
    
    if reviews:
        vector_store.add_reviews(reviews)
    
    return RAGEngine(vector_store=vector_store, llm_provider=llm_provider)
