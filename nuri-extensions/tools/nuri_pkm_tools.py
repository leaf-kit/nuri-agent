"""NURI PKM Tools — NURI Base 관리를 위한 전용 도구.

Hermes Agent의 도구 레지스트리(registry.register)를 통해 등록되며,
원본 코어를 수정하지 않고 플러그인 방식으로 동작합니다.

사용법:
  model_tools.py의 _discover_tools() 목록에 아래를 추가:
    "nuri-extensions.tools.nuri_pkm_tools"
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime, timedelta

try:
    from tools.registry import registry
except ImportError:
    registry = None


# ---------------------------------------------------------------------------
# 설정
# ---------------------------------------------------------------------------

def _get_nuri_base() -> Path:
    """NURI Base 경로를 반환합니다. 환경변수 또는 기본값을 사용합니다."""
    base = os.getenv("NURI_BASE", os.path.join(os.getcwd(), "notes"))
    return Path(base)


# ---------------------------------------------------------------------------
# 도구 1: nuri_scan_vault — NURI Base 파일 목록/메타데이터 스캔
# ---------------------------------------------------------------------------

def nuri_scan_vault(path: str = "", filter_type: str = "", filter_tag: str = "",
                    days: int = 0, **kwargs) -> str:
    """NURI Base를 스캔하여 노트 목록과 메타데이터를 반환합니다."""
    base = _get_nuri_base()
    scan_path = base / path if path else base

    if not scan_path.exists():
        return json.dumps({"error": f"경로가 존재하지 않습니다: {scan_path}"})

    results = []
    for md_file in sorted(scan_path.rglob("*.md")):
        # 날짜 필터
        if days > 0:
            mtime = datetime.fromtimestamp(md_file.stat().st_mtime)
            if mtime < datetime.now() - timedelta(days=days):
                continue

        # 프론트매터 파싱
        content = md_file.read_text(encoding="utf-8", errors="replace")
        frontmatter = _parse_frontmatter(content)

        # 유형 필터
        if filter_type and frontmatter.get("type", "") != filter_type:
            continue

        # 태그 필터
        if filter_tag:
            tags = frontmatter.get("tags", [])
            if isinstance(tags, str):
                tags = [t.strip() for t in tags.split(",")]
            if filter_tag not in tags:
                continue

        results.append({
            "path": str(md_file.relative_to(base)),
            "title": frontmatter.get("title", md_file.stem),
            "type": frontmatter.get("type", "unknown"),
            "tags": frontmatter.get("tags", []),
            "date": frontmatter.get("date", ""),
            "status": frontmatter.get("status", ""),
            "size": md_file.stat().st_size,
            "modified": datetime.fromtimestamp(md_file.stat().st_mtime).isoformat(),
        })

    return json.dumps({
        "base": str(base),
        "count": len(results),
        "notes": results[:100],  # 최대 100개
    }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 도구 2: nuri_find_links — 노트 간 링크 관계 분석
# ---------------------------------------------------------------------------

def nuri_find_links(target: str = "", mode: str = "outgoing", **kwargs) -> str:
    """노트 간 링크 관계를 분석합니다.

    mode:
      - outgoing: 대상 노트가 참조하는 노트 목록
      - incoming: 대상 노트를 참조하는 노트 목록 (백링크)
      - orphans: 어디서도 참조되지 않는 고아 노트 목록
      - broken: 존재하지 않는 노트를 참조하는 깨진 링크 목록
    """
    base = _get_nuri_base()

    if mode == "orphans":
        return _find_orphans(base)
    elif mode == "broken":
        return _find_broken_links(base)

    if not target:
        return json.dumps({"error": "target 매개변수가 필요합니다"})

    target_path = base / target if not target.endswith(".md") else base / target
    if not target_path.suffix:
        target_path = target_path.with_suffix(".md")

    if mode == "outgoing":
        return _find_outgoing(base, target_path)
    elif mode == "incoming":
        return _find_incoming(base, target_path)
    else:
        return json.dumps({"error": f"알 수 없는 mode: {mode}"})


def _find_outgoing(base: Path, target_path: Path) -> str:
    if not target_path.exists():
        return json.dumps({"error": f"파일이 존재하지 않습니다: {target_path}"})

    content = target_path.read_text(encoding="utf-8", errors="replace")
    wiki_links = re.findall(r'\[\[([^\]]+)\]\]', content)
    md_links = re.findall(r'\[.*?\]\(([^)]+\.md)\)', content)

    links = []
    for link in set(wiki_links + md_links):
        link_path = base / f"{link}.md" if not link.endswith(".md") else base / link
        links.append({"target": link, "exists": link_path.exists()})

    return json.dumps({"source": str(target_path.relative_to(base)),
                        "outgoing": links, "count": len(links)}, ensure_ascii=False)


def _find_incoming(base: Path, target_path: Path) -> str:
    target_name = target_path.stem
    incoming = []

    for md_file in base.rglob("*.md"):
        if md_file == target_path:
            continue
        content = md_file.read_text(encoding="utf-8", errors="replace")
        if f"[[{target_name}]]" in content or target_name in content:
            # 맥락 발췌
            for line in content.split("\n"):
                if target_name in line:
                    incoming.append({
                        "source": str(md_file.relative_to(base)),
                        "context": line.strip()[:200],
                    })
                    break

    return json.dumps({"target": str(target_path.relative_to(base)),
                        "incoming": incoming, "count": len(incoming)}, ensure_ascii=False)


def _find_orphans(base: Path) -> str:
    all_notes = {f.stem for f in base.rglob("*.md")}
    referenced = set()

    for md_file in base.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8", errors="replace")
        wiki_links = re.findall(r'\[\[([^\]]+)\]\]', content)
        for link in wiki_links:
            referenced.add(link)

    orphans = sorted(all_notes - referenced)
    return json.dumps({"orphans": orphans, "count": len(orphans)}, ensure_ascii=False)


def _find_broken_links(base: Path) -> str:
    all_notes = {f.stem for f in base.rglob("*.md")}
    broken = []

    for md_file in base.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8", errors="replace")
        wiki_links = re.findall(r'\[\[([^\]]+)\]\]', content)
        for link in wiki_links:
            if link not in all_notes:
                broken.append({"source": str(md_file.relative_to(base)), "broken_link": link})

    return json.dumps({"broken": broken, "count": len(broken)}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 도구 3: nuri_frontmatter — 프론트매터 일괄 읽기/수정
# ---------------------------------------------------------------------------

def nuri_frontmatter(path: str, action: str = "read", key: str = "",
                     value: str = "", **kwargs) -> str:
    """노트의 YAML 프론트매터를 읽거나 수정합니다.

    action:
      - read: 프론트매터 전체 반환
      - get: 특정 키의 값 반환
      - set: 특정 키에 값 설정
      - tags: 전체 NURI Base에서 사용 중인 태그 목록 반환
    """
    base = _get_nuri_base()

    if action == "tags":
        return _collect_all_tags(base)

    file_path = base / path
    if not file_path.exists():
        return json.dumps({"error": f"파일이 존재하지 않습니다: {file_path}"})

    content = file_path.read_text(encoding="utf-8", errors="replace")
    frontmatter = _parse_frontmatter(content)

    if action == "read":
        return json.dumps({"path": path, "frontmatter": frontmatter}, ensure_ascii=False)
    elif action == "get":
        return json.dumps({"path": path, "key": key,
                            "value": frontmatter.get(key, None)}, ensure_ascii=False)
    elif action == "set":
        if not key:
            return json.dumps({"error": "key 매개변수가 필요합니다"})
        frontmatter[key] = value
        new_content = _rebuild_frontmatter(content, frontmatter)
        file_path.write_text(new_content, encoding="utf-8")
        return json.dumps({"path": path, "key": key, "value": value,
                            "success": True}, ensure_ascii=False)
    else:
        return json.dumps({"error": f"알 수 없는 action: {action}"})


def _collect_all_tags(base: Path) -> str:
    tag_counts: dict[str, int] = {}
    for md_file in base.rglob("*.md"):
        content = md_file.read_text(encoding="utf-8", errors="replace")
        fm = _parse_frontmatter(content)
        tags = fm.get("tags", [])
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.split(",")]
        for tag in tags:
            tag = str(tag).strip()
            if tag:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

    sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
    return json.dumps({"tags": [{"name": t, "count": c} for t, c in sorted_tags],
                        "total": len(sorted_tags)}, ensure_ascii=False)


# ---------------------------------------------------------------------------
# 유틸리티
# ---------------------------------------------------------------------------

def _parse_frontmatter(content: str) -> dict:
    """간단한 YAML 프론트매터 파서."""
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    fm_text = parts[1].strip()
    result = {}
    for line in fm_text.split("\n"):
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            # 배열 파싱 [a, b, c]
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",")]
            elif val.startswith('"') and val.endswith('"'):
                val = val[1:-1]
            result[key] = val
    return result


def _rebuild_frontmatter(content: str, frontmatter: dict) -> str:
    """프론트매터를 재구성하여 본문과 합칩니다."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        body = parts[2] if len(parts) >= 3 else ""
    else:
        body = content

    fm_lines = ["---"]
    for k, v in frontmatter.items():
        if isinstance(v, list):
            fm_lines.append(f"{k}: [{', '.join(str(i) for i in v)}]")
        else:
            fm_lines.append(f'{k}: "{v}"' if " " in str(v) else f"{k}: {v}")
    fm_lines.append("---")

    return "\n".join(fm_lines) + body


