# ARCHITECTURE.md - Рекомендации по улучшению

## Фундамент
1. **Unit тесты** - Добавить тесты для services.py, schemas.py, обеспечить coverage 80%+
2. **Разделить файлы** - app/config.py для settings, app/repo.py для DB операций
3. **BaseSettings** - Использовать Pydantic BaseSettings для централизованного управления конфигурацией через переменные окружения.
4. **Lifespan** - Добавить @app.lifespan для инициализации БД и cleanup
5. **Стандартизация snake_case** - Использовать snake_case для всех полей Pydantic-моделей

## Критические
6. **Структурированное логирование** - Использовать структурированное логирование (например structlog) для трассировки запросов и корреляции логов.
7. **Обработка ошибок БД** - Различать типы ошибок (IntegrityError, SQLAlchemy) в исключениях
8. **Исключения приложения** - Создать custom HTTPException классы для разных ошибок

## Производительность
9. **Асинхронные endpoints** - Миграция на async/await для улучшения масштабируемости при I/O нагрузке
10. **Redis кеширование** - Кешировать результаты /flaky на 5 минут (10-100x ускорение)
11. **Rate limiting** - Ограничить 100 req/min для /runs, 10 req/min для /flaky

## Гибкость
12. **API версионирование** - Добавить /api/v1 префикс для обратной совместимости

13. **entrypoint.sh** - Инициализация: миграции, проверка БД, graceful shutdown
14. **Secrets management** - .env для dev (в .gitignore), Docker secrets/K8s для prod

## Приоритет внедрения

1. BaseSettings + config
2. Unit тесты
3. Repository layer
4. Structured logging
5. Error handling
6. Redis caching
7. Async migration