---
title: "Claude Skills V2 — A Skill System Evolved with Benchmarking and Automated Evaluation"
date: 2026-03-19
description: A breakdown of the key changes in Claude Code Skills V2. A built-in benchmarking system measures skill effectiveness numerically, and Skill Creator now automates everything from test case generation to iterative improvement. New frontmatter options and improved implicit triggering are also covered.
categories: ["developer-tools"]
tags: ["claude-code", "skills", "benchmarking", "evaluation", "anthropic", "skill-creator", "automation"]
image: "/images/posts/2026-03-19-claude-skills-v2/cover.jpg"
---

## Overview

Anthropic has announced a major update to Claude Code Skills. The most prominent change is the introduction of a **built-in benchmarking system**. You can now quantify whether a skill actually improves output quality through A/B testing, and Skill Creator V2 automates the entire lifecycle from test case generation through iterative improvement. New frontmatter options also provide fine-grained control over how skills execute.

<!--more-->

## Two Skill Categories: Capability Uplift vs. Inquiry Preference

Anthropic has formally divided skills into two categories.

### Capability Uplift Skills

Skills that enable the model to do something it fundamentally cannot do on its own. Specific API call patterns and external tool integrations fall here. This type of skill **may become unnecessary as the model improves** — once the model absorbs the capability itself, the skill is redundant.

### Inquiry Preference Skills

Skills that enforce a user's specific workflow or preferences. Examples: "always respond in Korean," "follow the security checklist on every PR review." This type **will never be deprecated**, because it captures requirements that are inherently user-specific, regardless of how powerful the model becomes.

```mermaid
flowchart TD
    A["Claude Code Skill"] --> B["Capability Uplift"]
    A --> C["Inquiry Preference"]
    B --> D["Enables functionality model can't do"]
    D --> E["May deprecate as model improves"]
    C --> F["Enforces user workflow"]
    F --> G["Never deprecated — user-specific requirement"]

    style B fill:#f9a825,stroke:#f57f17,color:#000
    style C fill:#42a5f5,stroke:#1565c0,color:#000
    style E fill:#ef5350,stroke:#c62828,color:#fff
    style G fill:#66bb6a,stroke:#2e7d32,color:#000
```

This classification matters because of the **benchmarking system** described next. Capability Uplift skills can be retired based on benchmark results when the model has absorbed the underlying capability.

## Benchmarking System: Proving a Skill's Value with Data

This is V2's flagship feature — a built-in evaluation system that **quantitatively measures** whether a skill actually improves output quality.

### How It Works

```mermaid
flowchart LR
    subgraph eval["A/B Test Execution"]
        direction TB
        A1["With skill"] --> R1["Result A"]
        A2["Without skill"] --> R2["Result B"]
    end

    subgraph judge["Score Comparison"]
        direction TB
        R1 --> SC["Score by evaluation criteria"]
        R2 --> SC
        SC --> V{"Score difference?"}
        V -->|"Meaningful difference"| KEEP["Keep skill"]
        V -->|"Similar scores"| DROP["Skill unnecessary — model already has it"]
    end

    eval --> judge

    style KEEP fill:#66bb6a,stroke:#2e7d32,color:#000
    style DROP fill:#ef5350,stroke:#c62828,color:#fff
```

**Multi-agent support** allows A/B tests to run simultaneously. One agent with the skill and one without perform the same task, and results are compared against evaluation criteria.

### Example Auto-Generated Evaluation Criteria

Seven criteria Skill Creator automatically generated for a social media post generation skill:

| # | Criteria | Description |
|---|----------|------|
| 1 | Platform coverage | Was a post generated for every specified platform? |
| 2 | Language match | Was it written in the requested language? |
| 3 | X character limit | Does the X (Twitter) post respect the character limit? |
| 4 | Hashtags | Were appropriate hashtags included? |
| 5 | Factual content | Is the content factually consistent with the source material? |
| 6 | Tone differentiation | Is the tone appropriately differentiated per platform? |
| 7 | Tone compliance | Does it follow the specified tone guidelines? |

