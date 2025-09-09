import pytest
from sqlalchemy import inspect
from app.database.base import Base
import app.models
import warnings
import subprocess
import app.models.product
import app.models.user
from app.schemas.product import ProductCreate, ProductUpdate
from app.database.crud import create_directory_item, get_directory_item, update_directory_item, delete_directory_item
from app.models.product import Product
from app.models.user import User
import pytest_asyncio


TYPE_SYNONYMS = {
    "FLOAT": ["FLOAT", "DOUBLE PRECISION"],
    "DOUBLE PRECISION": ["FLOAT", "DOUBLE PRECISION"],
    "VARCHAR": ["VARCHAR", "CHARACTER VARYING"],
    "CHARACTER VARYING": ["VARCHAR", "CHARACTER VARYING"],
    # добавьте другие при необходимости
}

def types_equivalent(model_type: str, db_type: str) -> bool:
    return db_type.upper() in TYPE_SYNONYMS.get(model_type.upper(), [model_type.upper()])


def test_models_and_db_tables_match(sync_engine):
    with sync_engine.begin() as conn:
        insp = inspect(conn)
        tables = insp.get_table_names()
    assert set(Base.metadata.tables.keys()).issubset(set(tables))

def test_warn_extra_tables(sync_engine):
    """
    Проверяет наличие в базе таблиц, которых нет в моделях.
    Не приводит к падению теста, а только выводит предупреждение.
    """
    with sync_engine.begin() as conn:
        insp = inspect(conn)
        db_tables = set(insp.get_table_names())
        model_tables = set(Base.metadata.tables.keys())

        extra_tables = db_tables - model_tables
        # Игнорируем служебную таблицу alembic_version
        extra_tables = {t for t in extra_tables if t != "alembic_version"}
        if extra_tables:
            warnings.warn(f"Extra tables in DB not present in models: {extra_tables}")
        else:
            warnings.warn("Нет лишних таблиц в базе данных.")
    assert True

def test_model_columns_match(sync_engine):
    """
    Проверяет, что каждая таблица из метаданных:
    - есть в базе
    - колонки по имени, типу и nullable совпадают
    """
    def _inspect_tables(sync_conn):
        insp = inspect(sync_conn)
        result = {}
        for table_name in Base.metadata.tables:
            cols = insp.get_columns(table_name)
            result[table_name] = {col["name"]: col for col in cols}
        return result

    with sync_engine.begin() as conn:
        db_columns = _inspect_tables(conn)

    for table_name, table in Base.metadata.tables.items():
        assert table_name in db_columns, f"Table {table_name} missing in DB"
        db_cols = db_columns[table_name]
        for col in table.columns:  # SQLAlchemy Column objects
            assert col.name in db_cols, f"Column {col.name!r} missing in {table_name}"
            db_col = db_cols[col.name]
            # check nullable
            assert db_col["nullable"] == col.nullable, (
                f"Mismatch nullable on {table_name}.{col.name!r}: "
                f"{db_col['nullable']} != {col.nullable}"
            )
            model_col_type_str = col.type.compile(sync_engine.dialect)
            db_col_type_str = db_col["type"].compile(sync_engine.dialect)

            assert types_equivalent(model_col_type_str, db_col_type_str), (
                f"Type mismatch on {table_name}.{col.name!r}: "
                f"Model: {model_col_type_str} ( SQLAlchemy type: {col.type} ) != "
                f"DB: {db_col_type_str} ( SQLAlchemy type: {db_col['type']} )"
            )

def test_db_schema_integrity(sync_engine):
    def check_schema(sync_conn):
        insp = inspect(sync_conn)
        db_tables = set(insp.get_table_names())
        model_tables = set(Base.metadata.tables.keys())
        errors = []

        # Проверка таблиц
        for table_name, table in Base.metadata.tables.items():
            if table_name not in db_tables:
                errors.append(f"Table {table_name} missing in DB")
                continue

            # Индексы
            db_indexes = {idx['name'] for idx in insp.get_indexes(table_name)}
            model_indexes = {idx.name for idx in table.indexes}
            missing_indexes = model_indexes - db_indexes
            if missing_indexes:
                errors.append(f"Missing indexes in DB for {table_name}: {missing_indexes}")

            # Уникальные ограничения
            db_uniques = {tuple(u['column_names']) for u in insp.get_unique_constraints(table_name)}
            model_uniques = {
                tuple(constraint.columns.keys())
                for constraint in table.constraints
                if constraint.__class__.__name__ == "UniqueConstraint"
            }
            missing_uniques = model_uniques - db_uniques
            if missing_uniques:
                errors.append(f"Missing unique constraints in DB for {table_name}: {missing_uniques}")

            # Внешние ключи
            db_fks = {
                (tuple(fk['constrained_columns']), fk['referred_table'], tuple(fk['referred_columns']))
                for fk in insp.get_foreign_keys(table_name)
            }
            model_fks = {
                (tuple(fk.parent.name for fk in constraint.elements),
                 constraint.elements[0].column.table.name,
                 tuple(fk.column.name for fk in constraint.elements))
                for constraint in table.constraints
                if constraint.__class__.__name__ == "ForeignKeyConstraint"
            }
            missing_fks = model_fks - db_fks
            if missing_fks:
                errors.append(f"Missing foreign keys in DB for {table_name}: {missing_fks}")

        return errors

    with sync_engine.begin() as conn:
        errors = check_schema(conn)

    assert not errors, "\n".join(errors)

