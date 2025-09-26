"""JSON reader utility for loading email configuration."""

import json
import os
from typing import Dict, Any


def load_email_config() -> Dict[str, Any]:
    """
    Load email configuration from the JSON file.
    
    Returns:
        Dict[str, Any]: Dictionary containing the email configuration data
        
    Raises:
        FileNotFoundError: If the config file doesn't exist
        json.JSONDecodeError: If the JSON file is malformed
    """
    # Get the project root directory (go up from src/utils to project root)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    config_path = os.path.join(project_root, "data", "config", "email_config.json")
    
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config_data = json.load(file)
            
            # Load HTML content if path is provided
            if config_data.get('html') and config_data['html'].strip():
                html_path = os.path.join(project_root, config_data['html'])
                try:
                    with open(html_path, 'r', encoding='utf-8') as html_file:
                        config_data['html_content'] = html_file.read()
                except FileNotFoundError:
                    print(f"Warning: HTML file not found at {html_path}")
                    config_data['html_content'] = ""
            else:
                config_data['html_content'] = ""
                
            return config_data
    except FileNotFoundError:
        raise FileNotFoundError(f"Email configuration file not found at: {config_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in email configuration file: {e}", e.doc, e.pos)