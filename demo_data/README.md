# Demo Excel files

Папка `excel/` содержит 64 XLSX-файла за разные дни недели и месяца.
Каждый файл совместим с текущим parser'ом и содержит обычные операции плюс один контролируемый сценарий.

Ключевые сценарии: ordinary refunds control, similar refund cluster, duplicate ticket refund, terminal burst, fake identity, close departure cluster, seat blocking, critical combo fraud, document collision, rapid cancellations, aggregator wave.

Critical-сценарии специально комбинируют 2+ сильных сигнала, чтобы passenger-level скоринг показывал `critical`, а operation-level таблица показывала конкретные причины.

Пошаговый сценарий очистки БД, загрузки всех файлов и демонстрации лежит в `PRESENTATION_WORKFLOW.md`.
