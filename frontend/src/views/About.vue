<template>
  <main class="about-main">
    <!-- Hero Header -->
    <header class="about-hero glass-card">
      <div class="hero-glow"></div>
      <div class="hero-content">
        <p class="about-tag">{{ t('about.group') }}</p>
        <h1 class="about-title">{{ t('about.title') }}</h1>
        <p class="about-subtitle">{{ t('about.subtitle') }}</p>
        <p class="about-mentor">💡 {{ t('about.mentor') }}</p>
      </div>
    </header>

    <!-- Main Content Grid -->
    <div class="about-grid">
      <!-- Left: Context & Objective -->
      <section class="about-left glass-card">
        <h2 class="section-title">📝 {{ t('about.context') }}</h2>
        <div class="text-content">
          <p class="about-paragraph">{{ t('about.paragraph1') }}</p>
          <p class="about-paragraph">{{ t('about.paragraph3') }}</p>
        </div>

        <div class="divider"></div>

        <h2 class="section-title">🎯 {{ t('about.objective') }}</h2>
        <div class="text-content">
          <p class="about-paragraph">{{ t('about.paragraph2') }}</p>
        </div>
      </section>

      <!-- Right: Vision, Mission & Core Values -->
      <section class="about-right">
        <!-- Vision -->
        <article class="info-card glass-card">
          <div class="card-icon-wrapper">
            <span class="card-icon">👁️</span>
          </div>
          <div class="card-body">
            <h3>{{ t('about.vision') }}</h3>
            <p>{{ t('about.visionDesc') }}</p>
          </div>
        </article>

        <!-- Mission -->
        <article class="info-card glass-card">
          <div class="card-icon-wrapper">
            <span class="card-icon">🚀</span>
          </div>
          <div class="card-body">
            <h3>{{ t('about.mission') }}</h3>
            <p>{{ t('about.missionDesc') }}</p>
          </div>
        </article>

        <!-- Core Values -->
        <article class="info-card glass-card">
          <div class="card-icon-wrapper">
            <span class="card-icon">💎</span>
          </div>
          <div class="card-body">
            <h3>{{ t('about.coreValues') }}</h3>
            <p>{{ t('about.coreValuesDesc') }}</p>
          </div>
        </article>
      </section>
    </div>

    <!-- Team Members Grid -->
    <section class="team-section glass-card">
      <h2 class="team-title">👥 {{ t('about.membersTitle') }}</h2>
      <div class="team-grid">
        <div 
          v-for="member in teamMembers" 
          :key="member.name" 
          class="member-card"
        >
          <div class="member-avatar">
            <span class="avatar-text">{{ member.initials }}</span>
          </div>
          <div class="member-info">
            <h4 class="member-name">{{ member.name }}</h4>
            <p class="member-role">{{ t(member.role) }}</p>
          </div>
        </div>
      </div>
    </section>

    <!-- Slogan Quote -->
    <footer class="about-footer glass-card">
      <div class="slogan-badge">✨ {{ t('about.slogan') }}</div>
      <blockquote class="footer-blockquote">
        {{ t('about.footerMessage') }}
      </blockquote>
    </footer>
  </main>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

// List of project members with their translation keys
const teamMembers = [
  { name: 'Ngô Văn Việt', initials: 'VV', role: 'about.roleLeader' },
  { name: 'Nguyễn Thị Thu Thủy', initials: 'TT', role: 'about.roleBA' },
  { name: 'Vũ Mai Linh', initials: 'ML', role: 'about.roleAI' },
  { name: 'Lê Đức Phong', initials: 'DP', role: 'about.roleFE' },
  { name: 'Trần Thị Xuân', initials: 'TX', role: 'about.roleQA' },
  { name: 'Trần Trung Hiếu', initials: 'TH', role: 'about.roleArchitect' },
  { name: 'Nguyễn Ngọc Linh', initials: 'NL', role: 'about.roleContent' }
]
</script>

