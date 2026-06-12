<template>
  <main class="admin-container">
    <!-- Header -->
    <div class="admin-header">
      <p class="section-tag">{{ t('admin.title') }}</p>
      <h1 class="welcome-text">📊 {{ t('admin.title') }}</h1>
      <p class="subtitle-text">{{ t('admin.subtitle') }}</p>
    </div>

    <!-- Tab Switching Navigation -->
    <div class="admin-tabs glass-card">
      <button 
        class="tab-btn" 
        :class="{ active: activeTab === 'overview' }" 
        @click="activeTab = 'overview'"
      >
        📈 {{ t('admin.overviewTab') }}
      </button>
      <button 
        class="tab-btn" 
        :class="{ active: activeTab === 'users' }" 
        @click="activeTab = 'users'"
      >
        👥 {{ t('admin.usersTab') }}
      </button>
    </div>

    <!-- TAB 1: SYSTEM OVERVIEW -->
    <div v-if="activeTab === 'overview'">
      <!-- Loading State -->
      <div v-if="loading" class="loading-box glass-card">
        <div class="loading-spinner"></div>
        {{ t('admin.loading') }}
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="error-box glass-card">
        <p>{{ t('admin.error') }}</p>
        <button class="btn-retry" @click="fetchStats">{{ t('admin.retry') }}</button>
      </div>

      <template v-else>
        <!-- ═══════════ KPI CARDS ═══════════ -->
        <div class="kpi-grid">
          <!-- Card 1: Tổng tài khoản -->
          <div class="kpi-card glass-card">
            <div class="kpi-card-header">
              <span class="kpi-label">{{ t('admin.totalUsers') }}</span>
              <div class="kpi-icon-wrap">
                <span class="kpi-icon">👥</span>
              </div>
            </div>
            <h2 class="kpi-value">{{ stats.users?.total_users ?? 0 }}</h2>
          </div>

          <!-- Card 2: DAU -->
          <div class="kpi-card glass-card">
            <div class="kpi-card-header">
              <span class="kpi-label">{{ t('admin.dau') }}</span>
              <div class="kpi-icon-wrap">
                <span class="kpi-icon">📈</span>
              </div>
            </div>
            <h2 class="kpi-value">{{ stats.users?.dau ?? 0 }}</h2>
          </div>

          <!-- Card 3: MAU -->
          <div class="kpi-card glass-card">
            <div class="kpi-card-header">
              <span class="kpi-label">{{ t('admin.mau') }}</span>
              <div class="kpi-icon-wrap">
                <span class="kpi-icon">📅</span>
              </div>
            </div>
            <h2 class="kpi-value">{{ stats.users?.mau ?? 0 }}</h2>
          </div>

          <!-- Card 4: Tổng lượt tải CV -->
          <div class="kpi-card glass-card">
            <div class="kpi-card-header">
              <span class="kpi-label">{{ t('admin.cvUploads') }}</span>
              <div class="kpi-icon-wrap">
                <span class="kpi-icon">📥</span>
              </div>
            </div>
            <h2 class="kpi-value">{{ stats.features?.cv_uploads ?? 0 }}</h2>
          </div>

          <!-- Card 5: Tổng lượt phân tích CV -->
          <div class="kpi-card glass-card">
            <div class="kpi-card-header">
              <span class="kpi-label">{{ t('admin.cvAnalyses') }}</span>
              <div class="kpi-icon-wrap">
                <span class="kpi-icon">🔍</span>
              </div>
            </div>
            <h2 class="kpi-value">{{ stats.features?.cv_analyses ?? 0 }}</h2>
          </div>

          <!-- Card 6: Tỷ lệ chuyển đổi đăng ký -->
          <div class="kpi-card glass-card">
            <div class="kpi-card-header">
              <span class="kpi-label">{{ t('admin.conversionRate') }}</span>
              <div class="kpi-icon-wrap">
                <span class="kpi-icon">🎯</span>
              </div>
            </div>
            <h2 class="kpi-value">{{ stats.success?.conversion_rate ?? 0 }}%</h2>
          </div>
        </div>

        <!-- ═══════════ LIVE STATUS & RECENT ACTIVITIES ROW ═══════════ -->
        <div class="live-status-row">
          <!-- Online Users List -->
          <section class="online-section glass-card">
            <h3 class="section-title">
              <span class="live-dot" :class="{ inactive: onlineCount === 0 }"></span>
              {{ t('admin.onlineUsers') }} ({{ onlineCount }})
            </h3>
            <div class="online-list" v-if="onlineUsers.length > 0">
              <div v-for="user in onlineUsers" :key="user.user_id" class="online-user-card">
                <div class="online-avatar">{{ getInitials(user.name || user.email) }}</div>
                <div class="online-info">
                  <p class="online-name">{{ user.name || user.email }}</p>
                  <p class="online-meta">{{ t('admin.connectedSince') }}: {{ formatTime(user.online_since) }} · {{ formatElapsed(user.elapsed_seconds) }}</p>
                </div>
              </div>
            </div>
            <p v-else class="text-muted text-sm italic py-4">Không có thành viên nào đang trực tuyến.</p>
          </section>

          <!-- System Recent Activities -->
          <section class="recent-activities-section glass-card">
            <h3 class="section-title">
              <span>🐾</span> Hoạt động gần đây trên hệ thống
            </h3>
            <div class="activity-timeline" v-if="stats.recent_activities && stats.recent_activities.length > 0">
              <div v-for="(act, idx) in stats.recent_activities" :key="idx" class="activity-item">
                <div class="activity-dot" :class="act.type"></div>
                <div class="activity-content">
                  <p class="activity-desc">{{ act.desc }}</p>
                  <span class="activity-time">{{ formatTimeWithDate(act.time) }}</span>
                </div>
              </div>
            </div>
            <p v-else class="text-muted text-center py-6">Chưa có hoạt động nào được ghi nhận.</p>
          </section>
        </div>

        <!-- ═══════════ CHARTS ROW 1: TRAFFIC + USERS ═══════════ -->
        <div class="charts-row">
          <!-- Daily Visits Line Chart -->
          <section class="chart-card glass-card">
            <h3 class="section-title">{{ t('admin.dailyVisits') }}</h3>
            <div class="chart-wrapper">
              <Line :data="dailyVisitsChartData" :options="lineChartOptions" />
            </div>
          </section>

          <!-- New Users Daily Line Chart -->
          <section class="chart-card glass-card">
            <h3 class="section-title">{{ t('admin.newUsersDaily') }}</h3>
            <div class="chart-wrapper">
              <Line :data="newUsersChartData" :options="lineChartOptions" />
            </div>
          </section>
        </div>

        <!-- ═══════════ CHARTS ROW 2: FEATURE + SOURCES ═══════════ -->
        <div class="charts-row">
          <!-- Feature Usage Bar Chart -->
          <section class="chart-card glass-card">
            <h3 class="section-title">{{ t('admin.featureUsage') }}</h3>
            <div class="chart-wrapper">
              <Bar :data="featureUsageChartData" :options="barChartOptions" />
            </div>
          </section>

          <!-- Traffic Sources Doughnut -->
          <section class="chart-card glass-card chart-card-small">
            <h3 class="section-title">{{ t('admin.trafficSources') }}</h3>
            <div class="chart-wrapper chart-wrapper-doughnut">
              <Doughnut :data="trafficSourcesChartData" :options="doughnutChartOptions" />
            </div>
          </section>
        </div>

        <!-- ═══════════ STATS TABLES ═══════════ -->
        <div class="tables-row">
          <!-- Traffic Metrics Table -->
          <section class="table-card glass-card">
            <h3 class="section-title">{{ t('admin.trafficTitle') }}</h3>
            <div class="stats-table">
              <div class="stat-row">
                <span class="stat-label">{{ t('admin.totalVisits') }}</span>
                <span class="stat-val">{{ stats.traffic?.total_visits ?? 0 }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">{{ t('admin.uniqueVisitors') }}</span>
                <span class="stat-val">{{ stats.traffic?.unique_visitors ?? 0 }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">{{ t('admin.totalSessions') }}</span>
                <span class="stat-val">{{ stats.traffic?.total_sessions ?? 0 }}</span>
              </div>
            </div>
          </section>

          <!-- Engagement Metrics Table -->
          <section class="table-card glass-card">
            <h3 class="section-title">{{ t('admin.engagementTitle') }}</h3>
            <div class="stats-table">
              <div class="stat-row">
                <span class="stat-label">{{ t('admin.avgSessionDuration') }}</span>
                <span class="stat-val">{{ formatDuration(stats.engagement?.avg_session_duration) }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">{{ t('admin.pagesPerSession') }}</span>
                <span class="stat-val">{{ stats.engagement?.pages_per_session ?? 0 }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">{{ t('admin.bounceRate') }}</span>
                <span class="stat-val">{{ stats.engagement?.bounce_rate ?? 0 }}%</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">{{ t('admin.retentionRate') }}</span>
                <span class="stat-val">{{ stats.engagement?.retention_rate ?? 0 }}%</span>
              </div>
            </div>
          </section>

          <!-- Success Metrics Table -->
          <section class="table-card glass-card">
            <h3 class="section-title">{{ t('admin.successTitle') }}</h3>
            <div class="stats-table">
              <div class="stat-row">
                <span class="stat-label">{{ t('admin.interviewCompletion') }}</span>
                <span class="stat-val highlight">{{ stats.success?.interview_completion_rate ?? 0 }}%</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">{{ t('admin.conversionRate') }}</span>
                <span class="stat-val highlight">{{ stats.success?.conversion_rate ?? 0 }}%</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">{{ t('admin.completedInterviews') }}</span>
                <span class="stat-val">{{ stats.success?.completed_interviews ?? 0 }} / {{ stats.success?.total_interviews ?? 0 }}</span>
              </div>
            </div>
          </section>
        </div>

        <!-- Refresh Button -->
        <div class="refresh-row">
          <button class="btn-refresh" @click="fetchStats" :disabled="loading">
            🔄 {{ t('admin.refreshData') }}
          </button>
          <span class="last-updated" v-if="lastUpdated">{{ t('admin.lastUpdated') }}: {{ lastUpdated }}</span>
        </div>
      </template>
    </div>

    <!-- TAB 2: USER MANAGEMENT -->
    <div v-else-if="activeTab === 'users'" class="users-tab-content">
      <!-- Controls: Search & Filters -->
      <div class="users-controls glass-card">
        <div class="search-input-wrap">
          <span class="search-icon">🔍</span>
          <input 
            v-model="userSearch" 
            type="text" 
            :placeholder="t('admin.searchPlaceholder')"
            @input="onUserSearchInput"
          />
        </div>

        <div class="filters-wrap">
          <select v-model="filterRole" @change="fetchUsers(0)">
            <option value="">{{ t('admin.filterRole') }}</option>
            <option value="admin">Admin</option>
            <option value="premium">Premium User</option>
            <option value="user">User</option>
          </select>

          <select v-model="filterStatus" @change="fetchUsers(0)">
            <option value="">{{ t('admin.filterStatus') }}</option>
            <option value="active">{{ t('admin.active') }}</option>
            <option value="blocked">{{ t('admin.blocked') }}</option>
          </select>

          <select v-model="filterOnline" @change="fetchUsers(0)">
            <option value="all">{{ t('admin.filterOnline') }}</option>
            <option value="online">{{ t('admin.online') }}</option>
            <option value="offline">{{ t('admin.offline') }}</option>
          </select>

          <select v-model="filterRegDate" @change="fetchUsers(0)">
            <option value="all">{{ t('admin.filterRegDate') }}</option>
            <option value="today">{{ t('admin.regToday') }}</option>
            <option value="week">{{ t('admin.regWeek') }}</option>
            <option value="month">{{ t('admin.regMonth') }}</option>
          </select>
        </div>
      </div>

      <!-- Users Table -->
      <div class="users-table-wrap glass-card">
        <div v-if="usersLoading" class="users-loading">
          <div class="loading-spinner"></div>
        </div>
        <table v-else class="users-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>{{ t('profile.fullName') }}</th>
              <th>{{ t('profile.email') }}</th>
              <th>Ngày đăng ký</th>
              <th>Lần đăng nhập cuối</th>
              <th>Trạng thái tài khoản</th>
              <th>{{ t('profile.role') }}</th>
              <th class="text-right">{{ t('admin.actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr 
              v-for="user in usersList" 
              :key="user.id" 
              class="user-row" 
              @click="openUserDetail(user.id)"
            >
              <td>#{{ user.id }}</td>
              <td class="font-semibold">
                <div class="user-cell">
                  <div class="avatar-wrap">
                    <span class="user-avatar-small">{{ getInitials(user.full_name || user.email) }}</span>
                    <span class="online-status-dot-mini" :class="{ online: user.is_online }"></span>
                  </div>
                  <span>{{ user.full_name || '—' }}</span>
                </div>
              </td>
              <td>{{ user.email }}</td>
              <td class="text-muted">{{ formatDateSimple(user.created_at) }}</td>
              <td class="text-muted">{{ formatTimeWithDate(user.last_login) || 'Chưa đăng nhập' }}</td>
              <td>
                <span class="status-dot-badge" :class="user.is_active ? 'active' : 'blocked'">
                  {{ user.is_active ? t('admin.active') : t('admin.blocked') }}
                </span>
              </td>
              <td>
                <span class="user-role-badge-table" :class="user.role">
                  {{ user.role }}
                </span>
              </td>
              <td class="text-right" @click.stop>
                <button 
                  v-if="user.id !== authStore.user?.id"
                  class="action-btn"
                  :class="user.is_active ? 'btn-lock' : 'btn-unlock'"
                  @click="toggleUserStatus(user)"
                >
                  {{ user.is_active ? '🔒 ' + t('admin.lockUser') : '🔓 ' + t('admin.unlockUser') }}
                </button>
                <span v-else class="text-muted italic text-xs">Chính bạn</span>
              </td>
            </tr>
            <tr v-if="usersList.length === 0">
              <td colspan="8" class="text-center py-8 text-muted">
                Không tìm thấy người dùng nào phù hợp.
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination -->
      <div class="pagination-row" v-if="usersTotal > 0">
        <span class="pagination-info">
          {{ t('admin.page') }} {{ userPage }} / {{ totalUserPages }} ({{ usersTotal }} users)
        </span>
        <div class="pagination-btns">
          <button 
            class="pagination-btn" 
            :disabled="userPage === 1" 
            @click="changeUserPage(userPage - 1)"
          >
            {{ t('admin.prev') }}
          </button>
          <button 
            class="pagination-btn" 
            :disabled="userPage === totalUserPages" 
            @click="changeUserPage(userPage + 1)"
          >
            {{ t('admin.next') }}
          </button>
        </div>
      </div>
    </div>

    <!-- PREMIUM SIDE DRAWER FOR USER STATS (5 nhóm chỉ số) -->
    <div class="drawer-overlay" v-if="showDrawer" @click="closeDrawer"></div>
    <div class="user-detail-drawer" :class="{ open: showDrawer }">
      <div v-if="drawerLoading" class="drawer-loading-state">
        <div class="loading-spinner"></div>
      </div>
      <template v-else-if="selectedUserStats">
        <div class="drawer-header">
          <div class="drawer-user-info">
            <span class="user-avatar-large">{{ getInitials(selectedUserStats.user?.full_name || selectedUserStats.user?.email) }}</span>
            <div class="drawer-name-wrap">
              <h2>{{ selectedUserStats.user?.full_name || 'Thành viên' }}</h2>
              <p class="drawer-email">{{ selectedUserStats.user?.email }}</p>
              <div class="drawer-badges">
                <span class="user-role-badge-table" :class="selectedUserStats.user?.role">
                  {{ selectedUserStats.user?.role }}
                </span>
                <span class="online-badge-table" :class="{ online: selectedUserStats.user?.is_online }">
                  <span class="badge-dot"></span>
                  {{ selectedUserStats.user?.is_online ? t('admin.online') : t('admin.offline') }}
                </span>
              </div>
            </div>
          </div>
          <button class="close-drawer-btn" @click="closeDrawer">✕</button>
        </div>

        <div class="drawer-body">
          <h3 class="drawer-section-title">📊 {{ t('admin.userActivityStats', { name: selectedUserStats.user?.full_name || selectedUserStats.user?.email }) }}</h3>

          <!-- KPI Cards for Single User -->
          <div class="drawer-kpi-grid">
            <div class="kpi-card glass-card">
              <div class="kpi-card-header">
                <span class="kpi-label">Truy cập / Phiên</span>
                <span class="kpi-icon">🖱️</span>
              </div>
              <h4 class="kpi-value">{{ selectedUserStats.traffic?.total_visits }} {{ t('admin.visits') }} / {{ selectedUserStats.traffic?.total_sessions }} {{ t('admin.sessions') }}</h4>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-card-header">
                <span class="kpi-label">Thời gian sử dụng TB</span>
                <span class="kpi-icon">⏱️</span>
              </div>
              <h4 class="kpi-value">{{ formatDuration(selectedUserStats.engagement?.avg_session_duration) }}</h4>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-card-header">
                <span class="kpi-label">Số ngày hoạt động (30d)</span>
                <span class="kpi-icon">📅</span>
              </div>
              <h4 class="kpi-value">{{ selectedUserStats.engagement?.active_days_30d }} {{ t('admin.activeDays') }}</h4>
            </div>

            <div class="kpi-card glass-card">
              <div class="kpi-card-header">
                <span class="kpi-label">Điểm ATS TB / Phỏng vấn TB</span>
                <span class="kpi-icon">🎯</span>
              </div>
              <h4 class="kpi-value">
                {{ selectedUserStats.success?.avg_ats_score }}/100 | {{ selectedUserStats.success?.avg_interview_score }}/10
              </h4>
            </div>
          </div>

          <!-- Feature Usage Bar Chart -->
          <section class="drawer-chart-card glass-card">
            <h4 class="drawer-chart-title">⚙️ Tần suất sử dụng tính năng</h4>
            <div class="drawer-chart-wrapper">
              <Bar :data="userFeatureChartData" :options="userBarChartOptions" />
            </div>
            <div class="feature-extremes">
              <p>⭐️ <strong>Tính năng nhiều nhất:</strong> {{ selectedUserStats.features?.most_used }}</p>
              <p>⚠️ <strong>Tính năng ít nhất:</strong> {{ selectedUserStats.features?.least_used }}</p>
            </div>
          </section>

          <!-- Traffic Referrer Sources Pie -->
          <section class="drawer-chart-card glass-card">
            <h4 class="drawer-chart-title">🌐 Cơ cấu nguồn truy cập</h4>
            <div class="drawer-chart-wrapper-small">
              <Doughnut :data="userTrafficChartData" :options="userDoughnutChartOptions" />
            </div>
          </section>

          <!-- Feature Details Counts -->
          <section class="detail-section glass-card">
            <h4 class="drawer-chart-title">💼 Chi tiết sử dụng tính năng</h4>
            <div class="details-table">
              <div class="detail-row">
                <span>Số CV đã tải lên:</span>
                <span class="detail-val">{{ selectedUserStats.features?.cv_uploads }}</span>
              </div>
              <div class="detail-row">
                <span>Số lượt phân tích CV:</span>
                <span class="detail-val">{{ selectedUserStats.features?.cv_analyses }}</span>
              </div>
              <div class="detail-row">
                <span>Số lượt luyện phỏng vấn:</span>
                <span class="detail-val">{{ selectedUserStats.features?.interviews }} (Hoàn thành: {{ selectedUserStats.success?.completed_interviews }} / {{ selectedUserStats.success?.total_interviews }})</span>
              </div>
              <div class="detail-row">
                <span>Số việc làm đã lưu:</span>
                <span class="detail-val">{{ selectedUserStats.features?.saved_jobs }}</span>
              </div>
            </div>
          </section>

          <!-- Success Details (Recent CVs and Interviews) -->
          <section class="detail-section glass-card">
            <h4 class="drawer-chart-title">📄 5 báo cáo phân tích CV gần nhất</h4>
            <div class="list-container" v-if="selectedUserStats.recent_cvs?.length > 0">
              <div v-for="cv in selectedUserStats.recent_cvs" :key="cv.analysis_id" class="list-item">
                <div class="list-item-left">
                  <span class="list-item-title">{{ cv.filename }}</span>
                  <span class="list-item-sub">{{ formatDateSimple(cv.created_at) }}</span>
                </div>
                <div class="list-item-right">
                  <span class="list-score-badge" :class="getScoreClass(cv.ats_score)">
                    {{ cv.ats_score ? cv.ats_score + ' ATS' : 'N/A' }}
                  </span>
                </div>
              </div>
            </div>
            <p v-else class="text-muted text-center py-4 text-sm">{{ t('admin.noCvs') }}</p>
          </section>

          <section class="detail-section glass-card">
            <h4 class="drawer-chart-title">🎤 5 buổi luyện phỏng vấn gần nhất</h4>
            <div class="list-container" v-if="selectedUserStats.recent_interviews?.length > 0">
              <div v-for="session in selectedUserStats.recent_interviews" :key="session.id" class="list-item">
                <div class="list-item-left">
                  <span class="list-item-title">{{ session.field || 'General' }} ({{ session.level || 'Junior' }})</span>
                  <span class="list-item-sub">{{ session.completed_at ? 'Hoàn thành ngày ' + formatDateSimple(session.completed_at) : 'Chưa hoàn thành' }}</span>
                </div>
                <div class="list-item-right">
                  <span class="list-score-badge" :class="getScoreClass(session.overall_score * 10)">
                    {{ session.overall_score ? session.overall_score.toFixed(1) + '/10' : 'N/A' }}
                  </span>
                </div>
              </div>
            </div>
            <p v-else class="text-muted text-center py-4 text-sm">{{ t('admin.noInterviews') }}</p>
          </section>

          <!-- Recent Access Logs Path -->
          <section class="detail-section glass-card">
            <h4 class="drawer-chart-title">🐾 {{ t('admin.recentVisits') }}</h4>
            <div class="list-container" v-if="selectedUserStats.traffic?.recent_activities?.length > 0">
              <div v-for="(log, idx) in selectedUserStats.traffic.recent_activities" :key="idx" class="list-item list-item-compact">
                <span class="path-text">{{ formatPath(log.path) }}</span>
                <span class="list-item-sub">{{ formatTimeWithDate(log.created_at) }}</span>
              </div>
            </div>
            <p v-else class="text-muted text-center py-4 text-sm">Chưa có nhật ký truy cập.</p>
          </section>

          <!-- Account Info Details -->
          <section class="detail-section glass-card">
            <h4 class="drawer-chart-title">🔐 {{ t('admin.userBriefInfo') }}</h4>
            <div class="details-table">
              <div class="detail-row">
                <span>{{ t('profile.role') || 'Vai trò' }}:</span>
                <select 
                  :value="selectedUserStats.user?.role" 
                  @change="changeUserRole(selectedUserStats.user?.id, $event.target.value)"
                  class="role-changer-select"
                  :disabled="selectedUserStats.user?.id === authStore.user?.id"
                >
                  <option value="user">User</option>
                  <option value="premium">Premium User</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
              <div class="detail-row">
                <span>{{ t('admin.joinedDate') }}:</span>
                <span class="detail-val-muted">{{ formatDateSimple(selectedUserStats.user?.created_at) }}</span>
              </div>
              <div class="detail-row">
                <span>{{ t('admin.lastActive') }}:</span>
                <span class="detail-val-muted">{{ formatTimeWithDate(selectedUserStats.user?.last_login) || 'Chưa đăng nhập' }}</span>
              </div>
              <div class="detail-row">
                <span>ID Tài khoản:</span>
                <span class="detail-val-muted">#{{ selectedUserStats.user?.id }}</span>
              </div>
            </div>
          </section>
        </div>
      </template>
    </div>
  </main>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '../stores/auth'
import api from '../api'
import { Line, Bar, Doughnut } from 'vue-chartjs'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js'

ChartJS.register(
  CategoryScale, LinearScale, PointElement, LineElement,
  BarElement, ArcElement, Title, Tooltip, Legend, Filler
)

const { t } = useI18n()
const authStore = useAuthStore()

const loading = ref(true)
const error = ref(false)
const stats = ref({})
const onlineCount = ref(0)
const onlineUsers = ref([])
const lastUpdated = ref('')
let adminWs = null
const isLightTheme = ref(document.documentElement.classList.contains('light-theme'))
let themeObserver = null

// ──────────────────────────────────────
// Fetch stats from HTTP API
// ──────────────────────────────────────
async function fetchStats() {
  loading.value = true
  error.value = false
  try {
    const { data } = await api.get('/admin/stats')
    stats.value = data
    onlineCount.value = data.users?.online_count ?? 0
    lastUpdated.value = new Date().toLocaleTimeString()
  } catch (err) {
    console.error('Failed to fetch admin stats:', err)
    error.value = true
  } finally {
    loading.value = false
  }
}

// ──────────────────────────────────────
// WebSocket for real-time presence
// ──────────────────────────────────────
function connectAdminWs() {
  const token = authStore.token
  if (!token) return

  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  const host = import.meta.env.VITE_API_URL
    ? new URL(import.meta.env.VITE_API_URL).host
    : window.location.host
  const wsUrl = `${protocol}//${host}/api/v1/admin/ws/admin?token=${token}`

  adminWs = new WebSocket(wsUrl)

  adminWs.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data)
      if (msg.type === 'presence_update') {
        onlineCount.value = msg.online_count
        onlineUsers.value = msg.online_users || []
      }
    } catch (e) {
      console.warn('WS parse error:', e)
    }
  }

  adminWs.onclose = () => {
    // Auto-reconnect after 5s
    setTimeout(connectAdminWs, 5000)
  }

  adminWs.onerror = (err) => {
    console.warn('Admin WS error:', err)
  }
}

// ──────────────────────────────────────
// Helpers
// ──────────────────────────────────────
function formatDuration(seconds) {
  if (!seconds) return '0s'
  const s = Math.round(seconds)
  if (s < 60) return `${s}s`
  const m = Math.floor(s / 60)
  const rem = s % 60
  return `${m}m ${rem}s`
}

function formatTime(isoStr) {
  if (!isoStr) return ''
  return new Date(isoStr).toLocaleTimeString()
}

function formatElapsed(seconds) {
  if (!seconds) return '0s'
  if (seconds < 60) return `${seconds}s`
  const m = Math.floor(seconds / 60)
  return `${m}m`
}

function getInitials(str) {
  if (!str) return '?'
  const parts = str.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
  return str[0].toUpperCase()
}

function formatDateLabel(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  return `${d.getDate()}/${d.getMonth() + 1}`
}

// ──────────────────────────────────────
// Chart Data (computed)
// ──────────────────────────────────────

const dailyVisitsChartData = computed(() => {
  const daily = stats.value.traffic?.daily_visits || []
  return {
    labels: daily.map(d => formatDateLabel(d.date)),
    datasets: [{
      label: t('admin.totalVisits'),
      data: daily.map(d => d.count),
      borderColor: '#818cf8',
      backgroundColor: 'rgba(129, 140, 248, 0.15)',
      tension: 0.4,
      fill: true,
      pointBackgroundColor: '#818cf8',
      pointBorderColor: '#fff',
      pointRadius: 4,
    }]
  }
})

const newUsersChartData = computed(() => {
  const daily = stats.value.users?.new_users_daily || []
  return {
    labels: daily.map(d => formatDateLabel(d.date)),
    datasets: [{
      label: t('admin.newUsersDaily'),
      data: daily.map(d => d.count),
      borderColor: '#34d399',
      backgroundColor: 'rgba(52, 211, 153, 0.15)',
      tension: 0.4,
      fill: true,
      pointBackgroundColor: '#34d399',
      pointBorderColor: '#fff',
      pointRadius: 4,
    }]
  }
})

const featureUsageChartData = computed(() => {
  const features = stats.value.features || {}
  return {
    labels: [
      t('admin.cvUploads'),
      t('admin.cvAnalyses'),
      t('admin.interviews'),
      t('admin.savedJobs'),
    ],
    datasets: [{
      label: t('admin.featureUsage'),
      data: [
        features.cv_uploads || 0,
        features.cv_analyses || 0,
        features.interviews || 0,
        features.saved_jobs || 0,
      ],
      backgroundColor: [
        'rgba(99, 102, 241, 0.7)',
        'rgba(52, 211, 153, 0.7)',
        'rgba(251, 191, 36, 0.7)',
        'rgba(244, 114, 182, 0.7)',
      ],
      borderColor: [
        '#6366f1',
        '#34d399',
        '#fbbf24',
        '#f472b6',
      ],
      borderWidth: 2,
      borderRadius: 8,
    }]
  }
})

const trafficSourcesChartData = computed(() => {
  const sources = stats.value.traffic?.sources || { Direct: 0, Google: 0, Facebook: 0, Instagram: 0, LinkedIn: 0, TikTok: 0, 'Twitter/X': 0, Other: 0 }
  return {
    labels: Object.keys(sources),
    datasets: [{
      data: Object.values(sources),
      backgroundColor: [
        'rgba(99, 102, 241, 0.8)',  // Direct - Indigo
        'rgba(52, 211, 153, 0.8)',  // Google - Emerald
        'rgba(59, 130, 246, 0.8)',  // Facebook - Blue
        'rgba(236, 72, 153, 0.8)',  // Instagram - Pink
        'rgba(14, 165, 233, 0.8)',  // LinkedIn - Light Blue
        'rgba(244, 63, 94, 0.8)',   // TikTok - Rose/Red
        'rgba(20, 184, 166, 0.8)',  // Twitter/X - Teal
        'rgba(156, 163, 175, 0.6)', // Other - Gray
      ],
      borderColor: isLightTheme.value ? '#ffffff' : '#1e1b4b',
      borderWidth: 2,
    }]
  }
})

// ──────────────────────────────────────
// Chart Options
// ──────────────────────────────────────
// ──────────────────────────────────────
// Chart Options
// ──────────────────────────────────────
const chartTextColor = computed(() => isLightTheme.value ? '#475569' : '#94a3b8')
const chartGridColor = computed(() => isLightTheme.value ? 'rgba(0, 0, 0, 0.06)' : 'rgba(255, 255, 255, 0.06)')

const lineChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  interaction: { intersect: false, mode: 'index' },
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: isLightTheme.value ? 'rgba(255, 255, 255, 0.95)' : 'rgba(30, 27, 75, 0.9)',
      titleColor: isLightTheme.value ? '#0f172a' : '#e2e8f0',
      bodyColor: isLightTheme.value ? '#334155' : '#e2e8f0',
      borderColor: isLightTheme.value ? '#cbd5e1' : 'rgba(99, 102, 241, 0.3)',
      borderWidth: 1,
      cornerRadius: 8,
      padding: 12,
    }
  },
  scales: {
    x: {
      grid: { color: chartGridColor.value },
      ticks: { color: chartTextColor.value, font: { size: 11 } },
    },
    y: {
      grid: { color: chartGridColor.value },
      ticks: { color: chartTextColor.value, font: { size: 11 }, precision: 0 },
      beginAtZero: true,
    }
  }
}))

const barChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    tooltip: {
      backgroundColor: isLightTheme.value ? 'rgba(255, 255, 255, 0.95)' : 'rgba(30, 27, 75, 0.9)',
      titleColor: isLightTheme.value ? '#0f172a' : '#e2e8f0',
      bodyColor: isLightTheme.value ? '#334155' : '#e2e8f0',
      borderColor: isLightTheme.value ? '#cbd5e1' : 'rgba(99, 102, 241, 0.3)',
      borderWidth: 1,
      cornerRadius: 8,
      padding: 12,
    }
  },
  scales: {
    x: {
      grid: { display: false },
      ticks: { color: chartTextColor.value, font: { size: 11 } },
    },
    y: {
      grid: { color: chartGridColor.value },
      ticks: { color: chartTextColor.value, font: { size: 11 }, precision: 0 },
      beginAtZero: true,
    }
  }
}))

const doughnutChartOptions = computed(() => ({
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        color: chartTextColor.value,
        padding: 16,
        font: { size: 12 },
        usePointStyle: true,
        pointStyleWidth: 12,
      }
    },
    tooltip: {
      backgroundColor: isLightTheme.value ? 'rgba(255, 255, 255, 0.95)' : 'rgba(30, 27, 75, 0.9)',
      titleColor: isLightTheme.value ? '#0f172a' : '#e2e8f0',
      bodyColor: isLightTheme.value ? '#334155' : '#e2e8f0',
      borderColor: isLightTheme.value ? '#cbd5e1' : 'rgba(99, 102, 241, 0.3)',
      borderWidth: 1,
      cornerRadius: 8,
      padding: 12,
    }
  },
  cutout: '65%',
}))

