TASK: Fix SQLAlchemy relationship overlaps in user.py model

FILE: src/mko_bi/db/models/user.py

GOAL: Resolve SQLAlchemy relationship overlap warnings

IMPLEMENT:

func: add overlaps parameter to relationship definitions

LOGIC:

найти relationships в user.py (lines 71-86)
добавить overlaps параметр:
  - для accesses: добавить overlaps="dashboards"
  - для dashboards: добавить overlaps="accesses,dashboard"
проверить аналогичные overlaps в dashboard.py модели если есть

Пример исправления:
```python
accesses: Mapped[list["DashboardAccess"]] = relationship(
    "DashboardAccess",
    back_populates="user",
    cascade="all, delete-orphan",
    lazy="selectin",
    overlaps="dashboards",
)
```

CONSTRAINTS:

использовать overlaps параметр согласно документации SQLAlchemy
не менять логику каскадного удаления
сохранить lazy="selectin"

DONE:

 SQLAlchemy warnings исчезли
 relationships работают корректно
 тесты проходят