# ---------------------------------------------------------------------------
# 레지스트리 등록
# ---------------------------------------------------------------------------

if registry is not None:

    SCAN_SCHEMA = {
        "type": "function",
        "function": {
            "name": "nuri_scan_vault",
            "description": "NURI Base(마크다운 노트 저장소)를 스캔하여 노트 목록과 메타데이터를 반환합니다. 경로, 유형, 태그, 날짜로 필터링 가능합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "스캔할 하위 경로 (비우면 전체 스캔)", "default": ""},
                    "filter_type": {"type": "string", "description": "노트 유형 필터 (article, meeting, permanent, literature, fleeting 등)", "default": ""},
                    "filter_tag": {"type": "string", "description": "태그 필터", "default": ""},
                    "days": {"type": "integer", "description": "최근 N일 내 수정된 노트만 (0=전체)", "default": 0},
                },
            },
        },
    }

    LINKS_SCHEMA = {
        "type": "function",
        "function": {
            "name": "nuri_find_links",
            "description": "NURI Base 노트 간 링크 관계를 분석합니다. 나가는 링크, 들어오는 백링크, 고아 노트, 깨진 링크를 찾습니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "대상 노트 파일명 (orphans/broken 모드에서는 불필요)"},
                    "mode": {"type": "string", "enum": ["outgoing", "incoming", "orphans", "broken"],
                             "description": "분석 모드: outgoing(나가는 링크), incoming(백링크), orphans(고아 노트), broken(깨진 링크)"},
                },
                "required": ["mode"],
            },
        },
    }

    FRONTMATTER_SCHEMA = {
        "type": "function",
        "function": {
            "name": "nuri_frontmatter",
            "description": "마크다운 노트의 YAML 프론트매터를 읽거나 수정합니다. 전체 NURI Base의 태그 목록도 조회 가능합니다.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "노트 파일 경로 (tags 액션에서는 불필요)"},
                    "action": {"type": "string", "enum": ["read", "get", "set", "tags"],
                               "description": "read(전체 읽기), get(특정 키), set(키 설정), tags(전체 태그 목록)"},
                    "key": {"type": "string", "description": "프론트매터 키 (get/set에서 사용)"},
                    "value": {"type": "string", "description": "설정할 값 (set에서 사용)"},
                },
                "required": ["action"],
            },
        },
    }

    registry.register(
        name="nuri_scan_vault",
        toolset="nuri-pkm",
        schema=SCAN_SCHEMA,
        handler=lambda args, **kw: nuri_scan_vault(**args, **kw),
        check_fn=lambda: True,
    )

    registry.register(
        name="nuri_find_links",
        toolset="nuri-pkm",
        schema=LINKS_SCHEMA,
        handler=lambda args, **kw: nuri_find_links(**args, **kw),
        check_fn=lambda: True,
    )

    registry.register(
        name="nuri_frontmatter",
        toolset="nuri-pkm",
        schema=FRONTMATTER_SCHEMA,
        handler=lambda args, **kw: nuri_frontmatter(**args, **kw),
        check_fn=lambda: True,
    )
