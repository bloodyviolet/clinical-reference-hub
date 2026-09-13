(() => {
  'use strict';

  const STORAGE_KEY =
    'clinical-reference-v2-pcdt-repository-v1';

  const state = {
    query: '',
    selectedPcdtId: null,
    indexPayload: null,
    detailPayload: null,
    documentsPayload: null,
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

          selectedPcdtId:
            state.selectedPcdtId,
        })
      );

    } catch (_) {}
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

    target.textContent =
      `${t(
        'pcdt.showing',
        'Exibindo',
        'Showing'
      )} ${state.indexPayload.returned} / ${state.indexPayload.total}`;
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

    target.innerHTML =
      data.items.map(
        item => {
          const selected =
            item.pcdt_id
            === state.selectedPcdtId;

          return `
            <button
              type="button"
              data-pcdt-open="${escapeHtml(item.pcdt_id)}"
              class="w-full text-left bg-slate-900 border ${
                selected
                ? 'border-teal-500'
                : 'border-slate-800'
              } rounded-xl p-4 hover:border-teal-700 transition shadow-lg"
            >
              <div class="flex items-start justify-between gap-3">
                <div>
                  <p class="text-sm font-semibold text-white">
                    ${escapeHtml(
                      item.canonical_title_pt
                    )}
                  </p>

                  <p class="text-[10px] text-slate-500 mt-1 font-mono break-all">
                    ${escapeHtml(
                      item.pcdt_id
                    )}
                  </p>
                </div>

                <span class="text-[10px] px-2 py-1 rounded border border-slate-700 text-slate-300">
                  ${escapeHtml(
                    item.document_count
                  )} docs
                </span>
              </div>

              <div class="mt-3 text-[11px] text-slate-400 flex flex-wrap gap-x-4 gap-y-1">
                <span>
                  ${escapeHtml(
                    t(
                      'pcdt.versions',
                      'Versões / atos de aprovação',
                      'Versions / approval instruments'
                    )
                  )}:
                  ${escapeHtml(
                    item.approval_version_count
                  )}
                </span>

                <span>
                  ${escapeHtml(
                    t(
                      'pcdt.approvalState',
                      'Situação de aprovação',
                      'Approval status'
                    )
                  )}:
                  ${escapeHtml(
                    item.approval_state
                  )}
                </span>
              </div>
            </button>
          `;
        }
      ).join('');
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
      document.getElementById(
        'pcdt-detail'
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

    const aliases = [
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
              t(
                'pcdt.officialTitle',
                'Título oficial',
                'Official title'
              )
            )} · PT-BR
          </p>

          <h2 class="text-xl font-bold text-white mt-1">
            ${escapeHtml(
              pcdt.canonical_title_pt
            )}
          </h2>

          <p class="text-[10px] text-slate-500 font-mono mt-1 break-all">
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
    query = ''
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

    state.query =
      clean;

    saveSession();

    const params =
      new URLSearchParams({
        limit:
          '50',

        offset:
          '0',
      });

    if (clean) {
      params.set(
        'q',
        clean
      );
    }

    try {
      state.indexPayload =
        await fetchJson(
          `/api/v1/pcdt?${params.toString()}`
        );

      renderIndex();

    } catch (error) {
      renderError(
        error
      );
    }
  }


  async function loadDetail(
    pcdtId
  ) {
    const key =
      String(
        pcdtId
        || ''
      );

    if (
      !/^[a-z0-9][a-z0-9-]{0,199}$/
        .test(
          key
        )
    ) {
      return;
    }

    state.selectedPcdtId =
      key;

    saveSession();
    renderIndex();

    const target =
      document.getElementById(
        'pcdt-detail'
      );

    if (target) {
      target.innerHTML = `
        <p class="text-sm text-slate-400">
          ${escapeHtml(
            t(
              'pcdt.loading',
              'Carregando repositório PCDT...',
              'Loading PCDT repository...'
            )
          )}
        </p>
      `;
    }

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

      state.detailPayload =
        detail;

      state.documentsPayload =
        documents;

      renderDetail();

    } catch (error) {
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

          state.selectedPcdtId =
            null;

          state.detailPayload =
            null;

          state.documentsPayload =
            null;

          const value =
            document
              .getElementById(
                'pcdt-search-input'
              )
              ?.value
            || '';

          void loadIndex(
            value
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
          const target =
            event.target
              ?.closest?.(
                '[data-pcdt-open]'
              );

          if (!target) {
            return;
          }

          void loadDetail(
            target.dataset.pcdtOpen
          );
        }
      );
  }


  async function initialise() {
    loadSession();
    localiseChrome();
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
      state.query
    );

    if (
      state.selectedPcdtId
    ) {
      await loadDetail(
        state.selectedPcdtId
      );
    }
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
      renderIndex();
      renderDetail();
    }
  );


  globalThis.ClinicalPcdtRepository =
    Object.freeze({
      loadIndex,
      loadDetail,
    });
})();
