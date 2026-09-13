const fs =
  require('fs');

const assert =
  require('assert');


const html =
  fs.readFileSync(
    'index.html',
    'utf8'
  );

const app =
  fs.readFileSync(
    'assets/app.js',
    'utf8'
  );

const i18n =
  fs.readFileSync(
    'assets/i18n.js',
    'utf8'
  );

const session =
  fs.readFileSync(
    'assets/ui-session.js',
    'utf8'
  );

const theme =
  fs.readFileSync(
    'assets/bloodviolet-theme.css',
    'utf8'
  );

const compiledCss =
  fs.readFileSync(
    'assets/app.css',
    'utf8'
  );

const manifest =
  JSON.parse(
    fs.readFileSync(
      'manifest.json',
      'utf8'
    )
  );

const sw =
  fs.readFileSync(
    'sw.js',
    'utf8'
  );

const main =
  fs.readFileSync(
    'main.py',
    'utf8'
  );

const preflight =
  fs.readFileSync(
    'scripts/preflight.py',
    'utf8'
  );


assert(
  html.includes(
    'id="brand-home"'
  )
);

assert(
  html.includes(
    'href="/"'
  )
);

assert(
  html.includes(
    'src="/assets/icons/icon-192.png"'
  )
);

assert(
  !/>\s*Rx\s*</.test(
    html
  )
);

assert(
  html.includes(
    '/assets/bloodviolet-theme.css'
  )
);

assert(
  html.includes(
    '/assets/ui-session.js'
  )
);

assert(
  html.indexOf(
    '/assets/app.js'
  )
  <
  html.indexOf(
    '/assets/ui-session.js'
  )
);

assert(
  html.includes(
    'content="#5A0B32"'
  )
);


const surfaceStart =
  session.indexOf(
    'const TOOL_RESULT_SURFACES'
  );

const surfaceEnd =
  session.indexOf(
    'const TOOL_SERIAL_KEYS',
    surfaceStart
  );

assert(
  surfaceStart >= 0
);

assert(
  surfaceEnd > surfaceStart
);

const surfaceBlock =
  session.slice(
    surfaceStart,
    surfaceEnd
  );

const formIds =
  [
    ...surfaceBlock.matchAll(
      /'([^']+-form)'\s*:/g
    )
  ].map(
    (match) =>
      match[1]
  );

assert.strictEqual(
  new Set(
    formIds
  ).size,
  26
);


const serialStart =
  session.indexOf(
    'const TOOL_SERIAL_KEYS'
  );

const serialEnd =
  session.indexOf(
    'function blankState',
    serialStart
  );

const serialBlock =
  session.slice(
    serialStart,
    serialEnd
  );

const serialForms =
  [
    ...serialBlock.matchAll(
      /'([^']+-form)'\s*:/g
    )
  ];

assert.strictEqual(
  serialForms.length,
  18
);


assert(
  session.includes(
    'clinical-reference-v2-ui-session-v1'
  )
);

assert(
  session.includes(
    'sessionStorage.getItem'
  )
);

assert(
  session.includes(
    'sessionStorage.setItem'
  )
);

assert(
  !session.includes(
    'localStorage'
  )
);

assert(
  !session.includes(
    'indexedDB'
  )
);

assert(
  !session.includes(
    'fetch('
  )
);

assert(
  !session.includes(
    'XMLHttpRequest'
  )
);

assert(
  session.includes(
    'MutationObserver'
  )
);

assert(
  session.includes(
    'sanitiseResultHtml'
  )
);

assert(
  session.includes(
    "button.type =\n        'reset'"
  )
);

assert(
  session.includes(
    'clearToolState'
  )
);

assert(
  session.includes(
    'restoreNavigation'
  )
);

assert(
  app.includes(
    'ClinicalSerialCaptureBridge'
  )
);

assert(
  app.includes(
    'serialCaptureRestoreBindings'
  )
);

assert(
  app.includes(
    'ClinicalUiSession'
  )
);

assert(
  app.includes(
    'clinicalResultStatus'
  )
);


assert.strictEqual(
  (
    i18n.match(
      /'tool\.reset'/g
    )
    || []
  ).length,
  2
);


assert(
  theme.includes(
    '--bv-ink: #09030f'
  )
);

assert(
  theme.includes(
    '--bv-plum: #1d082d'
  )
);

assert(
  theme.includes(
    '--bv-violet: #5b21a6'
  )
);

assert(
  theme.includes(
    '--bv-blood-main: #a40a2f'
  )
);

assert(
  theme.includes(
    '--bv-blood-bright: #cf1744'
  )
);

assert(
  theme.includes(
    '--color-fuchsia-600: #aa0c34'
  )
);

assert(
  theme.includes(
    '--color-rose-600: #c52247'
  )
);

assert(
  theme.includes(
    '--bv-text: #fff9ff'
  )
);


/*
 * Tailwind v4 compiled utilities must resolve through the
 * theme variables that the late Bloodviolet stylesheet overrides.
 */

assert(
  compiledCss.includes(
    'var(--color-slate-950)'
  )
);

assert(
  compiledCss.includes(
    'var(--color-teal-600)'
  )
);

assert(
  compiledCss.includes(
    'var(--color-violet-600)'
  )
);


assert.strictEqual(
  manifest.theme_color,
  '#5A0B32'
);

assert.strictEqual(
  manifest.background_color,
  '#09030F'
);


assert(
  sw.includes(
    'clinical-reference-v27-v2-bloodviolet-persistent-ux'
  )
);

assert(
  sw.includes(
    "'/assets/bloodviolet-theme.css'"
  )
);

assert(
  sw.includes(
    "'/assets/ui-session.js'"
  )
);

assert(
  sw.includes(
    "'/manifest.json?v=27'"
  )
);


for (
  const source
  of [
    main,
    preflight
  ]
) {
  assert(
    source.includes(
      'bloodviolet-theme.css'
    )
  );

  assert(
    source.includes(
      'ui-session.js'
    )
  );
}


console.log(
  'persistent_ux_brand_qc: 26-tool session persistence, 18 serial bridges, per-tool reset, linked brand home and Bloodviolet palette PASS'
);
