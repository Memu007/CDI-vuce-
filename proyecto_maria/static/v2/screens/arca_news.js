/* ============================================================
   CDI v2 — Novedades ARCA
   Widget que consume /api/arca/novedades y muestra las últimas
   5 noticias de ARCA/AFIP en el dashboard.
   ============================================================ */
(function () {
    'use strict';
    const CDI = window.CDI = window.CDI || {};

    const WIDGET_ID = 'arcaNewsWidget';
    const LIST_ID = 'arcaNewsList';
    const LOADER_ID = 'arcaNewsLoader';
    const EMPTY_ID = 'arcaNewsEmpty';
    const STORAGE_KEY = 'cdi_arca_news_collapsed';

    function $(id) { return document.getElementById(id); }

    function init() {
        const widget = $(WIDGET_ID);
        const list = $(LIST_ID);
        const loader = $(LOADER_ID);
        const empty = $(EMPTY_ID);
        const titleBtn = widget && widget.querySelector('.arca-news-title');
        if (!widget || !list) return;

        // Estado colapsado persistido por usuario
        try {
            if (localStorage.getItem(STORAGE_KEY) === '1') {
                widget.classList.add('is-collapsed');
            }
        } catch (_) {}

        if (titleBtn) {
            titleBtn.addEventListener('click', () => {
                widget.classList.toggle('is-collapsed');
                try {
                    localStorage.setItem(STORAGE_KEY, widget.classList.contains('is-collapsed') ? '1' : '0');
                } catch (_) {}
            });
        }

        loadNews();
    }

    async function loadNews() {
        const list = $(LIST_ID);
        const loader = $(LOADER_ID);
        const empty = $(EMPTY_ID);
        if (!list) return;

        try {
            const res = await CDI.api('/api/arca/novedades');
            if (!res.ok) throw new Error('HTTP ' + res.status);
            const data = await res.json();
            if (data.ok && Array.isArray(data.items) && data.items.length > 0) {
                render(list, data.items);
                if (loader) loader.hidden = true;
                if (empty) empty.hidden = true;
                CDI.track('arca_news_loaded', { count: data.items.length });
            } else {
                showEmpty();
            }
        } catch (e) {
            console.warn('[CDI] ARCA news unavailable:', e);
            showEmpty();
        }
    }

    function render(list, items) {
        const html = items.map(item => {
            const title = CDI.escapeHtml(item.titulo || 'Novedad ARCA');
            const link = CDI.escapeHtml(item.link || '#');
            const img = item.imagen ? CDI.escapeHtml(item.imagen) : '';
            const imgTag = img
                ? `<img class="arca-news-thumb" src="${img}" alt="" loading="lazy" onerror="this.style.display='none'">`
                : '';
            return `
                <a class="arca-news-item" href="${link}" target="_blank" rel="noopener noreferrer" title="${title}">
                    ${imgTag}
                    <span class="arca-news-item-title">${title}</span>
                </a>
            `;
        }).join('');
        list.innerHTML = html;
    }

    function showEmpty() {
        const list = $(LIST_ID);
        const loader = $(LOADER_ID);
        const empty = $(EMPTY_ID);
        if (list) list.innerHTML = '';
        if (loader) loader.hidden = true;
        if (empty) empty.hidden = false;
    }

    document.addEventListener('DOMContentLoaded', init);
})();