If scores differ **meaningfully** with and without the skill, the skill has value. If scores are **similar**, the model already has the capability and the skill is unnecessary.

## Skill Creator V2: Automate the Full Lifecycle

With Skill Creator upgraded to V2, it goes beyond simple generation to **automate the entire skill lifecycle**.

### Installation and Usage

1. Run `/plugin`
2. Search for "skill creator skill" and install
3. Describe the desired skill in natural language
4. Automatic: skill generation → test case generation → benchmark execution → result review

### The Automated Loop

```mermaid
flowchart TD
    START["User: describe desired skill"] --> CREATE["Skill Creator generates skill"]
    CREATE --> EVAL["Auto-generate test cases"]
    EVAL --> BENCH["Run benchmark &lt;br/&gt; with skill vs without skill"]
    BENCH --> REVIEW{"User satisfied?"}
    REVIEW -->|"No"| IMPROVE["Improve based on feedback"]
    IMPROVE --> EVAL
    REVIEW -->|"Yes"| DONE["Skill complete"]

    style START fill:#42a5f5,stroke:#1565c0,color:#000
    style DONE fill:#66bb6a,stroke:#2e7d32,color:#000
    style BENCH fill:#f9a825,stroke:#f57f17,color:#000
```

Improving existing skills is also supported. Hand an existing skill to Skill Creator and it benchmarks current performance, identifies areas for improvement, and optimizes iteratively.

**Built-in progressive disclosure guidance** walks users through skill creation step by step, making it accessible even for those without prior skill-writing experience.

### Improved Implicit Triggering

Previous versions had reliability issues with implicit triggers (auto-execution without a slash command). V2 has the Skill Creator perform **description optimization** alongside skill generation, significantly improving implicit triggering accuracy. The skill's description is automatically refined to communicate more clearly to the model when to invoke it.

## New Frontmatter Options

New frontmatter options in V2 enable fine-grained control over skill behavior.

| Option | Description |
|------|------|
| `user_invocable: false` | Only the model can trigger it; users cannot invoke it directly |
| `user_enable: false` | Users cannot invoke it via slash command |
| `allow_tools` | Restrict which tools the skill can use |
| `model` | Specify the model to run the skill with |
| `context: fork` | Run the skill in a sub-agent |
| `agents` | Define sub-agents (requires `context: fork`) |
| `hooks` | Define per-skill hooks in YAML format |

The `context: fork` + `agents` combination is particularly interesting. It delegates skill execution to a separate sub-agent, so the skill works independently without contaminating the main context. The benchmarking system's multi-agent A/B test also runs on this foundation.

`user_invocable: false` is useful for creating "background skills" that aren't exposed to users and are invoked internally by the model based on its own judgment.

## Quick Links

- [Claude Skills V2 update video](https://www.youtube.com/watch?v=t81f188Tvec)
- [Claude Code official docs](https://docs.anthropic.com/en/docs/claude-code)
- [Anthropic official site](https://www.anthropic.com)

## Insights

The core of this V2 update is that **the effectiveness of a skill can now be measured objectively**.

Until now, skills operated on the assumption that "adding a skill will make things better." With built-in benchmarking, you can finally determine with data whether a skill actually improves output quality, or whether you're adding unnecessary prompt overhead on top of something the model already handles well.

The **Capability Uplift vs. Inquiry Preference** classification is equally practical. Instead of treating all skills identically, it provides a framework for distinguishing skills that should naturally be retired as the model advances from skills that should be maintained permanently.

Skill Creator V2 automating the generation-evaluation-improvement loop dramatically lowers the barrier to entry. Skill writing used to be squarely in the domain of prompt engineering. Now you just describe what you want, and an optimized, benchmark-validated skill comes out the other end. The skill ecosystem is set to grow rapidly in both quantity and quality.
