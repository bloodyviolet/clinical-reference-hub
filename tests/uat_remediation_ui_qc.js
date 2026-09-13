'use strict';

const assert =
  require('assert');

const fs =
  require('fs');

const path =
  require('path');


const ROOT =
  path.resolve(
    __dirname,
    '..'
  );


const html =
  fs.readFileSync(
    path.join(
      ROOT,
      'index.html'
    ),
    'utf8'
  );


const app =
  fs.readFileSync(
    path.join(
      ROOT,
      'assets',
      'app.js'
    ),
    'utf8'
  );


const css =
  fs.readFileSync(
    path.join(
      ROOT,
      'assets',
      'app.css'
    ),
    'utf8'
  );


const cssBuilder =
  fs.readFileSync(
    path.join(
      ROOT,
      'scripts',
      'build_css.cjs'
    ),
    'utf8'
  );


const sw =
  fs.readFileSync(
    path.join(
      ROOT,
      'sw.js'
    ),
    'utf8'
  );


const exporter =
  require(
    path.join(
      ROOT,
      'assets',
      'serial-trends-export.js'
    )
  );


assert(
  css.includes(
    '.bg-violet-600'
  ),
  'rebuilt CSS must contain violet button background'
);


assert(
  cssBuilder.includes(
    'collectJavaScriptFiles'
  ),
  'CSS builder must scan application JavaScript sources'
);


assert(
  cssBuilder.includes(
    "path.join(\n      root,\n      'assets'"
  ),
  'CSS builder must include assets source directory'
);


for (
  const selector
  of [
    '.bg-emerald-500\\/10',
    '.bg-rose-500\\/10',
    '.bg-amber-500\\/10'
  ]
) {
  assert(
    css.includes(
      selector
    ),
    `rebuilt CSS missing dynamic application selector ${selector}`
  );
}


assert(
  css.includes(
    '.hover\\:bg-violet-500'
  ),
  'Tailwind v4 hover variant class must be generated'
);


const violetHoverStart =
  css.indexOf(
    '.hover\\:bg-violet-500'
  );


assert(
  violetHoverStart >= 0
);


const violetHoverFragment =
  css.slice(
    violetHoverStart,
    violetHoverStart + 240
  );


assert(
  violetHoverFragment.includes(
    '&:hover'
  ),
  'Tailwind v4 hover variant must contain nested &:hover'
);


assert(
  violetHoverFragment.includes(
    '--color-violet-500'
  ),
  'violet hover rule must resolve the expected colour token'
);


assert(
  css.includes(
    '.text-violet-200'
  ),
  'rebuilt CSS must contain violet text utility'
);


assert(
  html.includes(
    'data-i18n="steadi.tug.calculate"'
  )
);


assert(
  html.includes(
    'class="w-full bg-violet-600 hover:bg-violet-500'
  )
);


const calcGroups =
  [
    ...html.matchAll(
      /data-calc-group="([^"]+)"/g
    )
  ].map(
    (match) =>
      match[1]
  );


assert.deepStrictEqual(
  calcGroups,
  [
    'drip',
    'medication',
    'bmi',
    'paediatrics',
    'renal',
    'falls-function',
    'metabolic',
    'oxygenation',
    'hemodynamics',
    'obstetrics'
  ]
);


const scaleGroups =
  [
    ...html.matchAll(
      /data-scale-group="([^"]+)"/g
    )
  ].map(
    (match) =>
      match[1]
  );


assert.deepStrictEqual(
  scaleGroups,
  [
    'news2',
    'neurological',
    'apgar'
  ]
);


for (
  const required
  of [
    'CALCULATOR_GROUP_FORMS',
    'SCALE_GROUP_FORMS',
    'wireClinicalToolSubnavigation',
    'setClinicalToolGroup'
  ]
) {
  assert(
    app.includes(
      required
    )
  );
}


const serialStart =
  app.indexOf(
    '// ITEM11_SERIAL_TRENDS_UI_START'
  );


const serialEnd =
  app.indexOf(
    '// ITEM11_SERIAL_TRENDS_UI_END'
  );


assert(
  serialStart >= 0
  && serialEnd > serialStart
);


const serial =
  app.slice(
    serialStart,
    serialEnd
  );


assert(
  serial.includes(
    'SERIAL_SESSION_STORAGE_KEY'
  )
);


assert(
  serial.includes(
    'sessionStorage'
  )
);


assert(
  !serial.includes(
    'localStorage'
  )
);


assert(
  !serial.includes(
    'indexedDB'
  )
);


assert(
  serial.includes(
    'capturedAt:'
  )
);


assert(
  html.includes(
    'id="serial-download-pdf"'
  )
);


assert(
  html.includes(
    'id="serial-download-docx"'
  )
);


assert(
  html.includes(
    '/assets/serial-trends-export.js'
  )
);


assert(
  sw.includes(
    "'/assets/serial-trends-export.js'"
  )
);


const exportSource =
  fs.readFileSync(
    path.join(
      ROOT,
      'assets',
      'serial-trends-export.js'
    ),
    'utf8'
  );


assert(
  !exportSource.includes(
    'fetch('
  )
);


assert(
  !exportSource.includes(
    'XMLHttpRequest'
  )
);


const sample = {
  schema_version: 1,
  release: '2.0.0',
  generated_at:
    '2026-09-13T12:00:00.000Z',
  language: 'pt-BR',
  title:
    'Tendências seriadas',
  privacy_notice:
    'Sem identificadores.',
  visualisation_boundary:
    'Sem interpretação automática.',
  instruments: [
    {
      key: 'gcs',
      label:
        'Escala de Coma de Glasgow',
      observations: [
        {
          observed_at:
            '2026-09-13T08:00:00-03:00',
          captured_at:
            '2026-09-13T11:00:10.000Z',
          execution_source:
            'api',
          equal_time_tie:
            false,
          summary_fields: [
            {
              path: 'total',
              present: true,
              value: 15
            }
          ],
          component_fields: [],
          context_fields: [],
          request_snapshot: {
            eye: 4,
            verbal: 5,
            motor: 6
          },
          result_snapshot: {
            total: 15
          }
        }
      ]
    }
  ]
};


const pdf =
  exporter
    .buildPdfBytes(
      sample
    );


assert(
  pdf instanceof Uint8Array
);


assert.strictEqual(
  Buffer.from(
    pdf.slice(
      0,
      8
    )
  ).toString(
    'latin1'
  ),
  '%PDF-1.4'
);


const docx =
  exporter
    .buildDocxBytes(
      sample
    );


assert(
  docx instanceof Uint8Array
);


assert.strictEqual(
  docx[0],
  0x50
);


assert.strictEqual(
  docx[1],
  0x4b
);


const docxBuffer =
  Buffer.from(
    docx
  );


assert(
  docxBuffer.includes(
    Buffer.from(
      '[Content_Types].xml'
    )
  )
);


assert(
  docxBuffer.includes(
    Buffer.from(
      'word/document.xml'
    )
  )
);


console.log(
  'uat_remediation_ui_qc: '
  + 'button CSS, calculator/scale subnav, '
  + 'session restore and client PDF/DOCX export PASS'
);
