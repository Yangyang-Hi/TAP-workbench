#!/usr/bin/env python3
"""Resolve and activate the Node.js and pnpm runtime owned by an App frontend."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_PNPM_VERSION = "11.21.0"
LEGACY_PNPM_VERSION = "8.15.9"
PNPM_NODE_REQUIREMENTS = {
    3: ">=8.15.0",
    4: ">=10.13.0",
    5: ">=10.16.0",
    6: ">=12.17.0",
    7: ">=14.6.0",
    8: ">=16.14.0",
    9: ">=18.12.0",
    10: ">=18.12.0",
    11: ">=22.13.0",
}
PACKAGE_MANAGER_RE = re.compile(
    r"^pnpm@(\d+\.\d+\.\d+)"
    r"(?:\+sha(?:224|256|384|512)\.[A-Za-z0-9+/=_-]+)?$"
)
NODE_VERSION_RE = re.compile(r"^v?(\d+\.\d+\.\d+)$")
NODE_RANGE_TOKEN_RE = re.compile(
    r"^(?P<operator><=|>=|<|>|=|\^|~)?"
    r"(?P<version>v?(?:\d+|[xX*])"
    r"(?:\.(?:\d+|[xX*]))?"
    r"(?:\.(?:\d+|[xX*]))?)$"
)
LOCKFILE_VERSION_RE = re.compile(
    r"^lockfileVersion:\s*['\"]?([^'\"\s]+)['\"]?\s*$",
    re.MULTILINE,
)
RUNTIME_SHELL = r"""
set -euo pipefail
exec </dev/null
export NPM_CONFIG_YES=true
export npm_config_yes=true
export npm_config_confirm_modules_purge=false
export COREPACK_ENABLE_DOWNLOAD_PROMPT=0

node_selector="$1"
shift
current_node_version="$(node --version 2>/dev/null || true)"
if [ "$node_selector" = "current" ]; then
  if [ -z "$current_node_version" ]; then
    echo "[frontend-runtime] Node.js is unavailable and no exact version was declared." >&2
    exit 1
  fi
else
  required_node_version="v${node_selector#v}"
  if [ "$current_node_version" != "$required_node_version" ]; then
    nvm_dir="${NVM_DIR:-$HOME/.nvm}"
    nvm_script="$nvm_dir/nvm.sh"
    if [ ! -s "$nvm_script" ]; then
      echo "[frontend-runtime] Node.js $required_node_version is required, found ${current_node_version:-not installed}." >&2
      echo "[frontend-runtime] nvm is unavailable: $nvm_script" >&2
      echo "[frontend-runtime] Run: aime environment config --language nodejs --version $node_selector" >&2
      exit 1
    fi
    # shellcheck source=/dev/null
    . "$nvm_script" --no-use
    if ! nvm use --silent "$node_selector"; then
      echo "[frontend-runtime] Node.js $required_node_version is not installed in nvm." >&2
      echo "[frontend-runtime] Run: aime environment config --language nodejs --version $node_selector" >&2
      exit 1
    fi
    current_node_version="$(node --version 2>/dev/null || true)"
  fi
  if [ "$current_node_version" != "$required_node_version" ]; then
    echo "[frontend-runtime] Expected Node.js $required_node_version, found ${current_node_version:-not installed}." >&2
    exit 1
  fi
fi
exec "$@"
""".strip()


class PnpmConfigError(ValueError):
    """Raised when an App's pnpm configuration is ambiguous or unsupported."""


@dataclass(frozen=True)
class PnpmSelection:
    version: str
    source: str
    warning: str
    node_version: str | None
    node_spec: str | None
    node_source: str
    node_warning: str
    pnpm_node_spec: str = ""


@dataclass(frozen=True)
class NodeRuntimeSelection:
    selector: str
    version: str
    source: str
    warning: str


