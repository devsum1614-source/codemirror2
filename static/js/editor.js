/**
 * Monaco Editor Controller for CodeMirror 2.0
 */
class EditorManager {
  constructor() {
    this.monacoInstance = null;
    this.editor = null;
    this.isMonacoReady = false;
    this.currentLanguage = 'javascript';
    this.fallbackTextarea = document.getElementById('fallback-editor');
    this.container = document.getElementById('monaco-container');
  }

  async init() {
    // Attempt to load Monaco via AMD loader
    if (window.monaco) {
      this._createEditor();
      return;
    }

    if (window.require) {
      window.require(['vs/editor/editor.main'], () => {
        this._createEditor();
      });
    } else {
      // Fallback is immediately available
      console.log('Using fallback resilient code editor textarea');
    }
  }

  _createEditor() {
    try {
      this.editor = window.monaco.editor.create(this.container, {
        value: '// Loading mission code...',
        language: this.currentLanguage,
        theme: 'vs',
        automaticLayout: true,
        fontSize: 14,
        fontFamily: "'JetBrains Mono', 'Fira Code', Consolas, monospace",
        minimap: { enabled: false },
        lineNumbers: 'on',
        scrollBeyondLastLine: false,
        padding: { top: 12, bottom: 12 },
        tabSize: 2,
        renderLineHighlight: 'all',
        cursorBlinking: 'smooth',
        smoothScrolling: true
      });

      this.isMonacoReady = true;
      if (this.fallbackTextarea) {
        this.fallbackTextarea.style.display = 'none';
      }
    } catch (err) {
      console.warn('Monaco initialization failed, continuing with fallback:', err);
    }
  }

  setValue(code, language = 'javascript') {
    this.currentLanguage = language;
    if (this.isMonacoReady && this.editor) {
      const model = this.editor.getModel();
      if (model) {
        window.monaco.editor.setModelLanguage(model, this._normalizeLanguage(language));
      }
      this.editor.setValue(code || '');
    } else if (this.fallbackTextarea) {
      this.fallbackTextarea.value = code || '';
      this.fallbackTextarea.style.display = 'block';
    }
  }

  getValue() {
    if (this.isMonacoReady && this.editor) {
      return this.editor.getValue();
    } else if (this.fallbackTextarea) {
      return this.fallbackTextarea.value;
    }
    return '';
  }

  setLanguage(language) {
    this.currentLanguage = language;
    if (this.isMonacoReady && this.editor) {
      const model = this.editor.getModel();
      if (model) {
        window.monaco.editor.setModelLanguage(model, this._normalizeLanguage(language));
      }
    }
  }

  _normalizeLanguage(lang) {
    const l = (lang || '').toLowerCase();
    if (l === 'js' || l === 'javascript') return 'javascript';
    if (l === 'py' || l === 'python') return 'python';
    if (l === 'sql') return 'sql';
    if (l === 'c') return 'c';
    if (l === 'cpp' || l === 'c++') return 'cpp';
    if (l === 'html') return 'html';
    if (l === 'css') return 'css';
    return 'plaintext';
  }

  setTheme(themeName) {
    if (window.monaco && this.editor) {
      window.monaco.editor.setTheme(themeName === 'dark' ? 'vs-dark' : 'vs');
    }
    if (this.fallbackTextarea) {
      if (themeName === 'dark') {
        this.fallbackTextarea.style.background = '#1E293B';
        this.fallbackTextarea.style.color = '#F8FAFC';
      } else {
        this.fallbackTextarea.style.background = '#FFFFFF';
        this.fallbackTextarea.style.color = '#1B2230';
      }
    }
  }
}

window.editorManager = new EditorManager();
