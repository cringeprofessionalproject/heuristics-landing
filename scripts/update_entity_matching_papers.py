#!/usr/bin/env python3
"""
Автоматический сбор и двухступенчатая фильтрация новых научных работ
по Entity Matching / Product Matching / Entity Resolution (OpenAlex API + LLM-фильтр).

Запуск локально:
  python3 scripts/update_entity_matching_papers.py --dry-run
  OPENAI_API_KEY=... python3 scripts/update_entity_matching_papers.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "data" / "entity-matching-papers.json"

# Статьи, уже зашитые статически в HTML (чтобы не дублировать)
STATIC_DOIS = {
    "10.48550/arxiv.2405.16884",
    "10.1126/sciadv.abi8021",
    "10.14778/3421424.3421431",
    "10.1145/3442200",
}

# Стоп-слова для отсева одноимённых терминов из химии, биологии и медицины
# (например, "Single-Entity Resolution" в электрохимии и сенсорике)
STOP_TERMS = (
    "nanosensor",
    "single-cell",
    "electrochem",
    "redox",
    "microrna",
    "protein",
    "genomic",
    "clinical",
    "patient",
    "quantum neural",
    "crystallography",
    "microscopy",
)

TOP_VENUES = (
    "vldb",
    "pvldb",
    "sigmod",
    "management of data",
    "icde",
    "data engineering",
    "kdd",
    "knowledge discovery",
    "world wide web",
    "acl",
    "emnlp",
    "coling",
    "naacl",
    "aaai",
    "neurips",
    "iclr",
    "science advances",
)

DOMAIN_BOOST_TERMS = (
    "product matching",
    "entity matching",
    "entity resolution",
    "record linkage",
    "catalog",
    "e-commerce",
    "blocking",
    "schema matching",
    "attribute",
    "tabular",
    "large language model",
)


def reconstruct_abstract(inv_index: dict | None) -> str:
    if not inv_index or not isinstance(inv_index, dict):
        return ""
    positions: dict[int, str] = {}
    for word, idxs in inv_index.items():
        for pos in idxs:
            positions[pos] = word
    if not positions:
        return ""
    return " ".join(positions[i] for i in sorted(positions.keys()))


def normalize_doi(doi_url: str | None) -> str:
    if not doi_url:
        return ""
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", doi_url.strip(), flags=re.I).lower()


def deterministic_score(work: dict, abstract: str) -> tuple[int, str]:
    title = (work.get("title") or "").strip()
    hay = f"{title} {abstract}".lower()

    for bad in STOP_TERMS:
        if bad in hay:
            return -100, f"stop_term:{bad}"

    topic = work.get("primary_topic") or {}
    domain_name = ((topic.get("domain") or {}).get("display_name") or "").lower()
    field_name = ((topic.get("field") or {}).get("display_name") or "").lower()
    if domain_name and "physical" not in domain_name and "computer" not in field_name and "decision" not in field_name and "engineering" not in field_name:
        return -50, f"off_domain:{domain_name}/{field_name}"

    score = 0
    loc = work.get("primary_location") or {}
    venue = ((loc.get("source") or {}).get("display_name") or "").lower()

    if any(v in venue for v in TOP_VENUES):
        score += 4
    elif "arxiv" in venue:
        score += 1

    for kw in DOMAIN_BOOST_TERMS:
        if kw in hay:
            score += 1

    cites = int(work.get("cited_by_count") or 0)
    if cites >= 20:
        score += 3
    elif cites >= 5:
        score += 2
    elif cites >= 2:
        score += 1

    return score, venue or "preprint"


def llm_evaluate_and_summarize(title: str, abstract: str, venue: str, year: int) -> dict | None:
    """
    Второй этап фильтрации через Ollama Cloud (OLLAMA_API_KEY) или любой OpenAI-совместимый API.
    Оценивает практическую ценность статьи по шкале 0..10 для задач сопоставления товарной номенклатуры (SKU)
    и возвращает готовую русскоязычную аннотацию в редакционном стиле Heuristics.
    """
    ollama_key = os.environ.get("OLLAMA_API_KEY")
    api_key = ollama_key or os.environ.get("LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None

    default_url = "https://ollama.com/v1" if ollama_key else "https://api.openai.com/v1"
    default_model = "deepseek-v3.1:671b" if ollama_key else "gpt-4o-mini"
    base_url = os.environ.get("LLM_BASE_URL", default_url).rstrip("/")
    model = os.environ.get("LLM_MODEL", default_model)

    prompt = (
        "Ты научный редактор исследовательской группы Heuristics (занимаемся алгоритмами Entity Matching, "
        "сопоставлением промышленной B2B-номенклатуры, осевым скорингом атрибутов и LLM-экстракцией).\n"
        "Оцени научную статью по шкале от 0 до 10, насколько она фундаментальна или практически полезна "
        "именно для компьютерных задач Entity Matching / Product Matching / Entity Resolution в таблицах и каталогах "
        "(отсеивай медицину, биоинформатику, химию, соцсети и проходные студенческие заметки).\n\n"
        f"Название: {title}\nПлощадка/год: {venue} ({year})\nАннотация: {abstract[:2000]}\n\n"
        "Верни СТРОГО JSON без markdown-обёртки:\n"
        '{"score": <число 0..10>, "tag": "<короткий тег на англ, до 28 симв>", '
        '"summary_ru": "<емкая академическая аннотация на русском языке из 2 предложений без воды и пафоса>"}'
    )

    body = json.dumps(
        {
            "model": model,
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)


def fetch_candidates(since_date: str, per_page: int = 25) -> list[dict]:
    params = {
        "filter": (
            'title.search:"entity matching"|"product matching"|"entity resolution"|'
            f'"schema matching",from_publication_date:{since_date},type:article|preprint'
        ),
        "sort": "cited_by_count:desc",
        "per-page": str(per_page),
    }
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "HeuristicsResearchFeed/1.0 (mailto:info@heuristics.ru)"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    return payload.get("results", [])


def format_authors(work: dict) -> str:
    names = [
        (a.get("author") or {}).get("display_name", "").strip()
        for a in (work.get("authorships") or [])
        if (a.get("author") or {}).get("display_name")
    ]
    if not names:
        return "Research Preprint"
    if len(names) > 4:
        return ", ".join(names[:3]) + ", et al."
    return ", ".join(names)


def main() -> int:
    parser = argparse.ArgumentParser(description="Update curated Entity Matching bibliography.")
    parser.add_argument("--since", default="2024-01-01", help="ISO date YYYY-MM-DD")
    parser.add_argument("--min-det-score", type=int, default=6, help="Minimum deterministic score")
    parser.add_argument("--max-add", type=int, default=2, help="Max new papers per run")
    parser.add_argument("--dry-run", action="store_true", help="Print candidates without writing file")
    args = parser.parse_args()

    existing_data = {"updated_at": dt.date.today().isoformat(), "source": "", "items": []}
    if JSON_PATH.exists():
        existing_data = json.loads(JSON_PATH.read_text(encoding="utf-8"))

    known_dois = set(STATIC_DOIS)
    for item in existing_data.get("items", []):
        if item.get("doi"):
            known_dois.add(item["doi"].lower())

    works = fetch_candidates(args.since)
    accepted: list[dict] = []

    for w in works:
        doi = normalize_doi(w.get("doi"))
        if not doi or doi in known_dois:
            continue

        abstract = reconstruct_abstract(w.get("abstract_inverted_index"))
        det_score, venue_hint = deterministic_score(w, abstract)
        if det_score < args.min_det_score:
            continue

        title = (w.get("title") or "").strip()
        year = int(w.get("publication_year") or dt.date.today().year)
        loc = w.get("primary_location") or {}
        venue_display = ((loc.get("source") or {}).get("display_name") or "arXiv Preprint").strip()

        llm_res = llm_evaluate_and_summarize(title, abstract, venue_display, year)
        if llm_res is not None:
            if int(llm_res.get("score", 0)) < 8:
                print(f"[SKIP LLM {llm_res.get('score')}/10] {title}")
                continue
            desc_ru = llm_res["summary_ru"]
            tag = llm_res.get("tag") or "Entity Matching"
        else:
            if not args.dry_run:
                print(f"[CANDIDATE det={det_score}, set LLM_API_KEY to auto-annotate in RU] {title} ({doi})")
                continue
            desc_ru = f"[Кандидат прошёл детерминированный отбор: score={det_score}, цитирований={w.get('cited_by_count', 0)}] {abstract[:260]}..."
            tag = "Entity Matching"

        entry = {
            "id": doi,
            "venue": f"{venue_display[:34]} · {year}",
            "tag": tag,
            "title": title,
            "meta": f"{format_authors(w)} · {venue_display} ({year})",
            "desc": desc_ru,
            "doi": doi,
            "url": f"https://doi.org/{doi}",
        }
        accepted.append(entry)
        known_dois.add(doi)
        print(f"[ACCEPT] {year} | det={det_score} | {title} ({doi})")

        if len(accepted) >= args.max_add:
            break

    if args.dry_run:
        print(f"\nDry-run завершён: найдено новых релевантных работ: {len(accepted)}")
        return 0

    if accepted:
        existing_data["items"] = accepted + existing_data.get("items", [])
        existing_data["updated_at"] = dt.date.today().isoformat()
        JSON_PATH.write_text(json.dumps(existing_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Обновлён {JSON_PATH}: добавлено {len(accepted)} работ.")
    else:
        print("Новых статей сверх текущего списка не добавлено.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
