---
title: "log-blog 개발 로그 #8 — URL 분류기 품질 개선과 다국어 택소노미 경로 수정"
description: log-blog 8회차 개발 로그. URL 분류기에 YouTube Shorts와 Perplexity Computer 분류를 추가하고, 다국어 모드에서 택소노미 _index.md가 잘못된 경로에 쓰이던 버그를 수정한다.
date: 2026-04-13
image: "/images/posts/2026-04-13-log-blog-dev8/cover-ko.jpg"
series: "log-blog"
series_num: 8
last_commit: "9f2f41f"
categories: ["dev-log"]
tags: ["log-blog", "python", "hugo", "i18n"]
toc: true
math: false
---

## 개요

[이전 글: #7](/posts/2026-04-08-log-blog-dev7/)에 이은 8회차. 이번 사이클은 URL 분류기 품질 향상 두 건과, 다국어 블로그 배포에서 발견된 택소노미 경로 버그 한 건을 다룬다. 작은 fix 세 개지만 셋 다 사용자가 즉시 체감하는 표면 — 분류 정확도와 빌드 성공 — 에 닿는다.

<!--more-->

---

## URL 분류기 — Perplexity Computer 분류 + 빌링 페이지 필터

### 배경

Perplexity가 출시한 Computer Agent URL이 history extract 결과에 섞여 들어왔는데, 기존 분류기는 이걸 일반 web_page로 떨어뜨리고 있었다. 동시에 RunPod 빌링/계정 페이지가 개인 계좌 정보를 노출하면서도 "tech URL"로 분류되는 문제가 있었다.

### 구현

`url_classifier.py`의 디스패치 테이블에 두 가지 변경:
- Perplexity Computer agent 패턴 추가 → `ai_chat_perplexity` 분류
- 명시적 빌링 페이지 패턴(`/billing`, `/account`) → 기본 필터링 대상으로 이동

### 결과

이번 사이클부터 history extract에서 빌링 페이지가 더 이상 보이지 않고, Perplexity Computer 결과가 AI chat 그룹에 정상 분류된다.

---

## URL 분류기 — YouTube Shorts와 GitHub 정확도

### 배경

URL 분류기가 YouTube Shorts(`youtube.com/shorts/...`)를 감지하지 못해 일반 web_page로 떨어뜨렸다. 또한 GitHub URL의 `/blob/`, `/tree/`, `/commit/` 경로가 `github_repo`로 잘못 분류되어 fetcher가 README를 가져오려다 실패하는 케이스가 있었다.

### 구현

```python
# YouTube Shorts 패턴 추가
re.compile(r"youtube\.com/shorts/"): UrlType.YOUTUBE,
# GitHub repo 패턴 강화 — blob/tree/commit는 github_other로 분리
```

### 결과

YouTube Shorts가 정상 transcript fetch 대상이 되고, GitHub `/blob/` URL이 별도 카테고리(`github_other`)로 분리되어 fetcher 실패가 사라졌다.

---

## 다국어 택소노미 경로 버그

### 배경

블로그가 한국어/영어 듀얼 언어로 전환된 뒤, 새 태그를 만들 때 `_index.md`가 `content/tags/{tag}/_index.md`에 쓰였다. 그런데 다국어 모드에서 Hugo는 `content/{lang}/tags/{tag}/_index.md`를 기대한다. 결과적으로 새 태그가 영어 블로그 홈에서 404를 일으켰다.

### 구현

```mermaid
graph LR
    A[기존: content/tags/{tag}/] --> B[Hugo i18n &lt;br/&gt; 인식 불가]
    A --> C[수정: content/{lang}/tags/{tag}/]
    C --> D[정상 라우팅]
```

`image_handler.py`의 택소노미 _index 작성 로직이 `--language` 플래그를 받아 `language_content_dirs[lang]` 아래에 _index.md를 쓰도록 변경. publish 명령이 양쪽 언어를 각각 호출하면 양쪽 _index가 모두 만들어진다.

### 결과

이전에 broken 상태였던 영어 블로그의 태그 인덱스가 정상화되었고, 캐시 무효화 후 즉시 표시 확인.

---

## 커밋 로그

| 메시지 | 변경 |
|--------|------|
| fix: classify Perplexity Computer agent URLs and filter billing pages | url_classifier.py |
| fix: improve URL classifier quality — YouTube Shorts, noise filtering, GitHub accuracy | url_classifier.py |
| fix: write taxonomy _index.md under language content root | image_handler.py |

---

## 인사이트

세 개의 fix 모두 "다른 컴포넌트(History DB, Hugo i18n)의 어떤 가정을 우리가 잘못 모델링했는가"를 묻는 부류였다. URL 분류기는 본질적으로 외부 사이트 URL 스키마에 대한 가정의 집합이라 — Perplexity Computer 같은 신규 패턴이 나오면 즉시 stale이 된다. 다국어 택소노미 버그는 더 흥미로웠다 — Hugo의 multilingual mode는 *기본* 컨텐츠 디렉토리를 그대로 두지만, 택소노미 인덱스는 언어 아래로 옮겨야 한다는 비대칭이 있었다. 이런 비대칭은 단일 언어 → 다국어 전환 시점에 가장 먼저 무너진다.
