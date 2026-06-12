"""
CV MENTOR — Admin Dashboard API
=================================
WebSocket quản lý trạng thái Online/Offline + HTTP API thống kê 5 nhóm chỉ số.
"""

from __future__ import annotations
import asyncio
from datetime import datetime, timezone, timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, distinct, text

from database.connection import AsyncSessionLocal, AsyncSession
from database.models import (
    User, CVUpload, CVAnalysis, InterviewSession,
    SavedJob, AccessLog, UserSession,
)
from api.dependencies import require_admin
from core.security import decode_access_token
from core.logger import logger

router = APIRouter()


# ──────────────────────────────────────────────
# WebSocket Connection Manager
# ──────────────────────────────────────────────
class ConnectionManager:
    """Quản lý kết nối WebSocket cho user presence và admin dashboard."""

    def __init__(self):
        # {user_id: {"ws": WebSocket, "start_time": datetime, "email": str, "name": str}}
        self.active_users: dict[int, dict] = {}
        # Danh sách các WebSocket admin đang lắng nghe
        self.admin_connections: list[WebSocket] = []

    @property
    def online_count(self) -> int:
        return len(self.active_users)

    @property
    def online_user_list(self) -> list[dict]:
        result = []
        for uid, info in self.active_users.items():
            elapsed = (datetime.now(timezone.utc) - info["start_time"]).total_seconds()
            result.append({
                "user_id": uid,
                "email": info.get("email", ""),
                "name": info.get("name", ""),
                "online_since": info["start_time"].isoformat(),
                "elapsed_seconds": int(elapsed),
            })
        return result

    async def connect_user(self, user_id: int, ws: WebSocket, email: str = "", name: str = ""):
        self.active_users[user_id] = {
            "ws": ws,
            "start_time": datetime.now(timezone.utc),
            "email": email,
            "name": name,
        }
        await self._broadcast_to_admins()

    async def disconnect_user(self, user_id: int):
        info = self.active_users.pop(user_id, None)
        if info:
            duration = int((datetime.now(timezone.utc) - info["start_time"]).total_seconds())
            # Lưu phiên vào DB
            async with AsyncSessionLocal() as db:
                session_record = UserSession(
                    user_id=user_id,
                    login_time=info["start_time"],
                    logout_time=datetime.now(timezone.utc),
                    duration=duration,
                )
                db.add(session_record)
                await db.commit()
        await self._broadcast_to_admins()

    async def connect_admin(self, ws: WebSocket):
        self.admin_connections.append(ws)

    def disconnect_admin(self, ws: WebSocket):
        if ws in self.admin_connections:
            self.admin_connections.remove(ws)

    async def _broadcast_to_admins(self):
        """Gửi trạng thái online mới nhất tới tất cả admin đang kết nối."""
        payload = {
            "type": "presence_update",
            "online_count": self.online_count,
            "online_users": self.online_user_list,
        }
        dead = []
        for ws in self.admin_connections:
            try:
                await ws.send_json(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect_admin(ws)


manager = ConnectionManager()


# ──────────────────────────────────────────────
# WebSocket: User Presence
# ──────────────────────────────────────────────
@router.websocket("/ws/presence")
async def ws_presence(ws: WebSocket, token: str = Query(default="")):
    """Người dùng kết nối WS này khi truy cập web → server theo dõi Online/Offline."""
    await ws.accept()
    user_id = None
    try:
        # Giải mã token để lấy user_id
        if token:
            payload = decode_access_token(token)
            user_id = int(payload.get("sub", 0))
        if not user_id:
            await ws.close(code=4001, reason="Token không hợp lệ")
            return

        # Lấy thông tin user từ DB
        email, name = "", ""
        async with AsyncSessionLocal() as db:
            user = await db.get(User, user_id)
            if user:
                email = user.email or ""
                name = user.full_name or ""

        await manager.connect_user(user_id, ws, email, name)
        logger.info(f"🟢 User {user_id} ({email}) connected via WebSocket")

        # Giữ kết nối mở, chờ tin nhắn hoặc ngắt kết nối
        while True:
            # Đọc ping/pong hoặc bất cứ gì client gửi
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WS presence error user={user_id}: {e}")
    finally:
        if user_id:
            await manager.disconnect_user(user_id)
            logger.info(f"🔴 User {user_id} disconnected from WebSocket")


# ──────────────────────────────────────────────
# WebSocket: Admin Dashboard Real-time
# ──────────────────────────────────────────────
@router.websocket("/ws/admin")
async def ws_admin(ws: WebSocket, token: str = Query(default="")):
    """Admin kết nối để nhận cập nhật real-time về số lượng Online."""
    await ws.accept()
    try:
        # Xác thực admin
        if token:
            payload = decode_access_token(token)
            user_id = int(payload.get("sub", 0))
            async with AsyncSessionLocal() as db:
                user = await db.get(User, user_id)
                if not user or user.role != "admin":
                    await ws.close(code=4003, reason="Không có quyền admin")
                    return
        else:
            await ws.close(code=4001, reason="Thiếu token")
            return

        await manager.connect_admin(ws)

        # Gửi trạng thái ban đầu
        await ws.send_json({
            "type": "presence_update",
            "online_count": manager.online_count,
            "online_users": manager.online_user_list,
        })

        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning(f"WS admin error: {e}")
    finally:
        manager.disconnect_admin(ws)


# ──────────────────────────────────────────────
# HTTP: Track page view
# ──────────────────────────────────────────────
class TrackPayload(BaseModel):
    path: str
    referrer: str | None = None


from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

_optional_bearer = HTTPBearer(auto_error=False)


@router.post("/track")
async def track_page_view(
    payload: TrackPayload,
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_optional_bearer)] = None,
):
    """Frontend gửi log khi chuyển route để ghi nhận lượt truy cập (không yêu cầu đăng nhập)."""
    # Lấy user_id nếu có token hợp lệ (optional)
    user_id = None
    if credentials and credentials.credentials:
        try:
            token_data = decode_access_token(credentials.credentials)
            user_id = int(token_data.get("sub", 0)) or None
        except Exception:
            pass

    # Lấy IP thực từ request
    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    if not client_ip:
        client_ip = request.client.host if request.client else "0.0.0.0"

    async with AsyncSessionLocal() as db:
        log = AccessLog(
            ip=client_ip,
            user_id=user_id,
            path=payload.path,
            referrer=payload.referrer,
        )
        db.add(log)
        await db.commit()
    return {"status": "tracked"}


