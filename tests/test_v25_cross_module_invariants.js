const fs = require('fs');
const vm = require('vm');
const assert = require('assert');
const source = fs.readFileSync('_all.js', 'utf8');

function declaration(name) {
  const start = source.lastIndexOf('function ' + name + '(');
  assert(start >= 0, 'Fonction de production absente : ' + name);
  const end = source.indexOf('\nfunction ', start + 10);
  return source.slice(start, end >= 0 ? end : source.length);
}

const modelNames = [
  'gradeNumber',
  'evaluationModelMaxScore',
  'evaluationModelCoefficient',
  'evaluationModelTerms',
  'evaluationModelTerm',
  'evaluationModelDate',
  'evaluationModelInTerm',
  'evaluationModelPublished',
  'evaluationModelTargetStudents',
  'evaluationModelGrade',
  'evaluationModelNumericGrade',
  'evaluationModelOn20',
  'evaluationModelVisible',
  'evaluationModelAverage',
  'evaluationModelClassStats',
  'weightedAverageForEvaluations',
  'v101StudentAverage',
  'evaluationGradeLabel'
];
const context = {
  db: { students: [], evaluations: [], settings: { terms: [] } },
  iso: function () { return '2026-11-26'; }
};
vm.createContext(context);
vm.runInContext(modelNames.map(declaration).join('\n\n'), context);

let checks = 0;
function equal(actual, expected, message) {
  assert.strictEqual(actual, expected, message);
  checks += 1;
}
function truthy(value, message) {
  assert.ok(value, message);
  checks += 1;
}
function makeEvaluation(id, value, maxScore, extras) {
  const e = {
    id: id,
    classId: 'c1',
    group: 'A',
    subject: 'Mathématiques',
    date: '2026-11-10',
    published: true,
    coefficient: 1,
    grades: [{ studentId: 's1', value: value }]
  };
  if (maxScore !== undefined) e.maxScore = maxScore;
  return Object.assign(e, extras || {});
}
function setData(evaluations, terms) {
  context.db = {
    students: [
      { id: 's1', classId: 'c1', group: 'A' },
      { id: 's2', classId: 'c1', group: 'B' },
      { id: 's3', classId: 'c2', group: 'A' }
    ],
    evaluations: evaluations,
    settings: { terms: terms || [{ id: 'T1', start: '2026-09-01', end: '2026-12-31' }] }
  };
}
function average() {
  return context.v101StudentAverage('s1', 'T1');
}
function numberOn20(value, max) {
  return Number(((Number(String(value).replace(',', '.')) / max) * 20).toFixed(2));
}

// 1) Thirteen source scales x five representative values. Each scale is
// checked both for its displayed label and the normalized overall average.
const scales = [1, 2, 4, 5, 10, 12, 15, 20, 25, 30, 40, 50, 100];
for (const max of scales) {
  const values = [0, max / 4, max / 3, max / 2, max * 2 / 3, max * 0.75, max];
  for (const value of values) {
    const raw = String(value);
    const e = { id: 'scale-' + max + '-' + raw, maxScore: max };
    const g = { studentId: 's1', value: raw };
    equal(
      context.evaluationGradeLabel(e, g),
      raw + ' /' + max,
      'Le score ' + raw + ' doit conserver son barème /' + max
    );
    setData([makeEvaluation(e.id, raw, max)]);
    equal(
      average(),
      numberOn20(value, max).toFixed(2),
      'La moyenne sur 20 doit normaliser ' + raw + '/' + max
    );
  }
}

// 2) Legacy records without maxScore default to /20. Zero is a valid grade;
// comma decimals remain accepted without changing the displayed source value.
equal(context.evaluationGradeLabel({}, { value: '8' }), '8 /20', 'Un barème absent conserve la compatibilité /20');
setData([makeEvaluation('legacy-default-max', '8', undefined)]);
equal(average(), '8.00', 'Une ancienne note sans barème explicite reste sur 20');
equal(context.evaluationGradeLabel({ maxScore: 10 }, { value: '0' }), '0 /10', 'Une note nulle n’est pas assimilée à une absence de note');
setData([makeEvaluation('zero-grade', '0', 10)]);
equal(average(), '0.00', 'Une note zéro doit compter dans la moyenne');
equal(context.evaluationGradeLabel({ maxScore: 10 }, { value: '7,5' }), '7,5 /10', 'Une virgule décimale garde son affichage original');
setData([makeEvaluation('comma-grade', '7,5', 10)]);
equal(average(), '15.00', 'Une virgule décimale est convertie correctement sur 20');