def format_index(idx):
    """Форматирует индекс для сравнения: (имя, tuple(колонки), уникальный?)"""
    return (
        idx['name'],
        tuple(idx['column_names']),
        idx.get('unique', False)
    )

def format_unique_constraint(uq):
    """Форматирует уникальное ограничение: tuple(колонки)"""
    return tuple(uq['column_names'])

def format_fk(fk):
    """Форматирует внешний ключ для сравнения: (tuple(локальные колонки), таблица, tuple(внешние колонки))"""
    return (
        tuple(fk['constrained_columns']),
        fk['referred_table'],
        tuple(fk['referred_columns'])
    )

def test_indexes_uniques_foreign_keys(sync_engine):
    """
    Проверяет индексы, уникальные ограничения и внешние ключи (включая составные).
    Выводит подробные различия, не падает если их нет в моделях.
    """
    def check_schema(sync_conn):
        insp = inspect(sync_conn)
        results = {}
        for table_name, table in Base.metadata.tables.items():
            table_result = {}
            # Индексы
            db_indexes = [format_index(idx) for idx in insp.get_indexes(table_name)]
            model_indexes = [
                (idx.name, tuple(idx.columns.keys()), idx.unique)
                for idx in table.indexes
            ]
            table_result['db_indexes'] = db_indexes
            table_result['model_indexes'] = model_indexes

            # Уникальные ограничения
            db_uniques = {format_unique_constraint(uq) for uq in insp.get_unique_constraints(table_name)}
            model_uniques = {
                tuple(constraint.columns.keys())
                for constraint in table.constraints
                if constraint.__class__.__name__ == "UniqueConstraint"
            }
            table_result['db_uniques'] = db_uniques
            table_result['model_uniques'] = model_uniques

            # Внешние ключи
            db_fks = {format_fk(fk) for fk in insp.get_foreign_keys(table_name)}
            model_fks = {
                (
                    tuple(fk.parent.name for fk in constraint.elements),
                    constraint.elements[0].column.table.name,
                    tuple(fk.column.name for fk in constraint.elements)
                )
                for constraint in table.constraints
                if constraint.__class__.__name__ == "ForeignKeyConstraint"
            }
            table_result['db_fks'] = db_fks
            table_result['model_fks'] = model_fks

            results[table_name] = table_result
        return results

    with sync_engine.begin() as conn:
        schema_info = check_schema(conn)

    # Анализ результатов (уже вне run_sync)
    for table_name, table_result in schema_info.items():
        print(f"\nПроверка таблицы: {table_name}")

        # Индексы
        db_indexes = set(table_result['db_indexes'])
        model_indexes = set(table_result['model_indexes'])
        missing_indexes = model_indexes - db_indexes
        extra_indexes = db_indexes - model_indexes
        if model_indexes:
            if missing_indexes:
                print(f"  [!] Индексы, описанные в моделях, но отсутствующие в БД: {missing_indexes}")
            if extra_indexes:
                print(f"  [!] Индексы, присутствующие в БД, но отсутствующие в моделях: {extra_indexes}")
            assert not missing_indexes, f"Missing indexes in DB for {table_name}: {missing_indexes}"
        else:
            print("  [i] В моделях не описано ни одного индекса.")

        # Уникальные ограничения
        db_uniques = set(table_result['db_uniques'])
        model_uniques = set(table_result['model_uniques'])
        missing_uniques = model_uniques - db_uniques
        extra_uniques = db_uniques - model_uniques
        if model_uniques:
            if missing_uniques:
                print(f"  [!] Уникальные ограничения из моделей, отсутствующие в БД: {missing_uniques}")
            if extra_uniques:
                print(f"  [!] Уникальные ограничения в БД, отсутствующие в моделях: {extra_uniques}")
            assert not missing_uniques, f"Missing unique constraints in DB for {table_name}: {missing_uniques}"
        else:
            print("  [i] В моделях не описано ни одного уникального ограничения.")

        # Внешние ключи
        db_fks = set(table_result['db_fks'])
        model_fks = set(table_result['model_fks'])
        missing_fks = model_fks - db_fks
        extra_fks = db_fks - model_fks
        if model_fks:
            if missing_fks:
                print(f"  [!] Внешние ключи из моделей, отсутствующие в БД: {missing_fks}")
            if extra_fks:
                print(f"  [!] Внешние ключи в БД, отсутствующие в моделях: {extra_fks}")
            assert not missing_fks, f"Missing foreign keys in DB for {table_name}: {missing_fks}"
        else:
            print("  [i] В моделях не описано ни одного внешнего ключа.")

# Параметризация: проверка наличия каждой таблицы
@pytest.mark.parametrize("table_name", list(Base.metadata.tables.keys()))
def test_table_exists(sync_engine, table_name):
    with sync_engine.begin() as conn:
        insp = inspect(conn)
        assert table_name in insp.get_table_names(), f"Table {table_name} missing in DB"

