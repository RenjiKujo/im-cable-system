"""docs/ と実装（src/）の、機械的に検出できる不整合を検証する。

決定論的に判定できる 5 種類だけを対象にする。

1. **リンク切れ**: 相対 Markdown リンクの実在確認。
2. **バッククォートパスの実在**: `` `src/...` `` `` `docs/...` `` のように書かれた
   リポジトリ内パス参照の実在確認。
3. **ディレクトリツリー図の整合**: フェンスコードブロック中の ``├──`` / ``└──`` を含む
   ツリー図と、対応する実ディレクトリの直下エントリ（深さ 1）を突き合わせる。
4. **識別子の実在**: docs 内の `` `CamelCase` `` 表記が ``src/`` に定義／import されて
   いるかの確認。クラス・IF のリネームや削除の取り残しを検出する（パス参照ではないため
   2. では捕まらない）。
5. **ルール import の網羅**: `.cursor/rules/*.mdc` の `alwaysApply: true` と、
   `CLAUDE.md` の `@` import 行を突き合わせる。Cursor は前者を自動で読むが
   Claude Code は後者しか読まないため、両者がずれるとルールが片方でだけ効く。

## 検査対象の範囲

| 検査 | `docs/**/*.md` | メタ文書（``_iter_meta_files``） |
|---|---|---|
| 1. リンク切れ | ✅ | ✅ |
| 2. パス参照の実在 | ✅ | ✅ |
| 3. ツリー図 | ✅ | — |
| 4. 識別子 | ✅ | — |
| 5. ルール import | — | ✅（`CLAUDE.md` ↔ `.cursor/rules/` のみ） |

メタ文書は `README.md` / `CLAUDE.md` / `.cursor/rules/` / `.cursor/agents/` /
`.cursor/skills/` / `.claude/hooks/README.md`。**ルール・エージェント定義自身が
docs のパスを名指ししている**ため、
docs の移動・改名でこれらが静かに切れる（実例: 「docs/rules を conventions へ移す」変更）。
切れたルールは「読むべき文書を読めなかった」ことに気づかせないまま劣化するので、
docs と同じ 1.・2. の網に載せる。3.・4. を掛けないのは、メタ文書のツリー図・
`CamelCase` は説明用の例示を含み誤検知になるため。

**`src/` を編集したときも回す**。クラスのリネームは docs を触らずに docs を壊すため、
「docs を編集したときだけ」では最頻の drift を取り逃がす。

意味的な不整合（正本と再掲の食い違い、層をまたいだコピペ、陳腐化した設計判断など）は
検出できない。それらは `pj-review-docs` エージェントが見る。
"""

from __future__ import annotations

import builtins
import re
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_DOCS_DIR = _REPO_ROOT / "docs"
_SRC_DIR = _REPO_ROOT / "src"
_APPS_DIR = _REPO_ROOT / "apps"
_CLAUDE_MD = _REPO_ROOT / "CLAUDE.md"
_RULES_DIR = _REPO_ROOT / ".cursor" / "rules"

# 識別子チェックの対象外ディレクトリ。
# conventions/ は「特定プロジェクトに限定されない一般原則」を書く場所で、
# 説明用の架空クラス名（ModelEvaluator など）を意図的に含むため検査しない
# （docs/conventions/README.md の位置づけを参照）。
_IDENT_EXCLUDED_DIRS = ("conventions",)

# 実装識別子ではないが docs に `バッククォート` 付きで現れる語。
# 増やすときは「なぜ実装に無くてよいか」をコメントで残す（無条件の握りつぶしを防ぐ）。
_CONCEPT_NAMES = frozenset(
    {
        # 実行モード名。具体クラスは接尾辞付きで存在する（EstimateParamsPipeline 等）。
        "EstimateParams",
        "ForwardByCartesianGrid",
        "ForwardByOperatingPoints",
        # モード別の型の総称（ForwardJobSpecs / EstimateParamsJobSpec などを指す）。
        "JobSpec",
        "JobSpecs",
        "LoadedData",
        # 標準ライブラリの型を概念として参照しているもの。
        "Handler",  # stdlib logging.Handler
        # pydantic の外部クラス。apps/web/api/schemas.py で実際に import
        # されているが、6 個も import するため 1 行に収まらず括弧付き複数行
        # import になっており、_collect_src_symbols の正規表現（1 行の
        # `import ...` しか見ない）が拾えない。
        "BaseModel",
        # 命名規約のラベル・数式記号（識別子ではない）。
        "UPPER_SNAKE",
        "UPPER_SNAKE_CASE",
        "P_out",
    }
)

