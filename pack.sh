#!/usr/bin/env bash
# ============================================================================
# AIME 应用独立打包脚本
#
# 在模板初始化后，本脚本可独立运行，不依赖 aime-app-devkit 或其他外部工具。
# 完成：前端构建（如有）→ Go 交叉编译（如有）→ 创建发布用 zip 包。
#
# 用法:
#   bash pack.sh [options]
#
# 选项:
#   --skip-build         跳过前端构建，直接使用现有 app/dist
#   --skip-go-build      跳过 Go 编译，仅打包现有二进制
#   --include-source     zip 中包含前端源码（默认排除）
#   --include-go-source  zip 中包含 Go 源码（默认排除，仅打二进制）
#   --go-os <os>         Go 交叉编译目标 GOOS（默认: linux）
#   --go-arch <arch>     Go 交叉编译目标 GOARCH（默认: amd64）
#   --no-strip           保留 Go 二进制符号表（默认 strip）
#   --output <path>      指定输出 zip 路径（默认: 上级目录/<app-name>.zip）
#   -h, --help           显示帮助
# ============================================================================
set -euo pipefail

# --------------- 可配置变量（用户可按需修改） ---------------

# Go 交叉编译目标平台
GO_OS="${GO_OS:-linux}"
GO_ARCH="${GO_ARCH:-amd64}"

# 是否 strip Go 二进制符号表（减小体积）
STRIP_SYMBOLS="${STRIP_SYMBOLS:-true}"

# --------------- 内部变量 ---------------

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$SCRIPT_DIR/app"
FRONTEND_DIR="$APP_DIR/frontend"
SERVER_GO_DIR="$APP_DIR/server-go"
APP_NAME="$(basename "$SCRIPT_DIR")"

SKIP_BUILD=false
SKIP_GO_BUILD=false
INCLUDE_SOURCE=false
INCLUDE_GO_SOURCE=false
OUTPUT=""

# --------------- 参数解析 ---------------

show_help() {
    sed -n '/^# 用法/,/^# ====/{ /^#/s/^# //p }' "$0"
    exit 0
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-build)        SKIP_BUILD=true; shift ;;
        --skip-go-build)     SKIP_GO_BUILD=true; shift ;;
        --include-source)    INCLUDE_SOURCE=true; shift ;;
        --include-go-source) INCLUDE_GO_SOURCE=true; shift ;;
        --go-os)             GO_OS="$2"; shift 2 ;;
        --go-arch)           GO_ARCH="$2"; shift 2 ;;
        --no-strip)          STRIP_SYMBOLS=false; shift ;;
        --output)            OUTPUT="$2"; shift 2 ;;
        -h|--help)           show_help ;;
        *) echo "错误: 未知参数 $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$OUTPUT" ]]; then
    OUTPUT="$(dirname "$SCRIPT_DIR")/${APP_NAME}.zip"
fi

# --------------- 工具函数 ---------------

log_step() { printf "\n[%s] %s\n" "$1" "$2"; }
log_ok()   { printf "  ✓ %s\n" "$1"; }
log_info() { printf "  ℹ %s\n" "$1"; }
log_err()  { printf "  ✗ %s\n" "$1" >&2; }

# --------------- 前端构建 ---------------

build_frontend() {
    if [[ ! -d "$FRONTEND_DIR" ]] || [[ ! -f "$FRONTEND_DIR/package.json" ]]; then
        log_info "无前端项目，跳过"
        return 0
    fi
    if [[ "$SKIP_BUILD" == "true" ]]; then
        log_info "跳过前端构建（--skip-build）"
        return 0
    fi
    bash "$SCRIPT_DIR/build.sh" --mode release --target frontend --frontend-mode local
    log_ok "前端构建完成 → app/dist/"
}

# --------------- Go 编译 ---------------

build_go() {
    if [[ ! -d "$SERVER_GO_DIR" ]]; then
        log_info "无 Go 服务端，跳过"
        return 0
    fi
    if [[ "$SKIP_GO_BUILD" == "true" ]]; then
        log_info "跳过 Go 编译（--skip-go-build）"
        return 0
    fi
    if [[ ! -f "$SERVER_GO_DIR/main.go" ]]; then
        log_info "无 Go 源码，校验并打包已有产物"
        return 0
    fi
    local args=(--mode release --target backend --go-os "$GO_OS" --go-arch "$GO_ARCH")
    if [[ "$STRIP_SYMBOLS" != "true" ]]; then
        args+=(--no-strip)
    fi
    bash "$SCRIPT_DIR/build.sh" "${args[@]}"
    log_ok "Go 编译完成 → app/server-go/bin/server"
}

# --------------- 打包 ZIP ---------------

