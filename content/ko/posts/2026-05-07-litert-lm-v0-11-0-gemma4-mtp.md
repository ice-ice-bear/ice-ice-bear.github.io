---
title: "LiteRT-LM v0.11.0 — Gemma 4 MTP로 모바일 GPU 디코드 2배, Windows 네이티브 지원"
description: Google의 LiteRT-LM v0.11.0 릴리스가 Gemma 4 Multi-token Prediction과 Windows 네이티브 지원을 추가하며 온디바이스 LLM 추론을 한 단계 끌어올린다
date: 2026-05-07
image: "/images/posts/2026-05-07-litert-lm-v0-11-0-gemma4-mtp/cover-ko.jpg"
categories: ["ai"]
tags: ["google", "litert", "gemma", "on-device", "mobile-gpu", "mtp", "edge-ai"]
toc: true
math: false
---

## 개요

Google의 온디바이스 LLM 런타임 [LiteRT-LM](https://ai.google.dev/edge/litert-lm)이 [v0.11.0](https://github.com/google-ai-edge/LiteRT-LM/releases/tag/v0.11.0)을 풀었다. 핵심 두 가지: Gemma 4를 위한 **Single Position Multi-token Prediction (MTP)** 으로 모바일 GPU 디코드 속도가 2배 이상 빨라졌고, **Windows 네이티브**(CPU + GPU)가 처음으로 정식 지원된다. 같은 시기 워크스테이션 진영(DGX Spark + Qwen3.5)에서도 MTP-2가 +36% 속도를 보여준 만큼, MTP가 모바일부터 워크스테이션까지 가로지르는 **공통 디코드 가속 기법**으로 빠르게 표준화되는 흐름이 보인다.

<!--more-->

```mermaid
graph TD
    Input["입력 위치 t"] --> Target["Gemma 4 타겟 모델"]
    Input --> Drafter["MTP Drafter &lt;br/&gt; (lightweight)"]
    Drafter --> Draft["draft 토큰 t+1, t+2, ..., t+k"]
    Draft --> Verify["타겟 모델 1회 forward로 검증"]
    Target --> Verify
    Verify --> Accept["일치하는 prefix 채택 &lt;br/&gt; + 1개 추가 생성"]
    Accept --> Output["다중 토큰을 단일 step에 emit"]
```

## 1. Gemma 4 Multi-token Prediction 지원

[릴리스 노트](https://github.com/google-ai-edge/LiteRT-LM/releases/tag/v0.11.0)의 첫 줄: **"모바일 GPU에서 디코드 속도 2배 이상, 품질 저하 zero"**. 그 뒤 메커니즘은 [Gemma 4용 MTP를 다룬 Google 블로그](https://blog.google/innovation-and-ai/technology/developers-tools/multi-token-prediction-gemma-4/)와 [공식 문서](https://ai.google.dev/edge/litert-lm/models/gemma-4)에 정리돼 있다.

핵심은 **speculative decoding의 변형**이다.

- 한 위치(single position)에서 lightweight **drafter**가 미래 여러 토큰을 한 번에 예측
- 큰 **target 모델**(예: Gemma 4 26B/31B)이 한 번의 forward로 draft sequence 전체를 검증
- target이 동의하면 prefix 전체 채택 + 추가 토큰 1개를 자체 생성

표준 LLM 추론이 **memory-bandwidth bound** 라서 대부분의 사이클이 파라미터 전송에 쓰이는데, MTP는 같은 메모리 패스에서 더 많은 토큰을 뽑아내는 식으로 이 병목을 비튼다.

**플랫폼별 가속:**

| 플랫폼 | 백엔드 | 속도 향상 |
|---|---|---|
| 모바일 GPU (Samsung S26 Ultra, iPhone 17 Pro 등) | GPU | 최대 2.2× decode |
| 모바일 CPU | CPU | 최대 1.5× decode |
| Apple Silicon (M4 MacBook Pro) | CPU + SME | 큰 개선 (batch 4–8에서 약 2.2×) |
| NVIDIA RTX PRO 6000 (26B) | GPU | 약 50% latency 감소 |
| NVIDIA RTX 4090 / Linux ARM | GPU | 일관된 가속 |

**중요 디테일** — GPU 워크로드에서는 universally 권장, E4B는 CPU에서도 권장. **E2B는 CPU에서 freeform 생성 시 약간 느려질 수 있음** — rewrite/summarization/coding 같이 input prefix가 긴 태스크에선 여전히 이득.

지원 모델은 [`Gemma-4-E2B`](https://ai.google.dev/edge/litert-lm/models/gemma-4) (2.58 GB) / `Gemma-4-E4B` (3.65 GB)가 우선이고 26B A4B, 31B는 곧.

## 2. Windows 네이티브 지원

[LiteRT-LM CLI](https://ai.google.dev/edge/litert-lm/cli)가 Windows에서 **CPU와 GPU 백엔드 모두** 네이티브로 동작한다. 이전엔 Linux/macOS/Android 위주라 Windows 개발자는 WSL을 거쳐야 했다.

```bash
litert-lm run --from-huggingface-repo=litert-community/gemma-4-E2B-it-litert-lm
```

명시되지 않은 의도가 분명히 보인다 — **워크스테이션/노트북 개발자를 곧장 끌어들이는 이동 경로**다. Android 디바이스 없으면 손대기 어렵던 진입 장벽이 사라진다.

## 3. LiteRT 스택 — TF Lite의 후속

조금 떨어져서 보면 이게 어디 들어맞는지 보인다.

- **TensorFlow Lite**(이전 이름) → [LiteRT](https://ai.google.dev/edge/litert) (Light Runtime, 2024 리브랜드)
- **LiteRT-LM** = LLM에 특화된 LiteRT 변형
- 모델 패밀리: [Gemma](https://ai.google.dev/gemma) — Google의 오픈 가중치 LLM
- 타겟: **온디바이스 추론** — 모바일, 엣지, 임베디드, 데스크톱

Apache 2.0 라이선스. CPU + GPU + (Apple Silicon에서) SME 백엔드. Hugging Face와 직접 연결되는 [`litert-community`](https://huggingface.co/litert-community) 레포.

## 4. MTP가 표준이 되는 중

흥미로운 건 MTP가 한 회사 / 한 모델 패밀리의 트릭이 아니라는 점이다.

- 며칠 전 [albond DGX Spark + Qwen3.5 포스트](#)에서도 **MTP-2** 가 +36% 디코드 속도를 보여줬다 — 워크스테이션 클래스 GPU에서.
- Gemma 4 + LiteRT-LM은 같은 아이디어를 **모바일 GPU에서 2.2×**로 뽑아낸다.
- 두 케이스 모두 **품질 저하 zero** — target 모델이 최종 검증을 하기 때문.

MTP가 자리잡는 위치는 **inference-time 가속의 사실상 표준**이다. transformer attention이 표준이 됐듯, 향후 1년 안에 거의 모든 production decoder에 어떤 형태로든 들어갈 가능성이 높다.

## 5. 클라우드와 엣지의 동시 발전

같은 날 OpenAI는 [Realtime 음성 모델 3종](https://openai.com/index/advancing-voice-intelligence-with-new-models-in-the-api)과 [MRC 슈퍼컴 네트워킹](https://openai.com/index/mrc-supercomputer-networking)을 풀었고, 같은 날 Google은 LiteRT-LM v0.11.0을 풀었다. 한쪽은 **단일 회사가 5사 컨소시엄을 이끌고 슈퍼컴 표준을 만드는** 그림, 다른 한쪽은 **한 손에 들어가는 디바이스에서 LLM이 production-ready로 돌아가게 만드는** 그림. 양쪽 다 production-ready라는 점이 핵심이다 — LLM은 더 이상 "클라우드 vs 엣지" 양자택일이 아니라 **둘 다 동시에 진보**하는 단계에 들어왔다.

## 인사이트

LiteRT-LM v0.11.0은 작은 마이너 릴리스처럼 보이지만 두 가지 시그널을 함께 던진다. 첫째, **MTP가 모바일 GPU까지 내려왔다는 건** speculative decoding 계열 기법이 더 이상 데이터센터의 사치가 아니라 **배터리·발열 예산 안에서 작동하는 표준 가속**이 됐다는 뜻이다. 둘째, **Windows 네이티브 지원**은 단순한 OS 추가가 아니라 LiteRT-LM이 모바일 데모 라이브러리에서 **개발자 진입 첫 화면**으로 위치를 옮겼다는 뜻이다. 같은 주에 Qwen3.5의 MTP-2와 Gemma 4의 MTP가 동시에 나온 건 우연이 아니라, **2026년 하반기에 디코드 속도 향상이 모델 크기 경쟁만큼 중요한 축**이 된다는 신호다. 클라우드 쪽이 GPT-Realtime-2 + MRC로 빠르게 가는 동안 엣지 쪽도 Gemma 4 + LiteRT-LM으로 같이 빠르게 가고 있고, 이는 **양 진영 모두에서 LLM이 production-ready로 동시에 들어가는** 첫 분기다. 한국 개발자 입장에서 가장 즉시 시도해볼 수 있는 건 Windows에서 `litert-lm run --from-huggingface-repo=litert-community/gemma-4-E2B-it-litert-lm` 한 줄로 시작하는 길이다.

## 참고

**Release**
- [google-ai-edge/LiteRT-LM v0.11.0 릴리스 페이지](https://github.com/google-ai-edge/LiteRT-LM/releases/tag/v0.11.0)
- [google-ai-edge/LiteRT-LM 저장소](https://github.com/google-ai-edge/LiteRT-LM)

**Model and runtime docs**
- [LiteRT 홈페이지 (ai.google.dev/edge/litert)](https://ai.google.dev/edge/litert)
- [LiteRT-LM 공식 문서](https://ai.google.dev/edge/litert-lm)
- [Gemma 4 with LiteRT-LM](https://ai.google.dev/edge/litert-lm/models/gemma-4)
- [LiteRT-LM CLI 문서](https://ai.google.dev/edge/litert-lm/cli)
- [Gemma 모델 패밀리](https://ai.google.dev/gemma)
- [TensorFlow Lite (LiteRT 전신)](https://www.tensorflow.org/lite)
- [Hugging Face — litert-community](https://huggingface.co/litert-community)

**MTP technique references**
- [Google: Multi-token Prediction for Gemma 4](https://blog.google/innovation-and-ai/technology/developers-tools/multi-token-prediction-gemma-4/)
- [Big Bench Audio / 일반 speculative decoding 배경](https://arxiv.org/abs/2211.17192)
- 워크스테이션 사례 비교: 같은 가족 기법 — DGX Spark에서 Qwen3.5 + MTP-2 +36% 디코드 속도 (이전 포스트)
