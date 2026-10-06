# Public use and server readiness

Updated October 6, 2026. This is a deployment plan and current readiness boundary, not a completed multi-user launch.

## Deployment choices

| Surface | Suitable public path | Current boundary |
|---|---|---|
| Informational websites | Static hosting/CDN with public access enabled | Four Sites are deployed owner-private; sharing and public indexing are pending |
| GFC personal computer control | Each user connects their own installed server and private tunnel | Current plugins are bound to AJ's laptop and must not be distributed with that personal connection |
| Elias and Evidence Auditor hosted applications | Authenticated service with authorization on each operation and isolated user/case storage | Public multi-user isolation, retention/deletion, and export review are not acceptance-tested here |
| GrimForge public rendering | Authenticated job API, queue, durable asset storage, and separate render workers | Real output quality, concurrency, storage, provider availability, and cost limits need acceptance |

## Do we need a better server?

Static companion websites do not require a new physical server. A small hosted API can coordinate user accounts and jobs, while document processing and rendering run on workers suited to their actual memory, duration, and GPU requirements. Choose worker size from measured jobs and expected concurrency; there is no demonstrated requirement to buy a dedicated GPU workstation solely to publish the websites.

Keep laptop orchestration separate from public compute. For a hosted launch, use durable user storage, access-controlled exports, a job queue with recoverable job IDs, bounded concurrency, provider/cost controls, monitoring, backups, and tested restore/deletion behavior. GPU work can use separately provisioned capacity when required. A web frontend's successful deployment does not test a media worker.

Cloudflare Workers currently have a 128 MB memory-per-isolate limit and bounded CPU time. That is appropriate evidence for keeping large model and media workloads outside the website request runtime, rather than treating a static/edge website as the rendering machine. See [official Workers limits](https://developers.cloudflare.com/workers/platform/limits/).

## GFC and authentication

The current private GFC installation intentionally uses a no-auth loopback MCP server behind the owner's secure tunnel. Do not change that working personal connection to OAuth merely to publish the product website.

Public distribution of a computer-control product needs a user-specific connection and machine authorization. A hosted service exposing private customer data or write actions needs authenticated users and scoped authorization. OpenAI's MCP authentication guidance describes OAuth 2.1 for authenticated MCP services; this would be a separate public backend design, not a retrofit that silently shares or replaces AJ's tunnel. See [OpenAI authentication guidance](https://developers.openai.com/plugins/build/auth) and [MCP server production requirements](https://developers.openai.com/plugins/concepts/mcp-server).

## Acceptance before a public app launch

Verify cross-user read/write denial, per-case storage isolation, authorized uploads and downloads, safe export behavior, retention/deletion, dependency/provider failure recovery, quota and cost enforcement, and backup restoration with fictional test records. Exercise representative concurrent jobs and inspect the final media and evidence outputs. Test installation and actual tool discovery in fresh user connections. Public plugin-directory submission and review are additional distribution steps; private package creation is not directory approval.

Current GFC health and Forge connectivity have been checked. Private workflow creation and successful static deployments are complete. Unrestricted public app access, public-directory acceptance, browser visual acceptance of these companion pages, and every media/provider path are not established by those checks.
