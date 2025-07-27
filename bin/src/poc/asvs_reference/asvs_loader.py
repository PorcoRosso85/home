"""ASVS Data Loader Module.

This module provides functionality to load ASVS (Application Security Verification Standard)
data from YAML files and generate Cypher queries using Jinja2 templates.
"""

import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from jinja2 import Environment, FileSystemLoader, Template


class ASVSLoader:
    """Loads ASVS data and generates Cypher queries for graph database import."""
    
    def __init__(self, template_dir: Path = None, data_dir: Path = None):
        """Initialize the ASVS loader.
        
        Args:
            template_dir: Directory containing Jinja2 templates
            data_dir: Directory containing YAML data files
        """
        self.base_dir = Path(__file__).parent
        self.template_dir = template_dir or self.base_dir / "templates"
        self.data_dir = data_dir or self.base_dir / "data"
        
        # Initialize Jinja2 environment
        self.env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def load_yaml_data(self, filename: str) -> Dict[str, Any]:
        """Load ASVS data from a YAML file.
        
        Args:
            filename: Name of the YAML file to load
            
        Returns:
            Dictionary containing the loaded data
            
        Raises:
            FileNotFoundError: If the YAML file doesn't exist
            yaml.YAMLError: If the YAML file is invalid
        """
        filepath = self.data_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"YAML file not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def generate_cypher(self, data: Dict[str, Any], template_name: str = "asvs_reference.cypher.j2") -> str:
        """Generate Cypher queries from ASVS data using a template.
        
        Args:
            data: Dictionary containing ASVS data
            template_name: Name of the Jinja2 template to use
            
        Returns:
            Generated Cypher query string
        """
        template = self.env.get_template(template_name)
        
        # Add metadata to the context
        context = {
            **data,
            'timestamp': datetime.now().isoformat(),
            'source_file': 'asvs_sample.yaml'  # Could be parameterized
        }
        
        return template.render(context)
    
    def load_and_generate(self, yaml_filename: str, template_name: str = "asvs_reference.cypher.j2") -> str:
        """Load YAML data and generate Cypher queries in one step.
        
        Args:
            yaml_filename: Name of the YAML file to load
            template_name: Name of the Jinja2 template to use
            
        Returns:
            Generated Cypher query string
        """
        data = self.load_yaml_data(yaml_filename)
        return self.generate_cypher(data, template_name)
    
    def save_cypher(self, cypher: str, output_filename: str, output_dir: Optional[Path] = None) -> Path:
        """Save generated Cypher queries to a file.
        
        Args:
            cypher: Cypher query string to save
            output_filename: Name of the output file
            output_dir: Directory to save the file (defaults to current directory)
            
        Returns:
            Path to the saved file
        """
        output_dir = output_dir or Path.cwd()
        output_path = output_dir / output_filename
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(cypher, encoding='utf-8')
        
        return output_path


def main():
    """Example usage of the ASVS loader."""
    # Initialize loader
    loader = ASVSLoader()
    
    # Load and generate Cypher queries
    cypher = loader.load_and_generate("asvs_sample.yaml")
    
    # Save to file
    output_path = loader.save_cypher(cypher, "asvs_import.cypher")
    print(f"Generated Cypher queries saved to: {output_path}")
    
    # Print a preview
    print("\nGenerated Cypher (first 500 chars):")
    print(cypher[:500] + "..." if len(cypher) > 500 else cypher)


if __name__ == "__main__":
    main()