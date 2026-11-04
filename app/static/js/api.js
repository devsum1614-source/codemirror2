/**
 * Student Coding Quest & CodeMirror 2.0 API Client
 * Communicates exclusively through secure versioned REST endpoints.
 * Never connects directly to the database. Supports Student, Teacher, and Owner roles.
 */

const API = {
  isStaticHost() {
    return Boolean(window.StaticEngine) && (
      window.location.hostname.endsWith('github.io') ||
      window.location.protocol === 'file:'
    );
  },

  // Session & Authentication Storage
  getToken() {
    return localStorage.getItem('cm_session_token');
  },

  setSession(token, account) {
    if (token) localStorage.setItem('cm_session_token', token);
    if (account) {
      localStorage.setItem('cm_user', JSON.stringify(account));
      localStorage.setItem('quest_account_id', account.id);
      localStorage.setItem('quest_student_id', account.id);
    }
  },

  clearSession() {
    localStorage.removeItem('cm_session_token');
    localStorage.removeItem('cm_user');
    localStorage.removeItem('quest_account_id');
    localStorage.removeItem('quest_student_id');
  },

  getStoredUser() {
    try {
      const u = localStorage.getItem('cm_user');
      return u ? JSON.parse(u) : null;
    } catch (e) {
      return null;
    }
  },

  getAccountId() {
    const u = this.getStoredUser();
    return (u && u.id) ? u.id : (localStorage.getItem('quest_account_id') || '');
  },

  setAccountId(id) {
    localStorage.setItem('quest_account_id', id);
    localStorage.setItem('quest_student_id', id);
  },

  getStudentId() {
    return this.getAccountId();
  },

  getHeaders() {
    const headers = {
      'Content-Type': 'application/json'
    };
    const token = this.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const accId = this.getAccountId();
    if (accId) {
      headers['X-Account-Id'] = accId;
      headers['X-Student-Id'] = accId;
    }
    return headers;
  },

  // 1. Authentication Endpoints
  async login(identifier, password) {
    if (this.isStaticHost()) {
      const data = window.StaticEngine.login(identifier, password);
      this.setSession(data.token, data.account);
      return data;
    }
    const res = await fetch('/api/v1/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ identifier, password })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || 'Invalid username or password.');
    }
    this.setSession(data.token, data.account);
    return data;
  },

  async registerStudent(displayName, email, password, classId = null) {
    if (this.isStaticHost()) {
      const data = window.StaticEngine.registerStudent(displayName, email, password, classId);
      this.setSession(data.token, data.account);
      return data;
    }
    const res = await fetch('/api/v1/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        display_name: displayName,
        email: email,
        password: password,
        class_id: classId || null
      })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.detail || 'Registration failed. Please check your inputs.');
    }
    this.setSession(data.token, data.account);
    return data;
  },

  async logout() {
    if (!this.isStaticHost()) {
      try {
        await fetch('/api/v1/auth/logout', {
          method: 'POST',
          headers: this.getHeaders()
        });
      } catch (e) {
        console.warn('Logout error', e);
      }
    }
    this.clearSession();
    return { status: 'success' };
  },

  async getMyProfile() {
    if (!this.getToken() && !this.getAccountId()) {
      throw new Error('Unauthorized or session expired');
    }
    if (this.isStaticHost()) {
      const u = this.getStoredUser();
      if (!u) throw new Error('Unauthorized or session expired');
      return { account: u };
    }
    const res = await fetch('/api/v1/auth/me', { headers: this.getHeaders() });
    if (!res.ok) {
      this.clearSession();
      throw new Error('Unauthorized or session expired');
    }
    const data = await res.json();
    if (data.account) {
      this.setSession(this.getToken(), data.account);
    }
    return data;
  },

  async getAccounts() {
    if (this.isStaticHost()) return { accounts: Object.values(window.StaticEngine.getAccountsMap()) };
    const res = await fetch('/api/v1/auth/accounts');
    return await res.json();
  },

  // 2. Health & Runtimes check
  async getHealth() {
    if (this.isStaticHost()) return { status: 'ok', service: 'student-coding-quest-static' };
    const res = await fetch('/health');
    return await res.json();
  },

  async getRuntimes() {
    if (this.isStaticHost()) return window.StaticEngine.getRuntimes();
    const res = await fetch('/api/v1/runtimes');
    if (!res.ok) throw new Error('Failed to fetch runtime status');
    return await res.json();
  },

  async getAIStatus() {
    if (this.isStaticHost()) return window.StaticEngine.getAIStatus();
    const res = await fetch('/api/v1/ai-status');
    if (!res.ok) throw new Error('Could not read AI service status.');
    return await res.json();
  },

  async getSiteConfig() {
    if (this.isStaticHost()) return window.StaticEngine.getSiteConfig();
    const res = await fetch('/api/v1/site-config');
    if (!res.ok) throw new Error('Could not load site appearance settings.');
    return await res.json();
  },

  // 1b. Languages Catalog & Detailed Curriculum
  async getLanguages() {
    if (this.isStaticHost()) return window.StaticEngine.getLanguages();
    const res = await fetch('/api/v1/languages', { headers: this.getHeaders() });
    if (!res.ok) throw new Error('Failed to fetch languages catalog');
    return await res.json();
  },

  async getLanguageDetails(langId) {
    if (this.isStaticHost()) return window.StaticEngine.getLanguageDetails(langId);
    const res = await fetch(`/api/v1/languages/${langId}`, { headers: this.getHeaders() });
    if (!res.ok) throw new Error(`Failed to load details for ${langId}`);
    return await res.json();
  },

  // 3. Mission catalog (tests are private to server)
  async getChallenges(skill = null, level = null) {
    if (this.isStaticHost()) return window.StaticEngine.getChallenges();
    let url = '/api/v1/challenges';
    const params = new URLSearchParams();
    if (skill) params.append('skill', skill);
    if (level) params.append('level', level);
    if ([...params].length) url += `?${params.toString()}`;

    const res = await fetch(url, { headers: this.getHeaders() });
    if (!res.ok) throw new Error('Failed to load challenges');
    return await res.json();
  },

  async getChallenge(challengeId) {
    if (this.isStaticHost()) return window.StaticEngine.getChallenge(challengeId);
    const res = await fetch(`/api/v1/challenges/${challengeId}`, { headers: this.getHeaders() });
    if (!res.ok) throw new Error('Failed to load challenge details');
    return await res.json();
  },

  // 4. Isolated sandbox attempt submission (transactional XP rewards)
  async submitAttempt(challengeId, code, language = 'python') {
    if (this.isStaticHost()) {
      return window.StaticEngine.submitAttempt(challengeId, code, language, this.getAccountId());
    }
    const res = await fetch('/api/v1/attempts', {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        challenge_id: challengeId,
        code: code,
        language: language
      })
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Attempt submission failed.');
    }
    return await res.json();
  },

  // 5. Staged progressive hints (Question -> Clue -> Explanation)
  async requestHint(challengeId, currentCode = '', errorSummary = null, hintLevel = 1) {
    if (this.isStaticHost()) return window.StaticEngine.requestHint(challengeId, hintLevel);
    const res = await fetch('/api/v1/hints', {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        challenge_id: challengeId,
        current_code: currentCode,
        error_summary: errorSummary,
        hint_level: hintLevel
      })
    });
    if (!res.ok) throw new Error('Failed to retrieve staged hint.');
    return await res.json();
  },

  // 6. Authenticated student progress
  async getStudentProgress(studentId = null) {
    const sid = studentId || this.getAccountId() || 'stu_alex_vance';
    if (!sid || sid === 'undefined') {
      throw new Error('Failed to load student progress');
    }
    if (this.isStaticHost()) return window.StaticEngine.getStudentProgress(sid);
    const res = await fetch(`/api/v1/students/${encodeURIComponent(sid)}/progress`, { headers: this.getHeaders() });
    if (!res.ok) throw new Error('Failed to load student progress');
    return await res.json();
  },

  // ---------------------------------------------------------------------------
  // SITE OWNER & ADMIN API METHODS
  // ---------------------------------------------------------------------------
  async getAdminOverview() {
    if (this.isStaticHost()) return window.StaticEngine.getAdminOverview();
    const res = await fetch('/api/v1/admin/overview', { headers: this.getHeaders() });
    if (!res.ok) throw new Error('Failed to load admin overview. Requires Teacher or Owner role.');
    return await res.json();
  },

  async getAdminChallenges() {
    if (this.isStaticHost()) return window.StaticEngine.getChallenges();
    const res = await fetch('/api/v1/admin/challenges', { headers: this.getHeaders() });
    if (!res.ok) throw new Error('Failed to load challenges list.');
    return await res.json();
  },

  async createChallenge(payload) {
    const res = await fetch('/api/v1/admin/challenges', {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to create challenge.');
    }
    return await res.json();
  },

  async updateChallenge(id, payload) {
    const res = await fetch(`/api/v1/admin/challenges/${id}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || 'Failed to update challenge.');
    }
    return await res.json();
  },

  async toggleChallengeStatus(id) {
    const res = await fetch(`/api/v1/admin/challenges/${id}/toggle-status`, {
      method: 'POST',
      headers: this.getHeaders()
    });
    return await res.json();
  },

  async getAdminClasses() {
    if (this.isStaticHost()) return window.StaticEngine.getAdminClasses();
    const res = await fetch('/api/v1/admin/classes', { headers: this.getHeaders() });
    if (!res.ok) throw new Error('Failed to load classes.');
    return await res.json();
  },

  async updateStudentProfile(studentId, profile) {
    if (this.isStaticHost()) return { status: 'updated' };
    const res = await fetch(`/api/v1/admin/students/${encodeURIComponent(studentId)}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(profile)
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || 'Could not update student profile.');
    return data;
  },

  async getAdminSettings() {
    if (this.isStaticHost()) return window.StaticEngine.getSiteConfig();
    const res = await fetch('/api/v1/admin/settings', { headers: this.getHeaders() });
    if (!res.ok) throw new Error('Failed to load settings.');
    return await res.json();
  },

  async updateAdminSettings(settingsDict) {
    if (this.isStaticHost()) {
      localStorage.setItem('cm_static_settings', JSON.stringify(settingsDict));
      return { status: 'updated', settings: settingsDict };
    }
    const res = await fetch('/api/v1/admin/settings', {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ settings: settingsDict })
    });
    if (!res.ok) throw new Error('Failed to update settings.');
    return await res.json();
  },

  async exportPlatformData() {
    const res = await fetch('/api/v1/admin/export', {
      method: 'GET',
      headers: this.getHeaders()
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || 'Failed to export platform data. Requires Site Owner role.');
    }
    return await res.json();
  },

  async cleanupData() {
    const res = await fetch('/api/v1/admin/cleanup', {
      method: 'POST',
      headers: this.getHeaders()
    });
    return await res.json();
  },

  // --- Legacy compatibility wrappers ---
  async getUser() {
    try {
      const prog = await this.getStudentProgress();
      const me = await this.getMyProfile();
      return {
        user_id: 1,
        student_id: prog.student_id,
        name: me.account ? me.account.display_name : prog.display_name,
        role: me.account ? me.account.role : 'student',
        email: me.account ? me.account.email : `${prog.display_name.toLowerCase()}@quest.local`,
        streak_days: 3,
        completed_count: prog.completed_count,
        readiness_score: Math.min(100, Math.round((prog.total_xp / 350) * 100)) || 78,
        points: prog.total_xp,
        level: prog.level,
        evidence_count: prog.completed_count
      };
    } catch (e) {
      const res = await fetch('/api/user');
      return await res.json();
    }
  },

  async getMissions() {
    return await this.getChallenges();
  },

  async getMissionDetail(missionId) {
    return await this.getChallenge(missionId);
  },

  async saveCode(missionId, code) {
    const res = await fetch(`/api/missions/${missionId}/save`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({ code })
    });
    return await res.json();
  },

  async runTests(missionId, code) {
    return await this.submitAttempt(missionId, code);
  },

  async submitMission(missionId, code, explanation, language = 'python') {
    const result = await this.submitAttempt(missionId, code, language);
    if (!result.passed) {
      throw new Error(result.feedback || 'Test checks did not pass.');
    }
    return {
      status: 'completed',
      score: 100,
      xp_earned: result.xp_earned,
      message: result.feedback
    };
  },

  async getHint(missionId, level) {
    return await this.requestHint(missionId, '', null, level);
  },

  async askCoach(missionId, code, question, language = 'python', recentError = null) {
    if (this.isStaticHost()) {
      return window.StaticEngine.askCoach(missionId, code, question, language, recentError);
    }
    const res = await fetch('/api/v1/coach/ask', {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify({
        challenge_id: missionId,
        code,
        question,
        language,
        recent_error: recentError
      })
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || 'The AI Coach could not answer right now.');
    return data;
  },

  async getSkillProof() {
    if (this.isStaticHost()) return window.StaticEngine.getSkillProof(this.getAccountId());
    const res = await fetch('/api/skillproof');
    return await res.json();
  },

  async getLearningReport() {
    if (this.isStaticHost()) return { status: 'ok' };
    const res = await fetch('/api/learning-report');
    return await res.json();
  },

  async resetDemo() {
    if (this.isStaticHost()) {
      localStorage.removeItem('cm_prog_stu_alex_vance');
      return { status: 'success' };
    }
    const res = await fetch('/api/reset-demo', { method: 'POST' });
    return await res.json();
  }
};