def _read_package_data(frontend_dir: Path) -> dict:
    package_json = frontend_dir / "package.json"
    try:
        data = json.loads(package_json.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PnpmConfigError(f"package.json not found: {package_json}") from exc
    except (OSError, json.JSONDecodeError) as exc:
        raise PnpmConfigError(f"failed to read package.json: {exc}") from exc
    if not isinstance(data, dict):
        raise PnpmConfigError("package.json root must be an object")
    return data


def _read_lockfile_version(frontend_dir: Path) -> str | None:
    lockfile = frontend_dir / "pnpm-lock.yaml"
    if not lockfile.exists():
        return None
    try:
        content = lockfile.read_text(encoding="utf-8")
    except OSError as exc:
        raise PnpmConfigError(f"failed to read pnpm-lock.yaml: {exc}") from exc
    match = LOCKFILE_VERSION_RE.search(content)
    if not match:
        raise PnpmConfigError(
            "pnpm-lock.yaml is missing lockfileVersion; "
            "declare packageManager as an exact pnpm version"
        )
    return match.group(1)


def _read_nvmrc_version(frontend_dir: Path) -> str | None:
    nvmrc = frontend_dir / ".nvmrc"
    if not nvmrc.exists():
        return None
    try:
        value = nvmrc.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise PnpmConfigError(f"failed to read .nvmrc: {exc}") from exc
    match = NODE_VERSION_RE.fullmatch(value)
    if not match:
        raise PnpmConfigError(
            f"unsupported .nvmrc value {value!r}; use an exact version such as 22.23.1"
        )
    return match.group(1)


def _pnpm_node_spec(pnpm_version: str) -> str:
    major = int(pnpm_version.split(".", maxsplit=1)[0])
    node_spec = PNPM_NODE_REQUIREMENTS.get(major)
    if node_spec is None:
        raise PnpmConfigError(
            f"pnpm@{pnpm_version} has an unsupported major version; "
            "declare a supported exact pnpm version"
        )
    return node_spec


def _parse_partial_node_version(
    value: str,
) -> tuple[tuple[int | None, int | None, int | None], int]:
    normalized = value[1:] if value.startswith("v") else value
    parts = normalized.split(".")
    if len(parts) > 3:
        raise PnpmConfigError(f"unsupported Node.js version token {value!r}")

    parsed: list[int | None] = []
    wildcard_seen = False
    numeric_count = 0
    for part in parts:
        if part in {"x", "X", "*"}:
            wildcard_seen = True
            parsed.append(None)
            continue
        if wildcard_seen or not part.isdigit():
            raise PnpmConfigError(f"unsupported Node.js version token {value!r}")
        parsed.append(int(part))
        numeric_count += 1
    parsed.extend([None] * (3 - len(parsed)))
    return (parsed[0], parsed[1], parsed[2]), numeric_count


def _filled_node_version(
    partial: tuple[int | None, int | None, int | None],
) -> tuple[int, int, int]:
    return tuple(part if part is not None else 0 for part in partial)


def _upper_bound_for_partial(
    partial: tuple[int | None, int | None, int | None],
    numeric_count: int,
) -> tuple[int, int, int] | None:
    major, minor, _ = partial
    if numeric_count == 0 or major is None:
        return None
    if numeric_count >= 3:
        return None
    if numeric_count == 1 or minor is None:
        return major + 1, 0, 0
    return major, minor + 1, 0


def _expand_node_range_token(
    token: str,
) -> tuple[tuple[str, tuple[int, int, int]], ...]:
    match = NODE_RANGE_TOKEN_RE.fullmatch(token)
    if not match:
        raise PnpmConfigError(f"unsupported engines.node token {token!r}")

    operator = match.group("operator") or ""
    partial, numeric_count = _parse_partial_node_version(match.group("version"))
    lower = _filled_node_version(partial)
    upper = _upper_bound_for_partial(partial, numeric_count)
    is_exact = numeric_count == 3 and all(part is not None for part in partial)

    if operator in {"^", "~"}:
        if numeric_count == 0:
            return ()
        if operator == "^":
            major, minor, patch = lower
            if major > 0:
                upper = major + 1, 0, 0
            elif minor > 0:
                upper = 0, minor + 1, 0
            else:
                upper = 0, 0, patch + 1
        elif numeric_count == 1:
            upper = lower[0] + 1, 0, 0
        else:
            upper = lower[0], lower[1] + 1, 0
        return ((">=", lower), ("<", upper))

    if operator in {"", "="}:
        if is_exact:
            return (("=", lower),)
        if upper is None:
            return ()
        return ((">=", lower), ("<", upper))
    if operator == ">=":
        return ((">=", lower),)
    if operator == ">":
        return (((">=", upper) if upper is not None else (">", lower)),)
    if operator == "<":
        return (("<", lower),)
    if operator == "<=":
        return ((("<", upper) if upper is not None else ("<=", lower)),)
    raise PnpmConfigError(f"unsupported engines.node token {token!r}")


def _parse_node_range(
    spec: str,
) -> tuple[tuple[tuple[str, tuple[int, int, int]], ...], ...]:
    value = spec.strip()
    if not value:
        raise PnpmConfigError("engines.node must not be empty")

    alternatives: list[tuple[tuple[str, tuple[int, int, int]], ...]] = []
    for alternative in value.split("||"):
        group = alternative.strip()
        if not group:
            raise PnpmConfigError(f"unsupported engines.node {spec!r}")
        hyphen = re.fullmatch(r"(\S+)\s+-\s+(\S+)", group)
        if hyphen:
            lower_partial, _ = _parse_partial_node_version(hyphen.group(1))
            upper_partial, upper_count = _parse_partial_node_version(hyphen.group(2))
            comparators: list[tuple[str, tuple[int, int, int]]] = [
                (">=", _filled_node_version(lower_partial))
            ]
            upper = _upper_bound_for_partial(upper_partial, upper_count)
            if upper_count == 3:
                comparators.append(("<=", _filled_node_version(upper_partial)))
            elif upper is not None:
                comparators.append(("<", upper))
            alternatives.append(tuple(comparators))
            continue

        comparators = []
        for token in group.split():
            comparators.extend(_expand_node_range_token(token))
        alternatives.append(tuple(comparators))
    return tuple(alternatives)


def _node_version_satisfies(version: str, spec: str) -> bool:
    match = NODE_VERSION_RE.fullmatch(version.strip())
    if not match:
        raise PnpmConfigError(f"invalid Node.js version {version!r}")
    candidate = tuple(int(part) for part in match.group(1).split("."))
    alternatives = _parse_node_range(spec)

    def matches(comparator: tuple[str, tuple[int, int, int]]) -> bool:
        operator, expected = comparator
        if operator == "=":
            return candidate == expected
        if operator == ">":
            return candidate > expected
        if operator == ">=":
            return candidate >= expected
        if operator == "<":
            return candidate < expected
        if operator == "<=":
            return candidate <= expected
        raise AssertionError(f"unexpected comparator: {operator}")

    return any(all(matches(comparator) for comparator in group) for group in alternatives)


def _resolve_node_config(
    frontend_dir: Path,
    package_data: dict,
    pnpm_version: str,
) -> tuple[str | None, str | None, str, str, str]:
    pnpm_node_spec = _pnpm_node_spec(pnpm_version)
    engines = package_data.get("engines")
    if engines is not None and not isinstance(engines, dict):
        raise PnpmConfigError("engines must be an object when declared")

    node_spec = engines.get("node") if isinstance(engines, dict) else None
    if node_spec is not None:
        if not isinstance(node_spec, str):
            raise PnpmConfigError("engines.node must be a version range string")
        node_spec = node_spec.strip()
        _parse_node_range(node_spec)

    nvmrc_version = _read_nvmrc_version(frontend_dir)
    if nvmrc_version:
        if not _node_version_satisfies(nvmrc_version, pnpm_node_spec):
            raise PnpmConfigError(
                f".nvmrc selects Node.js {nvmrc_version}, which does not satisfy "
                f"pnpm@{pnpm_version} requirement {pnpm_node_spec!r}"
            )
        if node_spec and not _node_version_satisfies(nvmrc_version, node_spec):
            raise PnpmConfigError(
                f".nvmrc selects Node.js {nvmrc_version}, which does not satisfy "
                f"engines.node {node_spec!r}"
            )

    if nvmrc_version:
        return nvmrc_version, node_spec, ".nvmrc", "", pnpm_node_spec

    if node_spec is not None:
        exact_match = NODE_VERSION_RE.fullmatch(node_spec)
        if exact_match and not _node_version_satisfies(
            exact_match.group(1),
            pnpm_node_spec,
        ):
            raise PnpmConfigError(
                f"engines.node {node_spec!r} does not satisfy "
                f"pnpm@{pnpm_version} requirement {pnpm_node_spec!r}"
            )
        return (
            exact_match.group(1) if exact_match else None,
            node_spec,
            "engines.node",
            "",
            pnpm_node_spec,
        )

    return (
        None,
        None,
        f"pnpm@{pnpm_version}",
        ".nvmrc and engines.node are missing; selecting a locally available "
        f"Node.js that satisfies pnpm@{pnpm_version} requirement {pnpm_node_spec!r}",
        pnpm_node_spec,
    )


def _read_current_node_version() -> str | None:
    try:
        result = subprocess.run(
            ["node", "--version"],
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        return None
    if result.returncode != 0:
        return None
    match = NODE_VERSION_RE.fullmatch(result.stdout.strip())
    return match.group(1) if match else None


def _nvm_dir() -> Path:
    configured = os.environ.get("NVM_DIR")
    return Path(configured).expanduser() if configured else Path.home() / ".nvm"


def _read_installed_nvm_versions(nvm_dir: Path) -> tuple[str, ...]:
    try:
        if not (nvm_dir / "nvm.sh").is_file():
            return ()
        versions_dir = nvm_dir / "versions" / "node"
        if not versions_dir.is_dir():
            return ()

        versions: list[tuple[tuple[int, int, int], str]] = []
        for entry in versions_dir.iterdir():
            match = NODE_VERSION_RE.fullmatch(entry.name)
            if not match or not (entry / "bin" / "node").is_file():
                continue
            normalized = match.group(1)
            versions.append(
                (tuple(int(part) for part in normalized.split(".")), normalized)
            )
    except OSError as exc:
        raise PnpmConfigError(
            f"failed to inspect nvm directory {nvm_dir}: {exc}"
        ) from exc
    versions.sort(reverse=True)
    return tuple(version for _, version in versions)


def _node_satisfies_runtime_requirements(
    version: str,
    selection: PnpmSelection,
) -> bool:
    return (
        selection.node_spec is None
        or _node_version_satisfies(version, selection.node_spec)
    ) and (
        selection.pnpm_node_spec == ""
        or _node_version_satisfies(version, selection.pnpm_node_spec)
    )


def _runtime_requirements_description(selection: PnpmSelection) -> str:
    requirements = []
    if selection.pnpm_node_spec:
        requirements.append(
            f"pnpm@{selection.version} requires {selection.pnpm_node_spec!r}"
        )
    if selection.node_spec is not None:
        requirements.append(f"engines.node is {selection.node_spec!r}")
    return " and ".join(requirements) or "the declared Node.js requirements"


def _select_node_runtime(
    selection: PnpmSelection,
    *,
    current_version: str | None,
    installed_versions: tuple[str, ...],
) -> NodeRuntimeSelection:
    preferred = selection.node_version
    if preferred:
        if current_version == preferred and _node_satisfies_runtime_requirements(
            preferred,
            selection,
        ):
            return NodeRuntimeSelection(
                selector="current",
                version=preferred,
                source=selection.node_source,
                warning="",
            )
        if (
            preferred in installed_versions
            and _node_satisfies_runtime_requirements(preferred, selection)
        ):
            return NodeRuntimeSelection(
                selector=preferred,
                version=preferred,
                source=selection.node_source,
                warning="",
            )

    if current_version and _node_satisfies_runtime_requirements(
        current_version,
        selection,
    ):
        warning = ""
        if preferred:
            warning = (
                f"Node.js {preferred} from {selection.node_source} is unavailable; "
                f"using current Node.js {current_version}, which satisfies "
                f"{_runtime_requirements_description(selection)}"
            )
        return NodeRuntimeSelection(
            selector="current",
            version=current_version,
            source=selection.node_source,
            warning=warning,
        )
    for version in installed_versions:
        if _node_satisfies_runtime_requirements(version, selection):
            warning = ""
            if preferred:
                warning = (
                    f"Node.js {preferred} from {selection.node_source} is unavailable; "
                    f"using installed Node.js {version}, which satisfies "
                    f"{_runtime_requirements_description(selection)}"
                )
            return NodeRuntimeSelection(
                selector=version,
                version=version,
                source=selection.node_source,
                warning=warning,
            )
    found = current_version or "not installed"
    raise PnpmConfigError(
        f"no installed Node.js version satisfies {_runtime_requirements_description(selection)}; "
        f"current version is {found}; automatic installation is disabled"
    )


def resolve_node_runtime(
    selection: PnpmSelection,
) -> NodeRuntimeSelection:
    current_version = _read_current_node_version()
    if (
        selection.node_version is None
        and current_version is not None
        and _node_satisfies_runtime_requirements(current_version, selection)
    ):
        return _select_node_runtime(
            selection,
            current_version=current_version,
            installed_versions=(),
        )

    return _select_node_runtime(
        selection,
        current_version=current_version,
        installed_versions=_read_installed_nvm_versions(_nvm_dir()),
    )


def resolve_pnpm(frontend_dir: Path | str) -> PnpmSelection:
    frontend = Path(frontend_dir)
    package_data = _read_package_data(frontend)
    package_manager = package_data.get("packageManager")
    if package_manager is not None:
        if not isinstance(package_manager, str):
            raise PnpmConfigError(
                "packageManager must be a string in the form pnpm@x.y.z"
            )
        match = PACKAGE_MANAGER_RE.fullmatch(package_manager.strip())
        if not match:
            raise PnpmConfigError(
                f"unsupported packageManager {package_manager!r}; "
                "use an exact version such as pnpm@11.21.0"
            )
        version = match.group(1)
        source = "packageManager"
        warning = ""
    else:
        lockfile_version = _read_lockfile_version(frontend)
        if lockfile_version is None:
            version = DEFAULT_PNPM_VERSION
            source = "default"
            warning = (
                "packageManager and pnpm-lock.yaml are missing; "
                f"using pnpm@{DEFAULT_PNPM_VERSION}"
            )
        elif lockfile_version in {"6", "6.0"}:
            version = LEGACY_PNPM_VERSION
            source = "lockfile-v6"
            warning = (
                "packageManager is missing; lockfile v6 detected, "
                f"using legacy pnpm@{LEGACY_PNPM_VERSION}"
            )
        elif lockfile_version in {"9", "9.0"}:
            version = DEFAULT_PNPM_VERSION
            source = "lockfile-v9"
            warning = (
                "packageManager is missing; lockfile v9 detected, "
                f"using pnpm@{DEFAULT_PNPM_VERSION}"
            )
        else:
            raise PnpmConfigError(
                f"unsupported pnpm lockfileVersion {lockfile_version!r}; "
                "declare packageManager as an exact pnpm version"
            )

    (
        node_version,
        node_spec,
        node_source,
        node_warning,
        pnpm_node_spec,
    ) = _resolve_node_config(frontend, package_data, version)
    return PnpmSelection(
        version=version,
        source=source,
        warning=warning,
        node_version=node_version,
        node_spec=node_spec,
        node_source=node_source,
        node_warning=node_warning,
        pnpm_node_spec=pnpm_node_spec,
    )


def pnpm_command(
    frontend_dir: Path | str,
    version: str,
    *args: str,
) -> list[str]:
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise PnpmConfigError(f"invalid resolved pnpm version: {version!r}")
    selection = resolve_pnpm(frontend_dir)
    if selection.version != version:
        raise PnpmConfigError(
            f"resolved pnpm version changed from {version} to {selection.version}"
        )
    runtime = resolve_node_runtime(selection)
    return [
        "bash",
        "-c",
        RUNTIME_SHELL,
        "frontend-runtime",
        runtime.selector,
        "npx",
        "--yes",
        f"--package=pnpm@{version}",
        "--",
        "pnpm",
        *args,
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--frontend", required=True)
    node_output = parser.add_mutually_exclusive_group()
    node_output.add_argument("--node-version", action="store_true")
    node_output.add_argument("--resolved-node-version", action="store_true")
    parser.add_argument("--expected-pnpm-version")
    parser.add_argument("--exec", dest="exec_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    try:
        selection = resolve_pnpm(args.frontend)
    except PnpmConfigError as exc:
        print(f"frontend runtime configuration error: {exc}", file=sys.stderr)
        return 1
    if (
        args.expected_pnpm_version is not None
        and selection.version != args.expected_pnpm_version
    ):
        print(
            "frontend runtime configuration error: "
            f"resolved pnpm version changed from {args.expected_pnpm_version} "
            f"to {selection.version}",
            file=sys.stderr,
        )
        return 1
    if args.exec_args is not None:
        if not args.exec_args:
            print(
                "frontend runtime configuration error: "
                "--exec requires pnpm arguments",
                file=sys.stderr,
            )
            return 2
        if selection.warning:
            print(f"[pnpm] {selection.warning}", file=sys.stderr)
        if selection.node_warning:
            print(f"[node] {selection.node_warning}", file=sys.stderr)
        try:
            runtime = resolve_node_runtime(selection)
            if runtime.warning:
                print(f"[node] {runtime.warning}", file=sys.stderr)
            result = subprocess.run(
                pnpm_command(args.frontend, selection.version, *args.exec_args),
                cwd=Path(args.frontend).resolve(),
                env=os.environ.copy(),
            )
        except (FileNotFoundError, PnpmConfigError) as exc:
            print(f"frontend runtime error: {exc}", file=sys.stderr)
            return 1
        return result.returncode
    if args.node_version:
        if selection.node_warning:
            print(f"[node] {selection.node_warning}", file=sys.stderr)
        if selection.node_version:
            print(selection.node_version)
        else:
            try:
                print(resolve_node_runtime(selection).version)
            except PnpmConfigError as exc:
                print(f"frontend runtime error: {exc}", file=sys.stderr)
                return 1
    elif args.resolved_node_version:
        try:
            runtime = resolve_node_runtime(selection)
        except PnpmConfigError as exc:
            print(f"frontend runtime error: {exc}", file=sys.stderr)
            return 1
        if selection.node_warning:
            print(f"[node] {selection.node_warning}", file=sys.stderr)
        if runtime.warning:
            print(f"[node] {runtime.warning}", file=sys.stderr)
        print(runtime.version)
    else:
        if selection.warning:
            print(f"[pnpm] {selection.warning}", file=sys.stderr)
        print(selection.version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
