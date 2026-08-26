/* ==========================================
   SISTEMA DE CHAMADA LEGO - JAVASCRIPT
   ========================================== */

// --- TOAST NOTIFICATIONS ---
function showToast(message, type = 'success') {
  let container = document.getElementById('toastContainer');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let icon = '🧱';
  if (type === 'success') icon = '✅';
  if (type === 'error') icon = '❌';
  if (type === 'info') icon = 'ℹ️';

  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.transition = 'opacity 0.3s, transform 0.3s';
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// --- CONFETTI EFFECT (COMEMORAÇÃO LEGO) ---
function triggerLegoConfetti() {
  const count = 50;
  const colors = ['#E3000B', '#FFD700', '#0055BF', '#00852B', '#FF7700', '#7B1FA2'];
  
  for (let i = 0; i < count; i++) {
    const confetti = document.createElement('div');
    confetti.style.position = 'fixed';
    confetti.style.width = Math.random() * 12 + 8 + 'px';
    confetti.style.height = Math.random() * 8 + 6 + 'px';
    confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
    confetti.style.left = Math.random() * 100 + 'vw';
    confetti.style.top = '-20px';
    confetti.style.borderRadius = '2px';
    confetti.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
    confetti.style.zIndex = '99999';
    confetti.style.pointerEvents = 'none';
    confetti.style.transform = `rotate(${Math.random() * 360}deg)`;
    
    document.body.appendChild(confetti);

    const fallDuration = Math.random() * 2 + 1.5;
    const horizontalDrift = (Math.random() - 0.5) * 200;

    confetti.animate([
      { transform: `translate(0, 0) rotate(0deg)`, opacity: 1 },
      { transform: `translate(${horizontalDrift}px, 100vh) rotate(${Math.random() * 720}deg)`, opacity: 0 }
    ], {
      duration: fallDuration * 1000,
      easing: 'cubic-bezier(.25,.46,.45,.94)'
    }).onfinish = () => confetti.remove();
  }
}

// --- MODAL CONTROLS ---
function openModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.add('show');
}

function closeModal(modalId) {
  const m = document.getElementById(modalId);
  if (m) m.classList.remove('show');
}

// Fecha modal clicando fora
document.addEventListener('click', (e) => {
  if (e.target.classList.contains('modal-backdrop')) {
    e.target.classList.remove('show');
  }
});


// ==========================================
// MÓDULO DE CHAMADA (ATTENDANCE)
// ==========================================

let chamadasState = {}; // aluno_id -> { status, justificativa, pontos_bonus, motivo_bonus }

function initAttendancePage(turmaId, dataStr) {
  carregarChamada(turmaId, dataStr);
}

