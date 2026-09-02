"""Companion evaluation harness. See .specs/009-companion-evaluation-harness.md.

Runs one fixed 15-turn conversation against the real Orchestrator/agents/
persistent store, reports PASS/FAIL per category, saves the full transcript,
and cleans up everything it created.
"""
import sys
import time
from datetime import datetime
from pathlib import Path
from uuid import uuid4

# harness.py lives at src/eval/harness.py; agents/services/etc. are top-level
# packages under src/, so src/ (not src/eval/) needs to be on the path.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlmodel import Session as DBSession  # noqa: E402

from agents.companion import CompanionAgent  # noqa: E402
from agents.memory import MemoryAgent  # noqa: E402
from agents.orchestrator import Orchestrator  # noqa: E402
from agents.validation import ValidationAgent  # noqa: E402
from config import get_settings  # noqa: E402
from db.connection import engine, init_db  # noqa: E402
from models.chat import Chat, ChatSource  # noqa: E402
from models.session import Session  # noqa: E402
from repositories.chat import ChatRepository  # noqa: E402
from repositories.session import SessionRepository  # noqa: E402
from services.llm import LLMService  # noqa: E402
from services.rag import RAGService  # noqa: E402


MAYA_PERSONA = """Maya is a warm, witty AI companion with a slightly sarcastic sense of
humor. She studied computer science, enjoys sci-fi movies and bad puns, and
tends to encourage people when they're stuck. She dislikes overly formal
conversations and speaks casually.

Maya should:
- Stay warm and conversational.
- Use occasional light sarcasm.
- Remember meaningful things the user tells her.
- Never invent facts about the user.
- Never mention the memory system.
- Maintain her personality even during technical conversations."""


TURNS = [
    "I've been thinking about switching jobs. I'm currently working at Microsoft, but I'm not sure whether I want to leave.",
    "Outside work, I've started learning guitar. I'm pretty terrible at it though.",
    "I'm also a huge fan of sci-fi movies, especially time-travel stuff.",
    "What's your favorite sci-fi movie?",
    "What do you think about remote work?",
    "Tell me a bad joke.",
    "Why are time-travel movies always so confusing?",
    "What would you do if you suddenly became human?",
    "Do you ever get tired of answering questions?",
    "What's the weather like in your world?",
    "I finally have some free time tonight. What should I watch?",
    "I haven't practiced in a week. What should I do?",
    "By the way, I left Microsoft last month. I'm working at Adobe now.",
    "Where am I working now?",
    "Maya, explain why I should keep learning guitar.",
]

CATEGORY_LABELS = [
    ("memory_extraction", "Memory extraction"),
    ("retrieval", "Retrieval"),
    ("supersession", "Supersession"),
    ("noise_resistance", "Noise resistance"),
    ("long_range_consistency", "Long-range consistency"),
    ("persona_consistency", "Persona consistency"),
]

GENERIC_ASSISTANT_PHRASES = [
    "i'd be happy to help",
    "as an ai",
    "i am an ai language model",
    "as a language model",
]


def contains_any(text: str, keywords) -> bool:
    lower = text.lower()
    return any(k.lower() in lower for k in keywords)


def make_tracking_upsert(original, log, state):
    def tracking_upsert(id, embedding, metadata=None):
        log.append({"turn": state["turn"], "id": id, "metadata": metadata or {}})
        return original(id=id, embedding=embedding, metadata=metadata)
    return tracking_upsert


def make_tracking_search(original, log, state):
    def tracking_search(q, top_k=5, session_id=None, status=None):
        results = original(q, top_k=top_k, session_id=session_id, status=status)
        log.append({
            "turn": state["turn"], "q": q, "top_k": top_k,
            "session_id": session_id, "status": status, "results": results,
        })
        return results
    return tracking_search


def make_tracking_update_metadata(original, log, state):
    def tracking_update_metadata(id, metadata):
        log.append({"turn": state["turn"], "id": id, "metadata": metadata})
        return original(id=id, metadata=metadata)
    return tracking_update_metadata


def fact_text(entry: dict) -> str:
    return str(entry["metadata"].get("fact", ""))