// ──────────────────────────────────────
// User Management & Activity Tracking (quantri_admin.md)
// ──────────────────────────────────────
const activeTab = ref('overview')

// User list pagination, filter, search
const usersList = ref([])
const usersTotal = ref(0)
const usersLoading = ref(false)
const userSearch = ref('')
const filterRole = ref('')
const filterStatus = ref('')
const filterOnline = ref('all')
const filterRegDate = ref('all')
const userPage = ref(1)
const userLimit = ref(10)

// Single User Detail Drawer
const showDrawer = ref(false)
const drawerLoading = ref(false)
const selectedUserId = ref(null)
const selectedUserStats = ref(null)

const totalUserPages = computed(() => {
  return Math.ceil(usersTotal.value / userLimit.value) || 1
})

// Watch tab switches to reload users list
watch(activeTab, (newTab) => {
  if (newTab === 'users') {
    fetchUsers(0)
  }
})

// Load users list with query filters
async function fetchUsers(page = 0) {
  usersLoading.value = true
  try {
    const skip = page * userLimit.value
    let url = `/admin/users?skip=${skip}&limit=${userLimit.value}&search=${encodeURIComponent(userSearch.value)}&role=${filterRole.value}&online_status=${filterOnline.value}&reg_date=${filterRegDate.value}`
    if (filterStatus.value === 'active') {
      url += '&is_active=true'
    } else if (filterStatus.value === 'blocked') {
      url += '&is_active=false'
    }
    const { data } = await api.get(url)
    usersList.value = data.users || []
    usersTotal.value = data.total || 0
    userPage.value = page + 1
  } catch (err) {
    console.error('Failed to fetch admin users:', err)
  } finally {
    usersLoading.value = false
  }
}

