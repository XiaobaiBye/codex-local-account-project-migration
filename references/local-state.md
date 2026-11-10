# Windows 已成功实例：检查线索

本参考来自 Windows 桌面版 26.1103.4239.0 的一次本机迁移。现场版本不同必须重新核对，不提供一键数据库修改器。

## 层次与关联

- 实际 CODEX_HOME 下 `.codex-global-state.json` 保存 UI 元数据；`electron-account-renderer-state-v1` 包含当前 `owner` 和其他账号 `inactive` 下的 `atoms` / `globals`。
- 该实例账号指纹算法为 `sha256(JSON.stringify([userId, accountId]))`，这是本地配置选择方式，不是认证凭据。只复制所需项目显示字段，不能整份复制 atoms，以免搬入身份、远程连接、自动任务权限和认证状态。
- 项目字段包括 `local-projects`、`project-order` 和 `app-server-project-id-by-legacy-project-id-by-host`。迁移状态及 pending-deletions 可能影响重开后显示，需要根据实际实现处理。
- `thread-project-assignments` 保存旧 UI 项目 ID 关联；不能未经证明就假定该键永久共享或永久存在。第一次迁移时它存在，切换重启后它不再存在，导致仅复制项目列表不足以保证全部归属恢复。
- `state_5.sqlite` 的 `projects`、`project_roots` 保存运行时项目；`threads.project_id` 指向运行时项目 ID。旧 UI ID 和运行时 ID 不同。`creator_user_id` / `creator_account_id` 是来源身份，禁止为了显示会话修改它们。
- `sqlite/codex.db` 的 `local_thread_catalog` 是侧边栏会话目录，该实例键为 `(host_id, thread_id)`，也有 `project_id`。如果确需修改索引，应同时检查目录 revision/invalidation 是否需要更新，并备份这些字段的原值。
- `thread_history_1.sqlite` 保存投影后的 turns/items；旧 rollout 文件位于 sessions/archived_sessions。不能只看某一个来源就断言历史已经删除，也不能以存在 thread 元数据就推断正文完整。

## 实例中的遗漏与修复

一次实际迁移中，某项目的两条会话正文和目录记录存在，但两个索引的 `project_id` 都为空。只补这两行运行时归属、两行侧边栏归属及兼容映射，重开后用户确认项目和会话完整显示。其他项目已经正常，不重写它们。

这一经验只能指导检查，不能推出“project_id 为空就一定损坏”；旧版本可能通过 cwd 推断归属。

## 检查方法

优先发现可用的正式项目/任务接口；若没有，再使用 SQLite 只读查询、JSON 字段结构和当前安装包实现相互印证。读取安装包 ASAR 时可只在内存定位所需 JS，不必解包整个应用。不要修改应用包或认证数据库。

迁移前的回退应包含旧配置以及实际改动的索引行/目录 revision，而不仅是设置 gzip。应用在迁移后继续产生新记录，回退时按字段合并，不盲目覆盖整个旧数据库或全局配置。
