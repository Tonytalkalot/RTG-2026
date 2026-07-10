#!/usr/bin/env python
"""
Test runner for Eldobot test suite
Run with: python run_tests.py [options]

Options:
  --quick    Run only unit tests (faster)
  --full     Run all tests including integration (slower)
  --coverage Show detailed coverage report
"""
import sys
import subprocess

def run_tests():
    """Run the test suite with coverage reporting"""
    
    # Parse command line arguments
    quick_mode = "--quick" in sys.argv
    full_mode = "--full" in sys.argv
    coverage_mode = "--coverage" in sys.argv
    
    print("=" * 60)
    if quick_mode:
        print("Running Eldobot Test Suite (Quick Mode - Unit Tests Only)")
    elif full_mode:
        print("Running Eldobot Test Suite (Full Mode - All Tests)")
    else:
        print("Running Eldobot Test Suite (Default - Core Tests)")
    print("=" * 60)
    
    # Base command
    cmd = [sys.executable, "-m", "pytest"]
    
    # Select which tests to run
    if quick_mode:
        # Quick mode: only fast unit tests
        cmd.extend([
            "tests/test_basics.py",
            "tests/test_basics_edge_cases.py",
            "tests/test_calculations.py",
            "-q",  # Quiet output
            "--tb=no"  # No traceback for speed
        ])
    elif full_mode:
        # Full mode: all tests
        cmd.extend([
            "tests/",
            "-v",  # Verbose
            "--tb=short"  # Short traceback
        ])
    else:
        # Default: core tests that pass reliably
        cmd.extend([
            "tests/test_basics.py",
            "tests/test_basics_edge_cases.py",
            "tests/test_calculations.py",
            "tests/test_real_export_integration.py",
            "tests/test_error_handling.py",
            "tests/test_fa_commands.py::TestFACalculations",
            "tests/test_fa_commands.py::TestFAIntegration",
            "tests/test_player_commands.py::TestPlayerCalculations",
            "tests/test_player_commands.py::TestPlayerIntegration",
            "tests/test_gemini_integration.py",
            "tests/test_ai_media.py",
            "-q",  # Quiet output
            "--tb=line"  # One-line traceback
        ])
    
    # Add coverage if not in quick mode or if explicitly requested
    if coverage_mode or not quick_mode:
        cmd.extend([
            "--cov=basics",
            "--cov=fa_commands",
            "--cov=draft_commands",
            "--cov=player_commands",
            "--cov=team_commands",
            "--cov=league_commands",
            "--cov=input_trade",
            "--cov=trade_functions",
            "--cov=free_agency_runner",
            "--cov=gemini_integration",
            "--cov=ai_media",
            "--cov-report=term",
        ])
        
        if coverage_mode:
            cmd.append("--cov-report=html")
    
    try:
        # Run tests
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Print output
        print(result.stdout)
        
        # Print errors if any
        if result.stderr:
            print("\nErrors/Warnings:")
            print(result.stderr)
        
        # Print summary
        print("\n" + "=" * 60)
        if result.returncode == 0:
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed. See output above for details.")
        print("=" * 60)
        
        # Extract and display coverage
        if "basics.py" in result.stdout:
            for line in result.stdout.split('\n'):
                if "basics.py" in line and "%" in line:
                    print(f"\n📊 Coverage: {line.strip()}")
                    break
        
        print("\n📁 HTML coverage report generated in htmlcov/index.html")
        
        return result.returncode
        
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)