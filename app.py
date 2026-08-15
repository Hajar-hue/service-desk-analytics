
import os
import re
from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

import altair as alt
import numpy as np
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from google import genai
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


# =========================================================
# ENVIRONMENT
# =========================================================

load_dotenv()

GEMINI_MODEL = "gemini-3.6-flash"


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="Service Desk Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# GLOBAL UI STYLE
# =========================================================

st.markdown(
    """
    <style>
        :root {
            --navy: #082c57;
            --navy-2: #0b3c73;
            --blue: #0f4c97;
            --green: #138a4b;
            --red: #cf3d35;
            --orange: #d58a00;
            --ink: #10233f;
            --muted: #637083;
            --surface: #ffffff;
            --page: #f3f7fb;
            --line: #dfe7ef;
        }

        html {
            scroll-behavior: smooth;
        }

        .stApp {
            background:
                radial-gradient(circle at top right, rgba(15, 76, 151, 0.05), transparent 28%),
                linear-gradient(180deg, #f6f9fc 0%, #f2f6fa 100%);
        }

        [data-testid="stHeader"] {
            background: rgba(246, 249, 252, 0.85);
            backdrop-filter: blur(8px);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #082c57 0%, #06264a 100%);
            border-right: 1px solid rgba(255,255,255,0.08);
        }

        [data-testid="stSidebar"] * {
            color: #ffffff;
        }

        [data-testid="stSidebar"] .sidebar-title {
            font-size: 1.28rem;
            font-weight: 750;
            letter-spacing: 0.02em;
            line-height: 1.2;
            margin-bottom: 0.65rem;
        }

        [data-testid="stSidebar"] .sidebar-subtle {
            color: rgba(255,255,255,0.72);
            font-size: 0.78rem;
            line-height: 1.45;
        }

        [data-testid="stSidebar"] .sidebar-rule {
            height: 1px;
            background: rgba(255,255,255,0.18);
            margin: 0.9rem 0 1rem 0;
        }

        [data-testid="stSidebar"] .nav-link {
            display: block;
            text-decoration: none;
            color: rgba(255,255,255,0.92);
            padding: 0.72rem 0.85rem;
            border-radius: 8px;
            margin: 0.18rem 0;
            font-size: 0.9rem;
        }

        [data-testid="stSidebar"] .nav-link:hover {
            background: rgba(255,255,255,0.10);
            color: #ffffff;
        }

        [data-testid="stSidebar"] .dataset-box {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 9px;
            padding: 0.8rem;
            margin-top: 0.4rem;
        }

        .main .block-container {
            max-width: 1420px;
            padding-top: 1.4rem;
            padding-bottom: 2rem;
        }

        h1, h2, h3, h4 {
            color: var(--ink);
            letter-spacing: -0.015em;
        }

        .section-anchor {
            scroll-margin-top: 5rem;
        }

        .page-title {
            font-size: 2rem;
            font-weight: 760;
            color: var(--ink);
            margin-bottom: 0.1rem;
        }

        .page-subtitle {
            color: var(--muted);
            font-size: 0.95rem;
            margin-bottom: 0;
        }

        .kpi-card {
            background: rgba(255,255,255,0.96);
            border: 1px solid var(--line);
            border-radius: 12px;
            padding: 1.05rem 1.05rem 0.9rem 1.05rem;
            box-shadow: 0 6px 18px rgba(16,35,63,0.05);
            min-height: 116px;
        }

        .kpi-label {
            color: #43516a;
            font-size: 0.78rem;
            font-weight: 650;
            margin-bottom: 0.55rem;
        }

        .kpi-value {
            font-size: 1.72rem;
            font-weight: 780;
            line-height: 1.05;
            color: var(--ink);
            margin-bottom: 0.48rem;
        }

        .kpi-note {
            color: #8793a5;
            font-size: 0.72rem;
        }

        .kpi-green .kpi-value { color: var(--green); }
        .kpi-red .kpi-value { color: var(--red); }
        .kpi-blue .kpi-value { color: var(--blue); }

        .panel {
            background: rgba(255,255,255,0.97);
            border: 1px solid var(--line);
            border-radius: 12px;
            box-shadow: 0 6px 18px rgba(16,35,63,0.045);
            padding: 1rem 1.05rem;
            margin-bottom: 0.65rem;
        }

        .panel-title {
            color: var(--ink);
            font-size: 0.98rem;
            font-weight: 720;
            margin-bottom: 0.75rem;
        }

        .insight-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0;
        }

        .insight-item {
            padding: 0.25rem 1.15rem 0.25rem 0.2rem;
            min-height: 66px;
        }

        .insight-item + .insight-item {
            border-left: 1px solid var(--line);
            padding-left: 1.15rem;
        }

        .insight-label {
            color: #66758a;
            font-size: 0.72rem;
            margin-bottom: 0.28rem;
        }

        .insight-value {
            color: var(--ink);
            font-size: 0.92rem;
            font-weight: 680;
        }

        .change-card {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 10px;
            padding: 0.86rem 0.9rem;
            margin-bottom: 0.58rem;
        }

        .change-title {
            color: #526174;
            font-size: 0.74rem;
            margin-bottom: 0.35rem;
        }

        .change-value {
            font-size: 1.03rem;
            font-weight: 760;
            color: var(--ink);
        }

        .positive { color: var(--green); }
        .negative { color: var(--red); }
        .neutral { color: var(--blue); }

        .assessment {
            background: #edf8f1;
            border: 1px solid #cde6d4;
            border-radius: 9px;
            color: #244c32;
            padding: 0.85rem 0.95rem;
            font-size: 0.86rem;
            margin-top: 0.6rem;
        }

        .section-heading {
            font-size: 1.26rem;
            font-weight: 760;
            color: var(--ink);
            margin: 0.25rem 0 0.75rem 0;
        }

        .section-copy {
            color: var(--muted);
            font-size: 0.84rem;
            margin-top: -0.45rem;
            margin-bottom: 0.85rem;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 14px rgba(16,35,63,0.035);
        }

        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button {
            background: var(--navy);
            color: white;
            border: 1px solid var(--navy);
            border-radius: 8px;
            padding: 0.52rem 0.9rem;
            font-weight: 650;
        }

        div[data-testid="stButton"] > button:hover,
        div[data-testid="stDownloadButton"] > button:hover {
            background: var(--navy-2);
            color: white;
            border-color: var(--navy-2);
        }

        .footer {
            color: #8793a5;
            text-align: center;
            font-size: 0.72rem;
            padding: 1.3rem 0 0.2rem 0;
        }


        .landing-shell {
            max-width: 860px;
            margin: 7.5rem auto 0 auto;
        }

        .landing-card {
            background: rgba(255,255,255,0.98);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 2.4rem 2.5rem 2.2rem 2.5rem;
            box-shadow: 0 18px 42px rgba(16,35,63,0.08);
            text-align: center;
        }

        .landing-eyebrow {
            color: var(--blue);
            font-size: 0.78rem;
            font-weight: 750;
            letter-spacing: 0.11em;
            text-transform: uppercase;
            margin-bottom: 0.85rem;
        }

        .landing-title {
            color: var(--ink);
            font-size: 2.25rem;
            line-height: 1.08;
            font-weight: 780;
            letter-spacing: -0.025em;
            margin-bottom: 0.7rem;
        }

        .landing-copy {
            max-width: 620px;
            margin: 0 auto 1.45rem auto;
            color: var(--muted);
            font-size: 0.98rem;
            line-height: 1.65;
        }

        .landing-features {
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 0.65rem;
            flex-wrap: wrap;
            margin-top: 1.15rem;
            color: #6f7d90;
            font-size: 0.78rem;
        }

        .landing-dot {
            color: #aab5c3;
        }

        .landing-note {
            margin-top: 0.8rem;
            color: #8b97a8;
            font-size: 0.72rem;
        }

        /* Make the upload control feel like part of the landing card */
        div[data-testid="stFileUploader"] {
            max-width: 760px;
            margin: 0.9rem auto 0 auto;
        }

        div[data-testid="stFileUploader"] section {
            background: #f8fbfe;
            border: 1.5px dashed #b9c8d9;
            border-radius: 14px;
            padding: 1.15rem 1rem;
        }

        div[data-testid="stFileUploader"] section:hover {
            border-color: #7fa0c4;
            background: #f5f9fd;
        }

        div[data-testid="stFileUploader"] small {
            color: #8a96a7;
        }

        @media (max-width: 900px) {
            .insight-grid {
                grid-template-columns: 1fr;
            }
            .insight-item + .insight-item {
                border-left: 0;
                border-top: 1px solid var(--line);
                padding-left: 0.2rem;
                padding-top: 0.8rem;
            }
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# HELPERS
# =========================================================

def clean_column_names(dataframe):
    dataframe = dataframe.copy()

    dataframe.columns = (
        dataframe.columns
        .astype(str)
        .str.strip()
        .str.replace(" ", "_", regex=False)
        .str.replace("-", "_", regex=False)
    )

    return dataframe


def convert_date_column(series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")

    numeric = pd.to_numeric(series, errors="coerce")
    numeric_ratio = numeric.notna().mean()

    if (
        numeric_ratio > 0.8
        and numeric.dropna().size > 0
        and numeric.dropna().median() > 20000
    ):
        return pd.to_datetime(
            numeric,
            unit="D",
            origin="1899-12-30",
            errors="coerce",
        )

    return pd.to_datetime(series, errors="coerce")


def duration_to_hours(value):
    if pd.isna(value):
        return np.nan

    if isinstance(value, pd.Timedelta):
        return value.total_seconds() / 3600

    if isinstance(
        value,
        (int, float, np.integer, np.floating),
    ):
        return float(value)

    text = str(value).strip()

    if not text:
        return np.nan

    try:
        return float(text)
    except ValueError:
        pass

    try:
        return pd.to_timedelta(text).total_seconds() / 3600
    except Exception:
        return np.nan


def calculate_resolution_sla_flag(dataframe):
    if "Resolution_Status" not in dataframe.columns:
        return pd.Series(0, index=dataframe.index)

    status = (
        dataframe["Resolution_Status"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    return (
        status
        .str.contains("violat", na=False)
        .astype(int)
    )


def calculate_overall_metrics(dataframe):
    total_tickets = len(dataframe)

    sla_violations = int(
        dataframe["SLA_Violation_Flag"].sum()
    )

    violation_rate = (
        sla_violations / total_tickets * 100
        if total_tickets
        else 0.0
    )

    compliance_rate = 100 - violation_rate

    return {
        "Total_Tickets": total_tickets,
        "SLA_Violations": sla_violations,
        "SLA_Violation_Rate": violation_rate,
        "SLA_Compliance_Rate": compliance_rate,
        "Avg_First_Response_Hours": (
            dataframe["First_Response_Time_Hours"].mean()
        ),
        "Avg_Resolution_Hours": (
            dataframe["Resolution_Hours"].mean()
        ),
    }


def calculate_region_performance(dataframe):
    if "Region" not in dataframe.columns:
        return pd.DataFrame()

    region_data = (
        dataframe
        .assign(
            Region=dataframe["Region"].fillna("Unknown")
        )
        .groupby("Region")
        .agg(
            Total_Tickets=("Ticket_ID", "count"),
            SLA_Violations=("SLA_Violation_Flag", "sum"),
        )
        .reset_index()
    )

    region_data["SLA_Violation_Rate"] = np.where(
        region_data["Total_Tickets"] > 0,
        (
            region_data["SLA_Violations"]
            / region_data["Total_Tickets"]
            * 100
        ),
        0,
    )

    region_data["SLA_Violation_Rate"] = (
        region_data["SLA_Violation_Rate"].round(2)
    )

    return (
        region_data
        .sort_values(
            "SLA_Violation_Rate",
            ascending=False,
        )
        .reset_index(drop=True)
    )


def calculate_agent_performance(dataframe):
    if "Agent_ID" not in dataframe.columns:
        return pd.DataFrame()

    agent_data = (
        dataframe
        .assign(
            Agent_ID=dataframe["Agent_ID"].fillna("Unknown")
        )
        .groupby("Agent_ID")
        .agg(
            Tickets_Handled=("Ticket_ID", "count"),
            Avg_First_Response_Hours=(
                "First_Response_Time_Hours",
                "mean",
            ),
            SLA_Violations=("SLA_Violation_Flag", "sum"),
        )
        .reset_index()
    )

    agent_data["SLA_Violation_Rate"] = np.where(
        agent_data["Tickets_Handled"] > 0,
        (
            agent_data["SLA_Violations"]
            / agent_data["Tickets_Handled"]
            * 100
        ),
        0,
    )

    agent_data["Avg_First_Response_Hours"] = (
        agent_data["Avg_First_Response_Hours"].round(2)
    )

    agent_data["SLA_Violation_Rate"] = (
        agent_data["SLA_Violation_Rate"].round(2)
    )

    return agent_data


def calculate_ytd_comparison(dataframe):
    data_2025 = (
        dataframe[
            dataframe["Year"] == 2025
        ]
        .copy()
    )

    if data_2025.empty:
        return None, None

    latest_2025_date = (
        data_2025["Created_Time"]
        .dropna()
        .max()
    )

    if pd.isna(latest_2025_date):
        return None, None

    month = latest_2025_date.month
    day = latest_2025_date.day

    start_2024 = pd.Timestamp(2024, 1, 1)
    end_2024 = pd.Timestamp(
        year=2024,
        month=month,
        day=day,
        hour=23,
        minute=59,
        second=59,
    )

    start_2025 = pd.Timestamp(2025, 1, 1)
    end_2025 = pd.Timestamp(
        year=2025,
        month=month,
        day=day,
        hour=23,
        minute=59,
        second=59,
    )

    ytd_2024 = dataframe[
        (dataframe["Created_Time"] >= start_2024)
        & (dataframe["Created_Time"] <= end_2024)
    ].copy()

    ytd_2025 = dataframe[
        (dataframe["Created_Time"] >= start_2025)
        & (dataframe["Created_Time"] <= end_2025)
    ].copy()

    rows = []

    for year, subset in [
        (2024, ytd_2024),
        (2025, ytd_2025),
    ]:
        metrics = calculate_overall_metrics(subset)

        rows.append(
            {
                "Year": year,
                "Total_Tickets": metrics["Total_Tickets"],
                "SLA_Violations": metrics["SLA_Violations"],
                "SLA_Violation_Rate": metrics["SLA_Violation_Rate"],
                "SLA_Compliance_Rate": metrics["SLA_Compliance_Rate"],
                "Avg_First_Response_Hours": metrics[
                    "Avg_First_Response_Hours"
                ],
                "Avg_Resolution_Hours": metrics[
                    "Avg_Resolution_Hours"
                ],
            }
        )

    summary = pd.DataFrame(rows)

    for column in [
        "SLA_Violation_Rate",
        "SLA_Compliance_Rate",
        "Avg_First_Response_Hours",
        "Avg_Resolution_Hours",
    ]:
        summary[column] = summary[column].round(2)

    return summary, latest_2025_date


def create_ai_context(
    overall_metrics,
    region_summary,
    agent_summary,
    ytd_summary,
    common_priority,
):
    lines = [
        "OVERALL SERVICE DESK PERFORMANCE",
        (
            f"Total tickets: "
            f"{overall_metrics['Total_Tickets']:,}"
        ),
        (
            f"SLA violations: "
            f"{overall_metrics['SLA_Violations']:,}"
        ),
        (
            f"SLA violation rate: "
            f"{overall_metrics['SLA_Violation_Rate']:.2f}%"
        ),
        (
            f"SLA compliance rate: "
            f"{overall_metrics['SLA_Compliance_Rate']:.2f}%"
        ),
        (
            "Average first response: "
            f"{overall_metrics['Avg_First_Response_Hours']:.2f} hours"
        ),
        (
            "Average resolution time: "
            f"{overall_metrics['Avg_Resolution_Hours']:.2f} hours"
        ),
        (
            f"Most common priority: "
            f"{common_priority}"
        ),
    ]

    if not region_summary.empty:
        lines.append("\nREGION PERFORMANCE")

        for _, row in region_summary.iterrows():
            lines.append(
                f"{row['Region']}: "
                f"{int(row['Total_Tickets'])} tickets, "
                f"{int(row['SLA_Violations'])} SLA violations, "
                f"{row['SLA_Violation_Rate']:.2f}% SLA violation rate."
            )

    if not agent_summary.empty:
        lines.append("\nAGENT PERFORMANCE")

        eligible_agents = (
            agent_summary[
                agent_summary["Tickets_Handled"] >= 50
            ]
            .sort_values(
                "Tickets_Handled",
                ascending=False,
            )
            .head(10)
        )

        for _, row in eligible_agents.iterrows():
            lines.append(
                f"{row['Agent_ID']}: "
                f"{int(row['Tickets_Handled'])} tickets, "
                f"{int(row['SLA_Violations'])} SLA violations, "
                f"{row['SLA_Violation_Rate']:.2f}% SLA violation rate, "
                f"{row['Avg_First_Response_Hours']:.2f} hours "
                f"average first response."
            )

    if ytd_summary is not None:
        lines.append("\nFAIR YEAR-TO-DATE COMPARISON")

        for _, row in ytd_summary.iterrows():
            lines.append(
                f"{int(row['Year'])} YTD: "
                f"{int(row['Total_Tickets'])} tickets, "
                f"{int(row['SLA_Violations'])} SLA violations, "
                f"{row['SLA_Violation_Rate']:.2f}% SLA violation rate, "
                f"{row['SLA_Compliance_Rate']:.2f}% compliance, "
                f"{row['Avg_First_Response_Hours']:.2f} hours "
                f"average first response, "
                f"{row['Avg_Resolution_Hours']:.2f} hours "
                f"average resolution."
            )

    return "\n".join(lines)


def metric_card(label, value, note="All time", tone=""):
    return f"""
    <div class="kpi-card {tone}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-note">{note}</div>
    </div>
    """


def change_card(label, value, detail, css_class="neutral"):
    return f"""
    <div class="change-card">
        <div class="change-title">{label}</div>
        <div class="change-value {css_class}">{value}</div>
        <div class="kpi-note">{detail}</div>
    </div>
    """


# =========================================================
# PDF HELPERS
# =========================================================

def markdown_inline_to_reportlab(text):
    text = escape(str(text))

    text = re.sub(
        r"\*\*(.+?)\*\*",
        r"<b>\1</b>",
        text,
    )

    text = re.sub(
        r"__(.+?)__",
        r"<b>\1</b>",
        text,
    )

    return text


def build_executive_pdf(
    executive_text,
    overall_metrics,
    ytd_summary,
    source_name,
):
    buffer = BytesIO()

    page_width, page_height = A4

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=18 * mm,
        bottomMargin=17 * mm,
        title="Executive AI Brief",
        author="Service Desk Analytics",
    )

    base_styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ExecutiveTitle",
        parent=base_styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=28,
        textColor=colors.HexColor("#102A43"),
        alignment=TA_CENTER,
        spaceAfter=4 * mm,
    )

    subtitle_style = ParagraphStyle(
        "ExecutiveSubtitle",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#6B7280"),
        alignment=TA_CENTER,
        spaceAfter=7 * mm,
    )

    section_style = ParagraphStyle(
        "ExecutiveSection",
        parent=base_styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        textColor=colors.HexColor("#102A43"),
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )

    body_style = ParagraphStyle(
        "ExecutiveBody",
        parent=base_styles["BodyText"],
        fontName="Helvetica",
        fontSize=9.3,
        leading=13.5,
        textColor=colors.HexColor("#243B53"),
        spaceAfter=2.2 * mm,
    )

    bullet_style = ParagraphStyle(
        "ExecutiveBullet",
        parent=body_style,
        leftIndent=4.5 * mm,
        firstLineIndent=-3 * mm,
        spaceAfter=1.8 * mm,
    )

    small_style = ParagraphStyle(
        "ExecutiveSmall",
        parent=base_styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#52606D"),
    )

    callout_title_style = ParagraphStyle(
        "CalloutTitle",
        parent=base_styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#102A43"),
        spaceAfter=1 * mm,
    )

    callout_body_style = ParagraphStyle(
        "CalloutBody",
        parent=body_style,
        fontSize=8.8,
        leading=12,
    )

    def add_page_decor(canvas, current_doc):
        canvas.saveState()

        canvas.setFillColor(
            colors.HexColor("#102A43")
        )

        canvas.rect(
            0,
            page_height - 10 * mm,
            page_width,
            10 * mm,
            fill=1,
            stroke=0,
        )

        canvas.setStrokeColor(
            colors.HexColor("#D9E2EC")
        )

        canvas.line(
            18 * mm,
            12 * mm,
            page_width - 18 * mm,
            12 * mm,
        )

        canvas.setFillColor(
            colors.HexColor("#7B8794")
        )

        canvas.setFont(
            "Helvetica",
            7.5,
        )

        canvas.drawString(
            18 * mm,
            7.5 * mm,
            "Service Desk Analytics - Executive Brief",
        )

        canvas.drawRightString(
            page_width - 18 * mm,
            7.5 * mm,
            f"Page {current_doc.page}",
        )

        canvas.restoreState()

    story = [
        Spacer(1, 2 * mm),
        Paragraph(
            "Executive AI Brief",
            title_style,
        ),
    ]

    generated_at = (
        datetime.now()
        .strftime("%Y-%m-%d %H:%M")
    )

    story.append(
        Paragraph(
            (
                f"Management decision brief | Generated {generated_at} | "
                f"Source: {escape(source_name)}"
            ),
            subtitle_style,
        )
    )

    health_label = "MIXED"

    if (
        ytd_summary is not None
        and not ytd_summary.empty
    ):
        row_2024 = ytd_summary[
            ytd_summary["Year"] == 2024
        ]

        row_2025 = ytd_summary[
            ytd_summary["Year"] == 2025
        ]

        if (
            not row_2024.empty
            and not row_2025.empty
        ):
            old = row_2024.iloc[0]
            new = row_2025.iloc[0]

            score = 0

            if (
                new["SLA_Violation_Rate"]
                < old["SLA_Violation_Rate"]
            ):
                score += 1
            elif (
                new["SLA_Violation_Rate"]
                > old["SLA_Violation_Rate"]
            ):
                score -= 1

            if (
                new["Avg_First_Response_Hours"]
                < old["Avg_First_Response_Hours"]
            ):
                score += 1
            elif (
                new["Avg_First_Response_Hours"]
                > old["Avg_First_Response_Hours"]
            ):
                score -= 1

            if (
                new["Avg_Resolution_Hours"]
                < old["Avg_Resolution_Hours"]
            ):
                score += 1
            elif (
                new["Avg_Resolution_Hours"]
                > old["Avg_Resolution_Hours"]
            ):
                score -= 1

            if score > 0:
                health_label = "MIXED, TRENDING POSITIVE"
            elif score < 0:
                health_label = "MIXED, TRENDING NEGATIVE"

    health_table = Table(
        [
            [
                Paragraph(
                    "<b>OVERALL HEALTH</b>",
                    callout_title_style,
                ),
                Paragraph(
                    (
                        f"<b>{health_label}</b><br/>"
                        "Executive interpretation is based on SLA compliance, "
                        "first-response speed, and resolution-time signals."
                    ),
                    callout_body_style,
                ),
            ]
        ],
        colWidths=[
            42 * mm,
            122 * mm,
        ],
        hAlign="CENTER",
    )

    health_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    colors.HexColor("#DDEAFE"),
                ),
                (
                    "BACKGROUND",
                    (1, 0),
                    (1, 0),
                    colors.HexColor("#F5F8FC"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    colors.HexColor("#B8C7D9"),
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.extend(
        [
            health_table,
            Spacer(1, 5 * mm),
        ]
    )

    avg_response = (
        overall_metrics["Avg_First_Response_Hours"]
    )

    avg_resolution = (
        overall_metrics["Avg_Resolution_Hours"]
    )

    kpi_table = Table(
        [
            [
                "Total Tickets",
                "SLA Compliance",
                "SLA Violations",
                "Avg First Response",
                "Avg Resolution",
            ],
            [
                f"{overall_metrics['Total_Tickets']:,}",
                f"{overall_metrics['SLA_Compliance_Rate']:.1f}%",
                f"{overall_metrics['SLA_Violations']:,}",
                (
                    f"{avg_response:.2f} hrs"
                    if pd.notna(avg_response)
                    else "N/A"
                ),
                (
                    f"{avg_resolution:.2f} hrs"
                    if pd.notna(avg_resolution)
                    else "N/A"
                ),
            ],
        ],
        colWidths=[33 * mm] * 5,
        hAlign="CENTER",
    )

    kpi_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#EAF1F8"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.HexColor("#334E68"),
                ),
                (
                    "TEXTCOLOR",
                    (0, 1),
                    (-1, 1),
                    colors.HexColor("#102A43"),
                ),
                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold",
                ),
                (
                    "FONTNAME",
                    (0, 1),
                    (-1, 1),
                    "Helvetica-Bold",
                ),
                (
                    "FONTSIZE",
                    (0, 0),
                    (-1, 0),
                    7.5,
                ),
                (
                    "FONTSIZE",
                    (0, 1),
                    (-1, 1),
                    11,
                ),
                (
                    "ALIGN",
                    (0, 0),
                    (-1, -1),
                    "CENTER",
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.35,
                    colors.HexColor("#CBD5E1"),
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
            ]
        )
    )

    story.extend(
        [
            kpi_table,
            Spacer(1, 6 * mm),
        ]
    )

    if (
        ytd_summary is not None
        and not ytd_summary.empty
    ):
        story.append(
            Paragraph(
                "YTD Performance Snapshot",
                section_style,
            )
        )

        ytd_rows = [
            [
                "Year",
                "Tickets",
                "SLA Violations",
                "Violation Rate",
                "Compliance",
                "Avg Response",
                "Avg Resolution",
            ]
        ]

        for _, row in ytd_summary.iterrows():
            ytd_rows.append(
                [
                    str(int(row["Year"])),
                    f"{int(row['Total_Tickets']):,}",
                    f"{int(row['SLA_Violations']):,}",
                    f"{row['SLA_Violation_Rate']:.2f}%",
                    f"{row['SLA_Compliance_Rate']:.2f}%",
                    f"{row['Avg_First_Response_Hours']:.2f}h",
                    f"{row['Avg_Resolution_Hours']:.2f}h",
                ]
            )

        ytd_table = Table(
            ytd_rows,
            colWidths=[
                16 * mm,
                20 * mm,
                25 * mm,
                27 * mm,
                24 * mm,
                26 * mm,
                27 * mm,
            ],
            repeatRows=1,
        )

        ytd_commands = [
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor("#102A43"),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                7.5,
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),
            (
                "GRID",
                (0, 0),
                (-1, -1),
                0.35,
                colors.HexColor("#CBD5E1"),
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                5,
            ),
        ]

        if len(ytd_rows) >= 3:
            ytd_commands.append(
                (
                    "BACKGROUND",
                    (0, 2),
                    (-1, 2),
                    colors.HexColor("#F2F8F5"),
                )
            )

        ytd_table.setStyle(
            TableStyle(ytd_commands)
        )

        story.extend(
            [
                ytd_table,
                Spacer(1, 5 * mm),
            ]
        )

    sections = {}
    current_heading = None
    current_lines = []

    for raw_line in executive_text.splitlines():
        line = raw_line.strip()

        if line.startswith("## "):
            if current_heading is not None:
                sections[current_heading] = current_lines

            current_heading = line[3:].strip()
            current_lines = []

        elif current_heading is not None and line:
            current_lines.append(line)

    if current_heading is not None:
        sections[current_heading] = current_lines

    overall_lines = sections.get(
        "Overall Service Health",
        [],
    )

    improved_lines = sections.get(
        "What Improved",
        [],
    )

    attention_lines = sections.get(
        "What Needs Attention",
        [],
    )

    priority_lines = sections.get(
        "Top Management Priorities",
        [],
    )

    caveat_lines = sections.get(
        "Key Caveat",
        [],
    )

    story.append(
        Paragraph(
            "Overall Service Health",
            section_style,
        )
    )

    for line in overall_lines:
        story.append(
            Paragraph(
                markdown_inline_to_reportlab(line),
                body_style,
            )
        )

    improved_flowables = [
        Paragraph(
            "What Improved",
            section_style,
        )
    ]

    for line in improved_lines:
        clean_line = re.sub(
            r"^[\-\*•]\s*",
            "",
            line,
        )

        improved_flowables.append(
            Paragraph(
                "• "
                + markdown_inline_to_reportlab(clean_line),
                bullet_style,
            )
        )

    attention_flowables = [
        Paragraph(
            "What Needs Attention",
            section_style,
        )
    ]

    for line in attention_lines:
        clean_line = re.sub(
            r"^[\-\*•]\s*",
            "",
            line,
        )

        attention_flowables.append(
            Paragraph(
                "• "
                + markdown_inline_to_reportlab(clean_line),
                bullet_style,
            )
        )

    comparison_table = Table(
        [
            [
                improved_flowables,
                attention_flowables,
            ]
        ],
        colWidths=[
            82 * mm,
            82 * mm,
        ],
    )

    comparison_table.setStyle(
        TableStyle(
            [
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP",
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    6,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    4,
                ),
                (
                    "BOX",
                    (0, 0),
                    (0, 0),
                    0.5,
                    colors.HexColor("#CDE8D8"),
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, 0),
                    colors.HexColor("#F5FBF7"),
                ),
                (
                    "BOX",
                    (1, 0),
                    (1, 0),
                    0.5,
                    colors.HexColor("#F0D9A8"),
                ),
                (
                    "BACKGROUND",
                    (1, 0),
                    (1, 0),
                    colors.HexColor("#FFF9EA"),
                ),
            ]
        )
    )

    story.extend(
        [
            Spacer(1, 3 * mm),
            comparison_table,
            PageBreak(),
            Paragraph(
                "Top Management Priorities",
                section_style,
            ),
        ]
    )

    for index, line in enumerate(
        priority_lines,
        start=1,
    ):
        numbered_match = re.match(
            r"^\d+\.\s*(.*)$",
            line,
        )

        clean_line = (
            numbered_match.group(1).strip()
            if numbered_match
            else line.strip()
        )

        number_style = ParagraphStyle(
            f"PriorityNumber{index}",
            parent=body_style,
            fontSize=15,
            textColor=colors.white,
            alignment=TA_CENTER,
        )

        priority_card = Table(
            [
                [
                    Paragraph(
                        f"<b>{index}</b>",
                        number_style,
                    ),
                    Paragraph(
                        markdown_inline_to_reportlab(
                            clean_line
                        ),
                        body_style,
                    ),
                ]
            ],
            colWidths=[
                12 * mm,
                151 * mm,
            ],
        )

        priority_card.setStyle(
            TableStyle(
                [
                    (
                        "BACKGROUND",
                        (0, 0),
                        (0, 0),
                        colors.HexColor("#102A43"),
                    ),
                    (
                        "BACKGROUND",
                        (1, 0),
                        (1, 0),
                        colors.HexColor("#F7F9FC"),
                    ),
                    (
                        "BOX",
                        (0, 0),
                        (-1, -1),
                        0.5,
                        colors.HexColor("#D2DCE8"),
                    ),
                    (
                        "VALIGN",
                        (0, 0),
                        (-1, -1),
                        "MIDDLE",
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "TOPPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        8,
                    ),
                ]
            )
        )

        story.extend(
            [
                priority_card,
                Spacer(1, 3 * mm),
            ]
        )

    story.append(
        Paragraph(
            "Key Caveat",
            section_style,
        )
    )

    caveat_text = (
        " ".join(caveat_lines)
        if caveat_lines
        else (
            "The available aggregated data does not "
            "by itself establish root causes."
        )
    )

    caveat_table = Table(
        [
            [
                Paragraph(
                    markdown_inline_to_reportlab(
                        caveat_text
                    ),
                    body_style,
                )
            ]
        ],
        colWidths=[163 * mm],
    )

    caveat_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#FFF7ED"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.6,
                    colors.HexColor("#F4C48A"),
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    9,
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    8,
                ),
            ]
        )
    )

    story.extend(
        [
            caveat_table,
            Spacer(1, 7 * mm),
            Paragraph(
                (
                    "Prepared by Service Desk Analytics | "
                    "Aggregated operational metrics only | "
                    "Executive decision-support output"
                ),
                small_style,
            ),
        ]
    )

    doc.build(
        story,
        onFirstPage=add_page_decor,
        onLaterPages=add_page_decor,
    )

    buffer.seek(0)

    return buffer.getvalue()


# =========================================================
# FILE UPLOAD
# =========================================================

if "uploaded_dataset" not in st.session_state:
    st.session_state["uploaded_dataset"] = None


if st.session_state["uploaded_dataset"] is None:

    st.markdown(
        """
        <div class="landing-shell">
            <div class="landing-card">
                <div class="landing-eyebrow">IT Service Desk Reporting</div>
                <div class="landing-title">Service Desk Analytics</div>
                <div class="landing-copy">
                    Upload a CSV or Excel file to open the dashboard.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    landing_upload = st.file_uploader(
        "Upload your dataset",
        type=[
            "csv",
            "xlsx",
        ],
        label_visibility="collapsed",
        key="landing_file_uploader",
    )

    st.markdown(
        """
        <div class="landing-features">
            <span>SLA Monitoring</span>
            <span class="landing-dot">•</span>
            <span>Operational Insights</span>
            <span class="landing-dot">•</span>
            <span>YTD Comparison</span>
            <span class="landing-dot">•</span>
            <span>Management Reporting</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if landing_upload is None:
        st.stop()

    st.session_state["uploaded_dataset"] = landing_upload
    st.rerun()


uploaded_file = st.session_state["uploaded_dataset"]


with st.sidebar:
    if st.button(
        "Change dataset",
        use_container_width=True,
        key="change_dataset_button",
    ):
        st.session_state["uploaded_dataset"] = None
        st.session_state.pop(
            "executive_dataset_signature",
            None,
        )
        st.session_state.pop(
            "executive_brief_text",
            None,
        )
        st.session_state.pop(
            "executive_pdf_bytes",
            None,
        )
        st.rerun()


# =========================================================
# READ AND CLEAN DATA
# =========================================================

try:
    if (
        uploaded_file.name
        .lower()
        .endswith(".csv")
    ):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

except Exception as error:
    st.error(
        "The uploaded file could not be read."
    )

    st.exception(error)
    st.stop()


df = clean_column_names(df)


required_columns = [
    "Ticket_ID",
    "Created_Time",
    "Resolution_Status",
    "First_Response_Time_Hours",
    "Resolution_Time_Hours",
]


missing_columns = [
    column
    for column in required_columns
    if column not in df.columns
]


if missing_columns:
    st.error(
        "Dataset format not supported. "
        "This file does not contain the fields required for Service Desk analysis. "
        "Please upload a compatible Service Desk dataset."
    )
    st.stop()


for column in [
    "Created_Time",
    "Closed_Time",
    "Resolved_Time",
    "Last_Updated_Time",
    "Due_By_Time",
]:
    if column in df.columns:
        df[column] = convert_date_column(
            df[column]
        )


df["First_Response_Time_Hours"] = (
    pd.to_numeric(
        df["First_Response_Time_Hours"],
        errors="coerce",
    )
)


df["Resolution_Hours"] = (
    df["Resolution_Time_Hours"]
    .apply(duration_to_hours)
)


df.loc[
    df["First_Response_Time_Hours"] < 0,
    "First_Response_Time_Hours",
] = np.nan


df.loc[
    df["Resolution_Hours"] < 0,
    "Resolution_Hours",
] = np.nan


df["SLA_Violation_Flag"] = (
    calculate_resolution_sla_flag(df)
)


df["Year"] = (
    df["Created_Time"]
    .dt.year
)


df["Created_Month"] = (
    df["Created_Time"]
    .dt.to_period("M")
    .astype(str)
)


overall_metrics = (
    calculate_overall_metrics(df)
)


region_summary = (
    calculate_region_performance(df)
)


agent_summary = (
    calculate_agent_performance(df)
)


ytd_summary, latest_2025_date = (
    calculate_ytd_comparison(df)
)


# =========================================================
# DERIVED DISPLAY DATA
# =========================================================

latest_created = (
    df["Created_Time"]
    .dropna()
    .max()
)
common_priority = "N/A"

if "Priority" in df.columns:
    priority_counts = (
        df["Priority"]
        .fillna("Unknown")
        .value_counts()
    )

    if not priority_counts.empty:
        common_priority = (
            priority_counts.index[0]
        )


if not region_summary.empty:
    highest_violation_region = (
        region_summary.iloc[0]
    )

    highest_volume_region = (
        region_summary
        .sort_values(
            "Total_Tickets",
            ascending=False,
        )
        .iloc[0]
    )

else:
    highest_violation_region = None
    highest_volume_region = None


eligible_agents = (
    agent_summary[
        agent_summary["Tickets_Handled"] >= 50
    ]
    .copy()
    if not agent_summary.empty
    else pd.DataFrame()
)


# =========================================================
# SIDEBAR
# =========================================================

st.sidebar.markdown(
    """
    <div class="sidebar-title">
        SERVICE DESK<br>ANALYTICS
    </div>
    <div class="sidebar-rule"></div>

    <a class="nav-link" href="#overview">Overview</a>
    <a class="nav-link" href="#dashboard">Dashboard</a>
    <a class="nav-link" href="#operational-insights">Operational Insights</a>
    <a class="nav-link" href="#ytd-comparison">Year-to-Date Comparison</a>
    <a class="nav-link" href="#executive-brief">Executive Brief</a>
    <a class="nav-link" href="#ask-your-data">Ask Your Data</a>

    <div style="height:2rem"></div>
    """,
    unsafe_allow_html=True,
)


st.sidebar.markdown(
    f"""
    <div class="sidebar-rule"></div>
    <div class="sidebar-subtle" style="font-weight:700;margin-bottom:.3rem;">DATASET</div>
    <div class="dataset-box">
        <div style="font-size:.82rem;font-weight:650;word-break:break-word;">
            {uploaded_file.name}
        </div>
        <div class="sidebar-subtle" style="margin-top:.35rem;">
            {len(df):,} rows
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# OVERVIEW
# =========================================================

st.markdown(
    '<div id="overview" class="section-anchor"></div>',
    unsafe_allow_html=True,
)


st.markdown(
    '<div class="page-title">Overview</div>',
    unsafe_allow_html=True,
)

st.markdown(
    (
        '<div class="page-subtitle">'
        'Comprehensive view of IT Service Desk performance.'
        '</div>'
    ),
    unsafe_allow_html=True,
)


st.write("")


k1, k2, k3, k4, k5 = st.columns(5)


with k1:
    st.markdown(
        metric_card(
            "Total Tickets",
            f"{overall_metrics['Total_Tickets']:,}",
        ),
        unsafe_allow_html=True,
    )


with k2:
    st.markdown(
        metric_card(
            "SLA Compliance",
            f"{overall_metrics['SLA_Compliance_Rate']:.1f}%",
            tone="kpi-green",
        ),
        unsafe_allow_html=True,
    )


with k3:
    st.markdown(
        metric_card(
            "SLA Violations",
            f"{overall_metrics['SLA_Violations']:,}",
            tone="kpi-red",
        ),
        unsafe_allow_html=True,
    )


with k4:
    st.markdown(
        metric_card(
            "Avg First Response",
            (
                f"{overall_metrics['Avg_First_Response_Hours']:.2f} hrs"
                if pd.notna(
                    overall_metrics[
                        "Avg_First_Response_Hours"
                    ]
                )
                else "N/A"
            ),
            tone="kpi-blue",
        ),
        unsafe_allow_html=True,
    )


with k5:
    st.markdown(
        metric_card(
            "Avg Resolution Time",
            (
                f"{overall_metrics['Avg_Resolution_Hours']:.2f} hrs"
                if pd.notna(
                    overall_metrics[
                        "Avg_Resolution_Hours"
                    ]
                )
                else "N/A"
            ),
            tone="kpi-blue",
        ),
        unsafe_allow_html=True,
    )


# =========================================================
# AUTOMATIC INSIGHTS
# =========================================================

if (
    highest_violation_region is not None
    and highest_volume_region is not None
):
    st.markdown(
        f"""
        <div class="panel">
            <div class="panel-title">Automatic Insights</div>
            <div class="insight-grid">
                <div class="insight-item">
                    <div class="insight-label">Highest SLA violation rate</div>
                    <div class="insight-value">
                        {highest_violation_region['Region']}
                        ({highest_violation_region['SLA_Violation_Rate']:.2f}%)
                    </div>
                </div>
                <div class="insight-item">
                    <div class="insight-label">Highest ticket volume</div>
                    <div class="insight-value">
                        {highest_volume_region['Region']}
                        ({int(highest_volume_region['Total_Tickets']):,})
                    </div>
                </div>
                <div class="insight-item">
                    <div class="insight-label">Most common priority</div>
                    <div class="insight-value">{common_priority}</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# DASHBOARD
# =========================================================

st.markdown(
    '<div id="dashboard" class="section-anchor"></div>',
    unsafe_allow_html=True,
)


monthly_tickets = (
    df.dropna(
        subset=["Created_Time"]
    )
    .groupby("Created_Month")
    .size()
    .reset_index(name="Tickets")
    .sort_values("Created_Month")
)


line_chart = (
    alt.Chart(monthly_tickets)
    .mark_line(
        point=True,
        strokeWidth=2.4,
        color="#0f4c97",
    )
    .encode(
        x=alt.X(
            "Created_Month:N",
            title=None,
            sort=None,
            axis=alt.Axis(
                labelAngle=0,
                labelColor="#637083",
                labelFontSize=10,
                tickColor="#d9e2ec",
                domainColor="#d9e2ec",
            ),
        ),
        y=alt.Y(
            "Tickets:Q",
            title=None,
            axis=alt.Axis(
                grid=True,
                gridColor="#e8eef5",
                labelColor="#637083",
                labelFontSize=10,
                domain=False,
            ),
        ),
        tooltip=[
            alt.Tooltip(
                "Created_Month:N",
                title="Month",
            ),
            alt.Tooltip(
                "Tickets:Q",
                title="Tickets",
                format=",",
            ),
        ],
    )
    .properties(
        height=230,
        title=alt.TitleParams(
            text="Tickets Trend by Month",
            anchor="start",
            color="#10233f",
            fontSize=14,
            fontWeight=700,
        ),
    )
)


compliant = int(
    overall_metrics["Total_Tickets"]
    - overall_metrics["SLA_Violations"]
)


sla_chart_df = pd.DataFrame(
    {
        "Status": [
            "Compliant",
            "Violation",
        ],
        "Tickets": [
            compliant,
            overall_metrics["SLA_Violations"],
        ],
    }
)


donut_chart = (
    alt.Chart(sla_chart_df)
    .mark_arc(
        innerRadius=58,
        outerRadius=88,
    )
    .encode(
        theta=alt.Theta(
            "Tickets:Q",
            stack=True,
        ),
        color=alt.Color(
            "Status:N",
            scale=alt.Scale(
                domain=[
                    "Compliant",
                    "Violation",
                ],
                range=[
                    "#2f9e5b",
                    "#d94b45",
                ],
            ),
            legend=alt.Legend(
                orient="right",
                title=None,
                labelColor="#43516a",
            ),
        ),
        tooltip=[
            "Status:N",
            alt.Tooltip(
                "Tickets:Q",
                format=",",
            ),
        ],
    )
    .properties(
        height=230,
        title=alt.TitleParams(
            text="Resolution SLA Status",
            anchor="start",
            color="#10233f",
            fontSize=14,
            fontWeight=700,
        ),
    )
)


priority_chart = None

if "Priority" in df.columns:
    priority_df = (
        df["Priority"]
        .fillna("Unknown")
        .value_counts()
        .rename_axis("Priority")
        .reset_index(name="Tickets")
    )

    priority_chart = (
        alt.Chart(priority_df)
        .mark_bar(
            color="#0f4c97",
            cornerRadiusEnd=3,
        )
        .encode(
            y=alt.Y(
                "Priority:N",
                sort="-x",
                title=None,
                axis=alt.Axis(
                    labelColor="#43516a",
                    labelFontSize=10,
                    domain=False,
                    ticks=False,
                ),
            ),
            x=alt.X(
                "Tickets:Q",
                title=None,
                axis=None,
            ),
            tooltip=[
                "Priority:N",
                alt.Tooltip(
                    "Tickets:Q",
                    format=",",
                ),
            ],
        )
        .properties(
            height=230,
            title=alt.TitleParams(
                text="Tickets by Priority",
                anchor="start",
                color="#10233f",
                fontSize=14,
                fontWeight=700,
            ),
        )
    )


c1, c2, c3 = st.columns(3)


with c1:
    st.altair_chart(
        line_chart,
        use_container_width=True,
    )


with c2:
    st.altair_chart(
        donut_chart,
        use_container_width=True,
    )


with c3:
    if priority_chart is not None:
        st.altair_chart(
            priority_chart,
            use_container_width=True,
        )


# =========================================================
# OPERATIONAL INSIGHTS
# =========================================================

st.markdown(
    '<div id="operational-insights" class="section-anchor"></div>',
    unsafe_allow_html=True,
)


st.markdown(
    '<div class="section-heading">Operational Insights</div>',
    unsafe_allow_html=True,
)


left, right = st.columns(2)


with left:
    st.markdown(
        '<div class="panel-title">SLA Violation Rate by Region</div>',
        unsafe_allow_html=True,
    )

    region_display = (
        region_summary[
            [
                "Region",
                "Total_Tickets",
                "SLA_Violations",
                "SLA_Violation_Rate",
            ]
        ]
        .copy()
    )

    region_display.columns = [
        "Region",
        "Total Tickets",
        "SLA Violations",
        "Violation Rate %",
    ]

    st.dataframe(
        region_display,
        use_container_width=True,
        hide_index=True,
        height=250,
    )


with right:
    st.markdown(
        '<div class="panel-title">Agent Performance (minimum 50 tickets)</div>',
        unsafe_allow_html=True,
    )

    if not eligible_agents.empty:
        agent_display = (
            eligible_agents[
                [
                    "Agent_ID",
                    "Tickets_Handled",
                    "SLA_Violations",
                    "SLA_Violation_Rate",
                    "Avg_First_Response_Hours",
                ]
            ]
            .sort_values(
                [
                    "SLA_Violation_Rate",
                    "Tickets_Handled",
                ],
                ascending=[
                    True,
                    False,
                ],
            )
            .copy()
        )

        agent_display.columns = [
            "Agent ID",
            "Tickets Handled",
            "SLA Violations",
            "Violation Rate %",
            "Avg First Response",
        ]

        st.dataframe(
            agent_display,
            use_container_width=True,
            hide_index=True,
            height=250,
        )

    else:
        st.info(
            "No agents meet the minimum 50-ticket threshold."
        )


# =========================================================
# YTD COMPARISON
# =========================================================

st.markdown(
    '<div id="ytd-comparison" class="section-anchor"></div>',
    unsafe_allow_html=True,
)


st.markdown(
    '<div class="section-heading">Year-to-Date Comparison</div>',
    unsafe_allow_html=True,
)


if (
    ytd_summary is not None
    and latest_2025_date is not None
):
    st.markdown(
        (
            '<div class="section-copy">'
            f'Fair window: January 1 through '
            f'{latest_2025_date.strftime("%B %d")} '
            'in both 2024 and 2025.'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    row_2024 = (
        ytd_summary[
            ytd_summary["Year"] == 2024
        ]
    )

    row_2025 = (
        ytd_summary[
            ytd_summary["Year"] == 2025
        ]
    )

    if (
        not row_2024.empty
        and not row_2025.empty
    ):
        y2024 = row_2024.iloc[0]
        y2025 = row_2025.iloc[0]

        ticket_change = (
            (
                y2025["Total_Tickets"]
                - y2024["Total_Tickets"]
            )
            / y2024["Total_Tickets"]
            * 100
            if y2024["Total_Tickets"]
            else 0
        )

        sla_change = (
            y2025["SLA_Violation_Rate"]
            - y2024["SLA_Violation_Rate"]
        )

        response_change = (
            y2025["Avg_First_Response_Hours"]
            - y2024["Avg_First_Response_Hours"]
        )

        resolution_change = (
            y2025["Avg_Resolution_Hours"]
            - y2024["Avg_Resolution_Hours"]
        )

        yc1, yc2 = st.columns(
            [1, 2.45]
        )

        with yc1:
            st.markdown(
                change_card(
                    "Ticket Volume",
                    f"{ticket_change:+.1f}%",
                    (
                        f"{int(y2024['Total_Tickets']):,}"
                        f" → "
                        f"{int(y2025['Total_Tickets']):,}"
                    ),
                    "neutral",
                ),
                unsafe_allow_html=True,
            )

            st.markdown(
                change_card(
                    "SLA Violation Rate",
                    f"{sla_change:+.2f} pp",
                    (
                        f"{y2024['SLA_Violation_Rate']:.2f}%"
                        f" → "
                        f"{y2025['SLA_Violation_Rate']:.2f}%"
                    ),
                    (
                        "positive"
                        if sla_change < 0
                        else "negative"
                    ),
                ),
                unsafe_allow_html=True,
            )

            st.markdown(
                change_card(
                    "Avg First Response",
                    f"{response_change:+.2f} hrs",
                    (
                        f"{y2024['Avg_First_Response_Hours']:.2f}"
                        f" → "
                        f"{y2025['Avg_First_Response_Hours']:.2f} hrs"
                    ),
                    (
                        "positive"
                        if response_change < 0
                        else "negative"
                    ),
                ),
                unsafe_allow_html=True,
            )

            st.markdown(
                change_card(
                    "Avg Resolution Time",
                    f"{resolution_change:+.2f} hrs",
                    (
                        f"{y2024['Avg_Resolution_Hours']:.2f}"
                        f" → "
                        f"{y2025['Avg_Resolution_Hours']:.2f} hrs"
                    ),
                    (
                        "positive"
                        if resolution_change < 0
                        else "negative"
                    ),
                ),
                unsafe_allow_html=True,
            )

        with yc2:
            st.markdown(
                '<div class="panel-title">YTD Performance Summary</div>',
                unsafe_allow_html=True,
            )

            ytd_display = (
                ytd_summary[
                    [
                        "Year",
                        "Total_Tickets",
                        "SLA_Violations",
                        "SLA_Violation_Rate",
                        "SLA_Compliance_Rate",
                        "Avg_First_Response_Hours",
                        "Avg_Resolution_Hours",
                    ]
                ]
                .copy()
            )

            ytd_display.columns = [
                "Year",
                "Total Tickets",
                "SLA Violations",
                "Violation Rate %",
                "Compliance %",
                "Avg First Response",
                "Avg Resolution",
            ]

            st.dataframe(
                ytd_display,
                use_container_width=True,
                hide_index=True,
                height=140,
            )

            score = 0

            if sla_change < 0:
                score += 1
            elif sla_change > 0:
                score -= 1

            if response_change < 0:
                score += 1
            elif response_change > 0:
                score -= 1

            if resolution_change < 0:
                score += 1
            elif resolution_change > 0:
                score -= 1

            if score > 0:
                assessment_text = (
                    "Service desk performance improved in 2025 "
                    "across the majority of measured indicators."
                )

            elif score < 0:
                assessment_text = (
                    "Service desk performance declined in 2025 "
                    "across the majority of measured indicators."
                )

            else:
                assessment_text = (
                    "Service desk performance is mixed across "
                    "the measured indicators."
                )

            st.markdown(
                (
                    '<div class="assessment">'
                    '<b>Assessment</b><br>'
                    f'{assessment_text}'
                    '</div>'
                ),
                unsafe_allow_html=True,
            )

else:
    st.info(
        "A fair 2024 vs 2025 YTD comparison could not be calculated."
    )


# =========================================================
# EXECUTIVE BRIEF
# =========================================================

st.markdown(
    '<div id="executive-brief" class="section-anchor"></div>',
    unsafe_allow_html=True,
)


st.markdown(
    '<div class="section-heading">Executive Brief</div>',
    unsafe_allow_html=True,
)


st.markdown(
    (
        '<div class="section-copy">'
        'Generate a management-level summary from aggregated metrics, '
        'then export it as a PDF. Individual ticket records are not sent.'
        '</div>'
    ),
    unsafe_allow_html=True,
)


executive_api_key = os.getenv(
    "GEMINI_API_KEY"
)


dataset_signature = (
    uploaded_file.name,
    int(len(df)),
    str(latest_created),
    int(
        overall_metrics["SLA_Violations"]
    ),
)


if (
    st.session_state.get(
        "executive_dataset_signature"
    )
    != dataset_signature
):
    st.session_state[
        "executive_dataset_signature"
    ] = dataset_signature

    st.session_state.pop(
        "executive_brief_text",
        None,
    )

    st.session_state.pop(
        "executive_pdf_bytes",
        None,
    )


if not executive_api_key:
    st.warning(
        "GEMINI_API_KEY was not found in the .env file."
    )

else:
    generate_executive_brief = st.button(
        "Generate Executive Brief",
        key="generate_executive_brief",
    )

    if generate_executive_brief:
        executive_context = (
            create_ai_context(
                overall_metrics=
                    overall_metrics,
                region_summary=
                    region_summary,
                agent_summary=
                    agent_summary,
                ytd_summary=
                    ytd_summary,
                common_priority=
                    common_priority,
            )
        )

        executive_prompt = f"""
You are a senior IT Service Management analyst preparing
an executive briefing for technology leadership.

Analyze ONLY the aggregated statistics supplied below.

IMPORTANT RULES:
1. Do not invent facts or root causes.
2. Resolution SLA is the primary SLA metric.
3. Use the FAIR YTD comparison when discussing 2024 vs 2025.
4. Clearly separate evidence from interpretation.
5. Do not claim causation unless supported by the data.
6. Be careful with small sample sizes.
7. Do not make unsupported judgments about employees.
8. Quantify important findings.
9. Identify both improvements and concerns.
10. Provide exactly three management priorities.
11. Keep the brief concise and suitable for senior leadership.

AGGREGATED DATA:

{executive_context}


Return the brief using EXACTLY these sections:

## Overall Service Health

## What Improved

## What Needs Attention

## Top Management Priorities

## Key Caveat
"""

        try:
            executive_client = genai.Client(
                api_key=executive_api_key
            )

            with st.spinner(
                "Preparing the Executive Brief..."
            ):
                executive_interaction = (
                    executive_client
                    .interactions
                    .create(
                        model=GEMINI_MODEL,
                        input=executive_prompt,
                    )
                )

                executive_text = (
                    executive_interaction.output_text
                )

            if executive_text:
                st.session_state[
                    "executive_brief_text"
                ] = executive_text

                st.session_state[
                    "executive_pdf_bytes"
                ] = build_executive_pdf(
                    executive_text=
                        executive_text,
                    overall_metrics=
                        overall_metrics,
                    ytd_summary=
                        ytd_summary,
                    source_name=
                        uploaded_file.name,
                )

            else:
                st.warning(
                    "Gemini returned an empty Executive Brief."
                )

        except Exception as error:
            st.error(
                "Executive Brief could not be generated."
            )
            st.exception(error)


if st.session_state.get(
    "executive_brief_text"
):
    st.markdown(
        st.session_state[
            "executive_brief_text"
        ]
    )

    if st.session_state.get(
        "executive_pdf_bytes"
    ):
        st.download_button(
            label="Download Executive Brief (PDF)",
            data=st.session_state[
                "executive_pdf_bytes"
            ],
            file_name=(
                "Executive_AI_Brief_"
                + datetime.now().strftime(
                    "%Y%m%d"
                )
                + ".pdf"
            ),
            mime="application/pdf",
            key="download_executive_pdf",
        )


# =========================================================
# ASK YOUR DATA
# =========================================================

st.markdown(
    '<div id="ask-your-data" class="section-anchor"></div>',
    unsafe_allow_html=True,
)


st.markdown(
    '<div class="section-heading">Ask Your Data</div>',
    unsafe_allow_html=True,
)


st.markdown(
    (
        '<div class="section-copy">'
        'Ask an operational or management question about the uploaded '
        'service desk dataset. Only aggregated statistics are sent.'
        '</div>'
    ),
    unsafe_allow_html=True,
)


user_question = st.text_area(
    "Your question",
    placeholder=(
        "Example: Compare 2024 and 2025 YTD. "
        "Did performance improve, and what evidence supports it?"
    ),
    height=90,
    label_visibility="collapsed",
)


if st.button(
    "Analyze",
    key="analyze_with_ai",
):
    if not user_question.strip():
        st.warning(
            "Enter a question first."
        )

    else:
        api_key = os.getenv(
            "GEMINI_API_KEY"
        )

        if not api_key:
            st.error(
                "GEMINI_API_KEY was not found in the .env file."
            )

        else:
            ai_context = create_ai_context(
                overall_metrics=
                    overall_metrics,
                region_summary=
                    region_summary,
                agent_summary=
                    agent_summary,
                ytd_summary=
                    ytd_summary,
                common_priority=
                    common_priority,
            )

            prompt = f"""
You are a senior IT Service Management data analyst.

Use ONLY the aggregated statistics below.

Rules:
- Do not invent facts or root causes.
- Use the FAIR YTD comparison for 2024 vs 2025.
- Resolution SLA is the primary SLA metric.
- Distinguish evidence from interpretation.
- Be careful with small samples.
- Give evidence-based recommendations.
- State important limitations.

AGGREGATED DATA:

{ai_context}

USER QUESTION:

{user_question}

Respond using:
## Direct Answer
## Evidence From the Data
## Business Interpretation
## Recommended Actions
## Limitations
"""

            try:
                client = genai.Client(
                    api_key=api_key
                )

                with st.spinner(
                    "Analyzing..."
                ):
                    interaction = (
                        client
                        .interactions
                        .create(
                            model=GEMINI_MODEL,
                            input=prompt,
                        )
                    )

                    ai_text = (
                        interaction.output_text
                    )

                if ai_text:
                    st.markdown(ai_text)
                else:
                    st.warning(
                        "Gemini returned an empty response."
                    )

            except Exception as error:
                st.error(
                    "Analysis failed."
                )
                st.exception(error)


# =========================================================
# OPTIONAL RAW DATA
# =========================================================

with st.expander(
    "Data preview"
):
    st.dataframe(
        df.head(10),
        use_container_width=True,
        hide_index=True,
    )


# =========================================================
# FOOTER
# =========================================================

st.markdown(
    """
    <div class="footer">
        Service Desk Analytics &nbsp;&nbsp;|&nbsp;&nbsp; Performance Reporting
    </div>
    """,
    unsafe_allow_html=True,
)
