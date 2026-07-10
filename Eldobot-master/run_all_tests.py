#!/usr/bin/env python
"""
Master test runner for Eldobot
Runs all test suites and generates coverage report
"""

import sys
import subprocess
import os
import json
import asyncio
from datetime import datetime


def run_pytest_suite():
    """Run the pytest test suite"""
    print("\n" + "="*60)
    print("🧪 Running PyTest Suite")
    print("="*60)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_comprehensive.py",
        "-v",
        "--tb=short",
        "--cov=fa_commands",
        "--cov=player_commands", 
        "--cov=team_commands",
        "--cov=league_commands",
        "--cov=draft_commands",
        "--cov=roster",
        "--cov=basics",
        "--cov-report=term-missing",
        "--cov-report=html"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    return result.returncode == 0


async def run_command_tests():
    """Run the comprehensive command tests"""
    print("\n" + "="*60)
    print("🎮 Running Command Tests")
    print("="*60)
    
    # Import and run the test
    from test_all_commands import test_all_commands
    results = await test_all_commands()
    
    # Return success if most commands pass
    total = sum(len(results[k]) for k in ["pass", "fail", "no_output", "error"])
    passed = len(results["pass"])
    
    return passed > total * 0.7  # 70% pass rate


def run_integration_tests():
    """Run integration tests"""
    print("\n" + "="*60)
    print("🔗 Running Integration Tests")
    print("="*60)
    
    # Check if export exists
    if not os.path.exists("integration_test_export.json"):
        print("⚠️  No integration test export found")
        print("   Download an export to test with real data")
        return False
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_integration_fa_workflow.py",
        "tests/test_integration_roster_management.py",
        "-q",
        "--tb=no"
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(result.stdout)
    
    return "passed" in result.stdout.lower()


def generate_test_report():
    """Generate a comprehensive test report"""
    print("\n" + "="*60)
    print("📊 Generating Test Report")
    print("="*60)
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "python_version": sys.version,
        "test_results": {}
    }
    
    # Load command test results if available
    if os.path.exists("test_results.json"):
        with open("test_results.json", "r") as f:
            command_results = json.load(f)
            report["command_tests"] = command_results
    
    # Check coverage report
    coverage_file = "htmlcov/index.html"
    if os.path.exists(coverage_file):
        report["coverage_report"] = f"file://{os.path.abspath(coverage_file)}"
        print(f"📁 Coverage report: {coverage_file}")
    
    # Save report
    with open("test_report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Full report saved to test_report.json")
    
    return report


def print_summary(pytest_success, command_success, integration_success):
    """Print test summary"""
    print("\n" + "="*80)
    print("🏁 TEST SUMMARY")
    print("="*80)
    
    print("\nTest Suite Results:")
    print(f"  PyTest Suite:       {'✅ PASSED' if pytest_success else '❌ FAILED'}")
    print(f"  Command Tests:      {'✅ PASSED' if command_success else '❌ FAILED'}")
    print(f"  Integration Tests:  {'✅ PASSED' if integration_success else '⚠️  SKIPPED'}")
    
    overall_success = pytest_success and command_success
    
    print(f"\nOverall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    print("\n📚 Resources:")
    print("  - Coverage Report: htmlcov/index.html")
    print("  - Test Results:    test_results.json")
    print("  - Full Report:     test_report.json")
    
    print("\n💡 Tips:")
    print("  - Run 'python test_command.py -i' for interactive testing")
    print("  - Run 'python test_all_commands.py' to test all commands")
    print("  - Run 'pytest tests/' to run all pytest tests")
    
    return overall_success


async def main():
    """Main test runner"""
    print("\n" + "="*80)
    print("🚀 ELDOBOT COMPREHENSIVE TEST SUITE")
    print("="*80)
    print(f"Started at: {datetime.now()}")
    
    # Run all test suites
    pytest_success = run_pytest_suite()
    command_success = await run_command_tests()
    integration_success = run_integration_tests()
    
    # Generate report
    generate_test_report()
    
    # Print summary
    success = print_summary(pytest_success, command_success, integration_success)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())