# docs 内で「リポジトリ内パスらしきもの」とみなすバッククォート表記のプレフィックス。
_PATH_PREFIXES = (
    "src/",
    "docs/",
    "tests/",
    "examples/",
    "scripts/",
    "runner/",
    "apps/",
    ".cursor/",
    ".claude/",
)

# 1 件のファイルを指さない表記。`<mode>` や `1〜5_*.md` のような伏せ字は人向けの
# 略記なので実在確認しない。`*` / `?` だけを含むものは glob として扱い、
# 「1 件も一致しない」ことだけを不整合とする（`runner/run_*.py` が空になる等を拾う）。
_PLACEHOLDER_CHARS = ("<", ">", "〜", "{", "}")
_GLOB_CHARS = ("*", "?")

# 参照されていても実在しなくてよいパス。いずれも gitignore 対象のローカル専用
# ファイルで、「stage しない」対象として名指しされる（存在しないのが正常）。
_OPTIONAL_PATHS = frozenset(
    {
        ".claude/settings.local.json",
        ".claude/usage-notes.md",
    }
)

_LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_BACKTICK_PATH_PATTERN = re.compile(r"`([^`\n]+)`")
_TREE_FENCE_PATTERN = re.compile(r"```(?:text)?\n(.*?```)", re.DOTALL)
_TREE_ROOT_LINE_PATTERN = re.compile(r"^([A-Za-z0-9_./\-]+/)\s*(?:#.*)?$")
# docs 中の `CamelCase` 表記（クラス・IF 名らしきもの）。
# 4 文字以上・大文字始まり。全大文字（Enum 値）は _collect_src_symbols 側で拾う。
_IDENT_PATTERN = re.compile(r"`([A-Z][A-Za-z0-9_]{3,})`")
# os.environ から読む環境変数名。docs は変数名を名指しするが、実装側は
# 文字列リテラルなので定義・import の走査では拾えない。
_ENV_VAR_PATTERN = re.compile(
    r"""os\.environ(?:\.get)?[(\[]\s*["']([A-Z][A-Z0-9_]*)["']"""
)
# ツリー行の子エントリ（深さ 1）: "├── name/" や "└── name" の name 部分。
_TREE_CHILD_PATTERN = re.compile(r"^[│ ]{0,4}[├└]── ([A-Za-z0-9_.\-]+/?)")
# CLAUDE.md の import 行: 行頭の `@<リポジトリ相対パス>` のみ。
_IMPORT_PATTERN = re.compile(r"^@(\S+)[ \t]*$", re.MULTILINE)
# `.mdc` 冒頭の YAML frontmatter と、その中の `alwaysApply: true`。
_FRONTMATTER_PATTERN = re.compile(
    r"\A---\r?\n(.*?)\r?\n---\r?$", re.DOTALL | re.MULTILINE
)
_ALWAYS_APPLY_PATTERN = re.compile(
    r"^alwaysApply:[ \t]*true[ \t]*$", re.MULTILINE
)


@dataclass(frozen=True)
class _Finding:
    """1 件の不整合。"""

    file: Path
    line: int
    detail: str

    def format(self) -> str:
        return f"{self.file.relative_to(_REPO_ROOT)}:{self.line} {self.detail}"


def _iter_doc_files() -> list[Path]:
    return sorted(_DOCS_DIR.rglob("*.md"))


def _iter_meta_files() -> list[Path]:
    """docs/ の外にあり、docs/ や src/ のパスを名指しする文書を集める。

    ルート README とエージェント運用の正本（`.cursor/`）。`.claude/` のうち
    `agents/` と `skills/` は `.cursor/` への symlink なので辿らない
    （同じ実体を二重に報告しないため）。`hooks/README.md` は symlink ではない
    実体ファイルで、`.cursor/` 配下のパスを名指しするため対象に含める。
    """
    paths = [
        _REPO_ROOT / "README.md",
        _REPO_ROOT / "CLAUDE.md",
        _REPO_ROOT / ".claude" / "hooks" / "README.md",
        *(_REPO_ROOT / ".cursor" / "rules").glob("*.mdc"),
        *(_REPO_ROOT / ".cursor" / "agents").glob("*.md"),
        *(_REPO_ROOT / ".cursor" / "skills").glob("*/SKILL.md"),
    ]
    return sorted(p for p in paths if p.is_file())


def _iter_linked_files() -> list[Path]:
    """リンク切れ・パス参照の検査対象（docs/ とメタ文書）。"""
    return [*_iter_doc_files(), *_iter_meta_files()]


