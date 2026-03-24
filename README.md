# Comprinno PR Agent

An AI-powered Pull Request analysis tool that provides deep code analysis and insights with conversational context.

## Features

- Deep code analysis using AWS Bedrock
- **FAISS conversational context** - Remembers previous discussions and learns from history
- GitHub integration for automated PR reviews
- Python code parsing and analysis
- Markdown report generation
- GitHub Actions workflow support
- **Context-aware responses** - References similar patterns from history
- Comment-based re-analysis trigger with `@agent analyze`
- **Jira integration** - Validates code against ticket acceptance criteria

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r comprinno_pr_agent/requirements.txt
   ```

3. Configure environment variables:
   - Copy `comprinno_pr_agent/.env.template` to `comprinno_pr_agent/.env`
   - Add your AWS credentials and GitHub token

## Usage

Run the CLI tool:
```bash
python comprinno_pr_agent/cli.py
```

### Triggering Re-analysis

Comment `@agent analyze` on any PR to trigger a fresh analysis.

## GitHub Actions

The tool can be integrated with GitHub Actions for automated PR analysis. See `.github/workflows/code-analysis.yml` for configuration.

## Requirements

- Python 3.8+
- AWS Bedrock access
- GitHub API token
- FAISS for conversational context storage
- Jira API token (optional, for ticket validation)

## Changelog

- **2026-03-24**: Added Jira ticket validation and FAISS context memory.
- **2026-03-19**: Minor documentation update to test CI/CD flow.

