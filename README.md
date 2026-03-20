# PR Agent Context Demo

This repo demonstrates the **Comprinno PR Agent** — an AI-powered code reviewer using AWS Bedrock + Jira integration.

## Features
- Automatic code review on every PR
- Jira ticket context awareness
- Previous comment context (no repeated findings)
- Severity-based findings (Critical / Warning / Info)

## Demo Project
The `medical_app/` folder contains a real Flask + LangGraph medical application used as the target for code review.

## How It Works
1. Raise a PR → GitHub Actions triggers automatically
2. Agent fetches Jira ticket from branch name
3. Sends code to AWS Bedrock Nova Pro for analysis
4. Posts findings as a PR comment