# Параметризация: проверка наличия каждой колонки в каждой таблице
@pytest.mark.parametrize("table_name,column_name", [
    (table.name, col.name)
    for table in Base.metadata.tables.values()
    for col in table.columns
])
def test_column_exists(sync_engine, table_name, column_name):
    with sync_engine.begin() as conn:
        insp = inspect(conn)
        cols = [col["name"] for col in insp.get_columns(table_name)]
        assert column_name in cols, f"Column {column_name} missing in {table_name}"

def get_column_default(col):
    # SQLAlchemy column default может быть выражением или значением
    if col.default is not None:
        if hasattr(col.default, 'arg'):
            return col.default.arg
        return col.default
    return None

def test_column_defaults(sync_engine):
    """Проверяет, что default-значения колонок совпадают между моделями и БД (если заданы явно и там, и там)."""
    with sync_engine.begin() as conn:
        insp = inspect(conn)
        for table_name, table in Base.metadata.tables.items():
            db_cols = {col["name"]: col for col in insp.get_columns(table_name)}
            for col in table.columns:
                db_col = db_cols.get(col.name)
                if db_col is None:
                    continue
                # Игнорируем default для autoincrement PK (serial/bigserial)
                if col.primary_key and db_col.get("autoincrement", False):
                    continue
                model_default = get_column_default(col)
                db_default = db_col.get("default")
                # Сравниваем только если и там, и там явно задано default
                if model_default is not None and db_default is not None:
                    assert str(model_default) == str(db_default), (
                        f"Default mismatch on {table_name}.{col.name}: model={model_default!r}, db={db_default!r}")


def test_foreign_key_ondelete_onupdate(sync_engine):
    """Проверяет, что ondelete/onupdate для ForeignKey совпадают между моделями и БД."""
    with sync_engine.begin() as conn:
        insp = inspect(conn)
        for table_name, table in Base.metadata.tables.items():
            db_fks = {tuple(fk['constrained_columns']): fk for fk in insp.get_foreign_keys(table_name)}
            for constraint in table.constraints:
                if constraint.__class__.__name__ == "ForeignKeyConstraint":
                    model_cols = tuple(fk.parent.name for fk in constraint.elements)
                    db_fk = db_fks.get(model_cols)
                    if db_fk is None:
                        continue
                    # Проверяем ondelete/onupdate
                    model_ondelete = constraint.elements[0].ondelete if hasattr(constraint.elements[0], 'ondelete') else None
                    model_onupdate = constraint.elements[0].onupdate if hasattr(constraint.elements[0], 'onupdate') else None
                    db_ondelete = db_fk.get('options', {}).get('ondelete')
                    db_onupdate = db_fk.get('options', {}).get('onupdate')
                    if model_ondelete or db_ondelete:
                        assert (model_ondelete or '').lower() == (db_ondelete or '').lower(), (
                            f"ondelete mismatch on FK {table_name}.{model_cols}: model={model_ondelete}, db={db_ondelete}")
                    if model_onupdate or db_onupdate:
                        assert (model_onupdate or '').lower() == (db_onupdate or '').lower(), (
                            f"onupdate mismatch on FK {table_name}.{model_cols}: model={model_onupdate}, db={db_onupdate}")


def test_column_constraints(sync_engine):
    """Проверяет наличие NOT NULL, UNIQUE, PRIMARY KEY на уровне БД для каждой колонки."""
    with sync_engine.begin() as conn:
        insp = inspect(conn)
        for table_name, table in Base.metadata.tables.items():
            db_cols = {col["name"]: col for col in insp.get_columns(table_name)}
            db_pk = set(insp.get_pk_constraint(table_name).get('constrained_columns', []))
            # Собираем все unique constraints (в том числе составные)
            db_uniques = set()
            db_unique_sets = set()
            for uq in insp.get_unique_constraints(table_name):
                db_uniques.update(uq['column_names'])
                db_unique_sets.add(tuple(uq['column_names']))
            for col in table.columns:
                db_col = db_cols.get(col.name)
                if db_col is None:
                    continue
                # NOT NULL
                assert db_col["nullable"] == col.nullable, (
                    f"NOT NULL mismatch on {table_name}.{col.name}: model={col.nullable}, db={db_col['nullable']}")
                # PRIMARY KEY
                model_pk = col.primary_key
                db_is_pk = col.name in db_pk
                assert model_pk == db_is_pk, (
                    f"PRIMARY KEY mismatch on {table_name}.{col.name}: model={model_pk}, db={db_is_pk}")
                # UNIQUE
                model_unique = col.unique
                # Проверяем, что либо одиночный unique constraint есть, либо col входит в составной unique
                db_is_unique = col.name in db_uniques or any((col.name,) == uq for uq in db_unique_sets)
                if model_unique or db_is_unique:
                    assert model_unique == db_is_unique, (
                        f"UNIQUE mismatch on {table_name}.{col.name}: model={model_unique}, db={db_is_unique}")