// Search input debounce
let searchTimeout = null
function onUserSearchInput() {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    fetchUsers(0)
  }, 400)
}

function changeUserPage(newPage) {
  if (newPage < 1 || newPage > totalUserPages.value) return
  fetchUsers(newPage - 1)
}

// Toggle status Active/Blocked
async function toggleUserStatus(user) {
  const confirmed = confirm(
    user.is_active 
      ? t('admin.confirmLock') 
      : t('admin.confirmUnlock')
  )
  if (!confirmed) return

  try {
    const { data } = await api.post(`/admin/users/${user.id}/toggle-status`)
    if (data.status === 'updated') {
      user.is_active = data.is_active
      alert(data.is_active ? t('admin.unlockSuccess') : t('admin.lockSuccess'))
      // Update stats detail drawer if showing this user
      if (selectedUserStats.value && selectedUserStats.value.user.id === user.id) {
        selectedUserStats.value.user.is_active = data.is_active
      }
    }
  } catch (err) {
    console.error('Failed to toggle status:', err)
    const errorMsg = err.response?.data?.detail || 'Lỗi thao tác'
    alert(errorMsg === 'Cannot lock yourself' ? t('admin.cannotLockSelf') : errorMsg)
  }
}

// Change user role (admin, premium, user)
async function changeUserRole(userId, newRole) {
  if (userId === authStore.user?.id) {
    alert('Bạn không thể tự thay đổi quyền của chính mình')
    return
  }
  const confirmed = confirm(`Bạn có chắc chắn muốn thay đổi vai trò thành viên này thành "${newRole.toUpperCase()}"?`)
  if (!confirmed) return

  try {
    const { data } = await api.post(`/admin/users/${userId}/role`, { role: newRole })
    if (data.status === 'updated') {
      alert('Thay đổi vai trò thành công!')
      if (selectedUserStats.value && selectedUserStats.value.user.id === userId) {
        selectedUserStats.value.user.role = data.role
      }
      const u = usersList.value.find(user => user.id === userId)
      if (u) {
        u.role = data.role
      }
    }
  } catch (err) {
    console.error('Failed to change user role:', err)
    alert(err.response?.data?.detail || 'Lỗi thao tác')
  }
}