create_zip() {
    rm -f "$OUTPUT"

    log_info "创建压缩包..."

    # 使用内联 Python 脚本精确控制打包内容，逻辑清晰且跨平台可靠。
    python3 - "$SCRIPT_DIR" "$OUTPUT" "$APP_NAME" "$INCLUDE_SOURCE" "$INCLUDE_GO_SOURCE" << 'PACK_EOF'
import os
import json
import sys
import zipfile
from pathlib import Path

plugin_path = Path(sys.argv[1]).resolve()
output_path = Path(sys.argv[2]).resolve()
app_name = sys.argv[3]
include_source = sys.argv[4] == "true"
include_go_source = sys.argv[5] == "true"

has_go_server = (plugin_path / "app" / "server-go").is_dir()
keep_tools = include_source or include_go_source
ignored = set()
ignore_file = plugin_path / ".appignore"
if ignore_file.is_file():
    for line in ignore_file.read_text().splitlines():
        entry = line.strip().replace("\\", "/")
        if not entry or entry.startswith("#"):
            continue
        while entry.startswith("./"):
            entry = entry[2:]
        entry = entry.strip("/")
        if not entry or any(p in ("", ".", "..") for p in entry.split("/")):
            raise ValueError("Invalid .appignore path")
        ignored.add(entry)
archived = set()

# 永远排除的目录和文件
EXCLUDE_DIRS = {".git", ".idea", "node_modules", "__pycache__", ".aime_build"}
EXCLUDE_FILES = {".DS_Store"}
# 最大包体积: 128 MB
MAX_SIZE = 128 * 1024 * 1024

with zipfile.ZipFile(str(output_path), "w", zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(str(plugin_path)):
        rel_root = Path(root).relative_to(plugin_path)
        rel_root_str = rel_root.as_posix()
        if rel_root_str == ".":
            rel_root_str = ""
        in_skills = rel_root_str.startswith("skills")

        # 过滤目录
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        dirs[:] = [d for d in dirs if (rel_root / d).as_posix() not in ignored]

        # 前端源码排除（不影响 skills/ 下的模板）
        if not include_source and not in_skills:
            dirs[:] = [
                d for d in dirs
                if not (
                    rel_root_str in ("app", "")
                    and d == "frontend"
                    and (plugin_path / rel_root / d / "package.json").exists()
                )
            ]

        # Go 源码目录排除（不影响 skills/ 下的模板）
        if has_go_server and not include_go_source and not in_skills:
            dirs[:] = [
                d for d in dirs
                if not (rel_root_str == "" and (d == "internal" or (d == "tools" and not keep_tools)))
            ]

        for filename in files:
            if filename in EXCLUDE_FILES:
                continue
            if filename.endswith((".pyc", ".pyo")):
                continue

            rel_file = (rel_root / filename).as_posix()
            if rel_file in ignored or rel_file in ("server-go", "app/server-go/.build_stamp"):
                continue
            if rel_file == "build.sh" and not keep_tools:
                continue
            if rel_file.startswith("app/server-go/bin/.server-"):
                continue
            if not include_source and rel_file in ("app/api/api.yaml", "app/api/api.json"):
                continue
            in_template = rel_file.startswith("skills/")
            in_bin = rel_root.name == "bin"

            # Go 文件排除（应用根级别，不影响 bin/ 和 skills/ 模板）
            if has_go_server and not include_go_source and not in_template and not in_bin:
                if filename.endswith(".go") or filename in ("go.mod", "go.sum"):
                    continue

            filepath = Path(root) / filename
            if filepath.resolve() == output_path:
                continue

            arcname = f"{app_name}/{filepath.relative_to(plugin_path).as_posix()}"
            zf.write(str(filepath), arcname)
            archived.add(rel_file)

required = {"app.json"}
config = json.loads((plugin_path / "app.json").read_text())
if has_go_server:
    required.update({".template_meta.json", "app/server-go/start.sh", "app/server-go/bin/server"})
    if not os.access(plugin_path / "app/server-go/bin/server", os.X_OK):
        output_path.unlink(missing_ok=True)
        raise ValueError("Missing executable release binary")
if config.get("ui_provider") or (plugin_path / "app/frontend/package.json").is_file():
    required.add("app/dist/index.html")
for service in config.get("services", []):
    for prefix in service.get("upload_to_cdn", []) or []:
        rel = Path(prefix)
        if rel.is_absolute() or ".." in rel.parts or not (plugin_path / rel).exists():
            output_path.unlink(missing_ok=True)
            raise ValueError("Missing or invalid CDN resource path")
        path = plugin_path / rel
        resources = [path] if path.is_file() else [p for p in path.rglob("*") if p.is_file()]
        required.update(p.relative_to(plugin_path).as_posix() for p in resources)
if not required.issubset(archived):
    output_path.unlink(missing_ok=True)
    raise ValueError("Missing runtime files: " + ", ".join(sorted(required - archived)))

# 体积检查
size = output_path.stat().st_size
if size > MAX_SIZE:
    size_mb = size / (1024 * 1024)
    limit_mb = MAX_SIZE // (1024 * 1024)
    print(f"  ✗ ZIP 包 {size_mb:.1f} MB 超过 {limit_mb} MB 限制", file=sys.stderr)
    output_path.unlink()
    sys.exit(1)

print(f"  ✓ {size / 1024 / 1024:.1f} MB")
PACK_EOF

    if [[ $? -ne 0 ]]; then
        log_err "打包失败"
        exit 1
    fi

    log_ok "输出: $OUTPUT"
}

# --------------- 主流程 ---------------

main() {
    echo "📦 打包应用: ${APP_NAME}"
    echo "   路径: ${SCRIPT_DIR}"
    echo "   输出: ${OUTPUT}"
    if [[ -d "$SERVER_GO_DIR" ]]; then
        echo "   Go 目标: ${GO_OS}/${GO_ARCH} (strip=${STRIP_SYMBOLS})"
    fi

    log_step "1/3" "构建前端"
    build_frontend

    log_step "2/3" "编译 Go 服务"
    build_go

    log_step "3/3" "创建 ZIP 压缩包"
    create_zip

    echo ""
    echo "✅ 打包完成: ${OUTPUT}"
}

main
