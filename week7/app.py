from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from core.data_repository import (
    ProjectFiles,
    data_health,
    list_kpis,
    list_prediction_groups,
    load_anomaly_bundle,
    load_model_metrics,
    load_network_characteristics,
    load_predictions,
    read_kpi_series,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FILES = ProjectFiles(PROJECT_ROOT)

st.set_page_config(page_title="5G KPI 智能运维平台", page_icon="📡", layout="wide")
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem; padding-bottom: 3rem;}
    [data-testid="stMetric"] {background:#f7f9fc; border:1px solid #e2e8f0; padding:14px; border-radius:12px;}
    .hero {padding:1.4rem 1.6rem; border-radius:18px; color:white;
           background:linear-gradient(110deg,#102a43 0%,#1565c0 58%,#00a8a8 100%); margin-bottom:1rem;}
    .hero h1 {font-size:2rem; margin:0 0 .35rem 0;}
    .hero p {margin:0; opacity:.9;}
    .hint {color:#5b6573; font-size:.9rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def cached_metrics() -> pd.DataFrame:
    return load_model_metrics(FILES)


@st.cache_data(show_spinner=False)
def cached_predictions(group: str) -> pd.DataFrame:
    return load_predictions(FILES, group)


@st.cache_data(show_spinner=False)
def cached_anomalies():
    return load_anomaly_bundle(FILES)


@st.cache_data(show_spinner=False)
def cached_characteristics() -> pd.DataFrame:
    return load_network_characteristics(FILES)


@st.cache_data(show_spinner=False)
def cached_kpis() -> list[str]:
    return list_kpis(FILES)


@st.cache_data(show_spinner=False)
def cached_kpi_series(kpi: str) -> pd.DataFrame:
    return read_kpi_series(FILES, kpi)


def csv_download(label: str, data: pd.DataFrame, filename: str) -> None:
    buffer = io.StringIO()
    data.to_csv(buffer, index=False)
    st.download_button(label, buffer.getvalue().encode("utf-8-sig"), filename, "text/csv")


def render_home() -> None:
    metrics = cached_metrics()
    anomalies, summary, _, causes = cached_anomalies()
    best = metrics.loc[metrics["RMSE"].idxmin()]
    union_count = int(anomalies["ml_union_anomaly"].sum())
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("已接入模型", f"{len(metrics)} 个")
    c2.metric("最佳 RMSE", f"{best['RMSE']:.4f}", best["Model"])
    c3.metric("异常时刻", f"{union_count} / {len(anomalies)}")
    c4.metric("根因 KPI", f"{len(causes)} 个")

    left, right = st.columns([1.2, 1])
    with left:
        st.subheader("模型效果总览")
        chart = px.bar(
            metrics.sort_values("RMSE", ascending=False), x="RMSE", y="Model", color="任务范围",
            orientation="h", text_auto=".4f", color_discrete_sequence=px.colors.qualitative.Safe,
        )
        chart.update_layout(height=390, legend_title_text="实验口径", margin=dict(l=0, r=10, t=10, b=0))
        st.plotly_chart(chart, width="stretch")
    with right:
        st.subheader("异常检测覆盖")
        summary_cn = summary.rename(columns={"Method": "方法", "Anomaly_Count": "异常数", "Anomaly_Ratio": "异常率"})
        chart = px.bar(summary_cn, x="方法", y="异常数", color="异常率", text="异常数", color_continuous_scale="Blues")
        chart.update_layout(height=390, margin=dict(l=0, r=0, t=10, b=0), coloraxis_colorbar_title="异常率")
        st.plotly_chart(chart, width="stretch")
    st.info("结论：全网平均 KPI 预测中 LightGBM 的 RMSE 最低（0.00745）；异常检测采用 Isolation Forest 与 One-Class SVM 的并集用于高召回预警。")


def render_prediction() -> None:
    st.header("KPI 预测")
    st.caption("查看第 4–5 周模型结果。不同任务范围分组展示，指标只在相同任务范围内比较。")
    group = st.selectbox("预测结果组", list_prediction_groups())
    data = cached_predictions(group)
    models = [column for column in data.columns if column not in {"time_index", "实际值"}]
    selected = st.multiselect("选择模型", models, default=models[: min(2, len(models))])
    if not selected:
        st.warning("请至少选择一个模型。")
        return
    plot_data = data[["time_index", "实际值", *selected]].melt("time_index", var_name="序列", value_name="KPI")
    fig = px.line(plot_data, x="time_index", y="KPI", color="序列", color_discrete_sequence=["#111827", "#1565c0", "#00a8a8", "#f59e0b"])
    fig.update_layout(height=460, hovermode="x unified", margin=dict(l=0, r=0, t=15, b=0))
    st.plotly_chart(fig, width="stretch")

    metrics = cached_metrics()
    visible = metrics[metrics["Model"].isin(selected)]
    if not visible.empty:
        st.dataframe(visible[["Model", "MAE", "RMSE", "R2", "任务范围"]], width="stretch", hide_index=True)
    csv_download("下载当前预测结果", data[["time_index", "实际值", *selected]], "kpi_predictions.csv")


def render_anomaly() -> None:
    st.header("异常检测")
    results, summary, ranking, _ = cached_anomalies()
    characteristics = cached_characteristics()
    methods = {
        "Isolation Forest": "isolation_forest_anomaly",
        "One-Class SVM": "ocsvm_anomaly",
        "共同异常（高置信）": "ml_common_anomaly",
        "异常并集（高召回）": "ml_union_anomaly",
    }
    label = st.selectbox("检测策略", list(methods), index=3)
    flag = methods[label]
    combined = characteristics[["time_index", "mean_kpi"]].merge(results[["time_index", flag]], on="time_index")
    count = int(combined[flag].sum())
    c1, c2, c3 = st.columns(3)
    c1.metric("检测时刻", len(combined))
    c2.metric("异常时刻", count)
    c3.metric("异常率", f"{count / len(combined):.2%}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=combined["time_index"], y=combined["mean_kpi"], mode="lines", name="全网平均 KPI", line=dict(color="#1565c0")))
    anomalous = combined[combined[flag] == 1]
    fig.add_trace(go.Scatter(x=anomalous["time_index"], y=anomalous["mean_kpi"], mode="markers", name="异常", marker=dict(color="#ef4444", size=9, symbol="diamond")))
    fig.update_layout(height=460, hovermode="x unified", margin=dict(l=0, r=0, t=15, b=0))
    st.plotly_chart(fig, width="stretch")

    tab1, tab2 = st.tabs(["检测摘要", "异常时刻排行"])
    with tab1:
        view = summary.copy()
        view["Anomaly_Ratio"] = view["Anomaly_Ratio"].map(lambda value: f"{value:.2%}")
        st.dataframe(view, width="stretch", hide_index=True)
        st.subheader("为什么 3σ 和 IQR 都是 0？")
        network_mean = characteristics["mean_kpi"]
        sigma_low = network_mean.mean() - 3 * network_mean.std(ddof=1)
        sigma_high = network_mean.mean() + 3 * network_mean.std(ddof=1)
        q1, q3 = network_mean.quantile([0.25, 0.75])
        iqr_low, iqr_high = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
        st.write(
            f"这两种统计规则检查每个时刻 **2880 个 KPI 的平均值**，并非逐个 Beam 检查。"
            f"本数据的平均值范围为 {network_mean.min():.4f}–{network_mean.max():.4f}；"
            f"3σ 界限为 {sigma_low:.4f}–{sigma_high:.4f}，"
            f"IQR 界限为 {iqr_low:.4f}–{iqr_high:.4f}。"
            "840 个平均值均处在两组界限内，所以两种规则各检出 0 个。"
            "多 KPI 平均会平滑局部尖峰；0 个仅说明此聚合序列没有越过当前阈值，不能推断所有 KPI 或网络时刻都正常。"
        )
    with tab2:
        st.dataframe(ranking.head(20), width="stretch", hide_index=True)
        csv_download("下载异常排行", ranking, "anomaly_time_ranking.csv")


def render_causes() -> None:
    st.header("根因分析")
    _, _, ranking, causes = cached_anomalies()
    top_n = st.slider("显示前 N 个根因 KPI", 5, 30, 15)
    top = causes.head(top_n).sort_values("contribution_score")
    fig = px.bar(top, x="contribution_score", y="kpi", orientation="h", color="abs_correlation", text_auto=".3f", color_continuous_scale="Teal")
    fig.update_layout(height=max(430, top_n * 27), margin=dict(l=0, r=0, t=15, b=0), coloraxis_colorbar_title="相关度")
    st.plotly_chart(fig, width="stretch")
    st.dataframe(causes.head(top_n), width="stretch", hide_index=True)
    st.subheader("根因候选指标如何理解")
    st.write(
        "KPI 名称采用“小区_扇区_Beam”格式，例如 1_1_22。排名比较的是 40 个机器学习异常并集时刻与其余时刻的归一化 KPI 分布。"
        "normal_mean、anomaly_mean 是两组均值；mean_difference = anomaly_mean − normal_mean；"
        "normal_std、anomaly_std 是两组标准差；correlation_with_anomaly 是 KPI 与 0/1 异常标签的相关系数。"
        "contribution_score = 0.5 × 归一化绝对均值差 + 0.2 × 归一化绝对标准差差 + 0.3 × 归一化绝对相关系数，"
        "再按分数从高到低赋予 rank。这里的归一化是在 2880 个 KPI 之间分别做最小最大缩放。"
    )
    st.caption(
        f"最高风险时刻：time_index = {int(ranking.iloc[0]['time_index'])}，由异常检测模型分数融合排序。"
        "KPI 排名是整个异常集合的统计关联线索，不是该单一时刻的解释，也不是故障因果概率。"
    )
    csv_download("下载根因排名", causes, "root_cause_kpi_ranking.csv")


def render_data() -> None:
    st.header("KPI 数据浏览")
    kpis = cached_kpis()
    default = "1_1_22" if "1_1_22" in kpis else kpis[0]
    kpi = st.selectbox("选择 KPI（格式：小区_扇区_Beam）", kpis, index=kpis.index(default))
    data = cached_kpi_series(kpi)
    start, end = st.slider("时间范围", int(data.time_index.min()), int(data.time_index.max()), (int(data.time_index.min()), int(data.time_index.max())))
    view = data[data.time_index.between(start, end)]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("样本数", len(view))
    c2.metric("平均值", f"{view[kpi].mean():.4f}")
    c3.metric("最大值", f"{view[kpi].max():.4f}")
    c4.metric("标准差", f"{view[kpi].std():.4f}")
    fig = px.area(view, x="time_index", y=kpi, color_discrete_sequence=["#00a8a8"])
    fig.update_layout(height=420, margin=dict(l=0, r=0, t=15, b=0))
    st.plotly_chart(fig, width="stretch")
    csv_download("下载当前 KPI", view, f"kpi_{kpi}.csv")


st.markdown('<div class="hero"><h1>📡 5G KPI 智能运维平台</h1><p>预测 · 异常检测 · 根因定位 · 数据浏览</p></div>', unsafe_allow_html=True)
health = data_health(FILES)
if not health["ready"]:
    missing = [name for name, ok in health["files"].items() if not ok]
    st.error("系统数据不完整：" + "、".join(missing))
    st.stop()

page = st.sidebar.radio("功能导航", ["系统总览", "KPI 预测", "异常检测", "根因分析", "数据浏览"])
st.sidebar.success("数据与模型结果已就绪")
st.sidebar.caption("Week 7 · Windows 集成版")

pages = {
    "系统总览": render_home,
    "KPI 预测": render_prediction,
    "异常检测": render_anomaly,
    "根因分析": render_causes,
    "数据浏览": render_data,
}
pages[page]()