async function carregarChamada(turmaId, dataStr) {
  const container = document.getElementById('studentsGrid');
  if (!container) return;

  container.innerHTML = `
    <div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-muted);">
      <div style="font-size: 2rem; animation: spin 1s infinite linear;">⚙️</div>
      <p style="margin-top: 10px; font-weight: 700;">Carregando alunos da Turma Lego...</p>
    </div>
  `;

  try {
    const res = await fetch(`/api/chamada/carregar?turma_id=${turmaId}&data=${dataStr}`);
    const data = await res.json();

    if (data.error) {
      container.innerHTML = `<div style="grid-column: 1/-1; color: var(--lego-red); text-align: center;">${data.error}</div>`;
      return;
    }

    // Preenche campos do formulário
    const topicoInput = document.getElementById('topicoAula');
    if (topicoInput) topicoInput.value = data.topico || 'Oficina Lego';
    
    const obsInput = document.getElementById('observacoesAula');
    if (obsInput) obsInput.value = data.observacoes || '';

    const proxInput = document.getElementById('proximaAula');
    if (proxInput) proxInput.value = data.proxima_aula || '';

    const badgeStatus = document.getElementById('statusChamadaBadge');
    if (badgeStatus) {
      if (data.existe_sessao) {
        badgeStatus.innerHTML = `<span style="background: var(--lego-green-light); color: var(--lego-green-dark); padding: 4px 10px; border-radius: 6px; font-weight: 700;">✅ Chamada já registrada (Modo Edição)</span>`;
      } else {
        badgeStatus.innerHTML = `<span style="background: var(--lego-yellow-light); color: var(--lego-yellow-dark); padding: 4px 10px; border-radius: 6px; font-weight: 700;">📝 Nova Chamada para ${dataStr}</span>`;
      }
    }

    // Inicializa estado e renderiza cards
    chamadasState = {};
    container.innerHTML = '';

    if (data.alunos.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 40px; background: white; border-radius: 12px; border: 2px dashed #CBD5E1;">
          <div style="font-size: 3rem;">🧱</div>
          <h3 style="margin: 10px 0;">Nenhum aluno cadastrado nesta turma</h3>
          <p style="color: var(--text-muted); margin-bottom: 16px;">Adicione alunos na aba "Gerenciar Alunos" para poder realizar a chamada.</p>
          <a href="/alunos?turma_id=${turmaId}" class="btn-lego btn-blue">Cadastrar Alunos</a>
        </div>
      `;
      return;
    }

    data.alunos.forEach(item => {
      const a = item.aluno;
      chamadasState[a.id] = {
        status: item.status || 'presente',
        justificativa: item.justificativa || '',
        pontos_bonus: item.pontos_bonus || 0,
        motivo_bonus: item.motivo_bonus || ''
      };

      const card = renderStudentCallCard(a, chamadasState[a.id]);
      container.appendChild(card);
    });

    atualizarResumoContadores();

  } catch (err) {
    console.error(err);
    container.innerHTML = `<div style="grid-column: 1/-1; color: var(--lego-red); text-align: center;">Erro ao carregar dados da chamada.</div>`;
  }
}

function renderStudentCallCard(aluno, state) {
  const card = document.createElement('div');
  card.id = `card-aluno-${aluno.id}`;
  card.className = `student-call-card status-${state.status}`;

  // Avatar emoji baseado no tipo
  let avatarIcon = '🧱';
  if (aluno.avatar_tipo === 'lego-ninja') avatarIcon = '🥷';
  else if (aluno.avatar_tipo === 'lego-astronaut') avatarIcon = '👨‍🚀';
  else if (aluno.avatar_tipo === 'lego-purple') avatarIcon = '🧙';
  else if (aluno.avatar_tipo === 'lego-green') avatarIcon = '🦖';
  else if (aluno.avatar_tipo === 'lego-orange') avatarIcon = '🏎️';
  else if (aluno.avatar_tipo === 'lego-blue') avatarIcon = '🤖';
  else if (aluno.avatar_tipo === 'lego-yellow') avatarIcon = '😀';
  else avatarIcon = '🦸';

  card.innerHTML = `
    <div>
      <div class="student-profile-header">
        <div class="avatar-lego ${aluno.avatar_tipo || 'avatar-red'}">${avatarIcon}</div>
        <div style="flex: 1;">
          <div class="student-info-name">${aluno.nome}</div>
          <div class="student-team-tag">👥 ${aluno.equipe || 'Equipe Lego'}</div>
        </div>
        <div class="student-xp-pill">
          <span>⭐</span>
          <span>${aluno.pontos_xp} XP</span>
        </div>
      </div>

      <div class="status-buttons-group">
        <button type="button" class="btn-status btn-pres ${state.status === 'presente' ? 'active' : ''}" onclick="setStudentStatus(${aluno.id}, 'presente')">
          <span>✅</span>
          <span>Presente (+10)</span>
        </button>
        <button type="button" class="btn-status btn-falt ${state.status === 'falta' ? 'active' : ''}" onclick="setStudentStatus(${aluno.id}, 'falta')">
          <span>❌</span>
          <span>Falta (0)</span>
        </button>
        <button type="button" class="btn-status btn-just ${state.status === 'justificada' ? 'active' : ''}" onclick="setStudentStatus(${aluno.id}, 'justificada')">
          <span>⚠️</span>
          <span>Justif. (+2)</span>
        </button>
      </div>

      <!-- Justificativa (se falta ou justificada) -->
      <div id="justif-box-${aluno.id}" style="display: ${state.status === 'justificada' ? 'block' : 'none'}; margin-bottom: 8px;">
        <input type="text" class="input-lego" placeholder="Motivo da justificativa..." 
               value="${state.justificativa}" 
               oninput="updateJustificativa(${aluno.id}, this.value)" style="font-size: 0.8rem; padding: 6px;">
      </div>

      <!-- Bônus XP Lego (Engajamento / Trabalho em equipe) -->
      <div class="student-bonus-drawer">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span style="font-weight: 700; color: #475569;">🎁 Bônus Lego:</span>
          <div style="display: flex; gap: 4px;">
            <button type="button" class="btn-lego btn-yellow btn-sm" style="padding: 2px 6px; font-size: 0.75rem;" onclick="addBonusXP(${aluno.id}, 5, 'Destaque de Organização')">+5 Org</button>
            <button type="button" class="btn-lego btn-blue btn-sm" style="padding: 2px 6px; font-size: 0.75rem;" onclick="addBonusXP(${aluno.id}, 5, 'Trabalho em Equipe')">+5 Equipe</button>
            <button type="button" class="btn-lego btn-green btn-sm" style="padding: 2px 6px; font-size: 0.75rem;" onclick="addBonusXP(${aluno.id}, 10, 'Robô Funcional')">+10 Robô</button>
          </div>
        </div>
        <div id="bonus-info-${aluno.id}" style="font-size: 0.75rem; color: #0284C7; font-weight: 600; display: ${state.pontos_bonus > 0 ? 'block' : 'none'};">
          🌟 Bônus aplicado: +${state.pontos_bonus} XP (${state.motivo_bonus})
          <a href="javascript:void(0)" onclick="clearBonusXP(${aluno.id})" style="color: var(--lego-red); margin-left: 6px;">(remover)</a>
        </div>
      </div>
    </div>
  `;

  return card;
}

function setStudentStatus(alunoId, status) {
  if (!chamadasState[alunoId]) chamadasState[alunoId] = {};
  chamadasState[alunoId].status = status;

  const card = document.getElementById(`card-aluno-${alunoId}`);
  if (card) {
    card.className = `student-call-card status-${status}`;
    
    // Atualiza botões
    const btnPres = card.querySelector('.btn-pres');
    const btnFalt = card.querySelector('.btn-falt');
    const btnJust = card.querySelector('.btn-just');
    
    btnPres.classList.toggle('active', status === 'presente');
    btnFalt.classList.toggle('active', status === 'falta');
    btnJust.classList.toggle('active', status === 'justificada');

    // Mostra/oculta input de justificativa
    const justBox = document.getElementById(`justif-box-${alunoId}`);
    if (justBox) justBox.style.display = (status === 'justificada') ? 'block' : 'none';
  }

  atualizarResumoContadores();
}

function updateJustificativa(alunoId, val) {
  if (chamadasState[alunoId]) {
    chamadasState[alunoId].justificativa = val;
  }
}

function addBonusXP(alunoId, pts, motivo) {
  if (!chamadasState[alunoId]) chamadasState[alunoId] = {};
  chamadasState[alunoId].pontos_bonus = (chamadasState[alunoId].pontos_bonus || 0) + pts;
  chamadasState[alunoId].motivo_bonus = motivo;

  const info = document.getElementById(`bonus-info-${alunoId}`);
  if (info) {
    info.style.display = 'block';
    info.innerHTML = `🌟 Bônus aplicado: +${chamadasState[alunoId].pontos_bonus} XP (${motivo}) <a href="javascript:void(0)" onclick="clearBonusXP(${alunoId})" style="color: var(--lego-red); margin-left: 6px;">(remover)</a>`;
  }
  showToast(`+${pts} XP adicionados para ${motivo}!`, 'info');
}

function clearBonusXP(alunoId) {
  if (chamadasState[alunoId]) {
    chamadasState[alunoId].pontos_bonus = 0;
    chamadasState[alunoId].motivo_bonus = '';
  }
  const info = document.getElementById(`bonus-info-${alunoId}`);
  if (info) info.style.display = 'none';
}

function marcarTodos(status) {
  Object.keys(chamadasState).forEach(id => {
    setStudentStatus(id, status);
  });
  showToast(`Todos marcados como "${status.toUpperCase()}"!`, 'info');
}

function atualizarResumoContadores() {
  const ids = Object.keys(chamadasState);
  let pres = 0, falt = 0, just = 0;

  ids.forEach(id => {
    const st = chamadasState[id].status;
    if (st === 'presente') pres++;
    else if (st === 'falta') falt++;
    else if (st === 'justificada') just++;
  });

  const elPres = document.getElementById('countPresentes');
  const elFalt = document.getElementById('countFaltas');
  const elJust = document.getElementById('countJustificadas');
  const elTotal = document.getElementById('countTotal');

  if (elPres) elPres.innerText = pres;
  if (elFalt) elFalt.innerText = falt;
  if (elJust) elJust.innerText = just;
  if (elTotal) elTotal.innerText = ids.length;
}

async function salvarChamadaAtual(turmaId, dataStr) {
  const btnSalvar = document.getElementById('btnSalvarChamada');
  if (btnSalvar) {
    btnSalvar.disabled = true;
    btnSalvar.innerHTML = '⚙️ Salvando...';
  }

  const topico = document.getElementById('topicoAula') ? document.getElementById('topicoAula').value : 'Oficina Lego';
  const obs = document.getElementById('observacoesAula') ? document.getElementById('observacoesAula').value : '';
  const proximaAula = document.getElementById('proximaAula') ? document.getElementById('proximaAula').value : '';

  const registros = Object.keys(chamadasState).map(id => ({
    aluno_id: parseInt(id),
    status: chamadasState[id].status || 'presente',
    justificativa: chamadasState[id].justificativa || '',
    pontos_bonus: chamadasState[id].pontos_bonus || 0,
    motivo_bonus: chamadasState[id].motivo_bonus || ''
  }));

  try {
    const res = await fetch('/api/chamada/salvar', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        turma_id: turmaId,
        data: dataStr,
        topico: topico,
        observacoes: obs,
        proxima_aula: proximaAula,
        registros: registros
      })
    });

    const data = await res.json();
    if (data.success) {
      triggerLegoConfetti();
      showToast(`🎉 Chamada salva com sucesso! +${data.total_xp_distribuido} XP distribuídos!`, 'success');
      
      // Recarrega chamada para atualizar estado
      setTimeout(() => {
        window.location.href = `/historico?turma_id=${turmaId}&data=${dataStr}`;
      }, 1200);
    } else {
      showToast(data.error || 'Erro ao salvar chamada.', 'error');
    }
  } catch (err) {
    console.error(err);
    showToast('Erro de conexão ao salvar chamada.', 'error');
  } finally {
    if (btnSalvar) {
      btnSalvar.disabled = false;
      btnSalvar.innerHTML = '🧱 Salvar Chamada & Distribuir XP';
    }
  }
}


// ==========================================
// GESTÃO DE ALUNOS (CRUD)
// ==========================================

async function criarNovoAluno(e) {
  e.preventDefault();
  const form = e.target;
  const nome = form.nome.value;
  const turma_id = form.turma_id.value;
  const equipe = form.equipe.value;
  const avatar_tipo = form.avatar_tipo.value;
  const pontos_xp = form.pontos_xp.value || 0;

  try {
    const res = await fetch('/api/alunos', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ nome, turma_id, equipe, avatar_tipo, pontos_xp })
    });
    const data = await res.json();
    if (data.success) {
      showToast(`Aluno "${data.aluno.nome}" cadastrado com sucesso!`, 'success');
      closeModal('modalNovoAluno');
      setTimeout(() => location.reload(), 600);
    } else {
      showToast(data.error || 'Erro ao cadastrar aluno.', 'error');
    }
  } catch (err) {
    showToast('Erro ao comunicar com o servidor.', 'error');
  }
}

async function excluirAluno(alunoId, nome) {
  if (!confirm(`Tem certeza que deseja excluir o aluno "${nome}"? Todo o histórico de presença e XP será apagado.`)) return;

  try {
    const res = await fetch(`/api/alunos/${alunoId}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast('Aluno removido com sucesso!', 'success');
      setTimeout(() => location.reload(), 600);
    } else {
      showToast(data.error || 'Erro ao excluir aluno.', 'error');
    }
  } catch (err) {
    showToast('Erro ao comunicar com o servidor.', 'error');
  }
}

