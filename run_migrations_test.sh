#!/bin/bash

# Установить переменную окружения для тестового окружения
export ENVIRONMENT=test

# Запустить только миграционный тест отдельно
pytest tests/test_migrations.py -v

# Сохранить exit code
exit_code=$?

if [ $exit_code -eq 0 ]; then
  echo "[OK] Alembic migrations test PASSED"
else
  echo "[FAIL] Alembic migrations test FAILED"
fi

exit $exit_code 