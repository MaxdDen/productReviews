@echo off
setlocal

REM Установить переменную окружения для тестового окружения
set ENVIRONMENT=test

REM Запустить только миграционный тест отдельно
pytest tests/test_migrations.py -v
set exit_code=%ERRORLEVEL%

if %exit_code%==0 (
    echo [OK] Alembic migrations test PASSED
) else (
    echo [FAIL] Alembic migrations test FAILED
)

exit /b %exit_code% 