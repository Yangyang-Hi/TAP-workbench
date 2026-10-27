// Build the live workbench without requiring access to private npm registries.
// Uses the existing uploaded ByteCloud runtime verbatim, not an authentication mock.
import path from "node:path";
import fs from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(
  process.env.TAP_BUILD_NODE_MODULES
    ? path.join(process.env.TAP_BUILD_NODE_MODULES, "../package.json")
    : path.join(root, "app/frontend/package.json"),
);
const { build } = require("esbuild");
const modules =
  process.env.TAP_BUILD_NODE_MODULES ||
  path.join(root, "app/frontend/node_modules");
const out = path.join(root, "app/dist");
await fs.rm(out, { recursive: true, force: true });
await fs.mkdir(path.join(out, "assets"), { recursive: true });
const result = await build({
  absWorkingDir: path.join(root, "app/frontend"),
  entryPoints: ["src/workbench-entry.tsx"],
  outdir: path.join(out, "assets"),
  entryNames: "workbench-[hash]",
  assetNames: "[name]-[hash]",
  chunkNames: "chunk-[hash]",
  bundle: true,
  splitting: true,
  format: "esm",
  minify: true,
  target: "es2022",
  jsx: "automatic",
  nodePaths: [modules],
  alias: {
    "@bytecloud/common-lib": path.join(
      root,
      "app/frontend/vendor/bytecloud/index-CyHTFGrwEOXakQLE.js",
    ),
  },
  metafile: true,
  define: { "process.env.NODE_ENV": '"production"' },
});
const entries = Object.entries(result.metafile.outputs);
const entry = entries.find(([, x]) =>
  x.entryPoint?.endsWith("workbench-entry.tsx"),
);
if (!entry) throw Error("entry missing");
const js = path.basename(entry[0]);
const css = entries.find(([p]) => p.endsWith(".css"))?.[0];
await fs.writeFile(
  path.join(out, "index.html"),
  `<!doctype html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TAP Governance · AIME Live</title>${css ? `<link rel="stylesheet" href="./assets/${path.basename(css)}">` : ""}<style>body{margin:0}button{cursor:pointer}</style></head><body><div id="root"></div><script type="module" src="./assets/${js}"></script></body></html>`,
);
console.log("Built live AIME workbench:", js);
