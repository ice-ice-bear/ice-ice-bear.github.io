---
title: "Creative Agent Studio #6 — 라이브 게이트 마커, 그리고 내보내기 파이프라인 R&D"
description: SSE 스트림에서 진행 중인 게이트 단계를 정확히 표시하는 라이브 게이트 마커 버그를 잡고 Typst 기반 pptx 내보내기와 Firebase 인증을 착수한 개발 일지
date: 2026-05-29
image: "/images/posts/2026-05-29-creative-agent-studio-dev6/cover-ko.jpg"
series: "creative-agent-studio"
series_num: 6
last_commit: "12b6bff"
categories: ["tech-log"]
tags: ["creative-agent-studio", "react", "zustand", "sse", "typst", "firebase"]
toc: true
math: false
---

## 개요

오늘 Creative Agent Studio(diffs 챗 파이프라인)에서 실제로 merge한 건 **라이브 게이트 마커** 버그 6개 커밋이다. 멀티 에이전트 파이프라인이 게이트 단계를 통과하는 동안, 피드 UI가 "지금 어느 게이트를 진행 중인지"를 한 박자 늦게 보여주던 문제를 끝까지 추적해 잡았다. 그 외에 두 갈래가 더 진행 중이다 — 기획서·콘티를 pptx/pdf로 뽑는 **내보내기 파이프라인 R&D**(작업 트리, 아직 미커밋)와 별도 브랜치에 올린 **Firebase 인증** 작업이다.