// Open sliding drawer showing single user metrics (quantri_admin.md)
async function openUserDetail(userId) {
  selectedUserId.value = userId
  showDrawer.value = true
  drawerLoading.value = true
  try {
    const { data } = await api.get(`/admin/users/${userId}/stats`)
    selectedUserStats.value = data
  } catch (err) {
    console.error('Failed to load user stats:', err)
    alert('Không thể tải chi tiết hoạt động của thành viên này')
    showDrawer.value = false
  } finally {
    drawerLoading.value = false
  }
}

function closeDrawer() {
  showDrawer.value = false
  selectedUserId.value = null
  selectedUserStats.value = null
}

// Helpers
function formatDateSimple(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const dd = String(d.getDate()).padStart(2, '0')
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const yyyy = d.getFullYear()
  return `${dd}/${mm}/${yyyy}`
}

function formatTimeWithDate(isoStr) {
  if (!isoStr) return ''
  const d = new Date(isoStr)
  const dd = String(d.getDate()).padStart(2, '0')
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const yyyy = d.getFullYear()
  const time = d.toLocaleTimeString()
  return `${dd}/${mm}/${yyyy} ${time}`
}

function getScoreClass(score) {
  if (!score) return 'score-low'
  if (score >= 80) return 'score-high'
  if (score >= 50) return 'score-mid'
  return 'score-low'
}

