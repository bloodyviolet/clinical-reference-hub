const fs = require('fs');
const vm = require('vm');
const assert = require('assert');


const source =
  fs.readFileSync(
    'assets/clinical-tools.js',
    'utf8'
  );


vm.runInThisContext(
  source,
  {
    filename:
      'assets/clinical-tools.js'
  }
);


const vectors =
  JSON.parse(
    fs.readFileSync(
      'tests/fixtures/news2_vectors.json',
      'utf8'
    )
  );


for (const vector of vectors) {
  const result =
    ClinicalTools.calculateNews2(
      vector.input
    );

  assert.strictEqual(
    result.total,
    vector.total,
    `${vector.name}: total`
  );

  assert.strictEqual(
    result.trigger_code,
    vector.trigger,
    `${vector.name}: trigger`
  );

  assert(
    result.aggregate_label_pt
  );

  assert(
    result.aggregate_label_en
  );

  assert(
    result.monitoring_pt
  );

  assert(
    result.monitoring_en
  );

  assert(
    result.response_pt
  );

  assert(
    result.response_en
  );
}


assert.throws(
  () =>
    ClinicalTools.calculateNews2({
      ...vectors[0].input,

      spo2_scale: 2,

      scale2_prescribed: false
    }),

  /scale2_requires_prescribed_target/
);


const html =
  fs.readFileSync(
    'index.html',
    'utf8'
  );


const i18n =
  fs.readFileSync(
    'assets/i18n.js',
    'utf8'
  );


const sw =
  fs.readFileSync(
    'sw.js',
    'utf8'
  );


assert(
  html.includes(
    'data-language="pt-BR"'
  )
);

assert(
  html.includes(
    'data-language="en-GB"'
  )
);

assert(
  html.includes(
    'id="news2-form"'
  )
);

assert(
  html.includes(
    '/assets/i18n.js'
  )
);

assert(
  html.includes(
    '/assets/clinical-tools.js'
  )
);

assert(
  i18n.includes(
    "'pt-BR'"
  )
);

assert(
  i18n.includes(
    "'en-GB'"
  )
);

assert(
  sw.includes(
    '/assets/i18n.js'
  )
);

assert(
  sw.includes(
    '/assets/clinical-tools.js'
  )
);


console.log(
  'news2_i18n_qc: PASS'
);
