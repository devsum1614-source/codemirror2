/**
 * CodeMirror 2.0 - Beginner Coding Tutor & Learning Workspace
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
    adminClasses: []
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
    await Promise.all([this.loadRuntimes(), this.loadAIStatus(), this.loadSiteConfig()]);
    await this.checkAuthAndInitialize();

    // Listen for hash changes
    window.addEventListener('hashchange', () => this.handleRouting());
  },

  bindEvents() {
    // Top Navigation Links
    document.querySelectorAll('.nav-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        this.switchView(btn.dataset.view);
      });
    });

    // Brand click returns to Language Home Page or Login
    const brandBtn = document.getElementById('brand-btn');
    if (brandBtn) {
      brandBtn.addEventListener('click', () => {
        if (this.state.isAuthenticated) {
          if (this.state.account && (this.state.account.role === 'owner' || this.state.account.role === 'teacher')) {
            window.location.hash = '#admin';
            this.switchView('admin');
          } else {
            window.location.hash = '';
            this.switchView('languages');
          }
        } else {
          window.location.hash = '#login';
          this.switchView('student-login');
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

    // Owner student profile editor
    const studentClose = document.getElementById('modal-student-close-btn');
    if (studentClose) studentClose.addEventListener('click', () => this.closeStudentEditorModal());
    const studentCancel = document.getElementById('modal-student-cancel-btn');
    if (studentCancel) studentCancel.addEventListener('click', () => this.closeStudentEditorModal());
    const studentSave = document.getElementById('modal-student-save-btn');
    if (studentSave) studentSave.addEventListener('click', () => this.handleSaveStudentProfile());
  },

  bindAuthEvents() {
    // Auth Tab Switcher (Student Sign In vs Sign Up)
    const tabSignInBtn = document.getElementById('tab-student-signin-btn');
    const tabSignUpBtn = document.getElementById('tab-student-signup-btn');
    const formLogin = document.getElementById('form-student-login');
    const formRegister = document.getElementById('form-student-register');

    if (tabSignInBtn && tabSignUpBtn && formLogin && formRegister) {
      tabSignInBtn.addEventListener('click', () => {
        tabSignInBtn.classList.add('active');
        tabSignUpBtn.classList.remove('active');
        formLogin.style.display = 'block';
        formRegister.style.display = 'none';
        this.clearAuthAlert('student');
      });

      tabSignUpBtn.addEventListener('click', () => {
        tabSignUpBtn.classList.add('active');
        tabSignInBtn.classList.remove('active');
        formLogin.style.display = 'none';
        formRegister.style.display = 'block';
        this.clearAuthAlert('student');
      });
    }

    // Student Login Form & Button Submit
    if (formLogin) {
      formLogin.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleStudentLogin();
      });
    }
    const btnSubmitLogin = document.getElementById('btn-submit-student-login');
    if (btnSubmitLogin) {
      btnSubmitLogin.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleStudentLogin();
      });
    }

    // Student Registration Form & Button Submit
    if (formRegister) {
      formRegister.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleStudentRegister();
      });
    }
    const btnSubmitReg = document.getElementById('btn-submit-student-register');
    if (btnSubmitReg) {
      btnSubmitReg.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleStudentRegister();
      });
    }

    // Admin Login Form & Button Submit
    const formAdminLogin = document.getElementById('form-admin-login');
    if (formAdminLogin) {
      formAdminLogin.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleAdminLogin();
      });
    }
    const btnSubmitAdmin = document.getElementById('btn-submit-admin-login');
    if (btnSubmitAdmin) {
      btnSubmitAdmin.addEventListener('click', (e) => {
        e.preventDefault();
        this.handleAdminLogin();
      });
    }

    // Quick 1-Click Demo Credential Buttons
    document.querySelectorAll('.demo-autofill-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        const role = btn.dataset.role;
        const user = btn.dataset.user;
        const pass = btn.dataset.pass;
        if (role === 'student') {
          const idInput = document.getElementById('student-login-identifier');
          const pwdInput = document.getElementById('student-login-password');
          if (idInput) idInput.value = user;
          if (pwdInput) pwdInput.value = pass;
          this.handleStudentLogin();
        } else if (role === 'admin') {
          const idInput = document.getElementById('admin-login-identifier');
          const pwdInput = document.getElementById('admin-login-password');
          if (idInput) idInput.value = user;
          if (pwdInput) pwdInput.value = pass;
          this.handleAdminLogin();
        }
      });
    });

    // Switch between Student and Admin Auth Views
    const linkToAdmin = document.getElementById('link-to-admin-login');
    if (linkToAdmin) {
      linkToAdmin.addEventListener('click', () => {
        window.location.hash = '#admin-login';
        this.switchView('admin-login');
      });
    }

    const linkToStudent = document.getElementById('link-to-student-login');
    if (linkToStudent) {
      linkToStudent.addEventListener('click', () => {
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

  async handleStudentLogin() {
    if (this._loginInProgress) return;
    this.clearAuthAlert('student');
    const idInput = document.getElementById('student-login-identifier');
    const pwdInput = document.getElementById('student-login-password');
    const btn = document.getElementById('btn-submit-student-login');

    const identifier = idInput ? idInput.value.trim() : '';
    const password = pwdInput ? pwdInput.value : '';

    if (!identifier || !password) {
      this.showAuthAlert('student', 'Please enter both your email/ID and password.');
      return;
    }

    this._loginInProgress = true;
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Signing in…';
    }
    try {
      const res = await API.login(identifier, password);
      this.state.isAuthenticated = true;
      this.state.account = res.account;
      this.updateNavForAuth(true);
      await this.loadInitialData();

      if (res.account.role === 'owner' || res.account.role === 'teacher') {
        this.switchView('admin');
      } else {
        this.switchView('dashboard');
      }
    } catch (err) {
      this.showAuthAlert('student', err.message || 'Invalid username or password.');
    } finally {
      this._loginInProgress = false;
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Sign In to Learning Dashboard →';
      }
    }
  },

  async handleStudentRegister() {
    this.clearAuthAlert('student');
    const nameInput = document.getElementById('student-reg-name');
    const emailInput = document.getElementById('student-reg-email');
    const pwdInput = document.getElementById('student-reg-password');
    const classInput = document.getElementById('student-reg-class');
    const btn = document.getElementById('btn-submit-student-register');

    const name = nameInput ? nameInput.value.trim() : '';
    const email = emailInput ? emailInput.value.trim() : '';
    const password = pwdInput ? pwdInput.value : '';
    const classId = classInput ? classInput.value.trim() : null;

    if (!name || !email || !password) {
      this.showAuthAlert('student', 'Please fill in all required registration fields.');
      return;
    }
    if (password.length < 6) {
      this.showAuthAlert('student', 'Password must be at least 6 characters.');
      return;
    }

    if (btn) btn.disabled = true;
    try {
      const res = await API.registerStudent(name, email, password, classId);
      this.state.isAuthenticated = true;
      this.state.account = res.account;
      this.updateNavForAuth(true);
      await this.loadInitialData();
      window.location.hash = '';
      this.switchView('languages');
    } catch (err) {
      this.showAuthAlert('student', err.message || 'Registration failed.');
    } finally {
      if (btn) btn.disabled = false;
    }
  },

  async handleAdminLogin() {
    this.clearAuthAlert('admin');
    const idInput = document.getElementById('admin-login-identifier');
    const pwdInput = document.getElementById('admin-login-password');
    const btn = document.getElementById('btn-submit-admin-login');

    const identifier = idInput ? idInput.value.trim() : '';
    const password = pwdInput ? pwdInput.value : '';

    if (!identifier || !password) {
      this.showAuthAlert('admin', 'Please enter your administrator ID/email and password.');
      return;
    }

    if (btn) btn.disabled = true;
    try {
      const res = await API.login(identifier, password);
      this.state.isAuthenticated = true;
      this.state.account = res.account;
      this.updateNavForAuth(true);
      await this.loadInitialData();

      if (res.account.role === 'owner' || res.account.role === 'teacher') {
        window.location.hash = '#admin';
        this.switchView('admin');
      } else {
        // Logged in as student via admin portal
        window.location.hash = '';
        this.switchView('languages');
      }
    } catch (err) {
      this.showAuthAlert('admin', err.message || 'Invalid administrator credentials.');
    } finally {
      if (btn) btn.disabled = false;
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
    this.updateNavForAuth(false);
    window.location.hash = '#login';
    this.switchView('student-login');
  },

  async checkAuthAndInitialize() {
    try {
      const res = await API.getMyProfile();
      if (res && res.account) {
        this.state.isAuthenticated = true;
        this.state.account = res.account;
        this.updateNavForAuth(true);
        await this.loadInitialData();
        this.handleRouting();
        return;
      }
    } catch (e) {
      // Unauthenticated visitor
    }

    this.state.isAuthenticated = false;
    this.state.account = null;
    this.updateNavForAuth(false);

    const hash = window.location.hash;
    if (hash === '#admin-login' || window.location.pathname.startsWith('/admin')) {
      this.switchView('admin-login');
    } else {
      this.switchView('student-login');
    }
  },

  updateNavForAuth(isAuth) {
    const mainNav = document.getElementById('main-nav-container');
    const navUser = document.getElementById('nav-user-container');
    const authBtns = document.getElementById('nav-auth-buttons');

    if (isAuth) {
      if (mainNav) mainNav.style.display = 'block';
      if (navUser) navUser.style.display = 'flex';
      if (authBtns) authBtns.style.display = 'none';
      this.updateRoleBasedNavigation();
      this.renderUserBadge();
    } else {
      if (mainNav) mainNav.style.display = 'none';
      if (navUser) navUser.style.display = 'none';
      if (authBtns) authBtns.style.display = 'flex';
    }
  },

  handleRouting() {
    const path = window.location.pathname;
    const hash = window.location.hash.replace('#', '');

    // Unauthenticated user gating
    if (!this.state.isAuthenticated) {
      if (hash === 'admin-login' || path.startsWith('/admin')) {
        this.switchView('admin-login');
      } else {
        this.switchView('student-login');
      }
      return;
    }

    // Authenticated redirects
    if (hash === 'login' || hash === 'student-login') {
      if (this.state.account && (this.state.account.role === 'owner' || this.state.account.role === 'teacher')) {
        this.switchView('admin');
      } else {
        this.switchView('languages');
      }
      return;
    }

    if (hash === 'admin-login') {
      if (this.state.account && (this.state.account.role === 'owner' || this.state.account.role === 'teacher')) {
        this.switchView('admin');
      } else {
        this.switchView('languages');
      }
      return;
    }

    if (hash === 'admin') {
      if (this.state.account && (this.state.account.role === 'owner' || this.state.account.role === 'teacher')) {
        this.switchView('admin');
      } else {
        this.switchView('languages');
      }
      return;
    }

    // Check for language route e.g. /languages/python or #languages/python
    if (path.startsWith('/languages/') && path.length > 11) {
      const langId = path.split('/')[2];
      this.openLanguagePage(langId);
      return;
    }

    if (hash.startsWith('languages/') || hash.startsWith('language-')) {
      const langId = hash.replace('languages/', '').replace('language-', '');
      this.openLanguagePage(langId);
      return;
    }

    // Check for challenge route e.g. #challenge-ch_py_filter
    if (hash.startsWith('challenge-') || hash.startsWith('mission-')) {
      const chId = hash.replace('challenge-', '').replace('mission-', '');
      this.openMission(chId);
      return;
    }

    if (hash === 'dashboard') {
      this.switchView('dashboard');
    } else if (hash === 'languages') {
      this.switchView('languages');
    } else if (hash === 'missions') {
      this.switchView('missions');
    } else if (hash === 'workspace') {
      this.switchView('workspace');
    } else if (hash === 'skillproof') {
      this.switchView('skillproof');
    } else if (hash === 'report') {
      this.switchView('report');
    } else {
      if (this.state.account && (this.state.account.role === 'owner' || this.state.account.role === 'teacher')) {
        this.switchView('admin');
      } else {
        this.switchView('dashboard');
      }
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
      this.state.account = meResp.account;

      if (this.state.account && this.state.account.role === 'student') {
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

      // Load languages catalog
      await this.loadLanguages();

      // Load challenges
      const challengesResp = await API.getChallenges();
      this.state.challenges = challengesResp.challenges || [];

      this.renderDashboard();
      this.renderChallengesGrid();
    } catch (err) {
      console.error('Error loading initial platform data:', err);
    }
  },

  updateRoleBasedNavigation() {
    const role = (this.state.account && this.state.account.role) || 'student';
    const navAdminLi = document.getElementById('nav-admin-li');
    const adminNavLabel = document.getElementById('admin-nav-label');
    const adminViewTitle = document.getElementById('admin-view-title');
    const adminViewSubtitle = document.getElementById('admin-view-subtitle');
    const adminSettingsTabBtn = document.getElementById('admin-settings-tab-btn');

    if (role === 'owner') {
      if (navAdminLi) navAdminLi.style.display = 'block';
      if (adminNavLabel) adminNavLabel.textContent = 'Admin Console';
      if (adminViewTitle) adminViewTitle.textContent = 'Site Owner & Admin Console';
      if (adminViewSubtitle) adminViewSubtitle.textContent = 'Manage coding labs, classes, student rosters, learning analytics, and platform configurations.';
      if (adminSettingsTabBtn) adminSettingsTabBtn.style.display = 'inline-flex';
    } else if (role === 'teacher') {
      if (navAdminLi) navAdminLi.style.display = 'block';
      if (adminNavLabel) adminNavLabel.textContent = 'Teacher Portal';
      if (adminViewTitle) adminViewTitle.textContent = 'Instructor Class Portal';
      if (adminViewSubtitle) adminViewSubtitle.textContent = `View learning progress, pass rates, and student performance for your assigned classes.`;
      if (adminSettingsTabBtn) adminSettingsTabBtn.style.display = 'none';
    } else {
      if (navAdminLi) navAdminLi.style.display = 'none';
      if (this.state.activeView === 'admin') {
        this.switchView('languages');
      }
    }
  },

  renderUserBadge() {
    const acc = this.state.account || { display_name: 'Student', role: 'student', id: API.getAccountId() };
    const prog = this.state.studentProgress || { total_xp: 0, level: 1, completed_count: 0, completed_challenges: [] };

    const nameEl = document.getElementById('user-name');
    if (nameEl) nameEl.textContent = acc.display_name;

    const idEl = document.getElementById('user-id-display');
    if (idEl) idEl.textContent = acc.id;

    const roleEl = document.getElementById('user-role-badge');
    if (roleEl) {
      roleEl.textContent = acc.role.toUpperCase();
      if (acc.role === 'owner') {
        roleEl.style.background = 'rgba(79, 70, 229, 0.15)';
        roleEl.style.color = 'var(--indigo-primary)';
      } else if (acc.role === 'teacher') {
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
    this.state.activeView = viewName;
    document.querySelectorAll('.nav-btn').forEach(b => {
      b.classList.toggle('active', b.dataset.view === viewName);
    });

    document.querySelectorAll('.view-section').forEach(sec => {
      sec.classList.remove('active');
    });

    const target = document.getElementById(`view-${viewName}`);
    if (target) target.classList.add('active');

    if (viewName === 'languages') {
      this.renderLanguagesGrid();
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

  renderLanguagesGrid() {
    const container = document.getElementById('languages-grid-container');
    if (!container) return;
    container.innerHTML = '';

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

      card.innerHTML = `
        <div>
          <div class="lang-card-top">
            <span class="lang-card-icon">${lang.icon}</span>
            <span class="lang-avail-pill ${lang.available ? 'ready' : 'missing'}" title="${lang.toolchain_status || ''}">
              ${lang.available ? '● Ready to Run' : '⚪ Not Runnable Yet'}
            </span>
          </div>
          <h3 class="lang-card-title">${lang.name}</h3>
          <div class="lang-card-meta">
            <span class="diff-badge">${lang.difficulty}</span>
            <span class="track-tag track-py">${lang.category}</span>
          </div>
          <p class="lang-card-desc">${lang.short_description}</p>
          ${lang.available ? '' : '<p class="lang-card-desc" style="font-size:0.75rem;color:var(--amber-hint);">' + (lang.toolchain_status || 'Execution adapter unavailable') + '</p>'}
        </div>
        <div class="lang-card-footer">
          <span style="font-size: 0.82rem; font-weight: 700; color: var(--indigo-primary);">
            🎯 ${lang.challenges_count} Hands-On Labs
          </span>
          <button class="btn btn-secondary btn-explore-lang" style="padding: 6px 14px; font-size: 0.82rem;">
            Explore ${lang.name} →
          </button>
        </div>
      `;

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

  async openLanguagePage(langId) {
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
      document.getElementById('detail-lang-cat').textContent = details.category;
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
        heading.textContent = 'Compiler / Interpreter Ready:';
        text.textContent = 'Host environment is configured and ready for isolated sandbox execution.';
        version.textContent = details.version || 'Active';
      } else {
        banner.className = 'lang-status-banner missing';
        icon.textContent = '⚠️';
        heading.textContent = 'Execution Not Available:';
        text.textContent = `${details.runtime_description || details.toolchain_status || 'This language cannot run in the current server build.'} See setup guide below for local development.`;
        version.textContent = 'Runner unavailable';
      }

      const startButton = document.getElementById('detail-start-coding-btn');
      const canStart = Boolean(details.available && (details.challenges || []).length);
      if (startButton) {
        startButton.disabled = !canStart;
        startButton.title = canStart ? 'Open the first available lab for this language.' :
          (!details.available ? (details.runtime_description || 'This language cannot run in the current server build.') : 'No labs are available for this language yet.');
        startButton.innerHTML = canStart
          ? '<span>⚡</span> Start Coding Now'
          : '<span>⚙️</span> Setup Needed';
      }

      // Populate Count & Tabs
      const chCount = (details.challenges || []).length;
      document.getElementById('detail-challenges-count').textContent = chCount;

      // Render Sub-Views
      this.renderLanguageChallenges(details.challenges || []);
      this.renderLanguageLessons(details.lessons || []);
      this.renderLanguageExamples(details.examples || []);
      this.renderLanguageSetup(details.setup_guide || {});

      // Switch to language detail view
      this.switchView('language-detail');
      this.switchLangSubTab('challenges');
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

  renderLanguageChallenges(challenges) {
    const grid = document.getElementById('detail-challenges-grid');
    if (!grid) return;
    grid.innerHTML = '';

    const completedSet = new Set((this.state.studentProgress?.completed_challenges || []).map(c => c.challenge_id));

    if (challenges.length === 0) {
      grid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 36px 0; color: var(--text-muted);">
          No dedicated labs found for this track yet. Try our Python or SQL challenges!
        </div>
      `;
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
            <span class="track-tag track-py">${c.skill_tag}</span>
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
          <button class="btn btn-primary" style="padding: 6px 14px; font-size: 0.8rem;" ${canRun ? '' : 'disabled title="This lab language is not available on the server."'}>
            ${!canRun ? 'Runtime Needed' : (isCompleted ? 'Review Lab →' : 'Launch Lab →')}
          </button>
        </div>
      `;

      if (canRun) card.querySelector('button').addEventListener('click', () => this.openMission(c.id));

      grid.appendChild(card);
    });
  },

  renderLanguageLessons(lessons) {
    const container = document.getElementById('detail-lessons-list');
    if (!container) return;
    container.innerHTML = '';

    lessons.forEach(les => {
      const el = document.createElement('div');
      el.className = 'lesson-card';
      el.innerHTML = `
        <h4>${les.title}</h4>
        <p><strong>Overview:</strong> ${les.summary}</p>
        <p>${les.explanation}</p>
        <div style="font-size: 0.78rem; font-weight: 700; color: var(--text-muted); margin-bottom: 6px;">Syntax Pattern:</div>
        <div class="code-snippet-box">${les.example}</div>
      `;
      container.appendChild(el);
    });
  },

  renderLanguageExamples(examples) {
    const container = document.getElementById('detail-examples-list');
    if (!container) return;
    container.innerHTML = '';

    examples.forEach(ex => {
      const el = document.createElement('div');
      el.className = 'lesson-card';
      el.innerHTML = `
        <h4>💡 ${ex.title}</h4>
        <p>${ex.description}</p>
        <div class="code-snippet-box">${ex.code}</div>
      `;
      container.appendChild(el);
    });
  },

  renderLanguageSetup(setupGuide) {
    document.getElementById('detail-setup-title').textContent = setupGuide.title || 'Compiler Setup Guide';
    document.getElementById('detail-setup-text').textContent = setupGuide.instructions || 'Follow official toolchain installation documentation.';
    document.getElementById('detail-setup-cmd').textContent = setupGuide.command || 'runtime --version';
  },

  openWorkspaceForLanguage(langId) {
    // Find first challenge for this language or open scratch
    const details = this.state.currentLanguageDetail;
    const firstChallenge = details?.challenges?.[0];

    if (!this.state.runtimes[langId]?.available) {
      this.switchLangSubTab('setup');
      return;
    }

    if (firstChallenge) {
      this.openMission(firstChallenge.id);
    } else {
      // Set editor language directly
      this.state.currentLanguage = langId;
      const langSelect = document.getElementById('editor-language-select');
      if (langSelect) langSelect.value = langId;

      this.state.currentChallenge = null;
      const starter = details?.starter_code || '# Write your own program here.\n';
      window.editorManager.setValue(starter, langId);
      document.getElementById('current-file-tab').textContent = `main${details?.file_ext || '.txt'}`;
      this.updateRuntimeBadge(langId);
      this.switchView('workspace');
      this.switchRightTab('output');
    }
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
      document.getElementById('rec-mission-title').textContent = nextChallenge.title;
      document.getElementById('rec-mission-track').textContent = `${nextChallenge.skill_tag} (+${nextChallenge.xp_reward} XP)`;
      document.getElementById('rec-mission-btn').onclick = () => this.openMission(nextChallenge.id);
    }

    // Completed Challenges List in Dashboard
    const completedListEl = document.getElementById('dash-completed-list');
    if (completedListEl) {
      const completed = prog.completed_challenges || [];
      if (completed.length === 0) {
        completedListEl.innerHTML = `
          <div style="text-align: center; padding: 24px 0; color: var(--text-muted);">
            No completed labs yet. Launch your first lab above!
          </div>
        `;
      } else {
        completedListEl.innerHTML = completed.map(c => `
          <div style="padding: 10px 12px; background: #FAFAFC; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
            <div>
              <strong style="color: var(--text-primary); font-size: 0.88rem;">${c.title}</strong>
              <div style="font-size: 0.75rem; color: var(--text-muted);">${c.skill_tag} • ${c.completed_at || 'Verified'}</div>
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
  async openMission(challengeId) {
    try {
      const challenge = await API.getChallenge(challengeId);
      this.state.currentChallenge = challenge;
      this.state.unlockedHints = new Set([1]);
      this.state.recentError = null;

      const defaultLang = challenge.execution_language || 'python';
      const extMap = { python: '.py', sql: '.sql', html: '.html', javascript: '.js', java: '.java', c: '.c', cpp: '.cpp' };
      const fileName = `${challenge.id}${extMap[defaultLang] || '.txt'}`;

      this.state.currentLanguage = defaultLang;

      // Update language select dropdown
      const langSelect = document.getElementById('editor-language-select');
      if (langSelect) langSelect.value = defaultLang;

      // Set editor value & language
      window.editorManager.setValue(challenge.starter_code, defaultLang);
      document.getElementById('current-file-tab').textContent = fileName;

      // Update workspace header & brief
      document.getElementById('workspace-mission-title').textContent = challenge.title;
      document.getElementById('workspace-mission-track').textContent = `${challenge.skill_tag} (+${challenge.xp_reward} XP)`;
      document.getElementById('mission-scenario-text').textContent = challenge.prompt;

      // Populate 7-Step Pedagogical Teaching Flow in Lab Guide Tab
      document.getElementById('guide-step-1').textContent = `Restate the goal: Implement logic for '${challenge.title}' in your own words.`;
      document.getElementById('guide-step-2').textContent = `Acceptance Criteria: Must return correct results, guard against boundary inputs, and complete within 3.0s.`;
      document.getElementById('guide-step-3').textContent = `Walkthrough: Test your function with a sample input, then consider empty collections or None.`;

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

      // Load initial hint (Step 1: Guided Question)
      this.fetchAndDisplayHint(1);
      this.clearCoachChat();

      // Reset test panel
      document.getElementById('test-results-container').innerHTML = `
        <div style="text-align: center; color: var(--text-muted); padding: 30px 10px; font-size: 0.85rem;">
          Click <strong>▶ Run Tests</strong> above to execute automated validation inside the isolated sandbox.
        </div>
      `;
      document.getElementById('test-summary-box').style.display = 'none';

      // Switch to workspace view and Output tab
      this.switchView('workspace');
      this.switchRightTab('output');
      window.location.hash = `challenge-${challengeId}`;
    } catch (err) {
      alert(`Could not load lab challenge: ${err.message}`);
    }
  },

  handleLanguageChange(lang) {
    this.state.currentLanguage = lang;
    window.editorManager.setLanguage(lang);
    this.updateRuntimeBadge(lang);

    const fileTab = document.getElementById('current-file-tab');
    const chId = this.state.currentChallenge ? this.state.currentChallenge.id : 'code';
    const extMap = { python: '.py', sql: '.sql', html: '.html', javascript: '.js', java: '.java', c: '.c', cpp: '.cpp' };
    fileTab.textContent = `${chId}${extMap[lang] || '.txt'}`;

    // Toggle HTML preview
    const previewContainer = document.getElementById('html-preview-container');
    if (previewContainer) {
      previewContainer.style.display = (lang === 'html') ? 'block' : 'none';
      if (lang === 'html') {
        this.updateHtmlPreview(window.editorManager.getValue());
      }
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
    const runButton = document.getElementById('run-tests-btn');
    const submitButton = document.getElementById('submit-mission-btn');
    if (runButton) {
      runButton.disabled = !rt.available;
      runButton.title = rt.available ? 'Run the lab tests.' : (rt.description || `${rt.name} execution is unavailable on this server.`);
    }
    if (submitButton) {
      submitButton.disabled = !rt.available;
      submitButton.title = rt.available ? 'Submit your verified solution.' : (rt.description || `${rt.name} execution is unavailable on this server.`);
    }

    if (rt.available) {
      badge.textContent = '● Ready';
      badge.style.background = 'rgba(15, 159, 130, 0.12)';
      badge.style.color = 'var(--teal-success)';
      if (warningBanner) warningBanner.style.display = 'none';
    } else {
      badge.textContent = '⚪ Runner Unavailable';
      badge.style.background = 'var(--bg-subtle)';
      badge.style.color = 'var(--text-muted)';
      if (warningBanner) {
        warningBanner.style.display = 'block';
        warningTitle.textContent = `${rt.name} Execution Unavailable:`;
        warningText.textContent = `${rt.description || 'No execution adapter is available.'} Switch to Python, SQL, or HTML/CSS for working labs on this host.`;
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
    if (!this.state.currentChallenge) return;
    const challengeId = this.state.currentChallenge.id;
    const code = window.editorManager.getValue();
    const lang = this.state.currentLanguage || 'python';

    const runBtn = document.getElementById('run-tests-btn');
    const originalText = runBtn.innerHTML;
    runBtn.innerHTML = `<span>⏳</span> Sandboxing...`;
    runBtn.disabled = true;

    try {
      // If HTML, update live preview frame
      if (lang === 'html') {
        this.updateHtmlPreview(code);
      }

      const report = await API.submitAttempt(challengeId, code, lang);
      this.state.recentError = report.error_summary || null;
      this.renderAttemptResult(report);
      this.switchRightTab('output');

      // Refresh student progress
      await this.refreshStudentStats();

      // If passed, display celebratory confetti and concept recap
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
          <strong style="font-size: 0.95rem;">⚠️ Runner Unavailable</strong>
          <div style="font-size: 0.75rem; color: #78350F; margin-top: 2px;">
            ${report.feedback || 'This language cannot run in the current server build.'} Zero fake success reported.
          </div>
        </div>
        <div><span style="font-size: 1.2rem;">⚙️</span></div>
      `;
    } else {
      summaryBox.className = `output-summary-header ${report.passed ? 'passed' : 'failed'}`;
      summaryBox.innerHTML = `
        <div>
          <strong style="font-size: 0.95rem;">${report.passed ? '✓ All Tests Passed' : '⚠️ Tests Incomplete or Failed'}</strong>
          <div style="font-size: 0.75rem; margin-top: 2px;">
            Attempt ID: ${report.attempt_id} | ${report.xp_earned > 0 ? `+${report.xp_earned} XP Awarded` : 'Single-XP Policy Enforced'}
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
          <div class="test-msg">${d.error || 'Assertion passed successfully.'}</div>
        </div>
      `).join('');
    } else {
      container.innerHTML = `
        <div class="test-item-card ${report.passed ? 'passed' : 'failed'}">
          <div class="test-item-top">
            <span class="test-name">Sandbox Verification Suite</span>
            <span style="font-size: 0.75rem; font-weight: 700; color: ${report.passed ? 'var(--teal-success)' : 'var(--red-error)'}">
              ${report.passed ? 'PASS' : 'FAIL'}
            </span>
          </div>
          <div class="test-msg">${report.feedback}</div>
          ${!report.passed ? `<div class="test-error-callout">${report.error_summary || 'Open the AI Coach tab for guided debugging hints.'}</div>` : ''}
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

    document.getElementById('hint-level-title').textContent = stageTitle;
    document.getElementById('hint-content-text').innerHTML = hint.message.replace(/\n/g, '<br/>');
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
    this.switchRightTab('coach');
    const input = document.getElementById('coach-question-input');
    if (input) input.focus();
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
    const lang = this.state.currentLanguage || 'python';

    try {
      const res = await API.submitMission(this.state.currentChallenge.id, code, "", this.state.currentLanguage || 'python');
      this.triggerConfetti();
      alert(`🎉 Lab Solution Verified & Recorded!\n\n${res.message}`);
      
      await this.loadInitialData();
      this.switchView('skillproof');
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
    await this.renderAdminOverview();
    await this.renderAdminChallenges();
    await this.renderAdminClasses();
    await this.renderAdminSettings();
  },

  async renderAdminOverview() {
    try {
      const overview = await API.getAdminOverview();
      const metrics = overview.metrics || overview;
      document.getElementById('admin-total-students').textContent = metrics.total_students;
      document.getElementById('admin-total-classes').textContent = metrics.total_classes;
      document.getElementById('admin-total-attempts').textContent = metrics.total_attempts;
      document.getElementById('admin-pass-rate').textContent = `${metrics.overall_pass_rate}%`;

      const errorList = document.getElementById('admin-common-errors-list');
      if (errorList) {
        const topics = overview.common_errors || overview.common_error_topics || [];
        if (topics.length === 0) {
          errorList.innerHTML = `<div style="color: var(--text-muted); font-size: 0.85rem;">No error telemetry recorded yet.</div>`;
        } else {
          errorList.innerHTML = topics.map(err => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: #FAFAFC; border: 1px solid var(--border-subtle); border-radius: var(--radius-sm); margin-bottom: 6px;">
              <div>
                <strong style="color: var(--red-error); font-size: 0.85rem;">${err.topic || err.error_summary}</strong>
                <div style="font-size: 0.75rem; color: var(--text-muted);">${err.challenge_title || err.advice || 'Targeted debugging guidance'}</div>
              </div>
              <span class="diff-badge" style="background: var(--red-light); color: var(--red-error); font-size: 0.75rem;">
                ${err.count || err.frequency || 1} occurrences
              </span>
            </div>
          `).join('');
        }
      }
    } catch (e) {
      console.error('Failed to load admin overview:', e);
    }
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
                <td><strong style="color: var(--indigo-primary);">${s.total_xp} XP</strong></td>
                <td><span class="diff-badge">Lvl ${s.level}</span></td>
                <td><span style="color: var(--teal-success); font-weight: 700;">${s.completed_count} done</span></td>
                <td>${this.state.account?.role === 'owner' ? `<button class="btn btn-secondary btn-edit-student" type="button" data-student-id="${this.escapeHtml(s.id)}" style="padding: 4px 8px; font-size: 0.74rem;">Edit profile</button>` : '—'}</td>
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
    if (!modal || !classSelect || this.state.account?.role !== 'owner') return;

    document.getElementById('edit-student-id').value = student.id;
    document.getElementById('edit-student-name').value = student.display_name || '';
    document.getElementById('edit-student-email').value = student.email || '';
    classSelect.replaceChildren();
    const unassigned = document.createElement('option');
    unassigned.value = '';
    unassigned.textContent = 'Unassigned';
    classSelect.appendChild(unassigned);
    this.state.adminClasses.forEach(cls => {
      const option = document.createElement('option');
      option.value = cls.id;
      option.textContent = cls.name;
      classSelect.appendChild(option);
    });
    classSelect.value = student.class_id || '';
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
    if (!displayName || !email) {
      alert('Enter a display name and email address.');
      return;
    }
    try {
      await API.updateStudentProfile(studentId, { display_name: displayName, email, class_id: classId });
      this.closeStudentEditorModal();
      await this.renderAdminClasses();
      alert('Student profile saved.');
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
    const orig = saveBtn.innerHTML;
    saveBtn.innerHTML = `<span>✓</span> Saved`;
    setTimeout(() => { saveBtn.innerHTML = orig; }, 1500);
  },

  handleResetCode() {
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
