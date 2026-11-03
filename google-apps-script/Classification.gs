/**
 * Enquadramento interno (porta de servidor/regras_leads.py), versão score-v3. Serve só para PRIORIDADE e ENCAMINHAMENTO:
 * não rejeita contatos, não infere capacidade financeira, não é mostrada ao visitante e admite correção humana.
 * Os produtos são HIPÓTESE de triagem; o enquadramento final é humano. Máximo 16 pontos; faixas provisórias: A >= 10, B >= 6, C abaixo.
 */
var PONTUACAO_ = {
  role: { decides: 3, recommends: 2, gathering: 1, referring: 0, other_unsure: 0 },
  perfil: { contractor: 2, company_manager: 2, owner_investor: 1, technical_team: 1, other: 0 },
  urgencia: { immediate: 2, this_week: 2, this_month: 1, undefined: 0 },
  documentos: { yes: 2, partial: 1, no: 0, unknown: 0 },
  consequenciasAltas: ['penalty', 'stoppage', 'margin_cash_loss', 'contract_conflict'],
  faixaA: 10, faixaB: 6
};
var PRODUTOS_POR_SITUACAO_ = {
  obra_contrato_dificuldade: ['P01'], atraso_custo_margem: ['P08', 'P07'], projeto_terreno_propostas: ['P02', 'P03', 'P05'],
  planejamento_recursos_recuperacao: ['P06', 'P07'], medicao_alteracao_documentacao: ['P09', 'P12'], vistoria_recebimento_conferencia: ['P11'],
  comunicacao_ia_3d: ['CV01'], outra_nao_sei: []
};

function enquadrar_(lead) {
  var s = lead.scenario, n = s.narrative.length;
  var relevancia = s.situationCode !== 'outra_nao_sei' ? 3 : (n >= 200 ? 2 : 1);
  var papel = PONTUACAO_.role[s.decisionRole] || 0, perfil = PONTUACAO_.perfil[s.audienceProfile] || 0;
  var detalhe = n >= 200 ? 2 : n >= 80 ? 1 : 0;
  var tempo = PONTUACAO_.urgencia[s.urgency] || 0;
  var alta = s.consequences.some(function (c) { return PONTUACAO_.consequenciasAltas.indexOf(c) >= 0; });
  var consequencia = Math.min(2, (s.consequences.length ? 1 : 0) + (alta ? 1 : 0));
  var prontidao = PONTUACAO_.documentos[s.documents] || 0;
  var total = relevancia + papel + perfil + detalhe + tempo + consequencia + prontidao;
  var falta = [];
  if (!s.contextAnswerCode || s.contextAnswerCode === 'unknown') falta.push('context_answer');
  if (n < 80) falta.push('narrative_detail');
  if (['gathering', 'referring', 'other_unsure'].indexOf(s.decisionRole) >= 0) falta.push('decision_owner');
  if (!s.urgency || s.urgency === 'undefined') falta.push('decision_horizon');
  if (['', 'no', 'unknown'].indexOf(s.documents) >= 0) falta.push('documents');
  if (['', 'undisclosed', 'unknown'].indexOf(s.estimatedRange) >= 0) falta.push('estimated_range');
  return { relevanceScore: relevancia, decisionRoleScore: papel, audienceScore: perfil, detailScore: detalhe, timingScore: tempo, consequenceScore: consequencia,
    readinessScore: prontidao, totalScore: total, priority: total >= PONTUACAO_.faixaA ? 'A' : total >= PONTUACAO_.faixaB ? 'B' : 'C',
    ruleVersion: CRIVIA.SCORE_RULE_VERSION, candidateProducts: (PRODUTOS_POR_SITUACAO_[s.situationCode] || []).slice(), missingInformation: falta };
}
