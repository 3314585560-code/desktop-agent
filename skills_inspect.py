"""Generate the course Skill report from the runtime and tokenizer."""
import hashlib
import json
from pathlib import Path
from threading import Event
from unittest.mock import patch

from agent_core import Agent, TOOLS
from skills_runtime import SKILL_ROOT, Skill, SkillCatalog

TRIALS = (
    ("审查代码改动", "review-diff"),
    ("检查 Git 差异：只看 README.md", "review-diff"),
    ("检查 CSV 数据：weekly sales.csv", "csv-profile"),
    ("统计 CSV 缺失值：samples/report.csv", "csv-profile"),
    ("生成项目检查清单：Mini Cursor", "project-checklist"),
    ("请解释什么是 CSV，不要检查 CSV 数据", None),
)


def inspect_skills(tokenizer_path):
    from tokenizers import Tokenizer

    tokenizer_path = Path(tokenizer_path)
    tokenizer = Tokenizer.from_file(str(tokenizer_path))
    digest = hashlib.sha256(tokenizer_path.read_bytes()).hexdigest()
    source = "DeepSeek 官方 V4 离线分词器" if digest == (
        "89085f12ef79460ac5f66d1119325ddfc694b4ab209d80bbd81d35f081dc9614"
    ) else "自定义 tokenizer.json"
    catalog = SkillCatalog()
    loaded = []
    original_loader = Skill.load_body

    def tracked_load(skill):
        loaded.append(skill.name)
        return original_loader(skill)

    def trial(prompt, expected, enabled):
        loaded.clear()
        events = []
        requests = []

        def reply(payload, key, cancel):
            requests.append(payload)
            return {"output": [{"type": "message", "content": [
                {"type": "output_text", "text": "触发验收回复"},
            ]}]}

        agent = Agent(SKILL_ROOT.parent, events.append, Event(), key="inspect-only", request=reply)
        # Isolate intent and payload checks from model and MCP availability.
        with patch.dict("os.environ", {"ENABLE_SKILLS": "1" if enabled else "0"}):
            with patch.object(Agent, "connect", return_value=[]):
                agent.run(prompt)
        payload = requests[0]
        actual = [item["name"] for item in events if item["kind"] == "skill"]
        desired = [expected] if expected else []
        bodies = [item["content"] for item in payload["input"] if item["role"] == "system"]
        assert actual == desired and loaded == desired
        assert len(bodies) == len(desired)
        assert payload["input"][-1]["content"] == prompt
        assert payload["tools"] == TOOLS
        assert (catalog.render() in payload["instructions"]) == enabled
        return {"prompt": prompt, "expected": expected, "actual": actual[0] if actual else None,
                "loaded_bodies": list(loaded), "passed": True}

    with patch.object(Skill, "load_body", tracked_load):
        assert SkillCatalog().render() == catalog.render() and not loaded
        trials = [trial(prompt, expected, True) for prompt, expected in TRIALS]
        disabled = trial(TRIALS[0][0], None, False)

    def tokens(text):
        return len(tokenizer.encode(text, add_special_tokens=False).ids)

    catalog_text = catalog.render()
    full_text = "\n\n".join([catalog_text] + [catalog.use_skill(name) for name in catalog.skills])
    catalog_tokens, full_tokens = tokens(catalog_text), tokens(full_text)
    ratio = full_tokens / catalog_tokens
    assert ratio >= 5, "渐进披露比率未达到 5"
    return {
        "catalog_tokens": catalog_tokens, "full_tokens": full_tokens,
        "disclosure_ratio": round(ratio, 4), "trials": trials,
        "false_triggers": sum(item["expected"] is None and item["actual"] is not None for item in trials),
        "disabled_trial": disabled, "skill_names": list(catalog.skills),
        "tokenizer": {"source": source, "sha256": digest},
        "measurement": "计数范围为技能目录及正文，触发试验运行实际 Agent 路径并使用离线模型替身。",
    }


def print_report(tokenizer_path):
    print(json.dumps(inspect_skills(tokenizer_path), ensure_ascii=False, indent=2))