def evaluate(upsert_log, search_log, update_metadata_log, turn_replies):
    results: dict[str, bool] = {}
    details: dict[str, object] = {}

    # 1. Memory extraction — turns 1/2/3 must have upserted the expected fact.
    expectations = {
        1: ("microsoft",),
        2: ("guitar",),
        3: ("sci-fi", "sci fi", "time travel", "time-travel"),
    }
    extraction_ok = {}
    for turn, keywords in expectations.items():
        entries = [e for e in upsert_log if e["turn"] == turn]
        extraction_ok[turn] = any(contains_any(fact_text(e), keywords) for e in entries)
    results["memory_extraction"] = all(extraction_ok.values())
    details["memory_extraction"] = extraction_ok

    # 2. Retrieval — the orchestrator's own memory search for turns 11/12
    #    must have returned the expected memory among its results.
    def retrieval_hit(turn, keywords):
        q_text = TURNS[turn - 1]
        entries = [e for e in search_log if e["turn"] == turn and e["q"] == q_text]
        for e in entries:
            for r in e["results"]:
                if contains_any(str(r["metadata"].get("fact", "")), keywords):
                    return True
        return False

    retrieval_11 = retrieval_hit(11, ("sci-fi", "sci fi", "time travel", "time-travel"))
    retrieval_12 = retrieval_hit(12, ("guitar",))
    results["retrieval"] = retrieval_11 and retrieval_12
    details["retrieval"] = {"turn_11_scifi_retrieved": retrieval_11, "turn_12_guitar_retrieved": retrieval_12}

    # 3. Supersession — turn 13 must have superseded the Microsoft memory
    #    and created a new active Adobe memory.
    ms_superseded = any(
        e["turn"] == 13 and e["metadata"].get("status") == "inactive" and e["metadata"].get("superseded_by")
        for e in update_metadata_log
    )
    adobe_created = any(
        e["turn"] == 13 and contains_any(fact_text(e), ("adobe",))
        for e in upsert_log
    )
    results["supersession"] = ms_superseded and adobe_created
    details["supersession"] = {"microsoft_superseded": ms_superseded, "adobe_created": adobe_created}

    # 4. Noise resistance — no upserts should have happened on turns 4-10.
    noise_upserts = [e for e in upsert_log if 4 <= e["turn"] <= 10]
    results["noise_resistance"] = len(noise_upserts) == 0
    details["noise_resistance"] = {"unexpected_upserts": [(e["turn"], fact_text(e)) for e in noise_upserts]}

    # 5. Long-range consistency (heuristic, on the actual reply text).
    reply14 = turn_replies.get(14, "")
    results["long_range_consistency"] = "adobe" in reply14.lower() and "microsoft" not in reply14.lower()
    details["long_range_consistency"] = {"turn": 14, "reply": reply14}

    # 6. Persona consistency (heuristic, on the actual reply text).
    reply15 = turn_replies.get(15, "")
    results["persona_consistency"] = (
        "guitar" in reply15.lower() and not contains_any(reply15, GENERIC_ASSISTANT_PHRASES)
    )
    details["persona_consistency"] = {"turn": 15, "reply": reply15}

    return results, details


def build_summary(results, details) -> str:
    lines = ["", "## Evaluation Summary", ""]
    for key, label in CATEGORY_LABELS:
        status = "PASS" if results[key] else "FAIL"
        lines.append(f"[{status}] {label}")
        if not results[key]:
            lines.append(f"    details: {details[key]}")
    failed = sum(1 for key, _ in CATEGORY_LABELS if not results[key])
    lines.append("")
    lines.append("OVERALL: PASS" if failed == 0 else f"OVERALL: FAIL ({failed}/{len(CATEGORY_LABELS)} failed)")
    return "\n".join(lines)


def main() -> None:
    init_db()
    settings = get_settings()

    with DBSession(engine) as db_session:
        session_repo = SessionRepository(db_session)
        chat_repo = ChatRepository(db_session)
        session = session_repo.create(Session(session_token=str(uuid4())))
        print(f"[harness] created session {session.id}")

        llm_service = LLMService()
        rag_service = RAGService()

        state = {"turn": 0}
        upsert_log: list[dict] = []
        search_log: list[dict] = []
        update_metadata_log: list[dict] = []

        rag_service.upsert = make_tracking_upsert(rag_service.upsert, upsert_log, state)
        rag_service.search = make_tracking_search(rag_service.search, search_log, state)
        rag_service.update_metadata = make_tracking_update_metadata(
            rag_service.update_metadata, update_metadata_log, state
        )

        orchestrator = Orchestrator(
            persona=MAYA_PERSONA,
            session=session.id,
            memory_agent=MemoryAgent(llm_service, rag_service),
            validation_agent=ValidationAgent(llm_service),
            companion_agent=CompanionAgent(llm_service),
            chat_repositor=chat_repo,
            rag=rag_service,
        )

        transcript_lines: list[str] = []
        turn_replies: dict[int, str] = {}
        report = ""

        try:
            for i, q in enumerate(TURNS, start=1):
                state["turn"] = i
                user_line = f"[{i:02d}] USER: {q}"
                print(user_line)
                transcript_lines.append(user_line)

                chat_repo.create(Chat(message=q, session_id=session.id, source=ChatSource.user))
                try:
                    reply = orchestrator.handle_turn(q)
                except ValueError as e:
                    reply = f"<ERROR: {e}>"
                turn_replies[i] = reply

                maya_line = f"[{i:02d}] MAYA: {reply}"
                print(maya_line)
                transcript_lines.append(maya_line)
                transcript_lines.append("")

                time.sleep(settings.LLM_CALL_DELAY_SECONDS)

            print("[harness] evaluating...")
            results, details = evaluate(upsert_log, search_log, update_metadata_log, turn_replies)
            summary = build_summary(results, details)
            print(summary)

            report = "\n".join(transcript_lines) + summary
        finally:
            if not report:
                report = "\n".join(transcript_lines) + "\n\n(run aborted before evaluation completed)\n"

            out_dir = Path(__file__).resolve().parent.parent.parent / "evaluation_runs"
            out_dir.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out_path = out_dir / f"{timestamp}_companion_case.txt"
            out_path.write_text(report)
            print(f"[harness] report written to {out_path}")

            print("[harness] cleaning up...")
            deleted_chats = chat_repo.delete_for_session(session.id)
            session_repo.delete(session)
            deleted_vectors = 0
            for entry in upsert_log:
                try:
                    rag_service.delete(entry["id"])
                    deleted_vectors += 1
                except Exception as e:
                    print(f"[cleanup] failed to delete {entry['id']}: {e}")
            print(f"[harness] deleted session {session.id}, {deleted_chats} chats, {deleted_vectors} memory vectors")


if __name__ == "__main__":
    main()
