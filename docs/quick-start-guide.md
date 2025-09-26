# Ultra-Quick Start Guide

Get up and running with the TierII Email Campaign Tool in minutes!

## Prerequisites
- Python 3.7 or higher
- Git (if cloning the repository)

## Setup Steps

### 1. Create a Virtual Environment
```bash
python -m venv venv
```

### 2. Activate the Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Unix/MacOS:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run Tests to Verify Functionality
```bash
pytest
```

### 5. Build the Executable
```bash
pip install -e .
```

### 6. Configure Settings Files

Edit the following configuration files according to your needs:

- **Rate Configuration:** Edit `rate_config.json`
- **Email Configuration:** Edit `email_config.json`
- **Environment Variables:** Edit `.env` (copy from `.env.example` if needed)

## You're Ready!

After completing these steps, you can run the email campaign tool using:

```bash
email-campaign
```

For detailed configuration and usage instructions, refer to the [User Documentation](user-documentation.md).