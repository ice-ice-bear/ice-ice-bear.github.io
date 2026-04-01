---
title: "Honeycomb과 Observability 입문 — 오픈소스 대안 비교"
description: Honeycomb 공식 문서를 기반으로 observability 핵심 개념과 structured events 모델을 정리하고 Jaeger Zipkin SigNoz Pinpoint 등 오픈소스 대안을 비교한다
date: 2026-04-01
image: "/images/posts/2026-04-01-honeycomb-observability/cover.jpg"
categories: ["devops"]
tags: ["observability", "honeycomb", "jaeger", "zipkin", "signoz", "pinpoint", "opentelemetry", "ebpf", "distributed-tracing"]
toc: true
math: false
---

이전 글에서 Observability와 Monitoring의 차이, Honeycomb과 Grafana의 접근 방식을 비교했다. 이번에는 Honeycomb 공식 문서를 깊이 파고들어 observability의 핵심 개념을 정리하고, 셀프호스팅 가능한 오픈소스 대안들을 실무 관점에서 비교해 본다.

> [이전 글: Observability vs Monitoring — Honeycomb vs Grafana](/posts/2026-02-25-observability-honeycomb-vs-grafana/)

<!--more-->

## Observability 핵심 개념

Honeycomb 문서에서 가장 강조하는 정의는 이것이다:

> **Observability is about being able to ask arbitrary questions about your environment without having to know ahead of time what you wanted to ask.**

Monitoring은 이미 알고 있는 문제에 대한 threshold를 설정하고 alert을 받는 것이다. 반면 observability는 **예상하지 못한 질문**을 던질 수 있어야 한다. 마이크로서비스 환경에서 장애의 원인은 무한히 조합될 수 있기 때문에, 미리 정의한 dashboard만으로는 새로운 유형의 문제를 진단할 수 없다.

Observability를 개선하려면 두 가지가 필요하다:

1. **풍부한 런타임 컨텍스트를 포함한 텔레메트리 데이터 수집**
2. **그 데이터를 반복적으로 쿼리하여 인사이트를 발견하는 능력**

## Structured Events vs Metrics vs Logs

Honeycomb의 데이터 모델 핵심은 **structured event**다. Event, metric, log 각각의 차이를 이해하는 것이 observability 입문의 출발점이다.

### Structured Event

Event는 하나의 작업 단위(unit of work)를 완전하게 설명하는 JSON 객체다. HTTP 요청을 받아 처리하고 응답을 돌려주는 전체 과정이 하나의 event가 된다.

```json
{
  "service.name": "retriever",
  "duration_ms": 0.011668,
  "dataset_id": "46829",
  "global.env": "production",
  "global.instance_type": "m6gd.2xlarge",
  "global.memory_inuse": 671497992,
  "trace.trace_id": "845a4de7-...",
  "trace.span_id": "84c82b34..."
}
```

핵심은 **모든 필드가 쿼리 가능**하다는 것이다. `duration_ms`로 느린 요청을 찾고, `instance_type`별로 그룹핑하고, `memory_inuse`와의 상관관계를 한 번에 탐색할 수 있다.

### Pre-aggregated Metrics의 한계

Metrics 방식은 데이터를 미리 집계해서 보낸다:

```json
{
  "time": "4:03 pm",
  "total_hits": 500,
  "avg_duration": 113,
  "p95_duration": 236
}
```

만약 "storage engine cache hit 여부에 따른 latency 차이"를 보고 싶다면? `avg_duration_cache_hit_true`, `p95_duration_cache_hit_true` 같은 조합을 미리 만들어야 한다. 이것이 **차원의 저주(curse of dimensionality)** — 차원이 늘어날수록 필요한 metric 수가 기하급수적으로 증가한다.

### Unstructured Logs의 한계

로그는 사람이 읽기엔 편하지만 쿼리하기 어렵다. "어떤 서비스가 시작하는 데 가장 오래 걸리나?"를 알려면 여러 줄의 timestamp를 파싱하고 빼야 한다. Structured event는 `duration_ms` 필드 하나로 즉시 답할 수 있다.

```mermaid
graph TD
    A["Telemetry Data"] --> B["Structured Events"]
    A --> C["Metrics"]
    A --> D["Logs"]

    B --> B1["모든 필드 쿼리 가능 &lt;br/&gt; High Cardinality 지원"]
    C --> C1["미리 집계 필요 &lt;br/&gt; 차원의 저주"]
    D --> D1["파싱 필요 &lt;br/&gt; 구조화 어려움"]

    B1 --> E["Observability 달성"]
    C1 --> F["Monitoring 수준"]
    D1 --> F

    style B fill:#f5a623,color:#000
    style E fill:#7ed321,color:#000
    style F fill:#d0021b,color:#fff
```

## High Cardinality의 중요성

