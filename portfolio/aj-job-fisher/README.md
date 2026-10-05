# ARCHIVED - AJ Job Fisher

**Retired from the active portfolio: October 5, 2026.**

This project is preserved in place for source/history reference only. The former AppDeploy deployment and scheduled scan are no longer treated as active portfolio functionality, and no further cron repair is planned as part of the current portfolio.


AJ Job Fisher was a private job-search control center deployed on AppDeploy. This README is retained for historical reference.

Former live app (retained for historical reference only): https://aj-job-fisher-a2507o.v2.appdeploy.ai/

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

Historical behavior: the companion ChatGPT automation `AJ Job Fisher` ran every 3 hours. That recurring workflow is retired with the app and should remain disabled unless the project is deliberately restored.

Mandatory-stop examples include medical/disability questions, background-check authorization, binding agreements, driving/vehicle requirements, criminal-history questions, drug/medical exams, relocation, >10% travel, unapproved references, uncertain answers, and other unsupported commitments.

## Important limitation

The AppDeploy app itself does not independently sign into third-party job boards or bypass CAPTCHA/MFA. True browser-based submission requires an authenticated browser workflow/integration. The automation must never report an application as submitted without confirmation evidence.

## Build + upgrade history

See [BUILD_AND_UPGRADE.md](BUILD_AND_UPGRADE.md) for the step-by-step implementation and upgrade trail.

## Source

This directory mirrors the deployed AppDeploy source snapshot and is intended for version control, review, and future development.