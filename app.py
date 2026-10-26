"""Supplier invoice intake. Run with Streamlit on port 8502."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from invoice_intake.core import Policy, find_candidates, fingerprint, route
from invoice_intake.jev import check_invoice

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env", override=True)
st.set_page_config(page_title="Ledger Intake", page_icon="▤", layout="wide")
font = base64.b64encode((ROOT / "assets/app/host-grotesk.woff2").read_bytes()).decode()
st.html(
    "<style>@font-face{font-family:Host;src:url(data:font/woff2;base64,"
    + font
    + ") format('woff2');font-display:swap;}"
    + (ROOT / "invoice_intake/style.css").read_text()
    + "</style>"
)
samples = json.loads((ROOT / "data/invoices.json").read_text())
by_label = {sample["label"]: sample for sample in samples}


def load_invoice():
    st.session_state.invoice_text = by_label[st.session_state.invoice_pick]["text"]
    st.session_state.pop("result", None)


if "invoice_text" not in st.session_state:
    st.session_state.invoice_text = samples[0]["text"]

st.html(
    '<div class="app-header"><div class="brand">Ledger Intake</div><span>Supplier invoices</span></div>'
)
st.title("Check the amount. Keep the evidence.")
st.caption("Capture a source-backed invoice total or send it for review.")
left, right = st.columns([1.05, 1], gap="large")
with left:
    st.subheader("Invoice")
    st.selectbox("Supplier invoice", list(by_label), key="invoice_pick", on_change=load_invoice)
    text = st.text_area("Source text", key="invoice_text", height=370, max_chars=20_001)
    st.caption("Fictional suppliers. USD invoices. You can edit the extracted text.")
    key = os.getenv("TYPESAFE_API_KEY", "").strip()
    if not key:
        st.info(
            "Add TYPESAFE_API_KEY to this app's .env file to run Jev. You can inspect invoices and source values now."
        )
    if st.button("Check invoice", type="primary", disabled=not text.strip()):
        with st.spinner("Checking the source..."):
            st.session_state.result = check_invoice(
                text, api_key=key, model=os.getenv("TYPESAFE_MODEL", "jev-latest")
            )
    with st.expander("Review policy"):
        st.caption("Illustrative starting values. Validate them on your own invoices.")
        confidence = st.slider("Minimum Choice confidence", 0.0, 1.0, 0.85, 0.05)
        presence = st.slider("Minimum probability of a stated final total", 0.0, 1.0, 0.85, 0.05)
        unresolved = st.slider("Maximum probability of an unresolved amount", 0.0, 1.0, 0.15, 0.05)
        st.caption("Changing a policy reuses the current judgments. It does not call Jev again.")

with right:
    st.subheader("Amount check")
    current = st.session_state.get("result")
    if current and current.source_hash != fingerprint(text):
        st.info("The source changed. Check the invoice again to refresh its result.")
        current = None
    if current is None:
        st.html(
            '<div class="empty-results"><strong>No check yet</strong><p>Run a check to see the selected amount and the review decision.</p></div>'
        )
    else:
        decision = route(current, Policy(confidence, presence, unresolved))
        if decision.status == "Ready for draft":
            st.success(decision.status)
            st.metric("Draft invoice total", f"USD {decision.candidate.value}")
            st.code(decision.candidate.source_line, language=None)
            st.caption(
                f"Copied from source line {decision.candidate.line}. No amount was generated."
            )
            draft = {
                "currency": "USD",
                "total_due": decision.candidate.value,
                "source_text": decision.candidate.text,
                "source_line": decision.candidate.line,
                "policy": {
                    "min_confidence": confidence,
                    "min_presence": presence,
                    "max_unresolved": unresolved,
                },
                "check": current.as_dict(),
            }
            st.download_button(
                "Export checked draft",
                json.dumps(draft, indent=2),
                file_name="checked-invoice-draft.json",
                mime="application/json",
            )
        else:
            st.warning(decision.status)
        for reason in decision.reasons:
            st.write(reason)
        if current.judgment:
            answer = current.judgment
            with st.expander("Model judgments", expanded=True):
                one, two, three = st.columns(3)
                one.metric("Choice confidence", f"{answer.confidence:.2f}")
                two.metric("P(final total stated)", f"{answer.has_payable_total:.2f}")
                three.metric("P(unresolved amount)", f"{answer.unresolved_amounts:.2f}")
                selected = next((c for c in current.candidates if c.id == answer.choice), None)
                st.write("Selected source amount: " + (selected.text if selected else "None"))
                if selected:
                    st.code(selected.source_line, language=None)
                rows = [
                    {
                        "Option": c.text + f" (line {c.line})",
                        "Probability": answer.probabilities[c.id],
                    }
                    for c in current.candidates
                ]
                rows.append(
                    {"Option": "None of these", "Probability": answer.probabilities["none"]}
                )
                st.dataframe(
                    rows,
                    hide_index=True,
                    width="stretch",
                    column_config={
                        "Probability": st.column_config.ProgressColumn(
                            min_value=0, max_value=1, format="%.2f"
                        )
                    },
                )
                st.caption(
                    "Choice confidence summarizes the option distribution. It does not guarantee a correct invoice total."
                )
                st.caption(
                    "Noul values are probabilities of yes. A value near 0.5 means the model is unsure, not a medium amount."
                )
            with st.expander("Request details"):
                st.write(f"Model: {answer.model}")
                st.write(f"Request time: {current.latency_ms:,.0f} ms")
                st.write(
                    f"Tokens: {answer.input_tokens if answer.input_tokens is not None else 'unreported'} input, {answer.output_tokens if answer.output_tokens is not None else 'unreported'} output"
                )
                st.write("Cost: unavailable. This response reports tokens, not a billed amount.")
                st.json(current.as_dict())
        elif current.called_api:
            st.caption(
                "The request did not yield validated judgments. Any provider charge is unknown."
            )
    candidates = find_candidates(text) if len(text) <= 20_000 else ()
    with st.expander("Values found in the source", expanded=current is None):
        if candidates:
            st.dataframe(
                [
                    {"Amount": c.text, "Line": c.line, "Source": c.source_line}
                    for c in candidates[:40]
                ],
                hide_index=True,
                width="stretch",
            )
            if len(candidates) > 40:
                st.caption(
                    "Only the first 40 values are shown. The invoice needs review before any API call."
                )
        else:
            st.write("No supported amount found.")
st.html('<div class="app-footer">Source-backed drafts. Unresolved invoices need review.</div>')
