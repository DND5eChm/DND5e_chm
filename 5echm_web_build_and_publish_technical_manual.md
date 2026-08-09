# DND5e 不全书 Web 自动构建与发布技术手册

> 文档用途：交接给后续维护者，说明 DND5e_chm → 静态 Web → 搜索索引的完整构建、发布、密钥、分支、故障处理与回滚机制。  
> 基线日期：2026-08-09。后续若仓库结构、编译器接口、GitHub Actions 主版本或部署平台发生变化，应同步更新本手册。  
> 建议存放位置：`DND5e_chm/docs/web-build-handover.md`，并与 `.github/workflows/build-web.yml` 一起维护。

---

## 1. 系统目标与边界

这套自动化的目标是：每当 `DND5eChm/DND5e_chm` 的 `main` 分支有新提交，或者维护者手动启动 GitHub Actions 时，自动取得最新内容、最新版 Web 编译器、最新版基础模板和最新版搜索页面，构建静态站点与搜索索引，然后分别发布到两个目标位置。

静态网页发布到 `DND5eChm/5echm_web` 的 `pages` 分支。搜索索引不进入网页仓库，也不进入 `5echmweb_search` 的主开发分支，而是单独发布到 `DND5eChm/5echmweb_search` 的 `index` 分支。`5echmweb_search:main` 仅作为搜索前端页面 `webhelpsearch.htm` 和搜索服务代码的源码分支，自动构建流程不得向它提交生成物。

系统的核心原则是“源码与生成物分离”。`DND5e_chm:main` 是内容源码，`5echm_web_build:main` 是编译器源码，`5echm_web_templates:main` 是 WebHelp 基础模板源码，`5echmweb_search:main` 是搜索前端/后端源码；`5echm_web:pages` 与 `5echmweb_search:index` 才是自动生成物的发布位置。

---

## 2. 仓库与分支职责

| 仓库 | 分支 | 角色 | Actions 是否写入 |
|---|---|---|---|
| `DND5eChm/DND5e_chm` | `main` | 内容源、WCP 工程、触发自动构建 | 否 |
| `DND5eChm/5echm_web_build` | `main` | `wcp2web` 编译器 | 否 |
| `DND5eChm/5echm_web_templates` | `main` | WebHelp 基础模板 | 否 |
| `DND5eChm/5echmweb_search` | `main` | 最新 `webhelpsearch.htm` 与搜索服务器源码 | 否 |
| `DND5eChm/5echmweb_search` | `index` | 搜索索引 `data.js`、`data.js.zip` | 是 |
| `DND5eChm/5echm_web` | `pages` | 最终静态网站 / GitHub Pages 源 | 是 |

不要把 `data.js` 提交到 `5echm_web:pages`。不要让自动构建向 `5echmweb_search:main` 或任何 `master` 主开发分支推送索引。workflow 中有显式保护：如果 `SEARCH_INDEX_BRANCH` 被误设为 `main` 或 `master`，任务会直接失败。

---

## 3. 数据流

```text
DND5e_chm:main
  └── 不全书.wcp + HTML/HTM/图片/CSS/JS 等内容
          │
          │
          ├── 5echm_web_build:main
          │      └── wcp2web 编译器
          │
          ├── 5echm_web_templates:main
          │      └── WebHelp 基础模板
          │
          └── 5echmweb_search:main
                 └── webhelpsearch.htm（最新版搜索页面，只读）
                          │
                          ▼
                    wcp2web build
                          │
              ┌───────────┴───────────┐
              │                       │
              ▼                       ▼
       output/site/             output/search/data.js
              │                       │
              │                       ├── data.js
              │                       └── data.js.zip
              │                              │
              │                              ▼
              │                   5echmweb_search:index
              │
              ├── 删除 site/data.js
              ├── 不使用 rsync --delete
              ▼
       5echm_web:pages
              │
              ▼
         GitHub Pages
```

---

## 4. 编译器行为：维护者必须知道的事实

`wcp2web` 要求 Python 3.11 或更高版本。当前自动化固定使用 Python 3.12。其主要入口是：

