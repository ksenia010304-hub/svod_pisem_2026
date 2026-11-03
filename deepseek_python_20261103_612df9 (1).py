import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Свод писем 1С", layout="wide")
st.title("📨 Свод писем из 1С")
st.caption("Загрузите CSV-файл с таблицей писем (колонки: ID, Тема, Статус, На подписи/согласовании у, Ответственные, Контроль)")

# --- Загрузка файла ---
uploaded_file = st.file_uploader("Выберите CSV-файл", type=["csv"])

if uploaded_file is None:
    st.info("👆 Загрузите CSV-файл, чтобы построить дашборд. Если файла нет, можно сначала скачать пример из предыдущего шага.")
    st.stop()

# Читаем CSV (пробуем разные кодировки, чтобы не спотыкаться о кириллицу)
@st.cache_data
def load_data(file):
    for enc in ["utf-8", "utf-8-sig", "cp1251"]:
        try:
            return pd.read_csv(file, encoding=enc)
        except Exception:
            file.seek(0)
    raise ValueError("Не удалось прочитать файл. Сохраните таблицу в CSV UTF-8.")

df = load_data(uploaded_file)

# На всякий случай убираем лишние пробелы в названиях колонок
df.columns = df.columns.str.strip()

# --- Боковая панель с фильтрами ---
st.sidebar.header("🔎 Фильтры")

# Фильтр по статусу (если колонка есть)
if "Статус" in df.columns:
    status_options = sorted(df["Статус"].dropna().unique().tolist())
    selected_status = st.sidebar.multiselect(
        "Статус письма", options=status_options, default=status_options
    )
else:
    selected_status = None

# Фильтр по руководителю (если колонка есть)
if "На подписи/согласовании у" in df.columns:
    boss_options = sorted(df["На подписи/согласовании у"].dropna().unique().tolist())
    selected_boss = st.sidebar.multiselect(
        "На подписи / согласовании у", options=boss_options, default=boss_options
    )
else:
    selected_boss = None

# --- Применяем фильтры ---
filtered_df = df.copy()

if selected_status is not None and len(selected_status) < len(status_options):
    filtered_df = filtered_df[filtered_df["Статус"].isin(selected_status)]

if selected_boss is not None and len(selected_boss) < len(boss_options):
    filtered_df = filtered_df[filtered_df["На подписи/согласовании у"].isin(selected_boss)]

# --- KPI (ключевые цифры) ---
st.subheader("Ключевые показатели")
col1, col2, col3, col4 = st.columns(4)

total = len(filtered_df)
in_progress = len(filtered_df[~filtered_df["Статус"].isin(["Завершено", "Подписано", "Отклонено"])]) if "Статус" in filtered_df.columns else 0
on_sign = len(filtered_df[filtered_df["Статус"].astype(str).str.contains("подпис", case=False, na=False)]) if "Статус" in filtered_df.columns else 0
on_approve = len(filtered_df[filtered_df["Статус"].astype(str).str.contains("соглас", case=False, na=False)]) if "Статус" in filtered_df.columns else 0

col1.metric("Всего писем", total)
col2.metric("В работе", in_progress)
col3.metric("На подписи", on_sign)
col4.metric("На согласовании", on_approve)

# --- Графики ---
st.subheader("Визуализация")

chart_col1, chart_col2 = st.columns(2)

# График 1: распределение по статусам
if "Статус" in filtered_df.columns:
    status_counts = filtered_df["Статус"].value_counts().reset_index()
    status_counts.columns = ["Статус", "Количество"]
    fig_status = px.bar(
        status_counts,
        x="Статус",
        y="Количество",
        title="Письма по статусам",
        color="Статус",
        text="Количество",
    )
    fig_status.update_layout(showlegend=False, xaxis_title="", yaxis_title="Количество")
    chart_col1.plotly_chart(fig_status, use_container_width=True)
else:
    chart_col1.info("Колонка «Статус» не найдена — график по статусам недоступен.")

# График 2: нагрузка по руководителям
if "На подписи/согласовании у" in filtered_df.columns:
    boss_counts = (
        filtered_df["На подписи/согласовании у"]
        .fillna("Не указан")
        .value_counts()
        .reset_index()
    )
    boss_counts.columns = ["Руководитель", "Количество"]
    fig_boss = px.bar(
        boss_counts,
        x="Руководитель",
        y="Количество",
        title="Письма у руководителей",
        color="Руководитель",
        text="Количество",
    )
    fig_boss.update_layout(showlegend=False, xaxis_title="", yaxis_title="Количество")
    chart_col2.plotly_chart(fig_boss, use_container_width=True)
else:
    chart_col2.info("Колонка «На подписи/согласовании у» не найдена — график по руководителям недоступен.")

# --- Таблица с деталями ---
st.subheader("Детализация писем")
display_cols = [c for c in ["ID", "Тема", "Статус", "На подписи/согласовании у", "Ответственные", "Контроль", "Комментарий"] if c in filtered_df.columns]
st.dataframe(filtered_df[display_cols], use_container_width=True, hide_index=True)