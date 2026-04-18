(function () {
  const PAGE_CONFIG = {
    'workspace-home': {
      title: 'KIS Workspace Chat',
      placeholder: '이 페이지에서 다음에 뭘 보면 좋을지 물어보세요.',
      suggestions: ['이 화면에서 어디부터 보면 돼?', 'ETF랑 해외주식 중 뭐부터 붙어 있어?', 'SEPA 화면은 어디에 쓰면 돼?'],
    },
    'kis-catalog': {
      title: 'KIS Catalog Chat',
      placeholder: '어떤 상품군이 되는지 물어보세요.',
      suggestions: ['지금 프로젝트에서 바로 쓸 수 있는 상품군은?', 'ETF/해외주식/채권 차이를 요약해줘', '왜 ELW는 뒤로 미뤘어?'],
    },
    'domestic-etf': {
      title: 'ETF Chat',
      placeholder: 'ETF 분석이나 백테스트 흐름을 물어보세요.',
      suggestions: ['이 ETF가 왜 점수가 높아?', '다음으로 백테스트는 어떻게 해?', '지지선/저항선 해석해줘'],
    },
    'overseas-stocks': {
      title: 'Overseas Chat',
      placeholder: '해외주식 조회 결과를 물어보세요.',
      suggestions: ['이 종목 추세를 한 줄로 요약해줘', 'exchange 코드가 뭐야?', '차트 100일 기준으로 해석해줘'],
    },
    'legacy-sepa': {
      title: 'SEPA Chat',
      placeholder: '리더 스캔, 차트 데스크, 백테스트를 물어보세요.',
      suggestions: ['이 SEPA 화면은 뭘 보는 거야?', '리더 스캔이랑 ETF는 어떻게 같이 써?', '이 결과를 어떻게 해석해?'],
    },
  };

  const PATH_TO_PAGE = {
    '/': 'workspace-home',
    '/index.html': 'workspace-home',
    '/kis-mobile.html': 'kis-catalog',
    '/etf-mobile.html': 'domestic-etf',
    '/overseas-mobile.html': 'overseas-stocks',
  };

  const byId = (id) => document.getElementById(id);

  function resolvePageId() {
    const fromDataset = document.body && document.body.dataset ? document.body.dataset.chatPage : '';
    if (fromDataset && PAGE_CONFIG[fromDataset]) return fromDataset;
    return PATH_TO_PAGE[window.location.pathname] || 'workspace-home';
  }

  function resolveApiBase() {
    const candidates = ['workspaceApiBase', 'apiBase'];
    for (const id of candidates) {
      const input = byId(id);
      if (input && input.value && input.value.trim()) {
        return input.value.trim();
      }
    }
    return window.location.origin;
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;');
  }

  const state = {
    pageId: resolvePageId(),
    context: {
      page_title: document.title,
      page_path: window.location.pathname,
    },
    messages: [],
    open: false,
    sending: false,
    health: null,
  };

  function config() {
    return PAGE_CONFIG[state.pageId] || PAGE_CONFIG['workspace-home'];
  }

  function ensureMount() {
    if (byId('chatAssistantRoot')) return;
    const root = document.createElement('section');
    root.id = 'chatAssistantRoot';
    root.className = 'chat-assistant';
    root.innerHTML = `
      <div class="chat-assistant__panel" aria-live="polite">
        <div class="chat-assistant__header">
          <strong id="chatAssistantTitle"></strong>
          <span id="chatAssistantSubtitle"></span>
        </div>
        <div id="chatAssistantStatus" class="chat-assistant__status">로딩 중...</div>
        <div id="chatAssistantMessages" class="chat-assistant__messages"></div>
        <div class="chat-assistant__suggestions" id="chatAssistantSuggestions"></div>
        <div class="chat-assistant__composer">
          <textarea id="chatAssistantInput"></textarea>
          <div class="chat-assistant__composer-actions">
            <span class="chat-assistant__hint">로컬 Ollama 기본 / 필요시 Gemini</span>
            <button id="chatAssistantSend" class="chat-assistant__send" type="button">보내기</button>
          </div>
        </div>
      </div>
      <button id="chatAssistantLauncher" class="chat-assistant__launcher" type="button" aria-label="Open chat">AI</button>
    `;
    document.body.appendChild(root);

    byId('chatAssistantLauncher').addEventListener('click', toggleOpen);
    byId('chatAssistantSend').addEventListener('click', sendCurrentMessage);
    byId('chatAssistantInput').addEventListener('keydown', (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        sendCurrentMessage();
      }
    });
  }

  function renderShell() {
    const root = byId('chatAssistantRoot');
    if (!root) return;
    root.classList.toggle('is-open', state.open);
    byId('chatAssistantTitle').textContent = config().title;
    byId('chatAssistantSubtitle').textContent = state.pageId;
    byId('chatAssistantInput').placeholder = config().placeholder;
    byId('chatAssistantSend').disabled = state.sending;
    renderStatus();
    renderMessages();
    renderSuggestions();
  }

  function renderStatus() {
    const el = byId('chatAssistantStatus');
    if (!el) return;
    if (!state.health) {
      el.textContent = 'LLM 상태 확인 중...';
      return;
    }
    const provider = state.health.provider || 'unknown';
    const model = (((state.health.provider_health || {}).model) || '').trim();
    const ready = state.health.ready;
    el.textContent = ready
      ? `LLM ready: ${provider}${model ? ` / ${model}` : ''}`
      : `LLM check: ${provider}${model ? ` / ${model}` : ''}`;
  }

  function renderMessages() {
    const root = byId('chatAssistantMessages');
    if (!root) return;
    if (!state.messages.length) {
      root.innerHTML = `<div class="chat-assistant__bubble">안녕하세요. ${config().title}입니다. 이 페이지 데이터 기준으로 설명해드릴게요.</div>`;
      return;
    }
    root.innerHTML = state.messages.map((message) => `
      <div class="chat-assistant__bubble ${message.role === 'user' ? 'is-user' : ''} ${message.role === 'error' ? 'is-error' : ''}">
        ${escapeHtml(message.content)}
      </div>
    `).join('');
    root.scrollTop = root.scrollHeight;
  }

  function renderSuggestions() {
    const root = byId('chatAssistantSuggestions');
    if (!root) return;
    root.innerHTML = config().suggestions.map((text) => `
      <button class="chat-assistant__suggestion" type="button">${escapeHtml(text)}</button>
    `).join('');
    Array.from(root.querySelectorAll('button')).forEach((button) => {
      button.addEventListener('click', () => {
        byId('chatAssistantInput').value = button.textContent || '';
        sendCurrentMessage();
      });
    });
  }

  function toggleOpen() {
    state.open = !state.open;
    renderShell();
  }

  async function loadHealth() {
    try {
      const response = await fetch(`${resolveApiBase()}/api/assistant/health`);
      const payload = await response.json().catch(() => ({}));
      state.health = response.ok ? payload : {provider: 'unknown', ready: false, provider_health: payload};
    } catch (error) {
      state.health = {provider: 'unknown', ready: false, provider_health: {error: String(error)}};
    }
    renderShell();
  }

  async function sendCurrentMessage() {
    const input = byId('chatAssistantInput');
    if (!input || state.sending) return;
    const text = input.value.trim();
    if (!text) return;
    input.value = '';
    state.messages.push({role: 'user', content: text});
    state.sending = true;
    renderShell();
    try {
      const response = await fetch(`${resolveApiBase()}/api/assistant/chat`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          page_id: state.pageId,
          messages: state.messages.filter((item) => item.role === 'user' || item.role === 'assistant'),
          context: state.context,
        }),
      });
      const payload = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(payload.detail || payload.message || `HTTP ${response.status}`);
      }
      state.messages.push({role: 'assistant', content: payload.content || ''});
    } catch (error) {
      state.messages.push({role: 'error', content: String(error.message || error)});
    } finally {
      state.sending = false;
      renderShell();
    }
  }

  window.SEPAChatAssistant = {
    setContext(partial) {
      if (!partial || typeof partial !== 'object') return;
      state.context = {...state.context, ...partial};
    },
    replaceContext(nextContext) {
      state.context = nextContext && typeof nextContext === 'object' ? nextContext : {};
    },
    setPageId(pageId) {
      if (pageId && PAGE_CONFIG[pageId]) {
        state.pageId = pageId;
        renderShell();
      }
    },
    open() {
      state.open = true;
      renderShell();
    },
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      ensureMount();
      renderShell();
      loadHealth();
    });
  } else {
    ensureMount();
    renderShell();
    loadHealth();
  }
})();
