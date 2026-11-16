import { defineCollection } from "astro:content";
import { z } from "astro/zod";
import { glob } from "astro/loaders";

// One entry per project. Every project page uses the same case template (src/pages/work/[id].astro).
const work = defineCollection({
  loader: glob({ pattern: "**/*.mdx", base: "./src/content/work" }),
  schema: z.object({
    title: z.string(),
    summary: z.string(), // one or two lines for Home and Work lists
    fig: z.string(), // margin figure on lists
    figLabel: z.string(),
    order: z.number(),
    featured: z.boolean().default(false), // shown on Home
    status: z.enum(["full", "stub"]),
    area: z.string(), // crumb label, e.g. Evals, Adoption
    lede: z.string(),
    ledeMark: z.string().optional(), // phrase in the lede to highlight
    facts: z.array(z.object({ k: z.string(), v: z.string() })),
    description: z.string(),
  }),
});

const writing = defineCollection({
  loader: glob({ pattern: "**/*.md", base: "./src/content/writing" }),
  schema: z.object({
    title: z.string(),
    summary: z.string(),
    order: z.number(),
    published: z.boolean().default(false),
  }),
});

export const collections = { work, writing };
