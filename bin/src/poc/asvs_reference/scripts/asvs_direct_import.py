#!/usr/bin/env python3
"""
ASVS Direct Import - YAML無しでMarkdownから直接KuzuDBへインポート

設計方針:
1. YAML中間層を排除し、Markdown → CSV/DataFrame → KuzuDB
2. KuzuDBの高速COPY FROMを活用
3. エラーハンドリングを強化
"""
import re
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple
import kuzu


class ASVSDirectImporter:
    """ASVSデータを直接KuzuDBにインポート"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db = kuzu.Database(db_path)
        self.conn = kuzu.Connection(self.db)
    
    def create_schema(self):
        """KuzuDBスキーマを作成"""
        schema_queries = [
            # Nodeテーブル
            """CREATE NODE TABLE IF NOT EXISTS Standard(
                uri STRING PRIMARY KEY,
                name STRING,
                version STRING,
                description STRING,
                url STRING
            )""",
            
            """CREATE NODE TABLE IF NOT EXISTS Chapter(
                uri STRING PRIMARY KEY,
                number STRING,
                name STRING,
                standard_uri STRING
            )""",
            
            """CREATE NODE TABLE IF NOT EXISTS Section(
                uri STRING PRIMARY KEY,
                number STRING,
                name STRING,
                chapter_uri STRING
            )""",
            
            """CREATE NODE TABLE IF NOT EXISTS Requirement(
                uri STRING PRIMARY KEY,
                number STRING,
                description STRING,
                level1 BOOLEAN,
                level2 BOOLEAN,
                level3 BOOLEAN,
                section_uri STRING
            )""",
            
            # Relationshipテーブル
            """CREATE REL TABLE IF NOT EXISTS HAS_CHAPTER(
                FROM Standard TO Chapter
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS HAS_SECTION(
                FROM Chapter TO Section  
            )""",
            
            """CREATE REL TABLE IF NOT EXISTS HAS_REQUIREMENT(
                FROM Section TO Requirement
            )"""
        ]
        
        for query in schema_queries:
            self.conn.execute(query)
    
    def parse_markdown_to_dataframes(self, md_content: str, version: str = "5.0") -> Dict[str, pd.DataFrame]:
        """MarkdownをDataFrameに変換"""
        
        # 1. Standard DataFrame
        standards_df = pd.DataFrame([{
            'uri': f'asvs:{version}',
            'name': 'OWASP Application Security Verification Standard',
            'version': version,
            'description': 'The OWASP ASVS is a community-driven effort',
            'url': 'https://owasp.org/www-project-application-security-verification-standard/'
        }])
        
        # 2. Requirements parsing
        requirements = []
        pattern = r'\|\s*\*?\*?(\d+\.\d+\.\d+)\*?\*?\s*\|(.*?)\|\s*(\d+)\s*\|'
        
        for match in re.finditer(pattern, md_content):
            req_num = match.group(1).strip()
            description = match.group(2).strip()
            level = int(match.group(3).strip())
            
            # Extract chapter and section
            parts = req_num.split('.')
            chapter_num = f"V{parts[0]}"
            section_num = f"{parts[0]}.{parts[1]}"
            
            requirements.append({
                'uri': f'asvs:{version}:req:{req_num}',
                'number': req_num,
                'description': description,
                'level1': level >= 1,
                'level2': level >= 2,
                'level3': level >= 3,
                'section_uri': f'asvs:{version}:sec:{section_num}',
                'chapter_num': chapter_num,
                'section_num': section_num
            })
        
        requirements_df = pd.DataFrame(requirements)
        
        # 3. Extract unique chapters and sections
        chapters = requirements_df[['chapter_num']].drop_duplicates()
        chapters_df = pd.DataFrame([{
            'uri': f'asvs:{version}:ch:{ch}',
            'number': ch,
            'name': f'Chapter {ch}',
            'standard_uri': f'asvs:{version}'
        } for ch in chapters['chapter_num']])
        
        sections = requirements_df[['section_num', 'chapter_num']].drop_duplicates()
        sections_df = pd.DataFrame([{
            'uri': f'asvs:{version}:sec:{row.section_num}',
            'number': row.section_num,
            'name': f'Section {row.section_num}',
            'chapter_uri': f'asvs:{version}:ch:{row.chapter_num}'
        } for row in sections.itertuples()])
        
        # 4. Create relationship DataFrames
        has_chapter_df = pd.DataFrame([{
            'from': f'asvs:{version}',
            'to': uri
        } for uri in chapters_df['uri']])
        
        has_section_df = pd.DataFrame([{
            'from': row['chapter_uri'],
            'to': row['uri']
        } for _, row in sections_df.iterrows()])
        
        has_requirement_df = pd.DataFrame([{
            'from': row['section_uri'],
            'to': row['uri']
        } for _, row in requirements_df.iterrows()])
        
        # Clean requirements_df
        requirements_df = requirements_df.drop(['chapter_num', 'section_num'], axis=1)
        
        return {
            'standards': standards_df,
            'chapters': chapters_df,
            'sections': sections_df,
            'requirements': requirements_df,
            'has_chapter': has_chapter_df,
            'has_section': has_section_df,
            'has_requirement': has_requirement_df
        }
    
    def import_dataframes(self, dataframes: Dict[str, pd.DataFrame]):
        """DataFrameを直接KuzuDBにインポート"""
        
        # 1. Import nodes
        print("Importing nodes...")
        self.conn.execute("COPY Standard FROM df", {"df": dataframes['standards']})
        self.conn.execute("COPY Chapter FROM df", {"df": dataframes['chapters']})
        self.conn.execute("COPY Section FROM df", {"df": dataframes['sections']})
        self.conn.execute("COPY Requirement FROM df", {"df": dataframes['requirements']})
        
        # 2. Import relationships
        print("Importing relationships...")
        self.conn.execute("COPY HAS_CHAPTER FROM df", {"df": dataframes['has_chapter']})
        self.conn.execute("COPY HAS_SECTION FROM df", {"df": dataframes['has_section']})
        self.conn.execute("COPY HAS_REQUIREMENT FROM df", {"df": dataframes['has_requirement']})
        
        print("Import completed successfully!")
    
    def save_to_csv(self, dataframes: Dict[str, pd.DataFrame], output_dir: Path):
        """デバッグ用: DataFrameをCSVに保存"""
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for name, df in dataframes.items():
            csv_path = output_dir / f"{name}.csv"
            df.to_csv(csv_path, index=False)
            print(f"Saved {name} to {csv_path}")
    
    def import_from_markdown_file(self, md_file: Path, version: str = "5.0"):
        """Markdownファイルから直接インポート"""
        print(f"Importing from {md_file}...")
        
        # Read markdown
        content = md_file.read_text(encoding='utf-8')
        
        # Parse to DataFrames
        dataframes = self.parse_markdown_to_dataframes(content, version)
        
        # Create schema
        self.create_schema()
        
        # Import data
        self.import_dataframes(dataframes)
        
        # Verify import
        result = self.conn.execute("MATCH (r:Requirement) RETURN count(r) as count").get_next()
        print(f"Total requirements imported: {result[0]}")


def main():
    """使用例"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python asvs_direct_import.py <markdown_file> [db_path]")
        sys.exit(1)
    
    md_file = Path(sys.argv[1])
    db_path = sys.argv[2] if len(sys.argv) > 2 else "./asvs.db"
    
    importer = ASVSDirectImporter(db_path)
    importer.import_from_markdown_file(md_file)


if __name__ == "__main__":
    main()