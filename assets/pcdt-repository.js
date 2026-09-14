(() => {
  'use strict';

  const STORAGE_KEY =
    'clinical-reference-v2-pcdt-repository-v1';

  const RECENT_STORAGE_KEY =
    'clinical-reference-v2-pcdt-recent-v1';

  const PAGE_SIZE = 50;

  const state = {
    query: '',
    page: 1,
    selectedPcdtId: null,
    indexPayload: null,
    detailPayload: null,
    documentsPayload: null,

    recentPcdts: [],
    searchEpoch: 0,
  };


  function language() {
    return (
      globalThis.ClinicalI18n
        ?.getLanguage?.()
      || 'pt-BR'
    );
  }


  function t(
    key,
    pt,
    en
  ) {
    const translated =
      globalThis.ClinicalI18n
        ?.t?.(
          key
        );

    if (
      translated
      && translated !== key
    ) {
      return translated;
    }

    return (
      language() === 'en-GB'
      ? en
      : pt
    );
  }


  function escapeHtml(
    value
  ) {
    return String(
      value ?? ''
    )
      .replaceAll(
        '&',
        '&amp;'
      )
      .replaceAll(
        '<',
        '&lt;'
      )
      .replaceAll(
        '>',
        '&gt;'
      )
      .replaceAll(
        '"',
        '&quot;'
      )
      .replaceAll(
        "'",
        '&#039;'
      );
  }


  function safeExternalUrl(
    value
  ) {
    try {
      const url = new URL(
        String(
          value
          || ''
        )
      );

      return (
        url.protocol === 'https:'
        ? url.href
        : null
      );

    } catch (_) {
      return null;
    }
  }


  function safePcdtDocumentUrl(
    value
  ) {
    const text = String(
      value
      || ''
    );

    return (
      /^\/documents\/pcdt\/[0-9a-f]{64}\.pdf$/
        .test(
          text
        )
      ? text
      : null
    );
  }


  function loadSession() {
    try {
      const payload = JSON.parse(
        sessionStorage.getItem(
          STORAGE_KEY
        )
        || '{}'
      );

      if (
        typeof payload.query
        === 'string'
        && payload.query.length
          <= 120
      ) {
        state.query =
          payload.query;
      }

      if (
        Number.isInteger(
          payload.page
        )
        && payload.page >= 1
      ) {
        state.page =
          payload.page;
      }


      if (
        typeof payload.selectedPcdtId
          === 'string'
        && /^[a-z0-9][a-z0-9-]{0,199}$/
          .test(
            payload.selectedPcdtId
          )
      ) {
        state.selectedPcdtId =
          payload.selectedPcdtId;
      }

    } catch (_) {}
  }


  function saveSession() {
    try {
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          query:
            state.query,

          page:
            state.page,

          selectedPcdtId:
            state.selectedPcdtId,
        })
      );

    } catch (_) {}
  }


  function validPcdtId(
    value
  ) {
    return (
      typeof value === 'string'
      && /^[a-z0-9][a-z0-9-]{0,199}$/
        .test(
          value
        )
    );
  }


  function displayTitle(
    item
  ) {
    if (!item) {
      return '';
    }

    if (
      language() === 'en-GB'
      && typeof item.title_en
        === 'string'
      && item.title_en.trim()
    ) {
      return item.title_en;
    }

    return (
      item.canonical_title_pt
      || item.pcdt_id
      || ''
    );
  }


  function loadRecentSession() {
    try {
      const payload =
        JSON.parse(
          sessionStorage.getItem(
            RECENT_STORAGE_KEY
          )
          || '[]'
        );

      if (!Array.isArray(payload)) {
        return;
      }

      state.recentPcdts =
        payload
          .filter(
            item =>
              item
              && validPcdtId(
                item.pcdtId
              )
              && typeof item.canonical_title_pt
                === 'string'
              && item.canonical_title_pt
                .trim()
              && (
                item.title_en === null
                || typeof item.title_en
                  === 'string'
              )
          )
          .slice(
            0,
            3
          );

    } catch (_) {
      state.recentPcdts = [];
    }
  }


  function saveRecentSession() {
    try {
      sessionStorage.setItem(
        RECENT_STORAGE_KEY,
        JSON.stringify(
          state.recentPcdts
            .slice(
              0,
              3
            )
        )
      );

    } catch (_) {}
  }


  function rememberRecent(
    pcdt
  ) {
    if (
      !pcdt
      || !validPcdtId(
        pcdt.pcdt_id
      )
    ) {
      return;
    }

    const entry = {
      pcdtId:
        pcdt.pcdt_id,

      canonical_title_pt:
        String(
          pcdt.canonical_title_pt
          || pcdt.pcdt_id
        )
          .trim()
          .slice(
            0,
            500
          ),

      title_en:
        (
          typeof pcdt.title_en
            === 'string'
          && pcdt.title_en.trim()
        )
          ? pcdt.title_en
              .trim()
              .slice(
                0,
                500
              )
          : null,
    };

    state.recentPcdts = [
      entry,

      ...state.recentPcdts
        .filter(
          item =>
            item.pcdtId
            !== entry.pcdtId
        ),
    ]
      .slice(
        0,
        3
      );

    saveRecentSession();
  }


  function renderRecent() {
    const target =
      document.getElementById(
        'pcdt-recent'
      );

    if (!target) {
      return;
    }

    if (
      state.recentPcdts.length
      === 0
    ) {
      target.innerHTML = '';
      return;
    }

    target.innerHTML = `
      <div class="flex flex-wrap items-center gap-2">
        <span class="text-[10px] uppercase font-semibold text-slate-500">
          ${escapeHtml(
            t(
              'pcdt.recent',
              'PCDTs recentes',
              'Recent PCDTs'
            )
          )}
        </span>

        ${
          state.recentPcdts
            .map(
              item => `
                <button
                  type="button"
                  data-pcdt-recent="${escapeHtml(item.pcdtId)}"
                  class="text-xs px-3 py-1.5 rounded-lg border border-slate-700 bg-slate-900 text-teal-300 hover:border-teal-600 hover:text-teal-200 transition"
                  title="${escapeHtml(displayTitle(item))}"
                >
                  ${escapeHtml(displayTitle(item))}
                </button>
              `
            )
            .join('')
        }
      </div>
    `;
  }


  function clearExpandedState({
    persist = true,
  } = {}) {
    state.selectedPcdtId =
      null;

    state.detailPayload =
      null;

    state.documentsPayload =
      null;

    if (persist) {
      saveSession();
    }
  }


  function detailContainerFor(
    pcdtId
  ) {
    if (!validPcdtId(
      pcdtId
    )) {
      return null;
    }

    return document.querySelector(
      `[data-pcdt-inline-detail="${pcdtId}"]`
    );
  }

  function localiseChrome() {
    const input =
      document.getElementById(
        'pcdt-search-input'
      );

    if (!input) {
      return;
    }

    input.placeholder =
      t(
        'pcdt.placeholder',
        'Ex: asma, osteoporose, AVC...',
        'e.g. asma, osteoporose, AVC...'
      );

    input.setAttribute(
      'aria-label',
      t(
        'pcdt.searchLabel',
        'Buscar PCDT',
        'Search PCDT'
      )
    );
  }


  async function fetchJson(
    url
  ) {
    const response =
      await fetch(
        url,
        {
          headers: {
            Accept:
              'application/json',
          },

          cache:
            'no-store',
        }
      );

    if (!response.ok) {
      let detail = '';

      try {
        detail =
          (
            await response.json()
          ).detail
          || '';

      } catch (_) {}

      throw new Error(
        detail
        || t(
          'pcdt.error',
          'Não foi possível carregar o repositório PCDT.',
          'Unable to load the PCDT repository.'
        )
      );
    }

    return response.json();
  }


  function renderMeta() {
    const target =
      document.getElementById(
        'pcdt-meta'
      );

    if (
      !target
      || !state.indexPayload
    ) {
      return;
    }

    const total =
      Number(
        state.indexPayload.total
        || 0
      );

    const first =
      total > 0
      ? (
        (
          state.page - 1
        )
        * PAGE_SIZE
      ) + 1
      : 0;

    const last =
      total > 0
      ? Math.min(
        first
        + Number(
          state.indexPayload.returned
          || 0
        )
        - 1,
        total
      )
      : 0;

    target.textContent =
      `${t(
        'pcdt.showing',
        'Exibindo',
        'Showing'
      )} ${first}–${last} ${t(
        'pcdt.of',
        'de',
        'of'
      )} ${total}`;
  }


  function renderPagination(
    position
  ) {
    const data =
      state.indexPayload;

    if (!data) {
      return '';
    }

    const total =
      Number(
        data.total
        || 0
      );

    if (total <= 0) {
      return '';
    }

    const totalPages =
      Math.max(
        1,
        Math.ceil(
          total
          / PAGE_SIZE
        )
      );

    const currentPage =
      Math.min(
        Math.max(
          Number(
            state.page
            || 1
          ),
          1
        ),
        totalPages
      );

    const first =
      (
        (
          currentPage - 1
        )
        * PAGE_SIZE
      ) + 1;

    const last =
      Math.min(
        first
        + Number(
          data.returned
          || 0
        )
        - 1,
        total
      );

    const pageButtons =
      Array.from(
        {
          length:
            totalPages,
        },
        (_, index) =>
          index + 1
      )
      .map(
        page => {
          const current =
            page
            === currentPage;

          return `
            <button
              type="button"
              data-pcdt-page="${page}"
              aria-label="${escapeHtml(
                t(
                  'pcdt.page',
                  'Página',
                  'Page'
                )
              )} ${page}"
              ${current ? 'aria-current="page"' : ''}
              class="min-w-9 h-9 px-3 rounded-lg border ${
                current
                ? 'border-teal-500 bg-teal-950/50 text-teal-200'
                : 'border-slate-700 bg-slate-900 text-slate-300 hover:border-teal-700 hover:text-white'
              } text-xs font-semibold transition"
            >
              ${page}
            </button>
          `;
        }
      )
      .join('');

    const previousDisabled =
      currentPage <= 1;

    const nextDisabled =
      currentPage >= totalPages;

    return `
      <nav
        data-pcdt-pagination="${escapeHtml(position)}"
        aria-label="${escapeHtml(
          t(
            'pcdt.pagination',
            'Paginação dos PCDTs',
            'PCDT pagination'
          )
        )}"
        class="bg-slate-950/60 border border-slate-800 rounded-xl p-3"
      >
        <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <p class="text-xs text-slate-400">
            ${escapeHtml(
              t(
                'pcdt.showing',
                'Exibindo',
                'Showing'
              )
            )}
            ${first}–${last}
            ${escapeHtml(
              t(
                'pcdt.of',
                'de',
                'of'
              )
            )}
            ${total}
            ·
            ${escapeHtml(
              t(
                'pcdt.page',
                'Página',
                'Page'
              )
            )}
            ${currentPage}
            ${escapeHtml(
              t(
                'pcdt.of',
                'de',
                'of'
              )
            )}
            ${totalPages}
          </p>

          <div class="flex flex-wrap items-center gap-2">
            <button
              type="button"
              data-pcdt-page="${currentPage - 1}"
              aria-label="${escapeHtml(
                t(
                  'pcdt.previous',
                  'Página anterior',
                  'Previous page'
                )
              )}"
              ${previousDisabled ? 'disabled' : ''}
              class="h-9 px-3 rounded-lg border border-slate-700 bg-slate-900 text-xs font-semibold text-slate-300 transition disabled:opacity-40 disabled:cursor-not-allowed enabled:hover:border-teal-700 enabled:hover:text-white"
            >
              &lsaquo;
              ${escapeHtml(
                t(
                  'pcdt.previousShort',
                  'Anterior',
                  'Previous'
                )
              )}
            </button>

            ${pageButtons}

            <button
              type="button"
              data-pcdt-page="${currentPage + 1}"
              aria-label="${escapeHtml(
                t(
                  'pcdt.next',
                  'Próxima página',
                  'Next page'
                )
              )}"
              ${nextDisabled ? 'disabled' : ''}
              class="h-9 px-3 rounded-lg border border-slate-700 bg-slate-900 text-xs font-semibold text-slate-300 transition disabled:opacity-40 disabled:cursor-not-allowed enabled:hover:border-teal-700 enabled:hover:text-white"
            >
              ${escapeHtml(
                t(
                  'pcdt.nextShort',
                  'Próxima',
                  'Next'
                )
              )}
              &rsaquo;
            </button>
          </div>
        </div>
      </nav>
    `;
  }


  function renderIndex() {
    const target =
      document.getElementById(
        'pcdt-results'
      );

    if (!target) {
      return;
    }

    const data =
      state.indexPayload;

    if (
      !data
      || !Array.isArray(
        data.items
      )
    ) {
      return;
    }

    renderMeta();

    if (
      data.items.length
      === 0
    ) {
      target.innerHTML = `
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 text-sm text-slate-400">
          ${escapeHtml(
            t(
              'pcdt.noResults',
              'Nenhum PCDT encontrado.',
              'No PCDT found.'
            )
          )}
        </div>
      `;

      return;
    }

    const cards =
      data.items.map(
        item => {
          const selected =
            item.pcdt_id
            === state.selectedPcdtId;

          const title =
            displayTitle(
              item
            );

          return `
            <article
              class="bg-slate-900 border ${
                selected
                ? 'border-teal-500'
                : 'border-slate-800'
              } rounded-xl shadow-lg overflow-hidden"
            >
              <button
                type="button"
                data-pcdt-toggle="${escapeHtml(item.pcdt_id)}"
                aria-expanded="${selected ? 'true' : 'false'}"
                aria-controls="pcdt-panel-${escapeHtml(item.pcdt_id)}"
                class="w-full text-left p-4 hover:bg-slate-800/40 transition"
              >
                <div class="flex items-start justify-between gap-3">
                  <div class="flex items-start gap-3 min-w-0">
                    <span
                      aria-hidden="true"
                      class="text-teal-300 text-lg leading-5 shrink-0 transition-transform"
                      style="${
                        selected
                        ? 'transform: rotate(90deg);'
                        : ''
                      } transform-origin: center;"
                    >&gt;</span>

                    <div class="min-w-0">
                      <p class="text-sm font-semibold text-white">
                        ${escapeHtml(title)}
                      </p>

                      ${
                        language() === 'en-GB'
                        && item.title_en
                        && item.canonical_title_pt
                        ? `
                          <p class="text-[10px] text-slate-500 mt-1">
                            ${escapeHtml(
                              t(
                                'pcdt.officialPtShort',
                                'Título oficial PT-BR',
                                'Official PT-BR title'
                              )
                            )}:
                            ${escapeHtml(item.canonical_title_pt)}
                          </p>
                        `
                        : ''
                      }

                      <p class="text-[10px] text-slate-500 mt-1 font-mono break-all">
                        ${escapeHtml(item.pcdt_id)}
                      </p>
                    </div>
                  </div>

                  <span class="text-[10px] px-2 py-1 rounded border border-slate-700 text-slate-300 shrink-0">
                    ${escapeHtml(item.document_count)} docs
                  </span>
                </div>

                <div class="mt-3 pl-7 text-[11px] text-slate-400 flex flex-wrap gap-x-4 gap-y-1">
                  <span>
                    ${escapeHtml(
                      t(
                        'pcdt.versions',
                        'Versões / atos de aprovação',
                        'Versions / approval instruments'
                      )
                    )}:
                    ${escapeHtml(item.approval_version_count)}
                  </span>

                  <span>
                    ${escapeHtml(
                      t(
                        'pcdt.approvalState',
                        'Situação de aprovação',
                        'Approval status'
                      )
                    )}:
                    ${escapeHtml(item.approval_state)}
                  </span>
                </div>
              </button>

              ${
                selected
                ? `
                  <div
                    id="pcdt-panel-${escapeHtml(item.pcdt_id)}"
                    data-pcdt-inline-detail="${escapeHtml(item.pcdt_id)}"
                    class="border-t border-slate-800 p-5"
                  >
                    <p class="text-sm text-slate-400">
                      ${escapeHtml(
                        t(
                          'pcdt.loading',
                          'Carregando repositório PCDT...',
                          'Loading PCDT repository...'
                        )
                      )}
                    </p>
                  </div>
                `
                : ''
              }
            </article>
          `;
        }
      ).join('');

    target.innerHTML =
      '<div class="mb-3">'
      + renderPagination(
        'top'
      )
      + '</div>'
      + cards
      + '<div class="mt-3">'
      + renderPagination(
        'bottom'
      )
      + '</div>';
  }


  function revisionText(
    event
  ) {
    if (
      !event
      || typeof event
        !== 'object'
    ) {
      return String(
        event
        || ''
      );
    }

    return (
      event.raw_annotation
      || event.annotation
      || event.description
      || event.event_type
      || event.type
      || JSON.stringify(
        event
      )
    );
  }


  function renderVersions(
    versions
  ) {
    const rows =
      Array.isArray(
        versions
      )
      ? versions
      : [];

    return rows.map(
      version => {
        const current =
          Boolean(
            version.current_version
          );

        const events =
          Array.isArray(
            version.revision_events
          )
          ? version.revision_events
          : [];

        const eventHtml =
          events.length
          ? `
            <ul class="mt-2 space-y-1">
              ${
                events.map(
                  event => `
                    <li class="text-[11px] text-slate-400">
                      • ${escapeHtml(
                        revisionText(
                          event
                        )
                      )}
                    </li>
                  `
                ).join('')
              }
            </ul>
          `
          : `
            <p class="text-[11px] text-slate-500 mt-2">
              ${escapeHtml(
                t(
                  'pcdt.noRevisionEvents',
                  'Nenhum evento de revisão estruturado nesta versão.',
                  'No structured revision event is recorded for this version.'
                )
              )}
            </p>
          `;

        return `
          <div class="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <span class="text-xs font-bold text-teal-300 font-mono break-all">
                ${escapeHtml(
                  version.approval_version_id
                )}
              </span>

              <span class="${
                current
                ? 'text-emerald-300 border-emerald-800'
                : 'text-slate-400 border-slate-700'
              } border rounded px-2 py-0.5 text-[10px] uppercase">
                ${escapeHtml(
                  current
                  ? t(
                      'pcdt.current',
                      'Atual',
                      'Current'
                    )
                  : t(
                      'pcdt.historical',
                      'Histórico',
                      'Historical'
                    )
                )}
              </span>
            </div>

            <p class="text-xs text-slate-200 mt-2">
              <span class="font-semibold text-slate-400">
                ${escapeHtml(
                  t(
                    'pcdt.approvalAct',
                    'Ato de aprovação',
                    'Approval instrument'
                  )
                )}:
              </span>

              ${escapeHtml(
                version.raw_approval_citation
                || [
                  version.act_type,
                  version.act_number,
                  version.act_year
                ]
                  .filter(Boolean)
                  .join(' ')
                || '—'
              )}
            </p>

            ${
              version.dou_publication_date
              ? `
                <p class="text-[11px] text-slate-400 mt-1">
                  ${escapeHtml(
                    t(
                      'pcdt.published',
                      'Publicação',
                      'Publication'
                    )
                  )}:
                  ${escapeHtml(
                    version.dou_publication_date
                  )}
                </p>
              `
              : ''
            }

            <div class="mt-3 pt-2 border-t border-slate-800">
              <p class="text-[10px] font-semibold uppercase text-slate-500">
                ${escapeHtml(
                  t(
                    'pcdt.revisionEvents',
                    'Eventos de revisão',
                    'Revision events'
                  )
                )}
              </p>

              ${eventHtml}
            </div>
          </div>
        `;
      }
    ).join('');
  }


  function roleLabel(
    value
  ) {
    const roles = {
      protocol_text: [
        'pcdt.role.protocol_text',
        'Texto do protocolo',
        'Protocol text'
      ],

      approval_act: [
        'pcdt.role.approval_act',
        'Ato de aprovação',
        'Approval instrument'
      ],

      protocol_summary: [
        'pcdt.role.protocol_summary',
        'PCDT resumido',
        'PCDT summary'
      ],

      ministry_publication: [
        'pcdt.role.ministry_publication',
        'Publicação do Ministério',
        'Ministry publication'
      ],
    };

    const role =
      roles[
        value
      ];

    return (
      role
      ? t(
          ...role
        )
      : (
          value
          || '—'
        )
    );
  }


  function renderDocuments(
    documents
  ) {
    const rows =
      Array.isArray(
        documents
      )
      ? documents
      : [];

    return rows.map(
      item => {
        const localUrl =
          safePcdtDocumentUrl(
            item.self_hosted_url
          );

        const sourceUrl =
          safeExternalUrl(
            item.canonical_source_url
          );

        const status =
          item.current_version
          ? t(
              'pcdt.current',
              'Atual',
              'Current'
            )
          : t(
              'pcdt.historical',
              'Histórico',
              'Historical'
            );

        return `
          <div class="rounded-xl border border-slate-800 bg-slate-950/50 p-4">
            <div class="flex flex-wrap items-center justify-between gap-2">
              <span class="text-[10px] uppercase font-bold text-cyan-300">
                ${escapeHtml(
                  roleLabel(
                    item.document_role
                  )
                )}
              </span>

              <span class="text-[10px] text-slate-500">
                ${escapeHtml(
                  status
                )}
              </span>
            </div>

            <p class="text-sm text-white mt-2">
              ${escapeHtml(
                item.source_link_text
                || item.document_id
              )}
            </p>

            <p class="text-[10px] text-slate-500 mt-1 font-mono break-all">
              ${escapeHtml(
                item.archive_sha256
                || '—'
              )}
            </p>

            ${
              item.archive_last_verified_at
              ? `
                <p class="text-[10px] text-slate-500 mt-1">
                  ${escapeHtml(
                    t(
                      'pcdt.provenance',
                      'Proveniência',
                      'Provenance'
                    )
                  )}:
                  SHA-256 ·
                  ${escapeHtml(
                    item.archive_last_verified_at
                  )}
                </p>
              `
              : ''
            }

            <div class="flex flex-wrap gap-3 mt-3">
              ${
                localUrl
                ? `
                  <a
                    href="${escapeHtml(localUrl)}"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-xs font-semibold text-teal-300 hover:text-teal-200 underline underline-offset-2"
                  >
                    ${escapeHtml(
                      t(
                        'pcdt.officialPdf',
                        'Abrir PDF arquivado',
                        'Open archived PDF'
                      )
                    )} ↗
                  </a>
                `
                : `
                  <span class="text-xs text-slate-500">
                    ${escapeHtml(
                      t(
                        'pcdt.unavailable',
                        'Documento não disponível para abertura local.',
                        'Document is not available for local opening.'
                      )
                    )}
                  </span>
                `
              }

              ${
                sourceUrl
                ? `
                  <a
                    href="${escapeHtml(sourceUrl)}"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-xs text-cyan-300 hover:text-cyan-200 underline underline-offset-2"
                  >
                    ${escapeHtml(
                      t(
                        'pcdt.officialSource',
                        'Abrir fonte oficial',
                        'Open official source'
                      )
                    )} ↗
                  </a>
                `
                : ''
              }
            </div>
          </div>
        `;
      }
    ).join('');
  }


  function renderDetail() {
    const target =
      detailContainerFor(
        state.selectedPcdtId
      );

    if (!target) {
      return;
    }

    const detail =
      state.detailPayload;

    if (
      !detail
      || !detail.pcdt
    ) {
      return;
    }

    const pcdt =
      detail.pcdt;

    const documents =
      state.documentsPayload;

    const english =
      language() === 'en-GB';

    const primaryTitle =
      displayTitle(
        pcdt
      );

    const aliases =
      english
      ? [
          ...(pcdt.aliases_en || []),
        ]
      : [
          ...(pcdt.aliases_pt || []),
          ...(pcdt.historical_titles_pt || []),
        ];

    const catalogUrl =
      safeExternalUrl(
        pcdt.source_observation
          ?.official_catalog_url
      );

    target.innerHTML = `
      <div class="space-y-5">
        <div>
          <p class="text-[10px] uppercase tracking-wider text-teal-300 font-semibold">
            ${escapeHtml(
              english
              ? t(
                  'pcdt.productLocalisation',
                  'Localização do produto',
                  'Product localisation'
                )
              : t(
                  'pcdt.officialTitle',
                  'Título oficial',
                  'Official title'
                )
            )} · ${english ? 'EN-GB' : 'PT-BR'}
          </p>

          <h2 class="text-xl font-bold text-white mt-1">
            ${escapeHtml(
              primaryTitle
            )}
          </h2>

          ${
            english
            ? `
              <div class="mt-3 rounded-lg border border-slate-800 bg-slate-950/50 p-3">
                <p class="text-[10px] uppercase tracking-wider text-slate-500 font-semibold">
                  ${escapeHtml(
                    t(
                      'pcdt.officialPortugueseSourceTitle',
                      'Título oficial da fonte · PT-BR',
                      'Official source title · PT-BR'
                    )
                  )}
                </p>

                <p class="text-sm text-slate-200 mt-1">
                  ${escapeHtml(
                    pcdt.canonical_title_pt
                  )}
                </p>
              </div>
            `
            : ''
          }

          <p class="text-[10px] text-slate-500 font-mono mt-2 break-all">
            ${escapeHtml(
              pcdt.pcdt_id
            )}
          </p>
        </div>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
          <div class="rounded-lg border border-slate-800 bg-slate-950/50 p-3">
            <span class="text-slate-500">
              ${escapeHtml(
                t(
                  'pcdt.approvalState',
                  'Situação de aprovação',
                  'Approval status'
                )
              )}
            </span>

            <p class="text-white mt-1">
              ${escapeHtml(
                pcdt.approval_state
                || '—'
              )}
            </p>
          </div>

          <div class="rounded-lg border border-slate-800 bg-slate-950/50 p-3">
            <span class="text-slate-500">
              ${escapeHtml(
                t(
                  'pcdt.developmentState',
                  'Situação de desenvolvimento',
                  'Development status'
                )
              )}
            </span>

            <p class="text-white mt-1">
              ${escapeHtml(
                pcdt.development_state
                || '—'
              )}
            </p>
          </div>
        </div>

        ${
          aliases.length
          ? `
            <div>
              <p class="text-[10px] uppercase font-semibold text-slate-500">
                ${escapeHtml(
                  t(
                    'pcdt.aliases',
                    'Sinônimos / títulos relacionados',
                    'Aliases / related titles'
                  )
                )}
              </p>

              <p class="text-xs text-slate-300 mt-1">
                ${escapeHtml(
                  aliases.join(
                    ' · '
                  )
                )}
              </p>
            </div>
          `
          : ''
        }

        <div>
          <h3 class="text-sm font-semibold text-white mb-3">
            ${escapeHtml(
              t(
                'pcdt.versions',
                'Versões / atos de aprovação',
                'Versions / approval instruments'
              )
            )}
          </h3>

          <div class="space-y-3">
            ${renderVersions(
              detail.approval_versions
            )}
          </div>
        </div>

        <div>
          <h3 class="text-sm font-semibold text-white mb-3">
            ${escapeHtml(
              t(
                'pcdt.documents',
                'Documentos relacionados',
                'Related documents'
              )
            )}
          </h3>

          <div class="space-y-3">
            ${renderDocuments(
              documents?.items
            )}
          </div>
        </div>

        ${
          catalogUrl
          ? `
            <div class="pt-3 border-t border-slate-800">
              <a
                href="${escapeHtml(catalogUrl)}"
                target="_blank"
                rel="noopener noreferrer"
                class="text-xs text-teal-300 hover:text-teal-200 underline underline-offset-2"
              >
                ${escapeHtml(
                  t(
                    'pcdt.provenance',
                    'Proveniência',
                    'Provenance'
                  )
                )} ·
                ${escapeHtml(
                  t(
                    'pcdt.source',
                    'Fonte oficial',
                    'Official source'
                  )
                )} ↗
              </a>
            </div>
          `
          : ''
        }
      </div>
    `;
  }

  function renderError(
    error
  ) {
    const target =
      document.getElementById(
        'pcdt-results'
      );

    if (!target) {
      return;
    }

    target.innerHTML = `
      <div class="bg-rose-950/30 border border-rose-800/50 p-4 rounded-xl text-rose-300 text-sm">
        ${escapeHtml(
          error?.message
          || t(
            'pcdt.error',
            'Não foi possível carregar o repositório PCDT.',
            'Unable to load the PCDT repository.'
          )
        )}
      </div>
    `;
  }

  async function loadIndex(
    query = '',
    {
      preserveSelection = false,
      page = 1,
      scrollToTop = false,
    } = {}
  ) {
    const clean =
      String(
        query
        || ''
      )
      .trim()
      .slice(
        0,
        120
      );

    const requestedPage =
      (
        Number.isInteger(
          page
        )
        && page >= 1
      )
      ? page
      : 1;

    state.searchEpoch += 1;

    const requestEpoch =
      state.searchEpoch;

    if (!preserveSelection) {
      clearExpandedState({
        persist: false,
      });
    }

    state.query =
      clean;

    state.page =
      requestedPage;

    saveSession();

    const params =
      new URLSearchParams({
        limit:
          String(
            PAGE_SIZE
          ),

        offset:
          String(
            (
              requestedPage - 1
            )
            * PAGE_SIZE
          ),
      });

    if (clean) {
      params.set(
        'q',
        clean
      );
    }

    const target =
      document.getElementById(
        'pcdt-results'
      );

    if (target) {
      target.innerHTML = `
        <div class="bg-slate-900 border border-slate-800 rounded-xl p-5 text-sm text-slate-400">
          ${escapeHtml(
            t(
              'pcdt.loading',
              'Carregando repositório PCDT...',
              'Loading PCDT repository...'
            )
          )}
        </div>
      `;
    }

    try {
      const payload =
        await fetchJson(
          `/api/v1/pcdt?${params.toString()}`
        );

      if (
        requestEpoch
        !== state.searchEpoch
      ) {
        return;
      }

      const total =
        Number(
          payload.total
          || 0
        );

      const totalPages =
        Math.max(
          1,
          Math.ceil(
            total
            / PAGE_SIZE
          )
        );

      if (
        total > 0
        && requestedPage
          > totalPages
      ) {
        await loadIndex(
          clean,
          {
            preserveSelection,
            page:
              totalPages,
            scrollToTop,
          }
        );

        return;
      }

      state.indexPayload =
        payload;

      state.page =
        requestedPage;

      if (
        preserveSelection
        && state.selectedPcdtId
        && !payload.items
          ?.some(
            item =>
              item.pcdt_id
              === state.selectedPcdtId
          )
      ) {
        clearExpandedState({
          persist: false,
        });
      }

      saveSession();
      renderIndex();

      if (scrollToTop) {
        document
          .getElementById(
            'pcdt-meta'
          )
          ?.scrollIntoView?.({
            block:
              'start',
          });
      }

    } catch (error) {
      if (
        requestEpoch
        !== state.searchEpoch
      ) {
        return;
      }

      renderError(
        error
      );
    }
  }


  async function loadDetail(
    pcdtId,
    {
      remember = true,
    } = {}
  ) {
    const key =
      String(
        pcdtId
        || ''
      );

    if (!validPcdtId(
      key
    )) {
      return;
    }

    const detailEpoch =
      state.searchEpoch;

    state.selectedPcdtId =
      key;

    state.detailPayload =
      null;

    state.documentsPayload =
      null;

    saveSession();
    renderIndex();

    const initialTarget =
      detailContainerFor(
        key
      );

    try {
      const [
        detail,
        documents,
      ] = await Promise.all([
        fetchJson(
          `/api/v1/pcdt/${encodeURIComponent(key)}`
        ),

        fetchJson(
          `/api/v1/pcdt/${encodeURIComponent(key)}/documents`
        ),
      ]);

      if (
        state.selectedPcdtId
        !== key
        || state.searchEpoch
          !== detailEpoch
      ) {
        return;
      }

      state.detailPayload =
        detail;

      state.documentsPayload =
        documents;

      if (
        remember
        && detail?.pcdt
      ) {
        rememberRecent(
          detail.pcdt
        );

        renderRecent();
      }

      renderDetail();

    } catch (error) {
      if (
        state.selectedPcdtId
        !== key
        || state.searchEpoch
          !== detailEpoch
      ) {
        return;
      }

      const target =
        detailContainerFor(
          key
        )
        || initialTarget;

      if (target) {
        target.innerHTML = `
          <div class="bg-rose-950/30 border border-rose-800/50 p-4 rounded-xl text-rose-300 text-sm">
            ${escapeHtml(
              error?.message
              || t(
                'pcdt.error',
                'Não foi possível carregar o repositório PCDT.',
                'Unable to load the PCDT repository.'
              )
            )}
          </div>
        `;
      }
    }
  }

  function wireEvents() {
    document
      .getElementById(
        'pcdt-search-form'
      )
      ?.addEventListener(
        'submit',
        event => {
          event.preventDefault();

          const value =
            document
              .getElementById(
                'pcdt-search-input'
              )
              ?.value
            || '';

          void loadIndex(
            value,
            {
              page: 1,
            }
          );
        }
      );


    document
      .getElementById(
        'pcdt-results'
      )
      ?.addEventListener(
        'click',
        event => {
          const pageTarget =
            event.target
              ?.closest?.(
                '[data-pcdt-page]'
              );

          if (pageTarget) {
            if (pageTarget.disabled) {
              return;
            }

            const page =
              Number.parseInt(
                pageTarget.dataset
                  .pcdtPage,
                10
              );

            if (
              !Number.isInteger(page)
              || page < 1
              || page === state.page
            ) {
              return;
            }

            void loadIndex(
              state.query,
              {
                page,
                scrollToTop: true,
              }
            );

            return;
          }

          const target =
            event.target
              ?.closest?.(
                '[data-pcdt-toggle]'
              );

          if (!target) {
            return;
          }

          const pcdtId =
            target.dataset
              .pcdtToggle;

          if (
            state.selectedPcdtId
            === pcdtId
          ) {
            clearExpandedState();
            renderIndex();
            return;
          }

          void loadDetail(
            pcdtId
          );
        }
      );


    document
      .getElementById(
        'pcdt-recent'
      )
      ?.addEventListener(
        'click',
        event => {
          const target =
            event.target
              ?.closest?.(
                '[data-pcdt-recent]'
              );

          if (!target) {
            return;
          }

          const pcdtId =
            target.dataset
              .pcdtRecent;

          const recent =
            state.recentPcdts
              .find(
                item =>
                  item.pcdtId
                  === pcdtId
              );

          if (!recent) {
            return;
          }

          void (
            async () => {
              const query =
                displayTitle(
                  recent
                );

              const input =
                document.getElementById(
                  'pcdt-search-input'
                );

              if (input) {
                input.value =
                  query;
              }

              await loadIndex(
                query,
                {
                  page: 1,
                }
              );

              if (
                state.indexPayload
                  ?.items
                  ?.some(
                    item =>
                      item.pcdt_id
                      === pcdtId
                  )
              ) {
                await loadDetail(
                  pcdtId
                );
              }
            }
          )();
        }
      );
  }


  async function initialise() {
    loadSession();
    loadRecentSession();

    const restoredPcdtId =
      state.selectedPcdtId;

    localiseChrome();
    renderRecent();
    wireEvents();

    const input =
      document.getElementById(
        'pcdt-search-input'
      );

    if (input) {
      input.value =
        state.query;
    }

    await loadIndex(
      state.query,
      {
        preserveSelection: true,
        page:
          state.page,
      }
    );

    if (
      restoredPcdtId
      && state.selectedPcdtId
        === restoredPcdtId
    ) {
      await loadDetail(
        restoredPcdtId,
        {
          remember: false,
        }
      );
    }
  }


  async function goHome() {
    const input =
      document.getElementById(
        'pcdt-search-input'
      );

    if (input) {
      input.value = '';
    }

    clearExpandedState({
      persist: false,
    });

    await loadIndex(
      '',
      {
        page: 1,
      }
    );

    renderRecent();

    input?.focus?.();
  }


  document.addEventListener(
    'DOMContentLoaded',
    () => {
      void initialise();
    }
  );


  globalThis.addEventListener?.(
    'clinical-language-change',
    () => {
      localiseChrome();
      renderRecent();
      renderIndex();
      renderDetail();
    }
  );


  globalThis.ClinicalPcdtRepository =
    Object.freeze({
      loadIndex,
      loadDetail,
      goHome,
    });
})();
