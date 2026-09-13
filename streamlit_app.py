
import io
import math
import re
from datetime import datetime

import pandas as pd
import streamlit as st

try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_OK = True
except Exception:
    PLOTLY_OK = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    )
    REPORTLAB_OK = True
except Exception:
    REPORTLAB_OK = False

st.set_page_config(
    page_title="TB → Audit Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
.block-container {padding-top: 1.2rem; padding-bottom: 2rem;}
.hero {padding: 22px 24px; border: 1px solid #e4e7ec; border-radius: 18px;
       background: linear-gradient(135deg,#f8fafc,#ffffff); margin-bottom: 18px;}
.hero h1 {margin:0; font-size:34px;}
.hero p {margin:6px 0 0; color:#667085;}
.badge {display:inline-block; padding:4px 9px; border-radius:999px;
        font-size:12px; font-weight:700; margin-right:5px;}
.high {background:#fee4e2; color:#b42318;}
.medium {background:#fef0c7; color:#b54708;}
.low {background:#dcfae6; color:#027a48;}
.note {padding:12px 14px; border-left:4px solid #98a2b3; background:#f9fafb; border-radius:8px;}
.welcome-shell {min-height:72vh; display:flex; align-items:center; justify-content:center;
                                background:radial-gradient(circle at 50% 35%,#183b56 0,#09111d 45%,#05070b 100%);
                                border-radius:24px; padding:42px 24px; overflow:hidden; position:relative;}
.welcome-shell:before {content:""; position:absolute; inset:12%; border:1px solid rgba(94,234,212,.18);
                                             border-radius:50%; transform:rotateX(68deg) rotateZ(18deg); animation:orbit 9s linear infinite;}
.welcome-content {position:relative; z-index:2; width:min(100%,520px); text-align:center; color:#f8fafc;}
.welcome-content h1 {font-size:clamp(28px,5vw,48px); margin:18px 0 6px; letter-spacing:0;}
.welcome-content p {color:#b6c6d8; margin:0 0 24px;}
.welcome-mark {height:150px; width:150px; margin:0 auto; perspective:700px;}
.cube {height:86px; width:86px; position:relative; top:32px; left:32px; transform-style:preserve-3d;
             transform:rotateX(-24deg) rotateY(35deg); animation:floatcube 5s ease-in-out infinite;}
.face {position:absolute; height:86px; width:86px; border:1px solid rgba(255,255,255,.55);}
.face.front {transform:translateZ(43px); background:rgba(45,212,191,.7);}
.face.back {transform:rotateY(180deg) translateZ(43px); background:rgba(20,184,166,.55);}
.face.right {transform:rotateY(90deg) translateZ(43px); background:rgba(14,165,233,.62);}
.face.left {transform:rotateY(-90deg) translateZ(43px); background:rgba(56,189,248,.42);}
.face.top {transform:rotateX(90deg) translateZ(43px); background:rgba(125,211,252,.58);}
.face.bottom {transform:rotateX(-90deg) translateZ(43px); background:rgba(15,118,110,.65);}
@keyframes floatcube {0%,100% {transform:rotateX(-24deg) rotateY(35deg) translateY(0)}
                                         50% {transform:rotateX(18deg) rotateY(215deg) translateY(-12px)}}
@keyframes orbit {from {transform:rotateX(68deg) rotateZ(18deg)} to {transform:rotateX(68deg) rotateZ(378deg)}}
.login-card {background:rgba(255,255,255,.96); border:1px solid rgba(255,255,255,.5); border-radius:16px;
                         padding:18px 20px 4px; text-align:left; box-shadow:0 18px 60px rgba(0,0,0,.24);}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------
# 0. ENTRY GATE
# ---------------------------------------------------------------------
if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
        st.markdown("""
        <div class="welcome-shell">
            <div class="welcome-content">
                <div class="welcome-mark">
                    <div class="cube">
                        <div class="face front"></div><div class="face back"></div>
                        <div class="face right"></div><div class="face left"></div>
                        <div class="face top"></div><div class="face bottom"></div>
                    </div>
                </div>
                <h1>TB Audit Intelligence</h1>
                <p>Turn trial-balance data into structured audit insight.</p>
                <p>Developed by Basid Basathiya<br>with Guidance of CA Smit Sir</p>
                <div class="login-card">
        """, unsafe_allow_html=True)
        with st.form("login_form"):
                st.subheader("Sign in")
                username = st.text_input("User ID")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Enter Audit Tool", use_container_width=True)
                if submitted:
                        if username.strip().upper() == "ADMIN" and password == "ADMIN":
                                st.session_state["authenticated"] = True
                                st.rerun()
                        else:
                                st.error("Invalid User ID or Password.")
        st.markdown("</div></div></div>", unsafe_allow_html=True)
        st.stop()

with st.sidebar:
        if st.button("Logout", key="logout_button", use_container_width=True):
                st.session_state["authenticated"] = False
                st.rerun()

# ---------------------------------------------------------------------
# 1. KNOWLEDGE BASE TAILORED TO THE USER'S TB GROUPS
# ---------------------------------------------------------------------
GROUP_RULES = {
    "Trade receivables": {
        "risk": "High",
        "assertions": "Existence, Valuation, Rights, Cut-off, Completeness",
        "procedures": [
            "Obtain customer-wise ageing and reconcile it to the general ledger/TB.",
            "Test subsequent receipts for material and overdue balances.",
            "Send external confirmations for selected material/customer balances.",
            "For non-responses, inspect invoices, contracts/service evidence and subsequent receipts.",
            "Review credit notes, write-offs and unusual adjustments after year-end.",
            "Assess recoverability/ECL or doubtful-debt provision and challenge long-outstanding items.",
            "Perform revenue/receivable cut-off testing around year-end.",
            "Investigate material year-on-year increases and new customers.",
        ],
        "documents": [
            "Customer-wise ageing",
            "Customer confirmations",
            "Sales invoices",
            "Customer contracts / engagement agreements",
            "Service or delivery evidence",
            "Subsequent bank receipts",
            "Credit-note listing",
            "ECL / doubtful-debt calculation",
            "Receivable reconciliation",
        ],
        "questions": [
            "Why has the balance increased materially?",
            "Are large balances recoverable?",
            "Are there long-outstanding or disputed balances?",
            "Are any balances related-party or unusual?",
        ],
    },
    "Revenue from operations": {
        "risk": "High",
        "assertions": "Occurrence, Completeness, Accuracy, Cut-off, Classification",
        "procedures": [
            "Reconcile revenue ledger/register to the financial statements and relevant supporting reports.",
            "Perform monthly and customer/service-line analytical review against prior year.",
            "Vouch material revenue samples to contracts/orders, invoices and evidence of delivery/service.",
            "Perform year-end cut-off testing for transactions before and after year-end.",
            "Review post-year-end credit notes, cancellations and reversals.",
            "Test unusual/manual journal entries affecting revenue.",
            "Where relevant, reconcile revenue to GST/e-invoice/statutory records.",
            "Investigate significant year-on-year growth and unusual customer concentration.",
        ],
        "documents": [
            "Revenue ledger",
            "Sales/revenue register",
            "Customer contracts",
            "Invoices",
            "Customer orders",
            "Delivery/service-completion evidence",
            "Credit notes",
            "Subsequent receipts",
            "Monthly revenue analysis",
            "Revenue cut-off listing",
            "Relevant GST/e-invoice reconciliations",
        ],
        "questions": [
            "What explains the year-on-year increase?",
            "Could revenue have been recognised before performance/cut-off?",
            "Are unusual year-end sales genuine?",
            "Are post-year-end credit notes material?",
        ],
    },
    "Trade payables due to others": {
        "risk": "High",
        "assertions": "Completeness, Existence, Cut-off, Accuracy, Rights/Obligations",
        "procedures": [
            "Obtain supplier-wise ageing and reconcile it to the GL/TB.",
            "Send confirmations to material and unusual suppliers.",
            "Inspect supplier statements and reconcile differences.",
            "Perform subsequent-payment testing for significant balances.",
            "Vouch material invoices to purchase orders/GRNs/service evidence.",
            "Search for unrecorded liabilities using subsequent payments and unmatched invoices.",
            "Perform purchase/AP cut-off testing around year-end.",
            "Investigate new suppliers and unusually large balances.",
            "Assess related-party status for material or unusual vendors.",
        ],
        "documents": [
            "Supplier ageing",
            "Supplier confirmations",
            "Supplier statements",
            "Purchase invoices",
            "Purchase orders",
            "GRNs / service-completion evidence",
            "Subsequent-payment listing",
            "Unrecorded-liability search",
            "Vendor master",
            "Related-party declaration",
        ],
        "questions": [
            "Is the liability complete?",
            "Why has a new/material vendor balance arisen?",
            "Were goods/services actually received?",
            "Are any vendors related parties?",
        ],
    },
    "Other current liabilities": {
        "risk": "High",
        "assertions": "Completeness, Accuracy, Cut-off, Classification, Presentation",
        "procedures": [
            "Obtain a detailed liability schedule and reconcile to the TB.",
            "Inspect underlying contracts, invoices, calculations and approvals.",
            "Confirm significant balances where appropriate.",
            "Test subsequent settlement.",
            "Search for unrecorded liabilities.",
            "Assess whether the balance is correctly classified and disclosed.",
            "Investigate new or very large current-year balances.",
        ],
        "documents": [
            "Liability schedule",
            "Contracts/agreements",
            "Invoices",
            "Calculations",
            "Confirmations",
            "Subsequent settlement evidence",
            "Journal support",
            "Related-party assessment",
        ],
        "questions": [
            "What is the nature of the liability?",
            "Why is the balance new or significantly higher?",
            "Is the liability complete and correctly classified?",
        ],
    },
    "Cash and bank balances": {
        "risk": "Medium",
        "assertions": "Existence, Rights, Completeness, Accuracy, Cut-off",
        "procedures": [
            "Obtain direct bank confirmations for material accounts where appropriate.",
            "Obtain bank statements and bank reconciliations.",
            "Test significant reconciling items and subsequent clearance.",
            "Review unusual transfers around year-end.",
            "Check restrictions, liens or pledged balances.",
            "Perform cash count where applicable.",
        ],
        "documents": [
            "Bank confirmations",
            "Bank statements",
            "Bank reconciliations",
            "Outstanding-item schedules",
            "Cash-count record where applicable",
            "Loan/security documents where relevant",
        ],
        "questions": [
            "Are all bank accounts recorded?",
            "Are reconciling items genuine and subsequently cleared?",
            "Are any balances restricted or pledged?",
        ],
    },
    "Intangible assets": {
        "risk": "High",
        "assertions": "Existence, Rights, Valuation, Classification, Presentation",
        "procedures": [
            "Obtain intangible-asset movement schedule and reconcile it to the TB.",
            "For additions, inspect acquisition agreements, invoices and valuation support.",
            "For goodwill, inspect acquisition/business-combination documentation and purchase accounting.",
            "Evaluate impairment indicators and management's impairment assessment.",
            "Review useful lives/amortisation policy and recalculate amortisation where applicable.",
            "Check classification, disclosures and supporting journal entries.",
        ],
        "documents": [
            "Intangible asset register",
            "Acquisition/business-combination agreement",
            "Purchase consideration calculation",
            "Valuation/PPA report",
            "Goodwill calculation",
            "Impairment assessment",
            "Management forecasts",
            "Amortisation schedule",
            "Board approvals",
            "Journal support",
        ],
        "questions": [
            "How did the asset arise?",
            "Is the recorded amount supported?",
            "Are impairment indicators present?",
            "Is the accounting treatment consistent with the applicable framework?",
        ],
    },
    "Property Plant and Equipment": {
        "risk": "High",
        "assertions": "Existence, Rights, Valuation, Completeness, Classification",
        "procedures": [
            "Obtain the fixed-asset register and reconcile it to the TB.",
            "Vouch material additions to invoices, purchase orders and payment records.",
            "Physically verify significant assets where appropriate.",
            "Inspect ownership/title documentation where relevant.",
            "Recalculate depreciation and review useful lives/residual values.",
            "Test disposals and check gain/loss calculations.",
            "Review capitalization of repairs and other expenditure.",
            "Consider impairment indicators.",
        ],
        "documents": [
            "Fixed asset register",
            "Purchase invoices",
            "Purchase orders",
            "Payment proof",
            "Physical verification record",
            "Title/ownership documents",
            "Depreciation schedule",
            "Capitalisation policy",
            "Disposal documents",
        ],
        "questions": [
            "Are assets physically present and owned?",
            "Could revenue expenditure have been capitalised?",
            "Is depreciation accurate?",
        ],
    },
    "Employee benefit expenses": {
        "risk": "High",
        "assertions": "Occurrence, Accuracy, Completeness, Cut-off, Classification",
        "procedures": [
            "Reconcile payroll/employee-cost schedules to the GL.",
            "Perform analytical review against headcount, payroll and prior year.",
            "Test selected payroll transactions to employee records and approvals.",
            "Reconcile statutory payroll deductions and remittances where applicable.",
            "Review bonus/incentive accruals and year-end provisions.",
            "Investigate unusual accounts within this group, especially accounts whose names do not appear to be employee-related.",
        ],
        "documents": [
            "Payroll register",
            "Employee master",
            "Payroll reconciliation",
            "Payslips/sample support",
            "Employment/bonus agreements",
            "Statutory deduction reconciliations",
            "Accrual calculations",
            "GL detail",
        ],
        "questions": [
            "Are employee costs genuine and complete?",
            "Are accruals supported?",
            "Does the account name match the group classification?",
        ],
    },
    "Other expenses": {
        "risk": "Medium",
        "assertions": "Occurrence, Accuracy, Cut-off, Classification, Completeness",
        "procedures": [
            "Perform analytical review by account against prior year.",
            "Vouch material and unusual expense transactions.",
            "Test year-end cut-off and accruals.",
            "Review capital-vs-revenue classification for significant items.",
            "Inspect supporting invoices, contracts and payment evidence.",
        ],
        "documents": [
            "Expense ledger",
            "Invoices",
            "Contracts",
            "Payment proof",
            "Accrual schedule",
            "Capitalisation assessment where relevant",
        ],
        "questions": [
            "Which accounts explain the largest movement?",
            "Are any expenses capital in nature?",
            "Are accruals and cut-off appropriate?",
        ],
    },
    "Other current assets": {
        "risk": "Medium",
        "assertions": "Existence, Valuation, Rights, Accuracy, Cut-off",
        "procedures": [
            "Obtain detailed schedule and reconcile to TB.",
            "Inspect underlying agreements, invoices and calculations.",
            "Test subsequent settlement/realisation.",
            "Assess recoverability and ageing.",
            "Investigate new material balances and unusual movements.",
        ],
        "documents": [
            "Current-asset schedule",
            "Invoices",
            "Contracts",
            "Supporting calculations",
            "Subsequent receipts/settlement",
            "Ageing where relevant",
        ],
        "questions": [
            "What created the balance?",
            "Is it recoverable?",
            "Why did it arise or increase during the year?",
        ],
    },
    "Short term loans and advances": {
        "risk": "High",
        "assertions": "Existence, Rights, Valuation, Classification, Completeness",
        "procedures": [
            "Obtain loan/advance schedule and reconcile to TB.",
            "Confirm significant balances with counterparties where appropriate.",
            "Inspect agreements and approvals.",
            "Test subsequent settlement.",
            "Assess recoverability and expected credit loss where relevant.",
            "Investigate balances whose account names appear inconsistent with this group.",
        ],
        "documents": [
            "Loan/advance schedule",
            "Agreements",
            "Confirmations",
            "Payment records",
            "Subsequent settlement",
            "Recoverability assessment",
            "Board/management approvals",
        ],
        "questions": [
            "Is the balance actually a loan/advance?",
            "Is it recoverable?",
            "Does the account/group classification make sense?",
        ],
    },
    "Tax Expenses": {
        "risk": "High",
        "assertions": "Accuracy, Completeness, Valuation, Classification, Presentation",
        "procedures": [
            "Reconcile tax expense to the tax computation and financial statements.",
            "Inspect current-tax computation and supporting schedules.",
            "Reconcile tax ledgers to returns/challans where applicable.",
            "Review provisions and payments.",
            "Assess classification of tax balances and related disclosures.",
        ],
        "documents": [
            "Tax computation",
            "Tax provision working",
            "Tax returns",
            "Challans/payment proofs",
            "Tax ledger",
            "Reconciliation to financial statements",
            "Tax notices/correspondence",
        ],
        "questions": [
            "Does the tax expense reconcile to the computation?",
            "Are provisions supported?",
            "Are tax balances classified correctly?",
        ],
    },
    "Reserves and surplus": {
        "risk": "Medium",
        "assertions": "Completeness, Accuracy, Rights, Presentation",
        "procedures": [
            "Obtain equity movement schedule and reconcile opening-to-closing balances.",
            "Agree current-year profit/loss transfer.",
            "Test dividend/appropriation entries where applicable.",
            "For FCTR, verify source transactions, exchange rates and calculation.",
            "Review presentation and disclosures.",
        ],
        "documents": [
            "Equity movement schedule",
            "Board/shareholder resolutions",
            "Profit allocation support",
            "FCTR calculation",
            "Exchange-rate support",
            "Financial statement note",
        ],
        "questions": [
            "Can every movement be reconciled?",
            "Is FCTR supported?",
            "Are equity movements properly authorised and disclosed?",
        ],
    },
    "Share capital": {
        "risk": "Medium",
        "assertions": "Existence, Rights, Completeness, Presentation",
        "procedures": [
            "Reconcile share capital to statutory/shareholder records.",
            "Inspect share allotment or transfer documents for movements.",
            "Verify authorisations and filings where applicable.",
            "Check presentation and disclosures.",
        ],
        "documents": [
            "Share register",
            "Allotment/transfer documents",
            "Board/shareholder resolutions",
            "Statutory filings",
            "Share capital reconciliation",
        ],
        "questions": [
            "Do movements agree with statutory records?",
            "Are all changes authorised and properly recorded?",
        ],
    },
    "Short term borrowings": {
        "risk": "High",
        "assertions": "Completeness, Accuracy, Obligations, Classification, Presentation",
        "procedures": [
            "Obtain borrowing schedule and reconcile to TB.",
            "Inspect loan agreements and lender statements.",
            "Confirm material borrowings.",
            "Recalculate interest and review accrued finance costs.",
            "Review current/non-current classification and covenant compliance.",
        ],
        "documents": [
            "Borrowing schedule",
            "Loan agreements",
            "Lender statements/confirmations",
            "Repayment schedules",
            "Interest calculations",
            "Covenant compliance",
        ],
        "questions": [
            "Are all borrowings recorded?",
            "Is the classification correct?",
            "Are interest and covenants properly accounted for?",
        ],
    },
    "short term borrowings": {
        "risk": "High",
        "assertions": "Completeness, Accuracy, Obligations, Classification, Presentation",
        "procedures": [
            "Obtain borrowing schedule and reconcile to TB.",
            "Inspect agreements and lender statements.",
            "Confirm material balances.",
            "Recalculate interest and inspect repayments.",
        ],
        "documents": [
            "Borrowing schedule", "Loan agreements", "Lender statements",
            "Repayment schedule", "Interest calculation",
        ],
        "questions": ["Are all borrowings recorded and correctly classified?"],
    },
    "Depreciation and amortization expenses": {
        "risk": "Medium",
        "assertions": "Accuracy, Classification, Completeness",
        "procedures": [
            "Reconcile depreciation/amortisation expense to the fixed/intangible asset schedules.",
            "Recalculate depreciation/amortisation for selected assets.",
            "Review useful lives, residual values and start/stop dates.",
            "Investigate significant new depreciation/amortisation charges.",
        ],
        "documents": [
            "Depreciation schedule",
            "Fixed asset register",
            "Intangible asset register",
            "Accounting policy",
            "Recalculation workings",
        ],
        "questions": [
            "Why is depreciation/amortisation new or significantly changed?",
            "Are useful lives and calculations appropriate?",
        ],
    },
    "Non current investments": {
        "risk": "High",
        "assertions": "Existence, Rights, Valuation, Classification",
        "procedures": [
            "Obtain investment schedule and reconcile to TB.",
            "Inspect investment agreements/statements.",
            "Confirm holdings where appropriate.",
            "Assess valuation and impairment.",
            "Review classification and disclosures.",
        ],
        "documents": [
            "Investment schedule",
            "Investment statements/certificates",
            "Agreements",
            "Valuation/impairment assessment",
            "Board approvals",
        ],
        "questions": ["Do the investments exist and are they appropriately valued/classified?"],
    },
    "other income": {
        "risk": "Medium",
        "assertions": "Occurrence, Accuracy, Completeness, Classification",
        "procedures": [
            "Vouch material income items to supporting documents.",
            "Perform analytical review against prior year.",
            "Test unusual items and year-end cut-off.",
            "Check classification and presentation.",
        ],
        "documents": [
            "Income ledger", "Supporting agreements", "Invoices/credit notes",
            "Bank statements", "Calculations",
        ],
        "questions": ["What explains unusual income movements?"],
    },
}

DEFAULT_RULE = {
    "risk": "Medium",
    "assertions": "Existence, Completeness, Accuracy, Classification",
    "procedures": [
        "Understand the nature of the account and reconcile it to the TB.",
        "Perform analytical review against prior year.",
        "Vouch material/unusual transactions to supporting documents.",
        "Test cut-off and classification where relevant.",
    ],
    "documents": ["General ledger", "Invoices/supporting documents", "Reconciliation", "Payment/receipt evidence"],
    "questions": ["What is the nature of this balance?", "Why has it moved materially?"],
}

# Account-name signals. These supplement the Group field.
ACCOUNT_SIGNALS = [
    (["goodwill"], "Goodwill / acquisition", "High",
     "Inspect acquisition and purchase accounting; assess impairment; obtain valuation/PPA support."),
    (["accrued income"], "Accrued Income", "High",
     "Verify basis of accrual, subsequent invoicing/collection and revenue cut-off."),
    (["tax expense", "current tax", "provision for tax"], "Tax Classification Review", "High",
     "Reconcile tax computation and assess whether account is correctly grouped/presented."),
    (["cost of goods sold", "cogs"], "COGS Classification Review", "High",
     "Inspect GL transactions and assess whether grouping/classification is appropriate."),
    (["fctr", "foreign currency translation"], "Foreign Currency Translation", "Medium",
     "Reperform FCTR calculation, verify exchange rates and underlying foreign-currency balances."),
    (["reimbursement"], "Reimbursement", "Medium",
     "Inspect nature, supporting invoices and recoverability; assess correct classification."),
]

# ---------------------------------------------------------------------
# 2. DATA FUNCTIONS
# ---------------------------------------------------------------------
def load_testing_tb(uploaded_file):
    if uploaded_file.name.lower().endswith(".csv"):
        raw = pd.read_csv(uploaded_file)
    else:
        raw = pd.read_excel(uploaded_file, sheet_name=0)

    # Exact structure of Testing TB.xlsx:
    # Code | Account Name | Closing | PY Closing | Group
    expected = ["Code", "Account Name", "Closing", "PY Closing", "Group"]

    if all(c in raw.columns for c in expected):
        tb = raw[expected].copy()
    else:
        # Flexible fallback: normalize common headers.
        rename = {}
        for c in raw.columns:
            s = re.sub(r"[^a-z0-9]+", " ", str(c).lower()).strip()
            if s in ["code", "account code", "ledger code"]:
                rename[c] = "Code"
            elif s in ["account name", "account", "ledger", "particulars", "description"]:
                rename[c] = "Account Name"
            elif s in ["closing", "closing balance", "current", "current year"]:
                rename[c] = "Closing"
            elif s in ["py closing", "previous closing", "prior closing", "previous year", "py"]:
                rename[c] = "PY Closing"
            elif s in ["group", "account group", "category"]:
                rename[c] = "Group"
        raw = raw.rename(columns=rename)
        missing = [c for c in expected if c not in raw.columns]
        if missing:
            raise ValueError(f"Missing required columns: {missing}")
        tb = raw[expected].copy()

    tb = tb[tb["Account Name"].notna()].copy()
    for c in ["Closing", "PY Closing"]:
        tb[c] = pd.to_numeric(tb[c], errors="coerce").fillna(0)
    tb["Code"] = tb["Code"].astype(str).str.replace(r"\.0$", "", regex=True)
    tb["Group"] = tb["Group"].fillna("Unclassified").astype(str).str.strip()
    tb["Account Name"] = tb["Account Name"].astype(str).str.strip()
    return tb


def group_rule(group):
    if group in GROUP_RULES:
        return GROUP_RULES[group]
    # case-insensitive match
    for k, v in GROUP_RULES.items():
        if k.lower() == group.lower():
            return v
    return DEFAULT_RULE


def account_signal(account):
    text = str(account).lower()
    for keys, label, risk, procedure in ACCOUNT_SIGNALS:
        if any(k in text for k in keys):
            return label, risk, procedure
    return "", "", ""


def analyze(tb, materiality):
    x = tb.copy()
    x["Movement"] = x["Closing"] - x["PY Closing"]
    x["Absolute Balance"] = x["Closing"].abs()
    x["Absolute Movement"] = x["Movement"].abs()

    x["Movement %"] = x.apply(
        lambda r: (abs(r["Movement"]) / abs(r["PY Closing"]) * 100)
        if abs(r["PY Closing"]) > 0 else (999.0 if abs(r["Closing"]) > 0 else 0.0),
        axis=1
    )
    x["Materiality %"] = x["Absolute Balance"].apply(
        lambda v: (v / materiality * 100) if materiality > 0 else 0
    )
    x["New Current Balance"] = (x["Closing"].abs() > 0) & (x["PY Closing"].abs() == 0)
    x["Current Zeroed"] = (x["Closing"].abs() == 0) & (x["PY Closing"].abs() > 0)
    x["Negative Balance"] = x["Closing"] < 0
    x["Significant Movement"] = (x["Movement %"] >= 50) | x["New Current Balance"]
    x["Large Balance"] = x["Absolute Balance"] >= materiality

    def enrich(row):
        rule = group_rule(row["Group"])
        label, signal_risk, signal_proc = account_signal(row["Account Name"])

        reasons = []
        score = 0

        if row["Large Balance"]:
            score += 3
            reasons.append("balance is at/above configured materiality")
        if row["Materiality %"] >= 200:
            score += 2
            reasons.append("balance exceeds 2× materiality")
        if row["Significant Movement"]:
            score += 2
            reasons.append("significant year-on-year movement/new balance")
        if row["New Current Balance"]:
            score += 2
            reasons.append("new current-year balance")
        if row["Negative Balance"]:
            score += 1
            reasons.append("negative balance requires explanation")
        if signal_risk == "High":
            score += 3
            reasons.append(f"account-specific signal: {label}")
        elif rule["risk"] == "High":
            score += 2
            reasons.append(f"{row['Group']} is a high-attention audit area")

        if score >= 5:
            risk = "High"
        elif score >= 2:
            risk = "Medium"
        else:
            risk = "Low"

        procedures = list(rule["procedures"])
        documents = list(rule["documents"])
        questions = list(rule["questions"])
        area = row["Group"]

        if signal_proc:
            procedures.insert(0, signal_proc)
            area = label

        if row["Significant Movement"]:
            procedures.append(
                "Investigate the year-on-year movement and obtain a documented explanation supported by source evidence."
            )
            documents.append("Year-on-year movement reconciliation / management explanation")

        if row["New Current Balance"]:
            procedures.append(
                "For a new current-year balance, trace the originating transaction and verify recognition, classification and supporting evidence."
            )

        if row["Negative Balance"]:
            procedures.append(
                "Investigate the negative balance and determine whether it represents a genuine credit/debit position, reclassification, or posting error."
            )
            documents.append("Account reconciliation and explanation for negative balance")

        # Remove duplicate documents/procedures.
        procedures = list(dict.fromkeys(procedures))
        documents = list(dict.fromkeys(documents))
        questions = list(dict.fromkeys(questions))

        return pd.Series({
            "Risk": risk,
            "Risk Score": score,
            "Risk Reasons": "; ".join(reasons) if reasons else "Routine / lower relative significance",
            "Audit Area": area,
            "Assertions": rule["assertions"],
            "Suggested Procedures": " ".join(f"• {p}" for p in procedures),
            "Evidence Required": " | ".join(documents),
            "Audit Questions": " | ".join(questions),
        })

    enriched = x.apply(enrich, axis=1)
    return pd.concat([x, enriched], axis=1)


def group_analysis(df):
    g = df.groupby("Group", dropna=False).agg(
        Accounts=("Account Name", "count"),
        Closing=("Closing", "sum"),
        PY_Closing=("PY Closing", "sum"),
        High_Risk=("Risk", lambda s: (s == "High").sum()),
        Medium_Risk=("Risk", lambda s: (s == "Medium").sum()),
        New_Balances=("New Current Balance", "sum"),
        Significant_Movements=("Significant Movement", "sum"),
    ).reset_index()
    g["Movement"] = g["Closing"] - g["PY_Closing"]
    g["Movement %"] = g.apply(
        lambda r: abs(r["Movement"]) / abs(r["PY_Closing"]) * 100
        if abs(r["PY_Closing"]) > 0 else (999.0 if abs(r["Closing"]) > 0 else 0),
        axis=1
    )
    return g.sort_values("Absolute" if "Absolute" in g.columns else "Closing", ascending=False)


def fmt_money(v):
    return f"₹{v:,.0f}"


# ---------------------------------------------------------------------
# BENFORD'S LAW - DEBTORS AND CREDITORS
# ---------------------------------------------------------------------
BENFORD_EXPECTED = {
    1: 0.301, 2: 0.176, 3: 0.125, 4: 0.097, 5: 0.079,
    6: 0.067, 7: 0.058, 8: 0.051, 9: 0.046,
}

BENFORD_PROCEDURES = {
    "Debtor": [
        "Obtain debtor balance confirmation.", "Verify subsequent receipts.",
        "Examine large/unusual invoices.", "Trace selected invoices to supporting documents.",
        "Verify sales invoices.", "Check credit notes after year-end.", "Review ageing.",
        "Investigate unusual round-value transactions.", "Review year-end transactions.",
        "Reconcile ledger with supporting records.", "Check related-party indicators where relevant.",
        "Investigate unusual journal entries.",
    ],
    "Creditor": [
        "Obtain creditor confirmation.", "Verify subsequent payments.",
        "Examine large/unusual purchases.", "Trace selected invoices to supporting documents.",
        "Verify purchase invoices.", "Check GRNs/goods receipt documentation where applicable.",
        "Review unmatched invoices.", "Review year-end cut-off.",
        "Investigate unusual round-value transactions.", "Reconcile creditor ledger with supporting records.",
        "Review debit/credit notes.", "Check related-party indicators where relevant.",
    ],
}


def _normalise_header(value):
    return re.sub(r"[^a-z0-9]+", " ", str(value).lower()).strip()


def _find_column(columns, candidates):
    normalised = {_normalise_header(c): c for c in columns}
    for candidate in candidates:
        if candidate in normalised:
            return normalised[candidate]
    for key, original in normalised.items():
        if any(candidate in key for candidate in candidates):
            return original
    return None


def _benford_party_type(value):
    text = str(value).lower()
    if any(word in text for word in ["creditor", "payable", "vendor", "supplier"]):
        return "Creditor"
    if any(word in text for word in ["debtor", "receivable", "customer", "client"]):
        return "Debtor"
    return "Unclassified"


def load_benford_data(uploaded_file):
    """Load transaction-level data while retaining every original column."""
    if uploaded_file.name.lower().endswith(".csv"):
        raw = pd.read_csv(uploaded_file)
    else:
        raw = pd.read_excel(uploaded_file, sheet_name=0)
    if raw.empty:
        raise ValueError("The transaction file contains no rows.")
    columns = list(raw.columns)
    amount = _find_column(columns, ["amount", "transaction amount", "value", "net amount", "balance"])
    debit = _find_column(columns, ["debit", "debit amount", "dr"])
    credit = _find_column(columns, ["credit", "credit amount", "cr"])
    party = _find_column(columns, ["party name", "party", "customer", "vendor", "counterparty", "account name"])
    code = _find_column(columns, ["party code", "customer code", "vendor code", "account code", "code"])
    group = _find_column(columns, ["party type", "type", "debtor creditor", "category", "group"])
    if not party:
        raise ValueError("A party/account name column is required for Debtor/Creditor selection.")
    if not amount and not debit and not credit:
        raise ValueError("An Amount column or Debit/Credit columns are required.")
    data = raw.copy()
    data["_Party"] = data[party].fillna("Unidentified").astype(str).str.strip()
    data["_Party Code"] = data[code].fillna("").astype(str).str.replace(r"\.0$", "", regex=True) if code else ""
    data["_Group"] = data[group].fillna("").astype(str).str.strip() if group else ""
    if amount:
        data["_Benford Amount"] = pd.to_numeric(data[amount], errors="coerce")
        data["_Debit Amount"] = data["_Benford Amount"]
        data["_Credit Amount"] = 0.0
    else:
        data["_Debit Amount"] = pd.to_numeric(data[debit], errors="coerce").fillna(0)
        data["_Credit Amount"] = pd.to_numeric(data[credit], errors="coerce").fillna(0)
        data["_Benford Amount"] = data["_Debit Amount"] + data["_Credit Amount"]
    data["_Benford Amount"] = data["_Benford Amount"].abs()
    data["_Party Type"] = data["_Group"].map(_benford_party_type)
    data["_Original Row"] = range(1, len(data) + 1)
    return data


def clean_benford_amounts(data):
    result = data.copy()
    numeric = pd.to_numeric(result["_Benford Amount"], errors="coerce")
    result["_Valid Amount"] = numeric.notna() & numeric.gt(0)
    result["_Exclusion Reason"] = ""
    result.loc[numeric.isna(), "_Exclusion Reason"] = "Blank or non-numeric amount"
    result.loc[numeric.eq(0), "_Exclusion Reason"] = "Zero amount"
    result["_Benford Amount"] = numeric.abs()
    result["First Digit"] = result["_Benford Amount"].map(
        lambda value: int(str(value).replace(".", "", 1).lstrip("0")[0])
        if pd.notna(value) and value > 0 and str(value).replace(".", "", 1).lstrip("0") else pd.NA
    )
    return result


def benford_data_from_tb(tb):
    """Adapt the imported TB as the Benford population without another upload."""
    data = tb.copy()
    data["_Party"] = data["Account Name"].fillna("Unidentified").astype(str).str.strip()
    data["_Party Code"] = data["Code"].fillna("").astype(str)
    data["_Group"] = data["Group"].fillna("").astype(str).str.strip()
    data["_Benford Amount"] = pd.to_numeric(data["Closing"], errors="coerce").abs()
    data["_Debit Amount"] = data["_Benford Amount"]
    data["_Credit Amount"] = 0.0
    data["_Party Type"] = data["_Group"].map(_benford_party_type)
    data["_Original Row"] = range(1, len(data) + 1)
    return clean_benford_amounts(data)


def calculate_mad(observed, expected=BENFORD_EXPECTED):
    return sum(abs(observed.get(digit, 0) - expected[digit]) for digit in expected) / 9


def calculate_chi_square(counts, sample_size, expected=BENFORD_EXPECTED):
    if sample_size <= 0:
        return float("nan"), float("nan"), 8
    statistic = sum((counts.get(digit, 0) - sample_size * probability) ** 2 /
                    (sample_size * probability) for digit, probability in expected.items())
    x = statistic / 2
    p_value = math.exp(-x) * sum(x ** power / math.factorial(power) for power in range(4))
    return statistic, p_value, 8


def classify_benford_risk(sample_size, mad, p_value, maximum_deviation, threshold,
                          mad_moderate, mad_high, p_moderate, p_high, deviation_high):
    if sample_size < threshold:
        return "INSUFFICIENT DATA"
    if (p_value < p_high and mad >= mad_high) or (p_value < p_high and maximum_deviation >= deviation_high):
        return "HIGH RISK"
    if p_value < p_moderate or mad >= mad_moderate or maximum_deviation >= deviation_high / 2:
        return "MODERATE"
    return "LOW / ACCEPTABLE"


def analyze_party(data, party_type, party_name, threshold=100, settings=None):
    settings = settings or {"mad_moderate": .015, "mad_high": .025, "p_moderate": .05,
                             "p_high": .01, "deviation_high": .10}
    party_rows = data[(data["_Party Type"] == party_type) & (data["_Party"] == party_name)]
    valid = party_rows[party_rows["_Valid Amount"] & party_rows["First Digit"].notna()].copy()
    counts = valid["First Digit"].value_counts().to_dict()
    sample_size = len(valid)
    observed = {digit: counts.get(digit, 0) / sample_size if sample_size else 0 for digit in BENFORD_EXPECTED}
    mad = calculate_mad(observed)
    chi_square, p_value, degrees = calculate_chi_square(counts, sample_size)
    deviations = {digit: observed[digit] - BENFORD_EXPECTED[digit] for digit in BENFORD_EXPECTED}
    maximum_digit = max(deviations, key=lambda digit: abs(deviations[digit]))
    risk = classify_benford_risk(sample_size, mad, p_value, abs(deviations[maximum_digit]), threshold, **settings)
    details = pd.DataFrame([{
        "Digit": digit, "Expected %": BENFORD_EXPECTED[digit] * 100,
        "Actual %": observed[digit] * 100, "Difference %": deviations[digit] * 100,
        "Transaction Count": counts.get(digit, 0),
        "Status": "Significant deviation" if abs(deviations[digit]) >= settings["deviation_high"] else "Normal",
    } for digit in BENFORD_EXPECTED])
    result = {
        "Party Type": party_type, "Party Code": party_rows["_Party Code"].iloc[0] if len(party_rows) else "",
        "Party Name": party_name, "Transactions": sample_size, "Total Transaction Value": valid["_Benford Amount"].sum(),
        "Total Rows": len(party_rows), "Excluded": len(party_rows) - sample_size,
        "MAD": mad, "Chi-Square": chi_square, "P-Value": p_value, "Degrees of Freedom": degrees,
        "Largest Deviating Digit": maximum_digit, "Actual %": observed[maximum_digit] * 100,
        "Expected %": BENFORD_EXPECTED[maximum_digit] * 100,
        "Maximum Deviation %": abs(deviations[maximum_digit]) * 100, "Risk Classification": risk,
        "Audit Priority": "Immediate investigation" if risk == "HIGH RISK" else "Review" if risk == "MODERATE" else "Routine",
        "Recommended Audit Procedure": " ".join(BENFORD_PROCEDURES.get(party_type, [])),
    }
    return result, details, valid


def benford_export_bytes(results, details, transactions):
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        pd.DataFrame(results).to_excel(writer, index=False, sheet_name="Party Results")
        pd.DataFrame(details).to_excel(writer, index=False, sheet_name="Digit Details")
        transactions.to_excel(writer, index=False, sheet_name="Transaction Drilldown")
    buf.seek(0)
    return buf.getvalue()


def benford_pdf_bytes(results):
    if not REPORTLAB_OK:
        return None
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), rightMargin=12*mm, leftMargin=12*mm,
                            topMargin=12*mm, bottomMargin=12*mm)
    styles = getSampleStyleSheet()
    body = ParagraphStyle("BenfordBody", parent=styles["BodyText"], fontSize=8, leading=10)
    story = [Paragraph("Benford's Law Analysis - Debtors & Creditors", styles["Title"]),
             Paragraph("Analytical screening only: a deviation does not establish fraud, manipulation or error.", body),
             Spacer(1, 8)]
    rows = [["Type", "Party", "Transactions", "MAD", "Chi-square", "P-value", "Max deviation", "Risk"]]
    for result in results:
        rows.append([result["Party Type"], result["Party Name"], str(result["Transactions"]),
                     f"{result['MAD']:.2%}", f"{result['Chi-Square']:.2f}", f"{result['P-Value']:.4f}",
                     f"{result['Maximum Deviation %']:.2f}%", result["Risk Classification"]])
    table = Table(rows, repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAECF0")),
                               ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#D0D5DD")),
                               ("FONTSIZE", (0, 0), (-1, -1), 7), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(table)
    story.append(Spacer(1, 8))
    story.append(Paragraph("Benford applicability should be assessed by the auditor before relying on the result.", body))
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------
# 3. REPORT GENERATORS
# ---------------------------------------------------------------------
def excel_bytes(df):
    buf = io.BytesIO()
    ga = group_analysis(df)
    top = df.sort_values(["Risk Score", "Absolute Balance"], ascending=[False, False])

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Account Analysis")
        ga.to_excel(writer, index=False, sheet_name="Group Analysis")
        top.head(50).to_excel(writer, index=False, sheet_name="Top Audit Attention")
        df[df["Significant Movement"]].to_excel(writer, index=False, sheet_name="Movement Flags")
        df[df["New Current Balance"]].to_excel(writer, index=False, sheet_name="New Balances")
        df[df["Negative Balance"]].to_excel(writer, index=False, sheet_name="Negative Balances")
    buf.seek(0)
    return buf.getvalue()


def working_paper_excel_bytes(df, entity, materiality):
    """Create a complete group and individual-ledger working-paper workbook."""
    buf = io.BytesIO()
    ga = group_analysis(df)
    individual = df.sort_values(["Risk Score", "Absolute Balance"], ascending=[False, False]).copy()
    group_rows = []
    for group, group_df in df.groupby("Group", dropna=False, sort=True):
        procedures = []
        evidence = []
        assertions = []
        for value in group_df["Suggested Procedures"]:
            procedures.extend(str(value).split("•"))
        for value in group_df["Evidence Required"]:
            evidence.extend(str(value).split("|"))
        for value in group_df["Assertions"]:
            assertions.extend(str(value).split(","))
        group_rows.append({
            "Entity": entity,
            "Group": group,
            "Accounts": len(group_df),
            "Closing": group_df["Closing"].sum(),
            "PY Closing": group_df["PY Closing"].sum(),
            "Movement": group_df["Movement"].sum(),
            "High Risk Accounts": int((group_df["Risk"] == "High").sum()),
            "Assertions": " | ".join(sorted(set(x.strip() for x in assertions if x.strip()))),
            "Audit Procedures": " | ".join(sorted(set(x.strip() for x in procedures if x.strip()))),
            "Evidence Required": " | ".join(sorted(set(x.strip() for x in evidence if x.strip()))),
            "Group Conclusion": "Document the results of procedures performed and conclude on the group balance.",
        })
    group_wp = pd.DataFrame(group_rows)
    ledger_wp = individual[[
        "Code", "Account Name", "Group", "Closing", "PY Closing", "Movement",
        "Risk", "Risk Score", "Risk Reasons", "Audit Area", "Assertions",
        "Suggested Procedures", "Evidence Required", "Audit Questions",
    ]]

    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        pd.DataFrame([{
            "Entity": entity,
            "Generated": datetime.now().strftime("%d-%b-%Y %H:%M"),
            "Configured Materiality": materiality,
            "Accounts Covered": len(df),
            "Groups Covered": df["Group"].nunique(dropna=False),
        }]).to_excel(writer, index=False, sheet_name="WP Cover")
        group_wp.to_excel(writer, index=False, sheet_name="Group Working Papers")
        ledger_wp.to_excel(writer, index=False, sheet_name="Individual Ledger WPs")
        ga.to_excel(writer, index=False, sheet_name="Group Analysis")
    buf.seek(0)
    return buf.getvalue()


def individual_working_paper_excel_bytes(row, entity):
    """Create a workbook for one selected ledger account."""
    buf = io.BytesIO()
    account = row.to_frame().T
    checklist = pd.DataFrame({
        "Working Paper Field": [
            "Entity", "Account", "Code", "Group", "Audit Area", "Closing", "PY Closing",
            "Movement", "Risk", "Assertions", "Risk Rationale", "Procedures",
            "Evidence Required", "Audit Questions", "Finding", "Conclusion",
        ],
        "Value": [
            entity, row["Account Name"], row["Code"], row["Group"], row["Audit Area"],
            row["Closing"], row["PY Closing"], row["Movement"], row["Risk"],
            row["Assertions"], row["Risk Reasons"], row["Suggested Procedures"],
            row["Evidence Required"], row["Audit Questions"], "", "",
        ],
    })
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        checklist.to_excel(writer, index=False, sheet_name="Working Paper")
        account.to_excel(writer, index=False, sheet_name="Ledger Detail")
    buf.seek(0)
    return buf.getvalue()


def pdf_bytes(df, entity, materiality):
    if not REPORTLAB_OK:
        return None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4),
        rightMargin=12*mm, leftMargin=12*mm, topMargin=12*mm, bottomMargin=12*mm
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("T", parent=styles["Title"], fontSize=18, leading=22)
    body = ParagraphStyle("B", parent=styles["BodyText"], fontSize=8, leading=10)

    high = int((df["Risk"] == "High").sum())
    med = int((df["Risk"] == "Medium").sum())
    new = int(df["New Current Balance"].sum())
    mov = int(df["Significant Movement"].sum())
    anomalies = int(df["Audit Area"].str.contains("Review|Translation|Reimbursement|Goodwill|Accrued", case=False, na=False).sum())

    story = [
        Paragraph("TB → Audit Intelligence Report", title),
        Spacer(1, 5),
        Paragraph(f"<b>Entity:</b> {entity} &nbsp;&nbsp; <b>Generated:</b> {datetime.now().strftime('%d-%b-%Y %H:%M')}", body),
        Paragraph(f"<b>Configured materiality:</b> {fmt_money(materiality)}", body),
        Spacer(1, 8),
        Paragraph(
            f"<b>Summary:</b> {len(df)} accounts | High risk: {high} | Medium: {med} | "
            f"Significant movements: {mov} | New balances: {new} | Classification/account signals: {anomalies}",
            body
        ),
        Spacer(1, 10),
    ]

    top = df.sort_values(["Risk Score", "Absolute Balance"], ascending=[False, False]).head(30)
    data = [["Account", "Group", "Closing", "PY Closing", "Movement %", "Risk", "Reason"]]
    for _, r in top.iterrows():
        data.append([
            str(r["Account Name"])[:35],
            str(r["Group"])[:28],
            fmt_money(r["Closing"]),
            fmt_money(r["PY Closing"]),
            f"{r['Movement %']:.0f}%" if r["Movement %"] < 999 else "New",
            r["Risk"],
            str(r["Risk Reasons"])[:75],
        ])

    table = Table(data, colWidths=[45*mm, 40*mm, 28*mm, 28*mm, 20*mm, 18*mm, 78*mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#EAECF0")),
        ("GRID", (0,0), (-1,-1), .25, colors.HexColor("#D0D5DD")),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 7),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F9FAFB")]),
    ]))
    story.append(table)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Professional-judgement note:</b> The risk flags and procedures are audit-assistance outputs "
        "based on the uploaded TB, year-on-year movement, group classification and configured materiality. "
        "They do not replace engagement-specific risk assessment, applicable auditing standards, materiality "
        "judgement or the auditor's evaluation of sufficient appropriate audit evidence.",
        body
    ))
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


def working_paper_pdf_bytes(df, entity, materiality):
    if not REPORTLAB_OK:
        return None

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=landscape(A4), rightMargin=12*mm, leftMargin=12*mm,
        topMargin=12*mm, bottomMargin=12*mm
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("WPT", parent=styles["Title"], fontSize=17, leading=21)
    heading = ParagraphStyle("WPH", parent=styles["Heading2"], fontSize=11, leading=14)
    body = ParagraphStyle("WPB", parent=styles["BodyText"], fontSize=7, leading=9)
    story = [
        Paragraph("Audit Working Papers - Group and Individual Ledger", title),
        Paragraph(
            f"<b>Entity:</b> {entity} &nbsp;&nbsp; <b>Generated:</b> {datetime.now().strftime('%d-%b-%Y %H:%M')} "
            f"&nbsp;&nbsp; <b>Materiality:</b> {fmt_money(materiality)}",
            body,
        ),
        Spacer(1, 8),
    ]

    story.append(Paragraph("Group Working Papers", heading))
    group_data = [["Group", "Accounts", "Closing", "Movement", "High Risk", "Assertions"]]
    for _, row in group_analysis(df).iterrows():
        group_data.append([
            str(row["Group"])[:30], str(int(row["Accounts"])), fmt_money(row["Closing"]),
            fmt_money(row["Movement"]), str(int(row["High_Risk"])),
            str(", ".join(sorted(set(
                item.strip() for value in df.loc[df["Group"] == row["Group"], "Assertions"]
                for item in str(value).split(",") if item.strip()
            ))))[:70],
        ])
    group_table = Table(group_data, colWidths=[45*mm, 18*mm, 28*mm, 28*mm, 20*mm, 95*mm], repeatRows=1)
    group_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAECF0")),
        ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#D0D5DD")),
        ("FONTSIZE", (0, 0), (-1, -1), 7), ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.extend([group_table, Spacer(1, 8), Paragraph("Individual Ledger Working Papers", heading)])

    ledger_data = [["Code", "Account", "Group", "Balance", "Risk", "Audit Area", "Procedures / Evidence"]]
    for _, row in df.sort_values(["Risk Score", "Absolute Balance"], ascending=[False, False]).iterrows():
        details = f"Procedures: {row['Suggested Procedures']} Evidence: {row['Evidence Required']}"
        ledger_data.append([
            str(row["Code"])[:12], str(row["Account Name"])[:28], str(row["Group"])[:25],
            fmt_money(row["Closing"]), str(row["Risk"]), str(row["Audit Area"])[:25], details[:180],
        ])
    ledger_table = Table(
        ledger_data, colWidths=[18*mm, 35*mm, 32*mm, 25*mm, 16*mm, 30*mm, 84*mm], repeatRows=1
    )
    ledger_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAECF0")),
        ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#D0D5DD")),
        ("FONTSIZE", (0, 0), (-1, -1), 6), ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F9FAFB")]),
    ]))
    story.append(ledger_table)
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()


# ---------------------------------------------------------------------
# 4. APP UI
# ---------------------------------------------------------------------
st.markdown("""
<div class="hero">
<h1>TB → Audit Intelligence & Documentation</h1>
<p>Purpose-built for the Testing TB structure: Code • Account Name • Closing • PY Closing • Group</p>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("⚙️ Engagement Settings")
    entity = st.text_input("Entity / Client", "BH / Demo Entity")
    materiality = st.number_input(
        "Overall Materiality (₹)",
        min_value=1.0, value=10_000_000.0, step=500_000.0, format="%.2f"
    )
    st.divider()
    st.caption("Risk scoring is explainable. Change the materiality to see the account ranking change.")
    st.info(
        "This application assists audit planning and documentation. It does not replace professional judgement."
    )

tab_input, tab_dashboard, tab_accounts, tab_evidence, tab_wp, tab_benford, tab_journey = st.tabs([
    "📥 TB Input", "📊 Audit Dashboard", "🔎 Account Analysis",
    "🧾 Evidence Planner", "📝 Working Paper", "🔍 Benford's Law – Debtors & Creditors", "🧊 Audit Journey"
])

with tab_input:
    st.subheader("Import Testing TB.xlsx")
    uploaded = st.file_uploader(
        "Upload the Trial Balance",
        type=["xlsx", "xls", "csv"],
        help="Designed specifically for Code, Account Name, Closing, PY Closing and Group."
    )
    if uploaded:
        try:
            tb = load_testing_tb(uploaded)
            st.session_state["tb"] = tb
            st.success(f"Loaded {len(tb):,} populated accounts.")
        except Exception as e:
            st.error(f"Could not load the file: {e}")
    else:
        # Built-in sample matching the user's structure so the UI can be tested.
        sample = pd.DataFrame({
            "Code": ["1001","1002","1201","1301","1401","1501","1601","1701"],
            "Account Name": [
                "Ace Wireless","Intuit Inc.","KMK Ventures Pvt Ltd",
                "Goodwill","Accrued Income","Cost of Goods Sold",
                "Cash & Bank","Current Tax expense"
            ],
            "Closing": [117371,105390000,181090000,94650000,10370000,1178000000,6267627,7841094],
            "PY Closing": [111085,41290000,0,0,0,0,9165032,0],
            "Group": [
                "Trade receivables","Trade receivables","Trade payables due to others",
                "Intangible assets","Other current assets","Employee benefit expenses",
                "Cash and bank balances","Tax Expenses"
            ],
        })
        st.session_state["tb"] = sample
        st.info("No file uploaded. A small Testing-TB-style demo is loaded.")

    if "tb" in st.session_state:
        st.dataframe(st.session_state["tb"], use_container_width=True, height=360)
        st.download_button(
            "⬇️ Download imported TB as CSV",
            st.session_state["tb"].to_csv(index=False).encode(),
            "Testing_TB_normalized.csv",
            "text/csv"
        )

with tab_benford:
    st.markdown("## BENFORD'S LAW ANALYSIS – DEBTORS & CREDITORS")
    st.caption("Audit risk-screening procedure. A deviation from Benford's Law does not by itself indicate fraud, manipulation, or error.")
    st.info("Benford applicability should be assessed by the auditor before relying on the result. It may be inappropriate for small, constrained, fixed-price, formula-generated, or uniformly priced populations.")

    if "tb" not in st.session_state:
        st.warning("Import the Trial Balance in the TB Input tab first.")
    else:
        benford_data = benford_data_from_tb(st.session_state["tb"])
        party_types = [value for value in ["Debtor", "Creditor"] if value in benford_data["_Party Type"].unique()]
        if not party_types:
            st.warning("No Debtor or Creditor groups were identified. Provide a Party Type/Group column containing values such as Debtor, Creditor, Receivable, Payable, Customer or Supplier.")
        else:
            selected_type = st.selectbox("Select population", ["Select a population"] + party_types, key="benford_type")
            if selected_type != "Select a population":
                population = benford_data[benford_data["_Party Type"] == selected_type]
                valid_population = population[population["_Valid Amount"] & population["First Digit"].notna()]
                sample_size = len(valid_population)
                counts = valid_population["First Digit"].value_counts().to_dict()
                actual = {digit: counts.get(digit, 0) / sample_size if sample_size else 0 for digit in BENFORD_EXPECTED}
                deviation = {digit: actual[digit] - BENFORD_EXPECTED[digit] for digit in BENFORD_EXPECTED}
                st.metric(f"Total {selected_type.lower()} population", f"{sample_size:,}")
                st.caption(f"Based on {sample_size:,} valid account balances from the imported Trial Balance.")
                distribution = pd.DataFrame([{
                    "Digit": digit,
                    "Benford Rule %": BENFORD_EXPECTED[digit] * 100,
                    "Actual {0} %".format(selected_type): actual[digit] * 100,
                    "Difference %": deviation[digit] * 100,
                    "Account Count": counts.get(digit, 0),
                } for digit in BENFORD_EXPECTED])
                st.subheader("Benford's Law Rules and Population Distribution")
                st.dataframe(distribution, use_container_width=True, hide_index=True)
                if PLOTLY_OK:
                    chart = distribution[["Digit", "Benford Rule %", "Actual {0} %".format(selected_type)]].melt("Digit", var_name="Distribution", value_name="Percentage")
                    st.plotly_chart(px.bar(chart, x="Digit", y="Percentage", color="Distribution", barmode="group", title=f"{selected_type} Population: Benford Rule vs Actual"), use_container_width=True)

if "tb" in st.session_state:
    st.session_state["analysis"] = analyze(st.session_state["tb"], materiality)

with tab_dashboard:
    if "analysis" not in st.session_state:
        st.warning("Upload a TB first.")
    else:
        df = st.session_state["analysis"]
        high = int((df["Risk"] == "High").sum())
        med = int((df["Risk"] == "Medium").sum())
        low = int((df["Risk"] == "Low").sum())
        new = int(df["New Current Balance"].sum())
        movement = int(df["Significant Movement"].sum())
        neg = int(df["Negative Balance"].sum())

        c1,c2,c3,c4,c5,c6 = st.columns(6)
        c1.metric("Accounts", len(df))
        c2.metric("🔴 High Risk", high)
        c3.metric("🟠 Medium", med)
        c4.metric("🆕 New Balances", new)
        c5.metric("📈 Movement Flags", movement)
        c6.metric("⚠️ Negative", neg)

        st.subheader("Top Audit Attention")
        top = df.sort_values(["Risk Score","Absolute Balance"], ascending=[False,False]).head(15)
        st.dataframe(
            top[[
                "Code","Account Name","Group","Closing","PY Closing",
                "Movement","Movement %","Materiality %","Risk","Risk Reasons"
            ]],
            use_container_width=True, height=480
        )

        st.subheader("Group-Level Analytical Review")
        ga = group_analysis(df)
        st.dataframe(
            ga[[
                "Group","Accounts","Closing","PY_Closing","Movement",
                "Movement %","High_Risk","New_Balances","Significant_Movements"
            ]],
            use_container_width=True, height=430
        )

        if PLOTLY_OK:
            chart = ga.copy()
            chart["Absolute Closing"] = chart["Closing"].abs()
            fig = px.bar(
                chart.sort_values("Absolute Closing", ascending=False),
                x="Group", y="Absolute Closing", title="Absolute Closing Balance by Group"
            )
            fig.update_layout(xaxis_tickangle=-35)
            st.plotly_chart(fig, use_container_width=True)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.download_button(
                "📊 Download full Excel audit analysis",
                excel_bytes(df),
                "TB_Audit_Intelligence_Analysis.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col2:
            if REPORTLAB_OK:
                st.download_button(
                    "📄 Download PDF risk report",
                    pdf_bytes(df, entity, materiality),
                    "TB_Audit_Risk_Report.pdf",
                    "application/pdf"
                )
        with col3:
            st.download_button(
                "📝 Download working papers Excel",
                working_paper_excel_bytes(df, entity, materiality),
                "TB_Audit_Working_Papers.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col4:
            if REPORTLAB_OK:
                st.download_button(
                    "📄 Download working papers PDF",
                    working_paper_pdf_bytes(df, entity, materiality),
                    "TB_Audit_Working_Papers.pdf",
                    "application/pdf"
                )

with tab_accounts:
    if "analysis" not in st.session_state:
        st.warning("Upload a TB first.")
    else:
        df = st.session_state["analysis"]
        f1,f2,f3 = st.columns(3)
        with f1:
            risk = st.multiselect("Risk", ["High","Medium","Low"], default=["High","Medium","Low"])
        with f2:
            groups = st.multiselect("Group", sorted(df["Group"].unique()), default=sorted(df["Group"].unique()))
        with f3:
            search = st.text_input("Search account")

        view = df[df["Risk"].isin(risk) & df["Group"].isin(groups)].copy()
        if search:
            view = view[view["Account Name"].str.contains(search, case=False, na=False)]

        if view.empty:
            st.info("No accounts match the selected filters.")
        else:
            st.dataframe(
                view[[
                    "Code","Account Name","Closing","PY Closing","Movement",
                    "Movement %","Materiality %","Group","Risk","Audit Area"
                ]].assign(
                    _RiskScore=view["Risk Score"].to_numpy(),
                    _AbsoluteBalance=view["Absolute Balance"].to_numpy(),
                ).sort_values(
                    ["_RiskScore", "_AbsoluteBalance"], ascending=[False, False]
                ).drop(columns=["_RiskScore", "_AbsoluteBalance"]),
                use_container_width=True, height=500
            )

            selected = st.selectbox("Select account for detailed audit response", view["Account Name"].tolist())
            row = view[view["Account Name"] == selected].iloc[0]

            st.markdown(f"### {row['Account Name']}")
            a,b,c,d = st.columns(4)
            a.metric("Closing", fmt_money(row["Closing"]))
            b.metric("PY Closing", fmt_money(row["PY Closing"]))
            c.metric("Movement", fmt_money(row["Movement"]))
            d.metric("Risk", row["Risk"])

            st.markdown(f"**Audit area:** {row['Audit Area']}")
            st.markdown(f"**Group:** {row['Group']}")
            st.markdown(f"**Risk rationale:** {row['Risk Reasons']}")
            st.markdown(f"**Assertions:** {row['Assertions']}")

            st.markdown("#### Recommended audit procedures")
            for p in row["Suggested Procedures"].split("•"):
                if p.strip():
                    st.write("• " + p.strip())

            st.markdown("#### Required audit documents / evidence")
            for doc in row["Evidence Required"].split("|"):
                st.write("☐ " + doc.strip())

            st.markdown("#### Questions for the auditor")
            for q in row["Audit Questions"].split("|"):
                st.write("❓ " + q.strip())

with tab_evidence:
    if "analysis" not in st.session_state:
        st.warning("Upload a TB first.")
    elif st.session_state["analysis"].empty:
        st.info("No accounts are available for evidence planning.")
    else:
        df = st.session_state["analysis"]
        selected = st.selectbox("Select account", df["Account Name"].tolist(), key="evidence_select")
        row = df[df["Account Name"] == selected].iloc[0]

        st.markdown(f"### 🧾 Evidence Checklist — {row['Account Name']}")
        st.write(f"**Risk:** {row['Risk']} | **Audit Area:** {row['Audit Area']} | **Balance:** {fmt_money(row['Closing'])}")

        items = [x.strip() for x in row["Evidence Required"].split("|") if x.strip()]
        checks = []
        for i, item in enumerate(items):
            checks.append(st.checkbox(item, key=f"ev_{selected}_{i}"))

        complete = (sum(checks) / len(checks) * 100) if checks else 0
        st.progress(int(complete))
        st.metric("Evidence completeness", f"{complete:.0f}%")

        missing = [item for item, done in zip(items, checks) if not done]
        if missing:
            st.warning("Missing evidence: " + "; ".join(missing))
        else:
            st.success("All suggested evidence items have been marked complete.")

        finding = st.text_area(
            "Audit finding / exception",
            key=f"finding_{selected}",
            placeholder="Record the exception, if any, with enough detail for the working paper."
        )
        conclusion = st.text_area(
            "Audit conclusion",
            key=f"conclusion_{selected}",
            placeholder="Example: Based on procedures performed and evidence obtained, no material exception was identified."
        )

        st.session_state["working_paper"] = {
            "account": row["Account Name"],
            "group": row["Group"],
            "area": row["Audit Area"],
            "balance": row["Closing"],
            "risk": row["Risk"],
            "assertions": row["Assertions"],
            "reasons": row["Risk Reasons"],
            "procedures": row["Suggested Procedures"],
            "evidence": row["Evidence Required"],
            "completeness": complete,
            "finding": finding,
            "conclusion": conclusion,
        }

with tab_wp:
    if "analysis" not in st.session_state or st.session_state["analysis"].empty:
        st.info("Upload a TB first to generate group and individual working papers.")
    else:
        df = st.session_state["analysis"]
        st.subheader("Group Working Papers")
        group_names = sorted(df["Group"].dropna().unique().tolist())
        selected_group = st.selectbox("Select group for review", group_names, key="wp_group_select")
        group_df = df[df["Group"] == selected_group]
        group_summary = group_analysis(group_df).iloc[0]
        g1, g2, g3, g4 = st.columns(4)
        g1.metric("Ledger accounts", len(group_df))
        g2.metric("Closing balance", fmt_money(group_df["Closing"].sum()))
        g3.metric("Movement", fmt_money(group_df["Movement"].sum()))
        g4.metric("High-risk accounts", int((group_df["Risk"] == "High").sum()))
        st.write(f"**Assertions:** {', '.join(sorted(set(
            item.strip() for value in group_df['Assertions'] for item in str(value).split(',') if item.strip()
        )))}")
        st.write("**Group conclusion:** Document the results of procedures performed and conclude on the group balance.")
        st.download_button(
            "⬇️ Download all group and ledger working papers (Excel)",
            working_paper_excel_bytes(df, entity, materiality),
            "TB_Audit_Working_Papers.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="wp_all_excel",
        )
        if REPORTLAB_OK:
            st.download_button(
                "⬇️ Download all group and ledger working papers (PDF)",
                working_paper_pdf_bytes(df, entity, materiality),
                "TB_Audit_Working_Papers.pdf",
                "application/pdf",
                key="wp_all_pdf",
            )

        wp = st.session_state.get("working_paper")
        if not wp:
            st.info("Select an account in Evidence Planner to view its individual working paper.")
        else:
            st.subheader("Audit Working Paper")
            st.markdown(f"## {wp['area']}")
            st.write(f"**Account:** {wp['account']}")
            st.write(f"**Group:** {wp['group']}")
            st.write(f"**TB Balance:** {fmt_money(wp['balance'])}")
            st.write(f"**Risk:** {wp['risk']}")
            st.write(f"**Assertions:** {wp['assertions']}")
            st.write(f"**Risk rationale:** {wp['reasons']}")

            st.markdown("### Audit Objective")
            st.write(
                "To obtain sufficient appropriate audit evidence over the relevant assertions "
                "and determine whether the recorded balance is appropriately recognised, measured, "
                "classified and presented."
            )

            st.markdown("### Procedures")
            st.write(wp["procedures"].replace("•", "\n•"))

            st.markdown("### Evidence")
            st.write(wp["evidence"].replace("|", "\n•"))

            st.markdown("### Evidence completeness")
            st.progress(int(wp["completeness"]))
            st.write(f"{wp['completeness']:.0f}%")

            st.markdown("### Finding")
            st.write(wp["finding"] or "Not entered")

            st.markdown("### Conclusion")
            st.write(wp["conclusion"] or "Not entered")

            txt = f"""AUDIT WORKING PAPER
Entity: {entity}
Date: {datetime.now().strftime('%d-%b-%Y')}

Audit Area: {wp['area']}
Account: {wp['account']}
Group: {wp['group']}
TB Balance: {fmt_money(wp['balance'])}
Risk: {wp['risk']}
Assertions: {wp['assertions']}

Risk rationale:
{wp['reasons']}

Audit Objective:
To obtain sufficient appropriate audit evidence over the relevant assertions and determine whether the recorded balance is appropriately recognised, measured, classified and presented.

Suggested Procedures:
{wp['procedures'].replace("•", "\\n•")}

Evidence:
{wp['evidence'].replace("|", "\\n•")}

Evidence Completeness: {wp['completeness']:.0f}%

Finding:
{wp['finding'] or 'Not entered'}

Conclusion:
{wp['conclusion'] or 'Not entered'}

Prepared using TB → Audit Intelligence.
Professional judgement and engagement-specific review are required.
"""
            ind_row = df[df["Account Name"] == wp["account"]].iloc[0]
            st.download_button(
                "⬇️ Download Individual Working Paper (Excel)",
                individual_working_paper_excel_bytes(ind_row, entity),
                "Individual_Audit_Working_Paper.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="wp_individual_excel",
            )
            st.download_button("⬇️ Download Working Paper (Text)", txt.encode(), "Audit_Working_Paper.txt", "text/plain")

with tab_journey:
    st.subheader("🧊 Audit Journey")
    st.caption("Choose a visual format to present how the application converts the TB into an audit response.")
    steps = [
        "1. Import TB",
        "2. Validate structure",
        "3. Compare Closing vs PY Closing",
        "4. Identify material/significant movements",
        "5. Detect new and negative balances",
        "6. Detect account/group classification signals",
        "7. Assign audit risk",
        "8. Map assertions",
        "9. Recommend audit procedures",
        "10. Generate evidence checklist",
        "11. Document finding & conclusion",
        "12. Export working paper/report",
    ]

    journey_view = st.selectbox(
        "Journey chart type",
        ["Horizontal process flow", "Vertical process flow", "Sankey flow", "Stage funnel"],
        key="journey_chart_type",
    )

    if PLOTLY_OK:
        labels = [step.split(". ", 1)[1] for step in steps]
        if journey_view == "Horizontal process flow":
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=list(range(len(labels))), y=[0] * len(labels), mode="lines+markers+text",
                text=labels, textposition="top center", line=dict(color="#2563eb", width=4),
                marker=dict(size=18, color="#0f766e", line=dict(width=2, color="white")),
            ))
            fig.update_layout(height=430, xaxis=dict(visible=False), yaxis=dict(visible=False),
                              margin=dict(l=20, r=20, t=45, b=20), title="Audit process from import to reporting")
        elif journey_view == "Vertical process flow":
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=[0] * len(labels), y=list(range(len(labels))), mode="lines+markers+text",
                text=labels, textposition="middle right", line=dict(color="#2563eb", width=4),
                marker=dict(size=18, color="#0f766e", line=dict(width=2, color="white")),
            ))
            fig.update_layout(height=650, xaxis=dict(visible=False), yaxis=dict(visible=False),
                              margin=dict(l=20, r=180, t=45, b=20), title="Audit process sequence")
        elif journey_view == "Sankey flow":
            sources = list(range(len(labels) - 1))
            targets = list(range(1, len(labels)))
            fig = go.Figure(go.Sankey(
                arrangement="fixed",
                node=dict(label=labels, pad=18, thickness=18, color="#0f766e"),
                link=dict(source=sources, target=targets, value=[1] * len(sources), color="#93c5fd"),
            ))
            fig.update_layout(height=560, margin=dict(l=10, r=10, t=45, b=10), title="Audit workflow hand-offs")
        else:
            fig = go.Figure(go.Funnel(
                y=labels, x=list(range(len(labels), 0, -1)),
                textinfo="label+value", marker=dict(color="#0f766e"),
            ))
            fig.update_layout(height=560, margin=dict(l=20, r=20, t=45, b=20), title="Audit workflow stages")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Plotly is unavailable. The audit journey is shown as a sequential flow.")
        for index, step in enumerate(steps, start=1):
            st.write(f"{index}. {step.split('. ', 1)[1]}")

st.divider()
st.caption(
    "TB → Audit Intelligence & Documentation | Tailored to Testing TB.xlsx | "
    "Audit-assistance prototype — not a substitute for professional judgement or applicable auditing standards."
)