```bash
wcp2web build --config build-config/wcp2web.toml
```

配置文件中的相对路径不是相对于仓库根目录，而是相对于 `wcp2web.toml` 自身所在目录解析。因此当前 workflow 把配置写到 `build-config/wcp2web.toml`，路径统一写成 `../content/...`、`../templates`、`../output/...`。

当前内容主工程使用：

```text
content/不全书.wcp
```

当前核心配置为：

```toml
[project]
wcp = "../content/不全书.wcp"
source_root = "../content"
template_root = "../templates"
title = "5E 不全书"

[output]
site_dir = "../output/site"
search_data = "../output/search/data.js"
report_dir = "../output/reports"

[webhelp]
search_api_base = "https://5echmsearch.kagangtuya.top"
search_template = "../search-source/webhelpsearch.htm"
default_page = ""
nav_width = 285
back_color = "#ffffff"

[encoding]
default_fallback = "gb18030"
strict = false

[build]
jobs = 4
incremental = false
clean = true
```

这里的 `search_api_base` 必须是普通 TOML URL 字符串，不要写成 Markdown 链接。正确形式就是：

```toml
search_api_base = "https://5echmsearch.kagangtuya.top"
```

---

## 5. 为什么搜索页面不能使用模板仓库里的旧文件

`5echm_web_templates` 中存在一个历史版本的 `webhelpsearch.htm`，它属于旧式本地 WinCHM 搜索实现，不应再作为线上 Web 搜索页。最终构建必须明确使用：

```text
5echmweb_search:main/webhelpsearch.htm
```

workflow 将该仓库单独 checkout 到：

```text
search-source/
```

然后配置：

```toml
search_template = "../search-source/webhelpsearch.htm"
```

`wcp2web` 的模板选择逻辑会优先使用显式配置的 `search_template`，因此只要这个路径有效，最终 `output/site/webhelpsearch.htm` 就来自 `5echmweb_search:main`，而不是模板仓库里的旧搜索页。

当前搜索页源码仍可能包含：

```javascript
var API_BASE="http://localhost:13000"
```

而 `wcp2web` 的模板变量是：

```text
($SEARCH_API_BASE$)
```

因此 workflow 在临时工作区中把 `API_BASE` 的字符串赋值转换为：

```javascript
var API_BASE="($SEARCH_API_BASE$)"
```

随后由编译器根据 `search_api_base` 注入：

```javascript
var API_BASE="https://5echmsearch.kagangtuya.top"
```

这一步只修改 GitHub Actions runner 中的临时文件，不会提交回 `5echmweb_search:main`。如果未来 `webhelpsearch.htm` 已经原生使用 `($SEARCH_API_BASE$)`，workflow 会识别并直接使用；如果未来搜索页彻底重构、不再存在一个可识别的 `API_BASE = "..."` 赋值，workflow 会故意失败，提醒维护者同步调整注入逻辑，而不是静默发布错误 API。

---

## 6. 为什么网页仓库不能有 data.js

当前 `wcp2web` 在正常生成：

```text
output/search/data.js
```

之后，还会为了历史兼容额外复制一份：

```text
output/site/data.js
```

但是现行 Web 搜索使用远端搜索 API，网页本身不应携带巨大的本地搜索索引。因此自动构建在编译完成后会明确执行：

```bash
rm -f output/site/data.js output/site/data.js.zip
```

同步网页时还会再次排除：

```text
data.js
data.js.zip
```

并且会删除 `5echm_web:pages` 根目录中历史遗留的：

```text
data.js
data.js.zip
```

这两个文件是网页发布中唯一被主动清理的特殊生成物。

---

## 7. pages 同步策略：覆盖，但不清空

站点同步使用：

```bash
rsync -a \
  --exclude='.git/' \
  --exclude='.github/' \
  --exclude='CNAME' \
  --exclude='README.md' \
  --exclude='data.js' \
  --exclude='data.js.zip' \
  output/site/ \
  publish-site/
```

