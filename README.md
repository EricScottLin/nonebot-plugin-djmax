# nonebot-plugin-djmax

NoneBot2 插件：**DJMAX Respect V 查分**。

数据来自 [V-Archive](https://v-archive.net/)，出图基于
[djmax_bests_generate](https://github.com/SoreHait/djmax_bests_generate)（MIT）。

## 功能

| 命令 | 说明 |
| --- | --- |
| `dj bind <V-Archive ID>` | 绑定查分账号（填 V-Archive 注册 ID，不是游戏 ID） |
| `dj unbind` | 解绑 |
| `dj b100 <4/5/6/8>` | B100 分表 |
| `dj list <键数> <等级\|sc等级>` | 指定等级分表 |
| `dj pack <键数> <NM/HD/MX/SC> <曲包>` | 曲包分表 |
| `dj new <键数> <NM/HD/MX/SC>` | 新曲分表 |
| `dj pp <键数>` | Perfect Play 分表 |
| `dj max <键数>` | 理论值 B100 |
| `dj listdlc` | 曲包代码列表 |
| `dj song [键数] <歌曲>` | 曲目信息：封面、曲名、歌手、曲包，以及全部键数定数 |
| `dj info <键数> <歌曲>` | 个人成绩：难度 / 等级 / 定数 / 成绩 / DJPower，带 PP、MC 标记 |

`dj` 与 `djmax` 都可用；已绑定的账号可省略 ID，例如 `dj <ID> b100 4`。

「歌曲」可以是曲名、歌手或 songid，支持模糊匹配；命中多首时返回带 songid 的候选列表。

## 等级与定数有什么区别

DJMAX 一首歌最多有 16 张谱面（4B/5B/6B/8B × NM/HD/MX/SC），每张谱面有两个不同的难度数字：

- **等级（Level）**：游戏内显示的数字，1~15，官方给的，比较粗。同一等级内的谱面难度可以差很多。
- **定数（Constant）**：精确到小数点后一位的难度值，用来区分同等级内部的强度。

两者经常不一致。例如 TOXIC 的 4B MX 等级 10、SC 等级 9，但 SC 的定数 9.3 明显高于同键数 MX
（该谱面暂无定数）。`dj song` 默认把 16 张谱面的定数一次列全，加键数（`dj song 4B 歌名`）
则只看该键数。

### 定数从哪来

**定数不是官方数据，NEOWIZ 从未公布过。** 本项目用的是 [V-Archive](https://v-archive.net)
的定数，其来源是 DCInside「디제이맥스 리스펙트 V 마이너 갤러리」玩家投票产生的
**非官方难度表（서열표）**，V-Archive 借用了这张表。据 V-Archive 自己的说明，排序基准是：

> 正配置（原谱，非 mirror）、**99.00% 准确率 + MAX COMBO** 达成时的难度。

也就是说，定数衡量的是「打到 99% + 全连」这件事有多难，**不代表**满分（100%）的难度。
所以定数相同不代表满分难度相同——有的谱面 99% 容易但最后 1% 极难（判定难），
这类谱面定数会偏低。

### 怎么看定数

定数与 V-Archive 的 `rating` 是一一对应的固定映射（1.1 → 140、16.2 → 206，共 47 档），
`rating` 只是定数的另一种单位，不是独立指标：

| 定数 | rating | 定数 | rating | 定数 | rating |
|---|---|---|---|---|---|
| 1.1 | 140 | 7.1 | 163 | 12.3 | 190 |
| 2.1 | 146 | 8.1 | 166 | 13.3 | 194 |
| 3.1 | 151 | 9.1 | 170 | 14.3 | 198 |
| 4.1 | 154 | 10.1 | 176 | 15.3 | 202 |
| 5.1 | 157 | 11.1 | 182 | 16.2 | 206 |
| 6.1 | 160 | — | — | — | — |

实用读法：

- **定数是给「冲分」用的**：同样打 99%，定数高的谱面给出的 rating 更高，所以冲 rank 要挑定数高的打。
- **定数缺失表示「还没人投票」**：曲库共 12468 张谱面，只有 48% 有定数（5992 张）。
  新歌、冷门 DLC、以及大部分 NM/HD 难度通常没有。卡片上这类谱面显示「—」。
- **不要跨键数比较**：4B 和 8B 的定数各自独立，8B 定数普遍更高，不代表更值得练。

## 安装

```bash
nb plugin install nonebot-plugin-djmax
# 或
pip install nonebot-plugin-djmax
```

在 `bot.py` 中加载：

```python
nonebot.load_plugin("nonebot_plugin_djmax")
```

## 素材（必读）

出图需要 Respect 字体（约 51MB）和谱面覆盖素材（约 4.8MB），**这些不进仓库**。
首次出图前需要让插件拿到素材，三种方式任选其一：

### 1. 从 CDN 下载（推荐）

设置素材包地址，插件会自动下载到数据目录并缓存：

```dotenv
DJMAX_ASSETS_URL=https://your-cdn.example.com/djmax-assets-v1.tar.gz
```

素材包需解压后得到下列结构（`.zip` 与 `.tar.gz` 都支持）：

```
fonts/Respect_bd.ttf
fonts/Respect_rg.ttf
fonts/Respect_lt.ttf
bests_generator/assets/...
scorelist_generator/assets/...
```

### 2. 指向本地目录

已经有一份素材时直接指过去，避免重复下载：

```dotenv
DJMAX_ASSETS_DIR=/path/to/djmax-assets
```

### 3. 自建素材包

从上游仓库取素材后打包：

```bash
git clone https://github.com/SoreHait/djmax_bests_generate
cd djmax_bests_generate/djmax_bests/generators
tar -czf djmax-assets-v1.tar.gz fonts bests_generator/assets scorelist_generator/assets
```

把生成的包传到任意静态托管（对象存储、CDN、Nginx 均可），再设置 `DJMAX_ASSETS_URL`。

> 素材中的 Respect 字体是 DJMAX 游戏字体，版权归 Neowiz / Neowiz MUCA 所有。
> 本项目不在仓库中分发它们，请自行评估在你环境下的使用条件。

## 配置

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `djmax_group_ids` | `[]` | 允许使用的群号白名单；为空表示不限 |
| `djmax_private` | `true` | 是否允许私聊使用 |
| `djmax_record_ttl` | `180` | 单曲成绩缓存秒数 |
| `djmax_assets_dir` | `""` | 本地素材目录 |

### 环境变量

| 变量 | 说明 |
| --- | --- |
| `DJMAX_ASSETS_URL` | 素材包下载地址 |
| `DJMAX_ASSETS_DIR` | 本地素材目录（优先级高于下载） |
| `DJMAX_DATA_DIR` | 数据目录（缓存、封面、绑定） |

## 数据与缓存

- 绑定关系、曲库缓存、曲绘都写在 NoneBot 数据目录（`nonebot_plugin_localstore`），
  插件目录只读也能正常运行。
- 曲库（846 首）与曲包表首次查询时下载并缓存；单曲成绩有 180 秒 TTL。

## 目录

```
qqbot_djmax/
├── __init__.py          命令注册与分发
├── config.py            配置模型
├── bind_store.py        V-Archive ID 绑定存储
├── assets.py            素材下载与定位
├── render.py            单曲信息卡 / 单曲成绩卡（Pillow）
└── djmax_bests/         出图与数据层（vendored，见 VENDOR_NOTICE.md）
    ├── api_handler.py   V-Archive API
    ├── models.py        曲库与成绩模型
    ├── song_index.py    曲库检索
    ├── single_query.py  单曲数据组装
    ├── generate.py      分表出图入口
    └── generators/      分表图片绘制
```

## 致谢

- 出图库 [djmax_bests](qqbot_djmax/djmax_bests/) vendored 自 **SoreHait** 的
  [djmax_bests_generate](https://github.com/SoreHait/djmax_bests_generate)（MIT）。
  分表图片的绘制代码来自该项目，版权归原作者所有，详见
  [VENDOR_NOTICE.md](qqbot_djmax/djmax_bests/VENDOR_NOTICE.md)。
- 单曲信息卡与单曲成绩卡为本项目独立实现。
- 数据来自 [V-Archive](https://v-archive.net/)。

## 许可

[MIT](LICENSE)。`qqbot_djmax/djmax_bests/` 保留上游 MIT 版权声明。
