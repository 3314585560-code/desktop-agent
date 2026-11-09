# Mini Cursor 1.1 技能系统

| 技能 | 类型 | 可直接发送的任务 |
| --- | --- | --- |
| review-diff | 纯提示词 | 审查代码改动：只看 README.md |
| csv-profile | 带脚本 | 检查 CSV 数据：weekly sales.csv |
| project-checklist | MCP | 生成项目检查清单：Mini Cursor |

选择工作区并填写 API Key 后发送任务。技能命中时，对话区显示 `Skill / 技能名` 和「已按需加载技能正文」。CSV 文件放在工作区内，执行 CSV 脚本或审查 Git 差异前勾选「允许终端命令」。项目检查清单使用已有的独立 MCP 服务。

也可通过 `/skill csv-profile 检查 weekly sales.csv` 等命令显式选择。自动触发按任务开头与技能描述中的短语匹配，短语后可加冒号和参数。普通问题只向模型提供排序后的 `name`、`description` 目录。命中时，内部 `use_skill(name)` 才读取正文，并在本轮发送。后续普通问题仍只发送目录。技能没有改变四个内置工具的公开定义，CSV 检查通过现有 bash 工具执行。

## 开关

关闭应用后，在启动它的 PowerShell 里设置 `ENABLE_SKILLS=0`：

```powershell
$env:ENABLE_SKILLS = '0'
python app.py
```

安装版也可从同一终端启动，以继承该环境变量。恢复时运行 `Remove-Item Env:ENABLE_SKILLS`，再启动应用。

## 重生成验收报告

安装验收依赖 `python -m pip install -r requirements-inspect.txt`。从 [DeepSeek 的离线分词文档](https://api-docs.deepseek.com/quick_start/token_usage/) 下载分词器，将 `tokenizer.json` 放在 `build/skill-tokenizer.json`。在项目目录运行：

```powershell
$env:PYTHONIOENCODING = 'utf-8'
python app.py --inspect
```

可以用 `--tokenizer` 指向另一份 tokenizer 文件。项目根目录的 `skill_report.json` 由 `app.inspect` 生成。两种计数使用同一离线分词器，只比较技能目录与全量技能正文。六条试验通过实际 Agent 路径，并使用离线模型替身检验发出的请求。此处计数不含 API 的消息封装或其他提示词。
