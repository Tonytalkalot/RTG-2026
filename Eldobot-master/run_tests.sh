#!/bin/bash
# Simple test runner script for Eldobot
# Usage: ./run_tests.sh

echo "======================================"
echo "    Running Eldobot Test Suite"
echo "======================================"

# Run comprehensive tests with coverage
python -m pytest tests/test_basics.py \
    tests/test_basics_edge_cases.py \
    tests/test_calculations.py \
    tests/test_additional_coverage.py \
    tests/test_coverage_boost.py \
    tests/test_player_list_embed_advanced.py \
    tests/test_formula_ranking_advanced.py \
    tests/test_player_commands.py \
    tests/test_fa_commands.py \
    tests/test_team_commands.py \
    tests/test_league_commands.py \
    tests/test_trade_functions.py \
    tests/test_draft_commands.py \
    tests/test_discord_commands.py \
    tests/test_integration.py \
    --cov=basics \
    --cov-report=term \
    --cov-report=html \
    -v \
    --tb=short

echo ""
echo "======================================"
echo "    Test run complete!"
echo "    HTML report: htmlcov/index.html"
echo "======================================" 