# ──────────────────────────────────────────────
# HTTP: Dashboard Stats (5 nhóm chỉ số)
# ──────────────────────────────────────────────
@router.get("/stats")
async def get_admin_stats(
    request: Request,
    admin: Annotated[User, Depends(require_admin)],
):
    vietnam_tz = timezone(timedelta(hours=7))
    local_now = datetime.now(vietnam_tz)
    now = local_now
    
    # Tạo danh sách 7 ngày gần nhất (đảm bảo đầy đủ ngày liên tiếp trên biểu đồ)
    last_7_days = [(local_now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0) for i in range(7)]
    last_7_days.reverse()
    
    today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = last_7_days[0]
    month_ago = local_now - timedelta(days=30)

    async with AsyncSessionLocal() as db:
        # ═══════════════════════════════════════════
        # 1. TRAFFIC METRICS
        # ═══════════════════════════════════════════

        # Tổng lượt truy cập
        total_visits = (await db.execute(
            select(func.count(AccessLog.id))
        )).scalar() or 0

        # Unique IPs
        unique_visitors = (await db.execute(
            select(func.count(distinct(AccessLog.ip)))
        )).scalar() or 0

        # Tổng số phiên (sessions) - Kết hợp DB + active socket + fallback ước lượng từ AccessLog
        db_sessions_count = (await db.execute(
            select(func.count(UserSession.id))
        )).scalar() or 0
        active_sessions_count = len(manager.active_users)
        total_sessions = db_sessions_count + active_sessions_count
        
        if total_sessions == 0 and total_visits > 0:
            all_logs = (await db.execute(
                select(AccessLog.user_id, AccessLog.ip, AccessLog.created_at)
                .order_by(AccessLog.created_at.asc())
            )).all()
            
            user_logs = {}
            for uid, ip, t in all_logs:
                key = f"u_{uid}" if uid is not None else f"ip_{ip}"
                if key not in user_logs:
                    user_logs[key] = []
                user_logs[key].append(t)
                
            est_sessions_count = 0
            for key, log_times in user_logs.items():
                est_sessions_count += 1
                current_session_end = log_times[0]
                for t in log_times[1:]:
                    if (t - current_session_end).total_seconds() > 1800:
                        est_sessions_count += 1
                    current_session_end = t
            total_sessions = max(est_sessions_count, 1)

        # Nguồn truy cập (referrer breakdown)
        referrer_rows = (await db.execute(
            select(AccessLog.referrer, func.count(AccessLog.id))
            .group_by(AccessLog.referrer)
        )).all()

        # Trích xuất frontend host từ referer header của request để nhận biết các lượt chuyển trang nội bộ
        referer_header = request.headers.get("referer") or ""
        frontend_host = ""
        if "://" in referer_header:
            frontend_host = referer_header.split("://")[1].split("/")[0]

        traffic_sources = {
            "Direct": 0,
            "Google": 0,
            "Facebook": 0,
            "Instagram": 0,
            "LinkedIn": 0,
            "TikTok": 0,
            "Twitter/X": 0,
            "Other": 0
        }
        for ref, count in referrer_rows:
            if not ref or ref.strip() == "":
                traffic_sources["Direct"] += count
            elif (frontend_host and frontend_host in ref) or "localhost" in ref or "127.0.0.1" in ref:
                # Bỏ qua liên kết nội bộ chuyển đổi giữa các trang để tránh làm nhiễu biểu đồ nguồn truy cập
                continue
            elif "google" in ref.lower():
                traffic_sources["Google"] += count
            elif "facebook" in ref.lower() or "fb" in ref.lower() or "messenger" in ref.lower():
                traffic_sources["Facebook"] += count
            elif "instagram" in ref.lower() or "insta" in ref.lower():
                traffic_sources["Instagram"] += count
            elif "linkedin" in ref.lower() or "lnkd" in ref.lower():
                traffic_sources["LinkedIn"] += count
            elif "tiktok" in ref.lower():
                traffic_sources["TikTok"] += count
            elif "twitter" in ref.lower() or "x.com" in ref.lower() or "t.co" in ref.lower():
                traffic_sources["Twitter/X"] += count
            else:
                traffic_sources["Other"] += count

        # Lượt truy cập theo ngày (7 ngày gần nhất)
        daily_visits_rows = (await db.execute(
            select(
                func.date_trunc('day', func.timezone('Asia/Ho_Chi_Minh', AccessLog.created_at)).label('day'),
                func.count(AccessLog.id)
            )
            .where(AccessLog.created_at >= week_ago)
            .group_by(text("day"))
            .order_by(text("day"))
        )).all()
        
        visits_map = {}
        for row in daily_visits_rows:
            if row[0]:
                visits_map[row[0].date().isoformat()] = row[1]
                
        daily_visits = []
        for day in last_7_days:
            day_str = day.date().isoformat()
            daily_visits.append({
                "date": day.isoformat(),
                "count": visits_map.get(day_str, 0)
            })

        # ═══════════════════════════════════════════
        # 2. USER METRICS
        # ═══════════════════════════════════════════

        # Tổng tài khoản đăng ký
        total_users = (await db.execute(
            select(func.count(User.id))
        )).scalar() or 0

        # DAU: user_id khác null hoạt động trong 24h qua (AccessLog + UserSession + active_users)
        active_users_24h = set()
        for uid in manager.active_users:
            active_users_24h.add(uid)
            
        logs_24h = (await db.execute(
            select(distinct(AccessLog.user_id))
            .where(AccessLog.user_id.isnot(None), AccessLog.created_at >= now - timedelta(hours=24))
        )).scalars().all()
        active_users_24h.update(logs_24h)
        
        sessions_24h = (await db.execute(
            select(distinct(UserSession.user_id))
            .where(UserSession.user_id.isnot(None), UserSession.login_time >= now - timedelta(hours=24))
        )).scalars().all()
        active_users_24h.update(sessions_24h)
        
        dau = max(len(active_users_24h), 1 if active_users_24h else 0)

        # MAU: user_id khác null hoạt động trong 30 ngày qua (AccessLog + UserSession + active_users)
        active_users_30d = set()
        for uid in manager.active_users:
            active_users_30d.add(uid)
            
        logs_30d = (await db.execute(
            select(distinct(AccessLog.user_id))
            .where(AccessLog.user_id.isnot(None), AccessLog.created_at >= now - timedelta(days=30))
        )).scalars().all()
        active_users_30d.update(logs_30d)
        
        sessions_30d = (await db.execute(
            select(distinct(UserSession.user_id))
            .where(UserSession.user_id.isnot(None), UserSession.login_time >= now - timedelta(days=30))
        )).scalars().all()
        active_users_30d.update(sessions_30d)
        
        mau = max(len(active_users_30d), 1 if active_users_30d else 0)

        # Online real-time
        online_count = manager.online_count

        # Đăng ký mới 7 ngày gần nhất
        new_users_rows = (await db.execute(
            select(
                func.date_trunc('day', func.timezone('Asia/Ho_Chi_Minh', User.created_at)).label('day'),
                func.count(User.id)
            )
            .where(User.created_at >= week_ago)
            .group_by(text("day"))
            .order_by(text("day"))
        )).all()
        new_users_map = {}
        for row in new_users_rows:
            if row[0]:
                new_users_map[row[0].date().isoformat()] = row[1]
                
        new_users_daily = []
        for day in last_7_days:
            day_str = day.date().isoformat()
            new_users_daily.append({
                "date": day.isoformat(),
                "count": new_users_map.get(day_str, 0)
            })

        # Tỷ lệ user mới (7 ngày gần / tổng)
        new_users_week = (await db.execute(
            select(func.count(User.id))
            .where(User.created_at >= week_ago)
        )).scalar() or 0
        new_user_rate = round((new_users_week / total_users * 100), 1) if total_users else 0

        # ═══════════════════════════════════════════
        # 3. ENGAGEMENT METRICS
        # ═══════════════════════════════════════════

        # Thời gian sử dụng trung bình (giây)
        avg_duration = (await db.execute(
            select(func.avg(UserSession.duration))
            .where(UserSession.duration.isnot(None))
        )).scalar()
        
        durations = []
        if avg_duration is not None:
            db_durations = (await db.execute(
                select(UserSession.duration).where(UserSession.duration.isnot(None))
            )).scalars().all()
            durations.extend(db_durations)
            
        for uid, info in manager.active_users.items():
            curr_dur = (datetime.now(timezone.utc) - info["start_time"]).total_seconds()
            durations.append(int(curr_dur))
            
        if not durations and total_visits > 0:
            all_logs = (await db.execute(
                select(AccessLog.user_id, AccessLog.ip, AccessLog.created_at)
                .order_by(AccessLog.created_at.asc())
            )).all()
            
            user_logs = {}
            for uid, ip, t in all_logs:
                key = f"u_{uid}" if uid is not None else f"ip_{ip}"
                if key not in user_logs:
                    user_logs[key] = []
                user_logs[key].append(t)
                
            for key, log_times in user_logs.items():
                current_session_start = log_times[0]
                current_session_end = log_times[0]
                for t in log_times[1:]:
                    if (t - current_session_end).total_seconds() > 1800:
                        durations.append(max(int((current_session_end - current_session_start).total_seconds()), 15))
                        current_session_start = t
                        current_session_end = t
                    else:
                        current_session_end = t
                durations.append(max(int((current_session_end - current_session_start).total_seconds()), 15))
                
        avg_session_duration = round(sum(durations) / len(durations), 0) if durations else 0

        # Số trang xem mỗi phiên (ước tính: total_visits / total_sessions)
        pages_per_session = round(total_visits / total_sessions, 1) if total_sessions else 0

        # Bounce Rate: Tỷ lệ phiên chỉ xem 1 trang
        bounce_rate = 0.0
        if total_visits > 0:
            all_logs = (await db.execute(
                select(AccessLog.user_id, AccessLog.ip, AccessLog.created_at)
                .order_by(AccessLog.created_at.asc())
            )).all()
            
            user_logs = {}
            for uid, ip, t in all_logs:
                key = f"u_{uid}" if uid is not None else f"ip_{ip}"
                if key not in user_logs:
                    user_logs[key] = []
                user_logs[key].append(t)
                
            sessions_count = 0
            bounce_sessions_count = 0
            for key, log_times in user_logs.items():
                session_logs = [log_times[0]]
                for t in log_times[1:]:
                    if (t - session_logs[-1]).total_seconds() > 1800:
                        sessions_count += 1
                        if len(session_logs) == 1:
                            bounce_sessions_count += 1
                        session_logs = [t]
                    else:
                        session_logs.append(t)
                sessions_count += 1
                if len(session_logs) == 1:
                    bounce_sessions_count += 1
                    
            bounce_rate = round((bounce_sessions_count / sessions_count * 100), 1) if sessions_count else 0.0

        # Retention Rate: user cũ (đăng ký > 7 ngày) hoạt động trong tuần này (AccessLog hoặc UserSession)
        old_users_query = select(User.id).where(User.created_at < week_ago)
        old_users_list = (await db.execute(old_users_query)).scalars().all()
        old_users_set = set(old_users_list)
        
        returning_users_set = set()
        for uid in manager.active_users:
            if uid in old_users_set:
                returning_users_set.add(uid)
                
        log_returning = (await db.execute(
            select(distinct(AccessLog.user_id))
            .where(AccessLog.user_id.in_(old_users_list), AccessLog.created_at >= week_ago)
        )).scalars().all()
        returning_users_set.update(log_returning)
        
        session_returning = (await db.execute(
            select(distinct(UserSession.user_id))
            .where(UserSession.user_id.in_(old_users_list), UserSession.login_time >= week_ago)
        )).scalars().all()
        returning_users_set.update(session_returning)
        
        returning_users = len(returning_users_set)
        old_users = len(old_users_set)
        retention_rate = round((returning_users / old_users * 100), 1) if old_users else 0

        # ═══════════════════════════════════════════
        # 4. FEATURE USAGE METRICS
        # ═══════════════════════════════════════════

        cv_uploads_count = (await db.execute(
            select(func.count(CVUpload.id))
        )).scalar() or 0

        cv_analyses_count = (await db.execute(
            select(func.count(CVAnalysis.id))
        )).scalar() or 0

        interview_count = (await db.execute(
            select(func.count(InterviewSession.id))
        )).scalar() or 0

        saved_jobs_count = (await db.execute(
            select(func.count(SavedJob.id))
        )).scalar() or 0

        # Feature ranking
        features = [
            {"name": "CV Analysis", "count": cv_analyses_count},
            {"name": "Mock Interview", "count": interview_count},
            {"name": "Saved Jobs", "count": saved_jobs_count},
        ]
        features_sorted = sorted(features, key=lambda x: x["count"], reverse=True)

        # ═══════════════════════════════════════════
        # 5. SUCCESS METRICS
        # ═══════════════════════════════════════════

        # Tỷ lệ hoàn thành phỏng vấn
        completed_interviews = (await db.execute(
            select(func.count(InterviewSession.id))
            .where(InterviewSession.completed_at.isnot(None))
        )).scalar() or 0
        interview_completion_rate = round(
            (completed_interviews / interview_count * 100), 1
        ) if interview_count else 0

        # Conversion Rate: users / unique visitors
        conversion_rate = round(
            (total_users / unique_visitors * 100), 1
        ) if unique_visitors else 0

        # 6. SYSTEM-WIDE RECENT ACTIVITIES (thietke_admin.md)
        recent_regs = (await db.execute(
            select(User.full_name, User.email, User.created_at)
            .order_by(User.created_at.desc())
            .limit(10)
        )).all()
        
        recent_uploads = (await db.execute(
            select(User.full_name, User.email, CVUpload.filename, CVUpload.created_at)
            .join(User, User.id == CVUpload.user_id)
            .order_by(CVUpload.created_at.desc())
            .limit(10)
        )).all()
        
        recent_analyses = (await db.execute(
            select(User.full_name, User.email, CVAnalysis.created_at)
            .join(User, User.id == CVAnalysis.user_id)
            .order_by(CVAnalysis.created_at.desc())
            .limit(10)
        )).all()
        
        recent_interviews = (await db.execute(
            select(User.full_name, User.email, InterviewSession.field, InterviewSession.started_at)
            .join(User, User.id == InterviewSession.user_id)
            .order_by(InterviewSession.started_at.desc())
            .limit(10)
        )).all()

        recent_saved_jobs = (await db.execute(
            select(User.full_name, User.email, SavedJob.created_at)
            .join(User, User.id == SavedJob.user_id)
            .order_by(SavedJob.created_at.desc())
            .limit(10)
        )).all()
        
        activities = []
        for name, email, t in recent_regs:
            if t:
                activities.append({
                    "time": t.isoformat(),
                    "desc": f"Thành viên {name or email} vừa đăng ký tài khoản",
                    "type": "register"
                })
        for name, email, filename, t in recent_uploads:
            if t:
                activities.append({
                    "time": t.isoformat(),
                    "desc": f"Thành viên {name or email} đã tải lên CV: {filename}",
                    "type": "upload"
                })
        for name, email, t in recent_analyses:
            if t:
                activities.append({
                    "time": t.isoformat(),
                    "desc": f"Thành viên {name or email} đã thực hiện phân tích CV",
                    "type": "analysis"
                })
        for name, email, field, t in recent_interviews:
            if t:
                activities.append({
                    "time": t.isoformat(),
                    "desc": f"Thành viên {name or email} đã bắt đầu luyện phỏng vấn: {field or 'General'}",
                    "type": "interview"
                })
        for name, email, t in recent_saved_jobs:
            if t:
                activities.append({
                    "time": t.isoformat(),
                    "desc": f"Thành viên {name or email} đã lưu một cơ hội việc làm",
                    "type": "save_job"
                })
                
        activities.sort(key=lambda x: x["time"], reverse=True)
        recent_system_activities = activities[:10]

    return {
        "recent_activities": recent_system_activities,
        "traffic": {
            "total_visits": total_visits,
            "unique_visitors": unique_visitors,
            "total_sessions": total_sessions,
            "sources": traffic_sources,
            "daily_visits": daily_visits,
        },
        "users": {
            "total_users": total_users,
            "dau": dau,
            "mau": mau,
            "online_count": online_count,
            "new_user_rate": new_user_rate,
            "new_users_daily": new_users_daily,
        },
        "engagement": {
            "avg_session_duration": avg_session_duration,
            "pages_per_session": pages_per_session,
            "bounce_rate": bounce_rate,
            "retention_rate": retention_rate,
        },
        "features": {
            "cv_uploads": cv_uploads_count,
            "cv_analyses": cv_analyses_count,
            "interviews": interview_count,
            "saved_jobs": saved_jobs_count,
            "ranking": features_sorted,
        },
        "success": {
            "interview_completion_rate": interview_completion_rate,
            "conversion_rate": conversion_rate,
            "completed_interviews": completed_interviews,
            "total_interviews": interview_count,
        },
    }


