

# BLOCK 1.5 — Docker & Runtime Environment

## Проверить Dockerfile

### Проверить

* используется ли production-ready base image
* pinned versions
* отсутствие лишних system packages
* multi-stage build (если уместно)
* отсутствие dev dependencies в production image

### Проверить безопасность

* контейнер НЕ запускается от root
* secrets не baked into image
* `.env` не копируется внутрь image
* отсутствуют hardcoded credentials

### Проверить runtime

* корректный startup command
* healthcheck (если нужен)
* корректная работа uv
* predictable working directory

---

## Проверить docker-compose / orchestration

### Проверить

* разделение сервисов:

  * app
  * postgres
* volumes
* env variables
* restart policies

### Проверить networking

* отсутствие лишних exposed ports
* internal service communication

---

## Проверить persistence & temp files

### Проверить

* temp files directory handling
* cleanup behavior
* volume strategy
* PostgreSQL persistence

---

## Проверить production readiness

### Проверить

* env-based config
* configurable ports/hosts
* logging to stdout/stderr
* отсутствие debug mode в production

---

## Проверить dependency management

### Проверить

* использование uv
* lockfile consistency
* reproducible installs

---

# Что считать проблемами

## CRITICAL

* контейнер запускается от root
* secrets inside image
* debug mode enabled
* mutable runtime behavior

## HIGH

* отсутствие dependency pinning
* отсутствие persistence strategy
* dev dependencies в production

## MEDIUM

* oversized image
* плохая структура Dockerfile
* inconsistent env handling

---

# В отчет  добавить

Создать файл отчета: `TODO/TASK_038_docker_audit_report.md`

В `Findings`:

| Severity | File       | Line | Problem                | Impact        | Recommendation    |
| -------- | ---------- | ---- | ---------------------- | ------------- | ----------------- |
| HIGH     | Dockerfile | 12   | container runs as root | security risk | add non-root user |

---

И в `Final Assessment` отдельно:

```text
Deployment Readiness:
- READY
- PARTIALLY READY
- NOT READY
```

# 5. File-Level Recommendations

Для каждого проблемного файла:

```text
File: processing/pipeline.py

Problems:
- oversized function
- mixed responsibilities
- transaction handling unclear

Recommendations:
- split parsing/aggregation/save stages
- isolate DB writes
- add typed intermediate models
```

---