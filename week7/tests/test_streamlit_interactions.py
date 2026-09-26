"""Exercise the real Streamlit script and its user-facing controls."""

from pathlib import Path
import sys

from streamlit.testing.v1 import AppTest


WEEK7 = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WEEK7))


def open_app() -> AppTest:
    app = AppTest.from_file(str(WEEK7 / "app.py"), default_timeout=45).run()
    assert not app.exception
    return app


def test_navigation_and_prediction_controls():
    app = open_app()
    assert app.sidebar.radio[0].value == "系统总览"

    app.sidebar.radio[0].set_value("KPI 预测").run()
    assert not app.exception
    assert app.selectbox[0].label == "预测结果组"
    app.selectbox[0].set_value("Transformer（全网平均 KPI）").run()
    assert not app.exception
    assert "Transformer" in app.multiselect[0].options
    app.multiselect[0].set_value([]).run()
    assert not app.exception
    assert any("至少选择一个模型" in item.value for item in app.warning)


def test_anomaly_and_root_cause_explanations():
    app = open_app()
    app.sidebar.radio[0].set_value("异常检测").run()
    assert not app.exception
    assert app.selectbox[0].value == "异常并集（高召回）"
    assert any("3σ 和 IQR 都是 0" in item.value for item in app.subheader)
    app.selectbox[0].set_value("共同异常（高置信）").run()
    assert not app.exception
    assert any(item.value == "17" for item in app.metric)

    app.sidebar.radio[0].set_value("根因分析").run()
    assert not app.exception
    assert any("根因候选指标如何理解" in item.value for item in app.subheader)
    app.slider[0].set_value(5).run()
    assert not app.exception
    assert app.slider[0].value == 5


def test_kpi_browser_filter():
    app = open_app()
    app.sidebar.radio[0].set_value("数据浏览").run()
    assert not app.exception
    assert app.selectbox[0].value == "1_1_22"
    app.slider[0].set_value((0, 20)).run()
    assert not app.exception
    assert app.slider[0].value == (0, 20)
    assert any(item.value == "21" for item in app.metric)
