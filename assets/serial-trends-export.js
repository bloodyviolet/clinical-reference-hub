(() => {
  'use strict';


  function stringValue(value) {
    if (
      value === null
      || value === undefined
    ) {
      return '—';
    }

    if (
      typeof value === 'object'
    ) {
      return JSON.stringify(
        value
      );
    }

    return String(value);
  }


  function reportLines(report) {
    const lines = [
      report.title,
      `Release: ${report.release}`,
      `Generated: ${report.generated_at}`,
      '',
      report.privacy_notice,
      report.visualisation_boundary,
      ''
    ];

    for (
      const instrument
      of report.instruments
      || []
    ) {
      lines.push(
        `=== ${instrument.label} [${instrument.key}] ===`
      );

      for (
        const observation
        of instrument.observations
        || []
      ) {
        lines.push(
          `Observed: ${observation.observed_at}`
        );

        lines.push(
          `Captured: ${observation.captured_at}`
        );

        lines.push(
          `Source: ${observation.execution_source}`
        );

        if (
          observation.equal_time_tie
        ) {
          lines.push(
            'Temporal tie: yes; no clinical order inferred'
          );
        }

        for (
          const [
            label,
            fields
          ]
          of [
            [
              'Summary',
              observation.summary_fields
            ],
            [
              'Components',
              observation.component_fields
            ],
            [
              'Context',
              observation.context_fields
            ]
          ]
        ) {
          lines.push(
            `${label}:`
          );

          if (
            !fields
            || fields.length === 0
          ) {
            lines.push(
              '  —'
            );

          } else {
            for (
              const field
              of fields
            ) {
              lines.push(
                `  ${field.path}: ${
                  field.present
                    ? stringValue(
                        field.value
                      )
                    : '—'
                }`
              );
            }
          }
        }

        lines.push(
          'Request snapshot: '
          + JSON.stringify(
              observation
                .request_snapshot
            )
        );

        lines.push(
          'Result snapshot: '
          + JSON.stringify(
              observation
                .result_snapshot
            )
        );

        lines.push('');
      }
    }

    return lines;
  }


  function wrapLines(
    lines,
    width = 96
  ) {
    const output = [];

    for (
      const raw
      of lines
    ) {
      const line =
        String(
          raw
          ?? ''
        );

      if (
        line.length <= width
      ) {
        output.push(
          line
        );

        continue;
      }

      let remaining =
        line;

      while (
        remaining.length
        > width
      ) {
        let split =
          remaining.lastIndexOf(
            ' ',
            width
          );

        if (
          split < 1
        ) {
          split = width;
        }

        output.push(
          remaining
            .slice(
              0,
              split
            )
        );

        remaining =
          remaining
            .slice(
              split
            )
            .trimStart();
      }

      output.push(
        remaining
      );
    }

    return output;
  }


  const CP1252 =
    Object.freeze({
      0x20ac: 0x80,
      0x201a: 0x82,
      0x0192: 0x83,
      0x201e: 0x84,
      0x2026: 0x85,
      0x2020: 0x86,
      0x2021: 0x87,
      0x02c6: 0x88,
      0x2030: 0x89,
      0x0160: 0x8a,
      0x2039: 0x8b,
      0x0152: 0x8c,
      0x017d: 0x8e,
      0x2018: 0x91,
      0x2019: 0x92,
      0x201c: 0x93,
      0x201d: 0x94,
      0x2022: 0x95,
      0x2013: 0x96,
      0x2014: 0x97,
      0x02dc: 0x98,
      0x2122: 0x99,
      0x0161: 0x9a,
      0x203a: 0x9b,
      0x0153: 0x9c,
      0x017e: 0x9e,
      0x0178: 0x9f
    });


  function pdfByte(
    character
  ) {
    const code =
      character
        .codePointAt(
          0
        );

    if (
      code <= 0xff
    ) {
      return code;
    }

    if (
      Object.prototype
        .hasOwnProperty.call(
          CP1252,
          code
        )
    ) {
      return CP1252[
        code
      ];
    }

    return 0x3f;
  }


  function pdfEscape(
    value
  ) {
    let result = '';

    for (
      const character
      of String(value)
        .replaceAll(
          '≥',
          '>='
        )
        .replaceAll(
          '≤',
          '<='
        )
    ) {
      const byte =
        pdfByte(
          character
        );

      if (
        byte === 0x28
        || byte === 0x29
        || byte === 0x5c
      ) {
        result += '\\';
      }

      result +=
        String.fromCharCode(
          byte
        );
    }

    return result;
  }


  function binaryBytes(
    value
  ) {
    return Uint8Array.from(
      value,
      (character) =>
        character
          .charCodeAt(
            0
          )
        & 0xff
    );
  }


  function buildPdfBytes(
    report
  ) {
    const lines =
      wrapLines(
        reportLines(
          report
        ),
        96
      );

    const linesPerPage = 58;

    const pages = [];

    for (
      let i = 0;
      i < lines.length;
      i += linesPerPage
    ) {
      pages.push(
        lines.slice(
          i,
          i + linesPerPage
        )
      );
    }

    if (
      pages.length === 0
    ) {
      pages.push([]);
    }

    const objectCount =
      3
      + pages.length * 2;

    const objects =
      new Array(
        objectCount + 1
      );

    const pageObjectNumbers =
      pages.map(
        (_, index) =>
          4 + index * 2
      );

    const contentObjectNumbers =
      pages.map(
        (_, index) =>
          5 + index * 2
      );

    objects[1] =
      '<< /Type /Catalog /Pages 2 0 R >>';

    objects[2] =
      (
        '<< /Type /Pages /Count '
        + pages.length
        + ' /Kids ['
        + pageObjectNumbers
          .map(
            (number) =>
              `${number} 0 R`
          )
          .join(' ')
        + '] >>'
      );

    objects[3] =
      (
        '<< /Type /Font /Subtype /Type1 '
        + '/BaseFont /Helvetica '
        + '/Encoding /WinAnsiEncoding >>'
      );

    pages.forEach(
      (
        pageLines,
        index
      ) => {
        const pageNumber =
          pageObjectNumbers[
            index
          ];

        const contentNumber =
          contentObjectNumbers[
            index
          ];

        const commands = [
          'BT',
          '/F1 9 Tf',
          '40 800 Td',
          '11 TL'
        ];

        for (
          const line
          of pageLines
        ) {
          commands.push(
            `(${pdfEscape(line)}) Tj`
          );

          commands.push(
            'T*'
          );
        }

        commands.push(
          'ET'
        );

        const stream =
          commands.join(
            '\n'
          ) + '\n';

        objects[
          pageNumber
        ] =
          (
            '<< /Type /Page '
            + '/Parent 2 0 R '
            + '/MediaBox [0 0 595 842] '
            + '/Resources << /Font << /F1 3 0 R >> >> '
            + `/Contents ${contentNumber} 0 R >>`
          );

        objects[
          contentNumber
        ] =
          (
            `<< /Length ${stream.length} >>\n`
            + 'stream\n'
            + stream
            + 'endstream'
          );
      }
    );

    let binary =
      '%PDF-1.4\n'
      + '%\xE2\xE3\xCF\xD3\n';

    const offsets =
      new Array(
        objectCount + 1
      ).fill(
        0
      );

    for (
      let number = 1;
      number <= objectCount;
      number += 1
    ) {
      offsets[number] =
        binary.length;

      binary +=
        `${number} 0 obj\n`
        + objects[number]
        + '\nendobj\n';
    }

    const xrefOffset =
      binary.length;

    binary +=
      `xref\n0 ${objectCount + 1}\n`;

    binary +=
      '0000000000 65535 f \n';

    for (
      let number = 1;
      number <= objectCount;
      number += 1
    ) {
      binary +=
        String(
          offsets[number]
        )
          .padStart(
            10,
            '0'
          )
        + ' 00000 n \n';
    }

    binary +=
      'trailer\n'
      + `<< /Size ${objectCount + 1} /Root 1 0 R >>\n`
      + 'startxref\n'
      + `${xrefOffset}\n`
      + '%%EOF\n';

    return binaryBytes(
      binary
    );
  }


  const CRC_TABLE =
    (() => {
      const table =
        new Uint32Array(
          256
        );

      for (
        let n = 0;
        n < 256;
        n += 1
      ) {
        let c = n;

        for (
          let k = 0;
          k < 8;
          k += 1
        ) {
          c =
            (
              c & 1
            )
              ? (
                  0xedb88320
                  ^ (
                    c >>> 1
                  )
                )
              : (
                  c >>> 1
                );
        }

        table[n] =
          c >>> 0;
      }

      return table;
    })();


  function crc32(
    bytes
  ) {
    let crc =
      0xffffffff;

    for (
      const byte
      of bytes
    ) {
      crc =
        CRC_TABLE[
          (
            crc
            ^ byte
          )
          & 0xff
        ]
        ^ (
          crc >>> 8
        );
    }

    return (
      crc
      ^ 0xffffffff
    ) >>> 0;
  }


  function push16(
    output,
    value
  ) {
    output.push(
      value & 0xff,
      (
        value >>> 8
      ) & 0xff
    );
  }


  function push32(
    output,
    value
  ) {
    output.push(
      value & 0xff,
      (
        value >>> 8
      ) & 0xff,
      (
        value >>> 16
      ) & 0xff,
      (
        value >>> 24
      ) & 0xff
    );
  }


  function utf8(
    value
  ) {
    return new TextEncoder()
      .encode(
        value
      );
  }


  function concatBytes(
    chunks
  ) {
    const length =
      chunks.reduce(
        (
          total,
          chunk
        ) =>
          total + chunk.length,
        0
      );

    const result =
      new Uint8Array(
        length
      );

    let offset = 0;

    for (
      const chunk
      of chunks
    ) {
      result.set(
        chunk,
        offset
      );

      offset +=
        chunk.length;
    }

    return result;
  }


  function zipStore(
    files
  ) {
    const localChunks = [];
    const centralChunks = [];

    let localOffset = 0;

    for (
      const file
      of files
    ) {
      const nameBytes =
        utf8(
          file.name
        );

      const data =
        file.data;

      const crc =
        crc32(
          data
        );

      const localHeader = [];

      push32(
        localHeader,
        0x04034b50
      );

      push16(
        localHeader,
        20
      );

      push16(
        localHeader,
        0x0800
      );

      push16(
        localHeader,
        0
      );

      push16(
        localHeader,
        0
      );

      push16(
        localHeader,
        0
      );

      push32(
        localHeader,
        crc
      );

      push32(
        localHeader,
        data.length
      );

      push32(
        localHeader,
        data.length
      );

      push16(
        localHeader,
        nameBytes.length
      );

      push16(
        localHeader,
        0
      );

      const local =
        concatBytes([
          Uint8Array.from(
            localHeader
          ),
          nameBytes,
          data
        ]);

      localChunks.push(
        local
      );

      const centralHeader = [];

      push32(
        centralHeader,
        0x02014b50
      );

      push16(
        centralHeader,
        20
      );

      push16(
        centralHeader,
        20
      );

      push16(
        centralHeader,
        0x0800
      );

      push16(
        centralHeader,
        0
      );

      push16(
        centralHeader,
        0
      );

      push16(
        centralHeader,
        0
      );

      push32(
        centralHeader,
        crc
      );

      push32(
        centralHeader,
        data.length
      );

      push32(
        centralHeader,
        data.length
      );

      push16(
        centralHeader,
        nameBytes.length
      );

      push16(
        centralHeader,
        0
      );

      push16(
        centralHeader,
        0
      );

      push16(
        centralHeader,
        0
      );

      push16(
        centralHeader,
        0
      );

      push32(
        centralHeader,
        0
      );

      push32(
        centralHeader,
        localOffset
      );

      const central =
        concatBytes([
          Uint8Array.from(
            centralHeader
          ),
          nameBytes
        ]);

      centralChunks.push(
        central
      );

      localOffset +=
        local.length;
    }

    const centralDirectory =
      concatBytes(
        centralChunks
      );

    const localData =
      concatBytes(
        localChunks
      );

    const end = [];

    push32(
      end,
      0x06054b50
    );

    push16(
      end,
      0
    );

    push16(
      end,
      0
    );

    push16(
      end,
      files.length
    );

    push16(
      end,
      files.length
    );

    push32(
      end,
      centralDirectory.length
    );

    push32(
      end,
      localData.length
    );

    push16(
      end,
      0
    );

    return concatBytes([
      localData,
      centralDirectory,
      Uint8Array.from(
        end
      )
    ]);
  }


  function xmlEscape(
    value
  ) {
    return String(value)
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
        '&apos;'
      );
  }


  function buildDocxBytes(
    report
  ) {
    const lines =
      wrapLines(
        reportLines(
          report
        ),
        120
      );

    const paragraphs =
      lines.map(
        (line) =>
          (
            '<w:p>'
            + '<w:r>'
            + '<w:t xml:space="preserve">'
            + xmlEscape(
                line
              )
            + '</w:t>'
            + '</w:r>'
            + '</w:p>'
          )
      ).join('');

    const documentXml =
      (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        + '<w:document '
        + 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        + '<w:body>'
        + paragraphs
        + '<w:sectPr>'
        + '<w:pgSz w:w="11906" w:h="16838"/>'
        + '<w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440"/>'
        + '</w:sectPr>'
        + '</w:body>'
        + '</w:document>'
      );

    const contentTypes =
      (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        + '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
        + '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
        + '<Default Extension="xml" ContentType="application/xml"/>'
        + '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
        + '</Types>'
      );

    const relationships =
      (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        + '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        + '<Relationship Id="rId1" '
        + 'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
        + 'Target="word/document.xml"/>'
        + '</Relationships>'
      );

    return zipStore([
      {
        name:
          '[Content_Types].xml',

        data:
          utf8(
            contentTypes
          )
      },

      {
        name:
          '_rels/.rels',

        data:
          utf8(
            relationships
          )
      },

      {
        name:
          'word/document.xml',

        data:
          utf8(
            documentXml
          )
      }
    ]);
  }


  function downloadBytes(
    bytes,
    mime,
    filename
  ) {
    if (
      typeof document
      === 'undefined'
      || typeof Blob
      === 'undefined'
      || typeof URL
        ?.createObjectURL
      !== 'function'
    ) {
      throw new Error(
        'browser_download_unavailable'
      );
    }

    const blob =
      new Blob(
        [
          bytes
        ],
        {
          type: mime
        }
      );

    const url =
      URL.createObjectURL(
        blob
      );

    const anchor =
      document
        .createElement(
          'a'
        );

    anchor.href = url;
    anchor.download =
      filename;

    anchor.rel =
      'noopener';

    anchor.style.display =
      'none';

    document.body
      .appendChild(
        anchor
      );

    anchor.click();

    anchor.remove();

    setTimeout(
      () =>
        URL.revokeObjectURL(
          url
        ),
      0
    );
  }


  function downloadPdf(
    report,
    filename
  ) {
    downloadBytes(
      buildPdfBytes(
        report
      ),
      'application/pdf',
      filename
    );
  }


  function downloadDocx(
    report,
    filename
  ) {
    downloadBytes(
      buildDocxBytes(
        report
      ),
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      filename
    );
  }


  const api =
    Object.freeze({
      reportLines,
      buildPdfBytes,
      buildDocxBytes,
      downloadPdf,
      downloadDocx
    });


  if (
    typeof module !== 'undefined'
    && module.exports
  ) {
    module.exports =
      api;
  }


  if (
    typeof globalThis
    !== 'undefined'
  ) {
    globalThis
      .SerialTrendsExport =
        api;
  }
})();
