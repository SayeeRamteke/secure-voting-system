from fastapi import APIRouter
import db

router = APIRouter()


@router.get("/election/root")
def election_root():
    root = db.get_latest_root_record()
    if not root:
        return {
            "merkle_root": None,
            "total_votes": 0,
            "published_at": None,
            "sequence": None,
            "status": "not_published",
        }

    return {
        "merkle_root": root["root_hash"],
        "total_votes": root["vote_count"],
        "published_at": root["created_at"],
        "sequence": root["seq"],
        "status": "published",
    }