// 3) Overall averages must use the same publication, class, group and period
// rules as subject averages. Drafts, future publications and invalid scores
// must not contaminate the student's bulletin.
setData([
  makeEvaluation('valid-a', '8', 10, { coefficient: 2 }),
  makeEvaluation('valid-b', '18', 20, { coefficient: 1 }),
  makeEvaluation('draft', '20', 20, { published: false, coefficient: 100 }),
  makeEvaluation('missing-published-flag', '20', 20, { published: undefined, coefficient: 100 }),
  makeEvaluation('future-date-only', '20', 20, { publishAt: '2026-12-01', coefficient: 100 }),
  makeEvaluation('future-timestamp', '20', 20, { publishAt: '2026-12-01T10:00:00+01:00', coefficient: 100 }),
  makeEvaluation('invalid-timestamp', '20', 20, { publishAt: 'not-a-date', coefficient: 100 }),
  makeEvaluation('other-group', '20', 20, { group: 'B', coefficient: 100 }),
  makeEvaluation('other-class', '20', 20, { classId: 'c2', coefficient: 100 }),
  makeEvaluation('before-term', '20', 20, { date: '2026-08-31', coefficient: 100 }),
  makeEvaluation('after-term', '20', 20, { date: '2027-01-01', coefficient: 100 }),
  makeEvaluation('invalid-score', '21', 20, { coefficient: 100 })
]);
equal(average(), '16.67', 'Le bulletin doit agréger uniquement les notes publiées et pertinentes (16.67 attendu)');

// An absent publication flag is private everywhere. It must not be
// counted as a published evaluation by the teacher dashboard statistics.
equal(
  context.evaluationModelPublished({ id: 'legacy-no-flag' }, exactNow),
  false,
  'Une évaluation sans état publié explicite doit rester privée'
);
setData([
  makeEvaluation('published-stat', '12', 20),
  makeEvaluation('legacy-no-flag-stat', '20', 20, { published: undefined })
]);
const legacyStats = context.evaluationModelClassStats(context.db, 'c1', '', exactNow);
equal(legacyStats.evaluations, 1, 'Les statistiques ne doivent compter que les évaluations explicitement publiées');
equal(legacyStats.graded, 1, 'Les notes d’une évaluation sans état publié ne doivent pas entrer dans les statistiques');

// 4) A publication matrix crosses three publication flags with six scheduling
// states. The expected result is derived independently from the model.
const publicationFlags = [true, false, undefined];
const publicationDates = [
  ['', true],
  ['2026-11-25', true],
  ['2026-11-26', true],
  ['2026-11-27', false],
  ['2026-11-27T09:00:00+01:00', false],
  ['invalid-timestamp', false]
];
for (const published of publicationFlags) {
  for (const item of publicationDates) {
    const publishAt = item[0];
    const expectedVisible = published === true && item[1];
    setData([makeEvaluation('publication-matrix', '10', 20, {
      published: published,
      publishAt: publishAt
    })]);
    equal(
      average(),
      expectedVisible ? '10.00' : '—',
      'Publication=' + String(published) + ', date=' + (publishAt || '(vide)')
    );
  }
}

// 5) Same-day timestamp scheduling must be compared to the exact instant,
// not to midnight or the end of the calendar day.
const exactNow = '2026-11-26T10:00:00.000Z';
equal(
  context.evaluationModelPublished({ published: true, publishAt: '2026-11-26T09:59:59.000Z' }, exactNow),
  true,
  'Une publication programmée une seconde avant doit être disponible'
);
equal(
  context.evaluationModelPublished({ published: true, publishAt: '2026-11-26T10:00:00.000Z' }, exactNow),
  true,
  'Une publication programmée à l’instant exact doit être disponible'
);
equal(
  context.evaluationModelPublished({ published: true, publishAt: '2026-11-26T10:00:01.000Z' }, exactNow),
  false,
  'Une publication programmée une seconde après doit rester masquée'
);
equal(
  context.evaluationModelPublished({ published: true, publishAt: '2026-11-26T11:00:00+01:00' }, exactNow),
  true,
  'Les horodatages avec décalage doivent être comparés en UTC'
);
equal(
  context.evaluationModelPublished({ published: true, publishAt: '2026-11-26T11:00:01+01:00' }, exactNow),
  false,
  'Un décalage de fuseau ne doit pas rendre visible une publication future'
);

