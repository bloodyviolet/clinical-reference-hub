const fs =
  require('fs');

const assert =
  require('assert');


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


const app =
  fs.readFileSync(
    'assets/app.js',
    'utf8'
  );


const sw =
  fs.readFileSync(
    'sw.js',
    'utf8'
  );


function occurrences(
  text,
  token
) {
  return (
    text
      .split(token)
      .length
    - 1
  );
}


assert(
  html.includes(
    'id="falls-function-card"'
  )
);


assert(
  html.includes(
    'id="caderneta-falls-form"'
  )
);


assert(
  html.includes(
    'id="caderneta-falls-result"'
  )
);


assert(
  html.includes(
    'id="ivcf20-form"'
  )
);


assert(
  html.includes(
    'id="ivcf20-result"'
  )
);


assert.strictEqual(
  occurrences(
    html,
    'data-falls-field="'
  ),
  12
);


assert.strictEqual(
  occurrences(
    html,
    'data-ivcf-field="'
  ),
  24
);


const fallsAge =
  html.match(
    /<input\s+id="caderneta-falls-age"[\s\S]*?>/
  );


assert(
  fallsAge
);


assert(
  fallsAge[0].includes(
    'min="60"'
  )
);


assert(
  !fallsAge[0].includes(
    'max='
  )
);


const ivcfAge =
  html.match(
    /<input\s+id="ivcf20-age"[\s\S]*?>/
  );


assert(
  ivcfAge
);


assert(
  ivcfAge[0].includes(
    'min="60"'
  )
);


assert(
  !ivcfAge[0].includes(
    'max='
  )
);


for (const key of [
  '"falls.title"',
  '"falls.noScore"',
  '"falls.item.fall_previous_year"',
  '"falls.item.sadness_or_depressed_mood"',
  '"ivcf.title"',
  '"ivcf.instruction"',
  '"ivcf.gaitNotTug"',
  '"ivcf.noFallsScore"',
  '"ivcf.item.unintentional_weight_loss_criterion"',
  '"ivcf.item.gait_4m_gt_5_seconds"',
  '"ivcf.item.two_or_more_falls_last_year"',
  '"ivcf.item.hospitalized_last_six_months"'
]) {
  assert.strictEqual(
    occurrences(
      i18n,
      key
    ),
    2,
    `expected PT + EN translation for ${key}`
  );
}


assert(
  i18n.includes(
    '4,5 kg ou 5%'
  )
);


assert(
  i18n.includes(
    '6 kg nos últimos 6 meses'
  )
);


assert(
  i18n.includes(
    '3 kg no último mês'
  )
);


assert(
  i18n.includes(
    '4.5 kg or 5%'
  )
);


assert(
  i18n.includes(
    '6 kg during the previous 6 months'
  )
);


assert(
  i18n.includes(
    '3 kg during the previous month'
  )
);


assert(
  i18n.includes(
    'NÃO é Timed Up and Go (TUG)'
  )
);


assert(
  i18n.includes(
    'is NOT the Timed Up and Go (TUG)'
  )
);


assert(
  html.includes(
    'data-i18n="ivcf.noFallsScore"'
  )
);


assert(
  html.includes(
    'data-i18n="falls.noScore"'
  )
);


// C2B must wire the already-qualified static DOM
// without changing its clinical field contract.
assert(
  app.includes(
    'function calculateCadernetaFallsTool'
  )
);


assert(
  app.includes(
    'function calculateIvcf20Tool'
  )
);


assert(
  app.includes(
    "'caderneta-falls-form': calculateCadernetaFallsTool"
  )
);


assert(
  app.includes(
    "'ivcf20-form': calculateIvcf20Tool"
  )
);


assert(
  sw.includes(
    'clinical-reference-v24-v2-serial-trends-ui'
  )
);


assert(
  !sw.includes(
    'clinical-reference-v20-v2-brazil-methanol'
  )
);


console.log(
  'falls_function_ui_static_qc: bilingual Caderneta/IVCF-20 DOM + current cache PASS'
);