async def get_users_last_active(db: AsyncSession, user_ids: list[int]) -> dict[int, datetime]:
    """
    Tính toán thời điểm hoạt động cuối cùng của danh sách người dùng.
    Lấy thời gian lớn nhất trong các mốc:
    - Ngày tạo tài khoản (created_at)
    - Lần đăng nhập cuối (last_login)
    - Lần truy cập trang cuối cùng trong AccessLog
    - Lần đăng nhập/đăng xuất cuối trong UserSession
    - Thời điểm hiện tại (nếu đang online WebSocket)
    """
    if not user_ids:
        return {}

    last_active_map = {}
    
    # 1. Khởi tạo bằng created_at và last_login từ bảng users
    user_rows = (await db.execute(
        select(User.id, User.created_at, User.last_login).where(User.id.in_(user_ids))
    )).all()
    
    now_utc = datetime.now(timezone.utc)
    for uid, created_at, last_login in user_rows:
        candidates = []
        if created_at:
            candidates.append(created_at)
        if last_login:
            candidates.append(last_login)
        last_active_map[uid] = max(candidates) if candidates else now_utc

    # 2. Lấy thời gian đăng nhập/đăng xuất lớn nhất từ UserSession
    session_rows = (await db.execute(
        select(UserSession.user_id, func.max(UserSession.login_time), func.max(UserSession.logout_time))
        .where(UserSession.user_id.in_(user_ids))
        .group_by(UserSession.user_id)
    )).all()
    
    for uid, max_login, max_logout in session_rows:
        if uid in last_active_map:
            if max_login:
                last_active_map[uid] = max(last_active_map[uid], max_login)
            if max_logout:
                last_active_map[uid] = max(last_active_map[uid], max_logout)

    # 3. Lấy thời gian truy cập mới nhất từ AccessLog
    log_rows = (await db.execute(
        select(AccessLog.user_id, func.max(AccessLog.created_at))
        .where(AccessLog.user_id.in_(user_ids))
        .group_by(AccessLog.user_id)
    )).all()
    
    for uid, max_log_time in log_rows:
        if uid in last_active_map and max_log_time:
            last_active_map[uid] = max(last_active_map[uid], max_log_time)

    # 4. Nếu đang online (WebSocket hoạt động), cập nhật thành thời điểm hiện tại
    for uid in user_ids:
        if uid in manager.active_users:
            last_active_map[uid] = now_utc

    return last_active_map


