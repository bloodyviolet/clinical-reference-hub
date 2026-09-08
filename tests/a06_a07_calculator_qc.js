'use strict';

const assert = require('assert');
const fs = require('fs');
const vm = require('vm');

const appScript = fs.readFileSync(
  'assets/app.js',
  'utf8',
);

const elements = new Map();

function element(id) {
  if (!elements.has(id)) {
    elements.set(id, {
      id,
      value: '',
      innerHTML: '',
      textContent: '',
      className: '',
      classList: {
        add() {},
        remove() {},
      },
      setAttribute() {},
      addEventListener() {},
    });
  }

  return elements.get(id);
}

function set(id, value = '') {
  const target = element(id);
  target.value = String(value);
  target.innerHTML = '';
  return target;
}

const document = {
  getElementById: element,
  querySelectorAll() {
    return [];
  },
  addEventListener() {},
};

const context = {
  console,
  document,
  navigator: {
    onLine: true,
  },
  window: {},
  URL,
  setTimeout,
  clearTimeout,
};

vm.createContext(context);

vm.runInContext(
  appScript,
  context,
  {
    filename: 'assets/app.js',
  },
);

const event = {
  preventDefault() {},
};

// A06 — exact older-adult boundaries.
set('bmi-age', 60);
set('bmi-h', 1);
set('bmi-result');

set('bmi-w', 22);
context.calculateBMI(event);

assert(
  element('bmi-result').innerHTML.includes(
    'Baixo peso (risco nutricional)',
  ),
);

set('bmi-w', 22.01);
context.calculateBMI(event);

assert(
  element('bmi-result').innerHTML.includes(
    'Adequado (eutrófico)',
  ),
);

set('bmi-w', 26.99);
context.calculateBMI(event);

assert(
  element('bmi-result').innerHTML.includes(
    'Adequado (eutrófico)',
  ),
);

set('bmi-w', 27);
context.calculateBMI(event);

assert(
  element('bmi-result').innerHTML.includes(
    'Sobrepeso',
  ),
);

// A07 — mathematically positive tiny medication
// result must never become 0.000 mL.
set('med-presc', 0.001);
set('med-disp', 1000);
set('med-vol', 0.01);
set('med-presc-unit', 'mg');
set('med-disp-unit', 'mg');
set('med-result');

context.calculateMeds(event);

const medHtml = element(
  'med-result',
).innerHTML;

assert(
  medHtml.includes('<0.001 mL'),
);

assert(
  medHtml.includes(
    'Não interprete nem arredonde como zero',
  ),
);

assert(
  !medHtml.includes('0.000 mL'),
);

// A07 — tiny positive drip flow must not display
// as integer zero.
set('drip-v', 1);
set('drip-t', 100000);
set('drip-u', 'm');
set('drip-result');

context.calculateDrip(event);

const dripHtml = element(
  'drip-result',
).innerHTML;

assert(
  dripHtml.includes('<0.001'),
);

assert(
  dripHtml.includes(
    'Não arredonde para zero',
  ),
);

assert(
  dripHtml.includes(
    '20 gotas/mL',
  ),
);

assert(
  dripHtml.includes(
    '60 microgotas/mL',
  ),
);

console.log(
  'a06_a07_calculator_qc: '
  + 'BMI boundaries, adaptive non-zero display, '
  + 'and explicit drip factors PASS',
);