这里刻意没有 `--delete`。

因此行为是：构建输出中存在的同名文件覆盖网页仓库中的旧版本；新文件会增加；网页仓库中已有但本次构建没有产生的其他文件不会因为同步而消失。`output/site/` 最后的 `/` 很重要，它表示复制 `site` 里面的内容到仓库根目录，不会创建 `pages/site/` 或 `pages/output/`。

例如：

```text
output/site/index.html
```

会成为：

```text
5echm_web:pages/index.html
```

而不是：

```text
5echm_web:pages/site/index.html
```

`.github/`、`CNAME` 和 `README.md` 额外被排除，避免构建器覆盖仓库管理文件和自定义域名配置。

---

## 8. 搜索索引分支设计

搜索索引最终发布到：

```text
DND5eChm/5echmweb_search:index
```

目标文件为：

```text
data.js
data.js.zip
```

`data.js.zip` 是真正的 ZIP 文件，内部只包含一个根目录成员：

```text
data.js
```

不是 `output/search/data.js` 这样的嵌套路径。workflow 使用 Python `zipfile` 生成压缩包，并固定 ZIP 内部时间戳为 ZIP 规范允许的最早时间，目的是让同一个 `data.js` 产生稳定的压缩结果。这样内容没变化时，不会因为压缩包时间戳变化而制造无意义 commit。生成后还会重新打开 ZIP，验证 CRC、成员列表和解压后的字节内容。

如果 `index` 分支第一次运行时不存在，workflow 会创建：

```bash
git checkout --orphan index
```

即创建一个与 `main` 没有历史继承关系的独立发布分支。首次提交只有索引生成物。以后如果 `index` 已存在，则直接切换到远端 `index` 并更新两个索引文件。

workflow 对该分支的提交使用：

```bash
git add data.js data.js.zip
```

不会因为工作区其他变化而误提交其他文件。

---

## 9. 重要的部署耦合：index 分支不是搜索服务自动可见的

这是后来维护者最容易忽略的问题。

当前 `5echmweb_search/server.js` 实际代码从 Node 进程所在目录直接读取：

```javascript
const dataPath = path.join(__dirname, "data.js");
const content = fs.readFileSync(dataPath, "utf-8");
```

当前代码中没有 `DATA_JS_PATH` 的实际使用。因此，把生成物从 `main` 移到 `index` 后，如果生产平台仍然只 checkout / deploy `main`，服务器将不会自动得到最新版 `data.js`。

换句话说，本文档里的 DND5e_chm workflow 只负责“生成和发布索引到 index”，搜索服务的部署流程还必须负责“把 index:data.js 放到 server.js 同目录”。

推荐的生产部署结构是：

```text
部署阶段
  ├── checkout 5echmweb_search:main
  │      ├── server.js
  │      ├── package.json
  │      └── webhelpsearch.htm
  │
  └── 从 5echmweb_search:index 取得 data.js
         │
         ▼
      与 server.js 放到同一个运行目录
```

如果以后修改 `server.js`，可以考虑正式支持类似 `DATA_JS_PATH` 的环境变量；在那之前，以实际源码读取 `__dirname/data.js` 的行为为准，不要假设部署平台会自动跨分支取得索引。

---

## 10. GitHub Pages 设置

`5echm_web` 的发布源应保持：

```text
Branch: pages
Folder: / (root)
```

最终站点直接写入 `pages` 分支根目录。`CNAME` 由仓库自身管理，workflow 不覆盖它。

检查位置：

```text
5echm_web
→ Settings
→ Pages
→ Build and deployment
```

如果未来把 Pages 改成 GitHub Actions artifact deployment，而不是 branch deployment，需要重新设计这部分流程，本手册当前方案不再直接适用。

---

## 11. 密钥与权限

DND5e_chm 自带的 `GITHUB_TOKEN` 只用于读取当前仓库，不应该扩大它的权限。跨仓库向 `5echm_web` 和 `5echmweb_search` push 使用单独的：

```text
WEB_PUBLISH_TOKEN
```