# ──────────────────────────────────────────────
# HTTP: Manage Users
# ──────────────────────────────────────────────
@router.get("/users")
async def get_admin_users(
    admin: Annotated[User, Depends(require_admin)],
    skip: int = 0,
    limit: int = 50,
    search: str = "",
    role: str = "",
    is_active: bool | None = None,
    online_status: str = "all",  # "all" | "online" | "offline"
    reg_date: str = "all",      # "all" | "today" | "week" | "month"
):
    """Lấy danh sách người dùng với phân trang, lọc và tìm kiếm (chỉ dành cho Admin)."""
    async with AsyncSessionLocal() as db:
        query = select(User)

        # Filters
        if search:
            query = query.where(
                (User.email.ilike(f"%{search}%")) |
                (User.full_name.ilike(f"%{search}%"))
            )
        if role:
            query = query.where(User.role == role)
        if is_active is not None:
            query = query.where(User.is_active == is_active)

        # Filter by registration date
        vietnam_tz = timezone(timedelta(hours=7))
        local_now = datetime.now(vietnam_tz)
        if reg_date == "today":
            today_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
            query = query.where(User.created_at >= today_start)
        elif reg_date == "week":
            week_ago = local_now - timedelta(days=7)
            query = query.where(User.created_at >= week_ago)
        elif reg_date == "month":
            month_ago = local_now - timedelta(days=30)
            query = query.where(User.created_at >= month_ago)

        # Filter by online status using the in-memory WebSocket presencia manager
        online_ids = list(manager.active_users.keys())
        if online_status == "online":
            query = query.where(User.id.in_(online_ids or [-1]))
        elif online_status == "offline":
            query = query.where(~User.id.in_(online_ids or [-1]))

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await db.execute(count_query)).scalar() or 0

        # Sort and Page
        query = query.order_by(User.id.desc()).offset(skip).limit(limit)
        result = (await db.execute(query)).scalars().all()

        # Tính toán hoạt động thực tế cuối cùng
        user_ids = [u.id for u in result]
        last_active_map = await get_users_last_active(db, user_ids)

        users_list = []
        for u in result:
            la_time = last_active_map.get(u.id, u.last_login or u.created_at)
            users_list.append({
                "id": u.id,
                "email": u.email,
                "full_name": u.full_name,
                "role": u.role,
                "is_active": u.is_active,
                "created_at": u.created_at.isoformat() if u.created_at else None,
                "last_login": la_time.isoformat() if la_time else None,
                "is_online": u.id in manager.active_users,
            })

        return {
            "total": total,
            "users": users_list,
        }


