# Comprinno PR Agent — Feature Documentation

## Overview

Comprinno PR Agent is an AI-powered Pull Request review tool that automatically analyzes code changes, validates them against Jira tickets, and posts detailed findings as comments on GitHub PRs.

---

## Features Added

### 1. AWS Bedrock AI Code Analysis

**What it does:**
Sends changed code to AWS Bedrock (Amazon Nova Pro model) for deep analysis across 9 categories:
- Functional Validation
- Architecture & Design
- Scalability & Performance
- Security (SQL injection, hardcoded secrets, XSS, etc.)
- Reliability & Error Handling
- Technical Correctness
- Code Quality
- Testing Considerations
- Impact Assessment

**How it works:**
- `bedrock/client.py` initializes a boto3 Bedrock Runtime client using env vars
- `analyze_code()` builds a detailed prompt and calls the `converse` API
- Response is parsed as JSON with structured findings (severity, line numbers, description, fix suggestions)

**Configuration:**
```
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...   # only for STS/SSO credentials
AWS_REGION=ap-south-1
BEDROCK_MODEL=apac.amazon.nova-pro-v1:0
```

---

### 2. Jira Ticket Integration

**What it does:**
Extracts the Jira ticket ID from the PR title or branch name, fetches full ticket details, and passes them to Bedrock so the AI validates code against the ticket's acceptance criteria.

**How it works:**
1. `JiraTicketExtractor.extract_ticket_id()` uses regex to find ticket IDs (e.g. `AAS-30`) in branch name or PR title
2. `JiraProvider.get_issue()` fetches ticket details via Jira REST API v3
3. Ticket info (title, description, acceptance criteria, status, priority) is injected into the Bedrock prompt
4. Results are cached in `.pr_context/jira_cache.json` for 1 hour to avoid redundant API calls

**Supported PR title formats:**
```
AAS-30 Fix SQL injection
[AAS-30] Fix SQL injection
feature/AAS-30-fix-sql
```

**Configuration:**
```
JIRA_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=your_jira_api_token
```

**PR comment output includes:**
```
📋 Jira Ticket Details
Ticket: AAS-30 - Fix SQL injection in auth service
Type: Bug | Status: To Do | Priority: High
Assignee: Unassigned
```

---

### 3. FAISS Conversational Context Memory

**What it does:**
Stores code analysis findings as vector embeddings using FAISS so the agent can track issues across multiple analyses of the same PR — detecting which issues were fixed and which are still present.

**How it works:**
1. `PRContextManager` initializes a FAISS `IndexFlatIP` index per PR
2. Each finding is embedded using `sentence-transformers/all-MiniLM-L6-v2` (384-dim vectors)
3. Findings are stored with metadata (file, line, category, severity, status)
4. On re-analysis, `compare_findings()` checks if previously flagged code snippets are still present
5. Issues are marked as `open`, `fixed`, or `wontfix`

**Storage:**
```
.pr_context/
  pr_2/
    findings.index    ← FAISS index
    findings.json     ← metadata
  jira_cache.json     ← Jira ticket cache
```

---

### 4. Previous Comments Context

**What it does:**
Before each analysis, the agent fetches its own previous comments from the PR and passes them to Bedrock as context — preventing it from repeating already-flagged issues.

**How it works:**
1. `GitHubProvider.get_previous_agent_comments()` fetches all comments containing `🤖 Deep Code Analysis Report`
2. The most recent comment body (capped at 2000 chars) is passed to Bedrock as `PREVIOUS REVIEW CONTEXT`
3. Bedrock is instructed to acknowledge resolved issues and only raise new ones

**Log output:**
```
📋 Previous review comments found — passing as context to avoid repetition
Status: Re-analysis (Previous analysis: 15 comment(s))
```

---

### 5. Diff-Aware Filtering

**What it does:**
Only reports issues on lines that were actually changed in the PR diff — not the entire file.

**How it works:**
1. `GitHubProvider.parse_diff_lines()` parses the unified diff patch to extract changed line numbers
2. Findings from Bedrock are filtered to only include those whose `line_start`–`line_end` range overlaps with changed lines
3. For new files (all lines added), all findings are included

---

### 6. Re-analysis Trigger

**What it does:**
Allows anyone to trigger a fresh analysis on an existing PR by posting a comment.

**How to trigger:**
Comment any of the following on the PR:
```
@agent analyze
/analyze
analyze
```

**How it works:**
The GitHub Actions workflow listens for `issue_comment` events and checks if the comment body contains the trigger keywords.

---

### 7. GitHub Actions Automation

**What it does:**
Automatically runs the full analysis pipeline whenever a PR is opened, updated, or re-analysis is triggered.

**Workflow triggers:**
- PR opened / new commit pushed
- Comment with `@agent analyze`

**Workflow file:** `.github/workflows/code-analysis.yml`

**Required GitHub Secrets:**
| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS credentials |
| `AWS_SECRET_ACCESS_KEY` | AWS credentials |
| `AWS_SESSION_TOKEN` | Required for STS/SSO credentials |
| `AWS_REGION` | e.g. `ap-south-1` |
| `BEDROCK_MODEL` | e.g. `apac.amazon.nova-pro-v1:0` |
| `JIRA_URL` | e.g. `https://yourcompany.atlassian.net` |
| `JIRA_EMAIL` | Jira login email |
| `JIRA_API_TOKEN` | Jira API token |

---

## End-to-End Flow

```
PR Opened / @agent analyze comment
        ↓
GitHub Actions triggers
        ↓
Extract Jira ticket ID from branch/PR title
        ↓
Fetch Jira ticket details (cached 1hr)
        ↓
Fetch previous agent comments from PR
        ↓
For each changed file:
  → Get full file content
  → Parse diff to get changed line numbers
  → Send code + Jira context + previous findings to Bedrock
  → Filter findings to changed lines only
        ↓
Store findings in FAISS index
        ↓
Post consolidated comment on PR
```

---

## Sample PR Comment Output

```
🤖 Deep Code Analysis Report

PR: #2 - AAS-30 Fix SQL injection in auth service

📋 Jira Ticket Details
Ticket: AAS-30 - Fix SQL injection in auth service
Type: Bug | Status: To Do | Priority: High

🔍 Code Analysis Results
| Files Analyzed | 3 |
| Total Issues   | 5 |
| 🔴 Critical    | 3 |
| 🟡 Warning     | 1 |
| 🔵 Info        | 1 |

🔴 Critical (3)
1. SQL Injection Risk (Line 24) — delete_user uses string concatenation...
2. Security Risk (Line 18) — password stored as plain text...
3. Security Risk (Line 16) — credentials not validated...

🟡 Warning (1)
1. Scalability Issue (Line 10) — get_all_users has no pagination...

🔵 Info (1)
1. Code Quality (Line 1) — missing error handling...
```

---

## Local Usage

```bash
# Analyze a single file
python cli.py --file path/to/file.py

# Analyze a directory
python cli.py --directory ./src

# Analyze a GitHub PR
python cli.py --pr_url https://github.com/owner/repo/pull/123
```