推荐使用 Fine-grained Personal Access Token。Resource owner 选择 `DND5eChm`，Repository access 只选：

```text
DND5eChm/5echm_web
DND5eChm/5echmweb_search
```

Repository permissions 只需要：

```text
Contents: Read and write
```

不要无必要地授予 Administration、Actions、Issues、Pull requests 等权限。

Token 创建后，在：

```text
DND5eChm/DND5e_chm
→ Settings
→ Secrets and variables
→ Actions
→ New repository secret
```

创建：

```text
Name:  WEB_PUBLISH_TOKEN
Value: github_pat_...
```

不要把 PAT 写进 workflow、README、issue、commit message 或日志。Token 到期后，重新生成并替换同名 Repository Secret 即可，无需修改 YAML。

如果组织启用了 Fine-grained PAT 审批，需要确认 token 已被组织批准。若目标分支存在 branch ruleset / protection，还要确保该 PAT 所属账号被允许 push 或具有相应 bypass，否则典型错误是 `GH013`、protected branch rejection 等。

---

## 12. 最终 GitHub Actions

workflow 文件位置：

```text
DND5e_chm/.github/workflows/build-web.yml
```

完整内容见本手册同目录配套文件 `build-web.yml`。当前基线使用：

```text
actions/checkout@v7
actions/setup-python@v7
actions/upload-artifact@v7
```

GitHub Actions 的主版本会继续演进。后续维护者在升级时，应先阅读官方 action 的 release notes，确认 runner / Node runtime / input 行为没有破坏性变化，再修改 major version。对于更高供应链安全要求的部署，可以进一步把第三方 action pin 到完整 commit SHA。

---

## 13. 首次上线步骤

第一次部署前，先创建 `WEB_PUBLISH_TOKEN`，确认它至少能够向 `5echm_web:pages` 和 `5echmweb_search:index` 写入。如果 `index` 尚不存在，不需要手工创建，workflow 会创建 orphan 分支。

然后把 `build-web.yml` 放入 `DND5e_chm/.github/workflows/` 并提交到 `main`。该提交本身就会触发一次构建。也可以进入 GitHub 的 Actions 页面找到 `Build and Publish 5echm Web`，使用 `Run workflow` 手动执行。

首次成功运行后，至少检查以下结果：

```text
5echm_web:pages
  - index.html 已更新
  - webhelpsearch.htm 已更新
  - webhelpsearch.htm 包含 https://5echmsearch.kagangtuya.top
  - 不存在 data.js
  - 不存在 data.js.zip
  - CNAME 仍存在
  - .github/ 仍存在

5echmweb_search:main
  - 源码没有因为构建而产生提交

5echmweb_search:index
  - 存在 data.js
  - 存在 data.js.zip
  - ZIP 内只有 data.js
```

最后必须验证线上搜索服务是否真的使用了 `index` 分支的新数据。Action 成功只证明索引已经发布，不证明搜索服务器的部署环境已经把它同步到 `server.js` 所在目录。

---

## 14. 日常维护方式

内容更新只改 `DND5e_chm:main`。模板壳层更新改 `5echm_web_templates:main`。搜索 UI / API 客户端页面更新改 `5echmweb_search:main/webhelpsearch.htm`。编译逻辑更新改 `5echm_web_build:main`。

当前 workflow 的自动触发源只有 `DND5e_chm:main`。也就是说，单独修改编译器、模板或搜索页面，并不会自动启动 DND5e_chm 的构建。修改这些仓库后，如果需要立即重新发布网站，应到 `DND5e_chm` 的 Actions 页面手动执行 `workflow_dispatch`。

这是有意设计：内容仓库是发布编排入口，其他仓库只是构建依赖。若以后希望任一依赖仓库变更都自动重建，需要增加 `repository_dispatch`、可复用 workflow 或其他跨仓库触发机制。

---

## 15. 修改生产搜索 API

如果域名发生变化，只修改 workflow 顶部：

```yaml
env:
  SEARCH_API_BASE: "https://新的域名"
```

