#!/usr/bin/env python3
"""Build the standard App without starting it or contacting the publishing API."""
from __future__ import annotations

import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "utils"))
from frontend_runtime import pnpm_command, resolve_pnpm

SDK = "@aime-plugin/browser-sdk"
SEMVER = re.compile(r"(\d+)\.(\d+)\.(\d+)")
WORKSPACE = "packages:\n  - .\nallowBuilds:\n  esbuild: true\n"


def execute(args, *, cwd, env=None, timeout=120, capture=False):
    own_group = os.environ.get("AIME_BUILD_PROCESS_GROUP") != "1"
    with subprocess.Popen(args, cwd=cwd, env=env, start_new_session=own_group, text=True,
                          stdout=subprocess.PIPE if capture else None,
                          stderr=subprocess.PIPE if capture else None) as proc:
        try:
            out, err = proc.communicate(timeout=timeout)
        except BaseException:
            if own_group:
                try:
                    os.killpg(proc.pid, signal.SIGTERM)
                except ProcessLookupError:
                    pass
            else:
                proc.terminate()
            try:
                proc.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                if own_group:
                    os.killpg(proc.pid, signal.SIGKILL)
                else:
                    proc.kill()
                proc.communicate()
            raise
        return subprocess.CompletedProcess(args, proc.returncode, out, err)


def run(args, *, cwd=ROOT, env=None, timeout=120):
    print("[build] " + " ".join(map(str, args[:3])), flush=True)
    execute(args, cwd=cwd, env=env, timeout=timeout).check_returncode()


def prepare_frontend(frontend):
    workspace = frontend / "pnpm-workspace.yaml"
    managed = {
        ("allowBuilds:", "esbuild: false"), ("allowBuilds:", "esbuild: true"),
        ("packages:", "- .", "allowBuilds:", "esbuild: false"),
        ("packages:", "- .", "allowBuilds:", "esbuild: true"),
    }
    if not workspace.exists() or tuple(
        line.strip() for line in workspace.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ) in managed:
        workspace.write_text(WORKSPACE)
    modules = frontend / "node_modules"
    if modules.exists() and not (modules / ".modules.yaml").exists():
        shutil.rmtree(modules)


def update_sdk(frontend, version):
    path = frontend / "package.json"
    package = json.loads(path.read_text())
    section = next((s for s in ("dependencies", "devDependencies") if SDK in package.get(s, {})), "")
    if not section and not any(
        SDK in p.read_text(errors="replace") for p in (frontend / "src").rglob("*")
        if p.is_file() and p.suffix in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
    ):
        return False
    try:
        result = execute(pnpm_command(frontend, version, "view", SDK, "version", "--json"),
                         cwd=frontend, capture=True, timeout=30)
        latest = SEMVER.search(result.stdout) if result.returncode == 0 else None
    except (OSError, subprocess.TimeoutExpired):
        latest = None
    if not latest:
        print("[build] WARN: SDK version lookup failed; keeping declared dependencies")
        return False
    latest_text = latest.group(0)
    spec = str(package.get(section, {}).get(SDK, "")) if section else ""
    current = SEMVER.search(spec)
    replacement = None
    if not section or spec.strip().lower() in {"", "*", "latest"}:
        replacement = "^" + latest_text
    else:
        if not current:
            try:
                installed = json.loads((frontend / "node_modules" / SDK / "package.json").read_text())
                current = SEMVER.search(installed.get("version", ""))
            except (OSError, ValueError):
                pass
        if current and tuple(map(int, latest.groups())) > tuple(map(int, current.groups())):
            if latest.groups()[:2] == current.groups()[:2]:
                if not spec.startswith(("^", "~")):
                    replacement = latest_text
            else:
                print("[build] WARN: SDK minor/major update available; manual review required")
    if not replacement:
        return False
    package.setdefault(section or "dependencies", {})[SDK] = replacement
    path.write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n")
    return True


