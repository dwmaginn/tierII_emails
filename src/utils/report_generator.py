import webbrowser
import os
from datetime import datetime
from typing import List, Dict, Any


def generate_email_summary_report(
    total_contacts: int,
    successful_count: int,
    failed_count: int,
    success_rate: float,
    failed_contacts: List[Dict[str, Any]] = None,
    report_title: str = "Email Campaign Summary"
) -> str:
    """
    Generate an HTML summary report for email campaign results and open it in browser.
    
    Args:
        total_contacts (int): Total number of contacts processed
        successful_count (int): Number of successful email sends
        failed_count (int): Number of failed email sends
        success_rate (float): Success rate percentage
        failed_contacts (List[Dict]): List of failed contact details (optional)
        report_title (str): Title for the report
        
    Returns:
        str: Path to the generated HTML report file
    """
    if failed_contacts is None:
        failed_contacts = []
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)
    
    # Generate timestamp for the report
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Generate stats cards HTML
    stats_cards = f"""
        <div class="stat-card">
            <div class="stat-number total">{total_contacts}</div>
            <div class="stat-label">Total Contacts</div>
        </div>
        <div class="stat-card">
            <div class="stat-number success">{successful_count}</div>
            <div class="stat-label">Successful</div>
        </div>
        <div class="stat-card">
            <div class="stat-number failed">{failed_count}</div>
            <div class="stat-label">Failed</div>
        </div>
        <div class="stat-card">
            <div class="stat-number rate">{success_rate:.1f}%</div>
            <div class="stat-label">Success Rate</div>
        </div>
    """
    
    # Generate progress section HTML
    progress_section = f"""
        <div class="progress-section">
            <div class="progress-bar">
                <div class="progress-fill" style="width: {success_rate}%;">
                    {success_rate:.1f}% Success Rate
                </div>
            </div>
        </div>
    """
    
    # Generate failures section HTML
    failures_section = f"""
        <div class="failures-section">
            <h2 class="failures-title">Delivery Details</h2>
            {_generate_failures_section(failed_contacts)}
        </div>
    """

    # Create HTML content
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{report_title}</title>
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #a8d5a8 0%, #7cb97c 50%, #5a9b5a 100%);
                height: 100vh;
                overflow: hidden;
                color: #333;
                font-weight: 400;
                line-height: 1.4;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                height: 100vh;
                box-shadow: 0 0 30px rgba(0,0,0,0.1);
                overflow-y: auto;
            }}
            .hero-section {{
                background: linear-gradient(135deg, #a8d5a8 0%, #7cb97c 100%);
                padding: 40px 30px;
                text-align: center;
                color: white;
            }}
            .hero-title {{
                font-size: 2.8em;
                font-weight: 300;
                margin-bottom: 15px;
                text-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .hero-subtitle {{
                font-size: 1.1em;
                opacity: 0.95;
                margin-bottom: 20px;
                max-width: 600px;
                margin-left: auto;
                margin-right: auto;
                line-height: 1.5;
            }}
            .license-badge {{
                background: rgba(255,255,255,0.2);
                padding: 8px 20px;
                border-radius: 25px;
                display: inline-block;
                font-size: 0.85em;
                font-weight: 500;
                letter-spacing: 1px;
                text-transform: uppercase;
            }}
            .stats-section {{
                padding: 30px 30px;
                background: white;
                margin: 0;
                border-radius: 0;
            }}
            .section-title {{
                text-align: center;
                font-size: 2em;
                color: #2d5a2d;
                margin-bottom: 30px;
                font-weight: 300;
            }}
            .stats-grid {{
                display: flex;
                justify-content: center;
                align-items: center;
                flex-wrap: wrap;
                gap: 20px;
                margin-bottom: 25px;
            }}
            .stats-grid .stat-card:nth-child(4) {{
                order: -1;
                margin: 0 auto;
                width: 100%;
                max-width: 300px;
            }}
            .stat-card {{
                background: white;
                padding: 25px 20px;
                border-radius: 15px;
                text-align: center;
                box-shadow: 0 8px 25px rgba(0,0,0,0.08);
                border: 1px solid #f0f0f0;
                transition: all 0.3s ease;
                flex: 0 1 200px;
            }}
            .stat-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 12px 30px rgba(0,0,0,0.12);
            }}
            .stat-number {{
                font-size: 2.5em;
                font-weight: 300;
                margin-bottom: 10px;
                line-height: 1;
            }}
            .stat-label {{
                color: #666;
                font-size: 0.9em;
                text-transform: uppercase;
                letter-spacing: 1px;
                font-weight: 500;
            }}
            .success {{ color: #5a9b5a; }}
            .failed {{ color: #d32f2f; }}
            .total {{ color: #2d5a2d; }}
            .rate {{ color: #7cb97c; }}
            .progress-section {{
                background: #f8f9fa;
                padding: 25px;
                margin: 20px 0;
                border-radius: 15px;
            }}
            .progress-bar {{
                background: #e8f5e8;
                border-radius: 25px;
                overflow: hidden;
                height: 35px;
                position: relative;
                margin-bottom: 15px;
            }}
            .progress-fill {{
                height: 100%;
                background: linear-gradient(90deg, #5a9b5a 0%, #7cb97c 100%);
                border-radius: 25px;
                transition: width 1.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 600;
                font-size: 1em;
            }}
            .mission-section {{
                background: white;
                padding: 60px 40px;
                margin: 40px 0;
                border-radius: 20px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.08);
                text-align: center;
            }}
            .mission-title {{
                font-size: 2.2em;
                color: #2d5a2d;
                margin-bottom: 30px;
                font-weight: 300;
            }}
            .mission-text {{
                font-size: 1.1em;
                color: #666;
                line-height: 1.8;
                max-width: 700px;
                margin: 0 auto;
            }}
            .failures-section {{
                padding: 30px 30px;
                background: white;
                margin: 20px 0;
                border-radius: 20px;
                box-shadow: 0 8px 25px rgba(0,0,0,0.08);
            }}
            .failures-title {{
                color: #2d5a2d;
                margin-bottom: 20px;
                font-size: 1.8em;
                font-weight: 300;
                text-align: center;
            }}
            .failures-table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                font-size: 0.9em;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 4px 15px rgba(0,0,0,0.08);
            }}
            .failures-table th,
            .failures-table td {{
                padding: 12px 15px;
                text-align: left;
                border-bottom: 1px solid #f0f0f0;
            }}
            .failures-table th {{
                background: #2d5a2d;
                color: white;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-size: 0.8em;
            }}
            .failures-table tr:hover {{
                background: #f8f9fa;
            }}
            .failures-table tr:last-child td {{
                border-bottom: none;
            }}
            .no-failures {{
                text-align: center;
                color: #5a9b5a;
                font-size: 1.2em;
                padding: 40px 30px;
                background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%);
                border-radius: 15px;
                margin: 20px 0;
                border: 2px solid #a8d5a8;
            }}
            .no-failures::before {{
                content: "🎉";
                display: block;
                font-size: 2.5em;
                margin-bottom: 15px;
            }}
            .footer {{
                background: #2d5a2d;
                color: white;
                text-align: center;
                padding: 25px;
                font-size: 0.9em;
            }}
            .footer-content {{
                max-width: 600px;
                margin: 0 auto;
            }}
            .footer-title {{
                font-size: 1.2em;
                margin-bottom: 10px;
                font-weight: 600;
            }}
            .footer-subtitle {{
                opacity: 0.8;
                line-height: 1.6;
            }}
            @media (max-width: 768px) {{
                .nav-header {{
                    flex-direction: column;
                    gap: 15px;
                    padding: 15px;
                }}
                .nav-links {{
                    gap: 15px;
                }}
                .hero-section {{
                    padding: 30px 15px;
                }}
                .hero-title {{
                    font-size: 2.2em;
                }}
                .stats-section, .failures-section {{
                    padding: 20px 15px;
                }}
                .stats-grid {{
                    flex-direction: column;
                    gap: 15px;
                }}
                .stats-grid .stat-card:nth-child(4) {{
                    order: 0;
                    width: 100%;
                    max-width: none;
                }}
                .section-title, .failures-title {{
                    font-size: 1.6em;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="hero-section">
                <h1 class="hero-title">Email Campaign <span style="color: #2d5a2d;">Report</span></h1>
                <p class="hero-subtitle">Comprehensive analysis of your email marketing campaign performance and delivery metrics.</p>
                <div class="license-badge">Report Generated: {timestamp}</div>
            </div>
            
            <div class="stats-section">
                <h2 class="section-title">Campaign <span style="color: #7cb97c;">Statistics</span></h2>
                <div class="stats-grid">
                    {stats_cards}
                </div>
                {progress_section}
            </div>
            
            {failures_section}
            
            <div class="footer">
                <p>Report generated on {timestamp}</p>
                <p>Email Campaign System v1.0</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Write HTML to file
    report_path = os.path.join('logs', f'email_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.html')
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    # Open in browser
    webbrowser.open(f'file://{os.path.abspath(report_path)}')
    
    print(f"📊 Email summary report generated: {report_path}")
    print(f"🌐 Report opened in your default browser")
    
    return report_path


def _generate_failures_section(failed_contacts: List[Dict[str, Any]]) -> str:
    """Generate the failures section HTML content."""
    if not failed_contacts:
        return '''
        <div class="no-failures">
            🎉 Excellent! No failed email deliveries to report.
        </div>
        '''
    
    failures_html = '''
    <table class="failures-table">
        <thead>
            <tr>
                <th>Email</th>
                <th>Contact Name</th>
                <th>Status Code</th>
                <th>Error Message</th>
                <th>Timestamp</th>
            </tr>
        </thead>
        <tbody>
    '''
    
    for contact in failed_contacts:
        failures_html += f'''
        <tr>
            <td>{contact.get('email', 'N/A')}</td>
            <td>{contact.get('contact_name', 'N/A')}</td>
            <td>{contact.get('status_code', 'N/A')}</td>
            <td>{contact.get('error_message', 'N/A')[:100]}{'...' if len(str(contact.get('error_message', ''))) > 100 else ''}</td>
            <td>{contact.get('timestamp', 'N/A')}</td>
        </tr>
        '''
    
    failures_html += '''
        </tbody>
    </table>
    '''
    
    return failures_html