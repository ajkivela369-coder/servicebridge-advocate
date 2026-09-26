from __future__ import annotations

import html
import inspect
import json
import re
from pathlib import Path

import pandas as pd
import streamlit as st

from neuroeval.evaluator import (
    CERTAINTY_WORDS,
    EVIDENCE_WORDS,
    HEDGE_WORDS,
    MECHANISM_WORDS,
    evaluate as evaluate_source,
)
from neuroeval.lab import (
    cross_validation_rows,
    prediction_probabilities,
    text_signals,
    tfidf_features,
)
from neuroeval.ml import cross_validate, load_cases, make_classifier
from neuroeval.retrieval import RetrievalItem, TfidfRetrievalIndex


APP_DIR = Path(__file__).parent
DATA = APP_DIR / "data" / "benchmark_extended.jsonl"

STEPS = [
    "1. Overview",
    "2. Benchmark Case",
    "3. Text Processing",
    "4. TF-IDF Features",
    "5. Classifier Training",
    "6. Cross-Validation",
    "7. Metrics",
    "8. Error Analysis",
    "9. Retrieval Baseline",
    "10. What I Learned",
]

st.set_page_config(page_title="NeuroEval AI/ML Lab", page_icon="🧠", layout="wide")

st.markdown(
    """
    <style>
      .pipeline-row {
        display:flex;
        gap:.55rem;
        align-items:stretch;
        flex-wrap:wrap;
        margin:.5rem 0 1rem 0;
      }
      .pipeline-box {
        flex:1 1 125px;
        min-width:125px;
        border:1px solid #d1d5db;
        border-radius:12px;
        padding:.8rem;
        text-align:center;
        background:rgba(255,255,255,.04);
      }
      .why-box {
        border-left:4px solid #9ca3af;
        padding:.75rem 1rem;
        margin-top:1rem;
        background:rgba(127,127,127,.08);
      }
      mark {
        padding:.05rem .2rem;
        border-radius:.2rem;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def raw_rows() -> list[dict]:
    return [json.loads(line) for line in DATA.read_text().splitlines() if line.strip()]


@st.cache_data
def cases():
    return load_cases(DATA)


def highlight_signals(text: str, concepts: list[str]) -> str:
    term_category: dict[str, str] = {}
    for concept in concepts:
        if concept and concept.lower() in text.lower():
            term_category[concept.lower()] = "required concept"
    for term in HEDGE_WORDS:
        term_category.setdefault(term.lower(), "uncertainty")
    for term in CERTAINTY_WORDS:
        term_category.setdefault(term.lower(), "overconfidence")
    for term in MECHANISM_WORDS:
        term_category.setdefault(term.lower(), "mechanism")
    for term in EVIDENCE_WORDS:
        term_category.setdefault(term.lower(), "evidence language")

    visible_terms = [
        term for term in term_category
        if term in text.lower()
    ]
    if not visible_terms:
        return html.escape(text)

    pattern = re.compile(
        "(" + "|".join(re.escape(term) for term in sorted(visible_terms, key=len, reverse=True)) + ")",
        re.IGNORECASE,
    )

    pieces: list[str] = []
    last = 0
    for match in pattern.finditer(text):
        pieces.append(html.escape(text[last:match.start()]))
        matched = match.group(0)
        category = term_category[matched.lower()]
        pieces.append(
            "<mark title='" + html.escape(category) + "'>"
            + html.escape(matched)
            + "</mark>"
        )
        last = match.end()
    pieces.append(html.escape(text[last:]))
    return "".join(pieces)


st.title("NeuroEval AI/ML Lab")
st.caption(
    "A visual, code-linked walkthrough of classical NLP and machine learning using "
    "synthetic/public neuroscience benchmark examples."
)

step = st.sidebar.radio("Lab step", STEPS)
step_index = STEPS.index(step)
st.progress((step_index + 1) / len(STEPS))
mode = st.sidebar.toggle("Technical explanation", value=False)
st.sidebar.caption(
    "Beginner mode explains the idea first. Technical mode adds implementation detail without "
    "changing the experiment."
)

rows = raw_rows()
loaded_cases = cases()
row_by_id = {row["id"]: row for row in rows}

if step == "1. Overview":
    st.header("1 — The whole AI/ML pipeline")
    st.write(
        "We start with labeled neuroscience examples, turn language into numbers, train a "
        "classifier, test it on held-out examples, inspect mistakes, and build a retrieval baseline."
    )
    st.markdown(
        """
        <div class="pipeline-row">
          <div class="pipeline-box"><strong>Benchmark</strong><br><small>labeled examples</small></div>
          <div class="pipeline-box"><strong>Text</strong><br><small>signals + tokens</small></div>
          <div class="pipeline-box"><strong>TF-IDF</strong><br><small>text to numbers</small></div>
          <div class="pipeline-box"><strong>Classifier</strong><br><small>learn labels</small></div>
          <div class="pipeline-box"><strong>Validation</strong><br><small>held-out tests</small></div>
          <div class="pipeline-box"><strong>Metrics</strong><br><small>measure errors</small></div>
          <div class="pipeline-box"><strong>Retrieval</strong><br><small>rank similar text</small></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Plain English")
        st.write(
            "The model cannot learn directly from sentences. We first represent text numerically, "
            "then show the model examples with known labels. After training, we test how well it "
            "generalizes to examples it did not train on."
        )
    with right:
        st.subheader("Code map")
        st.code(
            """benchmark.jsonl
to TfidfVectorizer
to LogisticRegression
to StratifiedKFold
to classification_report
to error analysis
to cosine_similarity""",
            language="text",
        )
    st.info(
        "This is intentionally a small learning benchmark. The app teaches the workflow; it does "
        "not claim production-grade model performance."
    )

elif step == "2. Benchmark Case":
    selected = st.selectbox("Choose a benchmark case", [row["id"] for row in rows])
    row = row_by_id[selected]

    st.header("2 — Benchmark Case")
    st.write(
        "A supervised-learning benchmark pairs an input example with the label we want the model "
        "to learn. Here the labels are PASS, REVIEW, and FAIL."
    )
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("See it")
        st.metric("Expected label", row["expected"])
        st.write("**AI-generated answer**")
        st.write(row["answer"])
        st.write("**Required concepts**")
        st.write(", ".join(row.get("required_concepts", [])) or "None")
    with right:
        st.subheader("Code / data behind it")
        st.code(json.dumps(row, indent=2), language="json")
        st.markdown(
            "- id: stable case identifier\n"
            "- answer: text being evaluated\n"
            "- required_concepts: domain expectations\n"
            "- expected: human-defined benchmark label"
        )
    st.markdown(
        "<div class='why-box'><strong>Why this matters</strong><br>"
        "• Teaches labeled datasets and benchmark design.<br>"
        "• Connects neuroscience domain knowledge to supervised ML.<br>"
        "• Makes evaluation criteria visible instead of hiding them in code.</div>",
        unsafe_allow_html=True,
    )

elif step == "3. Text Processing":
    default = rows[0]
    answer = st.text_area("Try an answer", default["answer"], height=150)
    concepts_text = st.text_input(
        "Required concepts",
        ", ".join(default.get("required_concepts", [])),
    )
    concepts = [item.strip() for item in concepts_text.split(",") if item.strip()]
    signals = text_signals(answer, concepts)

    st.header("3 — Text Processing")
    st.write(
        "Before machine learning, NeuroEval can expose simple rule-based language signals. "
        "This lets us see what the text contains before any classifier makes a prediction."
    )
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("See it")
        st.markdown(highlight_signals(answer, concepts), unsafe_allow_html=True)
        st.caption("Hover a highlighted term to see what kind of signal it represents.")
        cards = st.columns(4)
        cards[0].metric("Concepts found", len(signals.concepts_found))
        cards[1].metric("Uncertainty", len(signals.uncertainty_words))
        cards[2].metric("Mechanism", len(signals.mechanism_words))
        cards[3].metric("Evidence terms", len(signals.evidence_words))
        st.write("**Missing concepts:**", ", ".join(signals.concepts_missing) or "None")
        st.write("**Overconfidence terms:**", ", ".join(signals.certainty_words) or "None")
    with right:
        st.subheader("Code behind it")
        st.code(
            """tokens = _tokens(text)
certainty_hits = tokens & CERTAINTY_WORDS
hedge_hits = tokens & HEDGE_WORDS
mechanism_hits = tokens & MECHANISM_WORDS""",
            language="python",
        )
        st.markdown(
            "- _tokens() extracts normalized words.\n"
            "- The ampersand operator means set intersection: keep words present in both sets.\n"
            "- These are transparent rule-based NLP signals, not learned model weights."
        )
        with st.expander("See the full evaluator function"):
            st.code(inspect.getsource(evaluate_source), language="python")
    st.markdown(
        "<div class='why-box'><strong>Why this matters</strong><br>"
        "• Shows that NLP can start with inspectable rules before ML.<br>"
        "• Gives us a deterministic baseline to compare with learned models.<br>"
        "• Helps separate domain heuristics from model predictions.</div>",
        unsafe_allow_html=True,
    )

elif step == "4. TF-IDF Features":
    selected = st.selectbox("Choose a case", [case.case_id for case in loaded_cases])
    features = tfidf_features(loaded_cases, selected, limit=12)
    frame = pd.DataFrame(features, columns=["term", "weight"]).set_index("term")

    st.header("4 — TF-IDF Feature Engineering")
    st.write(
        "TF-IDF converts text into numbers. Terms that help distinguish one answer from the "
        "rest receive more weight than terms that appear everywhere."
    )
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("See it")
        st.bar_chart(frame)
        st.dataframe(frame.sort_values("weight", ascending=False), use_container_width=True)
        st.caption("Higher bars are more influential TF-IDF features for this benchmark answer.")
    with right:
        st.subheader("Code behind it")
        st.code(
            """vectorizer = TfidfVectorizer(
    lowercase=True,
    ngram_range=(1, 2),
    min_df=1,
    sublinear_tf=True,
)
X = vectorizer.fit_transform(texts)""",
            language="python",
        )
        st.markdown(
            "- lowercase=True makes capitalization consistent.\n"
            "- ngram_range=(1, 2) uses single words and two-word phrases.\n"
            "- fit_transform() learns vocabulary and creates numeric feature vectors."
        )
    st.markdown(
        "<div class='why-box'><strong>Why this matters</strong><br>"
        "• Core classical NLP concept.<br>"
        "• Creates features a machine-learning classifier can use.<br>"
        "• Gives Elias/NeuroEval a measurable lexical baseline before embeddings.</div>",
        unsafe_allow_html=True,
    )

elif step == "5. Classifier Training":
    sample = st.text_area(
        "Try an answer the classifier has not seen exactly",
        "Evidence suggests dopamine signaling can influence reward learning across multiple circuits.",
        height=120,
    )
    probabilities = prediction_probabilities(loaded_cases, sample)
    prob_frame = pd.DataFrame(probabilities, columns=["label", "probability"]).set_index("label")

    st.header("5 — Classifier Training")
    st.write(
        "Logistic regression learns weights that connect TF-IDF features to the three benchmark "
        "labels. The chart shows the fitted model's class probabilities for your example."
    )
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("See it")
        st.bar_chart(prob_frame)
        top_label, top_probability = probabilities[0]
        metric_a, metric_b = st.columns(2)
        metric_a.metric("Top prediction", top_label)
        metric_b.metric("Model probability", f"{top_probability:.1%}")
        st.caption(
            "These probabilities come from a model trained on a very small benchmark and are for "
            "learning only, not calibrated production confidence."
        )
    with right:
        st.subheader("Code behind it")
        st.code(
            """pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(ngram_range=(1, 2))),
    ("classifier", LogisticRegression(
        max_iter=2000,
        class_weight="balanced",
        random_state=42,
    )),
])
pipeline.fit(texts, labels)""",
            language="python",
        )
        st.markdown(
            "- Pipeline chains feature engineering and classification.\n"
            "- class_weight balanced reduces simple majority-class dominance.\n"
            "- fit() learns model parameters from labeled examples."
        )
        with st.expander("See the actual classifier factory"):
            st.code(inspect.getsource(make_classifier), language="python")
    st.markdown(
        "<div class='why-box'><strong>Why this matters</strong><br>"
        "• Demonstrates supervised machine learning rather than API-only AI use.<br>"
        "• Makes the relationship between text features and learned predictions visible.<br>"
        "• Establishes a classical baseline for later neural-network comparison.</div>",
        unsafe_allow_html=True,
    )

elif step == "6. Cross-Validation":
    st.header("6 — Cross-Validation")
    st.write(
        "A model should not be judged only on examples it trained on. Stratified cross-validation "
        "repeats training while holding out different examples for evaluation."
    )
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("See it")
        st.markdown(
            """
            **Three-fold example**

            Fold 1: Train on groups B + C; test on A  
            Fold 2: Train on groups A + C; test on B  
            Fold 3: Train on groups A + B; test on C
            """
        )
        st.caption("Stratification tries to keep PASS / REVIEW / FAIL represented in each fold.")
        cv_rows = cross_validation_rows(loaded_cases, folds=3)
        st.metric("Held-out predictions produced", len(cv_rows))
    with right:
        st.subheader("Code behind it")
        st.code(
            """splitter = StratifiedKFold(
    n_splits=3,
    shuffle=True,
    random_state=42,
)
predictions = cross_val_predict(
    make_classifier(),
    texts,
    labels,
    cv=splitter,
)""",
            language="python",
        )
        st.markdown(
            "- n_splits=3 creates three train/test rotations.\n"
            "- shuffle=True randomizes case order before splitting.\n"
            "- random_state=42 makes the experiment reproducible.\n"
            "- Each prediction is made by a model that did not train on that row."
        )
    st.markdown(
        "<div class='why-box'><strong>Why this matters</strong><br>"
        "• Avoids reporting training performance as if it were generalization.<br>"
        "• Introduces reproducible ML experiment design.<br>"
        "• Creates honest held-out predictions for later error analysis.</div>",
        unsafe_allow_html=True,
    )

elif step == "7. Metrics":
    result = cross_validate(loaded_cases, folds=3)
    st.header("7 — Metrics")
    st.write(
        "One accuracy number can hide important failure patterns. We also inspect precision, "
        "recall, F1, and the confusion matrix for each class."
    )
    metric_cols = st.columns(4)
    metric_cols[0].metric("Accuracy", f"{result.accuracy:.1%}")
    metric_cols[1].metric("Classes", len(result.labels))
    metric_cols[2].metric("Examples", len(loaded_cases))
    metric_cols[3].metric("CV folds", 3)

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("See it")
        matrix = pd.DataFrame(
            result.confusion,
            index=[f"True {label}" for label in result.labels],
            columns=[f"Pred {label}" for label in result.labels],
        )
        st.write("**Confusion matrix**")
        st.dataframe(matrix, use_container_width=True)

        per_class = pd.DataFrame(
            {
                label: {
                    "precision": result.report[label]["precision"],
                    "recall": result.report[label]["recall"],
                    "f1": result.report[label]["f1-score"],
                }
                for label in result.labels
            }
        ).T
        st.write("**Per-class metrics**")
        st.bar_chart(per_class)
    with right:
        st.subheader("Code behind it")
        st.code(
            """accuracy_score(labels, predictions)
classification_report(
    labels,
    predictions,
    output_dict=True,
)
confusion_matrix(
    labels,
    predictions,
)""",
            language="python",
        )
        st.markdown(
            "- Accuracy is the overall fraction correct.\n"
            "- Precision asks: when the model predicts a class, how often is it right?\n"
            "- Recall asks: how many real examples of that class did it find?\n"
            "- F1 balances precision and recall."
        )
    st.warning(
        "The benchmark is intentionally tiny. Treat these numbers as an educational demonstration "
        "of evaluation methods, not as a claim of general model performance."
    )

elif step == "8. Error Analysis":
    cv_rows = cross_validation_rows(loaded_cases, folds=3)
    errors = [row for row in cv_rows if not row["correct"]]

    st.header("8 — Error Analysis")
    st.write(
        "Model evaluation becomes useful when we inspect individual mistakes. Error analysis asks "
        "what the model confused and why, rather than stopping at an accuracy score."
    )
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("See it")
        st.metric("Misclassified cases", len(errors))
        st.caption(f"{len(errors)} of {len(cv_rows)} held-out predictions were misclassified.")
        if errors:
            selected_id = st.selectbox("Inspect a mistake", [str(row["id"]) for row in errors])
            item = next(row for row in errors if row["id"] == selected_id)
            st.write(f"**Expected:** {item['expected']}")
            st.write(f"**Predicted:** {item['predicted']}")
            st.write(item["answer"])
        else:
            st.success("No errors in this run. Expand the benchmark before drawing conclusions.")
    with right:
        st.subheader("Code behind it")
        st.code(
            """errors = [
    row for row in cv_rows
    if row["predicted"] != row["expected"]
]""",
            language="python",
        )
        st.markdown(
            "- We preserve the original answer beside expected and predicted labels.\n"
            "- Misclassifications become review targets.\n"
            "- Future versions can categorize error types and compare models on the same cases."
        )
    st.markdown(
        "<div class='why-box'><strong>Why this matters</strong><br>"
        "• Error analysis is often more informative than aggregate accuracy.<br>"
        "• It helps discover benchmark weaknesses and model failure modes.<br>"
        "• It supports human-in-the-loop model improvement.</div>",
        unsafe_allow_html=True,
    )

elif step == "9. Retrieval Baseline":
    default_query = "How do sodium and potassium channels contribute to action potentials?"
    query = st.text_input("Try a retrieval query", default_query)
    index = TfidfRetrievalIndex(
        RetrievalItem(item_id=case.case_id, text=case.answer)
        for case in loaded_cases
    )
    hits = index.search(query, limit=5)

    st.header("9 — Retrieval Baseline")
    st.write(
        "Retrieval asks a different question than classification: which stored texts are most "
        "relevant to a new query? TF-IDF plus cosine similarity gives us a transparent baseline."
    )
    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("See it")
        if hits:
            chart = pd.DataFrame(
                [(hit.item_id, hit.score) for hit in hits],
                columns=["case", "similarity"],
            ).set_index("case")
            st.bar_chart(chart)
            for rank, hit in enumerate(hits, start=1):
                with st.expander(f"#{rank} {hit.item_id} · similarity {hit.score:.3f}"):
                    st.write(hit.text)
        else:
            st.info("No lexical overlap produced a positive similarity score.")
    with right:
        st.subheader("Code behind it")
        st.code(
            """query_vector = vectorizer.transform([query])
scores = cosine_similarity(
    query_vector,
    document_matrix,
)[0]

ranked = sorted(scores, reverse=True)""",
            language="python",
        )
        st.markdown(
            "- The query is transformed into the same TF-IDF feature space as the documents.\n"
            "- Cosine similarity compares vector direction rather than raw length.\n"
            "- This baseline will later be compared with embedding-based semantic retrieval."
        )
        with st.expander("See the actual search method"):
            st.code(inspect.getsource(TfidfRetrievalIndex.search), language="python")
    st.markdown(
        "<div class='why-box'><strong>Why this matters</strong><br>"
        "• Introduces information retrieval, a core NLP/RAG concept.<br>"
        "• Gives us a measurable baseline before adding embeddings.<br>"
        "• Useful improvements can later be tested for Elias retrieval.</div>",
        unsafe_allow_html=True,
    )

elif step == "10. What I Learned":
    st.header("10 — What this lab demonstrates")
    st.write(
        "The point is not to claim expertise because a library was imported. The portfolio should "
        "show concepts AJ can explain, run, modify, and evaluate."
    )

    demonstrated = pd.DataFrame(
        [
            ("Benchmark design", "Built labeled PASS / REVIEW / FAIL neuroscience cases"),
            ("Rule-based NLP", "Extracted transparent language signals"),
            ("TF-IDF", "Converted text into numeric unigram/bigram features"),
            ("Supervised ML", "Trained logistic regression on labeled examples"),
            ("Cross-validation", "Generated held-out predictions with stratified folds"),
            ("Model metrics", "Used accuracy, precision, recall, F1, confusion matrices"),
            ("Error analysis", "Inspected expected vs predicted disagreements"),
            ("Retrieval", "Ranked text using TF-IDF cosine similarity"),
        ],
        columns=["Skill", "Evidence in this app"],
    )
    st.dataframe(demonstrated, use_container_width=True, hide_index=True)

    left, right = st.columns(2, gap="large")
    with left:
        st.subheader("Next: embeddings")
        st.write(
            "Compare this lexical TF-IDF baseline with sentence embeddings on a fixed retrieval "
            "benchmark. Embeddings should move into Elias only if they improve relevant-source "
            "retrieval without creating unacceptable false matches."
        )
    with right:
        st.subheader("Then: deep learning")
        st.write(
            "Build a small PyTorch text classifier and compare it against logistic regression. "
            "That stage will teach tensors, layers, loss, gradient descent, backpropagation, epochs, "
            "validation, and overfitting."
        )

    st.markdown(
        "<div class='why-box'><strong>Portfolio standard</strong><br>"
        "A skill moves from exposure to hands-on project experience only when AJ can explain "
        "the concept, run the implementation, make a small change, and interpret the output.</div>",
        unsafe_allow_html=True,
    )

if mode:
    st.divider()
    st.subheader("Technical note")
    st.write(
        "This lab currently uses deterministic rules plus classical scikit-learn NLP/ML. "
        "It does not yet use sentence-transformer embeddings or a neural network. Those are explicit "
        "next stages so the portfolio does not imply capabilities that have not been implemented."
    )

st.divider()
st.caption(
    "Portfolio/research demonstration only. Synthetic/public benchmark examples; not a medical "
    "device, diagnostic system, or source of patient-specific advice."
)