配置生成步骤会自动把该变量写入 TOML；构建后的验证步骤也使用同一个变量，因此不存在“配置改了但验证仍检查旧 URL”的双重配置问题。

不要直接手工修改 `5echm_web:pages/webhelpsearch.htm`，因为下一次构建会覆盖它。

---

## 16. 常见故障

### 16.1 `WEB_PUBLISH_TOKEN is not configured`

原因是 DND5e_chm 没有同名 Repository Secret，或 Secret 名字拼写错误。重新创建 `WEB_PUBLISH_TOKEN`。

### 16.2 checkout / push 返回 403

优先检查 Fine-grained PAT 是否过期、是否已获组织批准、是否选择了两个目标仓库，以及 `Contents` 是否为 `Read and write`。然后检查目标分支 ruleset / branch protection。

### 16.3 `Could not find exactly one API_BASE assignment`

说明 `5echmweb_search:main/webhelpsearch.htm` 的 API 初始化代码发生了结构变化。不要删除这个检查来强行通过。先看新的搜索页如何定义 API 地址，再修改 `Prepare search template` 中的转换逻辑。目标仍然是让编译器拿到 `($SEARCH_API_BASE$)` 占位符，或者直接让搜索页源码原生使用该占位符。

### 16.4 编译后的搜索页仍然指向 localhost

workflow 的 `Verify compiled search page` 会阻止发布。检查 `search_template` 是否仍指向：

```text
../search-source/webhelpsearch.htm
```

检查 `Prepare search template` 是否成功，以及编译器 `template_renderer.py` 是否仍然实现 `SEARCH_API_BASE` 模板替换。

### 16.5 `default page missing`

通常是 WCP 默认页指向的源文件不存在、文件大小写/路径发生变化，或 WCP 工程本身未更新。检查 `不全书.wcp` 和对应 HTML。

### 16.6 pages 里仍出现 data.js

检查 `Remove search data from site output` 与 `Sync site output` 是否仍存在，同时确认同步没有改回 `rsync --delete` 等其他逻辑。最终还有 `Verify site publish tree` 防线，正常情况下存在 `data.js` 会直接让 Action 失败。

### 16.7 index 已更新，但线上搜索仍是旧数据

这通常不是 DND5e_chm workflow 的问题，而是搜索服务器部署没有从 `5echmweb_search:index` 取得新 `data.js`。当前 `server.js` 读取的是运行目录本地 `data.js`。检查生产部署的 checkout / download / copy 阶段。

### 16.8 ZIP 每次都变化但 data.js 没变

正常 workflow 使用固定 ZIP 时间戳，理论上同一输入应生成稳定压缩包。如果出现变化，检查 Python / ZIP 生成逻辑是否被修改，尤其不要换回普通 `zip` 命令后保留源文件 mtime。

### 16.9 GitHub Pages 文件没有全部删除

这是当前设计。站点同步故意不使用 `--delete`，只覆盖和增加，避免误删 `pages` 中维护者保留的历史文件。若确实需要删除某个已经废弃的站点文件，请单独删除它并提交，或者在 workflow 中对该特定文件加入显式清理。不要轻易全局加回 `--delete`。

---

## 17. 回滚

网站回滚与索引回滚是两个独立操作。

如果网站发布有问题，可以在 `5echm_web:pages` 上把自动构建生成的最新 commit revert，或在确认影响范围后把分支恢复到上一个正常 commit。由于站点是直接 branch deployment，回滚 pages 会回滚网站内容。

如果搜索索引有问题，在 `5echmweb_search:index` 回滚最新索引 commit。因为索引分支只存生成数据，回滚风险相对可控。

注意“网站版本”和“搜索索引版本”最好来自同一个 `DND5e_chm` commit。自动 commit message 会写入源内容短 SHA，例如：

```text
build: publish web from DND5e_chm@abc1234
build: update search index from DND5e_chm@abc1234
```

故障排查或回滚时，应优先选择短 SHA 一致的一对站点与索引版本，避免网页目录与搜索结果指向不同内容版本。

