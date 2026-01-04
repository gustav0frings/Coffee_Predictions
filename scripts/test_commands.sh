#!/bin/bash
# Test script to verify all commands in README work correctly
# This is a sanity check to ensure the project is working after changes

# Don't use set -e because we want to continue testing even if some tests fail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track test results
PASSED=0
FAILED=0

# Function to print test header
print_test() {
    echo -e "\n${YELLOW}=== Test: $1 ===${NC}"
}

# Function to print success
print_success() {
    echo -e "${GREEN}✓ PASSED: $1${NC}"
    ((PASSED++))
}

# Function to print failure
print_failure() {
    echo -e "${RED}✗ FAILED: $1${NC}"
    ((FAILED++))
}

# Function to run a command and check if it succeeds
run_test() {
    local test_name="$1"
    local command="$2"
    
    print_test "$test_name"
    if eval "$command" > /tmp/test_output.log 2>&1; then
        print_success "$test_name"
        return 0
    else
        print_failure "$test_name"
        echo "Command: $command"
        echo "Output:"
        cat /tmp/test_output.log
        return 1
    fi
}

# Check if we're in the project root
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: Must run from project root directory${NC}"
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated. Attempting to activate...${NC}"
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        echo -e "${RED}Error: Virtual environment not found. Please run 'uv venv' first.${NC}"
        exit 1
    fi
fi

# Set PYTHONPATH
export PYTHONPATH=$(pwd)

# Backup database if it exists
if [ -f "data/forecast.db" ]; then
    echo -e "${YELLOW}Backing up existing database...${NC}"
    cp data/forecast.db data/forecast.db.backup
    DB_BACKED_UP=true
else
    DB_BACKED_UP=false
fi

# Clean up function
cleanup() {
    if [ "$DB_BACKED_UP" = true ] && [ -f "data/forecast.db.backup" ]; then
        echo -e "\n${YELLOW}Restoring database backup...${NC}"
        if [ -f "data/forecast.db" ]; then
            rm data/forecast.db
        fi
        mv data/forecast.db.backup data/forecast.db 2>/dev/null || true
    fi
}

# Trap to ensure cleanup on exit
trap cleanup EXIT

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Testing README Commands${NC}"
echo -e "${GREEN}========================================${NC}"

# Test 1: Generate sample data
run_test "Generate sample data" \
    "python -c \"from src.ingest.load_sales import create_sample_data; import yaml; config = yaml.safe_load(open('config/config.yaml')); create_sample_data(config, num_items=3, days=60)\""

# Test 2: View database contents (summary)
run_test "View database summary" \
    "python src/utils/view_data.py"

# Test 3: View items
run_test "View items" \
    "python src/utils/view_data.py --items"

# Test 4: View sales data
run_test "View sales data" \
    "python src/utils/view_data.py --sales --limit 10"

# Test 5: View forecasts (may be empty if no model exists yet)
# This test may fail if no forecasts exist, so we allow it to fail gracefully
print_test "View forecasts"
if python src/utils/view_data.py --forecasts > /tmp/test_output.log 2>&1; then
    print_success "View forecasts"
else
    # Check if it's just because there are no forecasts (which is OK)
    if grep -q "No forecasts" /tmp/test_output.log; then
        print_success "View forecasts (no forecasts yet, which is OK)"
    else
        print_failure "View forecasts"
        cat /tmp/test_output.log
    fi
fi

# Test 6: View model runs (may be empty)
print_test "View model runs"
if python src/utils/view_data.py --runs > /tmp/test_output.log 2>&1; then
    print_success "View model runs"
else
    # Check if it's just because there are no runs (which is OK)
    if grep -q "No model runs" /tmp/test_output.log; then
        print_success "View model runs (no runs yet, which is OK)"
    else
        print_failure "View model runs"
        cat /tmp/test_output.log
    fi
fi

# Test 7: View all data
run_test "View all data" \
    "python src/utils/view_data.py --all"

# Test 8: View sales with item filter
run_test "View sales with item filter" \
    "python src/utils/view_data.py --sales --item-id 1 --limit 5"

# Test 9: Run pipeline in predict mode (without HIPOS file if it doesn't exist)
if [ -f "sample/output_hipos_sample.csv.csv" ]; then
    run_test "Run pipeline (predict mode)" \
        "python src/run_pipeline.py --mode predict"
else
    echo -e "${YELLOW}Skipping predict mode test (HIPOS file not found)${NC}"
fi

# Test 10: Run pipeline in retrain mode
run_test "Run pipeline (retrain mode)" \
    "python src/run_pipeline.py --mode retrain"

# Test 11: Run pipeline with HIPOS file (if it exists)
if [ -f "sample/output_hipos_sample.csv.csv" ]; then
    run_test "Run pipeline with HIPOS file" \
        "python src/run_pipeline.py --mode predict --hipos-file sample/output_hipos_sample.csv.csv --hipos-date 2025-01-15"
else
    echo -e "${YELLOW}Skipping HIPOS file test (file not found)${NC}"
fi

# Test 12: Verify forecasts were created
run_test "Verify forecasts exist" \
    "python src/utils/view_data.py --forecasts --limit 5"

# Test 13: Verify model was created
run_test "Verify model file exists" \
    "[ -f 'models/latest.model' ]"

# Test 14: Verify database tables exist
run_test "Verify database structure" \
    "python -c \"import sqlite3; conn = sqlite3.connect('data/forecast.db'); cursor = conn.cursor(); cursor.execute('SELECT name FROM sqlite_master WHERE type=\\\"table\\\"'); tables = [row[0] for row in cursor.fetchall()]; assert 'items' in tables, 'items table missing'; assert 'daily_item_sales' in tables, 'daily_item_sales table missing'; assert 'forecasts' in tables, 'forecasts table missing'; assert 'model_runs' in tables, 'model_runs table missing'; print('All tables exist'); conn.close()\""

# Print summary
echo -e "\n${GREEN}========================================${NC}"
echo -e "${GREEN}  Test Summary${NC}"
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Passed: ${PASSED}${NC}"
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}Failed: ${FAILED}${NC}"
    exit 1
else
    echo -e "${GREEN}Failed: ${FAILED}${NC}"
    echo -e "\n${GREEN}All tests passed! ✓${NC}"
    exit 0
fi

