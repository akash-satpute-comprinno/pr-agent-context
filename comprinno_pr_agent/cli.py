#!/usr/bin/env python3
import argparse
import os
import sys
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from bedrock.client import BedrockClient
from parsers.python_parser import PythonParser
from report.markdown_generator import MarkdownReportGenerator
from github_provider import GitHubProvider
from context_manager import PRContextManager
from jira_ticket_extractor import JiraTicketExtractor

def load_env():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent / '.env'
    load_dotenv(env_file)

def detect_language(file_path: str) -> str:
    """Detect programming language from file extension"""
    ext = file_path.lower().split('.')[-1]
    language_map = {
        'py': 'python',
        'js': 'javascript',
        'java': 'java',
        'ts': 'typescript',
        'jsx': 'javascript',
        'tsx': 'typescript'
    }
    return language_map.get(ext, 'unknown')

def analyze_file(file_path: str, bedrock_client: BedrockClient, report_gen: MarkdownReportGenerator):
    """Analyze a single file"""
    print(f"\n📄 Analyzing: {file_path}")
    
    language = detect_language(file_path)
    if language == 'unknown':
        print(f"⚠️  Unsupported file type: {file_path}")
        return
    
    # Read file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return
    
    # Analyze with Bedrock
    print(f"🔍 Running AI analysis...")
    results = bedrock_client.analyze_code(code, language, file_path)
    
    if 'error' in results:
        print(f"❌ Analysis error: {results['error']}")
        return
    
    # Generate report
    print(f"📝 Generating report...")
    report_content = report_gen.generate(file_path, results)
    report_path = report_gen.save_report(file_path, report_content)
    
    findings_count = len(results.get('findings', []))
    print(f"✅ Report saved: {report_path}")
    print(f"   Found {findings_count} issue(s)")

def analyze_pr(pr_url: str, bedrock_client: BedrockClient, report_gen: MarkdownReportGenerator,
               jira_context: dict = None, previous_comments_context: str = ""):
    """Analyze a GitHub PR with FAISS-based issue tracking"""
    print(f"\n🔗 Analyzing GitHub PR: {pr_url}")
    
    try:
        github = GitHubProvider(pr_url)
    except Exception as e:
        print(f"❌ Failed to connect to GitHub: {e}")
        return
    
    pr_info = github.get_pr_info()
    pr_number = pr_info['number']
    print(f"📋 PR #{pr_number}: {pr_info['title']}")
    
    context_mgr = PRContextManager(pr_number)
    
    # Extract Jira ticket from PR title
    jira_extractor = JiraTicketExtractor()
    ticket_info = jira_extractor.extract_and_fetch(pr_info['title'])
    if ticket_info:
        print(f"🎫 Linked ticket: {ticket_info['ticket_id']} - {ticket_info['title']}")
    else:
        print(f"⚠️  No Jira ticket found in PR title")
    
    # Fetch previous agent comments from GitHub (source of truth)
    previous_comments = github.get_previous_agent_comments()
    previous_findings = parse_previous_findings(previous_comments)
    
    if previous_findings:
        print(f"📋 Found {len(previous_findings)} previously flagged issue(s) — will check if resolved")
        for f in previous_findings:
            print(f"   - [{f['category']}] Line {f['line']}: {f['description'][:60]}")
    else:
        print(f"🆕 No previous analysis found — running fresh review")
    
    # Full analysis
    pr_files = github.get_pr_files()
    print(f"\n📁 Found {len(pr_files)} changed file(s)")
    
    all_findings = []
    ticket_completion = {"done": [], "not_done": [], "partial": []}
    all_resolved_issues = []
    
    for file_info in pr_files:
        filename = file_info['filename']
        language = detect_language(filename)
        
        if language == 'unknown':
            continue
        
        print(f"📄 Analyzing: {filename}")
        
        code = github.get_file_content(filename)
        if not code:
            continue
        
        changed_lines = github.parse_diff_lines(file_info['patch'])
        if not changed_lines:
            continue
        
        print(f"🔍 Running AI analysis...")
        results = bedrock_client.analyze_code(code, language, filename, ticket_info=jira_context or ticket_info, previous_findings=previous_findings, previous_comments_context=previous_comments_context)
        
        if 'error' in results:
            continue

        # Collect ticket completion from each file analysis (merge lists)
        tc = results.get('ticket_completion', {})
        for key in ['done', 'not_done', 'partial']:
            ticket_completion[key].extend(tc.get(key, []))

        # Collect resolved issues
        all_resolved_issues.extend(results.get('resolved_issues', []))
        
        findings = results.get('findings', [])
        changed_line_numbers = {cl['line_number'] for cl in changed_lines}
        is_new_file = file_info.get('status') == 'added' or len(changed_line_numbers) == len(code.splitlines())
        relevant_findings = findings if is_new_file else [
            f for f in findings
            if any(f.get('line_start', 0) <= ln <= f.get('line_end', 0) for ln in changed_line_numbers)
        ]
        
        # Add file info to findings
        for f in relevant_findings:
            f['file'] = filename

        # Post inline comments on the PR diff
        for finding in relevant_findings:
            line = finding.get('line_start')
            if not line:
                continue
            # Only comment on lines that are in the diff
            if line not in changed_line_numbers and not is_new_file:
                continue
            severity_emoji = {'Critical': '🔴', 'Warning': '🟡', 'Info': '🔵'}.get(finding.get('severity'), '⚪')
            inline_body = (
                f"{severity_emoji} **{finding.get('category')}** ({finding.get('severity')})\n\n"
                f"{finding.get('description', '')}\n\n"
                f"**Why it matters:** {finding.get('why_it_matters', '')}\n\n"
                f"**How to fix:**\n{finding.get('how_to_fix', '')}"
            )
            if finding.get('code_example'):
                inline_body += f"\n\n**Suggested fix:**\n```python\n{finding.get('code_example')}\n```"
            github.post_review_comment(filename, line, inline_body)

        all_findings.extend(relevant_findings)
    
    # Store findings in FAISS
    if all_findings:
        context_mgr.store_findings(all_findings)
        print(f"💾 Stored {len(all_findings)} findings in FAISS")
    
    # Post consolidated comment
    print(f"\n📝 Generating report...")
    summary = generate_pr_summary(pr_info, pr_files, all_findings, previous_comments, ticket_info=ticket_info, previous_findings=previous_findings, ticket_completion=ticket_completion, resolved_issues=all_resolved_issues)
    github.post_summary_comment(summary)
    
    print(f"\n✅ Analysis complete! Found {len(all_findings)} issue(s)")