function formatPath(path) {
  if (!path) return ''
  const base = path.split('?')[0].split('#')[0]
  
  if (base === '/') return t('nav.about') || 'Giới thiệu'
  if (base === '/login') return t('nav.login') || 'Đăng nhập'
  if (base === '/register') return t('nav.register') || 'Đăng ký'
  if (base === '/about') return t('nav.about') || 'Giới thiệu'
  if (base === '/dashboard') return t('nav.dashboard') || 'Bảng điều khiển'
  if (base === '/job-recommendation') return t('nav.matchJobs') || 'Gợi ý việc làm'
  if (base === '/job-search') return t('nav.searchJobs') || 'Tìm kiếm việc làm'
  if (base === '/cv-history') return t('nav.cvHistory') || 'Lịch sử phân tích CV'
  if (base === '/saved-jobs') return t('nav.savedJobs') || 'Job yêu thích'
  if (base === '/interview') return t('nav.mockInterview') || 'Luyện phỏng vấn'
  if (base === '/admin') return t('nav.admin') || 'Quản trị'
  
  if (base.startsWith('/cv-analysis')) return t('nav.cvAnalysis') || 'Phân tích CV'
  if (base.startsWith('/interview/result')) return t('mockInterview.resultTitle') || 'Đánh giá kết quả phỏng vấn'
  
  return path
}

// Computed charts for selected user stats
const userFeatureChartData = computed(() => {
  if (!selectedUserStats.value?.features) return { labels: [], datasets: [] }
  const f = selectedUserStats.value.features
  return {
    labels: [
      t('admin.cvUploads'),
      t('admin.cvAnalyses'),
      t('admin.interviews'),
      t('admin.savedJobs'),
    ],
    datasets: [{
      label: t('admin.featureUsage'),
      data: [
        f.cv_uploads || 0,
        f.cv_analyses || 0,
        f.interviews || 0,
        f.saved_jobs || 0,
      ],
      backgroundColor: [
        'rgba(99, 102, 241, 0.7)',
        'rgba(52, 211, 153, 0.7)',
        'rgba(251, 191, 36, 0.7)',
        'rgba(244, 114, 182, 0.7)',
      ],
      borderColor: [
        '#6366f1',
        '#34d399',
        '#fbbf24',
        '#f472b6',
      ],
      borderWidth: 2,
      borderRadius: 6,
    }]
  }
})

const userTrafficChartData = computed(() => {
  if (!selectedUserStats.value?.traffic?.sources) return { labels: [], datasets: [] }
  const s = selectedUserStats.value.traffic.sources
  return {
    labels: Object.keys(s),
    datasets: [{
      data: Object.values(s),
      backgroundColor: [
        'rgba(99, 102, 241, 0.8)',  // Direct - Indigo
        'rgba(52, 211, 153, 0.8)',  // Google - Emerald
        'rgba(59, 130, 246, 0.8)',  // Facebook - Blue
        'rgba(236, 72, 153, 0.8)',  // Instagram - Pink
        'rgba(14, 165, 233, 0.8)',  // LinkedIn - Light Blue
        'rgba(244, 63, 94, 0.8)',   // TikTok - Rose/Red
        'rgba(20, 184, 166, 0.8)',  // Twitter/X - Teal
        'rgba(156, 163, 175, 0.6)', // Other - Gray
      ],
      borderColor: isLightTheme.value ? '#ffffff' : '#1e1b4b',
      borderWidth: 2,
    }]
  }
})

const userBarChartOptions = barChartOptions
const userDoughnutChartOptions = doughnutChartOptions

// ──────────────────────────────────────
// Lifecycle
// ──────────────────────────────────────
onMounted(() => {
  fetchStats()
  connectAdminWs()
  fetchUsers(0)

  // Observe theme class changes on documentElement
  themeObserver = new MutationObserver(() => {
    isLightTheme.value = document.documentElement.classList.contains('light-theme')
  })
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] })
})

onUnmounted(() => {
  if (adminWs) {
    adminWs.onclose = null // Prevent reconnect
    adminWs.close()
  }
  if (themeObserver) {
    themeObserver.disconnect()
  }
})
</script>

<style scoped>
.admin-container {
  max-width: 1280px;
  margin: 0 auto;
  padding: 32px 24px 64px;
}

.admin-header {
  margin-bottom: 32px;
}

.section-tag {
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--text-accent);
  margin-bottom: 8px;
}

.welcome-text {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--text-heading);
  margin: 0 0 8px;
  line-height: 1.2;
}

.subtitle-text {
  font-size: 0.95rem;
  color: var(--text-label);
  margin: 0;
}

/* ═══════════ LOADING / ERROR ═══════════ */
.loading-box {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 48px;
  font-size: 0.95rem;
  color: var(--text-label);
}

.loading-spinner {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(99, 102, 241, 0.2);
  border-top-color: #818cf8;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.error-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  padding: 48px;
  text-align: center;
  color: #f87171;
}

.btn-retry {
  padding: 10px 24px;
  background: var(--gradient-primary);
  color: var(--text-on-primary);
  border: none;
  border-radius: 9999px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-retry:hover {
  transform: translateY(-1px);
  opacity: 0.9;
}

/* ═══════════ KPI CARDS ═══════════ */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
  gap: 16px;
  margin-bottom: 28px;
}

.kpi-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 12px;
  padding: 20px;
  border-radius: var(--radius-lg, 16px);
  background: var(--bg-glass);
  border: 1px solid var(--border-glass);
  box-shadow: var(--shadow-sm);
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.kpi-card:hover {
  transform: translateY(-4px);
  border-color: var(--primary);
  box-shadow: var(--shadow-glow);
  background: var(--bg-hover-card);
}

.kpi-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  width: 100%;
  gap: 12px;
}

.kpi-online {
  border: 1px solid rgba(52, 211, 153, 0.25);
  box-shadow: 0 4px 30px rgba(52, 211, 153, 0.05);
}

