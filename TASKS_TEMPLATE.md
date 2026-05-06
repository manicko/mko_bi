
---

## DATA PROCESSING

---

### TASK: базовый pipeline

FILE: src/mkobi/data/processing/base.py

GOAL: оркестрация обработки

IMPLEMENT:

* class DataPipeline
* method: run(df, config)

LOGIC:

1. transform
2. aggregate
3. вернуть результат

DONE:

* [ ] pipeline работает
* [ ] тест

---

### TASK: трансформации

FILE: src/mkobi/data/processing/transformations.py

GOAL: преобразование данных

IMPLEMENT:

* func: apply_transformations(df, config)

LOGIC:

1. фильтры
2. вычисляемые поля

DONE:

* [ ] трансформации применяются
* [ ] тест

---

### TASK: агрегации

FILE: src/mkobi/data/processing/registry.py

GOAL: агрегаты

IMPLEMENT:

* groupby
* YoY
* share

LOGIC:

1. группировка
2. расчет метрик

DONE:

* [ ] агрегаты считаются
* [ ] тест

---

