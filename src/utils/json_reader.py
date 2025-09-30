"""JSON reader utility for loading email configuration."""

import json
import os
import base64
from typing import Dict, Any, List


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
    config_path = os.path.join(project_root, "email_config.json")  # ← Simplified path
    
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
            
            # Process attachments if they exist
            config_data['processed_attachments'] = _process_attachments(
                config_data.get('attachments', []), project_root
            )
                
            return config_data
    except FileNotFoundError:
        raise FileNotFoundError(f"Email configuration file not found at: {config_path}")
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(f"Invalid JSON in email configuration file: {e}", e.doc, e.pos)


def _process_attachments(attachments: List[Dict[str, Any]], project_root: str) -> List[Dict[str, Any]]:
    """
    Process attachment configurations by loading and Base64 encoding the files.
    
    Args:
        attachments: List of attachment configurations from email_config.json
        project_root: Root directory of the project for resolving relative paths
        
    Returns:
        List[Dict[str, Any]]: List of processed attachments with Base64 encoded content
    """
    processed_attachments = []
    
    for attachment in attachments:
        try:
            # Validate required fields
            if not attachment.get('filename') or not attachment.get('path'):
                continue
                
            # Resolve attachment file path
            attachment_path = os.path.join(project_root, attachment['path'])
            
            # Read and encode the attachment file
            with open(attachment_path, 'rb') as file:
                file_content = file.read()
                base64_content = base64.b64encode(file_content).decode('utf-8')
                
            # Create processed attachment entry
            processed_attachment = {
                'filename': attachment['filename'],
                'content': base64_content,
                'content_id': attachment.get('content_id'),
                'disposition': attachment.get('disposition', 'attachment'),
                'path': attachment_path
            }
            
            processed_attachments.append(processed_attachment)
            
        except FileNotFoundError:
            # Skip missing files gracefully - tests expect this behavior
            continue
        except Exception:
            # Skip any other errors gracefully
            continue
    
    return processed_attachments