def _always_apply_rules() -> list[Path]:
    """`alwaysApply: true` を宣言している `.cursor/rules/*.mdc`。

    Cursor はこの宣言を見て自動で読み込む。frontmatter が無い、または宣言が
    無いファイルは対象外（Cursor 側でも自動適用されないため）。
    """
    rules: list[Path] = []
    for mdc in sorted(_RULES_DIR.glob("*.mdc")):
        matter = _FRONTMATTER_PATTERN.match(mdc.read_text(encoding="utf-8"))
        if matter is not None and _ALWAYS_APPLY_PATTERN.search(matter.group(1)):
            rules.append(mdc)
    return rules


def _line_of(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _assert_no_findings(findings: list[_Finding], header: str) -> None:
    """検出結果が空であることを、該当箇所付きのメッセージで表明する。"""
    assert not findings, "{}: {} 件\n{}".format(
        header,
        len(findings),
        "\n".join(f"  {f.format()}" for f in findings),
    )


def _collect_src_symbols() -> set[str]:
    """``src/`` と ``apps/`` で定義または import されている名前を集める。

    定義（class / def / 代入・TypeVar・Enum メンバー）に加えて import 名も含める。
    docs が ``DataFrame`` や ``Figure`` のような外部ライブラリ型に言及するのは
    正当なため、それらを未定義として誤検知しないようにする。``apps/`` を含めるのは、
    ``docs/apps/web/`` が ``JobRecord`` 等 apps 側の識別子に言及するため。

    ``os.environ`` から読む環境変数名も拾う。docs は利用者が設定する変数名を
    名指しするが、実装側では文字列リテラルなので定義・import のどちらにも
    現れない。許可リストに積むと「docs が名前を間違えても通る」ため、
    実際に読んでいる名前だけを正とする。
    """
    symbols: set[str] = set()
    for py in (*_SRC_DIR.rglob("*.py"), *_APPS_DIR.rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        text = py.read_text(encoding="utf-8")
        symbols |= set(
            re.findall(r"^\s*(?:class|def)\s+([A-Za-z_]\w*)", text, re.M)
        )
        # 代入・型付き代入。インデントの有無を問わない
        # （Enum メンバー・dataclass フィールド・モジュール定数・TypeVar を含める）。
        symbols |= set(re.findall(r"^\s*([A-Za-z_]\w*)\s*[:=][^=]", text, re.M))
        # import 名（as 別名を含む）。
        symbols |= set(
            re.findall(r"^\s*(?:from\s+[\w.]+\s+)?import\s+(.+)$", text, re.M)
        )
        # os.environ.get("NAME") / os.environ["NAME"] の NAME。
        symbols |= set(_ENV_VAR_PATTERN.findall(text))
    # "a, b as c" 形式をばらす。
    flat: set[str] = set()
    for item in symbols:
        for part in re.split(r"[,\s]+", item):
            name = part.strip("()")
            if name and re.fullmatch(r"[A-Za-z_]\w*", name):
                flat.add(name)
    return flat


def _parse_tree_block(block: str) -> tuple[Path, list[str]] | None:
    """フェンスブロックからルートパスと深さ1の子エントリ名を抽出する。"""
    lines = block.splitlines()
    if not lines:
        return None
    root_match = _TREE_ROOT_LINE_PATTERN.match(lines[0].strip())
    if root_match is None:
        return None
    root_path = (_REPO_ROOT / root_match.group(1)).resolve()
    if not root_path.is_dir():
        return None

    children: list[str] = []
    for line in lines[1:]:
        if line.strip() == "```":
            break
        # 深さ1のみを対象にする（先頭のツリー罫線が1階層分だけの行）。
        if line.startswith(("├── ", "└── ")):
            child_match = _TREE_CHILD_PATTERN.match(line)
            if child_match:
                children.append(child_match.group(1).rstrip("/"))
    return root_path, children


class TestDocsConsistency:
    """docs/ と実装の機械的な整合性。"""

    def test_no_broken_links(self) -> None:
        """docs・メタ文書の相対 Markdown リンクが指すファイルが実在する。"""
        findings: list[_Finding] = []
        for md in _iter_linked_files():
            text = md.read_text(encoding="utf-8")
            for m in _LINK_PATTERN.finditer(text):
                target = m.group(1).split("#")[0].strip()
                if not target or target.startswith(
                    ("http://", "https://", "mailto:")
                ):
                    continue
                if not (md.parent / target).resolve().exists():
                    findings.append(
                        _Finding(
                            md,
                            _line_of(text, m.start()),
                            f"-> {target}（実在しない）",
                        )
                    )
        _assert_no_findings(findings, "リンク切れ")

    def test_backtick_paths_exist(self) -> None:
        """`` `src/...` `` 等のバッククォートパス参照が実在する。"""
        findings: list[_Finding] = []
        for md in _iter_linked_files():
            text = md.read_text(encoding="utf-8")
            for m in _BACKTICK_PATH_PATTERN.finditer(text):
                candidate = m.group(1).strip()
                if not candidate.startswith(_PATH_PREFIXES):
                    continue
                # モジュールパス表記や末尾の説明混入を弾く簡易フィルタ。
                path_part = candidate.split()[0].rstrip(":,;、。")
                if not path_part.startswith(_PATH_PREFIXES):
                    continue
                if path_part in _OPTIONAL_PATHS:
                    continue
                if any(c in path_part for c in _PLACEHOLDER_CHARS):
                    continue
                if any(c in path_part for c in _GLOB_CHARS):
                    if not any(_REPO_ROOT.glob(path_part)):
                        findings.append(
                            _Finding(
                                md,
                                _line_of(text, m.start()),
                                f"`{path_part}` に一致するファイルが無い",
                            )
                        )
                    continue
                if not (_REPO_ROOT / path_part).resolve().exists():
                    findings.append(
                        _Finding(
                            md,
                            _line_of(text, m.start()),
                            f"`{path_part}` が実在しない",
                        )
                    )
        _assert_no_findings(findings, "パス参照の不在")

    def test_tree_diagrams_match_filesystem(self) -> None:
        """ディレクトリツリー図が実ディレクトリと一致する。"""
        findings: list[_Finding] = []
        for md in _iter_doc_files():
            text = md.read_text(encoding="utf-8")
            for m in _TREE_FENCE_PATTERN.finditer(text):
                block = m.group(1)
                if "├──" not in block and "└──" not in block:
                    continue
                parsed = _parse_tree_block(block)
                if parsed is None:
                    continue
                root_path, doc_children = parsed
                actual = {p.name for p in root_path.iterdir()}
                line = _line_of(text, m.start())
                findings.extend(
                    _Finding(
                        md,
                        line,
                        f"ツリー図の {root_path.relative_to(_REPO_ROOT)}/{name} "
                        "が実ディレクトリに存在しない",
                    )
                    for name in doc_children
                    if name not in actual
                )
        _assert_no_findings(findings, "ツリー図の不一致")

    def test_identifiers_exist_in_src(self) -> None:
        """docs 内の `` `CamelCase` `` 識別子が実装に存在する。"""
        known = _collect_src_symbols() | set(dir(builtins)) | _CONCEPT_NAMES
        findings: list[_Finding] = []
        for md in _iter_doc_files():
            rel_parts = md.relative_to(_DOCS_DIR).parts
            if rel_parts and rel_parts[0] in _IDENT_EXCLUDED_DIRS:
                continue
            text = md.read_text(encoding="utf-8")
            findings.extend(
                _Finding(
                    md,
                    _line_of(text, m.start()),
                    f"`{m.group(1)}` が src/ に定義も import もされていない",
                )
                for m in _IDENT_PATTERN.finditer(text)
                if m.group(1) not in known
            )
        _assert_no_findings(findings, "識別子の不在")


class TestRuleImportCoverage:
    """Cursor のルールと `CLAUDE.md` の `@` import の対応。

    Cursor は `.cursor/rules/*.mdc` の `alwaysApply: true` を自動で読むが、
    Claude Code は `CLAUDE.md` に手書きされた `@` 行しか読まない。片方だけを
    更新するとルールが Cursor でだけ効き、Claude Code では黙って無視される。
    どちらの方向にも落ちうるので、集合の両側を突き合わせる。
    """

    def test_always_apply_rules_are_imported(self) -> None:
        """`alwaysApply: true` のルールがすべて `CLAUDE.md` から import されている。"""
        imported = {
            m.group(1)
            for m in _IMPORT_PATTERN.finditer(
                _CLAUDE_MD.read_text(encoding="utf-8")
            )
        }
        findings = [
            _Finding(
                _CLAUDE_MD,
                1,
                f"@{rel} の import が無い（Cursor では効くが Claude Code では読まれない）",
            )
            for rule in _always_apply_rules()
            if (rel := rule.relative_to(_REPO_ROOT).as_posix()) not in imported
        ]
        _assert_no_findings(findings, "CLAUDE.md の import 漏れ")

    def test_imports_point_to_existing_files(self) -> None:
        """`CLAUDE.md` の `@` import 先が実在する。

        `@` 行は Markdown リンクでもバッククォート表記でもないため、
        `test_no_broken_links` / `test_backtick_paths_exist` では捕まらない。
        """
        text = _CLAUDE_MD.read_text(encoding="utf-8")
        findings = [
            _Finding(
                _CLAUDE_MD,
                _line_of(text, m.start()),
                f"@{m.group(1)} が実在しない",
            )
            for m in _IMPORT_PATTERN.finditer(text)
            if not (_REPO_ROOT / m.group(1)).exists()
        ]
        _assert_no_findings(findings, "CLAUDE.md の import 先の不在")
