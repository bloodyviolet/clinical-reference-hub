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
  source,
  token
) {
  return (
    source
      .split(token)
      .length
    - 1
  );
}


for (const id of [
  'steadi-complementary-card',
  'steadi-tug-form',
  'steadi-tug-result',
  'steadi-chair-form',
  'steadi-chair-result',
  'steadi-balance-form',
  'steadi-balance-result',
  'steadi-orthostatic-form',
  'steadi-orthostatic-result'
]) {
  assert(
    html.includes(
      `id="${id}"`
    ),
    `missing ${id}`
  );
}


for (const token of [
  'data-i18n="steadi.badge"',
  'data-i18n="steadi.boundary"',
  'data-i18n="steadi.sourceRole"',
  'data-i18n="steadi.tug.boundary"',
  'data-i18n="steadi.chair.noExtrapolation"',
  'data-i18n="steadi.balance.noDevice"',
  'data-i18n="steadi.balance.sequence"',
  'data-i18n="steadi.ortho.noPulseThreshold"',
  'data-i18n="steadi.ortho.boundary"'
]) {
  assert(
    html.includes(token),
    token
  );
}


const chairAge =
  html.match(
    /<input\s+id="steadi-chair-age"[\s\S]*?>/
  );


assert(
  chairAge
);


assert(
  chairAge[0].includes(
    'min="60"'
  )
);


assert(
  !chairAge[0].includes(
    'max='
  )
);


for (const id of [
  'steadi-balance-side',
  'steadi-balance-semi',
  'steadi-balance-tandem',
  'steadi-balance-one-leg'
]) {
  const match =
    html.match(
      new RegExp(
        `<input\\s+id="${id}"[\\s\\S]*?>`
      )
    );

  assert(
    match,
    id
  );

  assert(
    match[0].includes(
      'min="0"'
    )
  );

  assert(
    match[0].includes(
      'max="10"'
    )
  );
}


for (const optionalId of [
  'steadi-balance-semi',
  'steadi-balance-tandem',
  'steadi-balance-one-leg'
]) {
  const match =
    html.match(
      new RegExp(
        `<input\\s+id="${optionalId}"[\\s\\S]*?>`
      )
    );

  assert(
    !match[0].includes(
      ' required'
    ),
    `${optionalId} must remain optional for early stop`
  );
}


for (const key of [
  '"steadi.title"',
  '"steadi.badge"',
  '"steadi.boundary"',
  '"steadi.tug.title"',
  '"steadi.tug.increased"',
  '"steadi.tug.boundary"',
  '"steadi.chair.title"',
  '"steadi.chair.noExtrapolation"',
  '"steadi.balance.title"',
  '"steadi.balance.noDevice"',
  '"steadi.ortho.title"',
  '"steadi.ortho.abnormal"',
  '"steadi.ortho.noPulseThreshold"',
  '"steadi.ortho.boundary"'
]) {
  assert.strictEqual(
    occurrences(
      i18n,
      key
    ),
    2,
    `expected PT + EN for ${key}`
  );
}


assert(
  i18n.includes(
    'Após 94 anos'
  )
);


assert(
  i18n.includes(
    'After age 94'
  )
);


assert(
  i18n.includes(
    'não permite dispositivo de auxílio'
  )
);


assert(
  i18n.includes(
    'does not permit an assistive device'
  )
);


assert(
  i18n.includes(
    'nenhum limiar de pulso'
  )
);


assert(
  i18n.includes(
    'does not invent a pulse threshold'
  )
);


// E2 requires dynamic app wiring to match the frozen DOM.
for (const token of [
  'function calculateSteadiTugTool',
  'function calculateSteadiChairStandTool',
  'function calculateSteadiBalanceTool',
  'function calculateSteadiOrthostaticTool',
  "'steadi-tug-form': calculateSteadiTugTool",
  "'steadi-chair-form': calculateSteadiChairStandTool",
  "'steadi-balance-form': calculateSteadiBalanceTool",
  "'steadi-orthostatic-form': calculateSteadiOrthostaticTool"
]) {
  assert(
    app.includes(token),
    `missing wired-state contract: ${token}`
  );
}



assert(
  sw.includes(
    'clinical-reference-v24-v2-serial-trends-ui'
  )
);


assert(
  !sw.includes(
    'clinical-reference-v21-v2-brazil-falls-function'
  )
);


console.log(
  'steadi_ui_static_qc: bilingual complementary STEADI DOM + current cache PASS'
);
