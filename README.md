# 本地账号项目迁移

一个供 Codex 使用的 Skill：在同一台电脑切换账号后，检查并恢复本地项目列表、项目顺序、项目下的会话归属，以及可继续使用的历史。

**这是由 Codex 检查当前版本后执行的迁移流程，不是一键通用数据库修改器。** 内置 Python 工具仅负责压缩备份的校验与轮换，不负责自动识别或迁移所有版本的账号数据。

## 安装

将此仓库克隆到个人技能目录。默认 CODEX_HOME 为 `~/.codex`；如果设置了 CODEX_HOME，请使用实际目录。

```sh
git clone https://github.com/XiaobaiBye/codex-local-account-project-migration.git ~/.codex/skills/local-account-project-migration
```

Windows PowerShell：

```powershell
git clone https://github.com/XiaobaiBye/codex-local-account-project-migration.git "$env:USERPROFILE\.codex\skills\local-account-project-migration"
```

如果目标目录已存在，先检查已有技能，不要覆盖自己的修改。重新打开 Codex 的技能列表或开启新任务，确认“本地账号项目迁移”可见。

## 使用

在迁移前的原账号下发送：

> 使用 $local-account-project-migration，将本机原账号的项目迁移到我指定的新账号。保留每个项目下面的会话；验证成功后清理冗余，只保留当前迁移的一份压缩回退备份。

来源和目标账号不明确时，Codex 应先确认；不能假定当前账号一定是原账号。通常需要目标账号先在本机登录过，才能识别对应的本地配置。

流程包括只读盘点、当前版本结构核对、最小补丁 dry-run、压缩备份、退出应用后的写入、新账号界面验证，以及完成后的临时数据清理。需要文件系统权限时，按提示授权。请等正在进行的工作保存后，再正常完全退出桌面应用。

## 存储与备份规则

- 优先复用已有项目目录、会话历史和附件，仅修改必需的元数据。
- 只长期保留一个正式压缩备份：`rollback.json.gz`。
- 下一次迁移实际写入前，先生成并校验新备份，再原子替换上一份。准备和 dry-run 不删除旧备份。
- 同一次迁移有多轮修复时，补充到同一份备份，保留首次修改前的原值。
- 用户确认全部项目、会话历史及继续对话正常后，清理一次性脚本、临时快照、日志和重复备份。
- 项目源文件、历史、附件、登录信息、应用自己的 `.bak` 和 SQLite WAL/SHM 不属于可随意删除的冗余。

备份默认放在实际 CODEX_HOME 下的 `migration-backups/local-account-project-migration`，而非本仓库。备份可能包含个人路径、项目名称等元数据，不应上传。

## 适用范围

- 有一次 Windows 桌面版 `26.1103.4239.0` 的实际迁移成功记录。
- 其他版本及 macOS/Linux 的存储结构需要现场核对，尚不能视为经过验证。
- 不迁移云端资源、服务端账号权限、连接器授权、登录令牌或其他人的数据。
- 不通过修改会话创建者或伪造账号身份解决显示问题。
- 配置写入成功不等于迁移完成，必须在目标账号实际检查项目、历史及继续对话。

## 目录

```text
SKILL.md                     技能流程和操作约束
agents/openai.yaml           技能显示名称
references/local-state.md    已验证版本的本地数据检查线索
scripts/rollback_backup.py   唯一压缩备份的生成、轮换和校验
tests/test_rollback_backup.py 备份行为测试
```

运行测试需要 Python 3.10+，无第三方依赖：

```sh
python -m unittest discover -s tests -v
```

备份脚本的 `payload` 由执行迁移的 Codex 根据本次改动生成。它是 JSON 归档工具，不会自动判断回退资料是否足以恢复应用。请勿把任意空快照当作有效回退方案。

## Local account project migration (English)

A Codex skill for preserving local projects and their conversation membership when switching accounts on the same computer. It guides version-specific inspection, minimal metadata changes, rollback preparation, desktop verification, and cleanup. It is not a universal one-click migration utility.

Install this repository as `local-account-project-migration` under your actual `CODEX_HOME/skills`. Invoke `$local-account-project-migration` and identify the source and destination accounts. The bundled Python helper only manages a single compressed rollback bundle. On the next migration, the verified new bundle atomically replaces the previous bundle. No credentials or personal migration data belong in this repository.

MIT License. This is a community skill, not an official OpenAI migration tool.
