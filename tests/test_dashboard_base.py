"""Тесты для базового класса дашборда и реестра.

Тестирует:
- Абстрактный базовый класс DashboardBase
- Реестр и фабрику DashboardRegistry
- Декоратор регистрации
- Кэширование экземпляров
"""

import pytest
from abc import ABC
from mko_bi.dashboards.base import DashboardBase
from mko_bi.dashboards.registry import DashboardRegistry, registry, register
from mko_bi.models.dashboard import DashboardConfig


@pytest.fixture
def concrete_dashboard_class():
    """Создает конкретный класс дашборда для тестов."""

    class TestDashboard(DashboardBase):
        def get_data(self, filters):
            return [{"test": "data"}]

        def apply_filters(self, data, filters):
            return data

        def render(self, data):
            return {"rendered": True}

    return TestDashboard


@pytest.fixture
def fresh_registry():
    """Создает новый экземпляр реестра для каждого теста."""
    return DashboardRegistry()


class TestDashboardBase:
    """Тесты для базового класса DashboardBase."""

    def test_is_abstract_class(self):
        """Проверка, что DashboardBase является абстрактным классом."""
        assert issubclass(DashboardBase, ABC)

    def test_has_abstract_methods(self):
        """Проверка наличия абстрактных методов."""
        abstract_methods = DashboardBase.__abstractmethods__
        assert "get_data" in abstract_methods
        assert "apply_filters" in abstract_methods
        assert "render" in abstract_methods

    def test_cannot_instantiate_abstract_class(self):
        """Невозможно создать экземпляр абстрактного класса."""
        with pytest.raises(TypeError):
            DashboardBase(DashboardConfig(graph_types=["bar"]))

    def test_concrete_implementation_can_be_instantiated(self):
        """Конкретная реализация может быть создана."""

        class ConcreteDashboard(DashboardBase):
            def get_data(self, filters):
                return []

            def apply_filters(self, data, filters):
                return data

            def render(self, data):
                return {}

        config = DashboardConfig(graph_types=["bar"])
        dashboard = ConcreteDashboard(config)
        assert dashboard.config == config
        assert dashboard.config.graph_types == ["bar"]

    def test_init_stores_config(self):
        """Проверка сохранения конфигурации при инициализации."""

        class TestDashboard(DashboardBase):
            def get_data(self, filters):
                return []

            def apply_filters(self, data, filters):
                return data

            def render(self, data):
                return {}

        config = DashboardConfig(
            graph_types=["bar", "line"],
            title="Test Dashboard",
            description="Test description",
        )
        dashboard = TestDashboard(config)
        assert dashboard.config.title == "Test Dashboard"
        assert dashboard.config.description == "Test description"
        assert dashboard.config.graph_types == ["bar", "line"]


class TestDashboardRegistry:
    """Тесты для реестра дашбордов DashboardRegistry."""

    def test_initial_state(self, fresh_registry):
        """Проверка начального состояния реестра."""
        assert len(fresh_registry._registry) == 0
        assert len(fresh_registry._instances) == 0

    def test_register_dashboard(self, fresh_registry, concrete_dashboard_class):
        """Регистрация дашборда."""
        fresh_registry.register("test", concrete_dashboard_class)
        assert "test" in fresh_registry._registry
        assert fresh_registry._registry["test"] == concrete_dashboard_class

    def test_register_duplicate_name_raises_error(self, fresh_registry, concrete_dashboard_class):
        """Попытка повторной регистрации вызывает ошибку."""
        fresh_registry.register("test", concrete_dashboard_class)
        with pytest.raises(ValueError, match="уже зарегистрирован"):
            fresh_registry.register("test", concrete_dashboard_class)

    def test_register_invalid_class_raises_error(self, fresh_registry):
        """Попытка зарегистрировать некорректный класс вызывает ошибку."""

        class NotADashboard:
            pass

        with pytest.raises(TypeError, match="наследоваться от DashboardBase"):
            fresh_registry.register("invalid", NotADashboard)

    def test_get_dashboard(self, fresh_registry, concrete_dashboard_class):
        """Получение экземпляра дашборда."""
        config = DashboardConfig(graph_types=["bar"])
        fresh_registry.register("test", concrete_dashboard_class)
        instance = fresh_registry.get("test", config)
        assert isinstance(instance, concrete_dashboard_class)
        assert instance.config == config

    def test_get_nonexistent_dashboard_raises_error(self, fresh_registry):
        """Получение несуществующего дашборда вызывает ошибку."""
        config = DashboardConfig(graph_types=["bar"])
        with pytest.raises(KeyError, match="не найден"):
            fresh_registry.get("nonexistent", config)

    def test_get_creates_and_caches_instance(self, fresh_registry, concrete_dashboard_class):
        """Получение создает и кэширует экземпляр."""
        config = DashboardConfig(graph_types=["bar"])
        fresh_registry.register("test", concrete_dashboard_class)
        instance1 = fresh_registry.get("test", config)
        assert ("test", fresh_registry._generate_config_hash(config)) in fresh_registry._instances
        instance2 = fresh_registry.get("test", config)
        assert instance1 is instance2  # Один и тот же экземпляр

    def test_get_different_configs_create_different_instances(
        self, fresh_registry, concrete_dashboard_class
    ):
        """Разные конфигурации создают разные экземпляры."""
        config1 = DashboardConfig(graph_types=["bar"])
        config2 = DashboardConfig(graph_types=["line"])
        fresh_registry.register("test", concrete_dashboard_class)
        instance1 = fresh_registry.get("test", config1)
        instance2 = fresh_registry.get("test", config2)
        assert instance1 is not instance2
        assert instance1.config != instance2.config

    def test_exists(self, fresh_registry, concrete_dashboard_class):
        """Проверка существования дашборда."""
        assert not fresh_registry.exists("test")
        fresh_registry.register("test", concrete_dashboard_class)
        assert fresh_registry.exists("test")

    def test_clear_cache(self, fresh_registry, concrete_dashboard_class):
        """Очистка кэша."""
        config = DashboardConfig(graph_types=["bar"])
        fresh_registry.register("test", concrete_dashboard_class)
        fresh_registry.get("test", config)
        assert len(fresh_registry._instances) == 1
        fresh_registry.clear_cache()
        assert len(fresh_registry._instances) == 0

    def test_registered_dashboards_property(self, fresh_registry, concrete_dashboard_class):
        """Свойство registered_dashboards."""
        assert fresh_registry.registered_dashboards == []
        fresh_registry.register("test1", concrete_dashboard_class)
        fresh_registry.register("test2", concrete_dashboard_class)
        assert set(fresh_registry.registered_dashboards) == {"test1", "test2"}

    def test_repr(self, fresh_registry):
        """Строковое представление."""
        repr_str = repr(fresh_registry)
        assert "DashboardRegistry" in repr_str
        assert "registered=0" in repr_str
        assert "cached=0" in repr_str


