---
image: "/images/posts/2026-03-16-cmux-terminal/cover.jpg"
title: "cmux — AI 에이전트 시대를 위해 설계된 macOS 네이티브 터미널"
description: "cmux는 Ghostty의 libghostty를 렌더링 엔진으로 사용하는 macOS 네이티브 터미널로, 수직 탭과 알림 링으로 AI 코딩 에이전트 워크플로우를 최적화한다"
date: 2026-03-16
categories: ["developer-tools"]
tags: ["cmux", "terminal", "ghostty", "macos", "ai-agent", "developer-tools"]
toc: true
math: false
---

## 개요

AI 코딩 에이전트를 3~4개씩 동시에 돌리다 보면, 터미널 창이 폭발한다. iTerm2 탭이 15개, tmux 세션이 8개 — 어떤 에이전트가 입력을 기다리는지 찾느라 시간을 소모한다. [cmux](https://www.cmux.dev/)는 이 문제를 정면으로 해결하기 위해 설계된 macOS 네이티브 터미널이다.

<!--more-->

## 아키텍처: Ghostty 위의 새로운 레이어

```mermaid
graph TD
    A["cmux 앱 &lt;br/&gt; Swift + AppKit"] --> B["libghostty &lt;br/&gt; 터미널 렌더링 엔진"]
    A --> C["수직 탭 사이드바"]
    A --> D["알림 시스템 &lt;br/&gt; OSC 9/99/777"]
    A --> E["인앱 브라우저 &lt;br/&gt; 스크립터블 API"]
    A --> F["소켓 API &lt;br/&gt; CLI 자동화"]
```

cmux는 Ghostty의 **포크가 아니다**. libghostty를 라이브러리로 사용하는 별도의 앱이다 — WebKit을 사용하는 앱들이 Safari의 포크가 아닌 것과 같은 관계다. Mitchell Hashimoto(Ghostty + HashiCorp 창시자) 본인이 "또 하나의 libghostty 기반 프로젝트"라며 긍정적으로 언급했다.

GPU 가속 렌더링은 Ghostty에서 그대로 가져오므로 속도는 동일하다. 그 위에 cmux만의 레이어가 올라간다.

## 핵심 기능

### 수직 탭

사이드바에 탭이 수직으로 배치된다. 각 탭에는 git 브랜치, 작업 디렉토리, 포트, 알림 텍스트가 표시된다. Firefox의 수직 탭을 터미널에 적용한 것과 유사한 UX다.

### 알림 링

에이전트가 주의를 필요로 할 때:
1. **패인 알림 링**: 해당 패인 주변에 링이 표시
2. **사이드바 뱃지**: 읽지 않은 알림 카운트
3. **알림 팝오버**: 앱 내 알림
4. **macOS 데스크톱 알림**: 시스템 알림

표준 터미널 이스케이프 시퀀스(OSC 9/99/777)를 사용하므로 별도 설정 없이 동작한다. Claude Code hooks로도 트리거할 수 있다.

### 인앱 브라우저

터미널 옆에 브라우저를 분할 배치할 수 있다. PR 페이지나 문서를 브라우저에 띄워놓고, 옆에서 Claude Code가 작업하는 형태다. 스크립터블 API로 자동화도 가능하다.

### 분할 패인

수평/수직 분할을 각 탭 내에서 지원한다. tmux의 분할 기능과 유사하지만 GUI로 관리한다.

## tmux와의 차이

```mermaid
graph LR
    A["tmux"] --> B["어떤 터미널 안에서든 실행 &lt;br/&gt; prefix 키 기반 &lt;br/&gt; 설정 파일 필요 &lt;br/&gt; 서버/리눅스 지원"]
    C["cmux"] --> D["독립 macOS 앱 &lt;br/&gt; GUI 기반 &lt;br/&gt; 설정 없이 바로 사용 &lt;br/&gt; macOS 전용"]
```

| 구분 | tmux | cmux |
|------|------|------|
| 플랫폼 | 어디서든 (SSH 포함) | macOS 전용 |
| UI | TUI (텍스트) | 네이티브 GUI |
| 설정 | `.tmux.conf` 필수 | 설정 없이 바로 사용 |
| 내장 브라우저 | 없음 | 있음 (스크립터블) |
| 알림 | 없음 (recon 같은 도구 필요) | 내장 |
| 에이전트 호환 | 모든 에이전트 | 모든 에이전트 |

## 커뮤니티 반응

Google DeepMind Research Director Edward Grefenstette, Dagster 창시자 Nick Schrock, HashiCorp 창시자 Mitchell Hashimoto 등이 긍정적 피드백을 남겼다. 일본 개발자 커뮤니티에서도 "Warp → Ghostty → cmux"로 이동했다는 반응이 나오고 있다.

실제 사용 후기에서 가장 많이 언급되는 워크플로우:
> "수직 탭 하나에 WIP 작업 하나. 안에서 Claude Code 한쪽, 브라우저에 PR과 리소스 한쪽. 작업 전환이 자연스럽다."

## 설치

무료이며, GitHub에서 소스 코드를 확인할 수 있다. macOS에서만 동작한다.

## 공식 문서 탐색

공식 문서는 [cmux.dev](https://www.cmux.dev/)에서 한국어를 포함한 다국어로 제공된다.

### 개념 (Concepts)

[개념 페이지](https://www.cmux.dev/ko/docs/concepts)는 cmux의 설계 철학과 핵심 구성 요소를 설명한다.

- **탭(Tabs)**: cmux에서 탭은 독립적인 작업 컨텍스트 단위다. 각 탭은 수직 사이드바에 표시되며 git 브랜치, 현재 디렉토리, 실행 중인 포트, 알림 상태를 한눈에 보여준다.
- **패인(Panes)**: 탭 내에서 수평/수직으로 화면을 분할하는 단위. 하나의 탭 안에서 Claude Code와 인앱 브라우저를 나란히 배치하는 것이 대표적인 패턴이다.
- **알림(Notifications)**: OSC 이스케이프 시퀀스(OSC 9, 99, 777)를 통해 에이전트나 스크립트가 cmux에 알림을 보낼 수 있다. 별도의 플러그인 없이 표준 시퀀스만으로 동작한다.
- **인앱 브라우저(In-App Browser)**: 터미널과 같은 창에 내장된 브라우저. 스크립터블 API를 통해 자동으로 URL을 열거나 페이지와 상호작용할 수 있다.

### 시작하기 (Getting Started)

[시작하기 페이지](https://www.cmux.dev/ko/docs/getting-started)는 설치부터 기본 사용까지 안내한다.

Homebrew Cask로 설치할 수 있다:

```bash
brew install --cask cmux
```

설치 후 별도 설정 없이 바로 사용할 수 있다. 수직 탭 사이드바, 분할 패인, 인앱 브라우저는 모두 GUI에서 직접 조작 가능하다. Claude Code나 다른 AI 에이전트를 실행하면 알림 링이 자동으로 동작한다.

## 빠른 링크

- [cmux 공식 문서 — 개념](https://www.cmux.dev/ko/docs/concepts) — cmux의 핵심 개념 정리
- [cmux 공식 문서 — 시작하기](https://www.cmux.dev/ko/docs/getting-started) — 설치부터 기본 사용법
- [cmux GitHub](https://github.com/manaflow-ai/cmux) — 소스 코드 및 이슈 트래커
- [cmux Homebrew](https://formulae.brew.sh/cask/cmux) — `brew install --cask cmux`
- [AI 코딩 에이전트 전용 터미널 cmux 소개 영상](https://www.youtube.com/watch?v=jGj9yCqN08s) — 개발동생 채널

## 인사이트

cmux의 포지션은 명확하다 — tmux의 기능성을 macOS 네이티브 UX로 포장하고, AI 에이전트 워크플로우에 최적화한 것이다. 특히 알림 시스템은 "에이전트가 입력을 기다리고 있다"는 사실을 놓치지 않게 해주는데, 이것은 동시에 여러 에이전트를 돌리는 워크플로우에서 가장 큰 마찰 포인트였다. Ghostty의 libghostty를 라이브러리로 활용한다는 아키텍처 결정도 흥미롭다 — 터미널 렌더링이라는 어려운 문제를 해결된 것으로 취급하고, 그 위의 UX 레이어에 집중할 수 있게 해준다.

공식 문서와 에코시스템도 빠르게 성장하고 있다. 한국어를 포함한 다국어 문서, Homebrew Cask 등록, 활발한 커뮤니티 반응은 cmux가 단순한 실험적 프로젝트를 넘어 실용적인 도구로 자리잡고 있음을 보여준다. 아직 macOS 전용이라는 제약이 있지만, AI 에이전트 중심 개발 환경이 macOS 위에서 주로 이루어지는 현실을 감안하면 당장의 한계는 아니다.