def parse_previous_findings(comments: list) -> list:
    """Extract previously flagged issues from the last agent comment"""
    if not comments:
        return []
    
    last_comment = comments[0]['body']  # most recent first
    findings = []
    
    import re
    # Matches: "1. **Category** (Line 45)\n   description..."
    for match in re.finditer(r'\d+\.\s+\*\*(.+?)\*\*\s+\(Line\s+(\w+)\)\s*\n\s+(.+?)(?=\n|$)', last_comment):
        findings.append({
            'category': match.group(1).strip(),
            'line': match.group(2).strip(),
            'description': match.group(3).strip().rstrip('.')
        })
    
    return findings



    """Generate report comparing fixed vs still-present issues"""
    summary = f"## 🤖 Issue Resolution Check\n\n"
    summary += f"**PR:** #{pr_info['number']}\n\n"
    
    if fixed_issues:
        summary += f"### ✅ Fixed Issues ({len(fixed_issues)})\n\n"
        for issue in fixed_issues[:10]:
            summary += f"- **{issue.get('category', 'Issue')}** (Line {issue.get('line', '?')})\n"
            summary += f"  {issue.get('description', '')[:80]}...\n\n"
    
    if still_present:
        summary += f"### ❌ Still Present ({len(still_present)})\n\n"
        for issue in still_present[:10]:
            summary += f"- **{issue.get('category', 'Issue')}** (Line {issue.get('line', '?')})\n"
            summary += f"  {issue.get('description', '')[:80]}...\n\n"
    
    if not fixed_issues and not still_present:
        summary += f"### ℹ️ No previous issues to compare\n\n"
    
    summary += f"---\n*🤖 Generated by Deep Code Analysis Agent*"
    return summary