.kpi-online:hover {
  border-color: rgba(52, 211, 153, 0.5);
  box-shadow: 0 12px 32px rgba(52, 211, 153, 0.2);
  background: var(--bg-hover-card);
}

.kpi-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(99, 102, 241, 0.1);
  flex-shrink: 0;
}

.pulse-green {
  background: rgba(52, 211, 153, 0.15);
  animation: pulseGlow 2s ease-in-out infinite;
}

@keyframes pulseGlow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.3); }
  50% { box-shadow: 0 0 16px 4px rgba(52, 211, 153, 0.15); }
}

.kpi-icon {
  font-size: 1.1rem;
}

.kpi-label {
  font-size: 0.82rem;
  font-weight: 500;
  color: var(--text-label);
  margin: 0;
  line-height: 1.4;
  word-break: break-word;
}

.kpi-value {
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--text-heading);
  margin: 0;
  line-height: 1.1;
}

/* ═══════════ ONLINE USERS ═══════════ */
.online-section {
  padding: 24px;
  margin-bottom: 28px;
  border-radius: var(--radius-lg, 16px);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 16px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.live-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #34d399;
  display: inline-block;
  animation: blink 1.5s ease-in-out infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

.online-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.online-user-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(99, 102, 241, 0.05);
  border: 1px solid rgba(99, 102, 241, 0.12);
  border-radius: 12px;
  min-width: 260px;
}

.online-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--gradient-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 700;
  font-size: 0.85rem;
  flex-shrink: 0;
}

.online-info {
  min-width: 0;
}

.online-name {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.online-meta {
  font-size: 0.72rem;
  color: var(--text-label);
  margin: 2px 0 0;
}

/* ═══════════ CHARTS ═══════════ */
.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 28px;
}

.chart-card {
  padding: 24px;
  border-radius: var(--radius-lg, 16px);
}

.chart-card-small {
  max-width: 100%;
}

.chart-wrapper {
  height: 280px;
  position: relative;
}

.chart-wrapper-doughnut {
  height: 260px;
  max-width: 320px;
  margin: 0 auto;
}

/* ═══════════ STATS TABLES ═══════════ */
.tables-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 28px;
}

.table-card {
  padding: 24px;
  border-radius: var(--radius-lg, 16px);
}

.stats-table {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid rgba(148, 163, 184, 0.08);
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-label {
  font-size: 0.88rem;
  color: var(--text-label);
}

.stat-val {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-heading);
}

.stat-val.highlight {
  color: #818cf8;
  font-size: 1.1rem;
}

/* ═══════════ REFRESH ═══════════ */
.refresh-row {
  display: flex;
  align-items: center;
  gap: 16px;
  justify-content: center;
  padding: 16px 0;
}

.btn-refresh {
  padding: 10px 28px;
  background: var(--bg-hover-subtle);
  color: var(--primary);
  border: 1px solid var(--border-color);
  border-radius: 9999px;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-refresh:hover:not(:disabled) {
  background: var(--hover-bg);
  border-color: var(--primary);
  color: var(--primary-light);
  transform: translateY(-1px);
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.last-updated {
  font-size: 0.78rem;
  color: var(--text-label);
}

/* ═══════════ ADMIN TABS ═══════════ */
.admin-tabs {
  display: flex;
  gap: 8px;
  padding: 6px;
  background: var(--bg-card-inner);
  border: 1px solid var(--border-color);
  border-radius: 14px;
  margin-bottom: 32px;
  max-width: fit-content;
}

.tab-btn {
  padding: 10px 24px;
  background: transparent;
  color: var(--text-label);
  border: none;
  border-radius: 10px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  gap: 8px;
}

.tab-btn:hover {
  color: var(--text-heading);
}

.tab-btn.active {
  color: #fff;
  background: var(--gradient-primary, linear-gradient(135deg, #6366f1, #818cf8));
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
  transform: scale(1.02);
}

/* ═══════════ USER MANAGEMENT TAB ═══════════ */
.users-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 20px;
  border-radius: var(--radius-lg, 16px);
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.search-input-wrap {
  position: relative;
  flex: 1;
  min-width: 280px;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.9rem;
  color: var(--text-label);
}

.search-input-wrap input {
  width: 100%;
  padding: 12px 16px 12px 40px;
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  color: var(--text-primary);
  font-size: 0.88rem;
  transition: all 0.2s ease;
  outline: none;
}

.search-input-wrap input:focus {
  border-color: var(--primary);
  background: var(--bg-hover-card);
  box-shadow: 0 0 0 3px rgba(14, 165, 233, 0.15);
}

.filters-wrap {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.filters-wrap select {
  padding: 12px 16px;
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  border-radius: 10px;
  color: var(--text-primary);
  font-size: 0.88rem;
  outline: none;
  cursor: pointer;
  min-width: 150px;
  transition: all 0.2s ease;
}

.filters-wrap select:focus {
  border-color: var(--primary);
}

/* ═══════════ USERS TABLE ═══════════ */
.users-table-wrap {
  border-radius: var(--radius-lg, 16px);
  overflow-x: auto;
  position: relative;
  min-height: 200px;
}

.users-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
  font-size: 0.88rem;
}

.users-table th {
  padding: 16px 20px;
  font-weight: 600;
  color: var(--text-label);
  border-bottom: 1px solid var(--border-divider);
  background: var(--bg-card-inner);
  text-transform: uppercase;
  font-size: 0.72rem;
  letter-spacing: 0.05em;
}

.users-table td {
  padding: 16px 20px;
  color: var(--text-primary);
  border-bottom: 1px solid var(--border-color);
}

.user-row {
  cursor: pointer;
  transition: all 0.2s ease;
}

.user-row:hover {
  background: var(--dropdown-item-hover-bg);
}

.user-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-avatar-small {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--gradient-primary, linear-gradient(135deg, #6366f1, #818cf8));
  color: #fff;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.2);
}

.user-avatar-large {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  background: var(--gradient-primary, linear-gradient(135deg, #6366f1, #818cf8));
  color: #fff;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  box-shadow: 0 4px 16px rgba(99, 102, 241, 0.3);
  flex-shrink: 0;
}

.user-role-badge-table {
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  display: inline-block;
}

.user-role-badge-table.admin {
  background: var(--role-admin-bg);
  color: var(--role-admin-text);
  border: 1px solid var(--role-admin-border);
}

.user-role-badge-table.user {
  background: var(--role-user-bg);
  color: var(--role-user-text);
  border: 1px solid var(--role-user-border);
}

.status-dot-badge {
  padding: 4px 10px;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-dot-badge.active {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}

.status-dot-badge.blocked {
  background: rgba(156, 163, 175, 0.15);
  color: var(--text-label);
}

.online-badge-table {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-label);
}

.online-badge-table.online {
  color: #10b981;
}

.online-badge-table .badge-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--text-muted);
  display: inline-block;
}

.online-badge-table.online .badge-dot {
  background: #10b981;
  box-shadow: 0 0 8px #10b981;
  animation: blink 1.5s ease-in-out infinite;
}

.text-right {
  text-align: right;
}

.text-muted {
  color: var(--text-label);
}

.font-semibold {
  font-weight: 600;
}

.action-btn {
  padding: 6px 12px;
  border: none;
  border-radius: 8px;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn.btn-lock {
  background: rgba(239, 68, 68, 0.08);
  color: var(--role-admin-text);
  border: 1px solid var(--role-admin-border);
}

.action-btn.btn-lock:hover {
  background: rgba(239, 68, 68, 0.18);
  transform: translateY(-1px);
}

.action-btn.btn-unlock {
  background: rgba(16, 185, 129, 0.08);
  color: #10b981;
  border: 1px solid rgba(16, 185, 129, 0.2);
}

.action-btn.btn-unlock:hover {
  background: rgba(16, 185, 129, 0.18);
  transform: translateY(-1px);
}

/* ═══════════ PAGINATION ═══════════ */
.pagination-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 16px;
  padding: 0 4px;
}

.pagination-info {
  font-size: 0.8rem;
  color: var(--text-label);
}

.pagination-btns {
  display: flex;
  gap: 8px;
}

.pagination-btn {
  padding: 8px 16px;
  background: var(--pill-bg);
  border: 1px solid var(--border-card);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.pagination-btn:hover:not(:disabled) {
  background: var(--hover-bg);
  border-color: var(--primary);
}

.pagination-btn:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

/* ═══════════ PREMIUM SIDE DRAWER ═══════════ */
.drawer-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: var(--overlay-bg);
  backdrop-filter: blur(8px);
  z-index: 999;
  animation: fadeIn 0.2s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.user-detail-drawer {
  position: fixed;
  top: 0;
  right: 0;
  width: 520px;
  max-width: 100%;
  height: 100vh;
  background: var(--bg-modal);
  border-left: 1px solid var(--border-card);
  box-shadow: var(--shadow-modal);
  z-index: 1000;
  transform: translateX(100%);
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  flex-direction: column;
}

.user-detail-drawer.open {
  transform: translateX(0);
}

.drawer-loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px;
  border-bottom: 1px solid var(--border-color);
}

.drawer-user-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.drawer-name-wrap h2 {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-heading);
  margin: 0 0 4px;
}

.drawer-email {
  font-size: 0.85rem;
  color: var(--text-secondary);
  margin: 0 0 8px;
}

.drawer-badges {
  display: flex;
  gap: 8px;
  align-items: center;
}

.close-drawer-btn {
  background: var(--pill-bg);
  border: 1px solid var(--border-card);
  color: var(--text-secondary);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;
  transition: all 0.2s ease;
}

.close-drawer-btn:hover {
  background: var(--hover-bg);
  color: var(--text-primary);
}

.drawer-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.drawer-section-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--primary);
  margin: 0 0 4px;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.drawer-kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.drawer-kpi-grid .kpi-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 8px;
  padding: 16px;
  border-radius: 12px;
}

.drawer-kpi-grid .kpi-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.drawer-kpi-grid .kpi-icon {
  font-size: 1.1rem;
}

.drawer-kpi-grid .kpi-label {
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--text-label);
  margin: 0;
}

.drawer-kpi-grid .kpi-value {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-heading);
  margin: 0;
  line-height: 1.2;
}

