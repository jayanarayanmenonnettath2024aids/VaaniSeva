#!/usr/bin/env python3
"""
PALLAVI Automated E2E QA Test Suite (Python)

Comprehensive testing that validates:
- Backend service health
- Core workflow integration (voice -> AI -> action)
- Analytics and reporting
- Database persistence and DPDP compliance
- Error handling and negative cases
"""

import requests
import json
import sqlite3
import sys
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Any, Optional
import hashlib
import random


@dataclass
class TestResult:
    """Represents a single test result."""
    name: str
    passed: bool
    status_code: Optional[int] = None
    details: str = ""


class QATestSuite:
    """Main QA test orchestrator."""
    
    def __init__(self, backend_url: str = "http://127.0.0.1:8000", timeout: int = 30):
        self.backend_url = backend_url.rstrip('/')
        self.timeout = timeout
        self.results: List[TestResult] = []
        self.start_time = datetime.now()
        self.session = requests.Session()
        
    def log_test(self, name: str, passed: bool, status_code: Optional[int] = None, details: str = ""):
        """Log a test result."""
        result = TestResult(name, passed, status_code, details)
        self.results.append(result)
        
        status = "✓ PASS" if passed else "✗ FAIL"
        msg = f"{status} | {name}"
        if details:
            msg += f" | {details}"
        print(msg)
    
    def print_section(self, title: str):
        """Print section header."""
        print()
        print("=" * 80)
        print(title)
        print("=" * 80)
    
    def safe_request(
        self,
        method: str,
        endpoint: str,
        body: Optional[Dict] = None,
        as_form: bool = False,
    ) -> Dict[str, Any]:
        """Make HTTP request safely."""
        url = f"{self.backend_url}{endpoint}"
        try:
            if method.upper() == "GET":
                resp = self.session.get(url, timeout=self.timeout)
            else:
                if as_form:
                    resp = self.session.post(url, data=body, timeout=self.timeout)
                else:
                    resp = self.session.post(url, json=body, timeout=self.timeout)
            
            return {
                'success': True,
                'status_code': resp.status_code,
                'content': resp.text,
                'json': resp.json() if resp.headers.get('content-type', '').find('json') >= 0 else None
            }
        except requests.exceptions.RequestException as e:
            status_code = 0
            if hasattr(e.response, 'status_code'):
                status_code = e.response.status_code
            
            return {
                'success': False,
                'status_code': status_code,
                'content': str(e),
                'json': None
            }
    
    # ========================================================================
    # SMOKE TESTS
    # ========================================================================
    
    def test_health(self) -> bool:
        """Test backend health endpoint."""
        self.print_section("SMOKE TEST: Backend Health")
        
        resp = self.safe_request("GET", "/health")
        passed = resp['success'] and resp['status_code'] == 200
        
        self.log_test("Health Endpoint", passed, resp['status_code'])
        return passed
    
    def test_voice_response(self) -> bool:
        """Test voice module response."""
        self.print_section("SMOKE TEST: Voice Module")
        
        resp = self.safe_request("GET", "/voice-response")
        passed = resp['success'] and resp['status_code'] == 200 and 'Response' in resp['content']
        
        self.log_test("Voice Response XML", passed, resp['status_code'])
        return passed
    
    def test_process_text(self) -> bool:
        """Test AI process text endpoint."""
        self.print_section("SMOKE TEST: AI Module")
        
        body = {
            "call_id": "smoke-ai-001",
            "mobile": "+919999911111",
            "text": "Road pothole near school gate"
        }
        
        resp = self.safe_request("POST", "/process-text", body)
        passed = resp['success'] and resp['status_code'] == 200
        
        self.log_test("AI Process Text", passed, resp['status_code'])
        
        if passed and resp['json']:
            data = resp['json']
            self.log_test("  ├─ Call ID Binding", 
                         data.get('call_id') == "smoke-ai-001",
                         details=f"call_id: {data.get('call_id')}")
            
            issue_type = data.get('structured_data', {}).get('issue_type')
            self.log_test("  ├─ Issue Extraction",
                         issue_type is not None,
                         details=f"type: {issue_type}")
            
            response_text = data.get('response', '')
            self.log_test("  └─ Response Generated",
                         len(response_text) > 0,
                         details=f"length: {len(response_text)}")
        
        return passed
    
    def test_process_action(self) -> bool:
        """Test action module."""
        self.print_section("SMOKE TEST: Action Module")
        
        body = {
            "call_id": "smoke-action-001",
            "structured_data": {
                "customer_name": "QA User",
                "mobile": "+919999922222",
                "issue": "Water leakage in apartment",
                "location": "Narimanpoint, Mumbai",
                "issue_type": "Water"
            }
        }
        
        resp = self.safe_request("POST", "/process-action", body)
        passed = resp['success'] and resp['status_code'] == 200
        
        self.log_test("Action Process", passed, resp['status_code'])
        
        if passed and resp['json']:
            data = resp['json']
            ticket_id = data.get('ticket_id', '')
            self.log_test("  ├─ Ticket Created",
                         ticket_id.startswith('TKT-'),
                         details=f"ticket: {ticket_id}")
            
            department = data.get('department')
            self.log_test("  ├─ Department Assigned",
                         department is not None,
                         details=f"dept: {department}")
            
            sla_hours = data.get('sla_hours', 0)
            self.log_test("  └─ SLA Hours Set",
                         sla_hours > 0,
                         details=f"sla: {sla_hours}h")
        
        return passed
    
    def test_analytics(self) -> bool:
        """Test analytics endpoints."""
        self.print_section("SMOKE TEST: Analytics Endpoints")
        
        endpoints = [
            "/analytics/summary",
            "/analytics/issues",
            "/analytics/regions",
            "/analytics/sla",
            "/analytics/audit-summary"
        ]
        
        all_passed = True
        for endpoint in endpoints:
            resp = self.safe_request("GET", endpoint)
            passed = resp['success'] and resp['status_code'] == 200
            self.log_test(f"Analytics: {endpoint}", passed, resp['status_code'])
            all_passed = all_passed and passed
        
        return all_passed
    
    # ========================================================================
    # INTEGRATION TESTS
    # ========================================================================
    
    def test_integration_voice_to_action(self) -> bool:
        """Test full voice -> AI -> action integration."""
        self.print_section("INTEGRATION TEST: Voice -> AI -> Action")
        
        call_id = f"integ-e2e-{random.randint(1000, 9999)}"
        mobile = f"+91{random.randint(9000000000, 9999999999)}"
        
        self.log_test("Setup: Call ID", True, details=f"id: {call_id}")
        self.log_test("Setup: Mobile", True, details=f"mobile: {mobile}")
        
        # Step 1: Incoming call
        print()
        print("Step 1: Incoming Call")
        incoming_body = {"CallSid": call_id, "From": mobile}
        incoming_resp = self.safe_request("POST", "/incoming-call", incoming_body, as_form=True)
        step1_pass = incoming_resp['success'] and incoming_resp['status_code'] == 200
        self.log_test("  ├─ Incoming Call", step1_pass, incoming_resp['status_code'])
        
        # Step 2: Process text via AI
        print()
        print("Step 2: Process Text (AI)")
        ai_body = {
            "call_id": call_id,
            "mobile": mobile,
            "text": "Electricity outage near main gate for 3 hours"
        }
        ai_resp = self.safe_request("POST", "/process-text", ai_body)
        step2_pass = ai_resp['success'] and ai_resp['status_code'] == 200
        self.log_test("  ├─ AI Process", step2_pass, ai_resp['status_code'])
        
        if step2_pass and ai_resp['json']:
            data = ai_resp['json']
            lang = data.get('language', 'unknown')
            self.log_test("  ├─ Language Detected", len(lang) > 0, details=f"lang: {lang}")
            
            issue_type = data.get('structured_data', {}).get('issue_type', 'unknown')
            self.log_test("  ├─ Issue Type Extracted", len(issue_type) > 0, details=f"type: {issue_type}")
        
        # Step 3: Verify ticket persistence
        print()
        print("Step 3: Verify Ticket Persistence")
        tickets_resp = self.safe_request("GET", "/tickets")
        step3_pass = tickets_resp['success'] and tickets_resp['status_code'] == 200
        self.log_test("  ├─ Tickets Fetch", step3_pass, tickets_resp['status_code'])
        
        if step3_pass and tickets_resp['json']:
            ticket_count = len(tickets_resp['json'].get('tickets', []))
            self.log_test("  └─ Tickets in DB", ticket_count > 0, details=f"count: {ticket_count}")
        
        return step1_pass and step2_pass and step3_pass
    
    # ========================================================================
    # NEGATIVE TESTS
    # ========================================================================
    
    def test_negative_cases(self) -> bool:
        """Test error handling."""
        self.print_section("NEGATIVE TESTS: Error Handling")
        
        all_passed = True
        
        # Test 1: Invalid Recording URL
        print()
        print("Test 1: Invalid Recording URL")
        invalid_body = {"CallSid": "test-001", "RecordingUrl": "not-an-url"}
        invalid_resp = self.safe_request("POST", "/process-recording", invalid_body)
        test1_pass = (not invalid_resp['success']) or invalid_resp['status_code'] == 400
        self.log_test("  ├─ Rejects Invalid URL", test1_pass,
                     status_code=invalid_resp['status_code'],
                     details="expect 400")
        all_passed = all_passed and test1_pass
        
        # Test 2: Empty Text
        print()
        print("Test 2: Empty Text Processing")
        empty_body = {"call_id": "neg-001", "text": "", "mobile": "+919999933333"}
        empty_resp = self.safe_request("POST", "/process-text", empty_body)
        test2_pass = empty_resp['status_code'] == 400  # Empty text is treated as missing fields
        self.log_test("  ├─ Handles Empty Text", test2_pass,
                     status_code=empty_resp['status_code'])
        all_passed = all_passed and test2_pass
        
        # Test 3: Missing Fields
        print()
        print("Test 3: Missing Required Fields")
        incomplete_body = {"call_id": "neg-002"}  # Missing text
        incomplete_resp = self.safe_request("POST", "/process-text", incomplete_body)
        test3_pass = (not incomplete_resp['success']) or incomplete_resp['status_code'] >= 400
        self.log_test("  └─ Rejects Missing Fields", test3_pass,
                     status_code=incomplete_resp['status_code'])
        all_passed = all_passed and test3_pass
        
        return all_passed
    
    # ========================================================================
    # DATABASE VALIDATION
    # ========================================================================
    
    def test_database_persistence(self):
        """Validate database state and DPDP compliance."""
        self.print_section("DATABASE VALIDATION")
        
        try:
            conn = sqlite3.connect("data/pallavi.db")
            conn.row_factory = sqlite3.Row
            
            # Check migrations
            mig_count = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
            self.log_test("DB: Schema Migrations", mig_count > 0, details=f"count: {mig_count}")
            
            # Check tickets
            tkt_count = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
            self.log_test("DB: Tickets Table", tkt_count >= 0, details=f"count: {tkt_count}")
            
            # Check audit timeline
            aud_count = conn.execute("SELECT COUNT(*) FROM audit_timeline").fetchone()[0]
            self.log_test("DB: Audit Timeline", aud_count >= 0, details=f"count: {aud_count}")
            
            # Check for hashed refs (DPDP compliance)
            audit_sample = conn.execute(
                "SELECT call_ref, mobile_ref, meta_json FROM audit_timeline LIMIT 1"
            ).fetchone()
            
            if audit_sample:
                has_hashed = (audit_sample['call_ref'] is not None and 
                            audit_sample['mobile_ref'] is not None)
                self.log_test("DB: DPDP Hashed Refs", has_hashed, 
                            details="call_ref and mobile_ref present")
                
                try:
                    meta = json.loads(audit_sample['meta_json'] or '{}')
                    meta_keys = ', '.join(meta.keys()) if meta else 'empty'
                    self.log_test("DB: Audit Metadata", len(meta) > 0,
                                details=f"keys: {meta_keys}")
                except:
                    self.log_test("DB: Audit Metadata", False, details="JSON parse error")
            
            conn.close()
        
        except sqlite3.OperationalError as e:
            self.log_test("DB: Connection", False, details=str(e))
    
    # ========================================================================
    # REPORTING
    # ========================================================================
    
    def run_all_tests(self):
        """Execute all test suites."""
        print()
        self.print_section("PALLAVI E2E QA TEST SUITE")
        print(f"Start Time: {self.start_time}")
        print(f"Backend URL: {self.backend_url}")
        print()
        
        # Pre-flight check
        try:
            resp = self.safe_request("GET", "/health")
            if not resp['success']:
                print("[ERROR] Backend not responding at", self.backend_url)
                print("Please start backend: uvicorn app.main:app --port 8000")
                return False
        except Exception as e:
            print("[ERROR] Cannot connect to backend:", str(e))
            return False
        
        # Run test suites
        self.test_health()
        self.test_voice_response()
        self.test_process_text()
        self.test_process_action()
        self.test_analytics()
        self.test_integration_voice_to_action()
        self.test_negative_cases()
        self.test_database_persistence()
        
        # Print summary
        self.print_section("TEST SUMMARY")
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        duration = (datetime.now() - self.start_time).total_seconds()
        
        print(f"Tests Passed: {passed}")
        print(f"Tests Failed: {failed}")
        print(f"Total Tests: {total}")
        print(f"Duration: {duration:.2f}s")
        print()
        
        if failed == 0:
            print("✓ ALL TESTS PASSED")
            return True
        else:
            print("✗ SOME TESTS FAILED")
            return False
    
    def save_report(self, filepath: str = "qa_report_python.json"):
        """Save test results to JSON file."""
        report = {
            "timestamp": self.start_time.isoformat(),
            "backend_url": self.backend_url,
            "duration_seconds": (datetime.now() - self.start_time).total_seconds(),
            "tests": [
                {
                    "name": r.name,
                    "passed": r.passed,
                    "status_code": r.status_code,
                    "details": r.details
                }
                for r in self.results
            ],
            "summary": {
                "passed": sum(1 for r in self.results if r.passed),
                "failed": sum(1 for r in self.results if not r.passed),
                "total": len(self.results)
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Report saved to: {filepath}")


def main():
    """Main entry point."""
    try:
        suite = QATestSuite()
        success = suite.run_all_tests()
        suite.save_report()
        
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Test suite stopped by user")
        return 130
    except Exception as e:
        print(f"\n[ERROR] Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
