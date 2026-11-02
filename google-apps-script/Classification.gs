/**
 * Classificação interna PROVISÓRIA (determinística, versão score-v1). Serve só para prioridade e encaminhamento:
 * não rejeita contatos, não infere capacidade financeira, não é mostrada ao visitante e admite correção humana.
 * Pesos máximos: aderência 3, papel 3, consequência 3, horizonte 2, prontidão 2 (total 13). A >= 10, B >= 6, C abaixo.
 */
var PONTUACAO = {
  role: { decides: 3, leads_evaluation: 2, technical_participant: 1, early_research: 0, other: 0 },
  horizonte: { up_to_7_days: 2, '8_to_30_days': 2, '31_to_90_days': 1, after_90_days: 0, undefined: 0 },
  faixaA: 10, faixaB: 6
};
var PRODUTOS_POR_PROBLEMA = { schedule: 'P06', margin_cost: 'P07', measurement_receipt: 'P09', scope_change: 'P09', team_equipment_material: 'P08',
  project_info: 'P02', quality: 'P10', supplier: 'P05', undefined_responsibilities: 'P01' };
var PRODUTOS_POR_AVALIACAO = { land: 'P03', projects: 'P02', budget_costs: 'P04', supplier_proposals: 'P05', planning_resources: 'P06',
  measurement_change: 'P09', handover: 'P11', documentation_databook: 'P12' };
var PRODUTO_POR_ETAPA = { delay_or_critical: 'P07', execution: 'P10', near_completion: 'P11', planning: 'P06' };

function pontuar_(lead) {
  var s = lead.scenario, cons = s.consequences;
  var relevancia = s.entryPath !== 'other_or_unsure' ? 3 : (s.narrative.length >= 80 ? 2 : 1);
  var papel = PONTUACAO.role[s.decisionRole] || 0;
  var consequencia = 0;
  if (cons.length) {
    var alta = cons.some(function (c) { return LISTAS.HIGH_CONSEQUENCES.indexOf(c) >= 0; });
    consequencia = Math.min(3, 1 + (alta ? 1 : 0) + (cons.length >= 2 ? 1 : 0));
  }
  var tempo = PONTUACAO.horizonte[s.decisionHorizon] || 0;
  var docs = s.availableDocuments.filter(function (d) { return d !== 'none_organized'; });
  var prontidao = docs.length >= 3 ? 2 : (docs.length ? 1 : 0);
  var total = relevancia + papel + consequencia + tempo + prontidao;
  return { relevanceScore: relevancia, decisionRoleScore: papel, consequenceScore: consequencia, timingScore: tempo, readinessScore: prontidao,
    totalScore: total, priority: total >= PONTUACAO.faixaA ? 'A' : (total >= PONTUACAO.faixaB ? 'B' : 'C'), ruleVersion: CRIVIA.SCORE_RULE_VERSION };
}

function produtosCandidatos_(lead) {
  var s = lead.scenario, saida = [];
  var somar = function (c) { if (c && saida.indexOf(c) < 0) saida.push(c); };
  if (s.entryPath === 'underperforming') {
    s.issues.forEach(function (i) { somar(PRODUTOS_POR_PROBLEMA[i]); });
    somar(PRODUTO_POR_ETAPA[s.stage]);
    if (!saida.length || s.issues.indexOf('undefined_responsibilities') >= 0 || s.stage === 'unsure') somar('P01');
  } else if (s.entryPath === 'decision_support') {
    (s.branchSpecificData.evaluate || []).forEach(function (i) { somar(PRODUTOS_POR_AVALIACAO[i]); });
  } else if (s.entryPath === 'visual_communication') somar('CV01');
  else if (s.entryPath === 'ai_decision_engineering') somar('IA');
  return saida;   // rota "outro/ainda não sei": vazio = a revisão humana define o enquadramento
}

function informacoesAusentes_(lead) {
  var s = lead.scenario, f = [];
  if (!s.decisionHorizon || s.decisionHorizon === 'undefined') f.push('decision_horizon');
  if (!s.availableDocuments.length || (s.availableDocuments.length === 1 && s.availableDocuments[0] === 'none_organized')) f.push('organized_documents');
  if (!s.estimatedRange || s.estimatedRange === 'undisclosed' || s.estimatedRange === 'unknown') f.push('estimated_range');
  if (s.narrative.length < 80) f.push('narrative_detail');
  if (s.decisionRole === 'early_research') f.push('decision_owner');
  return f;
}

function enquadrar_(lead) {
  var q = pontuar_(lead);
  q.candidateProducts = produtosCandidatos_(lead);
  q.missingInformation = informacoesAusentes_(lead);
  return q;
}
