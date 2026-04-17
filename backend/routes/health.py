from fastapi import APIRouter
import db, detection

router = APIRouter()

@router.get("/health")
def health_check():
    try:
        detection.verify_chain()
        return {
            "status":     "OK",
            "root":       db.get_latest_root(),
            "vote_count": db.vote_count()
        }
    except detection.TamperDetected as e:
        return {
            "status":  "TAMPER DETECTED",
            "detail":  str(e),
            "root":    db.get_latest_root(),
            "vote_count": db.vote_count()
        }