[이전 글: #5 — Observability & UX Patterns](/posts/2026-05-28-creative-agent-studio-dev5/)

<!--more-->

---

## 라이브 게이트 마커: 두 박자 늦은 UI

### 배경

파이프라인은 GATE 1~5를 거치며 진행되고, 백엔드는 SSE로 `task_update`와 `gate_emit` 이벤트를 흘려보낸다. 피드의 `TaskUpdateNote` 컴포넌트는 이 이벤트들을 읽어 "현재 진행 게이트"를 마커로 표시한다. 그런데 화면상으로는 Gate 5(스토리보드)를 *생성 중*인데도 Gate 4가 계속 `ready` 상태로 비치는 문제가 스크린샷으로 잡혔다.

```mermaid
graph LR
    BE["백엔드 SSE"] -->|"task_update / gate_emit"| DISPATCH["dispatch-sse.ts"]
    DISPATCH -->|"sessionId 결정"| STORE["zustand store"]
    STORE --> NOTE["TaskUpdateNote (liveGate 계산)"]
    NOTE --> UI["피드 게이트 마커"]
```

### 문제 해결 1 — sessionId 드리프트

먼저 표시 로직 자체는 옳았다. 입력값이 문제였다. `dispatch-sse.ts:128`의 한 줄이 범인이었다.

```ts
// before
const sessionId = opts.sessionId ?? store.activeSessionId ?? undefined
```

`opts.sessionId`가 `undefined`인 상태에서, 두 이벤트 사이에 `store.activeSessionId`가 `null`→실제 id로 바뀌면 마커 id가 도중에 바뀌어 버린다(드리프트). 원인을 끝까지 파보니 — `addSession` 직후 `selectSession(created.id)`가 **동기로** 실행돼 `activeSessionId`가 즉시 박힌다. 그래서 세션이 한 번 생기고 나면 그 다음 submit부터는 항상 실제 id를 캡처하고, *세션 생성 직전 찰나*에 시작된 첫 스트림만 `undefined`를 잡는다. 즉 버그는 신규 세션의 "막 만든 직후 찰나"에만 생기고, 불러온 과거 세션에선 발생하지 않는다.

해결은 폴백 자체를 제거하는 한 줄 수정이었다.

```ts
// after — activeSessionId 폴백 제거
const sessionId = opts.sessionId ?? undefined
```

먼저 이 시나리오를 재현하는 회귀 테스트(`dispatch-sse-storyboard.test.ts`)를 작성해 버그를 고정한 뒤 고쳤다. 전체 스위트 79 파일 / 489 테스트 통과, 타입체크 클린.

### 문제 해결 2 — liveGate가 한 박자 뒤처짐

수정 이후에도 스크린샷에서 Gate 5 생성 중에 Gate 4가 여전히 `ready`로 보였다. 트레이스해 보니 진짜 빈틈은 여기였다 — 스토리보드 생성 중에는 아직 `final` `gate_emit`이 안 떴고, `session.gate`/`project.gate`도 시나리오 승인 시점의 4에 멈춰 있다. 그래서 내가 앞서 만든 `liveGate = max(gate_emit들)`이 5에 도달하지 못해, Gate 4가 진행 표시로 넘어가지 못했다. 한마디로 **`liveGate`가 한 박자 뒤처져 있었다.**

해결: Gate 5(스토리보드) `task_update` 마커가 존재하면, `final` `gate_emit`이 없고 게이트가 4에 멈춰 있어도 Gate 4 마커를 "Done"으로 읽도록 `TaskUpdateNote`를 보강했다. 이 정확한 시나리오에 대한 회귀 테스트(`live-gate-marker-regression.test.tsx`, `FeedItem.test.tsx`)를 추가했다. 더불어 스트림이 게이트에서 끝날 때 남아 있는 에이전트들을 마무리(finalize)하도록 `use-chat-stream.ts`와 `workspace` 슬라이스도 손봤다.

---

## 진행 중: 내보내기 파이프라인 (Typst over LibreOffice)

오늘 가장 긴 세션(약 2.5시간)은 기획서·콘티를 LLM 에이전트가 만들기 쉬운 형태로 가공하고 pptx/pdf로 변환하는 **내보내기 파이프라인** R&D였다. WeasyPrint, Slidev, Typst, LibreOffice를 비교한 끝에 — LibreOffice는 의존성이 너무 무거워 탈락 — **Typst**를 PDF 조판 백엔드로, python-pptx류를 네이티브 pptx 경로로 두는 방향을 잡았다. 작업 트리에 `runtime/export/`(render-pptx.js, render-typst.js, planning-deck.js, convert-pdf.js, pack.js), 토큰 팩(`templates/` — creative-warmth, keynote-minimal-fullbleed, consulting-precision-grid, conti-grid), 그리고 `ExportMenu.tsx` + `server/routes/export.js`를 깔았다. 아직 미커밋 상태라 이번 #6의 커밋 로그에는 빠져 있다. (이 주제는 [오늘의 슬라이드 생성 도구 탐색 글](/posts/2026-05-29-the-ai-slide-generation-rabbit-hole/)과 정확히 맞물린다.)

## 진행 중: Firebase 인증

또 하나의 갈래는 로그인 기능과 사용자별 데이터 관리를 Firebase로 붙이는 작업이다. `/plan`으로 설계를 잡고 구현을 시작했으며, main을 건드리지 않으려고 별도 브랜치에 올린 뒤 main으로 복귀했다. 마지막 짧은 세션에서 auth 미들웨어(`tests/api-auth-middleware.test.js`, 인증 컴포넌트)에 대한 보안 리뷰도 돌렸다. 이 역시 브랜치 작업이라 #6 커밋 로그에는 포함되지 않는다.

## 인프라: EventBridge / EC2 크론 검증

하루의 시작은 Terraform으로 EventBridge에 걸어둔 EC2 서버 크론 스케줄이 올바르게 반영됐는지 검증하는 일이었다 — 어제 EC2가 언제까지 켜져 있었는지, 적용한 스케줄이 의도대로 동작했는지 확인했다.

---

## 커밋 로그

| 메시지 | 변경 파일 |
|--------|-----------|
| show live gate marker for the in-progress stage before its gate | TaskUpdateNote.tsx, pipeline.ts, +회귀 테스트 2 |
| finalize lingering agents when the live stream ends at a gate | use-chat-stream.ts, workspace 슬라이스, +테스트 |
| enhance TaskUpdateNote logic to accurately reflect live gate | TaskUpdateNote.tsx, FeedItem.test.tsx |
| enhance TaskUpdateNote and FeedItem tests for accurate gate | TaskUpdateNote.tsx, dispatch-sse.ts, FeedItem.test.tsx |
| enhance storyboard tests to validate gate-5 marker behavior | dispatch-sse-storyboard.test.ts |
| update agent working hints for clarity | ApproveBar.tsx |

---

## 인사이트

게이트 마커 버그는 "UI가 틀렸다"가 아니라 "UI에 들어가는 입력이 한 박자 늦거나 도중에 바뀐다"는, SSE 기반 실시간 UI의 전형적인 함정이었다. 두 버그 모두 표시 로직이 아니라 *상태의 타이밍*이 원인이었다는 점이 핵심이다 — 하나는 `activeSessionId`가 비동기 흐름 중간에 채워지는 레이스, 다른 하나는 `gate_emit`의 `final`이 늦게 떠서 파생 상태(`liveGate`)가 진실보다 뒤처지는 지연. 실시간 파생 상태를 다룰 땐 "지금 값"이 아니라 "이미 도착한 이벤트들의 누적 최댓값"으로 계산하되, 그 최댓값을 *언제* 신뢰할 수 있는지(어떤 마커가 떴을 때)를 명시적으로 끌어올려야 한다는 교훈이다. 한편 내보내기 파이프라인에서 LibreOffice를 무게 때문에 버리고 Typst로 기운 결정은, 오늘 브라우징에서 따로 도달한 결론과 정확히 일치했다 — 도구 선택의 같은 중력장에 두 번 끌려간 셈이다.
