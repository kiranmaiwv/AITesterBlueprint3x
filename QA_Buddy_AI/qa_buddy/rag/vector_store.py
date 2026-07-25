"""Qdrant Cloud client wrapper — uses v1.18+ query_points API."""

from qdrant_client import QdrantClient as _QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance, Filter, FieldCondition, MatchValue
from qa_buddy.config import config


def get_client():
    return _QdrantClient(
        url=config.QDRANT_URL,
        api_key=config.QDRANT_API_KEY,
    )


def ensure_collection():
    client = get_client()
    collections = [c.name for c in client.get_collections().collections]
    if config.QDRANT_COLLECTION not in collections:
        client.create_collection(
            collection_name=config.QDRANT_COLLECTION,
            vectors_config=VectorParams(size=config.EMBEDDING_DIM, distance=Distance.COSINE),
        )
    return client


def upsert_points(points: list[PointStruct]):
    client = ensure_collection()
    client.upsert(collection_name=config.QDRANT_COLLECTION, points=points, wait=True)


def search(query_vector: list[float], top_k: int = 5, source_filter: str = None):
    """Search Qdrant using query_points (v1.18+ API)."""
    client = get_client()
    q_filter = None
    if source_filter:
        q_filter = Filter(must=[FieldCondition(key="source", match=MatchValue(value=source_filter))])

    result = client.query_points(
        collection_name=config.QDRANT_COLLECTION,
        query=query_vector,
        limit=top_k,
        query_filter=q_filter,
        with_payload=True,
    )

    return [
        {
            "content": hit.payload.get("content", ""),
            "score": hit.score,
            "metadata": {
                "file_path": hit.payload.get("file_path", ""),
                "folder_id": hit.payload.get("folder_id", ""),
                "source": hit.payload.get("source", ""),
                "language": hit.payload.get("language", ""),
            },
        }
        for hit in result.points
    ]
