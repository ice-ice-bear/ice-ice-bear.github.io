---
title: "Netflix VOID — Interaction-Aware Video Object Deletion"
date: 2026-04-16
image: "/images/posts/2026-04-16-netflix-void-model/cover-en.jpg"
description: Netflix VOID removes objects from videos along with their physical interactions using a two-pass CogVideoX pipeline with quadmask encoding
categories: ["Technology"]
tags: ["void", "netflix", "video-inpainting", "computer-vision", "cogvideox"]
slug: "2026-04-16-netflix-void-model"
---

## Overview

VOID — Video Object and Interaction Deletion — is a research project from Netflix and INSAIT that tackles a problem traditional video inpainting ignores: what happens to the physical world when you remove an object? If a person holding a guitar is removed from a scene, existing methods leave a floating guitar or fill the region with a blurry guess. VOID removes both the object and its physical interactions, so the guitar falls naturally. Built on CogVideoX and fine-tuned for interaction-aware inpainting, VOID uses a two-pass system with quadmask encoding to achieve temporally consistent results. The project has earned 1,598 GitHub stars.

<!--more-->

## Two-Pass Pipeline

VOID's core architecture is a two-pass refinement system that addresses both spatial accuracy and temporal consistency. Pass 1 performs base inpainting — removing the target object and filling the region with plausible content. This pass handles the fundamental question of what should exist in the space the object occupied, including resolving interaction dependencies.

Pass 2 applies warped-noise refinement for temporal consistency. Video inpainting is fundamentally harder than image inpainting because filled regions must be consistent across frames. A single-pass approach often produces results that flicker, shift, or contain subtle temporal artifacts. The warped-noise refinement in Pass 2 takes the base inpainting result and refines it by propagating noise patterns that are warped according to the video's optical flow, ensuring that the filled regions evolve naturally over time.

This two-pass design is a practical engineering decision. Attempting to optimize for both spatial accuracy and temporal consistency simultaneously creates competing objectives that degrade both. By separating the concerns, each pass can focus on its primary objective while building on the other's output.

```mermaid
flowchart LR
    A["Video"] --> B["Point Selection"]
    B --> C["SAM2 + VLM&lt;br/&gt;Mask Generation"]
    C --> D["Pass 1&lt;br/&gt;Base Inpainting"]
    D --> E["Pass 2&lt;br/&gt;Warped-Noise Refinement"]
    E --> F["Clean Video"]
```

## Quadmask Encoding

The quadmask encoding system is perhaps VOID's most technically distinctive contribution. Rather than using a simple binary mask (remove vs. keep), VOID segments the scene into four semantic regions: the primary object to be removed, the overlap zone where the object contacts other objects, the affected region where physical interactions will change, and the background that remains static.

This four-region decomposition gives the model explicit information about the physics of the scene. The overlap zone is where interaction-aware inpainting happens — the model knows that objects in this region were physically supported by or connected to the removed object. The affected region captures the cascade of physical consequences: if a person holding a tray is removed, the tray enters the affected region and the model must determine what happens to it physically.

Traditional binary masks treat removal as a simple fill operation. Quadmask encoding transforms it into a physics-informed synthesis problem, where the model has the semantic context to make physically plausible decisions about how the remaining scene should evolve.

## Mask Generation with SAM2 and Gemini VLM

Generating accurate quadmasks requires understanding both spatial boundaries and semantic relationships. VOID combines SAM2 (Segment Anything Model 2) for precise spatial segmentation with Gemini VLM (Vision-Language Model) for semantic understanding of object interactions.

SAM2 provides the initial object segmentation — given a point selection on the target object, it generates precise per-frame masks that track the object through the video. However, SAM2 alone cannot determine which parts of the scene are physically interacting with the target object. This is where Gemini VLM contributes: it analyzes the scene to identify interaction zones, contact points, and affected regions, providing the semantic layer that transforms a binary mask into the four-region quadmask.

This hybrid approach is effective because it plays to each model's strength. SAM2 excels at spatial precision but lacks semantic understanding of physical interactions. VLMs understand scene semantics but lack pixel-level precision. Together, they produce masks that are both spatially accurate and semantically informed.

## Hardware Requirements and Limitations

VOID requires 40GB+ VRAM, placing it firmly in the research and professional production category rather than consumer use. This requirement stems from the CogVideoX foundation model's size combined with the additional parameters for interaction-aware inpainting. The two-pass pipeline also means that inference time is roughly doubled compared to single-pass approaches.

These requirements are not unusual for state-of-the-art video generation models, but they do limit the deployment context. Professional video production studios with access to high-end GPUs are the primary audience. Real-time or near-real-time applications are not feasible with current hardware requirements.

The authors from Netflix and INSAIT position the work as a research contribution with production implications rather than a ready-to-deploy product. The key insight — that interaction-aware removal requires explicit physical reasoning through quadmask encoding — is likely to influence future video editing tools even if this specific implementation remains resource-intensive.

## Insights

VOID addresses a gap that becomes obvious once named: removing objects from video without removing their physical effects produces uncanny results. The quadmask encoding approach is the key innovation — by giving the model explicit semantic regions for physical interactions, it transforms inpainting from a texture synthesis problem into a physics-informed generation problem. The two-pass architecture is a pragmatic solution to the competing objectives of spatial accuracy and temporal consistency. While the 40GB+ VRAM requirement limits current accessibility, the conceptual framework will likely propagate to more efficient architectures. For video production teams, this represents the kind of capability that could fundamentally change post-production workflows once the computational requirements decrease.
