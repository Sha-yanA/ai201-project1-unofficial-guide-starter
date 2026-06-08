"""
Gradio web interface for The Unofficial Guide to UF Campus Dining.

Wires together embed.retrieve() → generate.ask() → formatted UI output.

Run:
    python app.py
Then open http://localhost:7860
"""

import gradio as gr

from generate import ask

# ── Example questions drawn from the evaluation plan ────────────────────────
EXAMPLE_QUESTIONS = [
    "What do students say about food quality at Gator Corner compared to Broward?",
    "Are there vegan options at UF dining halls?",
    "How much does a UF meal plan cost and is it worth buying?",
    "What food options are available at the Reitz Union?",
    "Where can UF students find food after midnight?",
]

DOC_TYPE_LABELS = {
    "review": "Review",
    "article": "Article",
    "reddit": "Reddit",
}

HEADER_HTML = """
<div style="padding: 16px 0 8px 0;">
  <h1 style="margin: 0; font-size: 1.75rem; font-weight: 700;">
    🐊 The Unofficial Guide to UF Campus Dining
  </h1>
  <p style="margin: 6px 0 0 0; color: #555; font-size: 0.95rem;">
    Answers grounded in student reviews, Reddit threads, and campus journalism —
    never invented by the AI.
  </p>
</div>
"""

NO_ANSWER_HTML = """
<div style="padding: 14px 16px; border-radius: 8px; background: #fff8e1;
            border-left: 4px solid #f9a825; color: #5d4037; font-size: 0.95rem;">
  ⚠️ I don't have enough information in my sources to answer that question.
  Try rephrasing or ask about a specific dining hall, meal plan, or campus location.
</div>
"""


def _render_sources(sources: list[dict]) -> str:
    if not sources:
        return ""

    rows = ""
    for s in sources:
        label = DOC_TYPE_LABELS.get(s["doc_type"], s["doc_type"].title())
        rows += f"""
        <tr>
          <td style="padding: 6px 12px 6px 0; white-space: nowrap;">
            <span style="display: inline-block; padding: 2px 8px; border-radius: 12px;
                         font-size: 0.75rem; font-weight: 600; background: #e3f2fd;
                         color: #1565c0;">{label}</span>
          </td>
          <td style="padding: 6px 12px 6px 0; font-weight: 500;">{s['source']}</td>
          <td style="padding: 6px 0; color: #555;">{s['location']}</td>
          <td style="padding: 6px 0 6px 16px; text-align: right;">
            <a href="{s['url']}" target="_blank"
               style="color: #1976d2; text-decoration: none; font-size: 0.85rem;">
              View source ↗
            </a>
          </td>
        </tr>"""

    return f"""
<div style="margin-top: 4px;">
  <p style="margin: 0 0 8px 0; font-size: 0.8rem; font-weight: 600;
             text-transform: uppercase; letter-spacing: 0.05em; color: #777;">
    Retrieved from
  </p>
  <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
    {rows}
  </table>
</div>"""


def _handle_query(question: str):
    question = question.strip()
    if not question:
        yield (
            "<div style='color: #888; padding: 12px;'>Enter a question above.</div>",
            "",
        )
        return

    # Show a loading state immediately
    yield (
        "<div style='color: #888; padding: 12px;'>Searching sources…</div>",
        "",
    )

    result = ask(question)
    answer = result["answer"]
    sources = result["sources"]

    not_enough = answer.lower().startswith("i don't have enough information")

    if not_enough:
        answer_html = NO_ANSWER_HTML
    else:
        safe = (
            answer.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )
        # Programmatically append filenames in parentheses — never from LLM output
        filenames = ", ".join(s["filename"] for s in sources)
        citation_line = (
            f'<p style="margin: 12px 0 0 0; font-size: 0.8rem; color: #888;">({filenames})</p>'
            if filenames else ""
        )
        answer_html = f"""
<div style="padding: 16px 20px; border-radius: 8px; background: #f8f9fa;
            border-left: 4px solid #1976d2; line-height: 1.65; font-size: 0.97rem;">
  {safe}
  {citation_line}
</div>"""

    sources_html = _render_sources(sources)
    yield (answer_html, sources_html)


# ── Layout ───────────────────────────────────────────────────────────────────

_THEME = gr.themes.Default(
    primary_hue="blue",
    neutral_hue="gray",
    font=gr.themes.GoogleFont("Inter"),
)

_CSS = """
    #question-box textarea { font-size: 1rem; }
    #ask-btn { min-width: 90px; }
    footer { display: none !important; }
"""

with gr.Blocks(title="Unofficial Guide — UF Campus Dining") as demo:

    gr.HTML(HEADER_HTML)

    with gr.Row():
        with gr.Column(scale=5):
            question_box = gr.Textbox(
                label="Your question",
                placeholder="e.g. Is the UF meal plan worth buying?",
                lines=2,
                elem_id="question-box",
            )
        with gr.Column(scale=1, min_width=100):
            ask_btn = gr.Button("Ask", variant="primary", elem_id="ask-btn")

    gr.Examples(
        examples=EXAMPLE_QUESTIONS,
        inputs=question_box,
        label="Example questions",
    )

    answer_out = gr.HTML(label="Answer")
    sources_out = gr.HTML(label="Sources")

    # Wire up both button click and Enter-key submit
    ask_btn.click(
        fn=_handle_query,
        inputs=question_box,
        outputs=[answer_out, sources_out],
    )
    question_box.submit(
        fn=_handle_query,
        inputs=question_box,
        outputs=[answer_out, sources_out],
    )

    gr.HTML(
        "<p style='margin-top: 24px; color: #aaa; font-size: 0.8rem; text-align: center;'>"
        "Answers are grounded in 12 student sources collected for AI201 Project 1. "
        "The system will decline to answer questions not covered by those sources."
        "</p>"
    )

if __name__ == "__main__":
    demo.launch(theme=_THEME, css=_CSS)