def generate_pr_summary(pr_info: dict, files: List, findings: List, previous_comments: List = None, ticket_info: dict = None, previous_findings: list = None, ticket_completion: dict = None, resolved_issues: list = None) -> str:
    """Generate consolidated PR summary comment with ticket details"""
    critical = sum(1 for f in findings if f.get('severity') == 'Critical')
    warning = sum(1 for f in findings if f.get('severity') == 'Warning')
    info = sum(1 for f in findings if f.get('severity') == 'Info')
    
    summary = f"## 🤖 Deep Code Analysis Report\n\n"
    summary += f"**PR:** #{pr_info['number']} - {pr_info['title']}\n\n"
    
    # Show previous context summary
    if previous_findings:
        summary += f"### 🔁 Previous Review Context\n\n"
        summary += f"The following issues were flagged in the last review. The model has been instructed to acknowledge resolved ones and skip unchanged ones:\n\n"
        for f in previous_findings:
            summary += f"- **{f['category']}** (Line {f['line']}): {f['description'][:80]}\n"
        summary += "\n"
    
    # Add Ticket Details
    if ticket_info:
        summary += f"---\n\n"
        summary += f"### 📋 Jira Ticket Details\n\n"
        summary += f"**Ticket:** {ticket_info['ticket_id']} - {ticket_info['title']}\n"
        summary += f"**Type:** {ticket_info['type']} | **Status:** {ticket_info['status']} | **Priority:** {ticket_info['priority']}\n"
        summary += f"**Assignee:** {ticket_info['assignee']}\n\n"
        summary += f"**Description:** {str(ticket_info['description'])[:150]}...\n\n"
    
    # Show if this is a re-analysis
    if previous_comments:
        summary += f"**Status:** Re-analysis (Previous analysis: {len(previous_comments)} comment(s))\n\n"
    
    summary += f"### 🔍 Code Analysis Results\n\n"
    summary += f"| Metric | Count |\n"
    summary += f"|--------|-------|\n"
    summary += f"| Files Analyzed | {len(files)} |\n"
    summary += f"| Total Issues | {len(findings)} |\n"
    summary += f"| 🔴 Critical | {critical} |\n"
    summary += f"| 🟡 Warning | {warning} |\n"
    summary += f"| 🔵 Info | {info} |\n\n"
    
    if ticket_info:
        summary += f"### ✅ Ticket Validation\n\n"
        summary += f"- ✅ Analyzed code against ticket: {ticket_info['ticket_id']}\n"
        summary += f"- ✅ Checked {len(files)} changed files\n"
        summary += f"- ✅ Validated code quality and best practices\n"
        summary += f"- ✅ Found {len(findings)} issue(s)\n\n"

        # Ticket completion status
        if ticket_completion and any(ticket_completion.values()):
            summary += f"### 📋 Jira Ticket Completion — {ticket_info['ticket_id']}\n\n"
            summary += f"**Ticket:** {ticket_info['title']}\n\n"
            if ticket_completion.get('done'):
                summary += f"**✅ Done:**\n"
                for item in ticket_completion['done']:
                    summary += f"- {item}\n"
                summary += "\n"
            if ticket_completion.get('partial'):
                summary += f"**⚠️ Partially Done:**\n"
                for item in ticket_completion['partial']:
                    summary += f"- {item}\n"
                summary += "\n"
            if ticket_completion.get('not_done'):
                summary += f"**❌ Not Yet Done:**\n"
                for item in ticket_completion['not_done']:
                    summary += f"- {item}\n"
                summary += "\n"

    # Resolved issues from previous review
    if resolved_issues:
        summary += f"### ✅ Resolved Since Last Review\n\n"
        for issue in resolved_issues:
            summary += f"- **{issue.get('category')}** — {issue.get('description')}\n"
        summary += "\n"
    if findings:
        summary += f"### Issues Found\n\n"
        
        # Group by severity
        for severity in ['Critical', 'Warning', 'Info']:
            severity_findings = [f for f in findings if f.get('severity') == severity]
            if severity_findings:
                emoji = {'Critical': '🔴', 'Warning': '🟡', 'Info': '🔵'}.get(severity, '⚪')
                summary += f"#### {emoji} {severity} ({len(severity_findings)})\n\n"
                
                for i, finding in enumerate(severity_findings[:5], 1):  # Limit to 5 per severity
                    summary += f"{i}. **{finding.get('category', 'Issue')}** (Line {finding.get('line_start', '?')})\n\n"
                    summary += f"   **Issue:** {finding.get('description', 'No description')}\n\n"
                    if finding.get('why_it_matters'):
                        summary += f"   **Why it matters:** {finding.get('why_it_matters')}\n\n"
                    if finding.get('how_to_fix'):
                        summary += f"   **How to fix:** {finding.get('how_to_fix')}\n\n"
                    if finding.get('code_example'):
                        summary += f"   **Suggested fix:**\n   ```python\n   {finding.get('code_example')}\n   ```\n\n"
                
                if len(severity_findings) > 5:
                    summary += f"   ... and {len(severity_findings) - 5} more\n\n"
        
        summary += f"### Recommendations\n\n"
        summary += f"1. ⚠️ Address **Critical** issues before merging\n"
        summary += f"2. 📋 Review **Warning** issues and plan fixes\n"
        summary += f"3. 💡 Consider **Info** items for code quality\n\n"
        summary += f"**To re-analyze:** Comment `@agent analyze` on this PR\n\n"
    else:
        summary += f"### ✅ No Issues Found!\n\n"
        summary += f"The changed code looks good. Great work! 🎉\n\n"
    
    summary += f"---\n*Powered by AWS Bedrock Nova | [Deep Code Analyzer](https://github.com)*"
    return summary

