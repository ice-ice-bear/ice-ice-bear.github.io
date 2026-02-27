---
image: "/images/posts/2026-02-24-alembic-database-migration/cover.jpg"
title: "Alembic — SQLAlchemy 데이터베이스 마이그레이션 가이드"
date: 2026-02-24
categories: ["backend"]
tags: ["alembic", "sqlalchemy", "database", "migration", "python", "postgresql"]
toc: true
math: false
---

## 개요

데이터베이스 스키마는 프로젝트와 함께 계속 변한다. 테이블을 추가하고, 컬럼을 수정하고, 인덱스를 생성하는 이 과정을 수동으로 관리하면 "이 DB에 어떤 변경을 했더라?" 같은 질문에 답할 수 없게 된다. [Alembic](https://alembic.sqlalchemy.org/)은 SQLAlchemy 기반의 마이그레이션 도구로, 스키마 변경을 **코드처럼 버전 관리**하고 안전하게 적용/롤백할 수 있게 해준다.

```mermaid
graph LR
    A[모델 변경] --> B[alembic revision]
    B --> C[마이그레이션 스크립트 생성]
    C --> D[alembic upgrade]
    D --> E[DB 스키마 적용]
    E --> F{문제 발생?}
    F -->|Yes| G[alembic downgrade]
    F -->|No| H[완료]
    G --> A
```

## 마이그레이션 환경 구조

Alembic을 초기화하면 다음과 같은 디렉토리 구조가 생성된다:

```
yourproject/
    alembic.ini          # 메인 설정 파일 (DB URL, 로깅 등)
    pyproject.toml       # Python 프로젝트 설정
    alembic/
        env.py           # 마이그레이션 실행 환경 (DB 연결, 트랜잭션 관리)
        README
        script.py.mako   # 마이그레이션 스크립트 생성 템플릿
        versions/        # 실제 마이그레이션 스크립트들
            3512b954651e_add_account.py
            2b1ae634e5cd_add_order_id.py
            3adcc9a56557_rename_username_field.py
```

### 핵심 파일별 역할

**`alembic.ini`**: DB URL, 로깅, 스크립트 경로 등 전체 설정. `%(here)s` 토큰으로 설정 파일 위치 기준 상대 경로를 지정할 수 있다.

**`env.py`**: 마이그레이션의 "두뇌". SQLAlchemy 엔진 생성, DB 연결, 트랜잭션 관리, 모델 임포트 등을 제어한다. 다중 DB나 커스텀 인자가 필요하면 이 파일을 수정한다.

**`script.py.mako`**: Mako 템플릿으로, 새 마이그레이션 파일의 뼈대를 정의한다. `upgrade()`와 `downgrade()` 함수 구조를 커스텀할 수 있다.

**`versions/`**: 실제 마이그레이션 스크립트가 저장되는 디렉토리. 파일 이름에 정수 시퀀스 대신 **부분 GUID**를 사용하여 브랜치 간 병합이 가능하다.

## 기본 워크플로우

### 1단계: 환경 초기화

```bash
cd /path/to/yourproject
alembic init alembic
```

4가지 템플릿 중 선택 가능:

| 템플릿 | 용도 |
|--------|------|
| `generic` | 단일 DB 기본 설정 |
| `pyproject` | pyproject.toml 기반 설정 (v1.16+) |
| `async` | 비동기 DB 드라이버 (asyncpg 등) |
| `multidb` | 다중 DB 환경 |

### 2단계: DB 연결 설정

`alembic.ini`에서 데이터베이스 URL을 설정한다:

```ini
sqlalchemy.url = postgresql://user:pass@localhost/dbname
```

> **주의**: URL에 `%` 기호가 포함된 경우 (URL 인코딩된 비밀번호 등) `%%`로 이스케이프해야 한다. 예: `p%40ss` → `p%%40ss`

### 3단계: 마이그레이션 스크립트 생성

```bash
alembic revision -m "add account table"
```

이 명령은 `versions/` 디렉토리에 새 마이그레이션 파일을 생성한다:

```python
"""add account table

Revision ID: 3512b954651e
Revises: 2b1ae634e5cd
Create Date: 2026-02-24 12:00:00.000000

"""

def upgrade():
    # 여기에 스키마 변경 코드 작성
    pass

def downgrade():
    # 여기에 롤백 코드 작성
    pass
```

### 4단계: 마이그레이션 적용

```bash
alembic upgrade head      # 최신 버전으로 업그레이드
alembic upgrade +2        # 현재 위치에서 2단계 앞으로
```

### 5단계: 롤백

```bash
alembic downgrade -1      # 1단계 롤백
alembic downgrade base    # 모든 마이그레이션 롤백
```

### 6단계: 상태 확인

```bash
alembic current           # 현재 DB가 어느 버전인지 확인
alembic history           # 전체 마이그레이션 히스토리
alembic history -r1a:3b   # 특정 범위의 히스토리만 조회
```

## 알아두면 유용한 기능

### 부분 Revision ID

명령어에서 Revision ID 전체를 입력할 필요 없이, 고유성이 보장되는 만큼만 입력하면 된다:

```bash
alembic upgrade ae1027a6acf   # 전체 ID
alembic upgrade ae1            # 이것만으로 충분 (고유하다면)
```

### Post-write Hooks

마이그레이션 파일 생성 후 자동으로 코드 포매터를 실행할 수 있다:

```ini
[post_write_hooks]
hooks = ruff
ruff.type = module
ruff.module = ruff
ruff.options = check --fix REVISION_SCRIPT_FILENAME
```

`black`, `ruff` 등을 연결하면 생성된 마이그레이션 스크립트가 자동으로 포매팅된다.

### pyproject.toml 지원

Alembic 1.16부터 `pyproject.toml`에서 직접 설정을 관리할 수 있다:

```bash
alembic init --template pyproject ./alembic
```

이 경우 소스 코드 관련 설정은 `pyproject.toml`에, DB 연결 등 환경별 설정은 `alembic.ini`에 분리된다.

## 빠른 링크

- [Alembic Tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html) — 공식 튜토리얼
- [Alembic Cookbook](https://alembic.sqlalchemy.org/en/latest/cookbook.html) — 실전 레시피
- [SQLAlchemy](https://www.sqlalchemy.org/) — Alembic의 기반 ORM

## 인사이트

Alembic의 핵심 가치는 "DB 스키마 변경을 코드처럼 관리한다"는 것이다. `git log`로 코드 변경 이력을 추적하듯, `alembic history`로 스키마 변경 이력을 추적할 수 있다. 특히 팀 개발에서는 "이 테이블 언제 추가했지?", "이 컬럼 누가 바꿨지?"라는 질문에 마이그레이션 스크립트가 답이 된다. 프로젝트 초기부터 Alembic을 도입하면 나중에 스키마 변경이 쌓일 때 큰 빚을 지지 않게 된다. 정수 시퀀스 대신 GUID 기반 버전 관리를 채택한 설계도 주목할 만한데, 이를 통해 여러 브랜치에서 동시에 마이그레이션을 생성해도 병합이 가능하다.
