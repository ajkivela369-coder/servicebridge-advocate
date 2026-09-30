import { z } from "zod";
import superjson from "superjson";

export const schema = z.object({
  url: z.string().url().max(2048),
});

export type InputType = z.infer<typeof schema>;

export type AuditCheck = {
  key: string;
  label: string;
  status: "pass" | "critical" | "high" | "medium" | "opportunity";
  finding: string;
  why: string;
  points: number;
  maxPoints: number;
};

export type OutputType = {
  url: string;
  finalUrl: string;
  statusCode: number;
  title: string | null;
  metaDescription: string | null;
  canonical: string | null;
  robots: string | null;
  language: string | null;
  wordCount: number;
  headings: { h1: string[]; h2: string[]; h3: string[] };
  links: { internal: number; external: number; emptyAnchors: number };
  images: { total: number; withAlt: number; altCoveragePercent: number };
  structuredDataTypes: string[];
  wordpressDetected: boolean;
  seoScore: number;
  geoScore: number;
  checks: AuditCheck[];
};

export const postAudit = async (body: InputType, init?: RequestInit): Promise<OutputType> => {
  const validated = schema.parse(body);
  const result = await fetch("/_api/audit", {
    method: "POST",
    body: superjson.stringify(validated),
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  if (!result.ok) {
    const errorObject = superjson.parse<{ error: string }>(await result.text());
    throw new Error(errorObject.error);
  }
  return superjson.parse<OutputType>(await result.text());
};
   54
