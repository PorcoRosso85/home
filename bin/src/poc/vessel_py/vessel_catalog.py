#!/usr/bin/env python3
"""
Vessel カタログシステム
使える器を体系的に管理・検索
"""
import os
import json
import ast
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from vessel_log import logger

@dataclass
class VesselMetadata:
    """器のメタデータ"""
    name: str
    path: str
    language: str  # python, bun, etc.
    category: str  # data, test, transform, etc.
    tags: List[str]
    description: str
    input_format: str
    output_format: str
    examples: List[Dict[str, str]]
    tested: bool = False
    quality_score: float = 0.0

class VesselCatalog:
    """器のカタログ管理"""
    
    def __init__(self, catalog_path: str = "vessel_catalog.json"):
        self.catalog_path = catalog_path
        self.vessels: Dict[str, VesselMetadata] = {}
        self.load_catalog()
    
    def load_catalog(self):
        """カタログを読み込み"""
        if os.path.exists(self.catalog_path):
            with open(self.catalog_path, 'r') as f:
                data = json.load(f)
                for name, vessel_data in data.items():
                    self.vessels[name] = VesselMetadata(**vessel_data)
    
    def save_catalog(self):
        """カタログを保存"""
        data = {name: asdict(vessel) for name, vessel in self.vessels.items()}
        with open(self.catalog_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_vessel(self, vessel: VesselMetadata):
        """新しい器を登録"""
        self.vessels[vessel.name] = vessel
        self.save_catalog()
    
    def search_by_tag(self, tag: str) -> List[VesselMetadata]:
        """タグで器を検索"""
        return [v for v in self.vessels.values() if tag in v.tags]
    
    def search_by_category(self, category: str) -> List[VesselMetadata]:
        """カテゴリで器を検索"""
        return [v for v in self.vessels.values() if v.category == category]
    
    def get_pipeline_suggestion(self, input_format: str, output_format: str) -> List[List[str]]:
        """入出力形式から器のパイプライン候補を提案"""
        suggestions = []
        
        # 単純な実装：直接変換できる器を探す
        for vessel in self.vessels.values():
            if vessel.input_format == input_format and vessel.output_format == output_format:
                suggestions.append([vessel.name])
        
        return suggestions

# 器の自動登録スクリプト
def auto_register_vessel(file_path: str, catalog: VesselCatalog):
    """ファイルから器のメタデータを抽出して登録"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # docstringからメタデータを抽出
    tree = ast.parse(content)
    docstring = ast.get_docstring(tree)
    
    if docstring and "@vessel" in docstring:
        # docstringからメタデータをパース
        lines = docstring.split('\n')
        metadata = {}
        
        for line in lines:
            if line.strip().startswith('@'):
                key, value = line.strip()[1:].split(':', 1)
                metadata[key.strip()] = value.strip()
        
        # VesselMetadataを作成
        vessel = VesselMetadata(
            name=os.path.basename(file_path).replace('.py', '').replace('.ts', ''),
            path=file_path,
            language='python' if file_path.endswith('.py') else 'typescript',
            category=metadata.get('category', 'general'),
            tags=metadata.get('tags', '').split(','),
            description=metadata.get('description', ''),
            input_format=metadata.get('input', 'text'),
            output_format=metadata.get('output', 'text'),
            examples=[]
        )
        
        catalog.register_vessel(vessel)

# 使用例
if __name__ == "__main__":
    catalog = VesselCatalog()
    
    # 手動登録の例
    vessel = VesselMetadata(
        name="vessel",
        path="vessel.py",
        language="python",
        category="core",
        tags=["basic", "exec", "dynamic"],
        description="基本的な動的スクリプト実行器",
        input_format="python_script",
        output_format="stdout",
        examples=[{
            "input": "print('Hello')",
            "output": "Hello"
        }]
    )
    
    catalog.register_vessel(vessel)
    
    # 検索例
    logger.info("Tag 'basic'で検索:", search_tag="basic")
    for v in catalog.search_by_tag('basic'):
        logger.info(f"検索結果: {v.name}", vessel_name=v.name, description=v.description)