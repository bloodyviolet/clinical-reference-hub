const fs = require('fs');
const assert = require('assert');

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

const ui =
  fs.readFileSync(
    'assets/pcdt-repository.js',
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

const sw =
  fs.readFileSync(
    'sw.js',
    'utf8'
  );


assert(
  html.includes(
    'id="tab-btn-pcdt"'
  )
);

assert(
  html.includes(
    'data-tab="pcdt"'
  )
);

assert(
  html.includes(
    'id="view-pcdt"'
  )
);

assert(
  html.includes(
    'id="pcdt-search-form"'
  )
);

assert(
  html.includes(
    'id="pcdt-search-input"'
  )
);

assert(
  html.includes(
    '/assets/pcdt-repository.js'
  )
);


assert(
  app.includes(
    "['sae', 'policy', 'pcdt', 'calc', 'scales', 'trends']"
  )
);

assert(
  session.includes(
    "'pcdt'"
  )
);


assert.strictEqual(
  (
    i18n.match(
      /'nav\.pcdt':/g
    )
    || []
  ).length,
  2
);

assert.strictEqual(
  (
    i18n.match(
      /'pcdt\.title':/g
    )
    || []
  ).length,
  2
);


assert(
  ui.includes(
    '/api/v1/pcdt?'
  )
);

assert(
    ui.includes(
      '/^\\/documents\\/pcdt\\/[0-9a-f]{64}\\.pdf$/'
    )
  );

assert(
  ui.includes(
    'safePcdtDocumentUrl'
  )
);

assert(
  ui.includes(
    'safeExternalUrl'
  )
);

assert(
  ui.includes(
    'escapeHtml'
  )
);

assert(
  ui.includes(
    'sessionStorage'
  )
);

assert(
  ui.includes(
    'clinical-language-change'
  )
);

assert(
  ui.includes(
    'encodeURIComponent'
  )
);


assert(
  !ui.includes(
    'eval('
  )
);

assert(
  !ui.includes(
    'local_relative_path'
  )
);

assert(
  !ui.includes(
    '/var/lib/medical-api'
  )
);


assert(
  sw.includes(
    'clinical-reference-v29-v2-pcdt-repository'
  )
);

assert(
  html.includes(
    '/manifest.json?v=29'
  )
);

assert(
  sw.includes(
    "'/assets/pcdt-repository.js'"
  )
);


const appShellMatch =
  sw.match(
    /const APP_SHELL = \[([\s\S]*?)\];/
  );

assert(
  appShellMatch
);

assert(
  !appShellMatch[1].includes(
    '/documents/pcdt/'
  )
);

assert(
  sw.includes(
    "url.pathname.startsWith('/documents/pcdt/')"
  )
);


console.log(
  'pcdt_repository_ui_qc: repository navigation, bilingual chrome, safe links and PDF cache isolation passed'
);