async function concederMedalhaAluno(alunoId, medalhaId) {
  try {
    const res = await fetch(`/api/alunos/${alunoId}/conceder-medalha`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ medalha_id: medalhaId })
    });
    const data = await res.json();
    if (data.success) {
      triggerLegoConfetti();
      showToast(data.message, 'success');
      setTimeout(() => location.reload(), 800);
    } else {
      showToast(data.error || 'Erro ao conceder medalha.', 'error');
    }
  } catch (err) {
    showToast('Erro de comunicação com o servidor.', 'error');
  }
}

async function ajustarXpManual(alunoId, quantidade, motivo) {
  try {
    const res = await fetch(`/api/alunos/${alunoId}/ajustar-xp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantidade, motivo })
    });
    const data = await res.json();
    if (data.success) {
      showToast(data.message, 'success');
      setTimeout(() => location.reload(), 600);
    }
  } catch (err) {
    showToast('Erro ao ajustar XP.', 'error');
  }
}

async function excluirChamadaHistorico(sessaoId) {
  if (!confirm("Tem certeza que deseja excluir esta chamada? Os pontos de XP atribuídos nela serão revertidos.")) return;

  try {
    const res = await fetch(`/api/historico/${sessaoId}`, { method: 'DELETE' });
    const data = await res.json();
    if (data.success) {
      showToast('Chamada excluída com sucesso!', 'success');
      setTimeout(() => location.reload(), 600);
    }
  } catch (err) {
    showToast('Erro ao excluir chamada.', 'error');
  }
}
