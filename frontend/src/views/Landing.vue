<template>
  <main class="landing-main">
    <!-- Hero Section -->
    <section class="hero-grid">
      <div class="hero-left">
        <div class="tag-badge">
          {{ t('landing.tagBadge') }}
        </div>
        <h1 class="hero-headline">
          {{ t('landing.headline') }}
        </h1>
        <p class="hero-subtext">
          {{ t('landing.subtext') }}
        </p>
        <div class="action-buttons">
          <router-link to="/cv-analysis" class="btn-primary start-btn">
            {{ t('landing.analyzeCV') }} <span class="arrow">→</span>
          </router-link>
          <router-link to="/dashboard" class="btn-outline-landing">
            {{ t('landing.openDashboard') }}
          </router-link>
        </div>
      </div>

      <!-- Hero Visual Card Preview -->
      <div class="hero-right glass-card">
        <div class="preview-container">
          <p class="preview-tag">{{ t('landing.preview') }}</p>
          
          <div class="preview-highlight-box">
            <p class="preview-box-tag">{{ t('landing.cvReadiness') }}</p>
            <div class="preview-box-row">
              <div>
                <p class="preview-score">86%</p>
                <p class="preview-role">{{ t('landing.candidateRole') }}</p>
              </div>
              <div class="preview-badge-sub">
                <p class="preview-badge-tag">{{ t('landing.match') }}</p>
                <p class="preview-badge-val">92%</p>
              </div>
            </div>
          </div>

          <div class="preview-mini-grid">
            <div class="preview-feature-card">
              <h4>{{ t('landing.cvAnalysisCard') }}</h4>
              <p>{{ t('landing.cvAnalysisCardDesc') }}</p>
            </div>
            <div class="preview-feature-card">
              <h4>{{ t('landing.jobMatchingCard') }}</h4>
              <p>{{ t('landing.jobMatchingCardDesc') }}</p>
            </div>
            <div class="preview-feature-card">
              <h4>{{ t('landing.mockInterviewCard') }}</h4>
              <p>{{ t('landing.mockInterviewCardDesc') }}</p>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Key Features Highlight -->
    <section class="highlights-section">
      <article class="highlight-card glass-card">
        <h3>{{ t('landing.cvAnalysisTitle') }}</h3>
        <p>{{ t('landing.cvAnalysisDesc') }}</p>
      </article>
      <article class="highlight-card glass-card">
        <h3>{{ t('landing.jobMatchingTitle') }}</h3>
        <p>{{ t('landing.jobMatchingDesc') }}</p>
      </article>
      <article class="highlight-card glass-card">
        <h3>{{ t('landing.mockInterviewTitle') }}</h3>
        <p>{{ t('landing.mockInterviewDesc') }}</p>
      </article>
    </section>

    <!-- Steps section -->
    <section class="steps-section glass-card">
      <div class="steps-header">
        <div>
          <p class="step-tag">{{ t('landing.flow') }}</p>
          <h2 class="step-title" v-html="t('landing.flowTitle')"></h2>
        </div>
        <router-link to="/job-recommendation" class="step-link-action">{{ t('landing.seeRecommendations') }}</router-link>
      </div>

      <div class="steps-grid">
        <div class="step-card">
          <p class="step-num">01</p>
          <p class="step-label">{{ t('landing.step1') }}</p>
        </div>
        <div class="step-card">
          <p class="step-num">02</p>
          <p class="step-label">{{ t('landing.step2') }}</p>
        </div>
        <div class="step-card">
          <p class="step-num">03</p>
          <p class="step-label">{{ t('landing.step3') }}</p>
        </div>
        <div class="step-card">
          <p class="step-num">04</p>
          <p class="step-label">{{ t('landing.step4') }}</p>
        </div>
      </div>
    </section>
  </main>
</template>

<script setup>
/**
 * Landing.vue — Trang chủ (Public)
 * Hiển thị các tính năng cốt lõi và giới thiệu thiết kế dark cyan-indigo chuẩn.
 */
import { useI18n } from 'vue-i18n'
const { t } = useI18n()
</script>

<style scoped>
.landing-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 60px 24px;
  width: 100%;
}

.hero-grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 48px;
  align-items: center;
  margin-bottom: 64px;
}

@media (max-width: 992px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }
}

.hero-left {
  text-align: left;
}