Cardinality란 특정 필드가 가질 수 있는 고유 값의 수를 말한다. `user_id`, `trace_id`, `request_id` 같은 필드는 수백만 개의 고유 값을 가진다 — 이것이 **high cardinality**다.

전통적인 metrics 도구(Prometheus, Graphite 등)는 high cardinality를 잘 처리하지 못한다. Label 조합이 폭발적으로 증가하면 성능이 급격히 저하된다. 하지만 observability에서는 "이 특정 사용자에게 왜 느린가?"처럼 개별 값을 추적해야 하는 질문이 핵심이다.

Honeycomb은 columnar storage 기반으로 high cardinality 데이터를 효율적으로 처리한다. **BubbleUp** 기능은 이상치(outlier)를 자동으로 감지하고, 어떤 필드 조합이 문제와 상관있는지 찾아준다.

## Core Analysis Loop

Honeycomb이 제안하는 디버깅 방법론은 **Core Analysis Loop**다:

1. **관찰(Observe)**: 시스템의 전체 상태를 시각화한다
2. **가설 수립(Hypothesize)**: 이상 패턴을 발견하면 원인에 대한 가설을 세운다
3. **검증(Validate)**: 데이터를 GROUP BY, WHERE로 쪼개어 가설을 검증하거나 기각한다
4. **반복(Iterate)**: 새로운 질문으로 돌아가 반복한다

이것은 "dashboard를 보고 alert를 기다리는" monitoring 방식과 근본적으로 다르다. Query Builder에서 SELECT, WHERE, GROUP BY, ORDER BY, LIMIT, HAVING 절을 조합하여 자유롭게 데이터를 탐색한다.

Honeycomb의 **Query Assistant**는 자연어로 질문하면 쿼리를 자동 생성해주는 실험적 기능이다. "show me the slowest endpoints grouped by service" 같은 입력으로 쿼리를 시작할 수 있다.

## eBPF와 Observability

**eBPF(extended Berkeley Packet Filter)** 는 Linux 커널을 수정하지 않고 확장 기능을 실행할 수 있는 기술이다. Observability 관점에서 중요한 이유는 **코드 변경 없이 텔레메트리를 수집**할 수 있기 때문이다.

### 동작 원리

- **JIT Compiler**: eBPF 프로그램은 커널 내 JIT 컴파일러로 실행되어 고성능을 보장한다
- **Hook Points**: system call, 함수 진입/종료, kernel tracepoint, network event 등 미리 정의된 hook에 연결된다
- **Kprobes / Uprobes**: 미리 정의된 hook이 없으면 커널 프로브(Kprobes)나 유저 프로브(Uprobes)를 생성하여 거의 모든 지점에 eBPF 프로그램을 부착할 수 있다

### Observability에서의 활용

자동 계측(automatic instrumentation) 도구가 없는 언어(C++, Rust 등)에서 eBPF는 특히 유용하다. 애플리케이션 외부에서 커널 프로브를 통해 네트워크 활동, CPU/메모리 사용률, 네트워크 인터페이스 메트릭 등을 수집할 수 있다.

OpenTelemetry는 현재 **Go 언어용 eBPF 기반 자동 계측 도구**를 개발 중이며, HTTP client/server, gRPC, gorilla/mux 라우터 등을 지원한다. C++과 Rust 지원도 계획되어 있다.

## 오픈소스 대안 비교

Honeycomb은 강력하지만 SaaS 종속성과 비용이 부담될 수 있다. 셀프호스팅 가능한 오픈소스 대안을 살펴보자.

### Jaeger

- **개발사**: Uber
- **백엔드**: Cassandra / Elasticsearch
- **특징**: 스팬(span) 단위 호출 시간/지연 분석이 핵심 강점. Zipkin과 호환되며, OpenTelemetry 네이티브 지원
- **배포**: Kubernetes Helm 차트, Jaeger Operator로 쉬운 배포
- **UI**: 16686 포트에서 서비스별 duration 쿼리, 트레이스 타임라인 시각화

```bash
# All-in-one 실행 (개발/테스트용)
./jaeger-all-in-one --memory-max-table-size=100000

# EKS 배포
kubectl create namespace observability
kubectl apply -f jaeger-operator.yaml
```

### Zipkin

- **개발사**: Twitter
- **백엔드**: Elasticsearch / MySQL
- **특징**: 가볍고 심플한 트레이싱 서버. **Spring Cloud Sleuth**와 네이티브 연동
- **배포**: Docker 한 줄로 실행 가능

```bash
docker run -d -p 9411:9411 openzipkin/zipkin
```

서비스 호출 그래프와 의존성(dependency) 다이어그램을 자동 생성하며, 장애 분석에 유용하다. 다만 OpenTelemetry 지원은 브릿지 방식이라 네이티브에 비해 설정이 더 필요하다.

### SigNoz

