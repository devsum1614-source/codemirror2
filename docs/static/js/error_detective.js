/**
 * Error Detective & Browser JS Sandbox for Code Wizard
 * - Parses compiler & runtime errors across Python, JS, TS, SQL, C, C++, Java, HTML/CSS
 * - Explains errors in plain beginner-friendly language, extracts line numbers
 * - Offers Give me a hint, Explain this error, and Suggest a fix (with diff & explicit Apply)
 * - Calls /api/v1/error-help when server AI is configured; falls back clearly when not
 * - Runs JavaScript safely inside a sandboxed iframe when host Node.js is unavailable
 */
(function () {
  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, ch => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[ch]);
  }

  function extractLineNumber(errorText, language) {
    const text = String(errorText || '');
    const patterns = [
      /line\s+(\d+)/i,
      /main\.(?:py|c|cpp|js|ts):(\d+)/i,
      /Main\.java:(\d+)/i,
      /:(\d+):\d+/
    ];
    for (const re of patterns) {
      const m = text.match(re);
      if (m && m[1]) {
        const n = parseInt(m[1], 10);
        if (n > 0) return n;
      }
    }
    return null;
  }

  function diagnoseError(errorText, code, language) {
    const err = String(errorText || '').trim();
    const lang = (language || 'python').toLowerCase();
    const lineNum = extractLineNumber(err, lang);
    const lines = String(code || '').split('\n');
    const offendingLine = lineNum && lines[lineNum - 1] !== undefined ? lines[lineNum - 1] : null;

    const rules = [
      {
        match: /SyntaxError.*expected ':'|expected ':'/i,
        title: 'Missing colon (:)',
        plain: 'In Python, lines starting with def, if, elif, else, for, or while must end with a colon (:).',
        hint: lineNum ? `Look at the end of line ${lineNum}. Is there a colon (:) missing?` : 'Check the end of your if, for, while, or def line for a missing colon (:).',
        fix: () => {
          if (!lineNum || offendingLine === null) return null;
          const trimmed = offendingLine.trimEnd();
          if (/^\s*(def|if|elif|else|for|while|class)\b/.test(trimmed) && !trimmed.endsWith(':')) {
            const copy = lines.slice();
            copy[lineNum - 1] = trimmed + ':';
            return { code: copy.join('\n'), note: `Added missing ':' at the end of line ${lineNum}.` };
          }
          return null;
        }
      },
      {
        match: /IndentationError|unexpected indent|expected an indented block/i,
        title: 'Indentation mismatch',
        plain: 'Python uses spaces at the start of a line to group code inside if, for, while, or def blocks. One or more lines are not aligned consistently.',
        hint: lineNum ? `Check the spaces at the beginning of line ${lineNum} (and the line right above it). Use 4 spaces for each inner block.` : 'Check that lines inside a block are indented by 4 spaces consistently.',
        fix: () => {
          if (!lineNum || offendingLine === null) return null;
          if (/expected an indented block/i.test(err) && !offendingLine.startsWith('    ')) {
            const copy = lines.slice();
            copy[lineNum - 1] = '    ' + offendingLine.trimStart();
            return { code: copy.join('\n'), note: `Indented line ${lineNum} by 4 spaces.` };
          }
          return null;
        }
      },
      {
        match: /NameError:\s*name '([^']+)' is not defined/i,
        title: 'Undefined variable or function name',
        plain: (m) => `Your code used "${m[1]}", but Python does not know what "${m[1]}" is yet. It may be misspelled or used before it was created.`,
        hint: (m) => `Check the spelling of "${m[1]}" (capitalization matters!) and make sure you defined it before this line.`,
        fix: () => null
      },
      {
        match: /ReferenceError:\s*([A-Za-z0-9_$]+) is not defined/i,
        title: 'Undefined variable or function',
        plain: (m) => `JavaScript tried to use "${m[1]}", which has not been declared yet or has a typo.`,
        hint: (m) => `Check if "${m[1]}" is spelled the same way where you declared it with let, const, or function.`,
        fix: () => null
      },
      {
        match: /ZeroDivisionError|division by zero/i,
        title: 'Division by zero',
        plain: 'Your program tried to divide a number by 0, which is not allowed in math or programming.',
        hint: lineNum ? `Check the denominator on line ${lineNum} — make sure it is not 0 before dividing.` : 'Check any / or % operator and make sure the right side cannot be 0.',
        fix: () => null
      },
      {
        match: /TypeError:/i,
        title: 'Mismatched data types',
        plain: 'An operation was applied to values of incompatible types — for example, adding text (a string) directly to a number, or calling something that is not a function.',
        hint: lineNum ? `Check the types of the values on line ${lineNum}. You may need int(), str(), or Number() to convert one of them.` : 'Check whether you are mixing text and numbers or calling a value that is undefined.',
        fix: () => null
      },
      {
        match: /IndexError|ArrayIndexOutOfBoundsException/i,
        title: 'Index out of range',
        plain: 'Your code tried to read an item at a position that does not exist in the list or array (remember indexing starts at 0).',
        hint: 'Check your loop bounds or index number — for a list of length N, valid indexes are 0 through N - 1.',
        fix: () => null
      },
      {
        match: /ValueError:/i,
        title: 'Invalid value for conversion',
        plain: 'A function received the right type of input, but the value itself could not be converted (for example, turning "abc" into an integer with int()).',
        hint: 'Check what input value is being passed — if using input(), make sure Custom Input contains a valid number.',
        fix: () => null
      },
      {
        match: /EOFError|EOF when reading a line/i,
        title: 'Waiting for input (empty stdin)',
        plain: 'Your program called input(), but no text was provided in the Custom Input box.',
        hint: 'Open "Input (stdin)" below the editor, type a sample value (like Sam or 5), and click Run again.',
        fix: () => null
      },
      {
        match: /no such table:\s*([^\s]+)/i,
        title: 'SQL table not found',
        plain: (m) => `SQLite could not find a table named "${m[1]}". Check the Available Tables panel on the right for exact table names.`,
        hint: 'Available tables include Customers, Orders, resources, and categories. Check spelling and capitalization.',
        fix: () => null
      },
      {
        match: /no such column:\s*([^\s]+)/i,
        title: 'SQL column not found',
        plain: (m) => `SQLite could not find a column named "${m[1]}". Remember to put text values inside single quotes ('like this'), not bare words.`,
        hint: 'Check the Available Tables schema on the right to verify the exact column name.',
        fix: () => null
      },
      {
        match: /SQL error:.*syntax error/i,
        title: 'SQL syntax error',
        plain: 'There is a grammar mistake in your SQL query — such as a missing comma, misspelled keyword (SELECT, FROM, WHERE), or unclosed quote.',
        hint: 'Check the keyword order: SELECT columns FROM table WHERE condition ORDER BY column;',
        fix: () => null
      },
      {
        match: /expected ['"]?;['"]?|';' expected/i,
        title: 'Missing semicolon (;)',
        plain: 'In C, C++, and Java, every statement must end with a semicolon (;).',
        hint: lineNum ? `Look at line ${lineNum} and the line just before it — one of them is likely missing a semicolon (;).` : 'Check the end of your statements for a missing semicolon (;).',
        fix: () => {
          const targetIdx = lineNum ? Math.max(0, lineNum - 2) : -1;
          if (targetIdx >= 0 && lines[targetIdx] && !lines[targetIdx].trimEnd().endsWith(';') && !lines[targetIdx].trimEnd().endsWith('{') && !lines[targetIdx].trimEnd().endsWith('}')) {
            const copy = lines.slice();
            copy[targetIdx] = copy[targetIdx].trimEnd() + ';';
            return { code: copy.join('\n'), note: `Added ';' at the end of line ${targetIdx + 1}.` };
          }
          return null;
        }
      },
      {
        match: /SyntaxError:/i,
        title: 'Syntax error',
        plain: 'The language could not understand the structure of your code. Common causes are a missing parenthesis ), quote ", bracket ], or comma.',
        hint: lineNum ? `Inspect line ${lineNum} (and the line just above it) for unclosed quotes, parentheses, or typos.` : 'Look for unmatched quotes, brackets, or parentheses.',
        fix: () => {
          if (!lineNum || offendingLine === null) return null;
          const opens = (offendingLine.match(/\(/g) || []).length;
          const closes = (offendingLine.match(/\)/g) || []).length;
          if (opens === closes + 1) {
            const copy = lines.slice();
            copy[lineNum - 1] = offendingLine.trimEnd() + ')';
            return { code: copy.join('\n'), note: `Added missing ')' at the end of line ${lineNum}.` };
          }
          return null;
        }
      },
      {
        match: /Expected\s+(.+?),\s*got\s+(None|undefined)\b/i,
        title: 'Missing return value (got None)',
        plain: (m) => `The test expected ${m[1]}, but your function returned ${m[2]}. In Python, a function without a return statement (or with only pass / print) returns None automatically.`,
        hint: 'Check your function body: make sure it ends with a return statement that sends back the calculated result (instead of pass or print).',
        fix: () => null
      },
      {
        match: /Expected\s+(.+?),\s*got\s+(.+)/i,
        title: 'Output does not match expected value',
        plain: (m) => `Your code ran without syntax errors, but it returned ${m[2]} instead of ${m[1]}.`,
        hint: 'Check your formula or conditions against the Lab Guide, and test with edge cases like 0, negative numbers, or decimals.',
        fix: () => null
      },
      {
        match: /Time limit exceeded|TimeoutExpired/i,
        title: 'Program took too long (possible infinite loop)',
        plain: 'Your program did not finish within the time limit. This usually happens when a while loop condition never becomes false.',
        hint: 'Check every while loop to be sure the loop variable changes each time so the loop can end.',
        fix: () => null
      }
    ];

    for (const rule of rules) {
      const m = err.match(rule.match);
      if (m) {
        const plain = typeof rule.plain === 'function' ? rule.plain(m) : rule.plain;
        const hint = typeof rule.hint === 'function' ? rule.hint(m) : rule.hint;
        const suggested = rule.fix ? rule.fix(m) : null;
        return {
          title: rule.title,
          lineNumber: lineNum,
          offendingLine,
          plain,
          hint,
          uncertain: false,
          suggested
        };
      }
    }

    return {
      title: 'Uncertain cause — needs closer inspection',
      lineNumber: lineNum,
      offendingLine,
      plain: 'Error Detective cannot be certain about the exact cause of this error from the message alone.',
      hint: lineNum
        ? `Start by reading line ${lineNum} and the line just above it carefully, then check variable names, brackets, and types.`
        : 'Read the last line of the error message carefully, check recent edits, and try printing intermediate values to narrow it down.',
      uncertain: true,
      suggested: null
    };
  }

  function buildLineDiffHtml(originalCode, suggestedCode) {
    const oldLines = String(originalCode || '').split('\n');
    const newLines = String(suggestedCode || '').split('\n');
    const maxLen = Math.max(oldLines.length, newLines.length);
    const rows = [];
    for (let i = 0; i < maxLen; i++) {
      const a = oldLines[i];
      const b = newLines[i];
      if (a === b) {
        rows.push(`<div class="ed-diff-line same"><span class="ed-ln">${i + 1}</span><span>  ${escapeHtml(a ?? '')}</span></div>`);
      } else {
        if (a !== undefined) {
          rows.push(`<div class="ed-diff-line removed"><span class="ed-ln">${i + 1}</span><span>- ${escapeHtml(a)}</span></div>`);
        }
        if (b !== undefined) {
          rows.push(`<div class="ed-diff-line added"><span class="ed-ln">${i + 1}</span><span>+ ${escapeHtml(b)}</span></div>`);
        }
      }
    }
    return rows.join('');
  }

  // Sandboxed browser JavaScript execution (no access to parent DOM or cookies)
  function runJavaScriptInBrowser(code, timeoutMs = 2000) {
    return new Promise((resolve) => {
      const start = performance.now();
      const iframe = document.createElement('iframe');
      iframe.setAttribute('sandbox', 'allow-scripts');
      iframe.style.display = 'none';
      const channelId = 'cw_js_' + Math.random().toString(36).slice(2);
      let settled = false;

      const cleanup = () => {
        window.removeEventListener('message', onMessage);
        if (iframe.parentNode) iframe.parentNode.removeChild(iframe);
      };

      const timer = setTimeout(() => {
        if (settled) return;
        settled = true;
        cleanup();
        resolve({
          language: 'javascript',
          language_name: 'JavaScript',
          runtime_label: 'Browser JS Sandbox',
          runtime_available: true,
          status_label: 'Browser Sandbox',
          mode_label: 'Runnable',
          ran: true,
          success: false,
          output: '',
          error: `Time limit exceeded (${timeoutMs / 1000}s). Check your code for an infinite loop.`,
          duration_ms: Math.round(performance.now() - start)
        });
      }, timeoutMs);

      function onMessage(ev) {
        if (!ev.data || ev.data.channel !== channelId) return;
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        cleanup();
        resolve({
          language: 'javascript',
          language_name: 'JavaScript',
          runtime_label: 'Browser JS Sandbox',
          runtime_available: true,
          status_label: 'Browser Sandbox',
          mode_label: 'Runnable',
          ran: true,
          success: !ev.data.error,
          output: ev.data.output || '',
          error: ev.data.error || null,
          duration_ms: Math.round(performance.now() - start)
        });
      }

      window.addEventListener('message', onMessage);
      const encoded = JSON.stringify(String(code || '')).replace(/<\/script>/gi, '<\\/script>');
      iframe.srcdoc = `<!DOCTYPE html><html><body><script>
        (function(){
          var logs = [];
          function fmt(v){
            if (typeof v === 'string') return v;
            try { return JSON.stringify(v); } catch(e) { return String(v); }
          }
          console.log = function(){ logs.push(Array.prototype.slice.call(arguments).map(fmt).join(' ')); };
          console.info = console.log;
          console.warn = function(){ logs.push('[warn] ' + Array.prototype.slice.call(arguments).map(fmt).join(' ')); };
          console.error = function(){ logs.push('[error] ' + Array.prototype.slice.call(arguments).map(fmt).join(' ')); };
          var errMsg = null;
          try {
            var fn = new Function(${encoded});
            fn();
          } catch (e) {
            errMsg = (e && e.name ? e.name + ': ' : '') + (e && e.message ? e.message : String(e));
          }
          parent.postMessage({ channel: ${JSON.stringify(channelId)}, output: logs.join('\\n'), error: errMsg }, '*');
        })();
      <\/script></body></html>`;
      document.body.appendChild(iframe);
    });
  }

  window.ErrorDetective = {
    extractLineNumber,
    diagnoseError,
    buildLineDiffHtml,
    runJavaScriptInBrowser
  };
})();
