#!/usr/bin/env python3
"""
OWASP ASVS 5.0データをGitHubから取得してYAML形式に変換するスクリプト
"""
import re
import yaml
import requests
from pathlib import Path
from typing import Dict, List, Any

class ASVS5Fetcher:
    """ASVS 5.0データをフェッチして変換"""
    
    BASE_URL = "https://raw.githubusercontent.com/OWASP/ASVS/master/5.0/en"
    
    # 取得対象のMarkdownファイル
    ASVS_FILES = [
        "0x15-V6-Authentication.md",
        "0x16-V7-Session-Management.md", 
        "0x17-V8-Authorization.md",
        # 必要に応じて追加
    ]
    
    def fetch_markdown(self, filename: str) -> str:
        """GitHubからMarkdownファイルを取得"""
        url = f"{self.BASE_URL}/{filename}"
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    
    def parse_requirements_table(self, content: str) -> List[Dict[str, Any]]:
        """Markdownテーブルから要件を抽出"""
        requirements = []
        
        # テーブル行のパターン
        # | **6.2.1** | Description text | 1 |
        pattern = r'\|\s*\*?\*?(\d+\.\d+\.\d+)\*?\*?\s*\|(.*?)\|\s*(\d+)\s*\|'
        
        for match in re.finditer(pattern, content):
            req_num, description, level = match.groups()
            requirements.append({
                'number': req_num.strip(),
                'description': description.strip(),
                'level': int(level.strip())
            })
        
        return requirements
    
    def convert_to_yaml_structure(self, all_requirements: Dict[str, List]) -> Dict:
        """ASVS POCのYAML形式に変換"""
        return {
            'standard': {
                'uri': 'ref:standard:owasp:asvs:5.0',
                'name': 'OWASP Application Security Verification Standard',
                'version': '5.0',
                'description': 'The OWASP ASVS is a community-driven effort to establish a framework of security requirements',
                'url': 'https://owasp.org/www-project-application-security-verification-standard/'
            },
            'chapters': self._build_chapters(all_requirements)
        }
    
    def _build_chapters(self, all_requirements: Dict[str, List]) -> List[Dict]:
        """チャプター構造を構築"""
        chapters = []
        
        for chapter_name, requirements in all_requirements.items():
            # V6.2.1 -> V6がチャプター番号
            chapter_num = requirements[0]['number'].split('.')[0] if requirements else 'V0'
            
            chapter = {
                'uri': f'ref:standard:owasp:asvs:5.0:chapter:{chapter_num}',
                'number': chapter_num,
                'name': chapter_name.replace('_', ' ').title(),
                'sections': self._group_by_sections(requirements, chapter_num)
            }
            chapters.append(chapter)
        
        return chapters
    
    def _group_by_sections(self, requirements: List[Dict], chapter_num: str) -> List[Dict]:
        """要件をセクションごとにグループ化"""
        sections_dict = {}
        
        for req in requirements:
            # 6.2.1 -> 6.2がセクション
            section_num = '.'.join(req['number'].split('.')[:2])
            
            if section_num not in sections_dict:
                sections_dict[section_num] = {
                    'uri': f'ref:standard:owasp:asvs:5.0:section:{section_num}',
                    'number': section_num,
                    'name': f'Section {section_num}',
                    'requirements': []
                }
            
            req_data = {
                'uri': f'ref:standard:owasp:asvs:5.0:requirement:{req["number"]}',
                'number': req['number'],
                'description': req['description'],
                'level1': req['level'] >= 1,
                'level2': req['level'] >= 2,
                'level3': req['level'] >= 3,
                'tags': []  # 必要に応じて追加
            }
            
            sections_dict[section_num]['requirements'].append(req_data)
        
        return list(sections_dict.values())
    
    def fetch_and_convert(self, output_path: Path):
        """全体の処理を実行"""
        all_requirements = {}
        
        for filename in self.ASVS_FILES:
            print(f"Fetching {filename}...")
            content = self.fetch_markdown(filename)
            
            # ファイル名からチャプター名を抽出
            chapter_name = filename.replace('.md', '').split('-', 2)[2]
            requirements = self.parse_requirements_table(content)
            
            if requirements:
                all_requirements[chapter_name] = requirements
                print(f"  Found {len(requirements)} requirements")
        
        # YAML形式に変換
        yaml_data = self.convert_to_yaml_structure(all_requirements)
        
        # ファイルに保存
        with open(output_path, 'w') as f:
            yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)
        
        print(f"\nConverted data saved to {output_path}")


if __name__ == "__main__":
    fetcher = ASVS5Fetcher()
    output_path = Path("data/asvs_5.0_from_github.yaml")
    fetcher.fetch_and_convert(output_path)