---

## 18. 安全与可靠性设计说明

workflow 设置：

```yaml
concurrency:
  group: 5echm-web-publish
  cancel-in-progress: false
```

目的是避免两个构建同时向 `pages` 和 `index` 写入。不能简单设置为取消进行中的旧任务，因为发布涉及两个仓库；如果一个任务在发布第一个目标后被强制取消，可能造成站点和索引版本不一致。

搜索索引先发布，站点后发布。这样如果索引发布失败，网站不会继续更新；若网站发布最终失败，则最多出现“索引比网页领先一个版本”，一般比“网页已经引用新内容但索引仍旧”更容易恢复。不过 GitHub 原生跨仓库 Git push 不支持真正的两阶段事务，因此仍然无法做到绝对原子发布。需要严格原子性时，应引入 release manifest / version pointer 或统一发布仓库。

所有关键 shell 步骤使用：

```bash
set -euo pipefail
```

任何未处理的命令失败、未定义变量或管道错误都会终止步骤，避免错误状态继续发布。

---

## 19. 当前已知的“源码与文档可能漂移”风险

维护时以实际代码为最高优先级。当前已经观察到一个典型例子：编译器相关说明曾提到搜索服务可以通过 `DATA_JS_PATH` 指定索引，但当前 `5echmweb_search/server.js` 实际仍直接使用 `path.join(__dirname, "data.js")`，代码搜索也未发现 `DATA_JS_PATH`。因此部署决策必须看当前 `server.js` 实现，而不是仅凭旧 README。

同理，如果以后 `wcp2web` 不再自动复制 `site/data.js`，当前 workflow 的 `rm -f` 仍然安全，可以继续保留作为防御性检查；如果模板系统取消 `SEARCH_API_BASE` 占位符，则必须更新搜索模板注入流程。

---

## 20. 不要做的事情

不要把 `data.js` 或 `data.js.zip` 重新提交到 `5echm_web:pages`。不要让搜索索引生成任务向 `5echmweb_search:main` / `master` 写入。不要直接把模板仓库里的旧 `webhelpsearch.htm` 当成线上搜索页。不要把 `WEB_PUBLISH_TOKEN` 写入 YAML。不要为了“同步得更干净”直接给站点 rsync 加 `--delete`，除非已经明确审计 pages 分支中所有必须保留的非构建文件。

也不要把 Action 成功等同于“线上搜索一定更新”。索引在 `index` 分支，而当前 Node 服务读取本地 `data.js`；生产部署是否同步该文件是另一条必须单独验证的链路。

---

## 21. 交接检查清单

新维护者接手时，至少应能回答以下问题：

```text
1. 内容源在哪里？
   DND5e_chm:main

2. 主 WCP 是什么？
   不全书.wcp

3. 编译器在哪里？
   5echm_web_build:main

4. 基础模板在哪里？
   5echm_web_templates:main

5. 新搜索页从哪里来？
   5echmweb_search:main/webhelpsearch.htm

6. 生产搜索 API 是什么？
   https://5echmsearch.kagangtuya.top

7. 网页发布到哪里？
   5echm_web:pages 根目录

8. 搜索索引发布到哪里？
   5echmweb_search:index

9. pages 能否包含 data.js？
   不能

10. main/master 会不会被索引 Action 修改？
    不会；workflow 有显式保护。

11. index 分支没有时怎么办？
    workflow 自动创建 orphan index。

12. 搜索服务器如何拿到 index 数据？
    部署过程必须把 index:data.js 放到 server.js 运行目录；
    当前 server.js 不会自己跨分支读取。
```

如果以上任一答案发生变化，应把 workflow 和本手册视为同一个变更一起更新。

---

## 22. 配套文件

本交接文档应与以下文件同时保存：

```text
.github/workflows/build-web.yml
docs/web-build-handover.md
```

建议未来每次改变仓库职责、分支、搜索 API、构建器输入输出或部署方式时，在 PR 中同时要求更新技术手册，避免自动化逻辑只存在于某位维护者的记忆中。
