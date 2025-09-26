import webbrowser
import os
from datetime import datetime
from typing import List, Dict, Any
from jinja2 import Environment, FileSystemLoader


def generate_email_summary_report(
    total_contacts: int,
    successful_count: int,
    failed_count: int,
    success_rate: float,
    failed_contacts: List[Dict[str, Any]] = None,
    report_title: str = "Email Campaign Summary",
    timestamp_override: str = None
) -> str:
    """
    Generate an HTML summary report for email campaign results and open it in browser.
    
    Args:
        total_contacts (int): Total number of contacts processed
        successful_count (int): Number of successful email sends
        failed_count (int): Number of failed email sends
        success_rate (float): Success rate as a percentage
        failed_contacts (List[Dict[str, Any]]): List of failed contact details
        report_title (str): Title for the report
        timestamp_override (str): Override timestamp for testing purposes
        
    Returns:
        str: Path to the generated HTML report file
    """
    if failed_contacts is None:
        failed_contacts = []
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Generate timestamp for the report
    timestamp = timestamp_override if timestamp_override else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Set up Jinja2 environment
    template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'templates')
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template('report_template.html')
    
    # Render template with data
    html_content = template.render(
        report_title=report_title,
        timestamp=timestamp,
        total_contacts=total_contacts,
        successful_count=successful_count,
        failed_count=failed_count,
        success_rate=success_rate,
        failed_contacts=failed_contacts
    )
    
    # Write HTML to file
    timestamp_str = timestamp_override if timestamp_override else datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join('logs', f'email_report_{timestamp_str}.html')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Open in browser
    webbrowser.open(f'file://{os.path.abspath(report_path)}')
    
    print(f"📊 Email summary report generated: {report_path}")
    print(f"🌐 Report opened in your default browser")
    
    return report_path