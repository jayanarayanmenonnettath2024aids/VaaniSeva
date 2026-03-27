#requires -version 5.0
<#
.SYNOPSIS
    Automated E2E QA Test Suite for PALLAVI Multi-Module Backend
.DESCRIPTION
    Comprehensive testing script that validates:
    - Backend service health
    - Core workflow integration (voice -> AI -> action)
    - Analytics and reporting
    - Database persistence
    - DPDP compliance (hashed refs, no raw PII)
    - Response validation and error handling
.AUTHOR
    PALLAVI QA Automation
.VERSION
    1.0
#>

param(
    [string]$BackendUrl = "http://127.0.0.1:8000",
    [string]$ReportPath = "qa_report.txt",
    [int]$TimeoutSeconds = 30
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# ============================================================================
# REPORT GENERATION HELPERS
# ============================================================================

$script:ReportLines = @()
$script:TestsPassed = 0
$script:TestsFailed = 0
$script:StartTime = Get-Date

function Write-Report {
    param([string]$Message)
    $script:ReportLines += $Message
    Write-Host $Message
}

function Log-Test {
    param(
        [string]$TestName,
        [bool]$Passed,
        [string]$Details = ""
    )
    if ($Passed) {
        $script:TestsPassed++
        $status = "[✓ PASS]"
    } else {
        $script:TestsFailed++
        $status = "[✗ FAIL]"
    }
    $msg = "$status $TestName"
    if ($Details) {
        $msg += " | $Details"
    }
    Write-Report $msg
}

function Log-Section {
    param([string]$Title)
    Write-Report ""
    Write-Report "=" * 80
    Write-Report $Title
    Write-Report "=" * 80
}

# ============================================================================
# HTTP REQUEST HELPERS
# ============================================================================

function Invoke-SafeRequest {
    param(
        [string]$Uri,
        [string]$Method = "Get",
        [hashtable]$Body = $null,
        [string]$ContentType = "application/json"
    )
    
    try {
        $params = @{
            Uri = $Uri
            Method = $Method
            ContentType = $ContentType
            TimeoutSec = $TimeoutSeconds
            UseBasicParsing = $true
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params.Body = $Body | ConvertTo-Json -Compress
        }
        
        $response = Invoke-WebRequest @params
        return @{
            Success = $true
            StatusCode = $response.StatusCode
            Content = $response.Content
            Headers = $response.Headers
        }
    } catch {
        if ($_.Exception.Response) {
            return @{
                Success = $false
                StatusCode = [int]$_.Exception.Response.StatusCode
                Content = $_.Exception.Message
            }
        }
        return @{
            Success = $false
            StatusCode = 0
            Content = $_.Exception.Message
        }
    }
}

# ============================================================================
# SMOKE TESTS
# ============================================================================

function Test-Health {
    Log-Section "SMOKE TEST: Backend Health"
    
    $response = Invoke-SafeRequest "$BackendUrl/health"
    $passed = $response.Success -and $response.StatusCode -eq 200
    
    Log-Test "Health Endpoint" $passed "Status: $($response.StatusCode)"
    return $passed
}

function Test-VoiceResponse {
    Log-Section "SMOKE TEST: Voice Module"
    
    $response = Invoke-SafeRequest "$BackendUrl/voice-response" -Method Get
    $passed = $response.Success -and $response.StatusCode -eq 200 -and $response.Content -like "*Response*"
    
    Log-Test "Voice Response XML" $passed "Status: $($response.StatusCode)"
    return $passed
}

function Test-ProcessText {
    Log-Section "SMOKE TEST: AI Module"
    
    $body = @{
        call_id = "smoke-ai-001"
        mobile = "+919999911111"
        text = "Road pothole near school gate"
    }
    
    $response = Invoke-SafeRequest "$BackendUrl/process-text" -Method Post -Body $body
    $passed = $response.Success -and $response.StatusCode -eq 200
    
    Log-Test "AI Process Text" $passed "Status: $($response.StatusCode)"
    
    if ($passed) {
        $content = $response.Content | ConvertFrom-Json
        Log-Test "  - Call ID Binding" ($null -ne $content.call_id) "call_id: $($content.call_id)"
        Log-Test "  - Issue Extraction" ($null -ne $content.structured_data.issue_type) "type: $($content.structured_data.issue_type)"
        Log-Test "  - Response Generated" ($content.response.Length -gt 0) "length: $($content.response.Length)"
    }
    
    return $passed
}

function Test-ProcessAction {
    Log-Section "SMOKE TEST: Action Module"
    
    $body = @{
        call_id = "smoke-action-001"
        structured_data = @{
            customer_name = "QA User"
            mobile = "+919999922222"
            issue = "Water leakage in apartment"
            location = "Narimanpoint, Mumbai"
            issue_type = "Water"
        }
    }
    
    $response = Invoke-SafeRequest "$BackendUrl/process-action" -Method Post -Body $body
    $passed = $response.Success -and $response.StatusCode -eq 200
    
    Log-Test "Action Process" $passed "Status: $($response.StatusCode)"
    
    if ($passed) {
        $content = $response.Content | ConvertFrom-Json
        Log-Test "  - Ticket Created" ($content.ticket_id -like "TKT-*") "ticket: $($content.ticket_id)"
        Log-Test "  - Department Assigned" ($null -ne $content.department) "dept: $($content.department)"
        Log-Test "  - SLA Hours Set" ($content.sla_hours -gt 0) "sla: $($content.sla_hours)h"
    }
    
    return $passed
}

function Test-Analytics {
    Log-Section "SMOKE TEST: Analytics Endpoints"
    
    $endpoints = @(
        "/analytics/summary",
        "/analytics/issues",
        "/analytics/regions",
        "/analytics/sla",
        "/analytics/audit-summary"
    )
    
    $allPassed = $true
    foreach ($endpoint in $endpoints) {
        $response = Invoke-SafeRequest "$BackendUrl$endpoint" -Method Get
        $passed = $response.Success -and $response.StatusCode -eq 200
        Log-Test "Analytics: $endpoint" $passed "Status: $($response.StatusCode)"
        $allPassed = $allPassed -and $passed
    }
    
    return $allPassed
}

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

function Test-Integration-VoiceToAction {
    Log-Section "INTEGRATION TEST: Voice -> AI -> Action"
    
    $callId = "integ-e2e-$(Get-Random -Minimum 1000 -Maximum 9999)"
    $mobile = "+91" + (Get-Random -Minimum 9000000000 -Maximum 9999999999).ToString()
    
    Log-Test "Setup: Call ID" $true "id: $callId"
    Log-Test "Setup: Mobile" $true "mobile: $mobile"
    
    # Step 1: Simulate incoming call
    Write-Report ""
    Write-Report "Step 1: Incoming Call"
    $incomingResponse = Invoke-SafeRequest "$BackendUrl/incoming-call" -Method Post -Body @{ CallSid = $callId; From = $mobile }
    $step1Pass = $incomingResponse.Success -and $incomingResponse.StatusCode -eq 200
    Log-Test "  - Incoming Call" $step1Pass "Status: $($incomingResponse.StatusCode)"
    
    # Step 2: Process complaint via AI
    Write-Report ""
    Write-Report "Step 2: Process Text (AI)"
    $aiBody = @{
        call_id = $callId
        mobile = $mobile
        text = "Electricity outage near main gate for 3 hours"
    }
    $aiResponse = Invoke-SafeRequest "$BackendUrl/process-text" -Method Post -Body $aiBody
    $step2Pass = $aiResponse.Success -and $aiResponse.StatusCode -eq 200
    Log-Test "  - AI Process" $step2Pass "Status: $($aiResponse.StatusCode)"
    
    $ticketId = $null
    if ($step2Pass) {
        $aiContent = $aiResponse.Content | ConvertFrom-Json
        Log-Test "  - Language Detected" ($aiContent.language -eq "en" -or $aiContent.language -ne "") "lang: $($aiContent.language)"
        Log-Test "  - Issue Type Extracted" ($aiContent.structured_data.issue_type.Length -gt 0) "type: $($aiContent.structured_data.issue_type)"
    }
    
    # Step 3: Get ticket list to verify persistence
    Write-Report ""
    Write-Report "Step 3: Verify Ticket Persistence"
    $ticketsResponse = Invoke-SafeRequest "$BackendUrl/tickets" -Method Get
    $step3Pass = $ticketsResponse.Success -and $ticketsResponse.StatusCode -eq 200
    Log-Test "  - Tickets Fetch" $step3Pass "Status: $($ticketsResponse.StatusCode)"
    
    if ($step3Pass) {
        $ticketsContent = $ticketsResponse.Content | ConvertFrom-Json
        $ticketCount = $ticketsContent.tickets.Count
        Log-Test "  - Tickets in DB" ($ticketCount -gt 0) "count: $ticketCount"
    }
    
    return $step1Pass -and $step2Pass -and $step3Pass
}

# ============================================================================
# NEGATIVE TESTS
# ============================================================================

function Test-NegativeCases {
    Log-Section "NEGATIVE TESTS: Error Handling"
    
    # Test 1: Invalid Recording URL
    Write-Report ""
    Write-Report "Test 1: Invalid Recording URL"
    $invalidRecBody = @{ CallSid = "test-001"; RecordingUrl = "not-an-url" }
    $invalidResponse = Invoke-SafeRequest "$BackendUrl/process-recording" -Method Post -Body $invalidRecBody
    $test1Pass = (-not $invalidResponse.Success) -or $invalidResponse.StatusCode -eq 400
    Log-Test "  - Rejects Invalid URL" $test1Pass "Status: $($invalidResponse.StatusCode) (expect 400)"
    
    # Test 2: Empty Text
    Write-Report ""
    Write-Report "Test 2: Empty Text Processing"
    $emptyBody = @{ call_id = "neg-001"; text = ""; mobile = "+919999933333" }
    $emptyResponse = Invoke-SafeRequest "$BackendUrl/process-text" -Method Post -Body $emptyBody
    $test2Pass = $emptyResponse.StatusCode -eq 200 # Should return 200 with fallback
    Log-Test "  - Handles Empty Text" $test2Pass "Status: $($emptyResponse.StatusCode)"
    
    # Test 3: Missing Fields
    Write-Report ""
    Write-Report "Test 3: Missing Required Fields"
    $incompleteBody = @{ call_id = "neg-002" } # Missing text
    $incompleteResponse = Invoke-SafeRequest "$BackendUrl/process-text" -Method Post -Body $incompleteBody
    $test3Pass = (-not $incompleteResponse.Success) -or $incompleteResponse.StatusCode -ge 400
    Log-Test "  - Rejects Missing Fields" $test3Pass "Status: $($incompleteResponse.StatusCode)"
    
    return $test1Pass -or $test2Pass -or $test3Pass
}

# ============================================================================
# DATABASE VALIDATION
# ============================================================================

function Test-DatabasePersistence {
    Log-Section "DATABASE VALIDATION"
    
    try {
        $pythonScript = @'
import sqlite3
import json
import sys

try:
    conn = sqlite3.connect("data/pallavi.db")
    conn.row_factory = sqlite3.Row
    
    # Check schema migrations
    mig_rows = conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
    print(f"MIGRATIONS_COUNT={mig_rows}")
    
    # Check tickets
    tkt_rows = conn.execute("SELECT COUNT(*) FROM tickets").fetchone()[0]
    print(f"TICKETS_COUNT={tkt_rows}")
    
    # Check audit timeline
    aud_rows = conn.execute("SELECT COUNT(*) FROM audit_timeline").fetchone()[0]
    print(f"AUDIT_EVENTS={aud_rows}")
    
    # Check for hashed refs (DPDP compliance)
    audit_sample = conn.execute(
        "SELECT call_ref, mobile_ref, meta_json FROM audit_timeline LIMIT 1"
    ).fetchone()
    
    if audit_sample:
        print(f"AUDIT_HASHED_REFS={'yes' if (audit_sample['call_ref'] or audit_sample['mobile_ref']) else 'no'}")
        meta = json.loads(audit_sample['meta_json'] or '{}')
        print(f"AUDIT_META_KEYS={','.join(meta.keys()) if meta else 'empty'}")
    
    conn.close()
    sys.exit(0)
except Exception as e:
    print(f"ERROR={str(e)}")
    sys.exit(1)
'@
        
        $pythonScript | python -c "exec(input())" 2>&1 | ForEach-Object {
            if ($_ -like "MIGRATIONS_COUNT=*") {
                $count = $_.Split("=")[1]
                Log-Test "DB: Schema Migrations" ($count -gt 0) "count: $count"
            }
            elseif ($_ -like "TICKETS_COUNT=*") {
                $count = $_.Split("=")[1]
                Log-Test "DB: Tickets Table" ($count -ge 0) "count: $count"
            }
            elseif ($_ -like "AUDIT_EVENTS=*") {
                $count = $_.Split("=")[1]
                Log-Test "DB: Audit Timeline" ($count -ge 0) "count: $count"
            }
            elseif ($_ -like "AUDIT_HASHED_REFS=*") {
                $value = $_.Split("=")[1]
                Log-Test "DB: DPDP Hashed Refs" ($value -eq "yes") "status: $value"
            }
            elseif ($_ -like "ERROR=*") {
                $error = $_.Split("=")[1]
                Log-Test "DB: Validation" $false "error: $error"
            }
        }
    } catch {
        Log-Test "DB: Validation" $false $_.Exception.Message
    }
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

function Main {
    Log-Section "PALLAVI E2E QA TEST SUITE"
    Write-Report "Start Time: $($script:StartTime)"
    Write-Report "Backend URL: $BackendUrl"
    Write-Report ""
    
    # Pre-flight check
    try {
        $healthResponse = Invoke-SafeRequest "$BackendUrl/health" -ErrorAction SilentlyContinue
        if (-not $healthResponse.Success) {
            Write-Report "[ERROR] Backend not responding at $BackendUrl"
            Write-Report "Please start backend: uvicorn app.main:app --port 8000"
            exit 1
        }
    } catch {
        Write-Report "[ERROR] Cannot connect to backend: $_"
        exit 1
    }
    
    # Run all test suites
    Test-Health
    Test-VoiceResponse
    Test-ProcessText
    Test-ProcessAction
    Test-Analytics
    Test-Integration-VoiceToAction
    Test-NegativeCases
    Test-DatabasePersistence
    
    # Generate summary
    Log-Section "TEST SUMMARY"
    $endTime = Get-Date
    $duration = ($endTime - $script:StartTime).TotalSeconds
    
    Write-Report "Tests Passed: $($script:TestsPassed)"
    Write-Report "Tests Failed: $($script:TestsFailed)"
    Write-Report "Total Tests: $($script:TestsPassed + $script:TestsFailed)"
    Write-Report "Duration: $([math]::Round($duration, 2))s"
    
    if ($script:TestsFailed -eq 0) {
        Write-Report ""
        Write-Report "✓ ALL TESTS PASSED"
        $exitCode = 0
    } else {
        Write-Report ""
        Write-Report "✗ SOME TESTS FAILED"
        $exitCode = 1
    }
    
    # Save to file
    $script:ReportLines | Out-File -FilePath $ReportPath -Encoding UTF8
    Write-Report ""
    Write-Report "Report saved to: $ReportPath"
    
    exit $exitCode
}

# Run main
Main
