---
title: "OpenAI 2026-05-07 발표 5건 디지스트 — Cyber 모델, ChatGPT 광고, Trusted Contact, Realtime 음성, MRC 네트워크"
description: 같은 날 한 번에 풀린 OpenAI 5건의 발표를 모델·API·제품 정책·인프라 4계층으로 정리한 디지스트
date: 2026-05-07
image: "/images/posts/2026-05-07-openai-2026-05-07-announcement-digest/cover-ko.jpg"
categories: ["ai"]
tags: ["openai", "gpt-5-5", "cybersecurity", "chatgpt", "voice-ai", "infrastructure"]
toc: true
math: false
---

## 개요

OpenAI가 같은 일자에 5건의 공식 발표를 동시에 풀었다. 묶어서 보면 모델·API·제품 정책·인프라 4개 레이어를 한 번에 친 형태다. 각각 따로 읽으면 평범한 발표지만, **묶었을 때 OpenAI가 어디에 자원을 쏟고 있는지** 가 드러난다.

<!--more-->

```mermaid
graph TD
    Day["OpenAI 2026-05-07"] --> Model["모델 레이어"]
    Day --> API["API 레이어"]
    Day --> Product["제품 정책"]
    Day --> Infra["인프라"]

    Model --> Cyber["GPT-5.5-Cyber &lt;br/&gt; Trusted Access"]
    API --> Voice["Realtime-2 / Translate / Whisper"]
    Product --> Ads["ChatGPT 광고 한국 확장"]
    Product --> Trust["Trusted Contact"]
    Infra --> MRC["MRC 슈퍼컴 네트워킹"]
```

## 1. GPT-5.5 + GPT-5.5-Cyber — Trusted Access for Cyber

