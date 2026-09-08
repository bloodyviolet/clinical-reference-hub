const fs = require('node:fs');
const path = require('node:path');
const tailwind = require('tailwindcss');
const postcss = require('postcss');

const root = path.resolve(__dirname, '..');
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const classPattern = /(?:class|className)\s*=\s*["'`]([^"'`]+)["'`]/g;
const candidates = new Set();
for (const match of html.matchAll(classPattern)) {
  for (const token of match[1].split(/\s+/)) {
    if (token && !token.includes('${')) candidates.add(token);
  }
}

const tailwindCss = fs.readFileSync(require.resolve('tailwindcss/index.css'), 'utf8');

(async () => {
  const compiler = await tailwind.compile(tailwindCss);
  const built = compiler.build([...candidates].sort());
  const rootCss = postcss.parse(built);
  rootCss.walkComments((node) => node.remove());
  rootCss.walk((node) => {
    if (node.raws) node.raws.before = '';
    if (node.type === 'rule' && node.raws) node.raws.between = '';
    if (node.type === 'decl' && node.raws) node.raws.between = ':';
  });
  const output = rootCss.toString().trim() + '\n';
  const target = path.join(root, 'assets', 'app.css');
  fs.writeFileSync(target, output);
  console.log(`Built ${target} from ${candidates.size} class candidates (${output.length} bytes).`);
})().catch((error) => {
  console.error(error);
  process.exit(1);
});