// 6) Term boundaries are inclusive; dates immediately outside the period
// are excluded. With no selected period, valid historic grades stay available.
for (const date of ['2026-09-01', '2026-12-31']) {
  setData([makeEvaluation('boundary-' + date, '15', 20, { date: date })]);
  equal(average(), '15.00', 'La borne de période ' + date + ' est incluse');
}
for (const date of ['2026-08-31', '2027-01-01']) {
  setData([makeEvaluation('outside-' + date, '15', 20, { date: date })]);
  equal(average(), '—', 'La date ' + date + ' hors période est exclue');
}
setData([makeEvaluation('no-term-filter', '13', 20, { date: '2025-01-15' })]);
equal(context.v101StudentAverage('s1', ''), '13.00', 'Sans période sélectionnée, les périodes historiques restent consultables');

// 7) Coefficients are applied once. Invalid and non-positive values use the
// canonical default coefficient of one.
const coefficients = [0, -1, 'invalid', 1, 2, 3, 0.5];
for (const coefficient of coefficients) {
  setData([
    makeEvaluation('coef-a', '10', 20, { coefficient: coefficient }),
    makeEvaluation('coef-b', '20', 20, { coefficient: 1 })
  ]);
  const numeric = Number(coefficient);
  const effective = numeric > 0 && Number.isFinite(numeric) ? numeric : 1;
  const expected = ((10 * effective + 20) / (effective + 1)).toFixed(2);
  equal(average(), expected, 'Coefficient ' + coefficient + ' doit être pondéré une seule fois');
}

// 8) Invalid, absent, negative and out-of-scale values cannot distort a
// valid neighboring grade.
const invalidValues = ['', null, undefined, 'abc', 'Infinity', -1, 21, 1000];
for (const value of invalidValues) {
  setData([
    makeEvaluation('invalid-' + String(value), value, 20),
    makeEvaluation('valid-neighbor', '12', 20)
  ]);
  equal(average(), '12.00', 'Valeur invalide ' + String(value) + ' ignorée');
}
equal(context.evaluationModelNumericGrade({ maxScore: 20 }, { value: '-1' }), null, 'Une note négative doit être rejetée par le moteur numérique');
equal(context.evaluationModelNumericGrade({ maxScore: 20 }, { value: '21' }), null, 'Une note supérieure au barème doit être rejetée par le moteur numérique');
equal(context.evaluationGradeLabel({ maxScore: 20 }, { value: '-1' }), 'Non noté', 'Une note négative ne doit pas être présentée comme une note valide');
equal(context.evaluationGradeLabel({ maxScore: 20 }, { value: '21' }), 'Non noté', 'Une note hors barème ne doit pas être présentée comme valide');
equal(context.evaluationGradeLabel({}, null), 'Non noté', 'Une absence de note est explicitement indiquée');
equal(context.evaluationGradeLabel({}, { value: '' }), 'Non noté', 'Une note vide est explicitement indiquée');
equal(
  context.evaluationGradeLabel({}, { value: '', criterionScores: { c1: 2 } }),
  'Évaluation qualitative',
  'Une grille qualitative est identifiée comme telle'
);

// 9) Ensure all the audited views use the same grade-scale helper.
for (const name of ['studentActivityCenter', 'studentHome', 'profile360Tab', 'openStudent']) {
  const body = declaration(name);
  truthy(body.includes('evaluationGradeLabel('), name + ' doit appeler le helper commun de barème');
  truthy(!/g\.value.{0,35}\/20/.test(body), name + ' ne doit plus imposer /20 à une note brute');
}
truthy(
  source.includes('function evaluationGradeLabel(e,g)'),
  'Le helper central doit être présent dans le bundle'
);
truthy(
  source.includes('function v101StudentAverage(id,termId=\'\'){const today=new Date().toISOString(),es='),
  'La moyenne du bulletin doit utiliser le modèle publié commun et l’horodatage exact'
);
truthy(
  declaration('subjectAverage').includes('today=new Date().toISOString()'),
  'La moyenne par matière doit respecter l’heure exacte de publication'
);
truthy(
  declaration('evaluationModelDashboardStats').includes('today=new Date().toISOString()'),
  'Le tableau de bord des évaluations doit respecter l’heure exacte de publication'
);

console.log('OK — ' + checks + ' invariants testés : barèmes, moyennes de bulletin, publication, périodes, groupes et vues élève.');