<style scoped>
.about-main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 24px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* Hero Header */
.about-hero {
  position: relative;
  padding: 48px;
  overflow: hidden;
  text-align: left;
  border-radius: var(--radius-xl);
}

.hero-glow {
  position: absolute;
  top: -50%;
  right: -10%;
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, rgba(14, 165, 233, 0.15) 0%, transparent 70%);
  z-index: 0;
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
}

.about-tag {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.3em;
  color: var(--text-accent);
  text-transform: uppercase;
  margin-bottom: 12px;
}

.about-title {
  font-size: 2.75rem;
  font-weight: 700;
  color: var(--text-heading);
  margin: 0 0 12px 0;
  letter-spacing: -0.02em;
}

.about-subtitle {
  font-size: 1.15rem;
  color: var(--text-secondary);
  margin: 0 0 16px 0;
  line-height: 1.5;
}

.about-mentor {
  font-size: 0.95rem;
  color: var(--text-heading);
  font-weight: 500;
  margin: 0;
  display: inline-block;
  padding: 6px 16px;
  background-color: var(--bg-card-inner);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-full);
}

/* Grid layout */
.about-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 32px;
}

@media (max-width: 992px) {
  .about-grid {
    grid-template-columns: 1fr;
  }
}

.about-left {
  padding: 40px;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0;
}

.text-content {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.about-paragraph {
  font-size: 0.95rem;
  line-height: 1.6;
  color: var(--text-body);
  margin: 0;
  text-align: justify;
}

.divider {
  height: 1px;
  background-color: var(--border-color);
  margin: 8px 0;
}

/* Cards block */
.about-right {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.info-card {
  display: flex;
  gap: 20px;
  padding: 24px;
  align-items: flex-start;
  text-align: left;
  transition: transform var(--transition-normal), border-color var(--transition-fast);
}

.info-card:hover {
  transform: translateY(-2px);
  border-color: var(--border-highlight);
}

.card-icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(14, 165, 233, 0.1);
  border: 1px solid rgba(14, 165, 233, 0.2);
  font-size: 1.35rem;
  flex-shrink: 0;
}

.card-body h3 {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 8px 0;
}

.card-body p {
  font-size: 0.9rem;
  line-height: 1.5;
  color: var(--text-body);
  margin: 0;
  text-align: justify;
  text-justify: inter-word;
  word-break: break-word;
}

/* Team section */
.team-section {
  padding: 40px;
  text-align: left;
}

.team-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 32px 0;
}

.team-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 24px;
}

.member-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: var(--radius-lg);
  background-color: var(--bg-card-inner);
  border: 1px solid var(--border-color);
  transition: all var(--transition-normal);
}

.member-card:hover {
  transform: translateY(-3px);
  border-color: var(--border-highlight);
  box-shadow: 0 4px 20px rgba(14, 165, 233, 0.1);
}

.member-avatar {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-text {
  color: var(--text-on-primary);
  font-weight: 700;
  font-size: 1rem;
}

.member-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.member-name {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0;
}

.member-role {
  font-size: 0.8rem;
  color: var(--text-secondary);
  margin: 0;
}

/* Footer Quote */
.about-footer {
  padding: 40px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.slogan-badge {
  font-size: 0.85rem;
  font-weight: 700;
  color: var(--text-accent);
  text-transform: uppercase;
  letter-spacing: 0.15em;
  padding: 6px 16px;
  background-color: rgba(14, 165, 233, 0.1);
  border: 1px solid rgba(14, 165, 233, 0.2);
  border-radius: var(--radius-full);
}

.footer-blockquote {
  font-size: 1.05rem;
  line-height: 1.6;
  color: var(--text-secondary);
  max-width: 800px;
  margin: 0;
  font-style: italic;
  text-align: justify;
  text-justify: inter-word;
  word-break: break-word;
}
</style>
