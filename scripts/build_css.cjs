const fs = require('node:fs');
const path = require('node:path');
const tailwind = require('tailwindcss');
const postcss = require('postcss');

const root =
  path.resolve(
    __dirname,
    '..'
  );


function collectJavaScriptFiles(
  directory
) {
  const files = [];

  for (
    const entry
    of fs.readdirSync(
      directory,
      {
        withFileTypes: true
      }
    )
  ) {
    const absolute =
      path.join(
        directory,
        entry.name
      );

    if (
      entry.isDirectory()
    ) {
      files.push(
        ...collectJavaScriptFiles(
          absolute
        )
      );

      continue;
    }

    if (
      entry.isFile()
      && entry.name.endsWith(
        '.js'
      )
    ) {
      files.push(
        absolute
      );
    }
  }

  return files;
}


const htmlPath =
  path.join(
    root,
    'index.html'
  );

const javascriptFiles =
  collectJavaScriptFiles(
    path.join(
      root,
      'assets'
    )
  ).sort();

const candidates =
  new Set();


function addCandidateString(
  value
) {
  for (
    const token
    of String(value)
      .split(
        /\s+/
      )
  ) {
    if (
      token
      && !token.includes(
        '${'
      )
    ) {
      candidates.add(
        token
      );
    }
  }
}


function quotedStrings(
  expression
) {
  const values = [];

  const pattern =
    /(["'`])((?:\\.|(?!\1)[\s\S])*?)\1/g;

  for (
    const match
    of expression.matchAll(
      pattern
    )
  ) {
    values.push(
      match[2]
        .replace(
          /\\"/g,
          '"'
        )
        .replace(
          /\\'/g,
          "'"
        )
    );
  }

  return values;
}


function scanHtmlClassAttributes(
  source
) {
  const pattern =
    /\bclass\s*=\s*["']([^"']+)["']/g;

  for (
    const match
    of source.matchAll(
      pattern
    )
  ) {
    addCandidateString(
      match[1]
    );
  }
}


function scanEmbeddedClassAttributes(
  source
) {
  const pattern =
    /\bclass\s*=\s*\\?["']([^"'`]+)\\?["']/g;

  for (
    const match
    of source.matchAll(
      pattern
    )
  ) {
    addCandidateString(
      match[1]
    );
  }
}


function scanClassNameAssignments(
  source
) {
  const pattern =
    /\.className\s*=\s*([\s\S]*?);/g;

  for (
    const match
    of source.matchAll(
      pattern
    )
  ) {
    for (
      const value
      of quotedStrings(
        match[1]
      )
    ) {
      addCandidateString(
        value
      );
    }
  }
}


function scanClassListCalls(
  source
) {
  const pattern =
    /\.classList\.(?:add|remove|toggle)\s*\(([\s\S]*?)\)/g;

  for (
    const match
    of source.matchAll(
      pattern
    )
  ) {
    for (
      const value
      of quotedStrings(
        match[1]
      )
    ) {
      addCandidateString(
        value
      );
    }
  }
}


const html =
  fs.readFileSync(
    htmlPath,
    'utf8'
  );

scanHtmlClassAttributes(
  html
);


for (
  const sourcePath
  of javascriptFiles
) {
  const source =
    fs.readFileSync(
      sourcePath,
      'utf8'
    );

  scanEmbeddedClassAttributes(
    source
  );

  scanClassNameAssignments(
    source
  );

  scanClassListCalls(
    source
  );
}


const tailwindCss =
  fs.readFileSync(
    require.resolve(
      'tailwindcss/index.css'
    ),
    'utf8'
  );


(async () => {
  const compiler =
    await tailwind.compile(
      tailwindCss
    );

  const built =
    compiler.build(
      [
        ...candidates
      ].sort()
    );

  const rootCss =
    postcss.parse(
      built
    );

  rootCss.walkComments(
    (node) =>
      node.remove()
  );

  rootCss.walk(
    (node) => {
      if (node.raws) {
        node.raws.before =
          '';
      }

      if (
        node.type === 'rule'
        && node.raws
      ) {
        node.raws.between =
          '';
      }

      if (
        node.type === 'decl'
        && node.raws
      ) {
        node.raws.between =
          ':';
      }
    }
  );

  const output =
    rootCss
      .toString()
      .trim()
    + '\n';

  const target =
    path.join(
      root,
      'assets',
      'app.css'
    );

  fs.writeFileSync(
    target,
    output
  );

  console.log(
    `Built ${target} from `
    + `${candidates.size} class candidates `
    + `across ${1 + javascriptFiles.length} source files `
    + `(${output.length} bytes).`
  );
})().catch(
  (error) => {
    console.error(
      error
    );

    process.exit(
      1
    );
  }
);
