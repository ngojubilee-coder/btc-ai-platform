"""Unit tests for train.py and download_data.py."""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ─── train.py tests ───

class TestTrainLog:
    def test_log_info(self):
        from train import log
        log("test message", "INFO")

    def test_log_ok(self):
        from train import log
        log("test message", "OK")

    def test_log_err(self):
        from train import log
        log("test message", "ERR")


class TestPrepareData:
    def test_prepare_data_basic(self):
        from train import prepare_data
        df = pd.DataFrame({
            "timestamp": pd.date_range("2024-01-01", periods=100, freq="1min"),
            "feature_1": np.random.randn(100),
            "feature_2": np.random.randn(100),
            "target_return_15m": np.random.randn(100),
        })
        feature_cols = ["feature_1", "feature_2"]
        X_train, X_test, y_train, y_test = prepare_data(df, feature_cols, target_col="target_return_15m")
        assert len(X_train) + len(X_test) <= 100
        assert len(y_train) == len(X_train)
        assert len(y_test) == len(X_test)
        assert set(y_train.unique()).issubset({0, 1})
        assert set(y_test.unique()).issubset({0, 1})

    def test_prepare_data_custom_split(self):
        from train import prepare_data
        df = pd.DataFrame({
            "feature_1": np.random.randn(200),
            "target_return_15m": np.random.randn(200),
        })
        X_train, X_test, y_train, y_test = prepare_data(df, ["feature_1"], target_col="target_return_15m", test_size=0.3)
        assert len(X_test) == 60
        assert len(X_train) == 140

    def test_prepare_data_drops_nan(self):
        from train import prepare_data
        df = pd.DataFrame({
            "feature_1": np.random.randn(100),
            "target_return_15m": [np.nan] * 20 + list(np.random.randn(80)),
        })
        X_train, X_test, y_train, y_test = prepare_data(df, ["feature_1"], target_col="target_return_15m")
        assert len(X_train) + len(X_test) <= 80


class TestSaveResults:
    def test_save_results_creates_json(self, tmp_path):
        from train import save_results
        import train as train_module
        original_dir = train_module.DATA_DIR
        train_module.DATA_DIR = str(tmp_path)
        try:
            metrics = {"model": "test", "accuracy": 0.85, "f1": 0.9, "train_time_sec": 1.5}
            backtest = {"win_rate": 55.0, "correct": 110, "total": 200, "pnl": 20}
            save_results(metrics, backtest)
            results_dir = os.path.join(str(tmp_path), "results")
            assert os.path.isdir(results_dir)
            files = [f for f in os.listdir(results_dir) if f.endswith(".json")]
            assert len(files) == 1
            import json
            with open(os.path.join(results_dir, files[0])) as f:
                data = json.load(f)
            assert data["metrics"]["model"] == "test"
            assert data["metrics"]["accuracy"] == 0.85
            assert data["backtest"]["win_rate"] == 55.0
        finally:
            train_module.DATA_DIR = original_dir

    def test_save_results_numpy_conversion(self, tmp_path):
        from train import save_results
        import train as train_module
        original_dir = train_module.DATA_DIR
        train_module.DATA_DIR = str(tmp_path)
        try:
            metrics = {
                "model": "test",
                "accuracy": np.float32(0.75),
                "f1": np.float64(0.8),
                "n_train": np.int32(1000),
                "n_test": np.int64(200),
            }
            save_results(metrics, None)
            results_dir = os.path.join(str(tmp_path), "results")
            files = [f for f in os.listdir(results_dir) if f.endswith(".json")]
            import json
            with open(os.path.join(results_dir, files[0])) as f:
                data = json.load(f)
            assert isinstance(data["metrics"]["accuracy"], float)
            assert isinstance(data["metrics"]["n_train"], int)
        finally:
            train_module.DATA_DIR = original_dir


class TestRunBacktest:
    def test_backtest_xgboost_like(self):
        from train import run_backtest
        from sklearn.ensemble import RandomForestClassifier
        X_train = pd.DataFrame({"f1": np.random.randn(200), "f2": np.random.randn(200)})
        y_train = (np.random.randn(200) > 0).astype(int)
        X_test = pd.DataFrame({"f1": np.random.randn(50), "f2": np.random.randn(50)})
        y_test = pd.Series((np.random.randn(50) > 0).astype(int))
        model = RandomForestClassifier(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)
        result = run_backtest(model, X_test, y_test, model_type="xgboost")
        assert "win_rate" in result
        assert "correct" in result
        assert "total" in result
        assert "pnl" in result
        assert result["total"] == 50
        assert 0 <= result["win_rate"] <= 100
        assert isinstance(result["pnl"], int)