.drawer-chart-card {
  padding: 20px;
  border-radius: 14px;
}

.drawer-chart-title {
  font-size: 0.88rem;
  font-weight: 600;
  color: var(--text-heading);
  margin: 0 0 14px;
}

.drawer-chart-wrapper {
  height: 180px;
  position: relative;
}

.drawer-chart-wrapper-small {
  height: 140px;
  position: relative;
}

.feature-extremes {
  margin-top: 14px;
  padding-top: 10px;
  border-top: 1px solid var(--border-divider);
  font-size: 0.78rem;
  display: flex;
  justify-content: space-between;
}

.feature-extremes p {
  margin: 0;
  color: var(--text-label);
}

.detail-section {
  padding: 20px;
  border-radius: 14px;
}

.details-table {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.82rem;
}

.detail-row span:first-child {
  color: var(--text-label);
}

.detail-val {
  font-weight: 600;
  color: var(--text-primary);
}

.detail-val-muted {
  color: var(--text-primary);
  opacity: 0.85;
}

.list-container {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.list-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  background: var(--bg-card-inner);
  border: 1px solid var(--border-card);
  border-radius: 10px;
}

.list-item-compact {
  padding: 8px 12px;
  flex-direction: row;
  justify-content: space-between;
}

.list-item-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.list-item-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.list-item-sub {
  font-size: 0.7rem;
  color: var(--text-label);
}

.path-text {
  font-family: monospace;
  font-size: 0.75rem;
  color: var(--primary);
}

.list-score-badge {
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
}

.list-score-badge.score-high {
  background: rgba(16, 185, 129, 0.12);
  color: #10b981;
}

.list-score-badge.score-mid {
  background: rgba(245, 158, 11, 0.12);
  color: #f59e0b;
}

.list-score-badge.score-low {
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
}

.italic {
  font-style: italic;
}

.text-xs {
  font-size: 0.75rem;
}

/* ═══════════ LIVE STATUS & RECENT ACTIVITIES ROW ═══════════ */
.live-status-row {
  display: grid;
  grid-template-columns: 1.2fr 1.8fr;
  gap: 20px;
  margin-bottom: 28px;
}
@media (max-width: 992px) {
  .live-status-row {
    grid-template-columns: 1fr;
  }
}

.live-dot.inactive {
  background: var(--text-muted);
  animation: none;
}

.recent-activities-section {
  padding: 24px;
  border-radius: var(--radius-lg, 16px);
  display: flex;
  flex-direction: column;
}

.activity-timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
  position: relative;
  padding-left: 20px;
  border-left: 2px solid var(--border-color);
  margin-left: 10px;
}

.activity-item {
  position: relative;
  display: flex;
  flex-direction: column;
}

.activity-dot {
  position: absolute;
  left: -27px;
  top: 6px;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--bg-card);
  background: var(--text-muted);
}

.activity-dot.register {
  background: #10b981;
}

.activity-dot.upload {
  background: #3b82f6;
}

.activity-dot.analysis {
  background: #6366f1;
}

.activity-dot.interview {
  background: #f59e0b;
}

.activity-dot.save_job {
  background: #ec4899;
}

.activity-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}

.activity-desc {
  font-size: 0.88rem;
  color: var(--text-primary);
  margin: 0;
}

.activity-time {
  font-size: 0.75rem;
  color: var(--text-label);
  white-space: nowrap;
}

@media (max-width: 576px) {
  .activity-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}

/* ═══════════ USER ROLE CHANGER & TABLE MINI DOT ═══════════ */
.role-changer-select {
  padding: 6px 12px;
  background: var(--input-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 0.8rem;
  outline: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.role-changer-select:focus {
  border-color: var(--primary);
}

.user-role-badge-table.premium {
  background: var(--role-premium-bg);
  color: var(--role-premium-text);
  border: 1px solid var(--role-premium-border);
}

.avatar-wrap {
  position: relative;
  display: inline-block;
  flex-shrink: 0;
}

.online-status-dot-mini {
  position: absolute;
  right: -2px;
  bottom: -2px;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: 2px solid var(--bg-card);
  background: var(--text-muted);
}

.online-status-dot-mini.online {
  background: #10b981;
  box-shadow: 0 0 6px #10b981;
}

/* ═══════════ RESPONSIVE ═══════════ */
@media (max-width: 768px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .charts-row {
    grid-template-columns: 1fr;
  }

  .tables-row {
    grid-template-columns: 1fr;
  }

  .welcome-text {
    font-size: 1.4rem;
  }
}

@media (max-width: 480px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }

  .admin-container {
    padding: 20px 16px 48px;
  }
}
</style>
