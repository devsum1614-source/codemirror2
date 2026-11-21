/**
 * Code Wizard - Online Compilers & Beginner Coding Platform
 * Implements:
 * - Language Home Page (Searchable catalog of actually supported languages)
 * - Dedicated Language Pages (/languages/{id}) with lessons, labs, examples, and setup
 * - Coding Workspace with Monaco, custom input, output, and HTML preview
 * - Core Learning Rule: Student writes the code, AI acts as Socratic tutor
 * - 7-Step Pedagogical Teaching Flow in Lab Guide
 * - Progressive hints and line-number error guidance
 * - Site Owner & Admin Console with Role-Based Access Control
 */

const App = {
  state: {
    isAuthenticated: false,
    account: null,
    studentProgress: null,
    languages: [],
    currentLanguageId: 'python',
    currentLanguageDetail: null,
    challenges: [],
    currentChallenge: null,
    activeView: 'student-login', // First screen is Student Login
    activeLangFilter: 'all',
    langSearchQuery: '',
    activeFilter: 'all',
    searchQuery: '',
    activeRightTab: 'output',
    activeAdminTab: 'overview',
    activeLangTab: 'challenges',
    hintLevel: 1,
    unlockedHints: new Set([1]),
    runtimes: {},
    currentLanguage: 'python',
    recentError: null,
    aiConfigured: false,
    siteSettings: {},
    adminClasses: [],
    examplesCatalog: {},
    selectedExampleLang: 'python',
    selectedExampleId: 'py_hello',
    workspaceMode: 'challenge',
    currentExample: null,
    adminStudents: [],
    adminStudentSearchQuery: '',
    selectedAdminStudentId: null,
    adminErrorTopics: [],
    adminErrorChallengeFilter: 'all',
    adminErrorCategoryFilter: 'all',
    adminErrorIsSampleData: false,
    adminErrorStatusLabel: 'Aggregated Sandbox Data',
    courses: [],
    currentCourse: null,
    currentLessonId: null
  },

  getAccountRole(account = this.state.account) {
    const rawRole = account && typeof account.role === 'string'
      ? account.role.trim().toLowerCase()
      : '';
    if (rawRole === 'owner' || rawRole === 'teacher' || rawRole === 'student') {
      return rawRole;
    }
    return 'student';
  },

  isStaffRole(account = this.state.account) {
    const role = this.getAccountRole(account);
    return role === 'owner' || role === 'teacher';
  },

  getDefaultViewForRole(account = this.state.account) {
    return this.isStaffRole(account) ? 'admin' : 'languages';
  },

  getDefaultHashForRole(account = this.state.account) {
    return this.isStaffRole(account) ? '#admin' : '#languages';
  },

  getBasePath() {
    const path = window.location.pathname || '/';
    if (path.startsWith('/codemirror2')) {
      return '/codemirror2/';
    }
    return '/';
  },

  setRouteHash(hash) {
    const cleanHash = String(hash || '').startsWith('#') ? hash : ('#' + hash);
    if (window.history && window.history.replaceState) {
      window.history.replaceState(null, '', this.getBasePath() + cleanHash);
    } else {
      window.location.hash = cleanHash;
    }
  },

  escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, character => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[character]);
  },

  async init() {
    this.initTheme();
    this.bindEvents();
    this.bindAuthEvents();
    if (window.editorManager) {
      await window.editorManager.init();
    }
    await Promise.all([this.loadRuntimes(), this.loadSiteConfig()]);
    await this.checkAuthAndInitialize();

    // Listen for hash changes
    window.addEventListener('hashchange', () => this.handleRouting());
  },

  bindEvents() {
    // Top Navigation Links
    document.querySelectorAll('.nav-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const view = btn.dataset.view;
        if (view === 'workspace') {
          this.openCompilerForLanguage(this.state.currentLanguage || 'python');
          return;
        }
        if (view) {
          this.setRouteHash('#' + view);
        }
        this.switchView(view);
      });
    });

    // Brand click returns to role-appropriate home portal or Login
    const brandBtn = document.getElementById('brand-btn');
    if (brandBtn) {
      brandBtn.addEventListener('click', () => {
        if (this.state.isAuthenticated) {
          const targetHash = this.getDefaultHashForRole();
          const targetView = this.getDefaultViewForRole();
          this.setRouteHash(targetHash);
          this.switchView(targetView);
        } else {
          this.setRouteHash('#languages');
          this.switchView('languages');
        }
      });
    }

    // Sign Out Button
    const signoutBtn = document.getElementById('signout-btn');
    if (signoutBtn) {
      signoutBtn.addEventListener('click', () => this.handleSignOut());
    }

    // Language Search & Filter in Languages Home
    const langSearch = document.getElementById('lang-search-input');
    if (langSearch) {
      langSearch.addEventListener('input', (e) => {
        this.state.langSearchQuery = e.target.value.toLowerCase().trim();
        this.renderLanguagesGrid();
      });
    }

    document.querySelectorAll('[data-lang-filter]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-lang-filter]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.state.activeLangFilter = btn.dataset.langFilter;
        this.renderLanguagesGrid();
      });
    });

    // Language Page Sub-Navigation
    document.querySelectorAll('.lang-subtab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.switchLangSubTab(btn.dataset.langTab);
      });
    });

    // Dedicated Language Page "Start Coding Now" button
    const detailStartCodingBtn = document.getElementById('detail-start-coding-btn');
    if (detailStartCodingBtn) {
      detailStartCodingBtn.addEventListener('click', () => {
        const lang = this.state.currentLanguageId || 'python';
        this.openWorkspaceForLanguage(lang);
      });
    }

    // Catalog Filter Pills (All Labs view)
    document.querySelectorAll('.filter-btn[data-filter]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.filter-btn[data-filter]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.state.activeFilter = btn.dataset.filter;
        this.renderChallengesGrid();
      });
    });

    // Catalog Search (All Labs view)
    const searchInput = document.getElementById('challenge-search-input');
    if (searchInput) {
      searchInput.addEventListener('input', (e) => {
        this.state.searchQuery = e.target.value.toLowerCase().trim();
        this.renderChallengesGrid();
      });
    }

    // Workspace Right Panel Tabs (Run & Output, AI Coach, 7-Step Lab Guide)
    document.querySelectorAll('.right-tab-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.switchRightTab(btn.dataset.tab);
      });
    });

    // Language selector dropdown
    const langSelect = document.getElementById('editor-language-select');
    if (langSelect) {
      langSelect.addEventListener('change', (e) => {
        this.handleLanguageChange(e.target.value);
      });
    }

    // Action buttons in editor (safely guarded)
    const runBtn = document.getElementById('run-tests-btn');
    if (runBtn) runBtn.addEventListener('click', () => this.handleRunTests());

    const submitBtn = document.getElementById('submit-mission-btn');
    if (submitBtn) submitBtn.addEventListener('click', () => this.handleSubmitMission());

    const saveBtn = document.getElementById('save-code-btn');
    if (saveBtn) saveBtn.addEventListener('click', () => this.handleSaveCode());

    const resetBtn = document.getElementById('reset-code-btn');
    if (resetBtn) resetBtn.addEventListener('click', () => this.handleResetCode());

    const helpBtn = document.getElementById('help-guide-btn');
    if (helpBtn) helpBtn.addEventListener('click', () => this.handleHelpGuide());

    // Related Challenge button
    const relBtn = document.getElementById('related-challenge-btn');
    if (relBtn) {
      relBtn.addEventListener('click', () => {
        const relId = relBtn.dataset.challengeId;
        if (relId) this.openMission(relId);
      });
    }

    // Progressive Hint Stepper (1: Question, 2: Clue, 3: Explanation)
    document.querySelectorAll('.hint-step-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const level = parseInt(btn.dataset.level, 10);
        this.fetchAndDisplayHint(level);
      });
    });

    // Socratic Coach Ask button
    const coachAskBtn = document.getElementById('coach-ask-btn');
    if (coachAskBtn) coachAskBtn.addEventListener('click', () => this.handleAskCoach());

    const coachInput = document.getElementById('coach-question-input');
    if (coachInput) {
      coachInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') this.handleAskCoach();
      });
    }

    // Reset Demo button
    const resetDemoBtn = document.getElementById('reset-demo-btn');
    if (resetDemoBtn) resetDemoBtn.addEventListener('click', () => this.handleResetDemo());

    // Print Learning Report button
    const printReportBtn = document.getElementById('print-report-btn');
    if (printReportBtn) printReportBtn.addEventListener('click', () => window.print());

    // Admin Navigation Tabs
    document.querySelectorAll('.admin-nav-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.switchAdminTab(btn.dataset.adminTab);
      });
    });

    // Admin Action Buttons
    const exportBtn = document.getElementById('btn-admin-export');
    if (exportBtn) exportBtn.addEventListener('click', () => this.handleExportData());

    const createChBtn = document.getElementById('btn-admin-create-ch');
    if (createChBtn) createChBtn.addEventListener('click', () => this.openChallengeEditorModal('create'));

    const saveSettingsBtn = document.getElementById('btn-save-settings');
    if (saveSettingsBtn) saveSettingsBtn.addEventListener('click', () => this.handleSaveSettings());

    const cleanupBtn = document.getElementById('btn-cleanup-attempts');
    if (cleanupBtn) cleanupBtn.addEventListener('click', () => this.handleCleanupAttempts());

    // Challenge Editor Modal
    const modalChClose = document.getElementById('modal-ch-close-btn');
    if (modalChClose) modalChClose.addEventListener('click', () => this.closeChallengeEditorModal());

    const modalChCancel = document.getElementById('modal-ch-cancel-btn');
    if (modalChCancel) modalChCancel.addEventListener('click', () => this.closeChallengeEditorModal());

    const modalChSave = document.getElementById('modal-ch-save-btn');
    if (modalChSave) modalChSave.addEventListener('click', () => this.handleSaveChallengeForm());

    // Staff student profile editor & program assignment
    const studentClose = document.getElementById('modal-student-close-btn');
    if (studentClose) studentClose.addEventListener('click', () => this.closeStudentEditorModal());
    const studentCancel = document.getElementById('modal-student-cancel-btn');
    if (studentCancel) studentCancel.addEventListener('click', () => this.closeStudentEditorModal());
    const studentSave = document.getElementById('modal-student-save-btn');
    if (studentSave) studentSave.addEventListener('click', () => this.handleSaveStudentProfile());

    const assignProgBtn = document.getElementById('admin-assign-program-btn');
    if (assignProgBtn) assignProgBtn.addEventListener('click', () => this.handleAssignStudentProgram());

    // Code Examples Library controls
    const exLangSelect = document.getElementById('examples-language-select');
    if (exLangSelect) {
      exLangSelect.addEventListener('change', (e) => this.handleExampleLanguageSelect(e.target.value));
    }
    const exItemSelect = document.getElementById('examples-item-select');
    if (exItemSelect) {
      exItemSelect.addEventListener('change', (e) => this.handleExampleItemSelect(e.target.value));
    }
    const runExBtn = document.getElementById('run-example-btn');
    if (runExBtn) {
      runExBtn.addEventListener('click', () => this.handleRunExample());
    }
    const loadExBtn = document.getElementById('load-example-editor-btn');
    if (loadExBtn) {
      loadExBtn.addEventListener('click', () => this.handleLoadCurrentExampleIntoEditor());
    }

    // Workspace Example Mode banner buttons
    const backToExBtn = document.getElementById('workspace-back-to-examples-btn');
    if (backToExBtn) {
      backToExBtn.addEventListener('click', () => this.switchView('examples'));
    }
    const returnChBtn = document.getElementById('workspace-return-challenge-btn');
    if (returnChBtn) {
      returnChBtn.addEventListener('click', () => this.handleReturnToChallengeFromExample());
    }

    // Beginner courses: back to the course list
    const courseBackBtn = document.getElementById('course-back-btn');
    if (courseBackBtn) {
      courseBackBtn.addEventListener('click', () => {
        this.setRouteHash('#courses');
        this.renderCoursesView();
      });
    }

    // Programiz-style Homepage Online Compiler tiles
    document.querySelectorAll('.pz-compiler-tile[data-compiler-lang]').forEach(tile => {
      tile.addEventListener('click', () => {
        this.openCompilerForLanguage(tile.dataset.compilerLang);
      });
    });

    // Programiz-style Vertical Language Icon Rail inside Workspace
    document.querySelectorAll('.pz-rail-btn[data-rail-lang]').forEach(btn => {
      btn.addEventListener('click', () => {
        this.openCompilerForLanguage(btn.dataset.railLang);
      });
    });

    // Compiler toolbar actions
    const clearCodeBtn = document.getElementById('compiler-clear-code-btn');
    if (clearCodeBtn) {
      clearCodeBtn.addEventListener('click', () => {
        if (window.editorManager) window.editorManager.setValue('', this.state.currentLanguage || 'python');
        this.hideErrorDetective();
      });
    }
    const clearOutBtn = document.getElementById('compiler-clear-output-btn');
    if (clearOutBtn) {
      clearOutBtn.addEventListener('click', () => {
        const container = document.getElementById('test-results-container');
        const summary = document.getElementById('test-summary-box');
        if (summary) summary.style.display = 'none';
        if (container) {
          container.innerHTML = '<div class="pz-empty-output">Output cleared. Click <strong>Run ▶</strong> to run your code.</div>';
        }
        this.hideErrorDetective();
      });
    }
    const copyCodeBtn = document.getElementById('compiler-copy-btn');
    if (copyCodeBtn) {
      copyCodeBtn.addEventListener('click', () => {
        const code = window.editorManager ? window.editorManager.getValue() : '';
        this.copyCourseCode(code, copyCodeBtn);
      });
    }
    const downloadCodeBtn = document.getElementById('compiler-download-btn');
    if (downloadCodeBtn) {
      downloadCodeBtn.addEventListener('click', () => this.handleDownloadCode());
    }
    const compilerThemeBtn = document.getElementById('compiler-theme-btn');
    if (compilerThemeBtn) {
      compilerThemeBtn.addEventListener('click', () => this.toggleTheme());
    }

    // Error Detective buttons
    const edHintBtn = document.getElementById('ed-btn-hint');
    if (edHintBtn) edHintBtn.addEventListener('click', () => this.handleErrorDetectiveAction('hint'));
    const edExplainBtn = document.getElementById('ed-btn-explain');
    if (edExplainBtn) edExplainBtn.addEventListener('click', () => this.handleErrorDetectiveAction('explain'));
    const edFixBtn = document.getElementById('ed-btn-fix');
    if (edFixBtn) edFixBtn.addEventListener('click', () => this.handleErrorDetectiveAction('fix'));
    const edApplyBtn = document.getElementById('ed-apply-fix-btn');
    if (edApplyBtn) edApplyBtn.addEventListener('click', () => this.applyErrorDetectiveFix());
    const edCancelBtn = document.getElementById('ed-cancel-fix-btn');
    if (edCancelBtn) edCancelBtn.addEventListener('click', () => this.cancelErrorDetectiveFix());
    const edLineBtn = document.getElementById('ed-line-jump-btn');
    if (edLineBtn) {
      edLineBtn.addEventListener('click', () => {
        const lineNum = parseInt(edLineBtn.dataset.line || '0', 10);
        if (lineNum && window.editorManager && window.editorManager.revealLine) {
          window.editorManager.revealLine(lineNum);
        }
      });
    }

    // Draggable vertical resizer between editor and output
    this.initCompilerResizer();

    // Ctrl+Enter shortcut to run code in Workspace
    document.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && this.state.activeView === 'workspace') {
        const runBtn = document.getElementById('run-tests-btn');
        if (runBtn && !runBtn.disabled) {
          e.preventDefault();
          this.handleRunTests();
        }
      }
    });

    // Admin Students Directory search input
    const adminStudentSearch = document.getElementById('admin-student-search-input');
    if (adminStudentSearch) {
      adminStudentSearch.addEventListener('input', (e) => {
        this.state.adminStudentSearchQuery = e.target.value.trim();
        this.renderAdminStudents(this.state.adminStudentSearchQuery);
      });
    }

    // Admin Common Student Error Topics filter controls
    const errChallengeFilter = document.getElementById('admin-error-challenge-filter');
    if (errChallengeFilter) {
      errChallengeFilter.addEventListener('change', (e) => {
        this.state.adminErrorChallengeFilter = e.target.value;
        this.renderAdminErrorTopicsList();
      });
    }
    const errCategoryFilter = document.getElementById('admin-error-category-filter');
    if (errCategoryFilter) {
      errCategoryFilter.addEventListener('change', (e) => {
        this.state.adminErrorCategoryFilter = e.target.value;
        this.renderAdminErrorTopicsList();
      });
    }
  },

  isValidEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(String(value || '').trim());
  },

  setFieldError(inputEl, errorEl, message) {
    if (inputEl) {
      inputEl.setAttribute('aria-invalid', 'true');
    }
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.hidden = false;
    }
  },

  clearFieldError(inputEl, errorEl) {
    if (inputEl) {
      inputEl.setAttribute('aria-invalid', 'false');
    }
    if (errorEl) {
      errorEl.textContent = '';
      errorEl.hidden = true;
    }
  },

  setupPasswordToggle(btnId, inputId) {
    const btn = document.getElementById(btnId);
    const input = document.getElementById(inputId);
    if (!btn || !input) return;

    btn.addEventListener('click', () => {
      const isPassword = input.type === 'password';
      input.type = isPassword ? 'text' : 'password';
      btn.setAttribute('aria-pressed', String(isPassword));
      btn.setAttribute('aria-label', isPassword ? 'Hide password' : 'Show password');
      const labelSpan = btn.querySelector('.password-toggle-text');
      if (labelSpan) labelSpan.textContent = isPassword ? 'Hide' : 'Show';
      const eyeOpen = btn.querySelector('.icon-eye');
      const eyeOff = btn.querySelector('.icon-eye-off');
      if (eyeOpen) eyeOpen.hidden = isPassword;
      if (eyeOff) eyeOff.hidden = !isPassword;
    });
  },

  resetPasswordToggle(btnId, inputId) {
    const btn = document.getElementById(btnId);
    const input = document.getElementById(inputId);
    if (input) input.type = 'password';
    if (btn) {
      btn.setAttribute('aria-pressed', 'false');
      btn.setAttribute('aria-label', 'Show password');
      const labelSpan = btn.querySelector('.password-toggle-text');
      if (labelSpan) labelSpan.textContent = 'Show';
      const eyeOpen = btn.querySelector('.icon-eye');
      const eyeOff = btn.querySelector('.icon-eye-off');
      if (eyeOpen) eyeOpen.hidden = false;
      if (eyeOff) eyeOff.hidden = true;
    }
  },

  switchStudentAuthMode(mode = 'signin') {
    const tabSignInBtn = document.getElementById('tab-student-signin-btn');
    const tabSignUpBtn = document.getElementById('tab-student-signup-btn');
    const formLogin = document.getElementById('form-student-login');
    const formRegister = document.getElementById('form-student-register');
    const heading = document.getElementById('login-heading');
    const subheading = document.getElementById('login-subheading');

    if (!tabSignInBtn || !tabSignUpBtn || !formLogin || !formRegister) return;

    const isSignIn = mode === 'signin';
    tabSignInBtn.classList.toggle('active', isSignIn);
    tabSignInBtn.setAttribute('aria-selected', String(isSignIn));
    tabSignUpBtn.classList.toggle('active', !isSignIn);
    tabSignUpBtn.setAttribute('aria-selected', String(!isSignIn));

    formLogin.style.display = isSignIn ? 'block' : 'none';
    formRegister.style.display = isSignIn ? 'none' : 'block';

    if (heading) {
      heading.textContent = isSignIn ? 'Sign in to Code Wizard' : 'Create your student account';
    }
    if (subheading) {
      subheading.textContent = isSignIn
        ? 'Continue your interactive coding labs and track your skill progress.'
        : 'Register with your email address to start interactive coding labs.';
    }

    this.clearAuthAlert('student');
    this.clearAuthStatus('student');
  },

  bindAuthEvents() {
    // Auth Tab Switcher (Sign In vs Create Account)
    const tabSignInBtn = document.getElementById('tab-student-signin-btn');
    const tabSignUpBtn = document.getElementById('tab-student-signup-btn');
    const formLogin = document.getElementById('form-student-login');
    const formRegister = document.getElementById('form-student-register');

    if (tabSignInBtn && tabSignUpBtn) {
      tabSignInBtn.addEventListener('click', () => this.switchStudentAuthMode('signin'));
      tabSignUpBtn.addEventListener('click', () => this.switchStudentAuthMode('signup'));
    }

    // Show/Hide Password Toggles
    this.setupPasswordToggle('toggle-login-password', 'student-login-identifier' ? 'student-login-password' : '');
    this.setupPasswordToggle('toggle-reg-password', 'student-reg-password');
    this.setupPasswordToggle('toggle-admin-password', 'admin-login-password');

    // Real-time Field Error Clearing & Blur Validation for Student Sign In
    const loginEmailInput = document.getElementById('student-login-identifier');
    const loginEmailError = document.getElementById('login-email-error');
    const loginPwdInput = document.getElementById('student-login-password');
    const loginPwdError = document.getElementById('login-password-error');

    if (loginEmailInput) {
      loginEmailInput.addEventListener('input', () => {
        const val = loginEmailInput.value.trim();
        if (val && this.isValidEmail(val)) {
          this.clearFieldError(loginEmailInput, loginEmailError);
        }
      });
      loginEmailInput.addEventListener('blur', () => {
        const val = loginEmailInput.value.trim();
        if (val && !this.isValidEmail(val)) {
          this.setFieldError(loginEmailInput, loginEmailError, 'Please enter a valid email address (for example, name@example.com).');
        }
      });
    }

    if (loginPwdInput) {
      loginPwdInput.addEventListener('input', () => {
        if (loginPwdInput.value) {
          this.clearFieldError(loginPwdInput, loginPwdError);
        }
      });
    }

    // Real-time Field Error Clearing & Blur Validation for Staff Sign In
    const adminEmailInput = document.getElementById('admin-login-identifier');
    const adminEmailError = document.getElementById('admin-email-error');
    const adminPwdInput = document.getElementById('admin-login-password');
    const adminPwdError = document.getElementById('admin-password-error');

    if (adminEmailInput) {
      adminEmailInput.addEventListener('input', () => {
        const val = adminEmailInput.value.trim();
        if (val && this.isValidEmail(val)) {
          this.clearFieldError(adminEmailInput, adminEmailError);
        }
      });
      adminEmailInput.addEventListener('blur', () => {
        const val = adminEmailInput.value.trim();
        if (val && !this.isValidEmail(val)) {
          this.setFieldError(adminEmailInput, adminEmailError, 'Please enter a valid staff email address (for example, instructor@campus.edu).');
        }
      });
    }
    if (adminPwdInput) {
      adminPwdInput.addEventListener('input', () => {
        if (adminPwdInput.value) {
          this.clearFieldError(adminPwdInput, adminPwdError);
        }
      });
    }

    // Student Login Form Submit
    if (formLogin) {
      formLogin.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleStudentLogin();
      });
    }

    // Student Registration Form Submit
    if (formRegister) {
      formRegister.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleStudentRegister();
      });
    }

    // Admin Login Form Submit
    const formAdminLogin = document.getElementById('form-admin-login');
    if (formAdminLogin) {
      formAdminLogin.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleAdminLogin();
      });
    }

    // Placeholder Links: Create Account, Back to Sign In, Forgot Password, Terms of Service, Privacy Policy
    const createAccountLink = document.getElementById('create-account-link');
    if (createAccountLink) {
      createAccountLink.addEventListener('click', (e) => {
        e.preventDefault();
        this.switchStudentAuthMode('signup');
        const nameInput = document.getElementById('student-reg-name');
        if (nameInput) nameInput.focus();
      });
    }

    const backToSignInLink = document.getElementById('back-to-signin-link');
    if (backToSignInLink) {
      backToSignInLink.addEventListener('click', (e) => {
        e.preventDefault();
        this.switchStudentAuthMode('signin');
        if (loginEmailInput) loginEmailInput.focus();
      });
    }

    const forgotPasswordLink = document.getElementById('forgot-password-link');
    if (forgotPasswordLink) {
      forgotPasswordLink.addEventListener('click', (e) => {
        e.preventDefault();
        this.clearAuthAlert('student');
        this.showAuthStatus(
          'student',
          'Self-service password recovery is not configured on this server. Please contact your course instructor or platform administrator to reset your password.',
          'info'
        );
      });
    }

    const adminForgotLink = document.getElementById('admin-forgot-password-link');
    if (adminForgotLink) {
      adminForgotLink.addEventListener('click', (e) => {
        e.preventDefault();
        this.clearAuthAlert('admin');
        this.showAuthStatus(
          'admin',
          'Self-service password recovery is not enabled on this server. Please contact the platform owner to reset staff credentials.',
          'info'
        );
      });
    }

    document.querySelectorAll('.auth-footer-link').forEach(link => {
      link.addEventListener('click', (e) => {
        e.preventDefault();
        const href = link.getAttribute('href') || '';
        const isAdminView = this.state.activeView === 'admin-login';
        const targetType = isAdminView ? 'admin' : 'student';
        this.clearAuthAlert(targetType);
        if (href.includes('terms')) {
          this.showAuthStatus(targetType, 'Terms of Service: Code Wizard is an educational coding workspace. Students write all code themselves with Socratic tutor guidance.', 'info');
        } else if (href.includes('privacy')) {
          this.showAuthStatus(targetType, 'Privacy Policy: Passwords are salted and hashed on the server (PBKDF2-HMAC-SHA256) and are never stored in browser storage.', 'info');
        }
      });
    });

    // Switch between Student and Admin Auth Views
    const linkToAdmin = document.getElementById('link-to-admin-login');
    if (linkToAdmin) {
      linkToAdmin.addEventListener('click', (e) => {
        e.preventDefault();
        this.clearAuthAlert('admin');
        this.clearAuthStatus('admin');
        this.clearFieldError(adminEmailInput, adminEmailError);
        this.clearFieldError(adminPwdInput, adminPwdError);
        window.location.hash = '#admin-login';
        this.switchView('admin-login');
      });
    }

    const linkToStudent = document.getElementById('link-to-student-login');
    if (linkToStudent) {
      linkToStudent.addEventListener('click', (e) => {
        e.preventDefault();
        this.clearAuthAlert('student');
        this.clearAuthStatus('student');
        this.clearFieldError(loginEmailInput, loginEmailError);
        this.clearFieldError(loginPwdInput, loginPwdError);
        window.location.hash = '#login';
        this.switchView('student-login');
      });
    }

    // Navbar Auth Buttons for Unauthenticated Visitors
    const navBtnLoginStudent = document.getElementById('nav-btn-login-student');
    if (navBtnLoginStudent) {
      navBtnLoginStudent.addEventListener('click', () => {
        window.location.hash = '#login';
        this.switchView('student-login');
      });
    }

    const navBtnLoginAdmin = document.getElementById('nav-btn-login-admin');
    if (navBtnLoginAdmin) {
      navBtnLoginAdmin.addEventListener('click', () => {
        window.location.hash = '#admin-login';
        this.switchView('admin-login');
      });
    }
  },

  clearAuthAlert(type = 'student') {
    const alertEl = document.getElementById(type === 'admin' ? 'admin-auth-alert' : 'student-auth-alert');
    if (alertEl) {
      alertEl.style.display = 'none';
      alertEl.textContent = '';
      alertEl.className = 'alert-box';
    }
  },

  showAuthAlert(type, message, isError = true) {
    const alertEl = document.getElementById(type === 'admin' ? 'admin-auth-alert' : 'student-auth-alert');
    if (alertEl) {
      alertEl.style.display = 'block';
      alertEl.textContent = message;
      alertEl.className = `alert-box ${isError ? 'error' : 'success'}`;
    }
  },

  clearAuthStatus(type = 'student') {
    const statusEl = document.getElementById(type === 'admin' ? 'admin-auth-status' : 'student-auth-status');
    if (statusEl) {
      statusEl.style.display = 'none';
      statusEl.textContent = '';
      statusEl.className = 'alert-box status-box';
    }
  },

  showAuthStatus(type, message, variant = 'info') {
    const statusEl = document.getElementById(type === 'admin' ? 'admin-auth-status' : 'student-auth-status');
    if (statusEl) {
      statusEl.style.display = 'block';
      statusEl.textContent = message;
      statusEl.className = `alert-box status-box ${variant}`;
    }
  },

  async handleStudentLogin() {
    if (this._loginInProgress) return;
    this.clearAuthAlert('student');
    this.clearAuthStatus('student');

    const form = document.getElementById('form-student-login');
    const idInput = document.getElementById('student-login-identifier');
    const emailError = document.getElementById('login-email-error');
    const pwdInput = document.getElementById('student-login-password');
    const pwdError = document.getElementById('login-password-error');
    const rememberInput = document.getElementById('login-remember-me');
    const btn = document.getElementById('btn-submit-student-login');
    const spinner = document.getElementById('login-btn-spinner');
    const btnText = document.getElementById('login-btn-text');

    const email = idInput ? idInput.value.trim() : '';
    const password = pwdInput ? pwdInput.value : '';
    const rememberMe = Boolean(rememberInput && rememberInput.checked);

    let firstInvalid = null;

    if (!email) {
      this.setFieldError(idInput, emailError, 'Email address is required.');
      firstInvalid = firstInvalid || idInput;
    } else if (!this.isValidEmail(email)) {
      this.setFieldError(idInput, emailError, 'Please enter a valid email address (for example, name@example.com).');
      firstInvalid = firstInvalid || idInput;
    } else {
      this.clearFieldError(idInput, emailError);
    }

    if (!password) {
      this.setFieldError(pwdInput, pwdError, 'Password is required.');
      firstInvalid = firstInvalid || pwdInput;
    } else {
      this.clearFieldError(pwdInput, pwdError);
    }

    if (firstInvalid) {
      this.showAuthAlert('student', 'Please enter a valid email address and password.');
      firstInvalid.focus();
      return;
    }

    this._loginInProgress = true;
    if (form) form.setAttribute('aria-busy', 'true');
    if (btn) {
      btn.disabled = true;
      btn.classList.remove('is-success');
      btn.classList.add('is-loading');
    }
    if (spinner) spinner.hidden = false;
    if (btnText) btnText.textContent = 'Signing in…';
    this.showAuthStatus('student', 'Signing in securely…', 'info');

    try {
      const res = await API.login(email, password, rememberMe);

      // Clear password from input and reset visibility toggle for security
      if (pwdInput) pwdInput.value = '';
      this.resetPasswordToggle('toggle-login-password', 'student-login-password');

      // Show accessible success state before transitioning
      if (spinner) spinner.hidden = true;
      if (btn) {
        btn.classList.remove('is-loading');
        btn.classList.add('is-success');
      }
      if (btnText) btnText.textContent = 'Signed in ✓';
      this.showAuthStatus('student', 'Signed in successfully! Loading your workspace…', 'success');

      this.state.isAuthenticated = true;
      this.state.account = API.sanitizeAccount(res.account);
      await this.loadInitialData();

      await new Promise(resolve => setTimeout(resolve, 600));
      this.updateNavForAuth(true);

      const targetView = this.getDefaultViewForRole(this.state.account);
      const targetHash = this.getDefaultHashForRole(this.state.account);
      this.setRouteHash(targetHash);
      this.switchView(targetView);
    } catch (_err) {
      this.clearAuthStatus('student');
      // Concise, accessible error message that never reveals whether an account exists
      this.showAuthAlert('student', 'Unable to sign in. Please check your email and password and try again.');
    } finally {
      this._loginInProgress = false;
      if (form) form.removeAttribute('aria-busy');
      if (spinner) spinner.hidden = true;
      if (btn) {
        btn.disabled = false;
        btn.classList.remove('is-loading', 'is-success');
      }
      if (btnText) btnText.textContent = 'Sign In';
    }
  },

  async handleStudentRegister() {
    this.clearAuthAlert('student');
    this.clearAuthStatus('student');

    const form = document.getElementById('form-student-register');
    const nameInput = document.getElementById('student-reg-name');
    const nameError = document.getElementById('reg-name-error');
    const emailInput = document.getElementById('student-reg-email');
    const emailError = document.getElementById('reg-email-error');
    const pwdInput = document.getElementById('student-reg-password');
    const pwdError = document.getElementById('reg-password-error');
    const classInput = document.getElementById('student-reg-class');
    const btn = document.getElementById('btn-submit-student-register');
    const spinner = document.getElementById('reg-btn-spinner');
    const btnText = document.getElementById('reg-btn-text');

    const name = nameInput ? nameInput.value.trim() : '';
    const email = emailInput ? emailInput.value.trim() : '';
    const password = pwdInput ? pwdInput.value : '';
    const classId = classInput ? classInput.value.trim() : null;

    let firstInvalid = null;

    if (!name || name.length < 2) {
      this.setFieldError(nameInput, nameError, 'Please enter your name (at least 2 characters).');
      firstInvalid = firstInvalid || nameInput;
    } else {
      this.clearFieldError(nameInput, nameError);
    }

    if (!email) {
      this.setFieldError(emailInput, emailError, 'Email address is required.');
      firstInvalid = firstInvalid || emailInput;
    } else if (!this.isValidEmail(email)) {
      this.setFieldError(emailInput, emailError, 'Please enter a valid email address (for example, name@example.com).');
      firstInvalid = firstInvalid || emailInput;
    } else {
      this.clearFieldError(emailInput, emailError);
    }

    if (!password) {
      this.setFieldError(pwdInput, pwdError, 'Password is required.');
      firstInvalid = firstInvalid || pwdInput;
    } else if (password.length < 6) {
      this.setFieldError(pwdInput, pwdError, 'Password must be at least 6 characters long.');
      firstInvalid = firstInvalid || pwdInput;
    } else {
      this.clearFieldError(pwdInput, pwdError);
    }

    if (firstInvalid) {
      this.showAuthAlert('student', 'Please complete all required fields with valid information.');
      firstInvalid.focus();
      return;
    }

    if (form) form.setAttribute('aria-busy', 'true');
    if (btn) {
      btn.disabled = true;
      btn.classList.add('is-loading');
    }
    if (spinner) spinner.hidden = false;
    if (btnText) btnText.textContent = 'Creating account…';
    this.showAuthStatus('student', 'Creating your account securely…', 'info');

    try {
      const res = await API.registerStudent(name, email, password, classId);
      if (pwdInput) pwdInput.value = '';
      this.resetPasswordToggle('toggle-reg-password', 'student-reg-password');

      if (spinner) spinner.hidden = true;
      if (btn) {
        btn.classList.remove('is-loading');
        btn.classList.add('is-success');
      }
      if (btnText) btnText.textContent = 'Account created ✓';
      this.showAuthStatus('student', 'Account created! Redirecting to your learning workspace…', 'success');

      this.state.isAuthenticated = true;
      this.state.account = API.sanitizeAccount(res.account);
      await this.loadInitialData();
      await new Promise(resolve => setTimeout(resolve, 600));
      this.updateNavForAuth(true);
      const targetView = this.getDefaultViewForRole(this.state.account);
      const targetHash = this.getDefaultHashForRole(this.state.account);
      this.setRouteHash(targetHash);
      this.switchView(targetView);
    } catch (_err) {
      this.clearAuthStatus('student');
      this.showAuthAlert('student', 'Unable to complete registration. Please check your details and try again.');
    } finally {
      if (form) form.removeAttribute('aria-busy');
      if (spinner) spinner.hidden = true;
      if (btn) {
        btn.disabled = false;
        btn.classList.remove('is-loading', 'is-success');
      }
      if (btnText) btnText.textContent = 'Create Account';
    }
  },

  async handleAdminLogin() {
    if (this._adminLoginInProgress) return;
    this.clearAuthAlert('admin');
    this.clearAuthStatus('admin');

    const form = document.getElementById('form-admin-login');
    const idInput = document.getElementById('admin-login-identifier');
    const emailError = document.getElementById('admin-email-error');
    const pwdInput = document.getElementById('admin-login-password');
    const pwdError = document.getElementById('admin-password-error');
    const rememberInput = document.getElementById('admin-remember-me');
    const btn = document.getElementById('btn-submit-admin-login');
    const spinner = document.getElementById('admin-btn-spinner');
    const btnText = document.getElementById('admin-btn-text');

    const email = idInput ? idInput.value.trim() : '';
    const password = pwdInput ? pwdInput.value : '';
    const rememberMe = Boolean(rememberInput && rememberInput.checked);

    let firstInvalid = null;

    if (!email) {
      this.setFieldError(idInput, emailError, 'Staff email address is required.');
      firstInvalid = firstInvalid || idInput;
    } else if (!this.isValidEmail(email)) {
      this.setFieldError(idInput, emailError, 'Please enter a valid staff email address (for example, instructor@campus.edu).');
      firstInvalid = firstInvalid || idInput;
    } else {
      this.clearFieldError(idInput, emailError);
    }

    if (!password) {
      this.setFieldError(pwdInput, pwdError, 'Password is required.');
      firstInvalid = firstInvalid || pwdInput;
    } else {
      this.clearFieldError(pwdInput, pwdError);
    }

    if (firstInvalid) {
      this.showAuthAlert('admin', 'Please enter a valid staff email address and password.');
      firstInvalid.focus();
      return;
    }

    this._adminLoginInProgress = true;
    if (form) form.setAttribute('aria-busy', 'true');
    if (btn) {
      btn.disabled = true;
      btn.classList.remove('is-success');
      btn.classList.add('is-loading');
    }
    if (spinner) spinner.hidden = false;
    if (btnText) btnText.textContent = 'Signing in…';
    this.showAuthStatus('admin', 'Signing in securely…', 'info');

    try {
      const res = await API.login(email, password, rememberMe);
      if (pwdInput) pwdInput.value = '';
      this.resetPasswordToggle('toggle-admin-password', 'admin-login-password');

      if (spinner) spinner.hidden = true;
      if (btn) {
        btn.classList.remove('is-loading');
        btn.classList.add('is-success');
      }
      if (btnText) btnText.textContent = 'Signed in ✓';
      this.showAuthStatus('admin', 'Signed in successfully! Loading console…', 'success');

      this.state.isAuthenticated = true;
      this.state.account = API.sanitizeAccount(res.account);
      await this.loadInitialData();
      await new Promise(resolve => setTimeout(resolve, 600));
      this.updateNavForAuth(true);

      const targetView = this.getDefaultViewForRole(this.state.account);
      const targetHash = this.getDefaultHashForRole(this.state.account);
      this.setRouteHash(targetHash);
      this.switchView(targetView);
    } catch (_err) {
      this.clearAuthStatus('admin');
      this.showAuthAlert('admin', 'Unable to sign in. Please check your email and password and try again.');
    } finally {
      this._adminLoginInProgress = false;
      if (form) form.removeAttribute('aria-busy');
      if (spinner) spinner.hidden = true;
      if (btn) {
        btn.disabled = false;
        btn.classList.remove('is-loading', 'is-success');
      }
      if (btnText) btnText.textContent = 'Sign In';
    }
  },

  async handleSignOut() {
    try {
      await API.logout();
    } catch (e) {
      console.warn('Sign out notice:', e);
    }
    this.state.isAuthenticated = false;
    this.state.account = null;
    this.state.studentProgress = null;
    this.state.selectedAdminStudentId = null;
    const adminSec = document.getElementById('view-admin');
    if (adminSec) {
      adminSec.classList.remove('active');
      adminSec.hidden = true;
    }
    this.updateNavForAuth(false);
    this.setRouteHash('#login');
    this.switchView('student-login');
  },

  async checkAuthAndInitialize() {
    try {
      const res = await API.getMyProfile();
      if (res && res.account) {
        this.state.isAuthenticated = true;
        this.state.account = API.sanitizeAccount(res.account);
        await this.loadInitialData();
        this.updateNavForAuth(true);
        this.handleRouting();
        return;
      }
    } catch (e) {
      // Unauthenticated visitor — can browse Programiz-style homepage, courses, examples & compilers
      API.clearSession();
    }

    this.state.isAuthenticated = false;
    this.state.account = null;
    this.updateNavForAuth(false);
    await Promise.all([this.loadLanguages(), this.loadExamplesCatalog(), this.loadPublicChallenges()]);
    this.handleRouting();
  },

  async loadPublicChallenges() {
    try {
      const data = await API.getChallenges();
      this.state.challenges = data.challenges || [];
    } catch (e) {
      this.state.challenges = [];
    }
  },

  updateNavForAuth(isAuth) {
    const mainNav = document.getElementById('main-nav-container');
    const navUser = document.getElementById('nav-user-container');
    const authBtns = document.getElementById('nav-auth-buttons');
    const authOnlyItems = document.querySelectorAll('.auth-only-nav-item');
    const publicItems = document.querySelectorAll('.public-nav-item');
    const navAdminLi = document.getElementById('nav-admin-li');

    if (isAuth) {
      if (mainNav) mainNav.style.display = 'block';
      if (navUser) navUser.style.display = 'flex';
      if (authBtns) authBtns.style.display = 'none';
      this.updateRoleBasedNavigation();
      this.renderUserBadge();
    } else {
      if (mainNav) mainNav.style.display = 'block';
      if (navUser) navUser.style.display = 'none';
      if (authBtns) authBtns.style.display = 'flex';
      publicItems.forEach(item => {
        item.style.display = 'block';
        item.hidden = false;
      });
      authOnlyItems.forEach(item => {
        item.style.display = 'none';
        item.hidden = true;
      });
      if (navAdminLi) {
        navAdminLi.style.display = 'none';
        navAdminLi.hidden = true;
      }
    }
  },

  handleRouting() {
    const path = window.location.pathname;
    const hash = window.location.hash.replace('#', '');

    // Authenticated staff (owner / teacher) ALWAYS route to Admin Console
    if (this.state.isAuthenticated && this.state.account && this.isStaffRole(this.state.account)) {
      if (window.location.hash !== '#admin') {
        this.setRouteHash('#admin');
      }
      this.switchView('admin');
      return;
    }

    // Unauthenticated visitors: allow login views + public learning views (Home, Courses, Compilers, Examples, Labs)
    if (!this.state.isAuthenticated || !this.state.account) {
      if (hash === 'admin-login' || hash === 'admin' || path.startsWith('/admin')) {
        this.switchView('admin-login');
        return;
      }
      if (hash === 'login' || hash === 'student-login' || path === '/login' || hash === 'dashboard' || hash === 'report') {
        this.switchView('student-login');
        return;
      }
    } else {
      // Authenticated student: block admin/login routes and redirect to Student Portal
      if (
        hash === 'login' ||
        hash === 'student-login' ||
        hash === 'admin-login' ||
        hash === 'admin' ||
        path.startsWith('/admin') ||
        path.includes('/admin')
      ) {
        const targetView = this.getDefaultViewForRole(this.state.account);
        const targetHash = this.getDefaultHashForRole(this.state.account);
        this.setRouteHash(targetHash);
        this.switchView(targetView);
        return;
      }
    }

    // Direct Online Compiler route: #compiler/python, #compiler/sql, etc.
    if (hash.startsWith('compiler/')) {
      const langId = hash.split('/')[1] || 'python';
      this.openCompilerForLanguage(langId);
      return;
    }

    // Beginner courses: #courses, #courses/python, #courses/python/python_l3
    if (hash === 'courses' || hash.startsWith('courses/')) {
      const parts = hash.split('/').filter(Boolean);
      this.switchView('courses');
      if (parts[1]) this.openCourse(parts[1], parts[2] || null);
      return;
    }

    // Check for language route e.g. /languages/python or #languages/python or #languages/python/lessons
    if (path.startsWith('/languages/') && path.length > 11) {
      const parts = path.split('/').filter(Boolean);
      const langId = parts[1];
      const subTab = parts[2] || null;
      this.openLanguagePage(langId, subTab);
      return;
    }

    if (hash.startsWith('languages/') || hash.startsWith('language-')) {
      const cleaned = hash.replace('languages/', '').replace('language-', '');
      const parts = cleaned.split('/').filter(Boolean);
      const langId = parts[0];
      const subTab = parts[1] || null;
      this.openLanguagePage(langId, subTab);
      return;
    }

    // Check for challenge route e.g. #challenge-ch_py_filter
    if (hash.startsWith('challenge-') || hash.startsWith('mission-')) {
      const chId = hash.replace('challenge-', '').replace('mission-', '');
      this.openMission(chId);
      return;
    }

    if (hash === 'languages' || path === '/languages' || path.endsWith('/languages')) {
      this.switchView('languages');
    } else if (hash === 'dashboard') {
      this.switchView('dashboard');
    } else if (hash === 'examples' || hash.startsWith('examples/')) {
      const exLang = hash.startsWith('examples/') ? hash.split('/')[1] : null;
      if (exLang) this.state.selectedExampleLang = exLang;
      this.switchView('examples');
    } else if (hash === 'missions') {
      this.switchView('missions');
    } else if (hash === 'workspace') {
      this.switchView('workspace');
    } else if (hash === 'skillproof') {
      this.switchView('skillproof');
    } else if (hash === 'report') {
      this.switchView('report');
    } else {
      const targetView = this.getDefaultViewForRole(this.state.account);
      const targetHash = this.getDefaultHashForRole(this.state.account);
      this.setRouteHash(targetHash);
      this.switchView(targetView);
    }
  },

  // ==========================================================
  // BEGINNER COURSES (student portal)
  // Catalog -> course with ordered lessons -> lesson (explanation, example, exercise).
  // Lesson content is public; progress is stored per student on the server.
  // ==========================================================
  courseStatusLabel(status) {
    return { not_started: 'Not started', in_progress: 'In progress', completed: 'Completed' }[status] || 'Not started';
  },

  courseStatusPill(status) {
    const safe = ['not_started', 'in_progress', 'completed'].includes(status) ? status : 'not_started';
    return `<span class="lesson-status ${safe}">${this.courseStatusLabel(safe)}</span>`;
  },

  showCoursesNotice(message) {
    const el = document.getElementById('courses-notice');
    if (!el) return;
    el.textContent = message || '';
    el.hidden = !message;
  },

  async renderCoursesView() {
    const catalog = document.getElementById('courses-catalog');
    const detail = document.getElementById('course-detail');
    const grid = document.getElementById('courses-grid');
    if (!catalog || !detail || !grid) return;

    detail.hidden = true;
    catalog.hidden = false;
    this.state.currentCourse = null;
    this.state.currentLessonId = null;
    grid.innerHTML = '';
    this.showCoursesNotice('');

    try {
      const data = await API.getCourses();
      this.state.courses = data.courses || [];
      this.renderCoursesGrid();
    } catch (e) {
      this.showCoursesNotice(e.message || 'Courses could not be loaded.');
    }
  },

  renderCoursesGrid() {
    const grid = document.getElementById('courses-grid');
    if (!grid) return;
    grid.innerHTML = '';

    this.state.courses.forEach(c => {
      const pct = Math.max(0, Math.min(100, Number(c.percent) || 0));
      const actionLabel = c.status === 'completed' ? 'Review course' : (c.status === 'in_progress' ? 'Continue' : 'Start course');
      const card = document.createElement('div');
      card.className = 'course-card';
      card.innerHTML = `
        <div class="course-card-top">
          <span class="course-icon" aria-hidden="true">${this.escapeHtml(c.icon)}</span>
          <h3>${this.escapeHtml(c.name)}</h3>
        </div>
        <p>${this.escapeHtml(c.tagline)}</p>
        <div class="course-progress-bar" role="progressbar" aria-label="${this.escapeHtml(c.name)} progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${pct}">
          <div class="course-progress-fill" style="width: ${pct}%"></div>
        </div>
        <div class="course-card-footer">
          ${this.courseStatusPill(c.status)}
          <span style="font-size: 0.78rem; color: var(--text-muted);">${Number(c.completed_count) || 0} of ${Number(c.lesson_count) || 0} lessons</span>
          ${c.runnable ? '' : '<span class="lesson-status not_started" title="' + this.escapeHtml(c.note || '') + '">View only</span>'}
        </div>
        <button type="button" class="btn btn-primary">${actionLabel}</button>
      `;
      card.querySelector('button').addEventListener('click', () => this.openCourse(c.id, c.next_lesson_id));
      grid.appendChild(card);
    });
  },

  async openCourse(courseId, lessonId = null) {
    try {
      const course = await API.getCourse(courseId);
      this.state.currentCourse = course;

      const catalog = document.getElementById('courses-catalog');
      const detail = document.getElementById('course-detail');
      if (catalog) catalog.hidden = true;
      if (detail) detail.hidden = false;

      const requested = lessonId && course.lessons.some(l => l.id === lessonId) ? lessonId : null;
      const target = requested || course.next_lesson_id || course.lessons[0].id;
      this.renderCourseDetail(target);
      this.setRouteHash(`#courses/${course.id}/${target}`);
    } catch (e) {
      const catalog = document.getElementById('courses-catalog');
      const detail = document.getElementById('course-detail');
      if (detail) detail.hidden = true;
      if (catalog) catalog.hidden = false;
      this.showCoursesNotice(e.message || 'This course could not be opened.');
    }
  },

  renderCourseDetail(activeLessonId) {
    const course = this.state.currentCourse;
    if (!course) return;
    this.state.currentLessonId = activeLessonId;

    const setText = (id, value) => { const el = document.getElementById(id); if (el) el.textContent = value; };
    setText('course-detail-icon', course.icon);
    setText('course-detail-name', course.name);
    setText('course-detail-tagline', course.tagline);

    const done = course.lessons.filter(l => l.status === 'completed').length;
    const pct = course.lessons.length ? Math.round((100 * done) / course.lessons.length) : 0;
    setText('course-progress-text', `${done} of ${course.lessons.length} lessons completed (${pct}%)`);
    const fill = document.getElementById('course-progress-fill');
    if (fill) fill.style.width = `${pct}%`;

    const note = document.getElementById('course-runtime-note');
    if (note) {
      note.textContent = course.runnable ? '' : (course.note || '');
      note.hidden = course.runnable || !course.note;
    }

    const list = document.getElementById('course-lesson-list');
    if (list) {
      list.innerHTML = '';
      course.lessons.forEach(lesson => {
        const li = document.createElement('li');
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'course-lesson-item' + (lesson.id === activeLessonId ? ' active' : '');
        if (lesson.id === activeLessonId) btn.setAttribute('aria-current', 'step');
        const dotContent = lesson.status === 'completed' ? '&#10003;' : String(lesson.order);
        btn.innerHTML = `
          <span class="lesson-dot ${this.escapeHtml(lesson.status)}" aria-hidden="true">${dotContent}</span>
          <span>${this.escapeHtml(lesson.title)}<span class="sr-only"> (${this.courseStatusLabel(lesson.status)})</span></span>
        `;
        btn.addEventListener('click', () => {
          this.renderCourseDetail(lesson.id);
          this.setRouteHash(`#courses/${course.id}/${lesson.id}`);
        });
        li.appendChild(btn);
        list.appendChild(li);
      });
    }

    const lesson = course.lessons.find(l => l.id === activeLessonId) || course.lessons[0];
    this.renderCourseLesson(lesson);
  },

  renderCourseLesson(lesson) {
    const course = this.state.currentCourse;
    const pane = document.getElementById('course-lesson-pane');
    if (!course || !pane) return;

    const index = course.lessons.findIndex(l => l.id === lesson.id);
    const prev = index > 0 ? course.lessons[index - 1] : null;
    const next = index < course.lessons.length - 1 ? course.lessons[index + 1] : null;
    const isWeb = course.id === 'html';
    const canRun = Boolean(course.language) && Boolean(course.runnable);

    let statusButtons = '';
    if (lesson.status === 'not_started') {
      statusButtons = `
        <button type="button" class="btn btn-secondary" data-set-status="in_progress">Start lesson</button>
        <button type="button" class="btn btn-primary" data-set-status="completed">Mark as completed</button>`;
    } else if (lesson.status === 'in_progress') {
      statusButtons = `
        <button type="button" class="btn btn-primary" data-set-status="completed">Mark as completed</button>
        <button type="button" class="btn btn-secondary" data-set-status="not_started">Reset</button>`;
    } else {
      statusButtons = `<button type="button" class="btn btn-secondary" data-set-status="not_started">Mark as not completed</button>`;
    }

    pane.innerHTML = `
      <h3>${this.escapeHtml(lesson.title)}</h3>
      <div class="course-lesson-meta">
        <span>Lesson ${lesson.order} of ${course.lessons.length}</span>
        ${this.courseStatusPill(lesson.status)}
      </div>
      <p><strong>${this.escapeHtml(lesson.summary)}</strong></p>
      <p>${this.escapeHtml(lesson.explanation)}</p>

      <div class="course-section-label">Example</div>
      <div class="code-snippet-box">${this.escapeHtml(lesson.example)}</div>
      <div class="course-section-label">${isWeb ? 'What you will see' : 'What it prints'}</div>
      <pre class="example-output-pre course-expected">${this.escapeHtml(lesson.expected_output)}</pre>
      ${lesson.sample_input ? `<p style="margin-top: 8px; font-size: 0.82rem;">When you run it in the Workspace, type <code>${this.escapeHtml(lesson.sample_input)}</code> in the Custom Input box first.</p>` : ''}
      <div class="course-actions">
        ${canRun ? '<button type="button" class="btn btn-primary" id="course-try-example">Try it in the Workspace</button>' : ''}
        <button type="button" class="btn btn-secondary" id="course-copy-example">Copy example</button>
      </div>

      <div class="course-section-label">Your turn</div>
      <div class="course-exercise">
        <p>${this.escapeHtml(lesson.exercise.prompt)}</p>
        <div class="course-actions" style="margin-top: 0;">
          ${canRun ? '<button type="button" class="btn btn-primary" id="course-try-exercise">Open the exercise</button>' : ''}
          <button type="button" class="btn btn-secondary" id="course-copy-exercise">Copy starter code</button>
        </div>
      </div>

      <div class="course-section-label">Progress</div>
      <div class="course-actions" id="course-status-actions">${statusButtons}</div>

      <div class="course-pager">
        ${prev ? '<button type="button" class="btn btn-secondary" id="course-prev">&larr; ' + this.escapeHtml(prev.title) + '</button>' : '<span></span>'}
        ${next ? '<button type="button" class="btn btn-secondary" id="course-next">' + this.escapeHtml(next.title) + ' &rarr;</button>' : '<span></span>'}
      </div>
    `;

    const goTo = (target) => {
      this.renderCourseDetail(target.id);
      this.setRouteHash(`#courses/${course.id}/${target.id}`);
      window.scrollTo({ top: 0, behavior: 'smooth' });
    };
    const prevBtn = pane.querySelector('#course-prev');
    const nextBtn = pane.querySelector('#course-next');
    if (prevBtn) prevBtn.addEventListener('click', () => goTo(prev));
    if (nextBtn) nextBtn.addEventListener('click', () => goTo(next));

    pane.querySelectorAll('[data-set-status]').forEach(btn => {
      btn.addEventListener('click', () => this.setLessonStatus(lesson.id, btn.dataset.setStatus));
    });

    const tryExample = pane.querySelector('#course-try-example');
    if (tryExample) tryExample.addEventListener('click', () => this.openCourseLessonInWorkspace(lesson, 'example'));
    const tryExercise = pane.querySelector('#course-try-exercise');
    if (tryExercise) tryExercise.addEventListener('click', () => this.openCourseLessonInWorkspace(lesson, 'exercise'));
    const copyExample = pane.querySelector('#course-copy-example');
    if (copyExample) copyExample.addEventListener('click', () => this.copyCourseCode(lesson.example, copyExample));
    const copyExercise = pane.querySelector('#course-copy-exercise');
    if (copyExercise) copyExercise.addEventListener('click', () => this.copyCourseCode(lesson.exercise.starter, copyExercise));
  },

  async copyCourseCode(text, button) {
    const original = button.textContent;
    try {
      await navigator.clipboard.writeText(text);
      button.textContent = 'Copied!';
    } catch (e) {
      button.textContent = 'Copy failed: select the code and copy it manually';
    }
    setTimeout(() => { button.textContent = original; }, 1800);
  },

  async setLessonStatus(lessonId, status) {
    const course = this.state.currentCourse;
    if (!course) return;
    try {
      const res = await API.setLessonProgress(course.id, lessonId, status);
      const lesson = course.lessons.find(l => l.id === lessonId);
      if (lesson) lesson.status = res.status;
      if (res.course) {
        course.status = res.course.status;
        course.completed_count = res.course.completed_count;
        course.percent = res.course.percent;
        course.next_lesson_id = res.course.next_lesson_id;
      }
      this.renderCourseDetail(lessonId);
    } catch (e) {
      alert(`Your progress could not be saved: ${e.message}`);
    }
  },

  openCourseLessonInWorkspace(lesson, kind) {
    const course = this.state.currentCourse;
    if (!course || !course.language) return;
    const isExercise = kind === 'exercise';
    const code = isExercise ? lesson.exercise.starter : lesson.example;
    const ext = course.file_ext || '';
    const filename = course.language === 'java' ? 'Main.java' : `lesson_${lesson.order}${ext}`;
    const exampleId = `${lesson.id}_${kind}`;

    this.handleLoadExampleIntoEditor(course.language, {
      id: exampleId,
      title: `${lesson.title}${isExercise ? ' (exercise)' : ''}`,
      category: `${course.name} course`,
      explanation: isExercise ? lesson.exercise.prompt : lesson.summary,
      filename,
      code,
      expected_output: isExercise ? '' : lesson.expected_output
    });

    // The loader asks for confirmation if the editor holds other code; only continue if it opened.
    if (this.state.workspaceMode !== 'example' || !this.state.currentExample || this.state.currentExample.id !== exampleId) {
      return;
    }

    const stdinEl = document.getElementById('custom-input-text');
    if (stdinEl) stdinEl.value = lesson.sample_input || '';

    // Opening the workspace for a lesson you have not started counts as starting it.
    if (lesson.status === 'not_started') {
      API.setLessonProgress(course.id, lesson.id, 'in_progress')
        .then(res => {
          lesson.status = res.status;
          if (res.course) {
            course.status = res.course.status;
            course.completed_count = res.course.completed_count;
            course.percent = res.course.percent;
            course.next_lesson_id = res.course.next_lesson_id;
          }
        })
        .catch(() => { /* progress is optional here; the lesson still opens */ });
    }
  },

  async loadRuntimes() {
    try {
      const data = await API.getRuntimes();
      this.state.runtimes = data.runtimes || {};
      this.renderRuntimeBar();
    } catch (e) {
      console.warn('Could not load toolchains:', e);
    }
  },

  async loadAIStatus() {
    const status = document.getElementById('coach-service-status');
    try {
      const data = await API.getAIStatus();
      this.state.aiConfigured = Boolean(data.configured);
      if (status) {
        status.textContent = data.configured
          ? 'Live Gemini Coach is ready.'
          : 'Built-in hints are active. Live AI needs a server-side GEMINI_API_KEY.';
        status.style.color = data.configured ? 'var(--teal-success)' : 'var(--amber-hint)';
      }
    } catch (error) {
      if (status) {
        status.textContent = 'AI status could not be loaded. Built-in hints remain available.';
        status.style.color = 'var(--amber-hint)';
      }
    }
  },

  async loadSiteConfig() {
    try {
      const data = await API.getSiteConfig();
      this.applySiteSettings(data.settings || {});
    } catch (error) {
      console.warn('Could not load public site settings:', error);
    }
  },

  applySiteSettings(settings) {
    this.state.siteSettings = { ...this.state.siteSettings, ...settings };
    const root = document.documentElement;
    const variables = {
      theme_primary: '--indigo-primary',
      theme_background: '--bg-primary',
      theme_surface: '--bg-surface',
      theme_text: '--text-primary'
    };
    Object.entries(variables).forEach(([key, cssVar]) => {
      const value = settings[key];
      if (/^#[0-9a-f]{6}$/i.test(value || '')) root.style.setProperty(cssVar, value);
    });
    if (settings.platform_name) document.title = settings.platform_name;
  },

  renderRuntimeBar() {
    const rts = this.state.runtimes;
    const pyEl = document.getElementById('rt-py');
    const sqlEl = document.getElementById('rt-sql');
    const htmlEl = document.getElementById('rt-html');
    const jsEl = document.getElementById('rt-js');
    const javaEl = document.getElementById('rt-java');
    const cEl = document.getElementById('rt-c');

    if (pyEl && rts.python) {
      pyEl.innerHTML = `<span class="status-dot active"></span> <span>Python ${rts.python.version || '3.x'} (Active)</span>`;
    }
    if (sqlEl && rts.sql) {
      sqlEl.innerHTML = `<span class="status-dot active"></span> <span>SQLite ${rts.sql.version || '3.x'} (Active)</span>`;
    }
    if (htmlEl && rts.html) {
      htmlEl.innerHTML = `<span class="status-dot active"></span> <span>HTML/CSS (Ready)</span>`;
    }
    if (jsEl && rts.javascript) {
      const isAvail = rts.javascript.available;
      jsEl.innerHTML = `<span class="status-dot ${isAvail ? 'active' : 'inactive'}"></span> <span>Node.js (${isAvail ? 'Active' : 'Not installed'})</span>`;
    }
    if (javaEl && rts.java) {
      const isAvail = rts.java.available;
      javaEl.innerHTML = `<span class="status-dot ${isAvail ? 'active' : 'inactive'}"></span> <span>Java JDK (${isAvail ? 'Active' : 'Not installed'})</span>`;
    }
    if (cEl && rts.c) {
      const isAvail = rts.c.available;
      cEl.innerHTML = `<span class="status-dot ${isAvail ? 'active' : 'inactive'}"></span> <span>GCC / Clang (${isAvail ? 'Active' : 'Not installed'})</span>`;
    }
  },

  async loadInitialData() {
    try {
      const meResp = await API.getMyProfile();
      if (meResp && meResp.account) {
        this.state.account = API.sanitizeAccount(meResp.account);
      }

      if (this.getAccountRole() === 'student') {
        try {
          this.state.studentProgress = await API.getStudentProgress(this.state.account.id);
        } catch (e) {
          this.state.studentProgress = { total_xp: 0, level: 1, completed_count: 0, completed_challenges: [] };
        }
      } else {
        this.state.studentProgress = { total_xp: 0, level: 1, completed_count: 0, completed_challenges: [] };
      }

      this.renderUserBadge();
      this.updateRoleBasedNavigation();

      // Load languages catalog and built-in code examples library
      await Promise.all([this.loadLanguages(), this.loadExamplesCatalog()]);

      // Load challenges
      const challengesResp = await API.getChallenges();
      this.state.challenges = challengesResp.challenges || [];

      this.renderDashboard();
      this.renderChallengesGrid();
      this.renderExamplesView();
    } catch (err) {
      console.error('Error loading initial platform data:', err);
    }
  },

  updateRoleBasedNavigation() {
    const role = this.getAccountRole();
    const navAdminLi = document.getElementById('nav-admin-li');
    const navSkillproofLi = document.getElementById('nav-skillproof-li');
    const studentNavItems = document.querySelectorAll('.student-nav-item');
    const adminNavLabel = document.getElementById('admin-nav-label');
    const adminViewTitle = document.getElementById('admin-view-title');
    const adminViewSubtitle = document.getElementById('admin-view-subtitle');
    const adminSettingsTabBtn = document.getElementById('admin-settings-tab-btn');
    const viewAdminSec = document.getElementById('view-admin');

    // Keep SkillProof & Examples hidden from student navigation
    if (navSkillproofLi) {
      navSkillproofLi.style.display = 'none';
      navSkillproofLi.hidden = true;
    }
    const navExamplesLi = document.getElementById('nav-examples-li');
    if (navExamplesLi) {
      navExamplesLi.style.display = 'none';
      navExamplesLi.hidden = true;
    }

    if (role === 'owner') {
      if (navAdminLi) {
        navAdminLi.style.display = 'block';
        navAdminLi.hidden = false;
      }
      studentNavItems.forEach(item => {
        item.style.display = 'none';
        item.hidden = true;
      });
      if (viewAdminSec) viewAdminSec.hidden = false;
      if (adminNavLabel) adminNavLabel.textContent = 'Admin Console';
      if (adminViewTitle) adminViewTitle.textContent = 'Site Owner & Admin Console';
      if (adminViewSubtitle) adminViewSubtitle.textContent = 'Search students, inspect SkillProof records, and manage coding labs, classes, and platform settings.';
      if (adminSettingsTabBtn) adminSettingsTabBtn.style.display = 'inline-flex';
    } else if (role === 'teacher') {
      if (navAdminLi) {
        navAdminLi.style.display = 'block';
        navAdminLi.hidden = false;
      }
      studentNavItems.forEach(item => {
        item.style.display = 'none';
        item.hidden = true;
      });
      if (viewAdminSec) viewAdminSec.hidden = false;
      if (adminNavLabel) adminNavLabel.textContent = 'Teacher Portal';
      if (adminViewTitle) adminViewTitle.textContent = 'Instructor Class Portal';
      if (adminViewSubtitle) adminViewSubtitle.textContent = 'Search students, review student profiles and SkillProof records, and track class progress.';
      if (adminSettingsTabBtn) adminSettingsTabBtn.style.display = 'none';
    } else {
      if (navAdminLi) {
        navAdminLi.style.display = 'none';
        navAdminLi.hidden = true;
      }
      studentNavItems.forEach(item => {
        item.style.display = 'block';
        item.hidden = false;
      });
      if (viewAdminSec) {
        viewAdminSec.classList.remove('active');
        viewAdminSec.hidden = true;
      }
      if (this.state.activeView === 'admin') {
        this.switchView('languages');
      }
    }
  },

  renderUserBadge() {
    const acc = this.state.account || { display_name: 'Student', role: 'student', id: API.getAccountId() };
    const role = this.getAccountRole(acc);
    const prog = this.state.studentProgress || { total_xp: 0, level: 1, completed_count: 0, completed_challenges: [] };

    const nameEl = document.getElementById('user-name');
    if (nameEl) nameEl.textContent = acc.display_name;

    const idEl = document.getElementById('user-id-display');
    if (idEl) idEl.textContent = acc.id;

    const roleEl = document.getElementById('user-role-badge');
    if (roleEl) {
      roleEl.textContent = role.toUpperCase();
      if (role === 'owner') {
        roleEl.style.background = 'rgba(79, 70, 229, 0.15)';
        roleEl.style.color = 'var(--indigo-primary)';
      } else if (role === 'teacher') {
        roleEl.style.background = 'rgba(15, 159, 130, 0.15)';
        roleEl.style.color = 'var(--teal-success)';
      } else {
        roleEl.style.background = 'rgba(217, 119, 6, 0.15)';
        roleEl.style.color = 'var(--amber-hint)';
      }
    }

    const initialsEl = document.getElementById('user-avatar-initials');
    if (initialsEl && acc.display_name) {
      const parts = acc.display_name.split(' ');
      const initials = parts.length > 1 ? (parts[0][0] + parts[1][0]).toUpperCase() : parts[0].slice(0, 2).toUpperCase();
      initialsEl.textContent = initials;
    }

    const pts = document.getElementById('user-points');
    if (pts) pts.textContent = `${prog.total_xp || 0} XP`;
    const rdy = document.getElementById('user-readiness');
    if (rdy) rdy.textContent = `Lvl ${prog.level || 1}`;
    const comp = document.getElementById('dash-completed-count');
    if (comp) comp.textContent = prog.completed_count || 0;
    const dashRdy = document.getElementById('dash-readiness-val');
    if (dashRdy) dashRdy.textContent = `Lvl ${prog.level || 1}`;
    const dashPts = document.getElementById('dash-points-val');
    if (dashPts) dashPts.textContent = prog.total_xp || 0;
    const dashEv = document.getElementById('dash-evidence-count');
    if (dashEv) dashEv.textContent = prog.completed_count || 0;
  },

  switchView(viewName) {
    // Enforce strict role separation before activating any view
    if (viewName === 'admin') {
      if (!this.state.isAuthenticated || !this.state.account) {
        viewName = 'admin-login';
      } else if (!this.isStaffRole(this.state.account)) {
        viewName = 'languages';
        this.setRouteHash('#languages');
      }
    } else if (
      viewName !== 'student-login' &&
      viewName !== 'admin-login' &&
      this.state.isAuthenticated &&
      this.isStaffRole(this.state.account)
    ) {
      viewName = 'admin';
      this.setRouteHash('#admin');
    }

    this.state.activeView = viewName;
    const navMatchView = viewName === 'language-detail' ? 'languages' : viewName;
    document.querySelectorAll('.nav-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.view === navMatchView);
    });

    const navBtnStudent = document.getElementById('nav-btn-login-student');
    const navBtnAdmin = document.getElementById('nav-btn-login-admin');
    if (navBtnStudent && navBtnAdmin) {
      const isAdminPortal = viewName === 'admin-login';
      navBtnStudent.className = isAdminPortal ? 'btn btn-secondary' : 'btn btn-primary';
      navBtnAdmin.className = isAdminPortal ? 'btn btn-primary' : 'btn btn-secondary';
      if (isAdminPortal) {
        navBtnAdmin.setAttribute('aria-current', 'page');
        navBtnStudent.removeAttribute('aria-current');
      } else if (viewName === 'student-login') {
        navBtnStudent.setAttribute('aria-current', 'page');
        navBtnAdmin.removeAttribute('aria-current');
      }
    }

    document.querySelectorAll('.view-section').forEach(sec => {
      sec.classList.remove('active');
    });

    const viewAdminSec = document.getElementById('view-admin');
    if (viewAdminSec) {
      viewAdminSec.hidden = (viewName !== 'admin');
    }

    const target = document.getElementById(`view-${viewName}`);
    if (target) {
      target.hidden = false;
      target.classList.add('active');
    }

    if (viewName === 'languages') {
      this.renderLanguagesGrid();
    } else if (viewName === 'courses') {
      this.renderCoursesView();
    } else if (viewName === 'examples') {
      this.renderExamplesView();
    } else if (viewName === 'dashboard') {
      this.renderDashboard();
    } else if (viewName === 'skillproof') {
      this.renderSkillProof();
    } else if (viewName === 'report') {
      this.renderLearningReport();
    } else if (viewName === 'admin') {
      this.renderAdminView();
    } else if (viewName === 'missions') {
      this.renderChallengesGrid();
    } else if (viewName === 'workspace') {
      if (this.state.workspaceMode !== 'example' && !this.state.currentChallenge) {
        this.openCompilerForLanguage(this.state.currentLanguage || 'python', true);
      } else {
        this.syncCompilerChrome(this.state.currentLanguage || 'python');
      }
    }
  },

  // ==========================================================
  // LANGUAGE HOME PAGE & DEDICATED LANGUAGE PAGES
  // ==========================================================
  async loadLanguages() {
    try {
      const data = await API.getLanguages();
      this.state.languages = data.languages || [];
      this.renderLanguagesGrid();
    } catch (e) {
      console.warn('Could not load language catalog:', e);
    }
  },

  renderStudentAssignedPrograms() {
    const sectionEl = document.getElementById('student-assigned-programs-section');
    const summaryEl = document.getElementById('student-own-profile-summary');
    const gridEl = document.getElementById('student-assigned-programs-grid');
    if (!sectionEl || !gridEl) return;

    if (!this.state.isAuthenticated || this.isStaffRole(this.state.account)) {
      sectionEl.style.display = 'none';
      return;
    }
    sectionEl.style.display = 'block';

    const acc = this.state.account || {};
    const prog = this.state.studentProgress || {};
    const assigned = prog.assigned_programs || [];
    const className = prog.class_name || acc.class_id || 'CS101';
    const studentEmail = prog.email || acc.email || '';

    if (summaryEl) {
      summaryEl.innerHTML = `
        <span class="diff-badge" style="background: rgba(79, 70, 229, 0.1); color: var(--indigo-primary);">
          👤 ${this.escapeHtml(acc.display_name || prog.display_name || 'Student')}
        </span>
        ${studentEmail ? `<span class="diff-badge">${this.escapeHtml(studentEmail)}</span>` : ''}
        <span class="diff-badge">🏫 ${this.escapeHtml(className)}</span>
        <span class="diff-badge" style="background: var(--teal-light); color: var(--teal-success);">
          ⭐ Lvl ${prog.level || 1} (${prog.total_xp || 0} XP) • ${prog.completed_count || 0} Labs Done
        </span>
      `;
    }

    if (assigned.length === 0) {
      gridEl.innerHTML = `
        <div style="grid-column: 1 / -1; padding: 14px 16px; background: var(--bg-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-sm); color: var(--text-secondary); font-size: 0.85rem;">
          No specific learning programs have been assigned by your instructor yet. You can freely explore all 7 languages in the catalog below!
        </div>
      `;
      return;
    }

    gridEl.innerHTML = assigned.map(p => {
      const statusColor = p.status === 'Completed'
        ? 'background: var(--teal-light); color: var(--teal-success);'
        : (p.status === 'In Progress'
          ? 'background: rgba(79, 70, 229, 0.12); color: var(--indigo-primary);'
          : 'background: var(--amber-light); color: var(--amber-hint);');
      const labSummary = p.total_labs > 0
        ? `${p.completed_labs} / ${p.total_labs} Labs Completed (${p.progress_percent}%)`
        : `${p.lessons_count || 4} Lessons • ${p.examples_count || 6} Examples`;

      return `
        <div class="glass-panel student-assigned-program-card" data-program-id="${this.escapeHtml(p.language_id)}" style="padding: 16px; display: flex; flex-direction: column; justify-content: space-between; gap: 12px; border: 1px solid var(--indigo-border);">
          <div>
            <div style="display: flex; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 8px;">
              <div style="display: flex; align-items: center; gap: 8px;">
                <span style="font-size: 1.5rem;">${p.icon || '💻'}</span>
                <strong style="font-size: 1rem; color: var(--text-primary);">${this.escapeHtml(p.name)}</strong>
              </div>
              <span class="diff-badge" style="${statusColor} font-size: 0.74rem;">${this.escapeHtml(p.status)}</span>
            </div>
            <div style="font-size: 0.8rem; color: var(--text-secondary); margin-bottom: 8px;">
              ${this.escapeHtml(labSummary)}
            </div>
            <div class="progress-bar-bg" style="height: 7px; margin-bottom: 4px;">
              <div class="progress-bar-fill" style="width: ${p.progress_percent || 0}%;"></div>
            </div>
          </div>
          <div style="display: flex; gap: 6px; flex-wrap: wrap;">
            <button type="button" class="btn btn-primary btn-assigned-open" data-lang-id="${this.escapeHtml(p.language_id)}" style="padding: 5px 10px; font-size: 0.76rem;">
              Open Program →
            </button>
            <button type="button" class="btn btn-secondary btn-assigned-lessons" data-lang-id="${this.escapeHtml(p.language_id)}" style="padding: 5px 9px; font-size: 0.75rem;">
              Lessons
            </button>
            <button type="button" class="btn btn-secondary btn-assigned-workspace" data-lang-id="${this.escapeHtml(p.language_id)}" style="padding: 5px 9px; font-size: 0.75rem;">
              Workspace
            </button>
          </div>
        </div>
      `;
    }).join('');

    gridEl.querySelectorAll('.btn-assigned-open').forEach(btn => {
      btn.addEventListener('click', () => this.openLanguagePage(btn.dataset.langId));
    });
    gridEl.querySelectorAll('.btn-assigned-lessons').forEach(btn => {
      btn.addEventListener('click', () => this.openLanguagePage(btn.dataset.langId, 'lessons'));
    });
    gridEl.querySelectorAll('.btn-assigned-workspace').forEach(btn => {
      btn.addEventListener('click', () => this.openWorkspaceForLanguage(btn.dataset.langId));
    });
  },

  renderLanguagesGrid() {
    this.renderStudentAssignedPrograms();
    const container = document.getElementById('languages-grid-container');
    if (!container) return;
    container.innerHTML = '';

    const assignedMap = new Map(
      ((this.state.studentProgress && this.state.studentProgress.assigned_programs) || []).map(p => [p.language_id, p])
    );

    const filter = this.state.activeLangFilter;
    const query = this.state.langSearchQuery;

    const filtered = this.state.languages.filter(lang => {
      let matchesFilter = true;
      if (filter === 'ready') matchesFilter = lang.available === true;
      else if (filter === 'beginner') matchesFilter = lang.difficulty.toLowerCase().includes('beginner');
      else if (filter === 'interpreted') matchesFilter = lang.category.toLowerCase().includes('interpreted') || lang.category.toLowerCase().includes('query');
      else if (filter === 'compiled') matchesFilter = lang.category.toLowerCase().includes('compiled');

      let matchesQuery = true;
      if (query) {
        matchesQuery = lang.name.toLowerCase().includes(query) ||
                       lang.category.toLowerCase().includes(query) ||
                       lang.short_description.toLowerCase().includes(query);
      }

      return matchesFilter && matchesQuery;
    });

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 40px 0; color: var(--text-muted);">
          No languages match your filter. Try clearing your search keyword.
        </div>
      `;
      return;
    }

    filtered.forEach(lang => {
      const card = document.createElement('div');
      card.className = 'language-card';
      const statusLabel = lang.status_label || (lang.available ? 'Available' : 'Not installed');
      const runtimeLabel = lang.runtime_label || lang.category;
      const lessonsCount = lang.lessons_count ?? 4;
      const examplesCount = lang.examples_count ?? 6;
      const labsCount = lang.challenges_count ?? 0;
      const assignedProg = assignedMap.get(lang.id);

      card.innerHTML = `
        <div>
          <div class="lang-card-top">
            <span class="lang-card-icon">${lang.icon}</span>
            <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
              ${assignedProg ? `<span class="diff-badge" style="background: rgba(79, 70, 229, 0.12); color: var(--indigo-primary); font-size: 0.72rem;">✓ Assigned (${this.escapeHtml(assignedProg.status)})</span>` : ''}
              <span class="lang-avail-pill ${lang.available ? 'ready' : 'missing'}" title="${this.escapeHtml(lang.toolchain_status || '')}">
                ${lang.available ? '● Available' : '⚪ Not installed'}
              </span>
            </div>
          </div>
          <h3 class="lang-card-title">${this.escapeHtml(lang.name)}</h3>
          <div class="lang-card-meta">
            <span class="diff-badge">${this.escapeHtml(lang.difficulty)}</span>
            <span class="track-tag track-py">${this.escapeHtml(runtimeLabel)}</span>
          </div>
          <p class="lang-card-desc">${this.escapeHtml(lang.short_description)}</p>
          <div style="display: flex; gap: 8px; flex-wrap: wrap; margin: 10px 0 6px; font-size: 0.76rem; color: var(--text-secondary);">
            <span class="diff-badge">📚 ${lessonsCount} Lessons</span>
            <span class="diff-badge">💡 ${examplesCount} Examples</span>
            <span class="diff-badge">🎯 ${labsCount} ${labsCount === 1 ? 'Lab' : 'Labs'}</span>
          </div>
          ${lang.available ? '' : `<p class="lang-card-desc" style="font-size:0.75rem;color:var(--amber-hint); margin-top: 6px;">View only (${this.escapeHtml(statusLabel)}) — ${this.escapeHtml(lang.toolchain_status || 'Compiler/runtime not installed on this host')}</p>`}
        </div>
        <div class="lang-card-footer" style="gap: 6px; flex-wrap: wrap;">
          <button class="btn btn-secondary btn-lang-lessons" type="button" style="padding: 6px 10px; font-size: 0.78rem;">
            📚 Lessons
          </button>
          <button class="btn btn-secondary btn-lang-examples" type="button" style="padding: 6px 10px; font-size: 0.78rem;">
            💡 Examples
          </button>
          <button class="btn btn-secondary btn-lang-workspace" type="button" style="padding: 6px 10px; font-size: 0.78rem;">
            💻 Workspace
          </button>
          <button class="btn btn-primary btn-explore-lang" type="button" style="padding: 6px 12px; font-size: 0.8rem;">
            Explore ${this.escapeHtml(lang.name)} →
          </button>
        </div>
      `;

      card.querySelector('.btn-lang-lessons').addEventListener('click', (e) => {
        e.stopPropagation();
        this.openLanguagePage(lang.id, 'lessons');
      });

      card.querySelector('.btn-lang-examples').addEventListener('click', (e) => {
        e.stopPropagation();
        this.openLanguagePage(lang.id, 'examples');
      });

      card.querySelector('.btn-lang-workspace').addEventListener('click', (e) => {
        e.stopPropagation();
        this.openWorkspaceForLanguage(lang.id);
      });

      card.querySelector('.btn-explore-lang').addEventListener('click', (e) => {
        e.stopPropagation();
        this.openLanguagePage(lang.id);
      });

      card.addEventListener('click', () => {
        this.openLanguagePage(lang.id);
      });

      container.appendChild(card);
    });
  },

  async openLanguagePage(langId, initialTab = null) {
    try {
      this.state.currentLanguageId = langId;
      const details = await API.getLanguageDetails(langId);
      this.state.currentLanguageDetail = details;

      // Update URL hash for clean bookmarking
      window.location.hash = `languages/${langId}`;

      // Populate Language Page Header
      document.getElementById('detail-lang-icon').textContent = details.icon;
      document.getElementById('detail-lang-title').textContent = details.name;
      document.getElementById('detail-lang-diff').textContent = details.difficulty;
      document.getElementById('detail-lang-cat').textContent = details.runtime_label || details.category;
      document.getElementById('detail-lang-desc').textContent = details.short_description;

      // Populate Live Toolchain Banner
      const banner = document.getElementById('detail-status-banner');
      const heading = document.getElementById('detail-status-heading');
      const text = document.getElementById('detail-status-text');
      const version = document.getElementById('detail-status-version');
      const icon = document.getElementById('detail-status-icon');

      if (details.available) {
        banner.className = 'lang-status-banner ready';
        icon.textContent = '●';
        heading.textContent = `${details.runtime_label || 'Toolchain'}: Available`;
        text.textContent = 'Host environment is configured and ready for isolated, time-limited execution.';
        version.textContent = details.version || 'Available';
      } else {
        banner.className = 'lang-status-banner missing';
        icon.textContent = '⚠️';
        heading.textContent = `${details.runtime_label || 'Toolchain'}: Not installed (View only)`;
        text.textContent = `${details.runtime_description || details.toolchain_status || 'This language cannot run in the current installation.'} See the setup guide tab to install the toolchain locally.`;
        version.textContent = 'Not installed';
      }

      const startButton = document.getElementById('detail-start-coding-btn');
      const canStart = Boolean(details.available && (details.challenges || []).length);
      if (startButton) {
        startButton.disabled = false;
        if (canStart) {
          startButton.title = 'Open the first available lab for this language in the Workspace.';
          startButton.innerHTML = '<span>⚡</span> Start Coding Now';
        } else {
          startButton.title = `Open ${details.name} starter code in the Workspace.`;
          startButton.innerHTML = '<span>💻</span> Open in Workspace';
        }
      }

      // Populate Count & Tabs
      const chCount = (details.challenges || []).length;
      document.getElementById('detail-challenges-count').textContent = chCount;

      // Render Sub-Views
      this.renderLanguageChallenges(details.challenges || [], details);
      this.renderLanguageLessons(details.lessons || [], details);
      this.renderLanguageExamples(details.examples || [], details);
      this.renderLanguageSetup(details.setup_guide || {});

      // Switch to language detail view
      this.switchView('language-detail');
      const validTabs = ['challenges', 'lessons', 'examples', 'setup'];
      const targetTab = (initialTab && validTabs.includes(initialTab))
        ? initialTab
        : (chCount > 0 ? 'challenges' : 'lessons');
      this.switchLangSubTab(targetTab);
    } catch (e) {
      alert(`Could not load language details: ${e.message}`);
    }
  },

  switchLangSubTab(tabName) {
    this.state.activeLangTab = tabName;
    document.querySelectorAll('.lang-subtab-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.langTab === tabName);
    });

    document.querySelectorAll('.lang-pane').forEach(p => {
      p.classList.remove('active');
    });

    const target = document.getElementById(`lang-pane-${tabName}`);
    if (target) target.classList.add('active');
  },

  renderLanguageChallenges(challenges, langDetails = null) {
    const grid = document.getElementById('detail-challenges-grid');
    if (!grid) return;
    grid.innerHTML = '';

    const langId = (langDetails && langDetails.id) || this.state.currentLanguageId || 'python';
    const langName = (langDetails && langDetails.name) || langId;
    const completedSet = new Set((this.state.studentProgress?.completed_challenges || []).map(c => c.challenge_id));

    if (challenges.length === 0) {
      const emptyCard = document.createElement('div');
      emptyCard.className = 'glass-panel';
      emptyCard.style.cssText = 'grid-column: 1 / -1; text-align: center; padding: 28px 24px;';
      emptyCard.innerHTML = `
        <h3 style="font-size: 1.05rem; font-weight: 700; color: var(--text-primary); margin-bottom: 6px;">
          Practice ${this.escapeHtml(langName)} with Beginner Lessons &amp; Working Examples
        </h3>
        <p style="font-size: 0.88rem; color: var(--text-secondary); max-width: 560px; margin: 0 auto 16px;">
          Explore the built-in ${this.escapeHtml(langName)} lessons and 6 complete code examples, or load ${this.escapeHtml(langName)} directly into the coding workspace.
        </p>
        <div style="display: flex; justify-content: center; gap: 10px; flex-wrap: wrap;">
          <button type="button" class="btn btn-secondary btn-empty-lessons">📚 View Beginner Lessons</button>
          <button type="button" class="btn btn-secondary btn-empty-examples">💡 View 6 Code Examples</button>
          <button type="button" class="btn btn-primary btn-empty-workspace">💻 Open ${this.escapeHtml(langName)} in Workspace →</button>
        </div>
      `;
      emptyCard.querySelector('.btn-empty-lessons').addEventListener('click', () => this.switchLangSubTab('lessons'));
      emptyCard.querySelector('.btn-empty-examples').addEventListener('click', () => this.switchLangSubTab('examples'));
      emptyCard.querySelector('.btn-empty-workspace').addEventListener('click', () => this.openWorkspaceForLanguage(langId));
      grid.appendChild(emptyCard);
      return;
    }

    challenges.forEach(c => {
      const isCompleted = completedSet.has(c.id);
      const runtime = this.state.runtimes[c.execution_language || this.state.currentLanguageId] || { available: false };
      const canRun = Boolean(runtime.available);
      const card = document.createElement('div');
      card.className = 'glass-panel mission-card';

      card.innerHTML = `
        <div>
          <div class="mission-top">
            <span class="track-tag track-py">${this.escapeHtml(c.skill_tag)}</span>
            <span class="diff-badge">${this.escapeHtml(c.difficulty)}</span>
          </div>
          <h3 class="mission-title">${this.escapeHtml(c.title)}</h3>
          <p class="mission-desc">${this.escapeHtml(c.prompt)}</p>
        </div>
        <div class="mission-footer">
          <div class="status-badge ${isCompleted ? 'status-completed' : 'status-inprogress'}">
            <span style="color: ${isCompleted ? 'var(--teal-success)' : '#F59E0B'};">
              ${isCompleted ? '✓ Completed' : `⭐ +${c.xp_reward} XP`}
            </span>
          </div>
          <button class="btn btn-primary" style="padding: 6px 14px; font-size: 0.8rem;" ${canRun ? '' : 'disabled title="This lab language is not available on the server."'}>
            ${!canRun ? 'Runtime Needed' : (isCompleted ? 'Review Lab →' : 'Launch Lab →')}
          </button>
        </div>
      `;

      if (canRun) card.querySelector('button').addEventListener('click', () => this.openMission(c.id));

      grid.appendChild(card);
    });
  },

  renderLanguageLessons(lessons, langDetails = null) {
    const container = document.getElementById('detail-lessons-list');
    if (!container) return;
    container.innerHTML = '';

    const langId = (langDetails && langDetails.id) || this.state.currentLanguageId || 'python';
    const fileExt = (langDetails && langDetails.file_ext) || '.py';

    lessons.forEach((les, idx) => {
      const el = document.createElement('div');
      el.className = 'lesson-card';
      el.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; margin-bottom: 6px;">
          <h4 style="margin-bottom: 0;">${this.escapeHtml(les.title)}</h4>
          <button type="button" class="btn btn-secondary btn-try-lesson-workspace" style="padding: 5px 12px; font-size: 0.78rem;">
            💻 Try in Workspace
          </button>
        </div>
        <p><strong>Overview:</strong> ${this.escapeHtml(les.summary)}</p>
        <p>${this.escapeHtml(les.explanation)}</p>
        <div style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); margin-bottom: 6px;">Syntax Pattern:</div>
        <div class="code-snippet-box">${this.escapeHtml(les.example)}</div>
      `;

      el.querySelector('.btn-try-lesson-workspace').addEventListener('click', () => {
        this.handleLoadExampleIntoEditor(langId, {
          id: les.id || `${langId}_lesson_${idx + 1}`,
          title: les.title,
          category: 'Beginner Lesson',
          explanation: les.summary || les.explanation,
          filename: `lesson_${idx + 1}${fileExt}`,
          code: les.example,
          expected_output: ''
        });
      });

      container.appendChild(el);
    });
  },

  renderLanguageExamples(examples, langDetails = null) {
    const container = document.getElementById('detail-examples-list');
    if (!container) return;
    container.innerHTML = '';

    const langId = (langDetails && langDetails.id) || this.state.currentLanguageId || 'python';
    const isAvail = langDetails ? Boolean(langDetails.available) : Boolean(this.state.runtimes[langId]?.available);
    const modeLabel = isAvail ? 'Runnable' : 'View only';

    examples.forEach((ex, idx) => {
      const el = document.createElement('div');
      el.className = 'lesson-card';
      el.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; margin-bottom: 8px;">
          <div>
            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 4px;">
              <span class="track-tag track-py">${idx + 1}. ${this.escapeHtml(ex.category || 'Example')}</span>
              <span class="mode-pill ${isAvail ? 'runnable' : 'view-only'}">${modeLabel}</span>
            </div>
            <h4 style="margin-bottom: 4px;">${this.escapeHtml(ex.title)}</h4>
            <p style="margin-bottom: 0;">${this.escapeHtml(ex.explanation || ex.description)}</p>
          </div>
          <div style="display: flex; gap: 8px; flex-wrap: wrap;">
            <button type="button" class="btn btn-primary btn-open-ex-runner" style="padding: 6px 12px; font-size: 0.78rem;">
              ${isAvail ? '▶ Open & Run' : '👁️ View in Examples Library'}
            </button>
            <button type="button" class="btn btn-secondary btn-load-ex-editor" style="padding: 6px 12px; font-size: 0.78rem;">
              Load into editor
            </button>
          </div>
        </div>
        <div class="code-snippet-box" style="margin-bottom: 10px;">${this.escapeHtml(ex.code)}</div>
        <div style="font-size: 0.76rem; font-weight: 700; color: var(--text-muted); margin-bottom: 4px;">Expected Output:</div>
        <pre class="example-output-pre">${this.escapeHtml(ex.expected_output || '')}</pre>
      `;

      el.querySelector('.btn-open-ex-runner').addEventListener('click', () => {
        this.openExamplesForLanguage(langId, ex.id);
      });
      el.querySelector('.btn-load-ex-editor').addEventListener('click', () => {
        this.handleLoadExampleIntoEditor(langId, ex);
      });

      container.appendChild(el);
    });
  },

  renderLanguageSetup(setupGuide) {
    document.getElementById('detail-setup-title').textContent = setupGuide.title || 'Compiler Setup Guide';
    document.getElementById('detail-setup-text').textContent = setupGuide.instructions || 'Follow official toolchain installation documentation.';
    document.getElementById('detail-setup-cmd').textContent = setupGuide.command || 'runtime --version';
  },

  // ==========================================================
  // BUILT-IN CODE EXAMPLES LIBRARY
  // ==========================================================
  async loadExamplesCatalog() {
    try {
      const data = await API.getExamples();
      const map = {};
      (data.languages || []).forEach(lang => {
        map[lang.id] = lang;
      });
      this.state.examplesCatalog = map;
    } catch (e) {
      console.warn('Could not load examples catalog:', e);
    }
  },

  openExamplesForLanguage(langId, exampleId = null) {
    this.state.selectedExampleLang = langId || 'python';
    const langEntry = this.state.examplesCatalog[this.state.selectedExampleLang];
    if (exampleId) {
      this.state.selectedExampleId = exampleId;
    } else if (langEntry && langEntry.examples && langEntry.examples.length > 0) {
      this.state.selectedExampleId = langEntry.examples[0].id;
    }
    window.location.hash = `examples/${this.state.selectedExampleLang}`;
    this.switchView('examples');
  },

  handleExampleLanguageSelect(langId) {
    this.state.selectedExampleLang = langId;
    const langEntry = this.state.examplesCatalog[langId];
    if (langEntry && langEntry.examples && langEntry.examples.length > 0) {
      this.state.selectedExampleId = langEntry.examples[0].id;
    }
    this.renderExamplesView();
  },

  handleExampleItemSelect(exampleId) {
    this.state.selectedExampleId = exampleId;
    this.renderSelectedExampleDetail();
  },

  renderExamplesView() {
    const langSelect = document.getElementById('examples-language-select');
    const itemSelect = document.getElementById('examples-item-select');
    if (!langSelect || !itemSelect) return;

    const langOrder = ['python', 'sql', 'html', 'javascript', 'java', 'c', 'cpp'];
    const currentLangId = this.state.selectedExampleLang || 'python';

    // Populate Language selector with clear Available / Not installed status
    langSelect.innerHTML = '';
    langOrder.forEach(id => {
      const entry = this.state.examplesCatalog[id] || this.state.languages.find(l => l.id === id);
      if (!entry) return;
      const opt = document.createElement('option');
      opt.value = id;
      const statusText = entry.status_label || (entry.available ? 'Available' : 'Not installed');
      const rtLabel = entry.runtime_label || entry.category || '';
      opt.textContent = `${entry.name} — ${rtLabel} (${statusText})`;
      langSelect.appendChild(opt);
    });
    langSelect.value = currentLangId;

    const langEntry = this.state.examplesCatalog[currentLangId];
    const examples = (langEntry && langEntry.examples) || [];

    itemSelect.innerHTML = '';
    examples.forEach((ex, index) => {
      const opt = document.createElement('option');
      opt.value = ex.id;
      opt.textContent = `${index + 1}. ${ex.category || ex.title} — ${ex.title}`;
      itemSelect.appendChild(opt);
    });

    if (!examples.some(ex => ex.id === this.state.selectedExampleId) && examples.length > 0) {
      this.state.selectedExampleId = examples[0].id;
    }
    itemSelect.value = this.state.selectedExampleId || '';

    this.renderSelectedExampleDetail();
  },

  renderSelectedExampleDetail() {
    const langId = this.state.selectedExampleLang || 'python';
    const langEntry = this.state.examplesCatalog[langId];
    if (!langEntry) return;

    const examples = langEntry.examples || [];
    const ex = examples.find(item => item.id === this.state.selectedExampleId) || examples[0];
    if (!ex) return;

    const isAvailable = Boolean(langEntry.available);
    const statusLabel = langEntry.status_label || (isAvailable ? 'Available' : 'Not installed');
    const modeLabel = langEntry.mode_label || (isAvailable ? 'Runnable' : 'View only');
    const runtimeLabel = langEntry.runtime_label || langEntry.name;

    const rtLabelEl = document.getElementById('examples-runtime-label');
    if (rtLabelEl) rtLabelEl.textContent = runtimeLabel;

    const tcBadge = document.getElementById('examples-toolchain-badge');
    if (tcBadge) {
      tcBadge.textContent = statusLabel;
      tcBadge.className = `toolchain-pill ${isAvailable ? 'available' : 'missing'}`;
    }

    const modeBadge = document.getElementById('example-mode-badge');
    if (modeBadge) {
      modeBadge.textContent = modeLabel;
      modeBadge.className = `mode-pill ${isAvailable ? 'runnable' : 'view-only'}`;
    }

    const catIndex = examples.findIndex(item => item.id === ex.id) + 1;
    const catTag = document.getElementById('example-category-tag');
    if (catTag) catTag.textContent = `${catIndex}. ${ex.category || 'Beginner Example'}`;

    const filePill = document.getElementById('example-filename-pill');
    if (filePill) filePill.textContent = ex.filename || `example.${langId}`;

    const titleEl = document.getElementById('example-title');
    if (titleEl) titleEl.textContent = ex.title;

    const expEl = document.getElementById('example-explanation');
    if (expEl) expEl.textContent = ex.explanation || ex.description;

    const langTag = document.getElementById('example-lang-tag');
    if (langTag) langTag.textContent = `${langEntry.name} (${ex.filename || langId})`;

    const codeContent = document.getElementById('example-code-content');
    if (codeContent) codeContent.textContent = ex.code;

    const expectedOut = document.getElementById('example-expected-output');
    if (expectedOut) expectedOut.textContent = ex.expected_output || '';

    // Hide previous live output until Run is clicked
    const liveWrapper = document.getElementById('example-live-output-wrapper');
    if (liveWrapper) liveWrapper.style.display = 'none';

    // HTML/CSS Browser Preview
    const previewWrapper = document.getElementById('example-preview-wrapper');
    const previewFrame = document.getElementById('example-preview-iframe');
    if (previewWrapper && previewFrame) {
      if (langId === 'html') {
        previewWrapper.style.display = 'block';
        previewFrame.srcdoc = ex.code;
      } else {
        previewWrapper.style.display = 'none';
        previewFrame.srcdoc = '';
      }
    }

    // Run button & Setup Guide visibility
    const runBtn = document.getElementById('run-example-btn');
    const runBtnText = document.getElementById('run-example-btn-text');
    const runStatusPill = document.getElementById('example-run-status-pill');
    const setupBox = document.getElementById('example-setup-guide-box');
    const setupText = document.getElementById('example-setup-text');
    const setupCmd = document.getElementById('example-setup-cmd');

    if (isAvailable) {
      if (runBtn) {
        runBtn.disabled = false;
        runBtn.title = `Run this ${langEntry.name} example using ${runtimeLabel}`;
      }
      if (runBtnText) runBtnText.textContent = langId === 'html' ? 'Refresh Preview' : 'Run';
      if (runStatusPill) {
        runStatusPill.textContent = 'Ready to Run';
        runStatusPill.style.color = 'var(--teal-success)';
      }
      if (setupBox) setupBox.style.display = 'none';
    } else {
      if (runBtn) {
        runBtn.disabled = true;
        runBtn.title = `${langEntry.name} toolchain is not installed on this host (View only).`;
      }
      if (runBtnText) runBtnText.textContent = 'View only';
      if (runStatusPill) {
        runStatusPill.textContent = 'View only (Toolchain not installed)';
        runStatusPill.style.color = 'var(--amber-hint)';
      }
      if (setupBox) {
        setupBox.style.display = 'block';
        const sg = langEntry.setup_guide || {};
        if (setupText) {
          setupText.textContent = sg.instructions || `${langEntry.name} (${runtimeLabel}) is not installed on this computer. Install the compiler or runtime locally to execute ${langEntry.name} code.`;
        }
        if (setupCmd) {
          setupCmd.textContent = sg.command || `${langId} --version`;
        }
      }
    }
  },

  async handleRunExample() {
    const langId = this.state.selectedExampleLang || 'python';
    const langEntry = this.state.examplesCatalog[langId];
    if (!langEntry) return;

    const examples = langEntry.examples || [];
    const ex = examples.find(item => item.id === this.state.selectedExampleId) || examples[0];
    if (!ex) return;

    if (!langEntry.available) {
      return;
    }

    const runBtn = document.getElementById('run-example-btn');
    const runBtnText = document.getElementById('run-example-btn-text');
    const runStatusPill = document.getElementById('example-run-status-pill');
    const liveWrapper = document.getElementById('example-live-output-wrapper');
    const liveOutput = document.getElementById('example-live-output');
    const liveLabel = document.getElementById('example-live-output-label');

    if (runBtn) runBtn.disabled = true;
    if (runBtnText) runBtnText.textContent = 'Running...';
    if (runStatusPill) runStatusPill.textContent = 'Running in sandbox...';

    try {
      if (langId === 'html') {
        const previewFrame = document.getElementById('example-preview-iframe');
        if (previewFrame) previewFrame.srcdoc = ex.code;
      }

      const res = await API.runCode(ex.code, langId, '');
      if (liveWrapper && liveOutput) {
        liveWrapper.style.display = 'block';
        if (res.ran) {
          liveOutput.className = 'example-output-pre live-output';
          liveOutput.textContent = res.output || '(Program finished with no console output)';
          if (liveLabel) liveLabel.textContent = `Actual Output (${res.runtime_label || langEntry.name} • ${res.duration_ms || 0} ms):`;
          if (runStatusPill) {
            runStatusPill.textContent = 'Executed Successfully';
            runStatusPill.style.color = 'var(--teal-success)';
          }
        } else {
          liveOutput.className = 'example-output-pre live-output error';
          liveOutput.textContent = res.error || res.message || 'Execution stopped with an error.';
          if (liveLabel) liveLabel.textContent = 'Execution Error (Plain Language):';
          if (runStatusPill) {
            runStatusPill.textContent = res.mode_label === 'View only' ? 'View only' : 'Execution Error';
            runStatusPill.style.color = 'var(--red-error)';
          }
        }
      }
    } catch (err) {
      if (liveWrapper && liveOutput) {
        liveWrapper.style.display = 'block';
        liveOutput.className = 'example-output-pre live-output error';
        liveOutput.textContent = err.message || 'Could not run example.';
      }
    } finally {
      if (runBtn) runBtn.disabled = false;
      if (runBtnText) runBtnText.textContent = langId === 'html' ? 'Refresh Preview' : 'Run';
    }
  },

  handleLoadCurrentExampleIntoEditor() {
    const langId = this.state.selectedExampleLang || 'python';
    const langEntry = this.state.examplesCatalog[langId];
    if (!langEntry) return;
    const examples = langEntry.examples || [];
    const ex = examples.find(item => item.id === this.state.selectedExampleId) || examples[0];
    if (!ex) return;
    this.handleLoadExampleIntoEditor(langId, ex);
  },

  handleLoadExampleIntoEditor(langId, example) {
    const currentCode = window.editorManager ? window.editorManager.getValue() : '';
    const starterBaseline = this.state.workspaceMode === 'example'
      ? (this.state.currentExample?.code || '')
      : (this.state.currentChallenge?.starter_code || '');

    if (currentCode.trim() && currentCode.trim() !== starterBaseline.trim()) {
      const ok = confirm(
        'You have code in the editor. Do you want to open this example in a fresh Example Workspace?\n\n(Your challenge starter code is kept separate and can be restored anytime with "Return to Challenge".)'
      );
      if (!ok) return;
    }

    this.state.workspaceMode = 'example';
    this.state.currentExample = { ...example, language: langId };
    this.state.currentLanguage = langId;

    const langSelect = document.getElementById('editor-language-select');
    if (langSelect) langSelect.value = langId;

    window.editorManager.setValue(example.code, langId);

    // Show only the example's file in the workspace file list
    const fileName = example.filename || this.getExerciseFileName(null, langId);
    const fileTab = document.getElementById('current-file-tab');
    if (fileTab) fileTab.textContent = fileName;
    const fileList = document.getElementById('workspace-file-list');
    if (fileList) {
      fileList.innerHTML = `
        <li class="file-item active">
          <span aria-hidden="true">📄</span> <span>${this.escapeHtml(fileName)}</span>
        </li>
      `;
    }

    // Show Example Mode banner
    const exBanner = document.getElementById('workspace-example-banner');
    const exBannerTitle = document.getElementById('workspace-example-banner-title');
    const exBannerDesc = document.getElementById('workspace-example-banner-desc');
    const rt = this.state.runtimes[langId] || { available: false };
    if (exBanner) {
      exBanner.style.display = 'flex';
      if (exBannerTitle) {
        exBannerTitle.textContent = `Example Workspace — ${example.title} (${rt.available ? 'Runnable' : 'View only'}):`;
      }
      if (exBannerDesc) {
        exBannerDesc.textContent = `${example.explanation || example.description} Challenge starter code is kept separate.`;
      }
    }

    // Update Lab Guide to describe the example
    const titleEl = document.getElementById('workspace-mission-title');
    if (titleEl) titleEl.textContent = `Example: ${example.title}`;
    const trackEl = document.getElementById('workspace-mission-track');
    if (trackEl) trackEl.textContent = `${example.category || 'Code Example'} (${rt.available ? 'Runnable' : 'View only'})`;
    const scenarioEl = document.getElementById('mission-scenario-text');
    if (scenarioEl) scenarioEl.textContent = example.explanation || example.description;

    this.syncCompilerChrome(langId);
    this.updateRuntimeBadge(langId);

    // HTML Preview
    const previewContainer = document.getElementById('html-preview-container');
    if (previewContainer) {
      previewContainer.style.display = (langId === 'html') ? 'block' : 'none';
      if (langId === 'html') {
        this.updateHtmlPreview(example.code);
      }
    }

    // Hide challenge concept recap
    const recapContainer = document.getElementById('concept-recap-container');
    if (recapContainer) recapContainer.style.display = 'none';

    const summaryBox = document.getElementById('test-summary-box');
    if (summaryBox) summaryBox.style.display = 'none';

    const resultsContainer = document.getElementById('test-results-container');
    if (resultsContainer) {
      if (rt.available) {
        resultsContainer.innerHTML = `
          <div class="test-item-card passed">
            <div class="test-item-top">
              <span class="test-name">Expected Example Output</span>
              <span style="font-size: 0.75rem; font-weight: 700; color: var(--teal-success);">Runnable</span>
            </div>
            <pre class="example-output-pre" style="margin-top: 6px;">${this.escapeHtml(example.expected_output || '')}</pre>
            <div class="test-msg" style="margin-top: 8px;">Click <strong>▶ Run Example</strong> above to execute this example in the isolated runner.</div>
          </div>
        `;
      } else {
        const sg = rt.setup_guide || {};
        resultsContainer.innerHTML = `
          <div class="test-item-card failed">
            <div class="test-item-top">
              <span class="test-name">View only — ${this.escapeHtml(rt.runtime_label || langId)} Not Installed</span>
              <span style="font-size: 0.75rem; font-weight: 700; color: var(--amber-hint);">View only</span>
            </div>
            <div class="test-msg">${this.escapeHtml(sg.instructions || rt.description || 'This language toolchain is not installed on this host.')}</div>
            <pre class="example-output-pre" style="margin-top: 8px;">Expected Output:\n${this.escapeHtml(example.expected_output || '')}</pre>
          </div>
        `;
      }
    }

    this.switchView('workspace');
    this.switchRightTab('output');
  },

  handleReturnToChallengeFromExample() {
    this.state.workspaceMode = 'challenge';
    this.state.currentExample = null;
    const exBanner = document.getElementById('workspace-example-banner');
    if (exBanner) exBanner.style.display = 'none';

    if (this.state.currentChallenge) {
      this.openMission(this.state.currentChallenge.id);
    } else if (this.state.challenges.length > 0) {
      this.openMission(this.state.challenges[0].id);
    } else {
      this.switchView('dashboard');
    }
  },

  openWorkspaceForLanguage(langId) {
    const normLang = (langId || 'python').toLowerCase().trim();
    const details = (this.state.currentLanguageDetail && this.state.currentLanguageDetail.id === normLang)
      ? this.state.currentLanguageDetail
      : null;
    const matchingChallenges = details?.challenges?.length
      ? details.challenges
      : (this.state.challenges || []).filter(c => (c.execution_language || 'python').toLowerCase() === normLang);
    const firstChallenge = matchingChallenges[0];

    if (this.state.runtimes[normLang]?.available && firstChallenge) {
      this.openMission(firstChallenge.id);
      return;
    }

    const langEntry = this.state.examplesCatalog[normLang] || details;
    const firstExample = langEntry?.examples?.[0];
    if (firstExample) {
      this.handleLoadExampleIntoEditor(normLang, firstExample);
      return;
    }

    this.openExamplesForLanguage(normLang);
  },

  // ==========================================================
  // DASHBOARD & CHALLENGES CATALOG
  // ==========================================================
  renderDashboard() {
    const prog = this.state.studentProgress || { total_xp: 0, level: 1, completed_challenges: [] };
    const xpPerLevel = Math.max(1, prog.xp_per_level || 100);
    const currentXp = prog.total_xp || 0;
    const currentLevel = prog.level || 1;
    const xpIntoLevel = currentXp % xpPerLevel;
    const pct = Math.min(100, Math.round((xpIntoLevel / xpPerLevel) * 100));

    const levelLabel = document.getElementById('dash-level-label');
    if (levelLabel) {
      const titles = ['Explorer', 'Junior Coder', 'Developer', 'Architect', 'Master'];
      const title = titles[Math.min(titles.length - 1, currentLevel - 1)];
      levelLabel.textContent = `Level ${currentLevel}: ${title}`;
    }

    const xpText = document.getElementById('dash-xp-progress-text');
    if (xpText) {
      xpText.textContent = `${xpIntoLevel} / ${xpPerLevel} XP to Level ${currentLevel + 1}`;
    }

    const progressBar = document.getElementById('dash-xp-progress-bar');
    if (progressBar) {
      progressBar.style.width = `${pct}%`;
    }

    // Suggested Next Challenge
    const completedSet = new Set((prog.completed_challenges || []).map(c => c.challenge_id));
    const nextChallenge = this.state.challenges.find(c => !completedSet.has(c.id)) || this.state.challenges[0];

    if (nextChallenge) {
      const recTitle = document.getElementById('rec-mission-title');
      const recTrack = document.getElementById('rec-mission-track');
      const recBtn = document.getElementById('rec-mission-btn');
      if (recTitle) recTitle.textContent = nextChallenge.title;
      if (recTrack) recTrack.textContent = `${nextChallenge.skill_tag} • +${nextChallenge.xp_reward} XP`;
      if (recBtn) recBtn.onclick = () => this.openMission(nextChallenge.id);
    }

    // Populate Languages & Lessons list on Dashboard (highlighting assigned learning programs first)
    const langListEl = document.getElementById('dashboard-languages-list');
    if (langListEl) {
      const langs = this.state.languages || [];
      const assignedMap = new Map(
        ((prog && prog.assigned_programs) || []).map(p => [p.language_id, p])
      );
      if (langs.length === 0) {
        langListEl.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem;">Loading languages...</div>`;
      } else {
        const sortedLangs = [...langs].sort((a, b) => {
          const aAssigned = assignedMap.has(a.id) ? 0 : 1;
          const bAssigned = assignedMap.has(b.id) ? 0 : 1;
          return aAssigned - bAssigned;
        });
        langListEl.innerHTML = sortedLangs.map(lang => {
          const ap = assignedMap.get(lang.id);
          const badgeHtml = ap
            ? `<span class="diff-badge" style="background: rgba(79, 70, 229, 0.12); color: var(--indigo-primary); font-size: 0.72rem; margin-left: 6px;">Assigned • ${this.escapeHtml(ap.status)} (${ap.completed_labs}/${ap.total_labs} labs)</span>`
            : '';
          return `
          <div class="dashboard-lang-row">
            <div style="display: flex; align-items: center; gap: 10px;">
              <span style="font-size: 1.35rem;">${lang.icon}</span>
              <div>
                <div style="display: flex; align-items: center; flex-wrap: wrap;">
                  <strong style="color: var(--text-primary); font-size: 0.9rem;">${this.escapeHtml(lang.name)}</strong>
                  ${badgeHtml}
                </div>
                <div style="font-size: 0.76rem; color: var(--text-secondary);">
                  ${this.escapeHtml(lang.difficulty)} • 6 Beginner Examples
                </div>
              </div>
            </div>
            <div style="display: flex; gap: 6px; align-items: center;">
              <button type="button" class="btn btn-secondary dash-lang-ex-btn" data-lang-id="${this.escapeHtml(lang.id)}" style="padding: 5px 10px; font-size: 0.76rem;">
                Examples
              </button>
              <button type="button" class="btn btn-secondary dash-lang-les-btn" data-lang-id="${this.escapeHtml(lang.id)}" style="padding: 5px 10px; font-size: 0.76rem;">
                Lessons →
              </button>
            </div>
          </div>
        `;
        }).join('');

        langListEl.querySelectorAll('.dash-lang-ex-btn').forEach(btn => {
          btn.addEventListener('click', () => this.openExamplesForLanguage(btn.dataset.langId));
        });
        langListEl.querySelectorAll('.dash-lang-les-btn').forEach(btn => {
          btn.addEventListener('click', () => this.openLanguagePage(btn.dataset.langId, 'lessons'));
        });
      }
    }

    // Completed Challenges List in Dashboard
    const completedListEl = document.getElementById('dash-completed-list');
    if (completedListEl) {
      const completed = prog.completed_challenges || [];
      if (completed.length === 0) {
        completedListEl.innerHTML = `
          <div style="text-align: center; padding: 20px 0; color: var(--text-muted);">
            No completed labs yet. Click <strong>Continue Mission</strong> above to start!
          </div>
        `;
      } else {
        completedListEl.innerHTML = completed.map(c => `
          <div style="padding: 10px 12px; background: var(--bg-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-sm); margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div>
              <strong style="color: var(--text-primary); font-size: 0.88rem;">${this.escapeHtml(c.title)}</strong>
              <div style="font-size: 0.75rem; color: var(--text-secondary);">${this.escapeHtml(c.skill_tag)} • ${this.escapeHtml(c.completed_at || 'Completed')}</div>
            </div>
            <span class="diff-badge" style="background: var(--teal-light); color: var(--teal-success); font-size: 0.75rem;">
              ✓ +${c.xp_awarded} XP
            </span>
          </div>
        `).join('');
      }
    }
  },

  handleContinueMission() {
    const prog = this.state.studentProgress || { completed_challenges: [] };
    const completedSet = new Set((prog.completed_challenges || []).map(c => c.challenge_id));
    const nextChallenge = this.state.challenges.find(c => !completedSet.has(c.id)) || this.state.challenges[0];
    if (nextChallenge) {
      this.openMission(nextChallenge.id);
    } else {
      this.switchView('languages');
    }
  },

  renderChallengesGrid() {
    const container = document.getElementById('missions-grid-container');
    if (!container) return;
    container.innerHTML = '';

    const filter = this.state.activeFilter;
    const query = this.state.searchQuery;
    const completedSet = new Set((this.state.studentProgress?.completed_challenges || []).map(c => c.challenge_id));

    const filtered = this.state.challenges.filter(c => {
      let matchesTrack = true;
      if (filter === 'python') matchesTrack = c.skill_tag.includes('python') || c.id.includes('py');
      else if (filter === 'sql') matchesTrack = c.skill_tag.includes('sql');
      else if (filter === 'html') matchesTrack = c.skill_tag.includes('html') || c.id.includes('html');
      else if (filter === 'javascript') matchesTrack = c.skill_tag.includes('web') || c.skill_tag.includes('js');
      else if (filter === 'java') matchesTrack = c.skill_tag.includes('java');
      else if (filter === 'c') matchesTrack = c.skill_tag === 'c-systems';
      else if (filter === 'cpp') matchesTrack = c.skill_tag.includes('cpp');

      let matchesQuery = true;
      if (query) {
        matchesQuery = c.title.toLowerCase().includes(query) ||
                       c.skill_tag.toLowerCase().includes(query) ||
                       c.prompt.toLowerCase().includes(query);
      }

      return matchesTrack && matchesQuery;
    });

    if (filtered.length === 0) {
      container.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 40px 0; color: var(--text-muted);">
          No labs matched your filter. Try another topic or search term.
        </div>
      `;
      return;
    }

    filtered.forEach(c => {
      const isCompleted = completedSet.has(c.id);
      const card = document.createElement('div');
      card.className = 'glass-panel mission-card';

      let trackClass = 'track-py';
      if (c.skill_tag.includes('sql')) trackClass = 'track-sql';
      else if (c.skill_tag.includes('web')) trackClass = 'track-web';
      else if (c.skill_tag.includes('c-systems')) trackClass = 'track-c';
      else if (c.skill_tag.includes('cpp')) trackClass = 'track-cpp';

      card.innerHTML = `
        <div>
          <div class="mission-top">
            <span class="track-tag ${trackClass}">${c.skill_tag}</span>
            <span class="diff-badge">${c.difficulty}</span>
          </div>
          <h3 class="mission-title">${c.title}</h3>
          <p class="mission-desc">${c.prompt}</p>
        </div>
        <div class="mission-footer">
          <div class="status-badge ${isCompleted ? 'status-completed' : 'status-inprogress'}">
            <span style="color: ${isCompleted ? 'var(--teal-success)' : '#F59E0B'};">
              ${isCompleted ? '✓ Completed' : `⭐ +${c.xp_reward} XP`}
            </span>
          </div>
          <button class="btn btn-primary" style="padding: 6px 14px; font-size: 0.8rem;">
            ${isCompleted ? 'Review Lab →' : 'Launch Lab →'}
          </button>
        </div>
      `;

      card.querySelector('button').addEventListener('click', () => {
        this.openMission(c.id);
      });

      container.appendChild(card);
    });
  },

  // ==========================================================
  // WORKSPACE & CORE LEARNING RULE (STUDENT WRITES THE CODE)
  // ==========================================================
  getExerciseFileName(challenge, lang) {
    const extMap = {
      python: '.py',
      sql: '.sql',
      html: '.html',
      javascript: '.js',
      java: '.java',
      c: '.c',
      cpp: '.cpp'
    };
    const ext = extMap[lang] || '.txt';
    if (!challenge) {
      return lang === 'java' ? 'Main.java' : `main${ext}`;
    }

    const baseNames = {
      ch_py_double: 'double_value',
      ch_py_filter: 'api_filter',
      ch_sql_search: 'search_query',
      ch_web_validator: 'validator',
      ch_c_bounds: 'attendee_processor',
      ch_cpp_binary_search: 'binary_search',
      ch_java_grade_calculator: lang === 'java' ? 'GradeAverage' : 'grade_average',
      ch_html_profile_card: 'profile_card'
    };

    const base = baseNames[challenge.id] || challenge.id.replace(/^ch_[a-z]+_/, '') || 'solution';
    return `${base}${ext}`;
  },

  renderWorkspaceFiles(challenge, lang) {
    const fileName = this.getExerciseFileName(challenge, lang);
    const fileTab = document.getElementById('current-file-tab');
    if (fileTab) {
      fileTab.textContent = fileName;
    }

    const fileList = document.getElementById('workspace-file-list');
    if (!fileList) return;

    fileList.innerHTML = '';
    const li = document.createElement('li');
    li.className = 'file-item active';
    li.innerHTML = `<span aria-hidden="true">📄</span> <span>${this.escapeHtml(fileName)}</span>`;
    li.addEventListener('click', () => {
      const monacoInput = document.querySelector('#monaco-container textarea') || document.getElementById('fallback-editor');
      if (monacoInput) monacoInput.focus();
    });
    fileList.appendChild(li);
  },

  handleHelpGuide() {
    this.switchRightTab('guide');
    const guidePane = document.getElementById('tab-pane-guide');
    if (guidePane) {
      guidePane.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  },

  async openMission(challengeId) {
    try {
      const challenge = await API.getChallenge(challengeId);
      this.state.workspaceMode = 'challenge';
      this.state.currentExample = null;
      this.state.currentChallenge = challenge;
      this.state.unlockedHints = new Set([1]);
      this.state.recentError = null;

      const exBanner = document.getElementById('workspace-example-banner');
      if (exBanner) exBanner.style.display = 'none';

      const defaultLang = challenge.execution_language || 'python';
      this.state.currentLanguage = defaultLang;

      // Update language select dropdown
      const langSelect = document.getElementById('editor-language-select');
      if (langSelect) langSelect.value = defaultLang;

      // Set editor value, language, and current exercise file list
      window.editorManager.setValue(challenge.starter_code, defaultLang);
      this.renderWorkspaceFiles(challenge, defaultLang);

      // Update workspace header & brief
      const titleEl = document.getElementById('workspace-mission-title');
      if (titleEl) titleEl.textContent = challenge.title;
      const trackEl = document.getElementById('workspace-mission-track');
      if (trackEl) trackEl.textContent = `${challenge.skill_tag} (+${challenge.xp_reward} XP)`;
      const scenarioEl = document.getElementById('mission-scenario-text');
      if (scenarioEl) scenarioEl.textContent = challenge.prompt;

      // Populate plain-language steps in Lab Guide Tab
      const step1 = document.getElementById('guide-step-1');
      if (step1) step1.textContent = `Complete the solution for "${challenge.title}" following the description above.`;
      const step2 = document.getElementById('guide-step-2');
      if (step2) step2.textContent = `Check the function parameters or table columns and return the expected output format.`;
      const step3 = document.getElementById('guide-step-3');
      if (step3) step3.textContent = `Test with normal inputs first, then check edge cases like empty lists, zero, or blank text.`;

      // Check runtime availability
      this.updateRuntimeBadge(defaultLang);

      // Check HTML preview visibility
      const previewContainer = document.getElementById('html-preview-container');
      if (previewContainer) {
        previewContainer.style.display = (defaultLang === 'html') ? 'block' : 'none';
        if (defaultLang === 'html') {
          this.updateHtmlPreview(challenge.starter_code);
        }
      }

      // Reset concept recap box
      const recapContainer = document.getElementById('concept-recap-container');
      if (recapContainer) recapContainer.style.display = 'none';

      // Reset test panel
      const resultsContainer = document.getElementById('test-results-container');
      if (resultsContainer) {
        resultsContainer.innerHTML = `
          <div style="text-align: center; color: var(--text-muted); padding: 30px 10px; font-size: 0.85rem;">
            Click <strong>▶ Run Tests</strong> above to check your code.
          </div>
        `;
      }
      const summaryBox = document.getElementById('test-summary-box');
      if (summaryBox) summaryBox.style.display = 'none';

      // Switch to workspace view and Output tab
      this.switchView('workspace');
      this.switchRightTab('output');
      window.location.hash = `challenge-${challengeId}`;
    } catch (err) {
      alert(`Could not load lab challenge: ${err.message}`);
    }
  },

  COMPILER_META: {
    python: {
      title: 'Python Online Compiler',
      badge: 'Py',
      filename: 'main.py',
      starter: '# Online Python Compiler\n# Write and run Python code below\n\ndef greet(name):\n    return f"Hello, {name}!"\n\nprint(greet("World"))\n'
    },
    c: {
      title: 'C Online Compiler',
      badge: 'C',
      filename: 'main.c',
      starter: '// Online C Compiler\n// Write and run C code below\n\n#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n    return 0;\n}\n'
    },
    cpp: {
      title: 'C++ Online Compiler',
      badge: 'C++',
      filename: 'main.cpp',
      starter: '// Online C++ Compiler\n// Write and run C++ code below\n\n#include <iostream>\n\nint main() {\n    std::cout << "Hello, World!" << std::endl;\n    return 0;\n}\n'
    },
    java: {
      title: 'Java Online Compiler',
      badge: 'Java',
      filename: 'Main.java',
      starter: '// Online Java Compiler\n// Write and run Java code below\n\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n    }\n}\n'
    },
    javascript: {
      title: 'JavaScript Online Compiler',
      badge: 'JS',
      filename: 'main.js',
      starter: '// Online JavaScript Compiler\n// Write and run JavaScript code below\n\nconsole.log("Hello, World!");\n'
    },
    typescript: {
      title: 'TypeScript Online Editor',
      badge: 'TS',
      filename: 'main.ts',
      starter: '// Online TypeScript Editor\nconst greeting: string = "Hello, TypeScript!";\nconsole.log(greeting);\n'
    },
    sql: {
      title: 'Online SQL Editor',
      badge: 'SQL',
      filename: 'query.sql',
      starter: '-- Online SQL Editor\n-- Run SQL queries against the Customers, Orders, and resources tables\n\nSELECT first_name, last_name, age, country\nFROM Customers;\n'
    },
    html: {
      title: 'HTML & CSS Online Editor',
      badge: 'HTML',
      filename: 'index.html',
      starter: '<!DOCTYPE html>\n<html>\n<head>\n  <style>\n    body { font-family: Inter, sans-serif; padding: 24px; }\n    h1 { color: #0556F3; }\n  </style>\n</head>\n<body>\n  <h1>Hello, World!</h1>\n  <p>Edit this HTML &amp; CSS and click Run to see your live preview.</p>\n</body>\n</html>\n'
    }
  },

  isRunnableInCurrentEnv(lang) {
    if (lang === 'html' || lang === 'javascript') return true;
    const rt = this.state.runtimes[lang];
    return Boolean(rt && rt.available);
  },

  syncCompilerChrome(lang) {
    const meta = this.COMPILER_META[lang] || this.COMPILER_META.python;
    const heading = document.getElementById('compiler-heading-title');
    const badgeDot = document.getElementById('compiler-lang-badge');
    const fileTab = document.getElementById('current-file-tab');
    const langSelect = document.getElementById('editor-language-select');
    const sqlSchema = document.getElementById('pz-sql-schema');
    const sqlPreview = document.getElementById('pz-sql-tables-preview');
    const previewContainer = document.getElementById('html-preview-container');

    if (heading) heading.textContent = meta.title;
    if (badgeDot) badgeDot.textContent = meta.badge;
    if (fileTab && this.state.workspaceMode === 'example') fileTab.textContent = meta.filename;
    if (langSelect) langSelect.value = lang;

    document.querySelectorAll('.pz-rail-btn[data-rail-lang]').forEach(btn => {
      const isCurrent = btn.dataset.railLang === lang;
      btn.classList.toggle('active', isCurrent);
      btn.hidden = !isCurrent;
      btn.style.display = isCurrent ? 'inline-flex' : 'none';
    });

    if (sqlSchema) sqlSchema.hidden = (lang !== 'sql');
    if (sqlPreview) sqlPreview.hidden = (lang !== 'sql');
    if (previewContainer) {
      previewContainer.style.display = (lang === 'html') ? 'block' : 'none';
    }
    this.updateRuntimeBadge(lang);
  },

  openCompilerForLanguage(langId, alreadySwitching = false) {
    const lang = this.COMPILER_META[langId] ? langId : 'python';
    const meta = this.COMPILER_META[lang];
    this._compilerDrafts = this._compilerDrafts || {};

    // Save current standalone draft before switching languages
    if (this.state.workspaceMode === 'example' && this.state.currentLanguage && window.editorManager) {
      const prevCode = window.editorManager.getValue();
      if (prevCode && prevCode.trim()) {
        this._compilerDrafts[this.state.currentLanguage] = prevCode;
      }
    }

    this.state.workspaceMode = 'example';
    this.state.currentLanguage = lang;
    this.state.currentExample = {
      id: `compiler_${lang}`,
      title: meta.title,
      category: 'Online Compiler',
      explanation: `Write and run ${meta.title} code.`,
      filename: meta.filename,
      code: meta.starter
    };

    const codeToLoad = this._compilerDrafts[lang] || meta.starter;
    if (window.editorManager) {
      window.editorManager.setValue(codeToLoad, lang);
    }

    const exBanner = document.getElementById('workspace-example-banner');
    if (exBanner) exBanner.style.display = 'none';
    const recapContainer = document.getElementById('concept-recap-container');
    if (recapContainer) recapContainer.style.display = 'none';
    const summaryBox = document.getElementById('test-summary-box');
    if (summaryBox) summaryBox.style.display = 'none';
    const container = document.getElementById('test-results-container');
    if (container) {
      container.innerHTML = `<div class="pz-empty-output">Click <strong>Run ▶</strong> to execute your ${this.escapeHtml(meta.badge)} code.</div>`;
    }
    this.hideErrorDetective();

    if (lang === 'html') {
      this.updateHtmlPreview(codeToLoad);
    }

    this.syncCompilerChrome(lang);
    if (!alreadySwitching) {
      this.setRouteHash(`#compiler/${lang}`);
      this.switchView('workspace');
    }
    this.switchRightTab('output');
  },

  handleDownloadCode() {
    const lang = this.state.currentLanguage || 'python';
    const meta = this.COMPILER_META[lang] || this.COMPILER_META.python;
    const code = window.editorManager ? window.editorManager.getValue() : '';
    const blob = new Blob([code], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = meta.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  },

  initCompilerResizer() {
    const resizer = document.getElementById('pz-resizer');
    const editorPane = document.getElementById('pz-editor-pane');
    const outputPane = document.getElementById('pz-output-pane');
    const shell = document.getElementById('pz-ide-shell');
    if (!resizer || !editorPane || !outputPane || !shell) return;

    let dragging = false;
    resizer.addEventListener('mousedown', (e) => {
      dragging = true;
      resizer.classList.add('dragging');
      document.body.style.cursor = 'col-resize';
      e.preventDefault();
    });
    document.addEventListener('mousemove', (e) => {
      if (!dragging) return;
      const rect = shell.getBoundingClientRect();
      const railWidth = 54 + (document.getElementById('pz-sql-schema')?.hidden ? 0 : 180);
      const avail = rect.width - railWidth - 6;
      const offset = e.clientX - rect.left - railWidth;
      const pct = Math.max(25, Math.min(75, (offset / avail) * 100));
      editorPane.style.flex = `0 0 ${pct}%`;
      outputPane.style.flex = `1 1 ${100 - pct}%`;
    });
    document.addEventListener('mouseup', () => {
      if (!dragging) return;
      dragging = false;
      resizer.classList.remove('dragging');
      document.body.style.cursor = '';
    });
  },

  renderSqlTablesHtml(tables) {
    if (!Array.isArray(tables) || tables.length === 0) return '';
    return tables.map((tbl) => {
      const ths = (tbl.columns || []).map(col => `<th>${this.escapeHtml(col)}</th>`).join('');
      const trs = (tbl.rows || []).map(row =>
        `<tr>${row.map(cell => `<td>${this.escapeHtml(cell === null ? 'NULL' : cell)}</td>`).join('')}</tr>`
      ).join('');
      return `
        <div class="pz-sql-mini-table-wrap" style="margin-top: 8px;">
          <table class="pz-sql-table">
            <thead><tr>${ths}</tr></thead>
            <tbody>${trs || `<tr><td colspan="${(tbl.columns || []).length || 1}">(0 rows)</td></tr>`}</tbody>
          </table>
        </div>
      `;
    }).join('');
  },

  // ==========================================================
  // ERROR DETECTIVE PANEL
  // ==========================================================
  showErrorDetective(errorText, code, language) {
    const panel = document.getElementById('error-detective-panel');
    if (!panel || !window.ErrorDetective) return;

    const diag = window.ErrorDetective.diagnoseError(errorText, code, language);
    this._edContext = { errorText, code, language, diag, pendingFixCode: null };

    const titleEl = document.getElementById('ed-error-title');
    const rawEl = document.getElementById('ed-raw-error');
    const plainEl = document.getElementById('ed-plain-explanation');
    const uncertainEl = document.getElementById('ed-uncertain-note');
    const lineBtn = document.getElementById('ed-line-jump-btn');
    const respBox = document.getElementById('ed-response-box');
    const fixBox = document.getElementById('ed-fix-compare');

    if (titleEl) titleEl.textContent = diag.title;
    if (rawEl) rawEl.textContent = String(errorText || '');
    if (plainEl) plainEl.textContent = diag.plain;
    if (uncertainEl) {
      if (diag.uncertain) {
        uncertainEl.textContent = 'Uncertain diagnosis: ' + diag.hint;
        uncertainEl.hidden = false;
      } else {
        uncertainEl.hidden = true;
      }
    }
    if (lineBtn) {
      if (diag.lineNumber) {
        lineBtn.textContent = `Jump to line ${diag.lineNumber}`;
        lineBtn.dataset.line = String(diag.lineNumber);
        lineBtn.hidden = false;
      } else {
        lineBtn.hidden = true;
      }
    }
    if (respBox) respBox.hidden = true;
    if (fixBox) fixBox.hidden = true;
    panel.hidden = false;
  },

  hideErrorDetective() {
    const panel = document.getElementById('error-detective-panel');
    if (panel) panel.hidden = true;
    this._edContext = null;
  },

  async handleErrorDetectiveAction(action) {
    const ctx = this._edContext;
    if (!ctx) return;

    const respBox = document.getElementById('ed-response-box');
    const respMeta = document.getElementById('ed-response-meta');
    const respText = document.getElementById('ed-response-text');
    const fixBox = document.getElementById('ed-fix-compare');
    const diffView = document.getElementById('ed-diff-view');

    if (respBox) respBox.hidden = false;
    if (respMeta) respMeta.textContent = 'Checking Error Detective...';
    if (respText) respText.textContent = 'Analyzing your error...';
    if (fixBox) fixBox.hidden = true;

    const lessonContext = this.state.currentChallenge
      ? `${this.state.currentChallenge.title}: ${this.state.currentChallenge.prompt}`
      : (this.state.currentExample ? this.state.currentExample.title : null);

    let aiRes = null;
    try {
      aiRes = await API.requestErrorHelp({
        code: ctx.code,
        language: ctx.language,
        errorMessage: ctx.errorText,
        action,
        lessonContext
      });
    } catch (e) {
      aiRes = { ai_configured: false, source: 'builtin', message: '' };
    }

    if (aiRes && aiRes.source === 'gemini') {
      if (respMeta) respMeta.textContent = `Live AI Tutor (${action})`;
      if (respText) respText.textContent = aiRes.message;
      if (action === 'fix' && aiRes.suggested_code && aiRes.suggested_code !== ctx.code) {
        ctx.pendingFixCode = aiRes.suggested_code;
        if (diffView) diffView.innerHTML = window.ErrorDetective.buildLineDiffHtml(ctx.code, aiRes.suggested_code);
        if (fixBox) fixBox.hidden = false;
      }
      return;
    }

    // Built-in honest fallback when AI is not configured or unavailable
    const aiNotice = aiRes && aiRes.message
      ? aiRes.message
      : 'AI help is not configured on this server (no GEMINI_API_KEY). Showing built-in Error Detective analysis.';

    if (action === 'hint') {
      if (respMeta) respMeta.textContent = 'Built-in Hint • Live AI not configured';
      if (respText) respText.textContent = `${ctx.diag.hint}\n\nNote: ${aiNotice}`;
    } else if (action === 'explain') {
      if (respMeta) respMeta.textContent = 'Built-in Explanation • Live AI not configured';
      const lineInfo = ctx.diag.lineNumber ? `Look closely at line ${ctx.diag.lineNumber}. ` : '';
      if (respText) respText.textContent = `${ctx.diag.plain} ${lineInfo}${ctx.diag.hint}\n\nNote: ${aiNotice}`;
    } else if (action === 'fix') {
      if (ctx.diag.suggested && ctx.diag.suggested.code && ctx.diag.suggested.code !== ctx.code) {
        if (respMeta) respMeta.textContent = 'Built-in Suggested Fix • Review before applying';
        if (respText) respText.textContent = `${ctx.diag.suggested.note}\n\nNote: ${aiNotice}`;
        ctx.pendingFixCode = ctx.diag.suggested.code;
        if (diffView) diffView.innerHTML = window.ErrorDetective.buildLineDiffHtml(ctx.code, ctx.diag.suggested.code);
        if (fixBox) fixBox.hidden = false;
      } else {
        if (respMeta) respMeta.textContent = 'No automatic fix available • Built-in Error Detective';
        if (respText) respText.textContent = `Error Detective is not certain enough to auto-fix this error safely. ${ctx.diag.hint}\n\nNote: ${aiNotice}`;
      }
    }
  },

  applyErrorDetectiveFix() {
    const ctx = this._edContext;
    if (!ctx || !ctx.pendingFixCode || !window.editorManager) return;
    window.editorManager.setValue(ctx.pendingFixCode, ctx.language);
    const fixBox = document.getElementById('ed-fix-compare');
    if (fixBox) fixBox.hidden = true;
    ctx.pendingFixCode = null;
    const respText = document.getElementById('ed-response-text');
    if (respText) respText.textContent = 'Fix applied to the editor. Click Run ▶ to test your updated code.';
  },

  cancelErrorDetectiveFix() {
    const fixBox = document.getElementById('ed-fix-compare');
    if (fixBox) fixBox.hidden = true;
    if (this._edContext) this._edContext.pendingFixCode = null;
  },

  handleLanguageChange(lang) {
    this.state.currentLanguage = lang;
    window.editorManager.setLanguage(lang);
    this.syncCompilerChrome(lang);
    this.renderWorkspaceFiles(this.state.currentChallenge, lang);

    if (lang === 'html') {
      this.updateHtmlPreview(window.editorManager.getValue());
    }
  },

  updateHtmlPreview(htmlCode) {
    const frame = document.getElementById('html-preview-frame');
    if (frame) {
      frame.srcdoc = htmlCode;
    }
  },

  updateRuntimeBadge(lang) {
    const badge = document.getElementById('editor-runtime-badge');
    const warningBanner = document.getElementById('runtime-warning-banner');
    const warningText = document.getElementById('runtime-warning-text');
    const warningTitle = document.getElementById('runtime-warning-title');

    const rt = this.state.runtimes[lang] || { available: false, name: lang };
    const isBrowserJs = (lang === 'javascript' && !rt.available);
    const isCloudSupported = ['c', 'cpp', 'java', 'typescript', 'javascript'].includes(lang);
    const isExampleMode = this.state.workspaceMode === 'example';
    const isRunnable = Boolean(rt.available) || lang === 'html' || isBrowserJs || (isExampleMode && isCloudSupported);
    const runButton = document.getElementById('run-tests-btn');
    const submitButton = document.getElementById('submit-mission-btn');

    if (runButton) {
      runButton.disabled = !isRunnable;
      if (isExampleMode) {
        runButton.innerHTML = isRunnable ? (lang === 'sql' ? 'Run SQL ▶' : 'Run ▶') : 'View only';
        runButton.title = isRunnable ? 'Run your code (Ctrl+Enter)' : `${rt.name} compiler is not available.`;
      } else {
        runButton.innerHTML = 'Run Tests ▶';
        runButton.title = isRunnable ? 'Run the lab tests.' : (rt.description || `${rt.name} execution is unavailable on this server.`);
      }
    }
    if (submitButton) {
      submitButton.style.display = isExampleMode ? 'none' : 'inline-flex';
      submitButton.disabled = !rt.available;
      submitButton.title = rt.available ? 'Submit your verified solution.' : (rt.description || `${rt.name} execution is unavailable on this server.`);
    }

    if (badge) {
      if (rt.available) {
        badge.textContent = '● Ready';
        badge.style.color = 'var(--teal-success)';
        if (warningBanner) warningBanner.style.display = 'none';
      } else if (isBrowserJs) {
        badge.textContent = '● Ready (Browser Sandbox)';
        badge.style.color = 'var(--teal-success)';
        if (warningBanner) warningBanner.style.display = 'none';
      } else if (isExampleMode && isCloudSupported) {
        badge.textContent = '● Ready (Cloud Sandbox)';
        badge.style.color = 'var(--teal-success)';
        if (warningBanner) warningBanner.style.display = 'none';
      } else {
        badge.textContent = '⚪ Compiler not installed (View only)';
        badge.style.color = 'var(--text-muted)';
        if (warningBanner) {
          warningBanner.style.display = 'block';
          warningTitle.textContent = `${rt.name || lang} Not Installed (View only):`;
          warningText.textContent = `${rt.description || 'Toolchain is not installed on this server.'}`;
        }
      }
    }
  },

  switchRightTab(tabName) {
    this.state.activeRightTab = tabName;
    document.querySelectorAll('.right-tab-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.tab === tabName);
    });

    document.querySelectorAll('.right-tab-pane').forEach(p => {
      p.classList.remove('active');
    });

    const target = document.getElementById(`tab-pane-${tabName}`);
    if (target) target.classList.add('active');
  },

  async handleRunTests() {
    const code = window.editorManager.getValue();
    const lang = this.state.currentLanguage || 'python';
    const customInputEl = document.getElementById('custom-input-text');
    const stdinText = customInputEl ? customInputEl.value : '';

    // Standalone Online Compiler / Example Mode
    if (this.state.workspaceMode === 'example') {
      const runBtn = document.getElementById('run-tests-btn');
      if (runBtn) {
        runBtn.innerHTML = '⏳ Running...';
        runBtn.disabled = true;
      }
      try {
        if (lang === 'html') {
          this.updateHtmlPreview(code);
        }

        const rt = this.state.runtimes[lang] || { available: false };
        let res;
        if (lang === 'javascript' && !rt.available && window.ErrorDetective) {
          res = await window.ErrorDetective.runJavaScriptInBrowser(code);
        } else {
          res = await API.runCode(code, lang, stdinText);
        }

        const summaryBox = document.getElementById('test-summary-box');
        const container = document.getElementById('test-results-container');
        const hasError = Boolean(res.error) || res.success === false;

        if (summaryBox) summaryBox.style.display = 'none';

        if (container) {
          if (res.ran && !hasError) {
            const sqlTableHtml = (lang === 'sql' && res.tables && res.tables.length)
              ? this.renderSqlTablesHtml(res.tables)
              : '';
            container.innerHTML = `
              <div class="test-item-card passed">
                <div class="test-item-top">
                  <span class="test-name">${this.escapeHtml(res.runtime_label || lang)} Output</span>
                  <span style="font-size: 0.74rem; font-weight: 700; color: var(--teal-success);">✓ Success</span>
                </div>
                ${sqlTableHtml || `<pre class="example-output-pre" style="margin-top: 6px;">${this.escapeHtml(res.output || '(Program finished with no output)')}</pre>`}
              </div>
            `;
            this.hideErrorDetective();
          } else {
            const errText = res.error || res.message || 'Execution failed.';
            container.innerHTML = `
              <div class="test-item-card failed">
                <div class="test-item-top">
                  <span class="test-name">${res.mode_label === 'View only' ? 'View only' : 'Program Error'}</span>
                  <span style="font-size: 0.74rem; font-weight: 700; color: var(--red-error);">${this.escapeHtml(res.status_label || 'Error')}</span>
                </div>
                ${res.output ? `<pre class="example-output-pre" style="margin-top: 6px;">${this.escapeHtml(res.output)}</pre>` : ''}
                <pre class="example-output-pre live-output error" style="margin-top: 6px;">${this.escapeHtml(errText)}</pre>
              </div>
            `;
            if (res.mode_label !== 'View only') {
              this.showErrorDetective(errText, code, lang);
            } else {
              this.hideErrorDetective();
            }
          }
        }
        this.switchRightTab('output');
      } catch (err) {
        this.showErrorDetective(err.message || 'Execution error', code, lang);
      } finally {
        this.updateRuntimeBadge(lang);
      }
      return;
    }

    if (!this.state.currentChallenge) return;
    const challengeId = this.state.currentChallenge.id;

    const runBtn = document.getElementById('run-tests-btn');
    const originalText = runBtn.innerHTML;
    runBtn.innerHTML = `⏳ Running...`;
    runBtn.disabled = true;

    try {
      if (lang === 'html') {
        this.updateHtmlPreview(code);
      }

      const report = await API.submitAttempt(challengeId, code, lang);
      this.state.recentError = report.error_summary || null;
      this.renderAttemptResult(report);
      if (!report.passed && report.error_summary && report.runtime_available !== false) {
        this.showErrorDetective(report.error_summary, code, lang);
      } else {
        this.hideErrorDetective();
      }
      this.switchRightTab('output');

      await this.refreshStudentStats();

      if (report.passed) {
        this.displayPostChallengeRecap(this.state.currentChallenge);
        if (report.xp_earned > 0) {
          this.triggerConfetti();
        }
      }
    } catch (err) {
      alert(`Test run error: ${err.message}`);
    } finally {
      runBtn.innerHTML = originalText;
      runBtn.disabled = false;
    }
  },

  renderAttemptResult(report) {
    const summaryBox = document.getElementById('test-summary-box');
    summaryBox.style.display = 'flex';

    if (report.runtime_available === false) {
      summaryBox.className = 'output-summary-header runtime-unavailable';
      summaryBox.innerHTML = `
        <div>
          <strong style="font-size: 0.95rem;">⚠️ Language Runner Unavailable</strong>
          <div style="font-size: 0.75rem; color: #78350F; margin-top: 2px;">
            ${report.feedback || 'This language cannot run on the server right now.'}
          </div>
        </div>
        <div><span style="font-size: 1.2rem;">⚙️</span></div>
      `;
    } else {
      summaryBox.className = `output-summary-header ${report.passed ? 'passed' : 'failed'}`;
      summaryBox.innerHTML = `
        <div>
          <strong style="font-size: 0.95rem;">${report.passed ? '✓ All Tests Passed' : '⚠️ Some Tests Failed'}</strong>
          <div style="font-size: 0.75rem; margin-top: 2px;">
            ${report.passed
              ? (report.xp_earned > 0 ? `+${report.xp_earned} XP earned` : 'All checks passed')
              : 'Review the test details below and try again.'}
          </div>
        </div>
        <div>
          <span style="font-size: 1.2rem;">${report.passed ? '🎉' : '❌'}</span>
        </div>
      `;
    }

    const container = document.getElementById('test-results-container');
    const details = report.details || [];

    if (details.length > 0) {
      container.innerHTML = details.map(d => `
        <div class="test-item-card ${d.passed ? 'passed' : 'failed'}">
          <div class="test-item-top">
            <span class="test-name">${d.name}</span>
            <span style="font-size: 0.75rem; font-weight: 700; color: ${d.passed ? 'var(--teal-success)' : 'var(--red-error)'}">
              ${d.passed ? 'PASS' : 'FAIL'}
            </span>
          </div>
          <div class="test-msg">${d.error || 'Test passed.'}</div>
        </div>
      `).join('');
    } else {
      container.innerHTML = `
        <div class="test-item-card ${report.passed ? 'passed' : 'failed'}">
          <div class="test-item-top">
            <span class="test-name">Test Results</span>
            <span style="font-size: 0.75rem; font-weight: 700; color: ${report.passed ? 'var(--teal-success)' : 'var(--red-error)'}">
              ${report.passed ? 'PASS' : 'FAIL'}
            </span>
          </div>
          <div class="test-msg">${report.feedback}</div>
          ${!report.passed ? `<div class="test-error-callout">${report.error_summary || 'Click Help (Lab Guide) to review the exercise instructions.'}</div>` : ''}
        </div>
      `;
    }
  },

  displayPostChallengeRecap(challenge) {
    const recapContainer = document.getElementById('concept-recap-container');
    const recapText = document.getElementById('concept-recap-text');
    const relCard = document.getElementById('related-challenge-card');
    const relTitle = document.getElementById('related-challenge-title');
    const relBtn = document.getElementById('related-challenge-btn');

    if (!recapContainer) return;
    recapContainer.style.display = 'block';

    const defaultRecap = "Great job! You validated constraints and solved this engineering problem cleanly.";
    recapText.textContent = challenge.concept_recap || defaultRecap;

    const relId = challenge.related_challenge_id;
    const relChallenge = relId ? this.state.challenges.find(c => c.id === relId) : null;

    if (relChallenge && relCard && relTitle && relBtn) {
      relCard.style.display = 'flex';
      relTitle.textContent = `${relChallenge.title} (${relChallenge.skill_tag})`;
      relBtn.dataset.challengeId = relChallenge.id;
    } else if (relCard) {
      relCard.style.display = 'none';
    }
  },

  async refreshStudentStats() {
    try {
      this.state.studentProgress = await API.getStudentProgress();
      this.renderUserBadge();
      this.renderDashboard();
    } catch (e) {
      console.warn('Failed to refresh student stats:', e);
    }
  },

  async fetchAndDisplayHint(level) {
    if (!this.state.currentChallenge) return;
    const challengeId = this.state.currentChallenge.id;
    const code = window.editorManager.getValue();

    const hint = await API.requestHint(challengeId, code, this.state.recentError, level);
    
    this.state.unlockedHints.add(level);
    document.querySelectorAll('.hint-step-btn').forEach(b => {
      const bLvl = parseInt(b.dataset.level, 10);
      b.classList.toggle('unlocked', this.state.unlockedHints.has(bLvl));
    });

    let stageTitle = "Step 1: Guided Question";
    if (hint.hint_type === "clue") stageTitle = "Step 2: Clearer Hint & Clue";
    if (hint.hint_type === "explanation") stageTitle = "Step 3: Conceptual Explanation";

    const titleEl = document.getElementById('hint-level-title');
    if (titleEl) titleEl.textContent = stageTitle;
    const contentEl = document.getElementById('hint-content-text');
    if (contentEl) contentEl.innerHTML = hint.message.replace(/\n/g, '<br/>');
  },

  async handleAskCoach() {
    if (!this.state.currentChallenge) return;
    const input = document.getElementById('coach-question-input');
    const question = input ? input.value.trim() : '';
    if (!question) return;

    const historyBox = document.getElementById('coach-chat-history');
    const askButton = document.getElementById('coach-ask-btn');
    
    // Add user question bubble
    const userMsg = document.createElement('div');
    userMsg.className = 'chat-bubble-user';
    userMsg.innerHTML = `<div class="bubble-content">${this.escapeHtml(question)}</div>`;
    if (historyBox) historyBox.appendChild(userMsg);
    if (input) input.value = '';
    if (askButton) {
      askButton.disabled = true;
      askButton.textContent = 'Thinking…';
    }

    const code = window.editorManager ? window.editorManager.getValue() : '';
    const lang = this.state.currentLanguage || 'python';
    const coachMsg = document.createElement('div');
    coachMsg.className = 'chat-bubble-ai';
    coachMsg.innerHTML = `
      <div class="ai-avatar">🪄</div>
      <div class="bubble-content">
        <em>AI Mentor is thinking…</em>
      </div>
    `;
    if (historyBox) {
      historyBox.appendChild(coachMsg);
      historyBox.scrollTop = historyBox.scrollHeight;
    }

    try {
      const ans = await API.askCoach(this.state.currentChallenge.id, code, question, lang, this.state.recentError);
      const bubble = coachMsg.querySelector('.bubble-content');
      if (bubble) {
        bubble.replaceChildren();
        const responseText = document.createElement('div');
        responseText.textContent = ans.explanation || 'Try asking a more specific question about the task or error.';
        responseText.style.whiteSpace = 'pre-wrap';
        bubble.appendChild(responseText);

        if (ans.recommendation) {
          const nextStep = document.createElement('div');
          nextStep.style.cssText = 'color: var(--indigo-primary); font-size: 0.76rem; font-weight: 600; margin-top: 6px;';
          nextStep.textContent = `💡 Next Step: ${ans.recommendation}`;
          bubble.appendChild(nextStep);
        }

        // Add interactive follow-up chips
        const chips = document.createElement('div');
        chips.className = 'chat-reaction-pills';
        chips.innerHTML = `
          <button type="button" class="reaction-pill-btn" onclick="App.handleCoachHelpfulFeedback(this)">👍 That helped!</button>
          <button type="button" class="reaction-pill-btn" onclick="App.quickAskCoach('Can you give me an even simpler clue?')">❓ Still stuck</button>
          <button type="button" class="reaction-pill-btn" onclick="App.quickAskCoach('Show a tiny syntax example')">📝 Syntax sample</button>
        `;
        bubble.appendChild(chips);
      }

      const status = document.getElementById('coach-service-status');
      if (status && ans.ai_available === false) {
        status.textContent = ans.ai_configured
          ? 'Live AI is unavailable right now; built-in tutoring is being used.'
          : 'Built-in hints are active. Add GEMINI_API_KEY on the server for live AI.';
        status.style.color = 'var(--amber-hint)';
      }
    } catch (error) {
      const bubble = coachMsg.querySelector('.bubble-content');
      if (bubble) {
        bubble.textContent = `I could not reach the tutor service. Your code was not changed. ${error.message}`;
      }
    } finally {
      if (askButton) {
        askButton.disabled = false;
        askButton.textContent = 'Ask';
      }
      if (historyBox) historyBox.scrollTop = historyBox.scrollHeight;
    }
  },

  handleCoachHelpfulFeedback(btn) {
    if (btn) {
      btn.textContent = '✓ Awesome!';
      btn.style.background = 'var(--teal-light)';
      btn.style.color = 'var(--teal-success)';
      btn.disabled = true;
    }
  },

  openWorkspaceAndAskCoach() {
    this.switchView('workspace');
    this.switchRightTab('guide');
  },

  quickAskCoach(prompt) {
    const input = document.getElementById('coach-question-input');
    if (input) {
      input.value = prompt;
      this.handleAskCoach();
    }
  },

  clearCoachChat() {
    const historyBox = document.getElementById('coach-chat-history');
    if (historyBox) {
      historyBox.replaceChildren();
      this.renderCoachWelcomeMessage();
    }
  },

  renderCoachWelcomeMessage() {
    const historyBox = document.getElementById('coach-chat-history');
    if (!historyBox) return;
    const title = (this.state.currentChallenge && this.state.currentChallenge.title) || 'this lab';
    const welcome = document.createElement('div');
    welcome.className = 'chat-bubble-ai';
    welcome.innerHTML = `
      <div class="ai-avatar">🪄</div>
      <div class="bubble-content">
        <strong>AI Mentor:</strong> Hi! I'm here to tutor you through <em>${this.escapeHtml(title)}</em>. What's on your mind?
        <div class="chat-reaction-pills">
          <button type="button" class="reaction-pill-btn" onclick="App.quickAskCoach('What is the goal of this lab?')">🎯 Goal</button>
          <button type="button" class="reaction-pill-btn" onclick="App.quickAskCoach('What edge cases should I think about?')">⚠️ Edge Cases</button>
          <button type="button" class="reaction-pill-btn" onclick="App.fetchAndDisplayHint(1)">💡 Hint 1</button>
        </div>
      </div>
    `;
    historyBox.appendChild(welcome);
  },

  initTheme() {
    const saved = localStorage.getItem('cm_theme') || 'light';
    this.setTheme(saved);

    const bindToggle = (btnId) => {
      const btn = document.getElementById(btnId);
      if (btn) {
        btn.addEventListener('click', (e) => {
          e.preventDefault();
          const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
          this.setTheme(isDark ? 'light' : 'dark');
        });
      }
    };
    bindToggle('theme-toggle-btn');
    bindToggle('theme-toggle-unauth-btn');
  },

  setTheme(themeName) {
    if (themeName === 'dark') {
      document.documentElement.setAttribute('data-theme', 'dark');
      localStorage.setItem('cm_theme', 'dark');
      const i1 = document.getElementById('theme-icon');
      const i2 = document.getElementById('theme-icon-unauth');
      if (i1) i1.textContent = '☀️';
      if (i2) i2.textContent = '☀️';
    } else {
      document.documentElement.removeAttribute('data-theme');
      localStorage.setItem('cm_theme', 'light');
      const i1 = document.getElementById('theme-icon');
      const i2 = document.getElementById('theme-icon-unauth');
      if (i1) i1.textContent = '🌙';
      if (i2) i2.textContent = '🌙';
    }
    if (window.editorManager && typeof window.editorManager.setTheme === 'function') {
      window.editorManager.setTheme(themeName);
    }
  },

  async handleSubmitMission() {
    if (!this.state.currentChallenge) return;
    const code = window.editorManager.getValue();

    try {
      const res = await API.submitMission(this.state.currentChallenge.id, code, "", this.state.currentLanguage || 'python');
      this.triggerConfetti();
      alert(`🎉 Lab Solution Verified & Recorded!\n\n${res.message}`);
      
      await this.loadInitialData();
      this.switchView('dashboard');
    } catch (err) {
      alert(`Submission check: ${err.message}`);
    }
  },

  async renderSkillProof() {
    const data = await API.getSkillProof();
    const badgesContainer = document.getElementById('skill-badges-container');
    if (!badgesContainer) return;
    badgesContainer.innerHTML = '';

    const evidence = data.evidence_records || [];
    if (evidence.length === 0) {
      badgesContainer.innerHTML = `
        <div style="color: var(--text-muted); font-size: 0.9rem; padding: 20px 0;">
          No verified labs completed yet. Complete a challenge in the workspace to earn verified SkillProof badges.
        </div>
      `;
      return;
    }

    evidence.forEach(ev => {
      const badge = document.createElement('div');
      badge.className = 'skill-badge-card';
      badge.innerHTML = `
        <div class="badge-seal">🛡️</div>
        <div class="badge-info">
          <h4>${ev.skill_name}</h4>
          <p>${ev.description}</p>
          <div class="verified-tag">✓ Verified Score: ${ev.score}%</div>
        </div>
      `;
      badgesContainer.appendChild(badge);
    });
  },

  async renderLearningReport() {
    const prog = await API.getStudentProgress();
    const reportName = document.getElementById('report-student-name');
    const reportId = document.getElementById('report-student-id');
    const reportDate = document.getElementById('report-date');
    const tbody = document.getElementById('report-tasks-tbody');

    if (reportName) reportName.textContent = (this.state.account && this.state.account.display_name) || prog.display_name || 'PixelPioneer';
    if (reportId) reportId.textContent = (this.state.account && this.state.account.id) || prog.student_id;
    if (reportDate) reportDate.textContent = new Date().toLocaleDateString();

    if (!tbody) return;
    tbody.innerHTML = '';

    const completed = prog.completed_challenges || [];
    if (completed.length === 0) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center; color:#64748b; padding: 20px;">No labs completed yet for this student profile. Complete a challenge in the workspace to populate this official report.</td></tr>`;
      return;
    }

    completed.forEach(t => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${t.title}</strong></td>
        <td>${t.skill_tag}</td>
        <td>Intermediate</td>
        <td>+${t.xp_awarded} XP</td>
        <td><span style="color: var(--teal-success); font-weight:700;">VERIFIED</span> (${t.completed_at || 'Recent'})</td>
      `;
      tbody.appendChild(tr);
    });
  },

  // ==========================================================
  // SITE OWNER & ADMIN CONSOLE
  // ==========================================================
  switchAdminTab(tabName) {
    this.state.activeAdminTab = tabName;
    document.querySelectorAll('.admin-nav-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.adminTab === tabName);
    });

    document.querySelectorAll('.admin-pane').forEach(p => {
      p.classList.remove('active');
    });

    const target = document.getElementById(`admin-pane-${tabName}`);
    if (target) target.classList.add('active');
  },

  async renderAdminView() {
    if (!this.state.isAuthenticated || !this.isStaffRole(this.state.account)) {
      return;
    }
    await this.renderAdminOverview();
    await this.renderAdminClasses();
    await this.renderAdminStudents(this.state.adminStudentSearchQuery || '');
    await this.renderAdminChallenges();
    if (this.getAccountRole() === 'owner') {
      await this.renderAdminSettings();
    }
  },

  async renderAdminStudents(query = '') {
    try {
      const data = await API.getAdminStudents(query);
      const students = data.students || [];
      this.state.adminStudents = students;

      const countBadge = document.getElementById('admin-students-count-badge');
      if (countBadge) {
        countBadge.textContent = `${students.length} ${students.length === 1 ? 'student' : 'students'}`;
      }

      const tbody = document.getElementById('admin-students-tbody');
      if (!tbody) return;
      tbody.innerHTML = '';

      if (students.length === 0) {
        tbody.innerHTML = `
          <tr>
            <td colspan="6" style="text-align: center; color: var(--text-muted); padding: 18px;">
              No students matched "${this.escapeHtml(query)}". Try searching by name, email, or student ID.
            </td>
          </tr>
        `;
        return;
      }

      const isStaff = this.isStaffRole(this.state.account);

      students.forEach(s => {
        const tr = document.createElement('tr');
        const isSelected = this.state.selectedAdminStudentId === s.id;
        if (isSelected) {
          tr.style.background = 'rgba(79, 70, 229, 0.06)';
        }

        const spCount = s.skillproof_count ?? s.completed_count ?? 0;
        const assignedProgs = s.assigned_programs || [];
        const progSummaryHtml = assignedProgs.length > 0
          ? `<div style="display: flex; gap: 4px; flex-wrap: wrap; margin-top: 4px;">
              ${assignedProgs.map(p => `<span class="diff-badge" style="font-size: 0.7rem; padding: 2px 6px;" title="${this.escapeHtml(p.name)}: ${this.escapeHtml(p.status)}">${p.icon || ''} ${this.escapeHtml(p.name)}</span>`).join('')}
            </div>`
          : `<div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 3px;">No assigned programs</div>`;

        tr.innerHTML = `
          <td data-label="Student">
            <strong style="color: var(--text-primary); font-size: 0.88rem;">${this.escapeHtml(s.display_name)}</strong>
            <div style="font-family: var(--font-mono); font-size: 0.74rem; color: var(--text-muted);">${this.escapeHtml(s.id)}</div>
          </td>
          <td data-label="Email"><span style="font-size: 0.82rem; color: var(--text-secondary); word-break: break-all;">${this.escapeHtml(s.email || '—')}</span></td>
          <td data-label="Class"><span class="diff-badge">${this.escapeHtml(s.class_name || s.class_id || 'Unassigned')}</span></td>
          <td data-label="Progress">
            <div>
              <strong style="color: var(--indigo-primary); white-space: nowrap;">Lvl ${s.level || 1}</strong>
              <span style="font-size: 0.78rem; color: var(--text-secondary); white-space: nowrap;">(${s.total_xp || 0} XP • ${s.completed_count || 0} labs)</span>
            </div>
            ${progSummaryHtml}
          </td>
          <td data-label="SkillProof Records">
            <span class="toolchain-pill ${spCount > 0 ? 'available' : 'missing'}" style="white-space: nowrap;">
              🛡️ ${spCount} Verified
            </span>
          </td>
          <td class="student-actions-cell" data-label="Actions">
            <div class="student-actions-group">
              <button type="button" class="btn btn-primary btn-view-student-profile" data-student-id="${this.escapeHtml(s.id)}">
                View profile
              </button>
              ${isStaff ? `
                <button type="button" class="btn btn-secondary btn-edit-student-dir" data-student-id="${this.escapeHtml(s.id)}">
                  Edit
                </button>
              ` : ''}
            </div>
          </td>
        `;

        tr.querySelector('.btn-view-student-profile').addEventListener('click', () => {
          this.openAdminStudentProfile(s.id);
        });

        const editBtn = tr.querySelector('.btn-edit-student-dir');
        if (editBtn) {
          editBtn.addEventListener('click', () => {
            this.openStudentEditorModal(s);
          });
        }

        tbody.appendChild(tr);
      });

      // Automatically open the first student's profile if none is currently displayed
      if (!this.state.selectedAdminStudentId && students.length > 0) {
        await this.openAdminStudentProfile(students[0].id);
      } else if (this.state.selectedAdminStudentId && students.some(s => s.id === this.state.selectedAdminStudentId)) {
        await this.openAdminStudentProfile(this.state.selectedAdminStudentId);
      }
    } catch (e) {
      console.error('Failed to load admin students directory:', e);
    }
  },

  async openAdminStudentProfile(studentId) {
    try {
      this.state.selectedAdminStudentId = studentId;
      const data = await API.getAdminStudentProfile(studentId);
      const stu = data.student;
      if (!stu) return;

      const emptyEl = document.getElementById('admin-student-profile-empty');
      const contentEl = document.getElementById('admin-student-profile-content');
      if (emptyEl) emptyEl.style.display = 'none';
      if (contentEl) contentEl.style.display = 'block';

      const avatarEl = document.getElementById('admin-prof-avatar');
      if (avatarEl && stu.display_name) {
        const parts = stu.display_name.split(' ');
        avatarEl.textContent = parts.length > 1
          ? (parts[0][0] + parts[1][0]).toUpperCase()
          : parts[0].slice(0, 2).toUpperCase();
      }

      const nameEl = document.getElementById('admin-prof-name');
      if (nameEl) nameEl.textContent = stu.display_name;

      const emailEl = document.getElementById('admin-prof-email');
      if (emailEl) emailEl.textContent = stu.email || 'No email on file';

      const idEl = document.getElementById('admin-prof-id');
      if (idEl) idEl.textContent = stu.id;

      const classEl = document.getElementById('admin-prof-class');
      if (classEl) classEl.textContent = stu.class_name || stu.class_id || 'Unassigned';

      const lvlEl = document.getElementById('admin-prof-level');
      if (lvlEl) lvlEl.textContent = `Lvl ${stu.level || 1}`;

      const xpEl = document.getElementById('admin-prof-xp');
      if (xpEl) xpEl.textContent = `${stu.total_xp || 0} XP`;

      const records = data.skillproof_records || [];
      const legacyEvidence = data.evidence_records || [];
      const totalVerified = records.length + legacyEvidence.length;
      const assignedPrograms = data.assigned_programs || stu.assigned_programs || [];
      const catalogPrograms = data.available_catalog_programs || [];
      this.state.selectedAdminStudentProfile = { ...stu, assigned_programs: assignedPrograms };

      const completedLabsEl = document.getElementById('admin-prof-completed-labs');
      if (completedLabsEl) completedLabsEl.textContent = String(stu.completed_count ?? records.length);

      const progCountEl = document.getElementById('admin-prof-programs-count');
      if (progCountEl) progCountEl.textContent = String(assignedPrograms.length);

      const spCountEl = document.getElementById('admin-prof-skillproof-count');
      if (spCountEl) spCountEl.textContent = String(totalVerified);

      // Staff quick-edit button inside profile header
      const ownerActions = document.getElementById('admin-prof-owner-actions');
      if (ownerActions) {
        ownerActions.innerHTML = '';
        if (this.isStaffRole(this.state.account)) {
          const editBtn = document.createElement('button');
          editBtn.type = 'button';
          editBtn.id = 'admin-prof-edit-btn';
          editBtn.className = 'btn btn-secondary';
          editBtn.style.cssText = 'padding: 5px 10px; font-size: 0.76rem; white-space: nowrap;';
          editBtn.textContent = 'Edit Profile';
          editBtn.addEventListener('click', () => this.openStudentEditorModal(this.state.selectedAdminStudentProfile));
          ownerActions.appendChild(editBtn);
        }
      }

      // Populate Assign Program select & Assigned Learning Programs list
      const assignSelect = document.getElementById('admin-assign-program-select');
      if (assignSelect && catalogPrograms.length > 0) {
        assignSelect.innerHTML = catalogPrograms.map(cp => `
          <option value="${this.escapeHtml(cp.language_id)}">
            ${cp.icon || '💻'} ${this.escapeHtml(cp.name)} ${cp.is_assigned ? '(Assigned)' : ''}
          </option>
        `).join('');
        const firstUnassigned = catalogPrograms.find(cp => !cp.is_assigned);
        if (firstUnassigned) assignSelect.value = firstUnassigned.language_id;
      }

      const progListEl = document.getElementById('admin-prof-programs-list');
      if (progListEl) {
        if (assignedPrograms.length === 0) {
          progListEl.innerHTML = `
            <div style="padding: 12px; background: #FFFFFF; border: 1px solid var(--border-color); border-radius: var(--radius-sm); color: var(--text-muted); font-size: 0.83rem;">
              No learning programs assigned yet. Choose a language above and click <strong>+ Assign Program</strong>.
            </div>
          `;
        } else {
          progListEl.innerHTML = assignedPrograms.map(p => {
            const statusStyle = p.status === 'Completed'
              ? 'background: var(--teal-light); color: var(--teal-success);'
              : (p.status === 'In Progress'
                ? 'background: rgba(79, 70, 229, 0.12); color: var(--indigo-primary);'
                : 'background: var(--amber-light); color: var(--amber-hint);');
            const detailText = p.total_labs > 0
              ? `${p.completed_labs} / ${p.total_labs} labs completed (${p.progress_percent}%)`
              : `${p.lessons_count || 4} lessons • ${p.examples_count || 6} examples`;
            return `
              <div class="admin-assigned-program-item" data-language-id="${this.escapeHtml(p.language_id)}" style="padding: 10px 12px; background: #FFFFFF; border: 1px solid var(--border-color); border-radius: var(--radius-sm); display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 180px;">
                  <div style="display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                    <strong style="color: var(--text-primary); font-size: 0.88rem;">${p.icon || '💻'} ${this.escapeHtml(p.name)}</strong>
                    <span class="diff-badge" style="${statusStyle} font-size: 0.72rem;">${this.escapeHtml(p.status)}</span>
                  </div>
                  <div style="font-size: 0.76rem; color: var(--text-secondary); margin-top: 3px;">
                    ${this.escapeHtml(detailText)}
                  </div>
                  <div class="progress-bar-bg" style="height: 6px; margin-top: 6px; max-width: 240px;">
                    <div class="progress-bar-fill" style="width: ${p.progress_percent || 0}%;"></div>
                  </div>
                </div>
                <button type="button" class="btn btn-secondary btn-remove-student-program" data-language-id="${this.escapeHtml(p.language_id)}" style="padding: 4px 10px; font-size: 0.75rem; color: var(--red-error); white-space: nowrap; flex-shrink: 0;">
                  Remove
                </button>
              </div>
            `;
          }).join('');

          progListEl.querySelectorAll('.btn-remove-student-program').forEach(btn => {
            btn.addEventListener('click', () => {
              this.handleRemoveStudentProgram(studentId, btn.dataset.languageId);
            });
          });
        }
      }

      // Render Verified SkillProof records
      const spListEl = document.getElementById('admin-prof-skillproof-list');
      if (spListEl) {
        if (records.length === 0 && legacyEvidence.length === 0) {
          spListEl.innerHTML = `
            <div style="padding: 14px; background: var(--bg-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-sm); color: var(--text-muted); font-size: 0.84rem;">
              No verified SkillProof records yet for this student.
            </div>
          `;
        } else {
          const challengeCards = records.map(r => `
            <div class="skillproof-record-card">
              <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; flex-wrap: wrap;">
                <div>
                  <strong style="color: var(--text-primary); font-size: 0.88rem;">🛡️ ${this.escapeHtml(r.title)}</strong>
                  <div style="font-size: 0.76rem; color: var(--text-secondary); margin-top: 2px;">
                    Skill: <strong>${this.escapeHtml(r.skill_tag)}</strong> • Language: ${this.escapeHtml(r.execution_language || 'python')} • ${this.escapeHtml(r.difficulty || 'Beginner')}
                  </div>
                </div>
                <span class="toolchain-pill available">✓ Verified (+${r.xp_awarded} XP)</span>
              </div>
              <div style="font-size: 0.73rem; color: var(--text-muted); margin-top: 6px;">
                ${this.escapeHtml(r.verification_source || 'Automated Sandbox Test Suite')} • Completed: ${this.escapeHtml(r.completed_at || 'Verified')}
              </div>
            </div>
          `).join('');

          const evidenceCards = legacyEvidence.map(ev => `
            <div class="skillproof-record-card">
              <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; flex-wrap: wrap;">
                <div>
                  <strong style="color: var(--text-primary); font-size: 0.88rem;">🛡️ ${this.escapeHtml(ev.skill_name)}</strong>
                  <div style="font-size: 0.76rem; color: var(--text-secondary); margin-top: 2px;">
                    ${this.escapeHtml(ev.description || '')}
                  </div>
                </div>
                <span class="toolchain-pill available">✓ Score: ${ev.score}%</span>
              </div>
            </div>
          `).join('');

          spListEl.innerHTML = challengeCards + evidenceCards;
        }
      }

      // Render Recent Sandbox Attempts
      const attListEl = document.getElementById('admin-prof-attempts-list');
      if (attListEl) {
        const attempts = data.recent_attempts || [];
        if (attempts.length === 0) {
          attListEl.innerHTML = `
            <div style="padding: 12px; background: var(--bg-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-sm); color: var(--text-muted); font-size: 0.82rem;">
              No sandbox test attempts recorded yet.
            </div>
          `;
        } else {
          attListEl.innerHTML = attempts.slice(0, 5).map(a => `
            <div style="padding: 9px 12px; background: var(--bg-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-sm); display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 0.8rem;">
              <div>
                <strong style="color: var(--text-primary);">${this.escapeHtml(a.challenge_title)}</strong>
                <div style="font-size: 0.73rem; color: var(--text-muted);">${this.escapeHtml(a.created_at || '')}</div>
              </div>
              <span class="diff-badge" style="background: ${a.passed ? 'var(--teal-light)' : 'var(--red-light)'}; color: ${a.passed ? 'var(--teal-success)' : 'var(--red-error)'};">
                ${a.passed ? 'PASS' : 'FAIL'}
              </span>
            </div>
          `).join('');
        }
      }
    } catch (e) {
      console.error('Failed to open student profile:', e);
    }
  },

  async handleAssignStudentProgram() {
    const studentId = this.state.selectedAdminStudentId;
    const selectEl = document.getElementById('admin-assign-program-select');
    if (!studentId || !selectEl || !selectEl.value) return;

    try {
      await API.assignStudentProgram(studentId, selectEl.value);
      await this.openAdminStudentProfile(studentId);
      await this.renderAdminStudents(this.state.adminStudentSearchQuery || '');
      await this.renderAdminOverview();
    } catch (e) {
      alert(`Could not assign learning program: ${e.message}`);
    }
  },

  async handleRemoveStudentProgram(studentId, languageId) {
    if (!studentId || !languageId) return;
    try {
      await API.removeStudentProgram(studentId, languageId);
      await this.openAdminStudentProfile(studentId);
      await this.renderAdminStudents(this.state.adminStudentSearchQuery || '');
      await this.renderAdminOverview();
    } catch (e) {
      alert(`Could not remove learning program: ${e.message}`);
    }
  },

  async renderAdminOverview() {
    try {
      const overview = await API.getAdminOverview();
      const metrics = overview.metrics || overview;
      const studentsEl = document.getElementById('admin-total-students');
      const activeProgsEl = document.getElementById('admin-active-programs');
      const completedLabsEl = document.getElementById('admin-completed-labs');
      const classesEl = document.getElementById('admin-total-classes');
      const attemptsEl = document.getElementById('admin-total-attempts');
      const passRateEl = document.getElementById('admin-pass-rate');
      if (studentsEl) studentsEl.textContent = metrics.total_students ?? 0;
      if (activeProgsEl) activeProgsEl.textContent = metrics.active_programs ?? 0;
      if (completedLabsEl) completedLabsEl.textContent = metrics.completed_labs ?? 0;
      if (classesEl) classesEl.textContent = metrics.total_classes ?? 0;
      if (attemptsEl) attemptsEl.textContent = metrics.total_attempts ?? 0;
      if (passRateEl) passRateEl.textContent = `${metrics.overall_pass_rate ?? 100}%`;

      // Render Active Programs Enrollment Summary
      const progEnrollEl = document.getElementById('admin-program-enrollment-list');
      if (progEnrollEl) {
        const progSummary = overview.program_summary || [];
        if (progSummary.length === 0) {
          progEnrollEl.innerHTML = `<div style="color: var(--text-muted); font-size: 0.83rem;">No active programs found.</div>`;
        } else {
          progEnrollEl.innerHTML = progSummary.map(item => `
            <div style="padding: 8px 12px; background: var(--bg-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-sm); display: flex; justify-content: space-between; align-items: center; gap: 8px; font-size: 0.82rem;">
              <strong style="color: var(--text-primary);">${item.icon || '💻'} ${this.escapeHtml(item.name)}</strong>
              <div style="display: flex; gap: 6px; align-items: center; flex-wrap: wrap;">
                <span class="diff-badge" style="background: rgba(79, 70, 229, 0.1); color: var(--indigo-primary);">
                  ${item.enrolled_students || 0} ${item.enrolled_students === 1 ? 'student' : 'students'}
                </span>
                <span class="diff-badge" style="background: var(--teal-light); color: var(--teal-success);">
                  ${item.completed_labs || 0} labs done
                </span>
              </div>
            </div>
          `).join('');
        }
      }

      // Render Recent Student Progress Feed
      const recentListEl = document.getElementById('admin-recent-progress-list');
      if (recentListEl) {
        const recent = overview.recent_progress || [];
        if (recent.length === 0) {
          recentListEl.innerHTML = `
            <div style="padding: 12px; background: var(--bg-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-sm); color: var(--text-muted); font-size: 0.83rem;">
              No completed labs recorded yet.
            </div>
          `;
        } else {
          recentListEl.innerHTML = recent.map(r => `
            <div style="padding: 9px 12px; background: var(--bg-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-sm); display: flex; justify-content: space-between; align-items: center; gap: 10px; flex-wrap: wrap; font-size: 0.82rem;">
              <div>
                <div>
                  <strong style="color: var(--text-primary);">${this.escapeHtml(r.student_name)}</strong>
                  <span style="color: var(--text-muted); font-size: 0.75rem;">(${this.escapeHtml(r.class_name || 'Unassigned')})</span>
                </div>
                <div style="color: var(--text-secondary); font-size: 0.78rem; margin-top: 2px;">
                  ${r.program_icon || '💻'} <strong>${this.escapeHtml(r.program_name || r.language_id)}</strong> — ${this.escapeHtml(r.challenge_title)}
                </div>
              </div>
              <div style="display: flex; align-items: center; gap: 8px;">
                <span class="diff-badge" style="background: var(--teal-light); color: var(--teal-success);">+${r.xp_awarded || 0} XP</span>
                <button type="button" class="btn btn-secondary btn-recent-open-student" data-student-id="${this.escapeHtml(r.student_id)}" style="padding: 4px 8px; font-size: 0.74rem; white-space: nowrap;">
                  View profile
                </button>
              </div>
            </div>
          `).join('');

          recentListEl.querySelectorAll('.btn-recent-open-student').forEach(btn => {
            btn.addEventListener('click', () => {
              this.switchAdminTab('students');
              this.openAdminStudentProfile(btn.dataset.studentId);
            });
          });
        }
      }

      const topics = overview.common_errors || overview.common_error_topics || [];
      this.state.adminErrorTopics = topics;
      this.state.adminErrorIsSampleData = Boolean(overview.is_sample_data);
      this.state.adminErrorStatusLabel = overview.telemetry_status_label || (overview.is_sample_data ? 'Sample Data' : 'Aggregated Sandbox Data');

      const sourceBadge = document.getElementById('admin-errors-source-badge');
      if (sourceBadge) {
        sourceBadge.textContent = this.state.adminErrorStatusLabel;
        if (this.state.adminErrorIsSampleData) {
          sourceBadge.style.background = 'rgba(245, 158, 11, 0.14)';
          sourceBadge.style.color = '#B45309';
        } else {
          sourceBadge.style.background = 'rgba(79, 70, 229, 0.1)';
          sourceBadge.style.color = 'var(--indigo-primary)';
        }
      }

      const noteEl = document.getElementById('admin-errors-note');
      if (noteEl && overview.telemetry_note) {
        noteEl.textContent = overview.telemetry_note;
      }

      // Populate Challenge filter options
      const challengeFilterEl = document.getElementById('admin-error-challenge-filter');
      if (challengeFilterEl) {
        const seenChallenges = new Map();
        topics.forEach(item => {
          const chKey = item.challenge_id || item.challenge_title;
          const chTitle = item.challenge_title || item.challenge_id || 'General Challenge';
          if (chKey && !seenChallenges.has(chKey)) {
            seenChallenges.set(chKey, chTitle);
          }
        });
        const currentChVal = this.state.adminErrorChallengeFilter || 'all';
        let chOptionsHtml = '<option value="all">All challenges &amp; lessons</option>';
        seenChallenges.forEach((title, key) => {
          chOptionsHtml += `<option value="${this.escapeHtml(key)}">${this.escapeHtml(title)}</option>`;
        });
        challengeFilterEl.innerHTML = chOptionsHtml;
        if (currentChVal !== 'all' && seenChallenges.has(currentChVal)) {
          challengeFilterEl.value = currentChVal;
        } else {
          this.state.adminErrorChallengeFilter = 'all';
          challengeFilterEl.value = 'all';
        }
      }

      // Populate Category filter options
      const categoryFilterEl = document.getElementById('admin-error-category-filter');
      if (categoryFilterEl) {
        const categories = Array.from(new Set(topics.map(item => item.error_category || 'Runtime / Test Failure').filter(Boolean)));
        const currentCatVal = this.state.adminErrorCategoryFilter || 'all';
        let catOptionsHtml = '<option value="all">All categories</option>';
        categories.forEach(cat => {
          catOptionsHtml += `<option value="${this.escapeHtml(cat)}">${this.escapeHtml(cat)}</option>`;
        });
        categoryFilterEl.innerHTML = catOptionsHtml;
        if (currentCatVal !== 'all' && categories.includes(currentCatVal)) {
          categoryFilterEl.value = currentCatVal;
        } else {
          this.state.adminErrorCategoryFilter = 'all';
          categoryFilterEl.value = 'all';
        }
      }

      this.renderAdminErrorTopicsList();
    } catch (e) {
      console.error('Failed to load admin overview:', e);
    }
  },

  renderAdminErrorTopicsList() {
    const errorList = document.getElementById('admin-common-errors-list');
    if (!errorList) return;

    const allTopics = this.state.adminErrorTopics || [];
    const chFilter = this.state.adminErrorChallengeFilter || 'all';
    const catFilter = this.state.adminErrorCategoryFilter || 'all';

    const filtered = allTopics.filter(item => {
      const chKey = item.challenge_id || item.challenge_title || '';
      const catKey = item.error_category || 'Runtime / Test Failure';
      const matchesChallenge = chFilter === 'all' || chKey === chFilter || item.challenge_title === chFilter;
      const matchesCategory = catFilter === 'all' || catKey === catFilter;
      return matchesChallenge && matchesCategory;
    });

    const totalOccurrences = filtered.reduce((sum, item) => sum + Number(item.frequency ?? item.count ?? 0), 0);
    const summaryCountEl = document.getElementById('admin-errors-summary-count');
    if (summaryCountEl) {
      const sampleSuffix = this.state.adminErrorIsSampleData ? ' • Sample data' : '';
      summaryCountEl.textContent = `Showing ${filtered.length} of ${allTopics.length} error ${allTopics.length === 1 ? 'topic' : 'topics'} (${totalOccurrences} total ${totalOccurrences === 1 ? 'occurrence' : 'occurrences'}${sampleSuffix})`;
    }

    if (filtered.length === 0) {
      errorList.innerHTML = `
        <div style="color: var(--text-muted); font-size: 0.85rem; padding: 14px; background: var(--bg-subtle); border: 1px solid var(--border-color); border-radius: var(--radius-sm);">
          No error topics match the selected filters.
        </div>
      `;
      return;
    }

    errorList.innerHTML = filtered.map((err, idx) => {
      const rankNum = err.rank || (idx + 1);
      const summary = err.error_summary || err.topic || 'Unspecified sandbox test error';
      const category = err.error_category || 'Runtime / Test Failure';
      const challengeTitle = err.challenge_title || 'General Challenge';
      const relatedLesson = err.related_lesson || err.skill_tag || 'Core Programming Lab';
      const count = Number(err.frequency ?? err.count ?? 1);

      return `
        <div class="admin-error-topic-card" data-challenge-id="${this.escapeHtml(err.challenge_id || '')}" data-error-category="${this.escapeHtml(category)}">
          <span class="admin-error-rank-badge" aria-label="Rank ${rankNum}">#${rankNum}</span>
          <div class="admin-error-topic-main">
            <div class="admin-error-topic-header">
              <code class="admin-error-summary-code">${this.escapeHtml(summary)}</code>
              <span class="admin-error-category-pill">${this.escapeHtml(category)}</span>
            </div>
            <div class="admin-error-meta-row">
              <span><strong>Challenge:</strong> ${this.escapeHtml(challengeTitle)}</span>
              <span aria-hidden="true">•</span>
              <span><strong>Lesson:</strong> ${this.escapeHtml(relatedLesson)}</span>
            </div>
          </div>
          <span class="admin-error-count-badge">
            ${count} ${count === 1 ? 'occurrence' : 'occurrences'}
          </span>
        </div>
      `;
    }).join('');
  },

  async renderAdminChallenges() {
    try {
      const data = await API.getAdminChallenges();
      const challenges = data.challenges || [];
      const tbody = document.getElementById('admin-challenges-tbody');
      const countEl = document.getElementById('admin-challenges-count');
      if (countEl) countEl.textContent = `${challenges.length} labs total`;

      if (!tbody) return;
      tbody.innerHTML = '';

      challenges.forEach(ch => {
        const tr = document.createElement('tr');
        const isActive = ch.active !== 0;

        tr.innerHTML = `
          <td>
            <strong style="color: var(--text-primary); font-size: 0.88rem;">${ch.title}</strong>
            <div style="font-size: 0.74rem; font-family: var(--font-mono); color: var(--text-muted);">${ch.id}</div>
          </td>
          <td><span class="track-tag track-py">${ch.skill_tag}</span></td>
          <td><span class="diff-badge">${ch.difficulty}</span></td>
          <td><strong style="color: var(--indigo-primary);">+${ch.xp_reward} XP</strong></td>
          <td>
            <span class="diff-badge" style="background: ${isActive ? 'var(--teal-light)' : 'var(--red-light)'}; color: ${isActive ? 'var(--teal-success)' : 'var(--red-error)'}; font-size: 0.72rem;">
              ${isActive ? 'Active' : 'Archived'}
            </span>
          </td>
          <td>
            <div style="display: flex; gap: 6px;">
              <button class="btn btn-secondary btn-edit-ch" style="padding: 4px 8px; font-size: 0.74rem;" data-id="${ch.id}">
                Edit
              </button>
              <button class="btn btn-secondary btn-toggle-ch" style="padding: 4px 8px; font-size: 0.74rem;" data-id="${ch.id}">
                ${isActive ? 'Archive' : 'Activate'}
              </button>
            </div>
          </td>
        `;

        tr.querySelector('.btn-edit-ch').addEventListener('click', () => {
          this.openChallengeEditorModal('edit', ch);
        });

        tr.querySelector('.btn-toggle-ch').addEventListener('click', async () => {
          try {
            await API.toggleChallengeStatus(ch.id);
            await this.renderAdminChallenges();
            const refreshed = await API.getChallenges();
            this.state.challenges = refreshed.challenges;
            this.renderChallengesGrid();
          } catch (e) {
            alert(`Error: ${e.message}`);
          }
        });

        tbody.appendChild(tr);
      });
    } catch (e) {
      console.error('Failed to load admin challenges:', e);
    }
  },

  async renderAdminClasses() {
    try {
      const data = await API.getAdminClasses();
      const classes = data.classes || [];
      this.state.adminClasses = classes;
      const container = document.getElementById('admin-classes-container');
      if (!container) return;
      container.innerHTML = '';

      if (classes.length === 0) {
        container.innerHTML = `<div style="color: var(--text-muted); padding: 20px 0;">No classes assigned or found.</div>`;
        return;
      }

      const isStaff = this.isStaffRole(this.state.account);

      classes.forEach(cls => {
        const card = document.createElement('div');
        card.style.cssText = "background: #FFFFFF; border: 1px solid var(--border-color); border-radius: var(--radius-lg); padding: 20px; margin-bottom: 20px; box-shadow: var(--shadow-sm);";

        const students = cls.students || [];
        const studentRows = students.length === 0
          ? `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 14px;">No students enrolled yet.</td></tr>`
          : students.map(s => `
              <tr>
                <td><strong>${this.escapeHtml(s.display_name)}</strong></td>
                <td><span style="font-family: var(--font-mono); font-size: 0.78rem; color: var(--text-muted);">${this.escapeHtml(s.id)}</span></td>
                <td><strong style="color: var(--indigo-primary); white-space: nowrap;">${s.total_xp} XP</strong></td>
                <td><span class="diff-badge">Lvl ${s.level}</span></td>
                <td><span style="color: var(--teal-success); font-weight: 700; white-space: nowrap;">${s.completed_count} done</span></td>
                <td class="student-actions-cell">
                  <div class="student-actions-group">
                    <button class="btn btn-secondary btn-view-student-skillproof" type="button" data-student-id="${this.escapeHtml(s.id)}">View profile</button>
                    ${isStaff ? `<button class="btn btn-secondary btn-edit-student" type="button" data-student-id="${this.escapeHtml(s.id)}">Edit</button>` : ''}
                  </div>
                </td>
              </tr>
            `).join('');

        card.innerHTML = `
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px;">
            <div>
              <h3 style="font-size: 1.15rem; font-weight: 700; color: var(--text-primary);">${this.escapeHtml(cls.name)}</h3>
              <div style="font-size: 0.8rem; color: var(--text-muted);">Class ID: ${this.escapeHtml(cls.id)} | Instructor: ${this.escapeHtml(cls.teacher_name)}</div>
            </div>
            <span class="diff-badge" style="background: rgba(79, 70, 229, 0.1); color: var(--indigo-primary);">
              ${students.length} Enrolled Students
            </span>
          </div>

          <table class="data-table">
            <thead>
              <tr>
                <th>Student Moniker</th>
                <th>Account ID</th>
                <th>Total XP</th>
                <th>Level</th>
                <th>Completed Labs</th>
                <th>Manage</th>
              </tr>
            </thead>
            <tbody>
              ${studentRows}
            </tbody>
          </table>
        `;

        card.querySelectorAll('.btn-view-student-skillproof').forEach(button => {
          button.addEventListener('click', () => {
            this.switchAdminTab('students');
            this.openAdminStudentProfile(button.dataset.studentId);
          });
        });

        card.querySelectorAll('.btn-edit-student').forEach(button => {
          button.addEventListener('click', () => {
            const student = students.find(item => item.id === button.dataset.studentId);
            if (student) this.openStudentEditorModal(student);
          });
        });

        container.appendChild(card);
      });
    } catch (e) {
      console.error('Failed to load admin classes:', e);
    }
  },

  openStudentEditorModal(student) {
    const modal = document.getElementById('modal-student-editor');
    const classSelect = document.getElementById('edit-student-class');
    const progContainer = document.getElementById('edit-student-programs-checkboxes');
    if (!modal || !classSelect || !this.isStaffRole(this.state.account)) return;

    document.getElementById('edit-student-id').value = student.id;
    document.getElementById('edit-student-name').value = student.display_name || '';
    document.getElementById('edit-student-email').value = student.email || '';
    classSelect.replaceChildren();
    const unassigned = document.createElement('option');
    unassigned.value = '';
    unassigned.textContent = 'Unassigned';
    classSelect.appendChild(unassigned);
    (this.state.adminClasses || []).forEach(cls => {
      const option = document.createElement('option');
      option.value = cls.id;
      option.textContent = cls.name;
      classSelect.appendChild(option);
    });
    classSelect.value = student.class_id || '';

    if (progContainer) {
      const assignedSet = new Set(
        (student.assigned_programs || []).map(p => typeof p === 'string' ? p : p.language_id)
      );
      const catalogLangs = (this.state.languages && this.state.languages.length > 0)
        ? this.state.languages
        : [
            { id: 'python', name: 'Python', icon: '🐍' },
            { id: 'sql', name: 'SQL', icon: '🗄️' },
            { id: 'html', name: 'HTML & CSS', icon: '🌐' },
            { id: 'javascript', name: 'JavaScript', icon: '⚡' },
            { id: 'java', name: 'Java', icon: '☕' },
            { id: 'c', name: 'C', icon: '⚙️' },
            { id: 'cpp', name: 'C++', icon: '🚀' }
          ];
      progContainer.innerHTML = catalogLangs.map(lang => `
        <label style="display: flex; align-items: center; gap: 6px; font-size: 0.82rem; color: var(--text-primary); cursor: pointer;">
          <input type="checkbox" class="edit-student-prog-cb" value="${this.escapeHtml(lang.id)}" ${assignedSet.has(lang.id) ? 'checked' : ''}>
          <span>${lang.icon || ''} ${this.escapeHtml(lang.name)}</span>
        </label>
      `).join('');
    }

    modal.classList.add('active');
  },

  closeStudentEditorModal() {
    document.getElementById('modal-student-editor')?.classList.remove('active');
  },

  async handleSaveStudentProfile() {
    const studentId = document.getElementById('edit-student-id').value;
    const displayName = document.getElementById('edit-student-name').value.trim();
    const email = document.getElementById('edit-student-email').value.trim();
    const classId = document.getElementById('edit-student-class').value || null;
    const progCheckboxes = document.querySelectorAll('.edit-student-prog-cb:checked');
    const assignedPrograms = Array.from(progCheckboxes).map(cb => cb.value);

    if (!displayName || !email) {
      alert('Enter a display name and email address.');
      return;
    }
    try {
      await API.updateStudentProfile(studentId, {
        display_name: displayName,
        email,
        class_id: classId,
        assigned_programs: assignedPrograms
      });
      this.closeStudentEditorModal();
      await this.renderAdminOverview();
      await this.renderAdminClasses();
      await this.renderAdminStudents(this.state.adminStudentSearchQuery || '');
      if (this.state.selectedAdminStudentId === studentId) {
        await this.openAdminStudentProfile(studentId);
      }
      alert('Student profile and learning programs saved.');
    } catch (error) {
      alert(`Could not save student profile: ${error.message}`);
    }
  },

  async renderAdminSettings() {
    try {
      const data = await API.getAdminSettings();
      const s = data.settings || {};
      if (s.platform_name) document.getElementById('cfg-platform-name').value = s.platform_name;
      document.getElementById('cfg-xp-per-level').value = s.xp_multiplier_per_level || 100;
      if (s.max_hints_allowed) document.getElementById('cfg-max-hints').value = s.max_hints_allowed;
      if (s.ai_coach_guidance) document.getElementById('cfg-ai-guidance').value = s.ai_coach_guidance;
      const colors = {
        theme_primary: 'cfg-theme-primary',
        theme_background: 'cfg-theme-background',
        theme_surface: 'cfg-theme-surface',
        theme_text: 'cfg-theme-text'
      };
      Object.entries(colors).forEach(([key, id]) => {
        if (/^#[0-9a-f]{6}$/i.test(s[key] || '')) document.getElementById(id).value = s[key];
      });
    } catch (e) {
      console.warn('Could not load settings:', e);
    }
  },

  async handleSaveSettings() {
    try {
      const newSettings = {
        platform_name: document.getElementById('cfg-platform-name').value,
        xp_multiplier_per_level: parseInt(document.getElementById('cfg-xp-per-level').value, 10),
        max_hints_allowed: parseInt(document.getElementById('cfg-max-hints').value, 10),
        ai_coach_guidance: document.getElementById('cfg-ai-guidance').value,
        theme_primary: document.getElementById('cfg-theme-primary').value,
        theme_background: document.getElementById('cfg-theme-background').value,
        theme_surface: document.getElementById('cfg-theme-surface').value,
        theme_text: document.getElementById('cfg-theme-text').value
      };
      if (!Number.isInteger(newSettings.xp_multiplier_per_level) || newSettings.xp_multiplier_per_level < 1) {
        throw new Error('XP per level must be a positive whole number.');
      }
      await API.updateAdminSettings(newSettings);
      this.applySiteSettings(newSettings);
      alert('✓ Platform settings saved successfully.');
    } catch (e) {
      alert(`Save error: ${e.message}`);
    }
  },

  async handleExportData() {
    try {
      const data = await API.exportPlatformData();
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(data, null, 2));
      const downloadAnchor = document.createElement('a');
      downloadAnchor.setAttribute("href", dataStr);
      downloadAnchor.setAttribute("download", `codemirror_backup_${Date.now()}.json`);
      document.body.appendChild(downloadAnchor);
      downloadAnchor.click();
      downloadAnchor.remove();
    } catch (e) {
      alert(`Export error: ${e.message}`);
    }
  },

  async handleCleanupAttempts() {
    if (confirm("Are you sure you want to clear test execution attempt logs? Student completion records and XP will be preserved.")) {
      try {
        await API.cleanupData('attempts');
        alert("Attempt logs cleared.");
        await this.renderAdminOverview();
      } catch (e) {
        alert(`Cleanup error: ${e.message}`);
      }
    }
  },

  // ==========================================================
  // LAB CREATE / EDIT MODAL
  // ==========================================================
  openChallengeEditorModal(mode = 'create', challenge = null) {
    const modal = document.getElementById('modal-challenge-editor');
    const title = document.getElementById('modal-ch-title');
    const modeInput = document.getElementById('edit-ch-mode');
    const idInput = document.getElementById('edit-ch-id');
    const titleInput = document.getElementById('edit-ch-title');
    const skillInput = document.getElementById('edit-ch-skill');
    const diffInput = document.getElementById('edit-ch-diff');
    const xpInput = document.getElementById('edit-ch-xp');
    const promptInput = document.getElementById('edit-ch-prompt');
    const recapInput = document.getElementById('edit-ch-recap');
    const relInput = document.getElementById('edit-ch-related');
    const starterInput = document.getElementById('edit-ch-starter');
    const languageInput = document.getElementById('edit-ch-language');

    modeInput.value = mode;

    if (mode === 'edit' && challenge) {
      title.textContent = `Edit Coding Lab: ${challenge.title}`;
      idInput.value = challenge.id;
      idInput.disabled = true;
      titleInput.value = challenge.title;
      skillInput.value = challenge.skill_tag;
      languageInput.value = challenge.execution_language || 'python';
      diffInput.value = challenge.difficulty;
      xpInput.value = challenge.xp_reward;
      promptInput.value = challenge.prompt;
      recapInput.value = challenge.concept_recap || '';
      relInput.value = challenge.related_challenge_id || '';
      starterInput.value = challenge.starter_code || '';
    } else {
      title.textContent = 'Create New Coding Lab';
      idInput.value = `ch_py_lab_${Date.now().toString().slice(-4)}`;
      idInput.disabled = false;
      titleInput.value = '';
      skillInput.value = 'python-backend';
      languageInput.value = 'python';
      diffInput.value = 'Intermediate';
      xpInput.value = '75';
      promptInput.value = '';
      recapInput.value = '';
      relInput.value = 'ch_py_filter';
      starterInput.value = 'def solve(data):\n    # Write your solution here\n    pass';
    }

    modal.classList.add('active');
  },

  closeChallengeEditorModal() {
    const modal = document.getElementById('modal-challenge-editor');
    if (modal) modal.classList.remove('active');
  },

  async handleSaveChallengeForm() {
    const mode = document.getElementById('edit-ch-mode').value;
    const challengeData = {
      id: document.getElementById('edit-ch-id').value.trim(),
      title: document.getElementById('edit-ch-title').value.trim(),
      skill_tag: document.getElementById('edit-ch-skill').value.trim(),
      execution_language: document.getElementById('edit-ch-language').value,
      difficulty: document.getElementById('edit-ch-diff').value,
      xp_reward: parseInt(document.getElementById('edit-ch-xp').value, 10),
      prompt: document.getElementById('edit-ch-prompt').value.trim(),
      concept_recap: document.getElementById('edit-ch-recap').value.trim(),
      related_challenge_id: document.getElementById('edit-ch-related').value.trim(),
      starter_code: document.getElementById('edit-ch-starter').value
    };

    if (!challengeData.id || !challengeData.title || !challengeData.prompt) {
      alert('Please fill out all required fields (ID, Title, Prompt).');
      return;
    }

    try {
      if (mode === 'create') {
        await API.createChallenge(challengeData);
        alert('✓ Coding Lab created successfully!');
      } else {
        await API.updateChallenge(challengeData.id, challengeData);
        alert('✓ Coding Lab updated successfully!');
      }

      this.closeChallengeEditorModal();
      await this.renderAdminChallenges();

      const refreshed = await API.getChallenges();
      this.state.challenges = refreshed.challenges;
      this.renderChallengesGrid();
    } catch (e) {
      alert(`Save Lab error: ${e.message}`);
    }
  },

  // ==========================================================
  // HELPER UTILITIES
  // ==========================================================
  handleSaveCode() {
    const saveBtn = document.getElementById('save-code-btn');
    if (!saveBtn) return;
    const orig = saveBtn.textContent;
    saveBtn.textContent = 'Saved ✓';
    setTimeout(() => { saveBtn.textContent = orig; }, 1500);
  },

  handleResetCode() {
    if (this.state.workspaceMode === 'example' && this.state.currentExample) {
      if (confirm("Reset code back to the original example code?")) {
        window.editorManager.setValue(this.state.currentExample.code, this.state.currentLanguage);
      }
      return;
    }
    if (!this.state.currentChallenge) return;
    if (confirm("Reset code back to the challenge's starter code?")) {
      window.editorManager.setValue(this.state.currentChallenge.starter_code, this.state.currentLanguage);
    }
  },

  async handleResetDemo() {
    if (confirm("Reset demo data back to clean starting state?")) {
      await API.resetDemo();
      window.location.hash = '';
      await this.loadInitialData();
      this.switchView('languages');
      alert("Platform reset to initial starter state.");
    }
  },

  triggerConfetti() {
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return;
    }

    const canvas = document.getElementById('confetti-canvas');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    const pieces = [];
    const colors = ['#4F46E5', '#0F9F82', '#D97706', '#3B82F6', '#10B981'];
    for (let i = 0; i < 80; i++) {
      pieces.push({
        x: canvas.width / 2,
        y: canvas.height / 2,
        vx: (Math.random() - 0.5) * 14,
        vy: (Math.random() - 0.7) * 14,
        size: Math.random() * 8 + 4,
        color: colors[Math.floor(Math.random() * colors.length)],
        rotation: Math.random() * 360,
        vr: (Math.random() - 0.5) * 10
      });
    }

    let frame = 0;
    function anim() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      frame++;
      pieces.forEach(p => {
        p.x += p.vx;
        p.y += p.vy;
        p.vy += 0.35;
        p.rotation += p.vr;
        ctx.save();
        ctx.translate(p.x, p.y);
        ctx.rotate((p.rotation * Math.PI) / 180);
        ctx.fillStyle = p.color;
        ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size);
        ctx.restore();
      });

      if (frame < 120) {
        requestAnimationFrame(anim);
      } else {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }
    anim();
  }
};

window.addEventListener('DOMContentLoaded', () => {
  App.init();
});
