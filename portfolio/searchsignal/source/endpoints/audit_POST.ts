import { lookup } from "node:dns/promises";
import { isIP } from "node:net";
import * as cheerio from "cheerio";
import superjson from "superjson";
import { schema, type OutputType, type AuditCheck } from "./audit_POST.schema";

const MAX_BYTES = 1_500_000;
const MAX_REDIRECTS = 5;

function privateIp(ip: string): boolean {
  if (isIP(ip) === 4) {
    const p = ip.split(".").map(Number);
    return p[0] === 10 || p[0] === 127 || (p[0] === 169 && p[1] === 254) ||
      (p[0] === 172 && p[1] >= 16 && p[1] <= 31) || (p[0] === 192 && p[1] === 168) ||
      p[0] === 0 || p[0] >= 224;
  }
  const v = ip.toLowerCase();
  return v === "::1" || v === "::" || v.startsWith("fc") || v.startsWith("fd") ||
    v.startsWith("fe8") || v.startsWith("fe9") || v.startsWith("fea") || v.startsWith("feb");
}

async function assertPublicUrl(raw: string) {
  const parsed = new URL(raw);
  if (parsed.protocol !== "http:" && parsed.protocol !== "https:") throw new Error("Only public HTTP/HTTPS URLs can be audited.");
  const host = parsed.hostname.toLowerCase();
  if (host === "localhost" || host.endsWith(".localhost") || host.endsWith(".local")) throw new Error("Local/private hosts are not allowed.");
  if (isIP(host) && privateIp(host)) throw new Error("Private network targets are not allowed.");
  if (!isIP(host)) {
    const results = await lookup(host, { all: true, verbatim: true });
    if (!results.length || results.some(r => privateIp(r.address))) throw new Error("The host resolves to a private or unavailable address.");
  }
  return parsed;
}

async function fetchSafe(raw: string) {
  let current = (await assertPublicUrl(raw)).toString();
  for (let i = 0; i <= MAX_REDIRECTS; i++) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10_000);
    let response: Response;
    try {
      response = await fetch(current, {
        redirect: "manual",
        signal: controller.signal,
        headers: {
          "User-Agent": "SearchSignalPortfolioAuditor/1.0",
          "Accept": "text/html,application/xhtml+xml",
        },
      });
    } finally {
      clearTimeout(timeout);
    }
    if ([301,302,303,307,308].includes(response.status)) {
      const location = response.headers.get("location");
      if (!location) throw new Error("Redirect response did not include a destination.");
      current = new URL(location, current).toString();
      await assertPublicUrl(current);
      continue;
    }
    const contentType = response.headers.get("content-type") || "";
    if (!contentType.toLowerCase().includes("text/html") && !contentType.toLowerCase().includes("application/xhtml+xml")) {
      throw new Error("The target did not return an HTML page.");
    }
    const declared = Number(response.headers.get("content-length") || 0);
    if (declared > MAX_BYTES) throw new Error("The HTML response is too large for this portfolio auditor.");
    const reader = response.body?.getReader();
    if (!reader) throw new Error("The page returned no readable body.");
    const chunks: Uint8Array[] = [];
    let total = 0;
    while (true) {
      const next = await reader.read();
      if (next.done) break;
      total += next.value.byteLength;
      if (total > MAX_BYTES) {
        await reader.cancel();
        throw new Error("The HTML response exceeded the 1.5 MB safety limit.");
      }
      chunks.push(next.value);
    }
    const merged = new Uint8Array(total);
    let offset = 0;
    for (const chunk of chunks) { merged.set(chunk, offset); offset += chunk.byteLength; }
    return { html: new TextDecoder().decode(merged), response, finalUrl: current };
  }
  throw new Error("Too many redirects.");
}

function textList($: cheerio.CheerioAPI, selector: string) {
  return $(selector).map((_, el) => $(el).text().replace(/\s+/g, " ").trim()).get().filter(Boolean);
}

function schemaTypes(value: unknown, output: Set<string>) {
  if (!value || typeof value !== "object") return;
  if (Array.isArray(value)) { value.forEach(v => schemaTypes(v, output)); return; }
  const obj = value as Record<string, unknown>;
  const t = obj["@type"];
  if (typeof t === "string") output.add(t);
  if (Array.isArray(t)) t.filter(x => typeof x === "string").forEach(x => output.add(x as string));
  Object.values(obj).forEach(v => schemaTypes(v, output));
}

function add(checks: AuditCheck[], key: string, label: string, status: AuditCheck["status"], finding: string, why: string, points: number, maxPoints: number) {
  checks.push({ key, label, status, finding, why, points, maxPoints });
}

