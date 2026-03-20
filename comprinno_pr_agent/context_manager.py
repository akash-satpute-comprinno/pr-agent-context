import faiss
import numpy as np
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from sentence_transformers import SentenceTransformer
from pathlib import Path

class PRContextManager:
    def __init__(self, pr_number: int, index_path: str = ".pr_context"):
        self.pr_number = pr_number
        self.index_path = Path(index_path) / f"pr_{pr_number}"
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize embedding model (local)
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.embedding_dim = 384
        
        # FAISS index files (per PR)
        self.index_file = self.index_path / "findings.index"
        self.metadata_file = self.index_path / "findings.json"
        
        self.index = self._load_or_create_index()
        self.metadata = self._load_metadata()
    
    def _load_or_create_index(self):
        if self.index_file.exists():
            return faiss.read_index(str(self.index_file))
        return faiss.IndexFlatIP(self.embedding_dim)
    
    def _load_metadata(self) -> List[Dict]:
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_index(self):
        faiss.write_index(self.index, str(self.index_file))
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def store_findings(self, findings: List[Dict]):
        """Store code analysis findings in FAISS"""
        for finding in findings:
            # Create embedding from issue description + code
            text = f"{finding.get('category', '')} {finding.get('description', '')} {finding.get('code_snippet', '')}"
            embedding = self.encoder.encode([text])[0]
            self.index.add(np.array([embedding], dtype=np.float32))
            
            self.metadata.append({
                'id': len(self.metadata),
                'file': finding.get('file', ''),
                'line': finding.get('line_start', 0),
                'category': finding.get('category', ''),
                'severity': finding.get('severity', ''),
                'description': finding.get('description', ''),
                'code_snippet': finding.get('code_snippet', ''),
                'timestamp': datetime.now().isoformat(),
                'status': 'open'  # open, fixed, wontfix
            })
        
        self._save_index()
    
    def check_issue_fixed(self, new_code: str, old_finding: Dict) -> bool:
        """Check if a previously reported issue is fixed in new code"""
        # Simple check: if the problematic code snippet is no longer present
        old_snippet = old_finding.get('code_snippet', '')
        if old_snippet and old_snippet not in new_code:
            return True
        return False
    
    def compare_findings(self, new_findings: List[Dict], new_code: str) -> Dict:
        """Compare new findings with stored findings"""
        if not self.metadata:
            return {
                'new_issues': new_findings,
                'fixed_issues': [],
                'still_present': []
            }
        
        new_categories = {f.get('category') for f in new_findings}
        
        fixed = []
        still_present = []
        
        for old_finding in self.metadata:
            if old_finding['status'] == 'open':
                if self.check_issue_fixed(new_code, old_finding):
                    fixed.append(old_finding)
                    old_finding['status'] = 'fixed'
                else:
                    still_present.append(old_finding)
        
        self._save_index()
        
        return {
            'new_issues': new_findings,
            'fixed_issues': fixed,
            'still_present': still_present
        }
    
    def get_open_issues(self) -> List[Dict]:
        """Get all open issues for this PR"""
        return [m for m in self.metadata if m['status'] == 'open']
