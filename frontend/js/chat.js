/**
 * Customer Support Chat Widget
 *
 * Habla con el backend FastAPI (/api/v1/*), no directamente con RASA.
 * El nginx.conf proxea /api/ → backend:8000 dentro de Docker Compose,
 * eliminando problemas de CORS en produccion.
 *
 * Para desarrollo sin Docker, cambiar API_BASE a 'http://localhost:8000/api/v1'
 */

(function () {
  'use strict';

  const API_BASE = '/api/v1';

  let sessionId = null;
  let isTyping = false;

  /* ── DOM refs ─────────────────────────────── */
  const toggle    = document.getElementById('chat-toggle');
  const panel     = document.getElementById('chat-panel');
  const messages  = document.getElementById('messages');
  const input     = document.getElementById('msg-input');
  const sendBtn   = document.getElementById('send-btn');
  const toast     = document.getElementById('error-toast');

  /* ── Session ─────────────────────────────── */
  async function initSession() {
    const stored = sessionStorage.getItem('chat_session_id');
    if (stored) { sessionId = stored; return; }

    try {
      const resp = await _apiPost('/sessions', {});
      sessionId = resp.session_id;
      sessionStorage.setItem('chat_session_id', sessionId);
    } catch (_) {
      sessionId = crypto.randomUUID();
      sessionStorage.setItem('chat_session_id', sessionId);
    }
  }

  /* ── Toggle panel ─────────────────────────── */
  toggle.addEventListener('click', async () => {
    const isOpen = panel.classList.toggle('open');
    toggle.classList.toggle('open', isOpen);

    if (isOpen && !sessionId) {
      await initSession();
      renderBotMessage('¡Hola! Soy el asistente virtual del banco. ¿En qué te puedo ayudar hoy?');
    }

    if (isOpen) {
      setTimeout(() => input.focus(), 300);
    }
  });

  /* ── Enviar mensaje ─────────────────────────── */
  async function sendMessage() {
    const text = input.value.trim();
    if (!text || isTyping) return;

    input.value = '';
    hideError();
    renderUserMessage(text);
    showTyping();
    setLoading(true);

    try {
      const data = await _apiPost('/messages', { session_id: sessionId, message: text });
      hideTyping();
      data.messages.forEach(m => renderBotMessage(m.text));
    } catch (err) {
      hideTyping();
      showError('No pude procesar tu mensaje. Intenta de nuevo en un momento.');
    } finally {
      setLoading(false);
    }
  }

  sendBtn.addEventListener('click', sendMessage);

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  /* ── Render ─────────────────────────────── */
  function renderUserMessage(text) {
    const row = _makeRow('user');
    row.innerHTML = `
      <div class="msg-body">
        <div class="bubble">${_escape(text)}</div>
        <span class="msg-time">${_time()}</span>
      </div>`;
    messages.appendChild(row);
    _scroll();
  }

  function renderBotMessage(text) {
    const row = _makeRow('bot');
    row.innerHTML = `
      <div class="msg-avatar">BC</div>
      <div class="msg-body">
        <div class="bubble">${_escape(text)}</div>
        <span class="msg-time">${_time()}</span>
      </div>`;
    messages.appendChild(row);
    _scroll();
  }

  function showTyping() {
    if (isTyping) return;
    isTyping = true;
    const el = document.createElement('div');
    el.id = 'typing';
    el.className = 'typing-indicator';
    el.innerHTML = `
      <div class="msg-avatar">BC</div>
      <div class="typing-dots">
        <span></span><span></span><span></span>
      </div>`;
    messages.appendChild(el);
    _scroll();
  }

  function hideTyping() {
    const el = document.getElementById('typing');
    if (el) el.remove();
    isTyping = false;
  }

  /* ── Helpers ─────────────────────────────── */
  function _makeRow(type) {
    const row = document.createElement('div');
    row.className = `msg-row ${type}`;
    return row;
  }

  function _time() {
    return new Date().toLocaleTimeString('es-CO', { hour: '2-digit', minute: '2-digit' });
  }

  function _escape(text) {
    return text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\n/g, '<br>');
  }

  function _scroll() {
    requestAnimationFrame(() => {
      messages.scrollTop = messages.scrollHeight;
    });
  }

  function setLoading(on) {
    sendBtn.disabled = on;
    input.disabled   = on;
  }

  function showError(msg) {
    toast.textContent = msg;
    toast.classList.add('show');
    setTimeout(() => hideError(), 4000);
  }

  function hideError() {
    toast.classList.remove('show');
  }

  /* ── API ─────────────────────────────── */
  async function _apiPost(path, body) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15_000);
    try {
      const res = await fetch(`${API_BASE}${path}`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    Object.keys(body).length ? JSON.stringify(body) : undefined,
        signal:  controller.signal,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } finally {
      clearTimeout(timeout);
    }
  }

})();
