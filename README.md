# Service Desk Analytics

A Streamlit dashboard for analyzing IT Service Desk data from CSV and Excel files.

The project focuses on SLA performance, ticket trends, regional performance, agent activity, and year-to-date comparisons. It also includes Gemini-powered features for asking questions about the data and generating an executive summary.

## What it includes

- SLA compliance and violation tracking
- Monthly ticket trends
- Ticket analysis by priority and region
- Agent performance metrics
- 2024 vs 2025 YTD comparison
- Automatic performance insights
- Ask Your Data using Gemini
- Executive brief with PDF export

## Built with

Python, Streamlit, Pandas, Altair, Google Gemini API, ReportLab, and OpenPyXL.

## Data privacy

The AI features use aggregated service desk metrics. Individual ticket records are not sent to Gemini.
## Run locally

Install the dependencies:

```bash
pip install -r requirements.txt
```

Run the application:

```bash
streamlit run app.py
```

## Live app

[Open the Service Desk Analytics dashboard](https://service-desk-analytics-3gmzrqgog5rxnnmu6fvzru.streamlit.app/)