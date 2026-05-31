# surge-ruleset-forge

把分散在各处的上游 Surge 规则源,自动**下载、合并、去重、归并、分类**成干净、可订阅的 `.list` 规则集。

[![build](https://github.com/qidewei2004/surge-ruleset-forge/actions/workflows/build.yml/badge.svg)](https://github.com/qidewei2004/surge-ruleset-forge/actions/workflows/build.yml)

## 解决什么问题

Surge 用户常把十几个上游规则集(blackmatrix7、skk.moe、dler-io 等)直接 `RULE-SET` 引用。这带来几个长期痛点:

- **源分散且更新不一**:部分源走 `raw.githubusercontent.com`,国内拉取慢、易失败。
- **规则重复冗余**:不同源覆盖同一服务,大量重叠域名,拖慢匹配。
- **格式不统一**:`.list` 与 `.conf` 混用,夹带 `USER-AGENT`、防盗版哨兵行等噪声。
- **难以维护**:想调整分类、增删源,只能手工编辑,容易出错。

`surge-ruleset-forge` 把这些上游源收敛成一份你自己维护的 `sources.yaml`,一条命令产出标准化规则集,并由 GitHub Actions 每日自动重建——你只需订阅产物 URL。

## 工作流程

```
sources.yaml  →  fetch  →  parse  →  filter  →  dedupe  →  emit  →  dist/*.list
 (你维护)        下载+缓存   解析+清洗   类型过滤   去重+子域归并  带头注释
```

- **fetch**:并发下载,失败指数退避重试,本地缓存兜底,单源失败不中断整体。
- **parse**:剥离注释/参数,丢弃不可复用类型(`USER-AGENT`/`PROCESS-NAME`/逻辑规则),过滤 skk.moe 防盗版哨兵行。
- **dedupe**:精确去重 + 子域归并(`DOMAIN-SUFFIX,a.com` 自动吸收 `x.a.com` 与 `sub.a.com`),显著缩小体积。
- **emit**:输出带头注释(更新时间、各类型计数、上游来源清单)的标准 `.list`。

## 快速开始

```bash
# 安装(推荐 uv)
uv venv && uv pip install -e ".[dev]"

# 构建全部分类到 dist/
forge build

# 忽略缓存强制重新下载
forge build --no-cache

# 查看产物统计
forge stats
```

## 配置 `sources.yaml`

```yaml
defaults:
  keep_types: [DOMAIN, DOMAIN-SUFFIX, DOMAIN-KEYWORD, DOMAIN-WILDCARD, DOMAIN-SET]

categories:
  - output: streaming           # 产出 dist/streaming.list
    desc: 海外流媒体
    sources:
      - https://.../Netflix.list
      - https://.../Disney%20Plus.list
```

每个 `category` 产出一个 `dist/<output>.list`。`keep_types` 控制只保留哪些规则类型(默认仅域名维度,便于放进非 IP 规则层复用)。

## 在 Surge 中订阅

构建产物提交进仓库后,通过 jsdelivr CDN 引用(策略目标按个人 Surge.conf 的策略组示例):

```ini
[Rule]
# 流媒体 / 社交 / AI
RULE-SET,https://fastly.jsdelivr.net/gh/qidewei2004/surge-ruleset-forge@main/dist/streaming.list,机场合集,extended-matching
RULE-SET,https://fastly.jsdelivr.net/gh/qidewei2004/surge-ruleset-forge@main/dist/social.list,国际社区,extended-matching
RULE-SET,https://fastly.jsdelivr.net/gh/qidewei2004/surge-ruleset-forge@main/dist/tiktok.list,TikTok,extended-matching
RULE-SET,https://fastly.jsdelivr.net/gh/qidewei2004/surge-ruleset-forge@main/dist/ai.list,AI,extended-matching
# 开发 / 学术 / 加密货币 / 测速
RULE-SET,https://fastly.jsdelivr.net/gh/qidewei2004/surge-ruleset-forge@main/dist/dev.list,国际基础服务,extended-matching
RULE-SET,https://fastly.jsdelivr.net/gh/qidewei2004/surge-ruleset-forge@main/dist/scholar.list,国际基础服务,extended-matching
RULE-SET,https://fastly.jsdelivr.net/gh/qidewei2004/surge-ruleset-forge@main/dist/crypto.list,PROXY,extended-matching
RULE-SET,https://fastly.jsdelivr.net/gh/qidewei2004/surge-ruleset-forge@main/dist/speedtest.list,SpeedTest,extended-matching
# 游戏
RULE-SET,https://fastly.jsdelivr.net/gh/qidewei2004/surge-ruleset-forge@main/dist/game.list,Game,extended-matching
# 国内服务 / Apple(直连)
RULE-SET,https://fastly.jsdelivr.net/gh/qidewei2004/surge-ruleset-forge@main/dist/cn-media.list,中文内容,extended-matching
RULE-SET,https://fastly.jsdelivr.net/gh/qidewei2004/surge-ruleset-forge@main/dist/apple.list,DIRECT,extended-matching
```

> 走 jsdelivr CDN 而非 raw.githubusercontent.com,国内访问更稳定。
> 当前共 11 个分类、约 4000 条规则,完整列表见 `sources.yaml`。

## 自动更新

`.github/workflows/build.yml` 每日定时运行 `forge build`,若 `dist/` 有变更则自动提交。规则集始终保持新鲜,无需人工介入。

## 开发

```bash
uv run pytest          # 运行测试
```

## License

MIT
