# AJ Job Fisher

AJ Job Fisher is a private job-search control center deployed on AppDeploy.

Live app: https://aj-job-fisher-a2507o.v2.appdeploy.ai/

## What it does

- Persistent candidate ledger with duplicate detection
- Weighted 0–100 fit scoring
- Remote/pay/travel/credential guardrails
- AI job-URL ingestion and ATS extraction
- Tailored ATS application packages
- Application queue and evidence tracking
- Scan analytics
- Recruiter-message triage and reply drafting

## Automation policy

The companion ChatGPT automation `AJ Job Fisher` runs every 3 hours. It searches for fully remote U.S. roles, scores them, prepares tailored packages, and is authorized to submit 85+ matches only when an authenticated supported submission path exists and no mandatory-stop condition is triggered.

Mandatory-stop examples include medical/disability questions, background-check authorization, binding agreements, driving/vehicle requirements, criminal-history questions, drug/medical exams, relocation, >10% travel, unapproved references, uncertain answers, and other unsupported commitments.

## Important limitation

The AppDeploy app itself does not independently sign into third-party job boards or bypass CAPTCHA/MFA. True browser-based submission requires an authenticated browser workflow/integration. The automation must never report an application as submitted without confirmation evidence.

## Source

This directory mirrors the deployed AppDeploy source snapshot and is intended for version control, review, and future development.
