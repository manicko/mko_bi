TASK: корректная обработка GZ файлов

FILE: src/mko_bi/services/data_service.py

GOAL: поддержка .csv.gz согласно SPEC

IMPLEMENT:

import gzip

def _process_csv_file(file_path: Path) -> pl.DataFrame:
    if file_path.suffix == ".gz" or file_path.suffixes == [".csv", ".gz"]:
        with gzip.open(file_path, "rt") as f:
            df = pl.read_csv(f)
    else:
        df = pl.read_csv(file_path)
    return df

LOGIC:

проверить расширение файла
если .gz - открыть через gzip.open()
передать файловый объект в pl.read_csv()

CONSTRAINTS:

поддержка .csv.gz файлов
корректное чтение сжатых файлов

DONE:

.csv.gz файлы обрабатываются корректно
тесты для GZ файлов пройдены
