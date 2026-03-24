import os
import boto3
import json
from typing import Dict, Any
from datetime import datetime
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from context_manager import PRContextManager

class BedrockClient:
    def __init__(self):
        # Use provided AWS credentials for Bedrock
        self.region = os.getenv('AWS_REGION', 'ap-south-1')
        self.model_id = os.getenv('BEDROCK_MODEL', 'apac.amazon.nova-pro-v1:0')
        self.temperature = 0.3
        self.max_tokens = 4096
        
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.region,
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            aws_session_token=os.getenv('AWS_SESSION_TOKEN')
        )
        
        # Context manager will be initialized per PR in analyze_pr
        self.context_manager = None
    
    def analyze_code_with_context(self, code: str, language: str, file_path: str, 
                                pr_number: int, line_number: int = None) -> Dict[str, Any]:
        """Analyze code with conversational context from FAISS"""
        
        # Check for existing conversation at this location
        existing_context = None
        if line_number:
            existing_context = self.context_manager.get_conversation_at_location(
                pr_number, file_path, line_number
            )
        
        # Find similar contexts from previous PRs
        similar_contexts = self.context_manager.find_similar_contexts(code, top_k=3)
        
        # Build context-aware prompt
        context_info = ""
        if existing_context:
            context_info += f"\nPrevious conversation at this location:\n"
            for msg in existing_context['conversation_thread']:
                context_info += f"{msg['author']}: {msg['content']}\n"
        
        if similar_contexts:
            context_info += f"\nSimilar patterns from previous PRs:\n"
            for ctx, score in similar_contexts:
                if score > 0.7:  # High similarity threshold
                    context_info += f"- {ctx['file_path']}: {ctx['conversation_thread'][-1]['content'][:100]}...\n"
        
        # Get analysis with context
        prompt = self._build_context_aware_prompt(code, language, file_path, context_info)
        
        request_body = {
            "messages": [{"role": "user", "content": [{"text": prompt}]}],
            "inferenceConfig": {"temperature": self.temperature, "maxTokens": self.max_tokens}
        }
        
        try:
            response = self.client.converse(
                modelId=self.model_id,
                messages=request_body["messages"],
                inferenceConfig=request_body["inferenceConfig"]
            )
            
            result_text = response['output']['message']['content'][0]['text']
            analysis = json.loads(result_text)
            
            # Store this analysis in FAISS for future context
            if line_number and analysis.get('findings'):
                conversation_thread = [{
                    'author': 'comprinno-agent',
                    'content': analysis['findings'][0].get('description', ''),
                    'timestamp': datetime.now().isoformat(),
                    'comment_type': 'initial_finding'
                }]
                
                self.context_manager.add_conversation_context(
                    pr_number, file_path, line_number, code, conversation_thread
                )
            
            return analysis
            
        except Exception as e:
            return {"error": f"Bedrock analysis failed: {str(e)}"}
    
    def _build_context_aware_prompt(self, code: str, language: str, file_path: str, context_info: str) -> str:
        """Build prompt with conversational context"""
        base_prompt = self._build_prompt(code, language, file_path)
        
        if context_info:
            return f"""
CONVERSATIONAL CONTEXT:
{context_info}

Based on the above context:
1. Acknowledge previous discussions if any
2. Avoid repeating resolved issues  
3. Reference similar patterns when relevant
4. Provide contextual responses

{base_prompt}
"""
        return base_prompt
    
    def analyze_code(self, code: str, language: str, file_path: str, ticket_info: dict = None, previous_findings: list = None, previous_comments_context: str = "") -> Dict[str, Any]:
        """Send code to Bedrock Nova for analysis"""
        
        prompt = self._build_prompt(code, language, file_path, ticket_info, previous_findings, previous_comments_context)
        
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "temperature": self.temperature,
                "maxTokens": self.max_tokens
            }
        }
        
        try:
            response = self.client.converse(
                modelId=self.model_id,
                messages=request_body["messages"],
                inferenceConfig=request_body["inferenceConfig"]
            )
            
            result_text = response['output']['message']['content'][0]['text']
            return self._parse_response(result_text)
            
        except Exception as e:
            print(f"Error calling Bedrock: {e}")
            return {"error": str(e), "findings": []}
    
    def _build_prompt(self, code: str, language: str, file_path: str, ticket_info: dict = None, previous_findings: list = None, previous_comments_context: str = "") -> str:
        """Build analysis prompt for Bedrock"""
        ticket_section = ""
        if ticket_info:
            ac = "\n".join(f"  - {c}" for c in ticket_info.get('acceptance_criteria', [])) or "  Not specified"
            ticket_section = f"""## JIRA TICKET CONTEXT
Ticket: {ticket_info.get('ticket_id')} - {ticket_info.get('title')}
Type: {ticket_info.get('type')} | Status: {ticket_info.get('status')} | Priority: {ticket_info.get('priority')}
Description: {str(ticket_info.get('description', ''))[:500]}
Acceptance Criteria:
{ac}

Validate the code against the above ticket requirements in addition to general code quality checks.
Flag any acceptance criteria that are missing or incorrectly implemented.

"""

        previous_section = ""
        if previous_findings:
            items = "\n".join(f"  - [{f['category']}] Line {f['line']}: {f['description']}" for f in previous_findings)
            previous_section = f"""## PREVIOUS REVIEW CONTEXT
The following issues were flagged in the last review of this PR:
{items}

Instructions:
1. If any of the above issues are now fixed in the current code, explicitly acknowledge them as RESOLVED — do not re-raise them.
2. Do NOT re-report issues that are unchanged and already flagged above.
3. Only raise NEW issues introduced since the last review.

"""

        comments_section = ""
        if previous_comments_context:
            comments_section = f"""## PREVIOUS AGENT COMMENTS
{previous_comments_context}

Do not repeat findings already mentioned above. Focus only on new or unresolved issues.

"""
        return f"""You are an expert code reviewer performing a COMPREHENSIVE, PRODUCTION-READY code analysis of the following {language} code.

{ticket_section}{previous_section}{comments_section}

Analyze ALL aspects across these categories:

## 1. FUNCTIONAL VALIDATION
- Does code satisfy acceptance criteria and business requirements?
- Business logic correctness and completeness
- Edge cases: null/empty values, max limits, invalid formats, boundary conditions
- Backward compatibility - will this break existing functionality?
- Validation rules completeness and correctness
- Error responses consistency and appropriate status codes
- Is the solution overly complex for the requirement?

## 2. ARCHITECTURE & DESIGN
- Architectural guideline violations
- Tight coupling between components
- Layer separation (Controller/Service/Repository/DAO)
- Is logic in the correct layer?
- Single Responsibility Principle violations
- Dependency injection usage
- Design pattern appropriateness

## 3. SCALABILITY & PERFORMANCE
- High load impact (e.g., 10,000 concurrent users)
- Pagination requirements for large datasets
- Caching opportunities and strategy
- Database query optimization (N+1 queries, missing indexes)
- Required database indexes
- Memory leaks or excessive memory usage
- Blocking operations that should be async
- Algorithm time/space complexity

## 4. SECURITY (Specific Checks)
- SQL injection vulnerabilities
- Authentication and authorization checks
- Role-based access control implementation
- Sensitive data exposure in logs or responses
- API overexposure (returning more data than needed)
- Data leakage risks
- Input validation and sanitization
- XSS, CSRF vulnerabilities
- Hardcoded secrets or credentials

## 5. RELIABILITY & ERROR HANDLING
- Graceful failure handling
- Fail-safe mechanisms
- Proper exception handling (not swallowing errors)
- Logging quality - is it useful for debugging?
- Transaction management and rollback
- Retry logic where appropriate
- Circuit breaker patterns for external calls

## 6. TECHNICAL CORRECTNESS
- Async/await pattern correctness
- Blocking calls in async code
- Transaction handling and isolation levels
- Concurrency issues and race conditions
- Thread safety
- Resource cleanup (connections, files, streams)
- Dependency justification - are new dependencies necessary?
- Deprecated API usage
- Type safety and null safety

## 7. CODE QUALITY
- Code structure and organization
- Redundant or unnecessary code
- Naming conventions and clarity
- Code duplication (DRY principle)
- Cyclomatic complexity
- Method/function length
- Class size (god classes)
- Magic numbers and hardcoded values
- Dead code

## 8. TESTING CONSIDERATIONS
- Unit test coverage gaps
- Edge case test scenarios missing
- Integration test needs
- Negative test cases
- Mock usage appropriateness
- Test data quality
- Testability of the code

## 9. IMPACT ASSESSMENT
- Production stability risk level
- Which modules/services are affected?
- Is rollback possible if issues occur?
- Feature toggle requirements
- Database migration requirements
- Deployment considerations

File: {file_path}

Code:
```{language}
{code}
```

For EACH issue found, provide DETAILED, EDUCATIONAL explanations suitable for developers of all experience levels:

Return your analysis as JSON:
{{
  "findings": [
    {{
      "category": "string (e.g., 'SQL Injection Risk', 'Missing Pagination', 'N+1 Query', 'Missing Edge Case', 'Layer Violation', 'Security Risk', 'Scalability Issue', etc.)",
      "severity": "Critical|Warning|Info",
      "line_start": <number>,
      "line_end": <number>,
      "description": "Detailed, educational description of the issue with context",
      "why_it_matters": "Explain the impact, consequences, production risks, and why this is important",
      "how_to_fix": "Step-by-step instructions on how to fix this issue",
      "code_example": "Detailed code example showing the fix with explanatory comments",
      "best_practice": "Related best practice, design principle, or architectural guideline",
      "code_snippet": "The problematic code"
    }}
  ]
}}

IMPORTANT: Be thorough and check ALL categories. Focus on production-readiness, not just code style.

Only return valid JSON, no other text."""
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Bedrock response"""
        try:
            # Extract JSON from response
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                json_str = response_text[start:end]
                return json.loads(json_str)
            return {"findings": []}
        except json.JSONDecodeError:
            return {"findings": [], "error": "Failed to parse response"}
