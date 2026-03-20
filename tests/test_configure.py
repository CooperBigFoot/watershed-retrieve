from pathlib import Path
from unittest.mock import patch

import pytest

import watershed_retrieve as wr
import watershed_retrieve._api as api_mod
from watershed_retrieve._store import LocalParquetStore, R2ParquetStore
from watershed_retrieve._types import Backend


class TestConfigure:
    def test_data_dir_sets_local_store(self, synthetic_parquet_dir: Path) -> None:
        wr.configure(synthetic_parquet_dir)
        assert isinstance(api_mod._store, LocalParquetStore)

    def test_data_dir_string(self, synthetic_parquet_dir: Path) -> None:
        wr.configure(str(synthetic_parquet_dir))
        assert isinstance(api_mod._store, LocalParquetStore)

    def test_no_args_sets_r2_store(self) -> None:
        wr.configure()
        assert isinstance(api_mod._store, R2ParquetStore)

    def test_backend_r2_sets_r2_store(self) -> None:
        wr.configure(backend=Backend.R2)
        assert isinstance(api_mod._store, R2ParquetStore)

    def test_backend_local_with_env_var(self, synthetic_parquet_dir: Path) -> None:
        with patch.dict("os.environ", {"WATERSHED_RETRIEVE_DATA_DIR": str(synthetic_parquet_dir)}):
            wr.configure(backend=Backend.LOCAL)
            assert isinstance(api_mod._store, LocalParquetStore)

    def test_backend_local_without_env_var_raises(self) -> None:
        from watershed_retrieve import ConfigurationError

        with patch.dict("os.environ", {}, clear=True), pytest.raises(ConfigurationError, match="requires data_dir"):
            wr.configure(backend=Backend.LOCAL)

    def test_configuration_error_is_watershed_retrieve_error(self) -> None:
        from watershed_retrieve import WatershedRetrieveError

        with patch.dict("os.environ", {}, clear=True), pytest.raises(WatershedRetrieveError):
            wr.configure(backend=Backend.LOCAL)

    def test_reconfigure_replaces_store(self, synthetic_parquet_dir: Path) -> None:
        wr.configure(synthetic_parquet_dir)
        first_store = api_mod._store
        wr.configure(backend=Backend.R2)
        assert api_mod._store is not first_store
        assert isinstance(api_mod._store, R2ParquetStore)


class TestDefaultBackend:
    def test_r2_when_no_env_var(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            assert api_mod._default_backend() is Backend.R2

    def test_local_when_env_var_set(self, synthetic_parquet_dir: Path) -> None:
        with patch.dict("os.environ", {"WATERSHED_RETRIEVE_DATA_DIR": str(synthetic_parquet_dir)}):
            assert api_mod._default_backend() is Backend.LOCAL


class TestGetStoreAutoInit:
    def test_defaults_to_r2_without_env_var(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            store = api_mod._get_store()
            assert isinstance(store, R2ParquetStore)

    def test_defaults_to_local_with_env_var(self, synthetic_parquet_dir: Path) -> None:
        with patch.dict("os.environ", {"WATERSHED_RETRIEVE_DATA_DIR": str(synthetic_parquet_dir)}):
            store = api_mod._get_store()
            assert isinstance(store, LocalParquetStore)

    def test_lazy_init_reuses_store(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            store1 = api_mod._get_store()
            store2 = api_mod._get_store()
            assert store1 is store2
