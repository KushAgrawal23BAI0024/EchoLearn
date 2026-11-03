import os
import streamlit as st
import requests
import time
from pathlib import Path
from streamlit.components.v1 import html
from playwright.sync_api import sync_playwright
import reportlab

import io
import re
from xml.sax.saxutils import escape

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    HRFlowable,
)

# Optional concept graph component
try:
    from frontend.components.concept_graph import render_graph
except Exception:
    render_graph = None


# ---------------- API ---------------- #

API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

# ---------------- API Helpers ---------------- #

def ask_chat(question, context):
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json={
                "question": question,
                "transcript": context,
            },
            timeout=600,
        )

        if response.status_code == 200:
            return response.json()["answer"]

        return "Chat failed."

    except Exception as e:
        return str(e)


def create_pdf(title, content):
    """Convert text or Markdown content into a formatted PDF."""

    buffer = io.BytesIO()

    # Register Unicode-compatible fonts
    font_dir = os.path.join(
        os.path.dirname(reportlab.__file__),
        "fonts"
    )

    pdfmetrics.registerFont(
        TTFont("Vera", os.path.join(font_dir, "Vera.ttf"))
    )

    pdfmetrics.registerFont(
        TTFont("Vera-Bold", os.path.join(font_dir, "VeraBd.ttf"))
    )

    pdfmetrics.registerFontFamily(
        "Vera",
        normal="Vera",
        bold="Vera-Bold",
        italic="Vera",
        boldItalic="Vera-Bold",
    )

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=22 * mm,
        bottomMargin=20 * mm,
        title=title,
        author="EchoLearn",
    )

    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="PDFTitle",
        parent=styles["Title"],
        fontSize=22,
        leading=28,
        textColor=colors.HexColor("#34316F"),
        alignment=TA_CENTER,
        spaceAfter=18,
    ))

    styles.add(ParagraphStyle(
        name="PDFHeading1",
        parent=styles["Heading1"],
        fontSize=17,
        leading=22,
        textColor=colors.HexColor("#34316F"),
        spaceBefore=16,
        spaceAfter=9,
    ))

    styles.add(ParagraphStyle(
        name="PDFHeading2",
        parent=styles["Heading2"],
        fontSize=14,
        leading=19,
        textColor=colors.HexColor("#514B91"),
        spaceBefore=12,
        spaceAfter=7,
    ))

    styles.add(ParagraphStyle(
        name="PDFHeading3",
        parent=styles["Heading3"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#34316F"),
        spaceBefore=9,
        spaceAfter=5,
    ))

    story = [Paragraph(escape(title), styles["PDFTitle"])]

    for line in str(content).splitlines():

        line = line.strip()

        # Normalize special Unicode hyphens and dashes
        line = (
            line.replace("\u2010", "-")
                .replace("\u2011", "-")
                .replace("\u2012", "-")
                .replace("\u2013", "-")
                .replace("\u2014", "-")
                .replace("\u2212", "-")
        )

        if not line:
            story.append(Spacer(1, 5))
            continue

        if line == "---":
            story.append(HRFlowable(
                width="100%",
                color=colors.lightgrey,
                spaceBefore=6,
                spaceAfter=6,
            ))
            continue

        # Convert Markdown headings
        heading_match = re.match(r"^(#{1,3})\s+(.*)", line)

        if heading_match:
            level = len(heading_match.group(1))
            heading_text = escape(heading_match.group(2))

            style = {
                1: styles["PDFHeading1"],
                2: styles["PDFHeading2"],
                3: styles["PDFHeading3"],
            }[level]

            story.append(Paragraph(heading_text, style))
            continue

        # Convert inline Markdown formatting
        line = escape(line)
        line = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", line)
        line = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", line)
        line = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", line)

        # Bullet points
        if re.match(r"^[-*]\s+", line):
            bullet_text = re.sub(r"^[-*]\s+", "", line)
            story.append(Paragraph(
                "•  " + bullet_text,
                styles["BodyText"],
            ))
            story.append(Spacer(1, 3))
            continue

        # Numbered points
        if re.match(r"^\d+\.\s+", line):
            story.append(Paragraph(line, styles["BodyText"]))
            story.append(Spacer(1, 3))
            continue

        story.append(Paragraph(line, styles["BodyText"]))
        story.append(Spacer(1, 5))

    def add_page_number(canvas, document):
        canvas.saveState()
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(
            A4[0] / 2,
            10 * mm,
            f"EchoLearn | Page {document.page}",
        )
        canvas.restoreState()

    doc.build(
        story,
        onFirstPage=add_page_number,
        onLaterPages=add_page_number,
    )

    buffer.seek(0)
    return buffer.getvalue()

def create_graph_pdf(graph_path):

    with sync_playwright() as p:

        browser = p.chromium.launch(headless=True)

        page = browser.new_page(
            viewport={"width": 1600, "height": 1000},
            device_scale_factor=2
        )

        page.goto(
            Path(graph_path).resolve().as_uri(),
            wait_until="networkidle"
        )

        page.wait_for_timeout(2000)

        graph_image = page.screenshot(
            full_page=True,
            type="png"
        )

        browser.close()

    buffer = io.BytesIO()

    pdf = SimpleDocTemplate(
        buffer,
        pagesize=(A4[1], A4[0]),
        rightMargin=10 * mm,
        leftMargin=10 * mm,
        topMargin=10 * mm,
        bottomMargin=10 * mm
    )

    graph_picture = reportlab.platypus.Image(
        io.BytesIO(graph_image)
    )

    graph_picture._restrictSize(
        pdf.width,
        pdf.height - 55
    )

    pdf.build([
        Paragraph(
            "EchoLearn Concept Graph",
            getSampleStyleSheet()["Title"]
        ),
        Spacer(1, 10),
        graph_picture
    ])

    buffer.seek(0)

    return buffer.getvalue()

# ---------------- Page ---------------- #

st.set_page_config(
    page_title="EchoLearn",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------- Session ---------------- #

defaults = {
    "study_package": None,
    "transcript_data": None,
    "show_transcript": False,
    "chat_history": [],
    "audio_quiz_questions": [],
    "study_quiz_checked": {},
    "study_quiz_answers": {},
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ---------------- CSS ---------------- #

css_path = Path(__file__).parent / "styles" / "main.css"

if css_path.exists():
    with open(css_path, encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True,
        )



# ---------------- Sidebar ---------------- #

with st.sidebar:

    st.markdown("## 🎓 EchoLearn")
    st.caption("AI-Powered Universal Study Platform")

    st.markdown("---")

    st.markdown("### 🧠 Platform Features")

    features = [
        ("📝", "Smart Notes"),
        ("🧠", "Interactive Flashcards"),
        ("❓", "AI Quiz Generator"),
        ("💬", "AI Tutor"),
        ("🕸️", "Concept Graph"),
        ("🏷️", "Key Terms Extraction"),
        ("📊", "Learning Insights"),
        ("🎙️", "Audio & Video Transcription"),
        ("📄", "Document Processing"),
    ]

    for icon, feature in features:
        st.markdown(f"{icon}  {feature}")

    st.markdown("---")

    st.markdown("### ⚙️ How It Works")

    st.markdown(
        """
        1. Upload your study material.
        2. Let the AI process the content.
        3. Generate notes, quizzes and flashcards.
        4. Explore concepts and ask the AI Tutor.
        """
    )

    st.markdown("---")

    st.markdown("### 📡 System Status")

    if st.session_state.study_package is not None:
        st.success("Study package generated")
    elif st.session_state.transcript_data is not None:
        st.success("Transcription completed")
    else:
        st.info("Waiting for study material")

    st.markdown("---")

    st.markdown("### 👨‍💻 Developer")
    st.markdown("**Kush Agrawal**")
    st.markdown(
        "[✉️ Contact Developer](mailto:kushagr6705@gmail.com)"
    )

    st.caption("EchoLearn | AI Learning Platform")


# ---------------- Hero ---------------- #

st.markdown(
    """
<div style="padding: 20px 0 35px 0;">
<div style="color: #8B83FF; font-size: 13px; font-weight: 700; letter-spacing: 3px; margin-bottom: 18px;">
AI-POWERED LEARNING PLATFORM
</div>

<div style="font-size: 3.5rem; font-weight: 800; letter-spacing: -2px; color: white; margin-bottom: 15px;">
🎓 EchoLearn
</div>

<div style="max-width: 850px; font-size: 19px; line-height: 1.7; color: #B8C4E2;">
Turn your lectures, documents and presentations into an interactive learning experience with AI-generated notes, flashcards, quizzes and personalised explanations.
</div>
</div>
""",
    unsafe_allow_html=True,
)

# ---------------- Upload ---------------- #


st.markdown("## 📂 Upload Your Study Material")
st.caption("Upload a lecture, document, presentation or recording to begin your learning session.")

uploaded_file = st.file_uploader(
    "Upload",
    type=[
        "mp3", "wav", "m4a", "aac", "flac", "ogg",
        "mp4", "mov", "avi", "mkv", "webm",
        "pdf",
        "docx",
        "pptx",
        "png", "jpg", "jpeg", "bmp", "tiff",
        "txt", "md"
    ],
    label_visibility="collapsed",
)

if uploaded_file:

    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)

    file_path = upload_dir / uploaded_file.name

    file_path.write_bytes(uploaded_file.getbuffer())

    st.success(f"Uploaded: {uploaded_file.name}")

    if st.button("🚀 Process Material"):

        st.session_state.study_package = None
        st.session_state.transcript_data = None
        st.session_state.chat_history = []
        st.session_state.show_transcript = False
        st.session_state.audio_quiz_questions = []
        st.session_state.study_quiz_checked = {}
        st.session_state.study_quiz_answers = {}

        for key in list(st.session_state.keys()):
            if key.startswith("audio_correct_"):
                del st.session_state[key]

        progress = st.progress(0)
        status = st.empty()

        try:

            status.info("📤 Uploading your material...")

            # Step 1: Upload file and receive job ID
            with open(file_path, "rb") as material:

                response = requests.post(
                    f"{API_URL}/upload",
                    files={"file": material},
                    timeout=120,
                )

            if response.status_code != 200:
                raise Exception(
                    response.text
                )

            upload_data = response.json()

            if "error" in upload_data:
                raise Exception(upload_data["error"])

            job_id = upload_data.get("job_id")

            if not job_id:
                raise Exception("Backend did not return a processing job ID.")

            # Step 2: Monitor actual backend progress
            status.info("🤖 AI is analyzing your material...")

            processing_start = time.time()

            while True:

                progress_response = requests.get(
                    f"{API_URL}/progress/{job_id}",
                    timeout=30,
                )

                progress_response.raise_for_status()

                progress_data = progress_response.json()

                current_progress = int(
                    progress_data.get("progress", 0)
                )

                progress.progress(
                    max(0, min(current_progress, 100))
                )

                status.info(
                    f"🤖 {progress_data.get('message', 'Processing...')}"
                )

                job_status = progress_data.get("status")

                if job_status == "completed":
                    break

                if job_status == "error":
                    raise Exception(
                        progress_data.get(
                            "error",
                            "Processing failed."
                        )
                    )

                if time.time() - processing_start > 3600:
                    raise TimeoutError(
                        "Processing took too long. Please try again."
                    )

                time.sleep(0.5)

            # Step 3: Retrieve completed study package
            result_response = requests.get(
                f"{API_URL}/result/{job_id}",
                timeout=3600,
            )

            result_response.raise_for_status()

            data = result_response.json()

            if "summary" in data:

                st.session_state.study_package = data

                # Audio and video also contain transcription data
                st.session_state.transcript_data = data.get(
                    "transcript_data"
                )

                progress.progress(100)
                status.success("✅ Processing completed!")

                time.sleep(0.5)
                st.rerun()

            elif "segments" in data:

                st.session_state.transcript_data = data
                st.session_state.study_package = None

                progress.progress(100)
                status.success("✅ Transcription completed!")

                time.sleep(0.5)
                st.rerun()

            else:

                progress.empty()
                status.error("❌ Unexpected response from backend.")

        except Exception as e:

            progress.empty()
            status.error(f"❌ Error: {e}")

# ---------------- Audio / Video Transcript ---------------- #

if st.session_state.transcript_data is not None:

    data = st.session_state.transcript_data

    st.success("🎙️ Lecture Processed Successfully!")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Language</div>
                <div class="metric-value">{data.get('language', 'Unknown').upper()}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-title">Duration</div>
                <div class="metric-value">{data.get('duration', 0):.0f}s</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            """
            <div class="metric-card">
                <div class="metric-title">Status</div>
                <div class="metric-value">Ready</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    segments = data.get("segments", [])

    transcript = " ".join(
        segment["text"]
        for segment in segments
    )

    display_transcript = "\n".join(
        f"[{s['start']:.2f}-{s['end']:.2f}] {s['text']}"
        for s in segments
    )

    st.markdown("## Transcript")

    if st.button(
        "📖 Show Transcript"
        if not st.session_state.show_transcript
        else "📕 Hide Transcript"
    ):
        st.session_state.show_transcript = (
            not st.session_state.show_transcript
        )
        st.rerun()

    if st.session_state.show_transcript:

        for segment in segments:

            st.markdown(
                f"""
                <div class="transcript-card">
                    <div class="timestamp">
                        {segment['start']:.2f}s – {segment['end']:.2f}s
                    </div>

                    {segment['text']}
                </div>
                """,
                unsafe_allow_html=True,
            )

    transcript_pdf = create_pdf(
        "Lecture Transcript",
        display_transcript,
    )

    st.download_button(
        "⬇ Download Transcript (PDF)",
        data=transcript_pdf,
        file_name="EchoLearn_Transcript.pdf",
        mime="application/pdf",
    )

# ---------------- Study Workspace ---------------- #

if st.session_state.study_package is not None:

    study = st.session_state.study_package

    st.success("📚 Study Package Ready!")

    st.markdown("---")

    tabs = st.tabs([
        "📚 Notes",
        "🧠 Flashcards",
        "❓ Quiz",
        "🕸 Concept Graph",
        "🏷 Key Terms",
        "📊 Insights",
        "💬 AI Tutor",
    ])

    # ---------- Notes ---------- #

    with tabs[0]:

        st.markdown(study["summary"])

        notes_pdf = create_pdf(
            "AI Lecture Notes",
            study["summary"],
        )

        st.download_button(
            "⬇ Download Notes (PDF)",
            data=notes_pdf,
            file_name="EchoLearn_AI_Notes.pdf",
            mime="application/pdf",
        )

    # ---------- Flashcards ---------- #

    with tabs[1]:

        if "flashcard_index" not in st.session_state:
            st.session_state.flashcard_index = 0

        if "show_flashcard_answer" not in st.session_state:
            st.session_state.show_flashcard_answer = False

        flashcards = study["flashcards"]
        total_cards = len(flashcards)

        if flashcards:
            flashcard_content = ""

            for i, card in enumerate(flashcards, 1):
                flashcard_content += (
                    f"## Flashcard {i}\n\n"
                    f"**Question:** {card['question']}\n\n"
                    f"**Answer:** {card['answer']}\n\n"
                    "---\n\n"
                )

            flashcards_pdf = create_pdf(
                "EchoLearn Flashcards",
                flashcard_content,
            )

            st.download_button(
                "⬇ Download Flashcards (PDF)",
                data=flashcards_pdf,
                file_name="EchoLearn_Flashcards.pdf",
                mime="application/pdf",
            )

        if total_cards > 0:

            index = st.session_state.flashcard_index
            card = flashcards[index]

            st.markdown(
                f"### Flashcard {index + 1} of {total_cards}"
            )

            if st.session_state.show_flashcard_answer:

                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, #183D3A, #24665A);
                        border-radius: 18px;
                        padding: 40px 25px;
                        min-height: 200px;
                        text-align: center;
                        color: white;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                    ">
                        <h3>ANSWER</h3>
                        <p>{card['answer']}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            else:

                st.markdown(
                    f"""
                    <div style="
                        background: linear-gradient(135deg, #252B49, #353B68);
                        border-radius: 18px;
                        padding: 40px 25px;
                        min-height: 200px;
                        text-align: center;
                        color: white;
                        display: flex;
                        flex-direction: column;
                        justify-content: center;
                    ">
                        <h3>QUESTION</h3>
                        <p>{card['question']}</p>
                        <small>Reveal the answer below</small>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            if st.button("🔄 Flip Card", use_container_width=True):
                st.session_state.show_flashcard_answer = (
                    not st.session_state.show_flashcard_answer
                )
                st.rerun()

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "⬅ Previous",
                    use_container_width=True,
                    disabled=index == 0
                ):
                    st.session_state.flashcard_index -= 1
                    st.session_state.show_flashcard_answer = False
                    st.rerun()

            with col2:
                if st.button(
                    "Next ➡",
                    use_container_width=True,
                    disabled=index == total_cards - 1
                ):
                    st.session_state.flashcard_index += 1
                    st.session_state.show_flashcard_answer = False
                    st.rerun()

        else:
            st.info("No flashcards available.")

    # ---------- Quiz ---------- #

    with tabs[2]:

        if study["quiz"]:
            quiz_content = ""

            for i, q in enumerate(study["quiz"], 1):
                quiz_content += f"## Question {i}\n\n"
                quiz_content += f"{q['question']}\n\n"

                for j, option in enumerate(q["options"]):
                    letter = chr(65 + j)
                    quiz_content += f"**{letter}.** {option}\n\n"

                correct_answer = q["answer"]
                quiz_content += (
                    f"**Correct Answer: {correct_answer}**\n\n"
                    "---\n\n"
                )

            quiz_pdf = create_pdf(
                "EchoLearn Quiz",
                quiz_content,
            )

            st.download_button(
                "⬇ Download Quiz (PDF)",
                data=quiz_pdf,
                file_name="EchoLearn_Quiz.pdf",
                mime="application/pdf",
            )

        for i, q in enumerate(study["quiz"]):

            st.markdown(f"### Question {i+1}")

            selected = st.radio(
                q["question"],
                q["options"],
                index=None,
                key=f"study_quiz_{i}",
            )

            if st.button(
                f"Check Answer {i+1}",
                key=f"study_check_{i}",
            ):

                if selected is None:

                    st.warning("Please select an option first.")

                else:

                    correct = q["options"][
                        ord(q["answer"]) - ord("A")
                    ]

                    st.session_state.study_quiz_checked[i] = (
                        selected == correct
                    )

                    st.session_state.study_quiz_answers[i] = selected

            if i in st.session_state.study_quiz_checked:

                if st.session_state.study_quiz_checked[i]:

                    st.success("✅ Correct!")

                else:

                    st.error("❌ Wrong!")

            st.markdown("---")

        score = sum(
            st.session_state.study_quiz_checked.values()
        )

        st.info(
            f"Score: {score}/{len(study['quiz'])}"
        )

        if st.button(
            "🔄 Retake Quiz",
            key="study_retake",
        ):

            st.session_state.study_quiz_checked = {}
            st.session_state.study_quiz_answers = {}

            for i in range(len(study["quiz"])):

                key = f"study_quiz_{i}"

                if key in st.session_state:

                    del st.session_state[key]

            st.rerun()

    # ---------- Concept Graph ---------- #

    with tabs[3]:

        graph = study.get("concept_graph", {})

        if graph.get("nodes"):

            if render_graph is not None:

                try:

                    graph_path = render_graph(graph)

                    with open(graph_path, encoding="utf-8") as f:
                        html(
                            f.read(),
                            height=620,
                        )

                    if st.button("Prepare Concept Graph PDF"):

                        with st.spinner("Generating Concept Graph PDF..."):

                            st.session_state["concept_graph_pdf"] = (
                                create_graph_pdf(graph_path)
                            )

                    if "concept_graph_pdf" in st.session_state:

                        st.download_button(
                            "⬇ Download Concept Graph (PDF)",
                            data=st.session_state["concept_graph_pdf"],
                            file_name="EchoLearn_Concept_Graph.pdf",
                            mime="application/pdf",
                        )                        

                except Exception as e:

                    st.error(f"Concept Graph rendering failed: {str(e)}")
                    st.json(graph)

            else:

                st.json(graph)

        else:

            st.info("No concept graph available.")

    # ---------- Key Terms ---------- #

    with tabs[4]:

        if study["key_terms"]:
            key_terms_content = "# Extracted Key Terms\n\n"

            for i, term in enumerate(study["key_terms"], 1):
                key_terms_content += f"{i}. {term}\n\n"

            key_terms_pdf = create_pdf(
                "EchoLearn Key Terms",
                key_terms_content,
            )

            st.download_button(
                "⬇ Download Key Terms (PDF)",
                data=key_terms_pdf,
                file_name="EchoLearn_Key_Terms.pdf",
                mime="application/pdf",
            )

        cols = st.columns(2)

        for i, term in enumerate(study["key_terms"]):

            with cols[i % 2]:

                st.markdown(
                    f"""
<div style="
padding:12px;
border-radius:12px;
background:#1f2937;
margin-bottom:8px;
text-align:center;
">
<b>{term}</b>
</div>
""",
                    unsafe_allow_html=True,
                )

    # ---------- Insights ---------- #

    with tabs[5]:

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Words",
            study["metadata"]["word_count"],
        )

        c2.metric(
            "Study Time",
            f"{study['metadata']['estimated_study_time']} min",
        )

        c3.metric(
            "Difficulty",
            study["metadata"]["difficulty"],
        )

        insights_content = f"""
## Learning Insights

**Total Words:** {study["metadata"]["word_count"]}

**Estimated Study Time:** {study["metadata"]["estimated_study_time"]} minutes

**Difficulty Level:** {study["metadata"]["difficulty"]}
"""

        insights_pdf = create_pdf(
            "EchoLearn Learning Insights",
            insights_content,
        )

        st.download_button(
            "⬇ Download Learning Insights (PDF)",
            data=insights_pdf,
            file_name="EchoLearn_Learning_Insights.pdf",
            mime="application/pdf",
        )        

        st.markdown("---")

        extracted_text = study.get("text", "")

        if extracted_text.strip():
            extracted_pdf = create_pdf(
                "EchoLearn Extracted Study Text",
                extracted_text,
            )

            st.download_button(
                "⬇ Download Extracted Text (PDF)",
                data=extracted_pdf,
                file_name="EchoLearn_Extracted_Text.pdf",
                mime="application/pdf",
            )
    # ---------- AI Tutor ---------- #

    with tabs[6]:

        question = st.text_input(
            "Ask anything about this material",
            key="study_chat",
            placeholder="Example: Explain NLP in simple words.",
        )

        if st.button(
            "🚀 Ask AI",
            key="study_chat_button",
        ):

            if question.strip():

                with st.spinner("Thinking..."):

                    answer = ask_chat(
                        question,
                        study.get("text", ""),
                    )

                    st.session_state.chat_history.append(
                        ("You", question)
                    )

                    st.session_state.chat_history.append(
                        ("EchoLearn", answer)
                    )

        for speaker, message in st.session_state.chat_history:

            with st.chat_message(
                "user"
                if speaker == "You"
                else "assistant"
            ):

                st.markdown(message)


# ---------------- AI Features ---------------- #

st.markdown("## AI Learning Suite")

st.caption(
    "Explore the intelligent tools available to transform "
    "your study material into an interactive learning experience."
)

cards = [
    (
        "📝",
        "Smart Notes",
        "Generate structured AI summaries and revision notes.",
    ),
    (
        "🧠",
        "Smart Flashcards",
        "Create interactive flashcards for effective revision.",
    ),
    (
        "❓",
        "AI Quiz Generator",
        "Test your understanding with AI-generated MCQs.",
    ),
    (
        "💬",
        "AI Tutor",
        "Ask questions and get answers based on your study material.",
    ),
    (
        "🕸️",
        "Concept Graph",
        "Visualise relationships between important concepts.",
    ),
    (
        "🏷️",
        "Key Terms",
        "Extract important academic terms from your material.",
    ),
    (
        "📊",
        "Learning Insights",
        "Explore word count, estimated study time and difficulty.",
    ),
    (
        "🎙️",
        "Audio & Video Transcription",
        "Convert lectures and recordings into readable transcripts.",
    ),
    (
        "📄",
        "Document Processing",
        "Extract learning content from PDFs, Word files and presentations.",
    ),
]

for start in range(0, len(cards), 3):

    cols = st.columns(3)

    for col, card in zip(cols, cards[start:start + 3]):

        with col:

            st.markdown(
                f"""
<div class="feature-card">
    <h2>{card[0]}</h2>
    <h4>{card[1]}</h4>
    <p>{card[2]}</p>
</div>
""",
                unsafe_allow_html=True,
            )
