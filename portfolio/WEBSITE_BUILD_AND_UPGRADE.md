# Employer-Facing Portfolio Website — Build + Upgrade History

This record explains how the employer-facing portfolio is assembled and how changes are validated. It is intentionally separate from individual app histories so an interviewer can understand the presentation layer as well as the projects behind it.

## Step-by-step

1. Define the employer audience and the technical story the landing page must communicate.
2. Organize the portfolio around verified project capabilities rather than job titles or unsupported claims.
3. Give each featured project a direct live/demo path and a source or project-history path where available.
4. Keep independent projects explicitly separate from paid employment and client work.
5. Add concise evidence of implementation: architecture, tests, acceptance status, limitations, and links to the relevant repository.
6. Add a build/upgrade history for every cataloged application so the site can show how a project evolved instead of presenting only a final screenshot.
7. Validate links, project names, live deployment availability, and public-safe wording before publishing.
8. Run the repository Portfolio QC gate after source changes; live deployment checks remain a separate evidence class.
9. Review the rendered site as an employer would: can a technical reviewer reach the project, understand the problem, inspect the implementation, and see what was actually verified within a few minutes?
10. Record meaningful upgrades in Git history and the affected app's BUILD_AND_UPGRADE.md file.

## Current presentation layer

- Employer-facing site: https://aj-kivela-portfolio.lovable.app/
- Source/project index: `portfolio/README.md`
- Build/upgrade index: `portfolio/BUILD_AND_UPGRADE_INDEX.md`
- Repository quality gate: `.github/workflows/portfolio-qc.yml`

## Evidence rule

The website is a presentation layer. It must not upgrade a project from "implemented" to "live-tested" merely because a polished page exists. Each project history distinguishes source implementation, automated/fixture checks, live deployment checks, target-PC acceptance, and real-participant research.

## Upgrade checklist

- Add or update the project history first.
- Update the project README and live/source links.
- Update the portfolio presentation only after the underlying evidence is current.
- Run the applicable static/fixture QA gate.
- Smoke-test the public page and featured project links.
- Check that limitations and experimental integrations remain visible.
- Commit the documentation and source changes together when practical.

## Reviewer path

A reviewer should be able to move from the portfolio site → project → BUILD_AND_UPGRADE.md → source/tests → acceptance evidence without relying on private machine paths or private user data.