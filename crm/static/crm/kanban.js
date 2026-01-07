(() => {
  'use strict';

  // ====== Настройки колонок (UI) ======
  // Эти статусы остаются как у тебя (показываем колонки фиксированно).
  const STATUSES = [
    { id: 'queue',      label: 'на очереди' },
    { id: 'inprogress', label: 'в процессе' },
    { id: 'help',       label: 'нужна помощь с задачей' },
    { id: 'blocked',    label: 'подвисло из-за заказчика' },
    { id: 'done',       label: 'выполнено' },
  ];

  const STATUS_LABEL_MAP = {};
STATUSES.forEach(s => {
  STATUS_LABEL_MAP[s.id] = s.label;
});


  // ====== DOM ======
  const activityBtn = document.getElementById('open-activity');
  const activityModal = document.getElementById('activity-modal');
  const activityList = document.getElementById('activity-list');

  const taskHistoryBox = document.getElementById('task-history');
  const taskHistoryList = document.getElementById('task-history-list');

  const boardEl = document.getElementById('board');
  const clearBtn = document.getElementById('clear-board');

  const modalEl = document.getElementById('modal');
  const formEl = document.getElementById('card-form');
  const modalTitleEl = document.getElementById('modal-title');
  const titleInput = /** @type {HTMLInputElement} */ (formEl.elements.namedItem('title'));
  const descInput = /** @type {HTMLTextAreaElement} */ (formEl.elements.namedItem('description'));
  const deadlineInput = /** @type {HTMLInputElement} */ (formEl.elements.namedItem('deadline'));
  const statusSelect = /** @type {HTMLSelectElement} */ (formEl.elements.namedItem('status'));
  const assigneeSelect = /** @type {HTMLSelectElement} */ (formEl.elements.namedItem('assignee'));
  const errorEl = document.getElementById('form-error');

  // project_id берём из data-project-id="{{ project.id }}" на #board
  const projectId = boardEl?.dataset.projectId;
  if (!projectId) {
    console.error('No projectId found on #board (data-project-id).');
    return;
  }

  // ====== API URLs ======
  const API_TASK_DELETE_URL = (taskId) => `/api/kanban/task/${taskId}/delete/`;
  const API_STATE_URL = `/api/kanban/${projectId}/`;
  const API_TASK_CREATE_URL = `/api/kanban/task/`;
  const API_TASK_URL = (taskId) => `/api/kanban/task/${taskId}/`;
  const API_REORDER_URL = `/api/kanban/reorder/`;
  const API_PROJECT_ACTIVITY_URL = `/api/kanban/project/${projectId}/activity/`;
  const API_TASK_HISTORY_URL = (taskId) => `/api/kanban/task/${taskId}/history/`;
  const API_ASSIGNEES_URL = `/api/kanban/${projectId}/assignees/`;



  // ====== State (теперь источник истины — сервер) ======
  let state = defaultState(); // локально держим только для рендера
  let assigneeOptions = null;
  const titleCache = Object.create(null);
  let modalCtx = { mode: 'create', cardId: null };
  let pollingTimer = null;

  document.addEventListener('DOMContentLoaded', init);

  function init() {
    buildBoardSkeleton();
    populateStatusSelect();
    attachEvents();
    loadAssignees();


    // начальная загрузка + polling (real-time)
    loadKanbanFromServer();
    pollingTimer = setInterval(loadKanbanFromServer, 3000);
  }

  function attachEvents() {
  boardEl.addEventListener('click', onBoardClick);
  boardEl.addEventListener('dblclick', onBoardDblClick);

  boardEl.addEventListener('dragstart', onDragStart);
  boardEl.addEventListener('dragend', onDragEnd);

  document.querySelectorAll('.cards').forEach((container) => {
    container.addEventListener('dragover', onDragOverCards);
  });

  modalEl.addEventListener('click', onModalClick);
  formEl.addEventListener('submit', onFormSubmit);
  document.addEventListener('keydown', onKeyDown);

  // "Сбросить доску"
  clearBtn.addEventListener('click', async () => {
    const ok = confirm('Сбросить доску? Все карточки будут удалены.');
    if (!ok) return;

    const ids = Object.keys(state.cards);
    for (const id of ids) {
      await apiDeleteTask(id);
    }
    await loadKanbanFromServer();
  });

  // ===== АКТИВНОСТЬ ПРОЕКТА (ИСТОРИЯ) =====
  if (activityBtn) {
    activityBtn.addEventListener('click', openActivity);
  }

  if (activityModal) {
    activityModal.addEventListener('click', (e) => {
      const close = e.target.closest('[data-action="closeActivity"]');
      if (close) closeActivity();
    });
  }
}


  // ====== UI Skeleton ======
  function buildBoardSkeleton() {
    const html = STATUSES.map(s => `
      <section class="column" data-status="${s.id}">
        <header class="column__header">
          <div class="column__title">
            <h2>${escapeHtml(s.label)}</h2>
            <span class="count" data-count="${s.id}">0</span>
          </div>
          <button class="btn btn--small" type="button" data-action="add" data-status="${s.id}">+ Добавить</button>
        </header>
        <div class="cards" data-status="${s.id}" aria-label="Колонка: ${escapeHtml(s.label)}"></div>
      </section>
    `).join('');
    boardEl.innerHTML = html;
  }

  function populateStatusSelect() {
    statusSelect.innerHTML = STATUSES
      .map(s => `<option value="${s.id}">${escapeHtml(s.label)}</option>`)
      .join('');
  }

  async function loadAssignees() {
      try {
        const resp = await fetch(API_ASSIGNEES_URL, { credentials: 'same-origin' });
        if (!resp.ok) throw new Error('assignees failed');
        assigneeOptions = await resp.json();
        populateAssigneeSelect();
      } catch (e) {
        console.error(e);
        assigneeOptions = [{ value: "", label: "—" }, { value: "customer", label: "Заказчик" }];
        populateAssigneeSelect();
      }
    }

    function populateAssigneeSelect(selectedValue = "") {
      if (!assigneeSelect) return;
      const opts = Array.isArray(assigneeOptions) ? assigneeOptions : [];
      assigneeSelect.innerHTML = opts
        .map(o => `<option value="${escapeHtml(o.value)}">${escapeHtml(o.label)}</option>`)
        .join('');
      assigneeSelect.value = selectedValue || "";
    }


  // ====== Click handlers ======
  function onBoardClick(e) {
    const btn = e.target.closest('button[data-action]');
    if (!btn) return;

    const action = btn.dataset.action;

    if (action === 'add') {
      const status = btn.dataset.status || 'queue';
      openModalCreate(status);
      return;
    }

    const cardEl = e.target.closest('.card');
    if (!cardEl) return;
    const cardId = cardEl.dataset.id;

    if (action === 'edit') {
      openModalEdit(cardId);
      return;
    }

    if (action === 'delete') {
      deleteCard(cardId);
      return;
    }
  }

  function onBoardDblClick(e) {
    const cardEl = e.target.closest('.card');
    if (!cardEl) return;
    openModalEdit(cardEl.dataset.id);
  }

  // ====== Modal ======
  function openModalCreate(status) {
    modalCtx = { mode: 'create', cardId: null };
    modalTitleEl.textContent = 'Новая карточка';
    errorEl.textContent = '';

    formEl.reset();
    statusSelect.value = status;
    populateAssigneeSelect("");


    showModal();
    taskHistoryBox.style.display = 'none';
    taskHistoryList.innerHTML = '';
    deadlineInput.value = "";


  }

  function openModalEdit(cardId) {
    const card = state.cards[cardId];
    if (!card) return;

    modalCtx = { mode: 'edit', cardId };
    modalTitleEl.textContent = 'Изменить карточку';
    errorEl.textContent = '';

    titleInput.value = card.title || '';
    descInput.value = card.description || '';
    statusSelect.value = card.status || 'queue';
    populateAssigneeSelect(card.assignee_value || "");
    deadlineInput.value = card.deadline || "";



    showModal();
    loadTaskHistory(cardId);
  }

  async function loadTaskHistory(cardId) {
  taskHistoryBox.style.display = 'block';
  taskHistoryList.textContent = 'Загрузка...';

  try {
    const resp = await fetch(API_TASK_HISTORY_URL(cardId), { credentials: 'same-origin' });
    if (!resp.ok) throw new Error('history failed');
    const items = await resp.json();
    taskHistoryList.innerHTML = renderHistory(items, 'task');
  } catch (e) {
    console.error(e);
    taskHistoryList.textContent = 'Не удалось загрузить историю.';
  }
}


function renderHistory(items, mode = 'task') {
  if (!Array.isArray(items) || items.length === 0) {
    return '<div style="color:#9ca3af;">История пуста</div>';
  }

  return items.map(it => {
    const who = escapeHtml(it.user_display || 'System');
    const when = escapeHtml(new Date(it.created_at).toLocaleString());
    const taskId = String(it.task ?? it.task_id ?? '');
    const cachedTitle =
        (it.new_data && it.new_data.title) ||
        (it.old_data && it.old_data.title) ||
        (taskId && titleCache[taskId]) ||
        (taskId && state.cards && state.cards[taskId] && state.cards[taskId].title) ||
        null;


    let text = it.action;

    // ===== MOVE =====
    if (it.action === 'move') {
  const fromLabel = STATUS_LABEL_MAP[it.from_column] || it.from_column;
  const toLabel = STATUS_LABEL_MAP[it.to_column] || it.to_column;

  if (mode === 'project' && cachedTitle) {
    text = `переместил карточку <b>"${escapeHtml(cachedTitle)}"</b> `
         + `из <b>${escapeHtml(fromLabel)}</b> в <b>${escapeHtml(toLabel)}</b>`;
  } else {
    text = `переместил из <b>${escapeHtml(fromLabel)}</b> в <b>${escapeHtml(toLabel)}</b>`;
  }
}


    // ===== CREATE =====
    else if (it.action === 'create') {
  if (mode === 'project' && cachedTitle) {
    text = `создал карточку <b>"${escapeHtml(cachedTitle)}"</b>`;
  } else {
    text = 'создал карточку';
  }
}


    // ===== UPDATE =====
    else if (it.action === 'update') {
  if (mode === 'project' && cachedTitle) {
    text = `обновил карточку <b>"${escapeHtml(cachedTitle)}"</b>`;
  } else {
    text = 'обновил карточку';
  }
}


    // ===== DELETE =====
    else if (it.action === 'delete') {
  if (mode === 'project' && cachedTitle) {
    text = `удалил карточку <b>"${escapeHtml(cachedTitle)}"</b>`;
  } else {
    text = 'удалил карточку';
  }
}


    // ===== REORDER =====
    else if (it.action === 'reorder') {
      text = 'изменил порядок карточек';
    }

    return `
      <div style="padding:6px 0; border-bottom:1px solid #263a57;">
        <div style="font-size:0.8rem; color:#9ca3af;">${when}</div>
        <div><b>${who}</b> — ${text}</div>
      </div>
    `;
  }).join('');
}



  function showModal() {
    modalEl.classList.remove('hidden');
    modalEl.setAttribute('aria-hidden', 'false');
    setTimeout(() => titleInput.focus(), 0);
  }

  function closeModal() {
    modalEl.classList.add('hidden');
    modalEl.setAttribute('aria-hidden', 'true');
    errorEl.textContent = '';
    formEl.reset();
  }

  function onModalClick(e) {
    const close = e.target.closest('[data-action="closeModal"]');
    if (close) closeModal();
  }

  function onKeyDown(e) {
    if (e.key === 'Escape' && !modalEl.classList.contains('hidden')) {
      closeModal();
    }
  }

  // ====== Form submit ======
  async function onFormSubmit(e) {
    e.preventDefault();

    const title = titleInput.value.trim();
    const description = descInput.value.trim();
    const status = statusSelect.value;
    const assignee = assigneeSelect ? assigneeSelect.value : "";
    const deadline = deadlineInput && deadlineInput.value
        ? deadlineInput.value
        : null;




    if (!title) {
      errorEl.textContent = 'Пожалуйста, заполните заголовок.';
      titleInput.focus();
      return;
    }
    if (!isValidStatus(status)) {
      errorEl.textContent = 'Некорректный этап.';
      return;
    }

    try {
      if (modalCtx.mode === 'create') {
        await apiCreateTask({ title, description, status, assignee, deadline });
        closeModal();
        await loadKanbanFromServer();
        return;
      }

      if (modalCtx.mode === 'edit' && modalCtx.cardId) {
        await apiPatchTask(modalCtx.cardId, { title, description, status, assignee, deadline });
        closeModal();
        await loadKanbanFromServer();
      }
    } catch (err) {
      console.error(err);
      errorEl.textContent = 'Ошибка сохранения. Попробуйте ещё раз.';
    }
  }

  // ====== CRUD (через API) ======
  async function createCardLocal({ id, title, description, status }) {
    // локально используем только для мгновенного UI (если захочешь optimistic)
    state.cards[id] = { id, title, description, status, createdAt: Date.now(), updatedAt: Date.now() };
    state.order[status].unshift(id);
    renderAllColumns();
  }

  async function deleteCard(cardId) {
    const ok = confirm('Удалить карточку?');
    if (!ok) return;

    try {
      if (state.cards[cardId] && state.cards[cardId].title) {
            titleCache[String(cardId)] = state.cards[cardId].title;
        }

      await apiDeleteTask(cardId);
      await loadKanbanFromServer();
    } catch (err) {
      console.error(err);
      alert('Не удалось удалить карточку.');
    }
  }

  async function openActivity() {
  activityModal.classList.remove('hidden');
  activityModal.setAttribute('aria-hidden', 'false');
  activityList.textContent = 'Загрузка...';

  try {
    const resp = await fetch(API_PROJECT_ACTIVITY_URL, { credentials: 'same-origin' });
    if (!resp.ok) throw new Error('activity failed');
    const items = await resp.json();
    activityList.innerHTML = renderHistory(items, 'project');
  } catch (e) {
    console.error(e);
    activityList.textContent = 'Не удалось загрузить активность.';
  }
}

function closeActivity() {
  activityModal.classList.add('hidden');
  activityModal.setAttribute('aria-hidden', 'true');
  activityList.innerHTML = '';
}


  // ====== Render ======
  function renderAllColumns() {
    STATUSES.forEach(s => {
      const container = document.querySelector(`.cards[data-status="${s.id}"]`);
      const countEl = document.querySelector(`[data-count="${s.id}"]`);
      if (!container) return;

      container.innerHTML = '';

      const ids = state.order[s.id] || [];
      ids.forEach((id) => {
        const card = state.cards[id];
        if (!card) return;
        container.appendChild(renderCard(card));
      });

      if (countEl) countEl.textContent = String(ids.length);
    });
  }

  function renderCountsOnly() {
    STATUSES.forEach(({ id }) => {
      const countEl = document.querySelector(`[data-count="${id}"]`);
      if (countEl) countEl.textContent = String((state.order[id] || []).length);
    });
  }

  function renderCard(card) {
    const el = document.createElement('article');
    el.className = 'card';
    el.setAttribute('draggable', 'true');
    el.dataset.id = String(card.id);

    const title = document.createElement('div');
    title.className = 'card__title';
    title.textContent = card.title;
    el.appendChild(title);

    if (card.description) {
      const desc = document.createElement('div');
      desc.className = 'card__desc';
      desc.textContent = card.description;
      el.appendChild(desc);
    }

    if (card.assignee_display && card.assignee_display !== "—") {
      const meta = document.createElement('div');
      meta.className = 'card__meta';
      meta.textContent = `Исполнитель: ${card.assignee_display}`;
      el.appendChild(meta);
    }

    if (card.deadline) {
      const deadlineEl = document.createElement('div');
      deadlineEl.className = 'card__deadline';

      const today = new Date();
      today.setHours(0, 0, 0, 0);

      const deadlineDate = new Date(card.deadline);
      deadlineDate.setHours(0, 0, 0, 0);

          if (deadlineDate < today) {
            deadlineEl.classList.add('overdue');
          }

      deadlineEl.textContent = `Дедлайн: ${deadlineDate.toLocaleDateString()}`;
      el.appendChild(deadlineEl);
    }

    const actions = document.createElement('div');
    actions.className = 'card__actions';

    const editBtn = document.createElement('button');
    editBtn.type = 'button';
    editBtn.className = 'icon-btn';
    editBtn.dataset.action = 'edit';
    editBtn.setAttribute('aria-label', 'Изменить');
    editBtn.title = 'Изменить';
    editBtn.textContent = '✏️';

    const delBtn = document.createElement('button');
    delBtn.type = 'button';
    delBtn.className = 'icon-btn';
    delBtn.dataset.action = 'delete';
    delBtn.setAttribute('aria-label', 'Удалить');
    delBtn.title = 'Удалить';
    delBtn.textContent = '🗑️';

    actions.appendChild(editBtn);
    actions.appendChild(delBtn);
    el.appendChild(actions);

    return el;
  }

  /* -------------------- Drag & Drop -------------------- */

  function onDragStart(e) {
    const cardEl = e.target.closest('.card');
    if (!cardEl) return;

    cardEl.classList.add('dragging');

    if (e.dataTransfer) {
      e.dataTransfer.setData('text/plain', cardEl.dataset.id || '');
      e.dataTransfer.effectAllowed = 'move';
    }
  }

  async function onDragEnd() {
    const dragging = document.querySelector('.card.dragging');
    if (dragging) dragging.classList.remove('dragging');

    document.querySelectorAll('.cards.drag-over').forEach(el => el.classList.remove('drag-over'));

    // Синхронизируем локальный state из DOM (для UI)
    syncStateFromDOM();
    renderCountsOnly();

    // И отправляем на сервер массово порядок
    try {
      await apiReorderFromState();
    } catch (err) {
      console.error(err);
      // если упало — просто перезагрузим состояние с сервера, чтобы не было рассинхрона
      await loadKanbanFromServer();
    }
  }

  function onDragOverCards(e) {
    e.preventDefault();

    const container = e.currentTarget;
    if (!(container instanceof HTMLElement)) return;

    container.classList.add('drag-over');

    const dragging = document.querySelector('.card.dragging');
    if (!dragging) return;

    const afterElement = getDragAfterElement(container, e.clientY);
    if (afterElement == null) {
      container.appendChild(dragging);
    } else {
      container.insertBefore(dragging, afterElement);
    }
  }

  function getDragAfterElement(container, y) {
    const draggableElements = Array.from(container.querySelectorAll('.card:not(.dragging)'));

    let closestOffset = Number.NEGATIVE_INFINITY;
    let closestElement = null;

    draggableElements.forEach((child) => {
      const box = child.getBoundingClientRect();
      const offset = y - (box.top + box.height / 2);
      if (offset < 0 && offset > closestOffset) {
        closestOffset = offset;
        closestElement = child;
      }
    });

    return closestElement;
  }

  function syncStateFromDOM() {
    const newOrder = {};
    const seen = new Set();

    STATUSES.forEach(({ id: statusId }) => {
      const container = document.querySelector(`.cards[data-status="${statusId}"]`);
      if (!container) return;

      const ids = Array.from(container.querySelectorAll('.card'))
        .map(el => el.dataset.id)
        .filter(Boolean);

      const unique = [];
      ids.forEach((cid) => {
        if (seen.has(cid)) return;
        if (!state.cards[cid]) return;
        seen.add(cid);
        unique.push(cid);
      });

      newOrder[statusId] = unique;
      unique.forEach((cid) => { state.cards[cid].status = statusId; });
    });

    const orderedIds = new Set();
    Object.keys(newOrder).forEach((st) => {
      (newOrder[st] || []).forEach((cid) => orderedIds.add(cid));
    });

    Object.keys(state.cards).forEach((cid) => {
      if (orderedIds.has(cid)) return;
      state.cards[cid].status = 'queue';
      if (!newOrder.queue) newOrder.queue = [];
      newOrder.queue.push(cid);
    });

    state.order = Object.assign(defaultState().order, newOrder);
  }

  /* -------------------- Server (API) -------------------- */

  async function loadKanbanFromServer() {
    const resp = await fetch(API_STATE_URL, { credentials: 'same-origin' });
    if (!resp.ok) return;

    const data = await resp.json();

    // Ожидаем:
    // data.columns: [{id, code/status, title, order}, ...] (можно не использовать)
    // data.tasks:   [{id, title, description, status, order}, ...]
    // ВАЖНО: status должен быть одним из STATUSES.id
    const next = defaultState();

    // tasks сортируем по status+order
    const tasks = Array.isArray(data.tasks) ? data.tasks.slice() : [];
    tasks.sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

    for (const t of tasks) {
      const id = String(t.id);
      const status = isValidStatus(t.status) ? t.status : 'queue';

      next.cards[id] = {
          id,
          title: t.title || '',
          description: t.description || '',
          status,
          deadline: t.deadline || null,
          assignee_value: t.assignee_value || "",
          assignee_display: t.assignee_display || "",
          createdAt: Date.now(),
          updatedAt: Date.now(),
      };


      titleCache[id] = next.cards[id].title;
      next.order[status].push(id);
    }

    // если сервер не прислал order для пустых колонок — они уже есть
    state = next;
    renderAllColumns();
  }

  async function apiCreateTask({ title, description, status, assignee, deadline }) {
      return fetchJson(API_TASK_CREATE_URL, {
        method: 'POST',
        body: JSON.stringify({
          project: Number(projectId),
          title,
          description,
          status,
          assignee,
          deadline,
          order: 0,
        }),
      });
    }



  async function apiPatchTask(taskId, payload) {
    return fetchJson(API_TASK_URL(taskId), {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async function apiDeleteTask(taskId) {
  const resp = await fetch(API_TASK_DELETE_URL(taskId), {
    method: 'DELETE',
    headers: {
      'X-CSRFToken': getCookie('csrftoken'),
    },
    credentials: 'same-origin',
  });
  if (!resp.ok) throw new Error('DELETE failed');
}


  async function apiReorderFromState() {
    // Собираем список изменений: [{id, status, order}, ...]
    const updates = [];
    STATUSES.forEach(({ id: st }) => {
      const ids = state.order[st] || [];
      ids.forEach((taskId, idx) => {
        updates.push({ id: Number(taskId), status: st, order: idx });
      });
    });

    return fetchJson(API_REORDER_URL, {
      method: 'POST',
      body: JSON.stringify({ project: Number(projectId), updates }),
    });
  }

  async function fetchJson(url, { method, body }) {
    const resp = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCookie('csrftoken'),
      },
      credentials: 'same-origin',
      body,
    });
    if (!resp.ok) throw new Error(`${method} ${url} failed`);
    return resp.json().catch(() => ({}));
  }

  /* -------------------- Storage-free default state -------------------- */

  function defaultState() {
    const order = {};
    STATUSES.forEach(s => { order[s.id] = []; });
    return { cards: {}, order };
  }

  /* -------------------- Helpers -------------------- */

  function isValidStatus(status) {
    return STATUSES.some(s => s.id === status);
  }

  function escapeHtml(str) {
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return '';
  }
})();
