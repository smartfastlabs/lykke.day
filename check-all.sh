#!/bin/bash

# Script to run all frontend and backend checks
# Continue running all checks even if one fails

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if any checks failed
FAILED=0

echo "=========================================="
echo "Running all checks for planned.day"
echo "=========================================="
echo ""

# Backend checks
echo -e "${YELLOW}Running backend checks...${NC}"
echo "----------------------------------------"

echo -e "\n${YELLOW}→ Running backend typecheck (mypy)...${NC}"
cd backend
if make typecheck; then
    echo -e "${GREEN}✓ Backend typecheck passed${NC}"
else
    echo -e "${RED}✗ Backend typecheck failed${NC}"
    FAILED=1
fi

echo -e "\n${YELLOW}→ Running backend tests...${NC}"
if make test; then
    echo -e "${GREEN}✓ Backend tests passed${NC}"
else
    echo -e "${RED}✗ Backend tests failed${NC}"
    FAILED=1
fi

echo -e "\n${YELLOW}→ Running backend mapper checks...${NC}"
if make check-mappers; then
    echo -e "${GREEN}✓ Backend mapper checks passed${NC}"
else
    echo -e "${RED}✗ Backend mapper checks failed${NC}"
    FAILED=1
fi
cd ..

# Frontend checks
echo ""
echo -e "${YELLOW}Running frontend checks...${NC}"
echo "----------------------------------------"
cd frontend

echo -e "\n${YELLOW}→ Running frontend checks (type-check, lint, test)...${NC}"
if npm run check; then
    echo -e "${GREEN}✓ Frontend checks passed${NC}"
else
    echo -e "${RED}✗ Frontend checks failed${NC}"
    FAILED=1
fi

cd ..

# Summary
echo ""
echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All checks passed! ✓${NC}"
    echo "=========================================="
    exit 0
else
    echo -e "${RED}Some checks failed! ✗${NC}"
    echo "=========================================="
    exit 1
fi