# ─── download_data.py tests ───

class TestGenerateSyntheticDataset:
    def test_generates_correct_shape(self, tmp_path):
        import download_data as dd
        original_data_dir = dd.DATA_DIR
        original_parquet = dd.PARQUET_PATH
        dd.DATA_DIR = str(tmp_path)
        dd.PARQUET_PATH = os.path.join(str(tmp_path), "test_dataset.parquet")
        try:
            df = dd.generate_synthetic_dataset(n_rows=500)
            assert len(df) == 500
            assert "price_close" in df.columns
            assert "volume" in df.columns
            assert "timestamp" in df.columns
        finally:
            dd.DATA_DIR = original_data_dir
            dd.PARQUET_PATH = original_parquet

    def test_has_technical_indicators(self, tmp_path):
        import download_data as dd
        original_data_dir = dd.DATA_DIR
        original_parquet = dd.PARQUET_PATH
        dd.DATA_DIR = str(tmp_path)
        dd.PARQUET_PATH = os.path.join(str(tmp_path), "test_dataset.parquet")
        try:
            df = dd.generate_synthetic_dataset(n_rows=500)
            for col in ["sma_7", "ema_14", "rsi_14", "macd", "bb_upper", "bb_lower"]:
                assert col in df.columns, f"Missing column: {col}"
        finally:
            dd.DATA_DIR = original_data_dir
            dd.PARQUET_PATH = original_parquet

    def test_has_target_columns(self, tmp_path):
        import download_data as dd
        original_data_dir = dd.DATA_DIR
        original_parquet = dd.PARQUET_PATH
        dd.DATA_DIR = str(tmp_path)
        dd.PARQUET_PATH = os.path.join(str(tmp_path), "test_dataset.parquet")
        try:
            df = dd.generate_synthetic_dataset(n_rows=500)
            for horizon in [5, 15, 30, 60]:
                assert f"target_return_{horizon}m" in df.columns
        finally:
            dd.DATA_DIR = original_data_dir
            dd.PARQUET_PATH = original_parquet

    def test_saves_parquet_file(self, tmp_path):
        import download_data as dd
        original_data_dir = dd.DATA_DIR
        original_parquet = dd.PARQUET_PATH
        dd.DATA_DIR = str(tmp_path)
        parquet_path = os.path.join(str(tmp_path), "test_dataset.parquet")
        dd.PARQUET_PATH = parquet_path
        try:
            dd.generate_synthetic_dataset(n_rows=200)
            assert os.path.isfile(parquet_path)
            df_loaded = pd.read_parquet(parquet_path)
            assert len(df_loaded) == 200
        finally:
            dd.DATA_DIR = original_data_dir
            dd.PARQUET_PATH = original_parquet

    def test_no_nan_after_fill(self, tmp_path):
        import download_data as dd
        original_data_dir = dd.DATA_DIR
        original_parquet = dd.PARQUET_PATH
        dd.DATA_DIR = str(tmp_path)
        dd.PARQUET_PATH = os.path.join(str(tmp_path), "test_dataset.parquet")
        try:
            df = dd.generate_synthetic_dataset(n_rows=500)
            assert not df.isnull().any().any(), "Dataset should have no NaN values"
        finally:
            dd.DATA_DIR = original_data_dir
            dd.PARQUET_PATH = original_parquet

    def test_rsi_in_valid_range(self, tmp_path):
        import download_data as dd
        original_data_dir = dd.DATA_DIR
        original_parquet = dd.PARQUET_PATH
        dd.DATA_DIR = str(tmp_path)
        dd.PARQUET_PATH = os.path.join(str(tmp_path), "test_dataset.parquet")
        try:
            df = dd.generate_synthetic_dataset(n_rows=500)
            rsi = df["rsi_14"].dropna()
            assert rsi.min() >= 0
            assert rsi.max() <= 100
        finally:
            dd.DATA_DIR = original_data_dir
            dd.PARQUET_PATH = original_parquet


class TestLoadDataset:
    def test_load_dataset_missing_file(self):
        from train import load_dataset
        original_path = os.getenv("PARQUET_PATH")
        os.environ["PARQUET_PATH"] = "/nonexistent/path/file.parquet"
        import importlib
        import train as train_module
        importlib.reload(train_module)
        result = train_module.load_dataset()
        assert result is None
        if original_path:
            os.environ["PARQUET_PATH"] = original_path