export async function handle(request: Request) {
  try {
    const input = schema.parse(superjson.parse(await request.text()));
    const { html, response, finalUrl } = await fetchSafe(input.url);
    if (!response.ok) throw new Error("Target returned HTTP " + response.status + ".");

    const $ = cheerio.load(html);
    $("script,style,noscript,template,svg").remove();
    const title = $("title").first().text().replace(/\s+/g, " ").trim() || null;
    const metaDescription = $('meta[name="description"]').attr("content")?.trim() || null;
    const canonical = $('link[rel="canonical"]').attr("href")?.trim() || null;
    const robots = $('meta[name="robots"]').attr("content")?.trim() || null;
    const language = $("html").attr("lang")?.trim() || null;
    const h1 = textList($, "h1");
    const h2 = textList($, "h2");
    const h3 = textList($, "h3");
    const bodyText = $("body").text().replace(/\s+/g, " ").trim();
    const wordCount = bodyText ? bodyText.split(/\s+/).length : 0;
    const base = new URL(finalUrl);
    let internal = 0, external = 0, emptyAnchors = 0;
    $("a").each((_, el) => {
      const href = ($(el).attr("href") || "").trim();
      const label = $(el).text().trim();
      if (!href || href === "#" || (!label && !$(el).find("img[alt]").length)) emptyAnchors++;
      if (!href || href.startsWith("#") || href.startsWith("mailto:") || href.startsWith("tel:") || href.startsWith("javascript:")) return;
      try {
        const u = new URL(href, finalUrl);
        if (u.hostname === base.hostname) internal++; else external++;
      } catch {}
    });
    const totalImages = $("img").length;
    const withAlt = $("img").filter((_, el) => $(el).attr("alt") !== undefined && ($(el).attr("alt") || "").trim().length > 0).length;
    const altCoveragePercent = totalImages ? Math.round((withAlt / totalImages) * 100) : 100;

    const types = new Set<string>();
    $('script[type="application/ld+json"]').each((_, el) => {
      try { schemaTypes(JSON.parse($(el).text()), types); } catch {}
    });
    const structuredDataTypes = [...types].sort();
    const wordpressDetected = /wp-content|wp-includes|wordpress/i.test(html) ||
      /wordpress/i.test($('meta[name="generator"]').attr("content") || "");

    const checks: AuditCheck[] = [];
    add(checks, "seo-title", "SEO · title", title && title.length >= 30 && title.length <= 65 ? "pass" : "high",
      title ? title.length + " characters: " + title : "Missing title",
      "A unique, descriptive title supports search relevance and click-through.", title && title.length >= 30 && title.length <= 65 ? 15 : title ? 8 : 0, 15);
    add(checks, "seo-description", "SEO · meta description", metaDescription && metaDescription.length >= 90 && metaDescription.length <= 180 ? "pass" : "medium",
      metaDescription ? metaDescription.length + " characters" : "Missing meta description",
      "Descriptions help searchers understand page value before clicking.", metaDescription ? 12 : 0, 12);
    add(checks, "seo-canonical", "SEO · canonical", canonical ? "pass" : "high", canonical || "Missing canonical",
      "Canonical URLs consolidate duplicate signals and clarify the preferred page.", canonical ? 15 : 0, 15);
    const noindex = /noindex/i.test(robots || "");
    add(checks, "seo-index", "SEO · indexability", noindex ? "critical" : "pass", robots || "No noindex directive detected",
      "An unintended noindex removes a page from conventional search results.", noindex ? 0 : 15, 15);
    add(checks, "seo-headings", "SEO · heading structure", h1.length === 1 ? "pass" : h1.length === 0 ? "high" : "medium",
      h1.length + " H1 · " + h2.length + " H2 · " + h3.length + " H3",
      "A clear heading hierarchy improves scanning and document structure.", h1.length === 1 ? 13 : h1.length ? 7 : 0, 13);
    add(checks, "seo-alt", "SEO · image alt coverage", altCoveragePercent >= 90 ? "pass" : altCoveragePercent >= 70 ? "medium" : "high",
      totalImages + " images · " + altCoveragePercent + "% with non-empty alt text",
      "Alt text supports accessibility and image understanding.", Math.round(10 * altCoveragePercent / 100), 10);
    add(checks, "seo-schema", "SEO · structured data", structuredDataTypes.length ? "pass" : "opportunity",
      structuredDataTypes.length ? structuredDataTypes.join(", ") : "No JSON-LD types detected",
      "Supported structured data helps machines identify page entities and relationships.", structuredDataTypes.length ? 10 : 0, 10);
    add(checks, "seo-links", "SEO · internal linking", internal >= 3 ? "pass" : "opportunity",
      internal + " internal · " + external + " external · " + emptyAnchors + " empty/weak anchors",
      "Internal links expose relationships and distribute discovery signals.", internal >= 3 ? 10 : Math.min(internal * 3, 9), 10);

    const firstParagraph = $("main p, article p, p").first().text().replace(/\s+/g, " ").trim();
    const answerFirst = firstParagraph.length >= 80 && firstParagraph.length <= 500;
    const questionHeadings = [...h2, ...h3].filter(x => x.endsWith("?")).length;
    const hasFaq = structuredDataTypes.includes("FAQPage");
    const hasAuthor = Boolean($('meta[name="author"]').attr("content") || $('[rel="author"], .author, [itemprop="author"]').length);
    const hasDate = Boolean($('meta[property="article:published_time"], meta[property="article:modified_time"], time[datetime], [itemprop="datePublished"], [itemprop="dateModified"]').length);
    const factualSpecificity = /\b\d+(?:\.\d+)?%|\b\d{4}\b|\b\d+(?:\.\d+)?\b/.test(bodyText);

    add(checks, "geo-answer", "GEO · answer-first summary", answerFirst ? "pass" : "high",
      answerFirst ? "Opening paragraph is concise and extractable." : "Opening content is absent, too short, or too diffuse.",
      "Answer engines benefit from a direct, self-contained summary near the top.", answerFirst ? 20 : 5, 20);
    add(checks, "geo-headings", "GEO · semantic sections", h2.length >= 2 ? "pass" : "medium", h2.length + " H2 sections detected",
      "Clear sections make facts easier to extract without losing context.", Math.min(h2.length * 5, 15), 15);
    add(checks, "geo-qa", "GEO · question/answer structure", questionHeadings > 0 || hasFaq ? "pass" : "opportunity",
      hasFaq ? "FAQPage schema detected" : questionHeadings + " question-style headings",
      "Explicit questions can align content with answer-oriented queries.", questionHeadings > 0 || hasFaq ? 10 : 2, 10);
    add(checks, "geo-schema", "GEO · machine-readable entities", structuredDataTypes.length ? "pass" : "high",
      structuredDataTypes.length ? structuredDataTypes.join(", ") : "No JSON-LD detected",
      "Schema can make entities, authorship, courses, articles, and page type more explicit.", structuredDataTypes.length ? 15 : 0, 15);
    add(checks, "geo-sources", "GEO · source signals", external >= 2 ? "pass" : "opportunity", external + " external source links",
      "Relevant source links make claims easier to verify and contextualize.", external >= 2 ? 10 : external * 4, 10);
    add(checks, "geo-editorial", "GEO · author/editorial context", hasAuthor ? "pass" : "opportunity", hasAuthor ? "Author signal detected" : "No clear author signal detected",
      "Named responsibility and editorial context support provenance.", hasAuthor ? 10 : 2, 10);
    add(checks, "geo-date", "GEO · freshness signal", hasDate ? "pass" : "opportunity", hasDate ? "Published/updated date signal detected" : "No machine-readable date detected",
      "Date signals help systems reason about freshness.", hasDate ? 10 : 2, 10);
    add(checks, "geo-specificity", "GEO · factual specificity", factualSpecificity ? "pass" : "opportunity", factualSpecificity ? "Concrete numeric/date detail detected" : "Little concrete numeric/date detail detected",
      "Specific facts are easier to extract and verify than vague claims.", factualSpecificity ? 10 : 3, 10);
    add(checks, "geo-readable", "GEO · accessible text", wordCount >= 250 ? "pass" : "medium", wordCount + " visible words",
      "Substantive HTML text is more extractable than image-only or script-hidden content.", wordCount >= 250 ? 10 : Math.min(Math.round(wordCount / 25), 9), 10);

    const score = (prefix: string) => {
      const set = checks.filter(c => c.key.startsWith(prefix));
      const got = set.reduce((n,c)=>n+c.points,0);
      const max = set.reduce((n,c)=>n+c.maxPoints,0);
      return Math.round((got / max) * 100);
    };

    const output: OutputType = {
      url: input.url, finalUrl, statusCode: response.status, title, metaDescription, canonical, robots, language,
      wordCount, headings: { h1, h2, h3 }, links: { internal, external, emptyAnchors },
      images: { total: totalImages, withAlt, altCoveragePercent }, structuredDataTypes, wordpressDetected,
      seoScore: score("seo-"), geoScore: score("geo-"), checks,
    };
    return new Response(superjson.stringify(output), { headers: { "Content-Type": "application/json" } });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Audit failed.";
    return new Response(superjson.stringify({ error: message }), { status: 400, headers: { "Content-Type": "application/json" } });
  }
}
  222