.tag-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border-radius: 9999px;
  border: 1px solid var(--tag-badge-border);
  background-color: var(--tag-badge-bg);
  padding: 8px 16px;
  font-size: 0.85rem;
  color: var(--tag-badge-text);
  margin-bottom: 24px;
}

.sparkle-icon {
  color: var(--text-link);
}

.hero-headline {
  font-size: 3.25rem;
  line-height: 1.15;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 24px 0;
  letter-spacing: -0.02em;
}

@media (max-width: 768px) {
  .hero-headline {
    font-size: 2.25rem;
  }
}

.hero-subtext {
  font-size: 1.15rem;
  line-height: 1.6;
  color: var(--text-secondary);
  margin-bottom: 32px;
  max-width: 640px;
}

.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.start-btn {
  padding: 14px 32px;
  font-size: 1.05rem;
}

.arrow {
  margin-left: 6px;
  transition: transform var(--transition-fast);
}

.start-btn:hover .arrow {
  transform: translateX(4px);
}

.btn-outline-landing {
  display: inline-flex;
  align-items: center;
  padding: 14px 32px;
  border: 1px solid var(--btn-landing-outline-border);
  color: var(--btn-landing-outline-text);
  border-radius: var(--radius-full);
  font-weight: 600;
  font-size: 1.05rem;
  transition: all var(--transition-normal);
  text-decoration: none;
}

.btn-outline-landing:hover {
  border-color: var(--border-highlight);
  background-color: var(--bg-hover-subtle);
}

.hero-right {
  padding: 24px;
}

.preview-container {
  text-align: left;
}

.preview-tag {
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-label);
  text-transform: uppercase;
  margin-bottom: 16px;
}

.preview-highlight-box {
  background: var(--bg-highlight-box);
  border: 1px solid var(--border-highlight);
  border-radius: var(--radius-lg);
  padding: 20px;
  margin-bottom: 20px;
}

.preview-box-tag {
  font-size: 0.85rem;
  color: var(--text-body);
  margin-bottom: 12px;
}

.preview-box-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.preview-score {
  font-size: 3rem;
  font-weight: 600;
  color: var(--text-heading);
  line-height: 1;
}

.preview-role {
  font-size: 0.85rem;
  color: var(--text-body);
  margin-top: 6px;
}

.preview-badge-sub {
  background-color: var(--bg-badge);
  border-radius: var(--radius-md);
  padding: 8px 16px;
  text-align: right;
}

.preview-badge-tag {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.25em;
  color: var(--text-link);
  text-transform: uppercase;
  margin-bottom: 2px;
}

.preview-badge-val {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0;
}

.preview-mini-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.preview-feature-card {
  background-color: var(--bg-card-inner);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: 16px;
}

.feat-icon {
  font-size: 1.25rem;
}

.preview-feature-card h4 {
  font-size: 0.95rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 6px 0 4px 0;
}

.preview-feature-card p {
  font-size: 0.8rem;
  color: var(--text-label);
  line-height: 1.4;
}

.highlights-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 24px;
  margin-bottom: 64px;
}

.highlight-card {
  text-align: left;
  padding: 32px;
}

.h-icon {
  font-size: 2.25rem;
  display: block;
  margin-bottom: 20px;
}

.highlight-card h3 {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 12px 0;
}

.highlight-card p {
  font-size: 0.95rem;
  color: var(--text-body);
  line-height: 1.6;
}

.steps-section {
  text-align: left;
  padding: 40px;
}

.steps-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  flex-wrap: wrap;
  gap: 16px;
  border-bottom: 1px solid var(--border-divider);
  padding-bottom: 24px;
  margin-bottom: 32px;
}

.step-tag {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.35em;
  color: var(--text-link);
  text-transform: uppercase;
  margin-bottom: 8px;
}

.step-title {
  font-size: 1.75rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0;
}

.step-link-action {
  font-size: 0.95rem;
  color: var(--text-link);
  font-weight: 500;
}

.step-link-action:hover {
  text-decoration: underline;
}

.steps-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
}

.step-card {
  background-color: var(--bg-card-inner);
  border: 1px solid var(--border-card);
  border-radius: var(--radius-md);
  padding: 24px;
}

.step-num {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-link);
  margin-bottom: 8px;
}

.step-label {
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--text-heading);
  margin: 0;
}
</style>