- **특징**: **OpenTelemetry 네이티브** 오픈소스 APM. Honeycomb 스타일의 쿼리와 대시보드를 셀프호스팅으로 제공
- **백엔드**: ClickHouse (고성능 columnar DB)
- **장점**: 로그, 메트릭, 트레이스를 **하나의 플랫폼**에서 통합. Honeycomb의 가장 가까운 오픈소스 대안
- **배포**: AWS ECS CloudFormation 템플릿, Kubernetes 풀스택 배포 지원

SigNoz는 OTLP(OpenTelemetry Protocol)을 직접 수신하므로 별도 변환 없이 OpenTelemetry Collector에서 데이터를 보낼 수 있다.

### Pinpoint

- **개발사**: Naver
- **백엔드**: HBase
- **특징**: **대규모 Java 애플리케이션** 트레이싱에 최적화. 바이트코드 계측으로 코드 변경 없이 에이전트 적용
- **강점**: Scatter/Timeline 차트로 호출 흐름과 시간을 상세 분석. 한국 대기업 환경에서 검증된 안정성

```bash
# 에이전트 적용 (JVM 옵션)
java -javaagent:pinpoint-agent.jar \
  -Dpinpoint.agentId=myapp-01 \
  -Dpinpoint.applicationName=my-service \
  -jar my-application.jar
```

## 비교 테이블

| 도구 | 백엔드 | OTel 지원 | K8s 배포 | 핵심 강점 |
|------|--------|-----------|----------|-----------|
| **Honeycomb** | SaaS (AWS) | 네이티브 | N/A (SaaS) | High cardinality 쿼리, BubbleUp, AI 분석 |
| **Jaeger** | ES / Cassandra | 네이티브 | Helm / Operator | 고트래픽 스팬 트레이싱 |
| **Zipkin** | ES / MySQL | 브릿지 | 기본 Deployment | 간단 배포, Spring 연동 |
| **SigNoz** | ClickHouse | 네이티브 | 풀스택 | 올인원 관찰성 (로그+메트릭+트레이스) |
| **Pinpoint** | HBase | 부분 지원 | 지원 | 대규모 Java APM, 바이트코드 계측 |

## Honeycomb 가격 (2026 기준)

| 플랜 | 월 비용 | 이벤트 한도 | 보관 기간 | 대상 |
|------|---------|-------------|-----------|------|
| **Free** | 무료 | 20M/월 | 60일 | 소규모 팀, 테스트 |
| **Pro** | $100~ | 1.5B/월 | 60일 | 성장 팀, SLO 필요 |
| **Enterprise** | 맞춤 | 무제한 | 확장 | 대규모, Private Cloud |

연간 계약 시 15~20% 할인이 적용된다. Free 플랜의 20M 이벤트는 소규모 서비스 검증에 충분하다.

## 인사이트

**Observability의 본질은 도구가 아니라 사고방식의 전환이다.** "어떤 dashboard를 만들까?"가 아니라 "어떤 질문이든 던질 수 있는가?"가 핵심이다. Honeycomb은 이 철학을 structured event와 high cardinality 쿼리로 구현했다.

실무에서의 선택 기준을 정리하면:

- **빠른 시작**: Honeycomb Free 플랜 (20M 이벤트/월)으로 observability 경험을 먼저 쌓고
- **셀프호스팅 올인원**: SigNoz가 Honeycomb에 가장 가까운 오픈소스 대안. ClickHouse 백엔드의 쿼리 성능이 좋고 OTel 네이티브
- **Java 중심 레거시**: Pinpoint가 바이트코드 계측으로 코드 변경 없이 적용 가능
- **이미 Kubernetes에 익숙하다면**: Jaeger + OpenTelemetry Collector 조합이 생태계가 가장 넓음

eBPF는 아직 초기 단계지만, 코드 변경 없는 계측이라는 점에서 Go, C++, Rust 생태계에서 점점 중요해질 기술이다. OpenTelemetry의 eBPF 기반 자동 계측이 성숙하면 observability 도입 비용이 크게 낮아질 것이다.

## 참고 자료

- [Honeycomb Docs: Introduction to Observability](https://docs.honeycomb.io/get-started/basics/observability/introduction)
- [Honeycomb Docs: Events, Metrics, and Logs](https://docs.honeycomb.io/get-started/basics/observability/concepts/events-metrics-logs)
- [Honeycomb Docs: eBPF](https://docs.honeycomb.io/get-started/basics/observability/concepts/ebpf)
- [Honeycomb Docs: Build a Query](https://docs.honeycomb.io/investigate/query/build)
- [Jaeger - Distributed Tracing](https://www.jaegertracing.io/)
- [Zipkin](https://zipkin.io/)
- [SigNoz - Open Source APM](https://signoz.io/)
- [Pinpoint - Application Performance Management](https://pinpoint-apm.gitbook.io/)
