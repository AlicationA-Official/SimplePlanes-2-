# 工具说明

这些脚本用于**在游戏更新后找出新增的未译文本**，以及校验词表完整性。
纯 Python 标准库实现，无需安装任何依赖（Windows 上建议 `set PYTHONIOENCODING=utf-8`，否则控制台会因为 GBK 编码报错）。

所有脚本顶部的路径常量默认指向本机游戏目录，移植到别的机器时改一下即可：

```python
MANAGED = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\Managed'
ASSETS  = r'D:\SteamLibrary\steamapps\common\SimplePlanes 2\SimplePlanes 2_Data\resources.assets'
```

---

## 底层库

| 文件 | 作用 |
|---|---|
| `clrmeta.py` | 纯 Python 的 PE / CLR 元数据解析器：读 TypeDef / MethodDef / TypeRef / MemberRef、提取 `#US` 用户字符串堆、反汇编方法 IL 并还原 token。其它脚本大多依赖它。 |

## 缺口扫描（游戏更新后跑这些）

| 文件 | 目标 | 说明 |
|---|---|---|
| `extract_parts.py` | 零件 | 从 `resources.assets` 解析 `<DesignerPart name="…" description="…">`，输出未翻译的 `名称` 与 `名称\n描述` |
| `check_headers.py` | 零件分组标题 | 解析 part XML 的 `header="…"` 属性并比对词表 |
| `check_all_parts.py` | 零件（全文件） | 跨全部资源文件统计 `DesignerPart`，确认没有漏扫的文件 |
| `extract_inputs.py` | 控制项 | 从 Rewired 输入数据里抽取动作显示名；同时列出带 `[占位符]` 的 tooltip |
| `extract_ui_xml.py` | UI 模板 | 从 `resources.assets` 抽出 77 个数据驱动 UI XML 到 `data/ui_xml/` |
| `diff_ui_xml.py` | UI 文案 | 比对 UI XML 的 `text=`/`tooltip=` 属性与词表 |
| `scan_utf16.py` | 程序集界面文本 | **按 UTF-16 文本流扫描** `Game.dll` 等（Tip 这类文本不在 `#US` 堆里，ASCII 搜索找不到） |
| `sweep_tips_tooltips.py` | 说明句 / Tip | 按句式特征抽取设置说明句与提示句 |
| `extract_tips.py` | Tip 全量 | 定位 `Game.dll` 里连续的 Tip 句子数组（运行时拼 `"Tip: " + 句子`） |
| `region_sweep.py` | 指定区域 | 扫描 `Game.dll` 某个偏移区间的 UI 字符串（定位已知文本的邻居） |
| `final_gap_sweep.py` | 全量（噪声较多） | 全 `#US` 堆比对，会产生大量日志文本噪声，仅作参考 |

## 构建与生成

| 文件 | 作用 |
|---|---|
| `build_patch.py` | 本补丁使用的构建脚本（工作区布局）。源码包内的 `build.py` 是它的自包含版本。 |
| `gen_placeholder_rules.py` | 自动为 `…\nShortcut: [键位]` 一族生成"未设置"词条 + 动态前缀规则（中文标签从原词表反查） |
| `translate_parts.py` | 由零件译文表 + 精确英文原文组装 122 条零件词条（避免手抄长描述出错） |

## 辅助/一次性脚本

| 文件 | 作用 |
|---|---|
| `build_string_inventory.py` | 导出英文候选文案清单 CSV（含引用它的方法名，便于判断语境） |
| `classify_gaps.py` / `final_filter.py` / `build_to_translate.py` | 缺口分类与过滤流水线（分出可安全建键的条目） |
| `us_strings.py` / `fontscan.py` | `#US` 堆导出 / Unity 资源内嵌字体识别 |
| `locate_probes.py` / `dump_inputdata.py` / `find_headers.py` / `tip_neighborhood.py` | 定位特定文本来源的一次性排查脚本 |

---

## 典型工作流

```powershell
set PYTHONIOENCODING=utf-8

# 1. 游戏更新后，找新增缺口
python tools\extract_parts.py        # 零件
python tools\check_headers.py        # 分组标题
python tools\extract_inputs.py       # 控制项
python tools\scan_utf16.py           # 程序集界面文本 / Tip

# 2. 翻译后写入 src\gap_fill_*.json

# 3. 重建并安装
python build.py
Copy-Item .\build\zh-CN.json "…\BepInEx\plugins\SimplePlanes2Translation\translations\zh-CN.json" -Force

# 4. 游戏内按 F2 热重载验证
```

> 静态扫描拿不到的文本（部分 tooltip、设置页说明）用插件的采集模式补：
> `settings.json` 里 `Mode` 改 `hybrid`、`LogMissingTexts` 改 `true`，进游戏走一遍界面，
> 读插件目录的 `captured-texts.json`（含场景名与控件路径，判断语境用），完事改回 `translate`。