def analyze_directory(dir_path: str, bedrock_client: BedrockClient, report_gen: MarkdownReportGenerator):
    """Analyze all supported files in directory and generate consolidated report"""
    supported_extensions = ['.py', '.js', '.java', '.ts', '.jsx', '.tsx']
    
    files = []
    for root, _, filenames in os.walk(dir_path):
        for filename in filenames:
            if any(filename.endswith(ext) for ext in supported_extensions):
                files.append(os.path.join(root, filename))
    
    if not files:
        print(f"⚠️  No supported files found in {dir_path}")
        return
    
    print(f"\n📁 Found {len(files)} file(s) to analyze")
    
    # Reset consolidated data
    report_gen.reset()
    
    # Analyze each file and collect results
    for file_path in files:
        print(f"\n📄 Analyzing: {file_path}")
        
        language = detect_language(file_path)
        if language == 'unknown':
            print(f"⚠️  Unsupported file type: {file_path}")
            continue
        
        # Read file
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            continue
        
        # Analyze with Bedrock
        print(f"🔍 Running comprehensive AI analysis...")
        results = bedrock_client.analyze_code(code, language, file_path)
        
        if 'error' in results:
            print(f"❌ Analysis error: {results['error']}")
            continue
        
        # Add to consolidated report
        report_gen.add_file_analysis(file_path, results)
        
        findings_count = len(results.get('findings', []))
        print(f"✅ Analysis complete: {findings_count} finding(s)")
    
    # Generate and save consolidated report
    print(f"\n📝 Generating consolidated report...")
    dir_name = os.path.basename(os.path.normpath(dir_path))
    report_content = report_gen.generate_consolidated_report(dir_name)
    report_path = report_gen.save_consolidated_report(dir_path, report_content)
    
    print(f"✅ Consolidated report saved: {report_path}")

def main():
    parser = argparse.ArgumentParser(
        description='Deep Code Analysis Agent - Automated code quality analyzer',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze a single file
  python cli.py --file sample.py
  
  # Analyze all files in a directory
  python cli.py --directory ./src
  
  # Analyze a GitHub PR
  python cli.py --pr_url https://github.com/owner/repo/pull/123
  
  # Analyze with custom AWS region
  AWS_REGION=us-west-2 python cli.py --file app.py
        """
    )
    
    parser.add_argument('--file', type=str, help='Path to a single file to analyze')
    parser.add_argument('--directory', type=str, help='Path to directory to analyze')
    parser.add_argument('--pr_url', type=str, help='GitHub PR URL to analyze')
    parser.add_argument('--version', action='version', version='Deep Code Analyzer v1.0.0')
    
    args = parser.parse_args()
    
    if not args.file and not args.directory and not args.pr_url:
        parser.print_help()
        sys.exit(1)
    
    # Load environment
    load_env()
    
    # Check AWS credentials
    if not os.getenv('AWS_ACCESS_KEY_ID'):
        print("❌ Error: AWS_ACCESS_KEY_ID not set")
        print("   Please configure .env file or set environment variables")
        sys.exit(1)
    
    # Check GitHub token if analyzing PR
    if args.pr_url and not os.getenv('GITHUB_TOKEN'):
        print("❌ Error: GITHUB_TOKEN not set")
        print("   Please configure .env file or set GITHUB_TOKEN environment variable")
        sys.exit(1)
    
    print("🚀 Deep Code Analysis Agent")
    print("=" * 50)
    
    # Initialize components
    try:
        bedrock_client = BedrockClient()
        report_gen = MarkdownReportGenerator()
        print(f"✅ Connected to AWS Bedrock ({os.getenv('AWS_REGION', 'us-east-1')})")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        sys.exit(1)
    
    # Run analysis
    if args.pr_url:
        analyze_pr(args.pr_url, bedrock_client, report_gen)
    elif args.file:
        if not os.path.exists(args.file):
            print(f"❌ File not found: {args.file}")
            sys.exit(1)
        analyze_file(args.file, bedrock_client, report_gen)
    elif args.directory:
        if not os.path.isdir(args.directory):
            print(f"❌ Directory not found: {args.directory}")
            sys.exit(1)
        analyze_directory(args.directory, bedrock_client, report_gen)
    
    print("\n✨ Analysis complete!")

if __name__ == '__main__':
    main()