def build_frontend(root, mode, *, release=False):
    frontend = root / "app/frontend"
    if not (frontend / "package.json").is_file():
        print("[build] No frontend; skipped")
        return
    selection = resolve_pnpm(frontend)
    version = selection.version
    run(pnpm_command(frontend, version, "--version"), cwd=frontend)
    prepare_frontend(frontend)
    changed = update_sdk(frontend, version) if release else False
    package = json.loads((frontend / "package.json").read_text())
    modules = frontend / "node_modules"
    dependencies = {**package.get("dependencies", {}), **package.get("devDependencies", {})}
    missing = not modules.exists() or any(not (modules / name / "package.json").exists() for name in dependencies)
    install = pnpm_command(frontend, version, "install", "--config.confirm-modules-purge=false")
    if changed or missing:
        run(install, cwd=frontend)
    scripts = package.get("scripts", {})
    if mode == "cdn":
        args = ["run", "build:cdn"] if "build:cdn" in scripts else ["run", "build", "--mode", "cdn"]
    elif mode == "local" and "build:local" in scripts:
        args = ["run", "build:local"]
    else:
        args = ["run", "build"]
    try:
        run(pnpm_command(frontend, version, *args), cwd=frontend)
    except subprocess.CalledProcessError:
        print("[build] Repairing frontend dependencies and retrying once", flush=True)
        if modules.exists():
            shutil.rmtree(modules)
        run(install, cwd=frontend)
        run(pnpm_command(frontend, version, *args), cwd=frontend)
    if not (root / "app/dist/index.html").is_file():
        raise ValueError("Frontend build did not produce app/dist/index.html")


def generate_api(root):
    generator = root / "tools/gen_api.py"
    definition = root / "app/api/api.yaml"
    if not definition.is_file():
        definition = root / "app/api/api.json"
    generated = root / "app/server-go/handler_items.gen.go"
    if not generator.is_file() or not definition.is_file():
        raise ValueError("Missing tools/gen_api.py or app/api/api.yaml (api.json)")
    if generated.is_file() and generated.stat().st_mtime >= definition.stat().st_mtime:
        print("[build] API artifacts are up to date")
        return
    run([sys.executable, str(generator), str(root)], cwd=root)


def build_backend(root, args):
    if not (root / "app/server-go/main.go").is_file():
        raise ValueError("Missing app/server-go/main.go")
    env = os.environ.copy()
    env["GOWORK"] = "off"
    if args.mode == "release":
        env.update(GOOS=args.go_os or "linux", GOARCH=args.go_arch or "amd64", CGO_ENABLED="0")
        output = root / "app/server-go/bin/server"
    else:
        env.pop("GOOS", None)
        env.pop("GOARCH", None)
        output = root / ".aime_build/bin/server"
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".server-", dir=output.parent)
    os.close(fd)
    try:
        command = ["go", "build", "-buildvcs=false"]
        if args.mode == "release" and not args.no_strip:
            command += ["-ldflags=-s -w"]
        command += ["-o", temporary, "./app/server-go"]
        run(command, cwd=root, env=env, timeout=300)
        os.chmod(temporary, 0o755)
        os.replace(temporary, output)
        print(f"[build] Output: {output.relative_to(root)}", flush=True)
    finally:
        Path(temporary).unlink(missing_ok=True)


def build(root, args):
    state = root / ".aime_build"
    state.mkdir(exist_ok=True)
    with (state / "build.lock").open("a") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("Another build is running for this App") from exc
        generate_api(root)
        if args.target in {"all", "frontend"}:
            build_frontend(root, args.frontend_mode, release=args.mode == "release")
        if args.target in {"all", "backend"}:
            build_backend(root, args)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=["dev", "release"], default="dev")
    parser.add_argument("--target", choices=["all", "frontend", "backend"], default="all")
    parser.add_argument("--frontend-mode", choices=["local", "cdn", "default"], default="local")
    parser.add_argument("--go-os")
    parser.add_argument("--go-arch")
    parser.add_argument("--no-strip", action="store_true")
    args = parser.parse_args()
    if args.mode == "dev" and (args.go_os or args.go_arch):
        parser.error("--go-os/--go-arch are only valid for release builds")
    # Raising on TERM permits finally blocks to remove incomplete binaries.
    def terminate(_signum, _frame):
        raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM, terminate)
    try:
        build(ROOT, args)
    except (OSError, ValueError, subprocess.SubprocessError, KeyboardInterrupt) as exc:
        print(f"[build] ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