@router.get("/users/{user_id}/stats")
async def get_user_stats(
    user_id: int,
    request: Request,
    admin: Annotated[User, Depends(require_admin)],
):
    """Lấy chỉ số hoạt động chi tiết của 1 user theo 5 nhóm chỉ số của quantri_admin.md (chỉ dành cho Admin)."""
    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Người dùng không tồn tại")

        # ═══════════════════════════════════════════
        # 1. TRAFFIC METRICS
        # ═══════════════════════════════════════════
        total_visits = (await db.execute(
            select(func.count(AccessLog.id)).where(AccessLog.user_id == user_id)
        )).scalar() or 0

        total_sessions = (await db.execute(
            select(func.count(UserSession.id)).where(UserSession.user_id == user_id)
        )).scalar() or 0

        referrer_rows = (await db.execute(
            select(AccessLog.referrer, func.count(AccessLog.id))
            .where(AccessLog.user_id == user_id)
            .group_by(AccessLog.referrer)
        )).all()

        # Trích xuất frontend host từ referer header của request để nhận biết các lượt chuyển trang nội bộ
        referer_header = request.headers.get("referer") or ""
        frontend_host = ""
        if "://" in referer_header:
            frontend_host = referer_header.split("://")[1].split("/")[0]

        traffic_sources = {
            "Direct": 0,
            "Google": 0,
            "Facebook": 0,
            "Instagram": 0,
            "LinkedIn": 0,
            "TikTok": 0,
            "Twitter/X": 0,
            "Other": 0
        }
        for ref, count in referrer_rows:
            if not ref or ref.strip() == "":
                traffic_sources["Direct"] += count
            elif (frontend_host and frontend_host in ref) or "localhost" in ref or "127.0.0.1" in ref:
                # Bỏ qua liên kết nội bộ
                continue
            elif "google" in ref.lower():
                traffic_sources["Google"] += count
            elif "facebook" in ref.lower() or "fb" in ref.lower() or "messenger" in ref.lower():
                traffic_sources["Facebook"] += count
            elif "instagram" in ref.lower() or "insta" in ref.lower():
                traffic_sources["Instagram"] += count
            elif "linkedin" in ref.lower() or "lnkd" in ref.lower():
                traffic_sources["LinkedIn"] += count
            elif "tiktok" in ref.lower():
                traffic_sources["TikTok"] += count
            elif "twitter" in ref.lower() or "x.com" in ref.lower() or "t.co" in ref.lower():
                traffic_sources["Twitter/X"] += count
            else:
                traffic_sources["Other"] += count

        # Recent activities (last 10 pages)
        recent_activities_rows = (await db.execute(
            select(AccessLog.path, AccessLog.created_at)
            .where(AccessLog.user_id == user_id)
            .order_by(AccessLog.created_at.desc())
            .limit(10)
        )).all()
        recent_activities = [
            {"path": row[0], "created_at": row[1].isoformat() if row[1] else ""}
            for row in recent_activities_rows
        ]

        # ═══════════════════════════════════════════
        # 2. USER METRICS
        # ═══════════════════════════════════════════
        last_active_map = await get_users_last_active(db, [user_id])
        la_time = last_active_map.get(user_id, user.last_login or user.created_at)
        
        user_info = {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "is_active": user.is_active,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "last_login": la_time.isoformat() if la_time else None,
            "is_online": user.id in manager.active_users,
        }

        # ═══════════════════════════════════════════
        # 3. ENGAGEMENT METRICS
        # ═══════════════════════════════════════════
        # Sử dụng thuật toán gộp phiên (session merging) dựa trên khoảng thời gian
        # giữa AccessLog và UserSession + active WebSocket để tính toán chính xác nhất
        is_online = user_id in manager.active_users
        
        intervals = []
        db_sessions = (await db.execute(
            select(UserSession.login_time, UserSession.duration)
            .where(UserSession.user_id == user_id)
        )).all()
        for login_time, duration in db_sessions:
            if login_time and duration is not None:
                intervals.append((login_time, login_time + timedelta(seconds=duration)))
                
        if is_online:
            online_info = manager.active_users[user_id]
            start = online_info["start_time"]
            end = datetime.now(timezone.utc)
            intervals.append((start, end))
            
        log_times = [
            row[0] for row in (await db.execute(
                select(AccessLog.created_at)
                .where(AccessLog.user_id == user_id)
                .order_by(AccessLog.created_at.asc())
            )).all()
        ]
        for t in log_times:
            intervals.append((t, t + timedelta(seconds=15)))
            
        merged_sessions = []
        if intervals:
            intervals.sort(key=lambda x: x[0])
            curr_start, curr_end = intervals[0]
            for start, end in intervals[1:]:
                if (start - curr_end).total_seconds() <= 1800:
                    curr_end = max(curr_end, end)
                else:
                    merged_sessions.append((curr_start, curr_end))
                    curr_start = start
                    curr_end = end
            merged_sessions.append((curr_start, curr_end))
            
        total_sessions = len(merged_sessions)
        session_durations = [max(int((end - start).total_seconds()), 15) for start, end in merged_sessions]
        avg_session_duration = round(sum(session_durations) / len(session_durations), 0) if session_durations else 0
        pages_per_session = round(total_visits / total_sessions, 1) if total_sessions else 0
        
        # Active days in last 30 days
        vietnam_tz = timezone(timedelta(hours=7))
        local_now = datetime.now(vietnam_tz)
        month_ago = local_now - timedelta(days=30)
        active_days = len(set(start.astimezone(vietnam_tz).date() for start, _ in merged_sessions if start >= month_ago))

        # ═══════════════════════════════════════════
        # 4. FEATURE USAGE METRICS
        # ═══════════════════════════════════════════
        cv_uploads_count = (await db.execute(
            select(func.count(CVUpload.id)).where(CVUpload.user_id == user_id)
        )).scalar() or 0

        cv_analyses_count = (await db.execute(
            select(func.count(CVAnalysis.id)).where(CVAnalysis.user_id == user_id)
        )).scalar() or 0

        interview_count = (await db.execute(
            select(func.count(InterviewSession.id)).where(InterviewSession.user_id == user_id)
        )).scalar() or 0

        saved_jobs_count = (await db.execute(
            select(func.count(SavedJob.id)).where(SavedJob.user_id == user_id)
        )).scalar() or 0

        features = [
            {"name": "CV Uploads", "count": cv_uploads_count},
            {"name": "CV Analysis", "count": cv_analyses_count},
            {"name": "Mock Interview", "count": interview_count},
            {"name": "Saved Jobs", "count": saved_jobs_count},
        ]
        features_sorted = sorted(features, key=lambda x: x["count"], reverse=True)
        most_used = features_sorted[0]["name"] if features_sorted[0]["count"] > 0 else "N/A"
        least_used = features_sorted[-1]["name"] if features_sorted[-1]["count"] > 0 else "N/A"

        # ═══════════════════════════════════════════
        # 5. SUCCESS METRICS
        # ═══════════════════════════════════════════
        completed_interviews = (await db.execute(
            select(func.count(InterviewSession.id))
            .where(InterviewSession.user_id == user_id, InterviewSession.completed_at.isnot(None))
        )).scalar() or 0
        interview_completion_rate = round(
            (completed_interviews / interview_count * 100), 1
        ) if interview_count else 0

        avg_ats = (await db.execute(
            select(func.avg(CVAnalysis.ats_score))
            .where(CVAnalysis.user_id == user_id, CVAnalysis.ats_score.isnot(None))
        )).scalar()
        avg_ats_score = round(float(avg_ats), 1) if avg_ats else 0

        avg_interview = (await db.execute(
            select(func.avg(InterviewSession.overall_score))
            .where(InterviewSession.user_id == user_id, InterviewSession.overall_score.isnot(None))
        )).scalar()
        avg_interview_score = round(float(avg_interview), 1) if avg_interview else 0

        # Recent 5 CVs analysed
        recent_cvs_rows = (await db.execute(
            select(CVUpload.filename, CVUpload.created_at, CVAnalysis.ats_score, CVAnalysis.id)
            .join(CVAnalysis, CVAnalysis.cv_id == CVUpload.id, isouter=True)
            .where(CVUpload.user_id == user_id)
            .order_by(CVUpload.created_at.desc())
            .limit(5)
        )).all()
        recent_cvs = [
            {
                "filename": row[0],
                "created_at": row[1].isoformat() if row[1] else None,
                "ats_score": row[2],
                "analysis_id": row[3],
            }
            for row in recent_cvs_rows
        ]

        # Recent 5 interview sessions
        recent_interviews_rows = (await db.execute(
            select(
                InterviewSession.id,
                InterviewSession.field,
                InterviewSession.level,
                InterviewSession.overall_score,
                InterviewSession.completed_at,
            )
            .where(InterviewSession.user_id == user_id)
            .order_by(InterviewSession.started_at.desc())
            .limit(5)
        )).all()
        recent_interviews = [
            {
                "id": row[0],
                "field": row[1],
                "level": row[2],
                "overall_score": row[3],
                "completed_at": row[4].isoformat() if row[4] else None,
            }
            for row in recent_interviews_rows
        ]

        return {
            "user": user_info,
            "traffic": {
                "total_visits": total_visits,
                "total_sessions": total_sessions,
                "sources": traffic_sources,
                "recent_activities": recent_activities,
            },
            "engagement": {
                "avg_session_duration": avg_session_duration,
                "pages_per_session": pages_per_session,
                "active_days_30d": active_days,
            },
            "features": {
                "cv_uploads": cv_uploads_count,
                "cv_analyses": cv_analyses_count,
                "interviews": interview_count,
                "saved_jobs": saved_jobs_count,
                "ranking": features_sorted,
                "most_used": most_used,
                "least_used": least_used,
            },
            "success": {
                "interview_completion_rate": interview_completion_rate,
                "avg_ats_score": avg_ats_score,
                "avg_interview_score": avg_interview_score,
                "completed_interviews": completed_interviews,
                "total_interviews": interview_count,
            },
            "recent_cvs": recent_cvs,
            "recent_interviews": recent_interviews,
        }


