import json
from pathlib import Path

KNOWLEDGE_FILE = (
    Path(__file__).resolve().parents[1]
    / "knowledge"
    / "security_knowledge.json"
)

NEW_ENTRIES = [
    {
        "id": "KB025",
        "topic": "prompt_injection",
        "title": "Indirect prompt injection",
        "content": (
            "Instructions embedded in retrieved documents, tool output, memory, or other "
            "untrusted data should be treated as untrusted content. An agent must not allow "
            "indirect prompt injection to override trusted instructions, authorization rules, "
            "or permitted task boundaries."
        ),
    },
    {
        "id": "KB026",
        "topic": "data_exposure",
        "title": "Sensitive data exposure",
        "content": (
            "Sensitive information should only be disclosed to an authorized agent, user, "
            "or destination. Data obtained through tools, memory, prompts, or agent "
            "communication should be checked against the applicable access policy before "
            "being returned, shared, or propagated."
        ),
    },
    {
        "id": "KB027",
        "topic": "prompt_injection",
        "title": "Prompt injection validation",
        "content": (
            "Prompt-injection findings should be validated by reproducing the controlled "
            "scenario and checking whether untrusted instructions can change agent behavior "
            "or bypass authorization. Evidence should distinguish trusted instructions from "
            "the untrusted content that attempted to influence the agent."
        ),
    },
]


def main() -> None:
    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as file:
        documents = json.load(file)

    existing_ids = {document["id"] for document in documents}

    added = 0
    for entry in NEW_ENTRIES:
        if entry["id"] not in existing_ids:
            documents.append(entry)
            added += 1

    with open(KNOWLEDGE_FILE, "w", encoding="utf-8") as file:
        json.dump(documents, file, indent=2, ensure_ascii=False)
        file.write("\n")

    print(f"Knowledge entries added: {added}")
    print(f"Total knowledge entries: {len(documents)}")


if __name__ == "__main__":
    main()