class TestModuleRegistry:
    """Тесты для модульного экземпляра реестра."""

    def test_module_registry_exists(self):
        """Проверка существования модульного экземпляра."""
        assert isinstance(registry, DashboardRegistry)

    def test_register_decorator(self, concrete_dashboard_class):
        """Тест декоратора регистрации."""

        @register("decorated")
        class DecoratedDashboard(DashboardBase):
            def get_data(self, filters):
                return []

            def apply_filters(self, data, filters):
                return data

            def render(self, data):
                return {}

        assert registry.exists("decorated")
        assert "decorated" in registry.registered_dashboards

    def test_get_from_module_registry(self, concrete_dashboard_class):
        """Получение экземпляра из модульного реестра."""
        config = DashboardConfig(graph_types=["bar"])

        @register("module_test")
        class ModuleTestDashboard(DashboardBase):
            def get_data(self, filters):
                return []

            def apply_filters(self, data, filters):
                return data

            def render(self, data):
                return {}

        instance = registry.get("module_test", config)
        assert isinstance(instance, ModuleTestDashboard)


class TestDashboardConfigIntegration:
    """Тесты интеграции с DashboardConfig."""

    def test_config_with_all_fields(self):
        """Тест конфигурации со всеми полями."""

        class FullDashboard(DashboardBase):
            def get_data(self, filters):
                return []

            def apply_filters(self, data, filters):
                return data

            def render(self, data):
                return {}

        config = DashboardConfig(
            graph_types=["bar", "line", "pie"],
            title="Full Test Dashboard",
            description="Full test description",
            filters=[{"field": "year", "type": "select"}],
            aggregations=[{"type": "sum", "field": "revenue"}],
            charts=[{"type": "bar", "x": "category", "y": "value"}],
        )
        fresh_registry = DashboardRegistry()
        fresh_registry.register("full", FullDashboard)
        instance = fresh_registry.get("full", config)
        assert instance.config.title == "Full Test Dashboard"
        assert instance.config.description == "Full test description"
        assert len(instance.config.graph_types) == 3

    def test_config_hash_generation(self):
        """Тест генерации хеша конфигурации."""
        fresh_registry = DashboardRegistry()
        config1 = DashboardConfig(graph_types=["bar"])
        config2 = DashboardConfig(graph_types=["bar"])
        config3 = DashboardConfig(graph_types=["line"])

        hash1 = fresh_registry._generate_config_hash(config1)
        hash2 = fresh_registry._generate_config_hash(config2)
        hash3 = fresh_registry._generate_config_hash(config3)

        assert hash1 == hash2  # Одинаковые конфигурации
        assert hash1 != hash3  # Разные конфигурации

    def test_cache_key_uses_config_hash(self):
        """Ключ кэша использует хеш конфигурации."""

        class TestDashboard(DashboardBase):
            def get_data(self, filters):
                return []

            def apply_filters(self, data, filters):
                return data

            def render(self, data):
                return {}

        fresh_registry = DashboardRegistry()
        config = DashboardConfig(graph_types=["bar"])
        fresh_registry.register("test", TestDashboard)
        fresh_registry.get("test", config)

        config_hash = fresh_registry._generate_config_hash(config)
        cache_key = ("test", config_hash)
        assert cache_key in fresh_registry._instances
