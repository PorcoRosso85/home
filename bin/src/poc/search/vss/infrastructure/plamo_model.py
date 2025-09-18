"""PLaMo-Embedding-1B 埋め込みモデルの実装（将来使用のためコメント化）"""

# from typing import List
# from transformers import AutoModel, AutoTokenizer
# import torch
# from ..domain.types import (
#     EmbeddingModel, 
#     EmbeddingRequest, 
#     EmbeddingResult, 
#     EmbeddingType
# )
# 
# 
# class PlamoEmbeddingModel:
#     """pfnet/plamo-embedding-1b の実装"""
#     
#     def __init__(self, model_name: str = "pfnet/plamo-embedding-1b"):
#         self._model_name = model_name
#         self._dimension = 1536  # PLaMo-Embedding-1Bの次元数
#         
#         self.tokenizer = AutoTokenizer.from_pretrained(
#             model_name, 
#             trust_remote_code=True
#         )
#         
#         # メモリ最適化オプション
#         self.model = AutoModel.from_pretrained(
#             model_name,
#             trust_remote_code=True,
#             torch_dtype=torch.float16,  # 半精度
#             low_cpu_mem_usage=True      # 低メモリ使用
#         )
#     
#     @property
#     def model_name(self) -> str:
#         return self._model_name
#     
#     @property
#     def dimension(self) -> int:
#         return self._dimension
#     
#     def encode(self, request: EmbeddingRequest) -> EmbeddingResult:
#         """単一テキストの埋め込み"""
#         if request.embedding_type == EmbeddingType.QUERY:
#             embeddings = self.model.encode_query(
#                 request.text, 
#                 self.tokenizer
#             )
#         else:
#             # PLaMoではdocument用メソッドはリストを受け取る
#             embeddings = self.model.encode_document(
#                 [request.text], 
#                 self.tokenizer
#             )[0]
#         
#         return EmbeddingResult(
#             embeddings=embeddings.tolist(),
#             model_name=self.model_name,
#             dimension=self.dimension
#         )
#     
#     def encode_batch(self, requests: List[EmbeddingRequest]) -> List[EmbeddingResult]:
#         """バッチ埋め込み"""
#         results = []
#         
#         # タイプ別にグループ化
#         query_requests = [r for r in requests if r.embedding_type == EmbeddingType.QUERY]
#         doc_requests = [r for r in requests if r.embedding_type != EmbeddingType.QUERY]
#         
#         # クエリの処理
#         for req in query_requests:
#             result = self.encode(req)
#             results.append(result)
#         
#         # ドキュメントの処理（バッチ処理可能）
#         if doc_requests:
#             texts = [req.text for req in doc_requests]
#             embeddings_list = self.model.encode_document(texts, self.tokenizer)
#             
#             for i, embeddings in enumerate(embeddings_list):
#                 results.append(EmbeddingResult(
#                     embeddings=embeddings.tolist(),
#                     model_name=self.model_name,
#                     dimension=self.dimension
#                 ))
#         
#         return results