@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    admin: Annotated[User, Depends(require_admin)],
):
    """Khóa hoặc mở khóa tài khoản người dùng (chỉ dành cho Admin). Không thể tự khóa chính mình."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Không thể tự khóa tài khoản của chính mình")
    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
        user.is_active = not user.is_active
        db.add(user)
        await db.commit()
        logger.info(f"🛡️ Admin {admin.id} toggled active status of User {user_id} to {user.is_active}")
        return {"status": "updated", "is_active": user.is_active}


class UpdateRolePayload(BaseModel):
    role: str


@router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    payload: UpdateRolePayload,
    admin: Annotated[User, Depends(require_admin)],
):
    """Thay đổi vai trò (role) của người dùng (chỉ dành cho Admin). Không thể tự đổi quyền của chính mình."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Không thể tự thay đổi quyền của chính mình")
    if payload.role not in ["admin", "premium", "user"]:
        raise HTTPException(status_code=400, detail="Vai trò không hợp lệ. Chỉ chấp nhận: admin, premium, user")
        
    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="Người dùng không tồn tại")
        user.role = payload.role
        db.add(user)
        await db.commit()
        logger.info(f"🛡️ Admin {admin.id} changed role of User {user_id} to {payload.role}")
        return {"status": "updated", "role": user.role}
