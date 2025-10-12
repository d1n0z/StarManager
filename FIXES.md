# Исправления проблемы с зависанием FastAPI

## Найденная проблема

FastAPI перестаёт принимать подключения из-за **утечки фоновых задач** в эндпоинте `/api/listener/vk`.

### Причины:

1. **Неотслеживаемые задачи** - `asyncio.create_task()` создавал задачи без отслеживания
2. **Отсутствие таймаутов** - задачи могли выполняться бесконечно
3. **Исчерпание пула БД** - каждая задача держит соединение, пул из 150 соединений заполняется
4. **Перегрузка event loop** - накопление задач блокирует обработку новых запросов

## Внесённые исправления

### 1. routes.py - Отслеживание VK задач
- Добавлен `_vk_tasks` set для отслеживания активных задач
- Добавлен таймаут 30 секунд на обработку события
- Автоматическая очистка завершённых задач через callback

### 2. app.py - Мониторинг и shutdown
- Добавлен мониторинг количества активных VK задач (каждую минуту)
- Корректная отмена всех VK задач при shutdown

### 3. db.py - Оптимизация пула БД
- Уменьшен timeout с 60 до 30 секунд
- Уменьшен command_timeout с 120 до 60 секунд
- Добавлен max_queries=50000
- Добавлен max_cached_statement_lifetime=300

## Дополнительные рекомендации

### Критично:

1. **Добавить мониторинг пула БД**:
```python
# В app.py в _monitor_tasks
from StarManager.core.db import pool
db_pool = await pool()
logger.info(f"DB pool: size={db_pool.get_size()}, free={db_pool.get_idle_size()}")
```

2. **Ограничить количество одновременных VK задач**:
```python
# В routes.py изменить семафор
_vk_semaphore = asyncio.Semaphore(10)  # было 25
```

3. **Добавить healthcheck эндпоинт**:
```python
@router.get("/health")
async def health():
    from StarManager.site.routes import _vk_tasks
    from StarManager.core.db import pool
    db_pool = await pool()
    return {
        "status": "ok",
        "vk_tasks": len(_vk_tasks),
        "db_pool_size": db_pool.get_size(),
        "db_pool_free": db_pool.get_idle_size()
    }
```

### Важно:

4. **Добавить таймауты в message_handlers.py** - много операций БД без таймаутов

5. **Оптимизировать scheduler.py** - задачи могут блокировать друг друга

6. **Использовать connection pooling правильно**:
   - Не держать соединения открытыми долго
   - Использовать `async with` для автоматического возврата в пул

7. **Логирование медленных запросов**:
```python
# В db.py
async def pool():
    global _pool
    if _pool is None:
        _pool = await create_asyncpool(
            DATABASE_STR,
            # ... другие параметры
            server_settings={
                'log_min_duration_statement': '1000'  # логировать запросы >1сек
            }
        )
    return _pool
```

## Мониторинг и диагностика

### 1. Healthcheck эндпоинт `/health`
Показывает детальную информацию:
- Количество активных VK задач
- Состояние пула БД (занято/свободно)
- Время отклика БД
- Использование памяти и CPU
- Количество потоков

```bash
curl http://127.0.0.1:5000/health | jq
```

### 2. Скрипт monitor.py (диагностика)
Собирает данные о проблемах в `logs/diagnostic.jsonl`:

```bash
# Добавить в crontab (каждую минуту)
* * * * * cd /path/to/StarManager && python3 monitor.py
```

### 3. Анализ проблем
```bash
python3 analyze_diagnostic.py
```

Покажет:
- Частоту проблем по типам
- Состояние системы в момент проблемы
- Тренды (много VK задач, исчерпание пула БД и т.д.)

### 4. Автоматический перезапуск (опционально)
После диагностики можно добавить в monitor.py:
```python
if not ok:
    save_diagnostic(data, msg)
    subprocess.run(["systemctl", "restart", "starmanager"])
```

## Как проверить исправления

1. Установить зависимости: `pip install psutil requests`
2. Запустить приложение
3. Проверить логи на наличие `Active VK tasks: N`
4. Настроить мониторинг: `crontab -e` → добавить `* * * * * cd /path && python3 monitor.py`
5. Проверить `/health`: `curl http://127.0.0.1:5000/health | jq`
6. При проблемах: `python3 analyze_diagnostic.py`

## Признаки проблемы

- FastAPI перестаёт отвечать на запросы
- В логах нет ошибок
- Фоновые задачи (scheduler, tgbot) продолжают работать
- Количество VK задач растёт
- Пул БД исчерпан (все 150 соединений заняты)