[원문](https://openai.com/index/gpt-5-5-with-trusted-access-for-cyber)

2주 전 풀린 GPT-5.5에 더해 **GPT-5.5-Cyber** 가 limited preview로 공개됐다. 핵심 인프라 방어자 대상.

Trusted Access for Cyber(TAC)는 신원·신뢰 기반 프레임워크다. 검증된 방어자에게는 분류기 거부율을 낮춰 취약점 트리아지·악성코드 분석·바이너리 리버스·탐지 엔지니어링·패치 검증 같은 작업을 풀어준다.

**3단계 액세스:**
- **GPT-5.5 (default)** — 일반 안전장치
- **GPT-5.5 with TAC** — 인증된 방어 작업용 안전장치 완화
- **GPT-5.5-Cyber** — 가장 허용적, 인가된 red teaming/pentest용

2026-06-01부터 TAC 사용자는 phishing-resistant Advanced Account Security 의무화. 조직은 SSO 차원에서 attest 가능.

> "AI를 보안 공격에 쓰면 어떡하지" 우려에 대한 OpenAI식 답이다. 원천 차단 대신 **신원 확인된 화이트리스트만 더 풀어주는 방식** 으로 정책을 분화했다.

## 2. ChatGPT 광고 — 한국 확장

[원문](https://openai.com/index/testing-ads-in-chatgpt)

2026-02-09 미국에서 시작한 광고 파일럿이 5월부로 **영국·멕시코·브라질·일본·한국**으로 확장된다.

| 항목 | 내용 |
|---|---|
| 적용 대상 | 로그인한 성인의 Free / Go 티어 |
| 미적용 | Plus / Pro / Business / Enterprise / Education |
| 광고 영향 | 답변에 영향 없음, 별도 라벨링 |
| 광고주 권한 | 대화·메모리·개인정보 접근 불가, 집계 통계만 수신 |
| 옵트아웃 | Free 티어에서 일일 무료 메시지 수 감소 대가로 가능 |
| 노출 제외 | 18세 미만 추정 계정, 건강/정신건강/정치 토픽 근처 |

**한국이 직접 영향권에 들어왔다.** AI 무료 사용자의 비즈니스 모델이 광고 기반으로 이행하는 첫 큰 전환점이다.

## 3. Trusted Contact in ChatGPT

[원문](https://openai.com/index/introducing-trusted-contact-in-chatgpt)

자해/심각한 안전 우려가 감지되면, 사용자가 **미리 지정한 1인의 신뢰할 수 있는 어른**에게 알림이 가는 옵트인 기능. 18+ 글로벌, **한국은 19+** 로 적용된다.

**흐름:**
1. 자동 모니터링 → 사용자에게 "Trusted Contact에게 알릴 수도 있다" 고지
2. 전담 인간 검토팀이 1시간 이내 검토
3. 이메일/SMS/in-app 알림 발송
4. 알림 내용은 의도적으로 제한적 — 구체 대화 내용·트랜스크립트는 포함하지 않음

기존 부모 알림 기능(미성년 계정용)을 성인까지 확장한 형태. AI가 단순 응답에서 **실세계 인적 안전망과 연결하는 매개** 로 역할이 확대된다.

## 4. Realtime 음성 모델 3종 — GPT-Realtime-2 / Translate / Whisper

[원문](https://openai.com/index/advancing-voice-intelligence-with-new-models-in-the-api)

가장 개발자 직접 영향이 큰 발표다. 3개 모델이 동시에 공개됐다.

### GPT-Realtime-2
- **컨텍스트 32K → 128K** 로 4배 확장 (긴 agentic workflow)
- Preambles ("잠시만요, 확인해볼게요" 같은 짧은 도입어), 병렬 tool call + tool transparency, recovery 동작 강화
- 추론 강도 5단계 선택 (minimal / low / medium / high / xhigh, default = low)
- Big Bench Audio +15.2%, Audio MultiChallenge +13.8% 향상

### GPT-Realtime-Translate
- 입력 70+ 언어 / 출력 13개 언어 실시간 번역 + 트랜스크립션
- BolnaAI 케이스: 힌디·타밀·텔루구에서 WER −12.5%

### GPT-Realtime-Whisper
- 저지연 스트리밍 STT — 회의/방송/교실 자막용

### 가격 (Realtime API)
| 모델 | 가격 |
|---|---|
| GPT-Realtime-2 | $32 / 1M audio input, $64 / 1M audio output, cached input $0.40 / 1M |
| GPT-Realtime-Translate | $0.034 / min |
| GPT-Realtime-Whisper | $0.017 / min |

보이스 에이전트 빌더가 더 빠르고 똑똑한 모델을 즉시 쓸 수 있게 됐다. **128K context와 parallel tool call이 진짜 중요** — 이게 있어야 길고 복잡한 voice agent flow가 끊기지 않는다.

## 5. MRC — OpenAI 슈퍼컴퓨터 네트워킹

[원문](https://openai.com/index/mrc-supercomputer-networking)

가장 깊이 있는 엔지니어링 글이다. **MRC(Multipath Reliable Connection)** 는 800Gb/s 네트워크 인터페이스에 내장된 새 프로토콜로, RoCE를 SRv6 source routing으로 확장한다.

**핵심 아이디어 3가지:**

1. **Multi-plane 토폴로지** — 800Gb/s 인터페이스를 100Gb/s × 8개로 쪼개 8개 병렬 plane. 64포트 800G 스위치 = 512포트 100G로 사용 → **131K GPU를 2-tier 스위치로** 연결 가능 (기존엔 3-4 tier 필요).

2. **Packet spraying** — 한 transfer를 단일 경로가 아니라 수백 경로에 spray. 패킷이 out-of-order 도착해도 final memory address가 헤더에 있어서 destination에서 정렬.

3. **SRv6 source routing** — BGP 같은 dynamic routing 폐기. 송신자가 IPv6 주소에 경로를 인코딩, 스위치는 자기 ID만 확인하고 다음으로 forward. 정적 라우팅 테이블만 유지.

**결과:** 링크 fail이 분당 여러 번 일어나도 동기 학습에 측정 가능한 영향 없음. tier-1 스위치 4대 reboot도 학습팀과 협의 없이 진행 가능. AMD / Broadcom / Intel / Microsoft / NVIDIA 협업, OCP에 기여 (오픈). 이미 NVIDIA GB200 Stargate (OCI Abilene, Texas) + Microsoft Fairwater에 배포 완료.

**AI training의 병목이 GPU에서 네트워크로 옮겨가는 시대의 인프라 표준.** frontier model 학습은 단일 회사 작품이 아니라 **chip + switch + protocol 5사 컨소시엄**의 결과물이 됐다.

## 묶어서 본 패턴

OpenAI 단일 일자 발표 5건이 정확히 4개 레이어를 하나씩 친 형태:

```mermaid
flowchart LR
    A["모델 레이어"] --> B["GPT-5.5-Cyber"]
    C["API 레이어"] --> D["Realtime-2 / Translate / Whisper"]
    E["제품 정책"] --> F["광고 한국 / Trusted Contact"]
    G["인프라 레이어"] --> H["MRC + Multi-plane + SRv6"]
```

"오늘 OpenAI가 뭐 했어?" 라는 질문에 한 줄로 답한다면: **"보안 모델 풀고, 광고 한국에 풀고, 자해 안전망 풀고, 음성 모델 풀고, 슈퍼컴 네트워크 표준 풀었다."**

## 인사이트

다섯 발표가 같은 시각에 나왔다는 점 자체가 메시지다. OpenAI는 이제 **동시에 4개 레이어를 끌고 가는 풀 스택 회사** — 모델만 잘 만드는 회사가 아니라 모델·API·정책·인프라를 모두 자기 표준으로 시장에 박는 회사다. 한국 시장에는 광고와 Trusted Contact(19+) 두 곳에서 직접 영향이 들어왔고, 개발자에게는 Realtime 음성 3종이 즉시 돈 버는 플레이가 됐다. MRC가 OCP에 기여로 풀린 것은 인프라 표준의 주도권 쟁탈전을 시작했다는 신호 — 단일 회사 작품을 넘어 chip + switch + protocol 컨소시엄을 자기 중심으로 모은다. **다음 분기 가장 빠르게 변할 영역은 보이스 에이전트 빌더 시장**이다. GPT-5.5-Cyber는 진영 분화의 첫 사례이고, 이후 다른 도메인(법무·의료)에서도 유사 trusted-access 패턴이 나올 가능성이 높다.
