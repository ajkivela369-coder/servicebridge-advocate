#!/usr/bin/env bash
set -euo pipefail

echo "1) Python data check"
python python/summary.py

echo "2) SQL schema/query examples"
echo "Open sql/evaluations.sql with SQLite to create/query the evaluation store."

echo "3) TypeScript UI logic"
echo "See typescript/src for typed review-model examples."

echo "4) Statistical analysis"
echo "Run Rscript r/label_analysis.R when R is installed."

echo "5) C++ systems example"
echo "Compile: g++ -std=c++17 cpp/cosine_similarity.cpp -o /tmp/cosine_demo"
