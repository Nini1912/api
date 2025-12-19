from fastapi import FastAPI, HTTPException, Query
from db import get_connection

app = FastAPI(
    title="Georgian Dictionary API",
    version="1.0.0"
)


@app.get("/api/v1/word/{word}")
def get_word(word: str):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT w.id, w.word, wt.name
            FROM words w
            JOIN word_types wt ON w.word_type_id = wt.id
            WHERE w.word ILIKE %s
        """, (word,))

        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Word not found")

        word_id, word_text, word_type = row

        cur.execute("""
            SELECT definition, example
            FROM definitions
            WHERE word_id = %s
            ORDER BY id
        """, (word_id,))

        definitions = [
            {"definition": d, "example": e}
            for d, e in cur.fetchall()
        ]

        return {
            "word": word_text,
            "word_type": word_type,
            "definitions": definitions
        }

    finally:
        cur.close()
        conn.close()


@app.get("/api/v1/search")
def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(20, ge=1, le=100)
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT w.word, wt.name
            FROM words w
            JOIN word_types wt ON w.word_type_id = wt.id
            WHERE w.search_vector @@ plainto_tsquery('simple', %s)
            ORDER BY ts_rank(w.search_vector, plainto_tsquery('simple', %s)) DESC
            LIMIT %s
        """, (q, q, limit))

        results = [
            {"word": w, "word_type": t}
            for w, t in cur.fetchall()
        ]

        return {
            "query": q,
            "count": len(results),
            "results": results
        }

    finally:
        cur.close()
        conn.close()


@app.get("/api/v1/word-type/{type_name}")
def get_words_by_type(
    type_name: str,
    limit: int = Query(50, ge=1, le=200)
):
    conn = get_connection()
    cur = conn.cursor()

    try:
        cur.execute("""
            SELECT w.word
            FROM words w
            JOIN word_types wt ON w.word_type_id = wt.id
            WHERE wt.name = %s
            ORDER BY w.word
            LIMIT %s
        """, (type_name, limit))

        words = [row[0] for row in cur.fetchall()]

        return {
            "word_type": type_name,
            "count": len(words),
            "words": words
        }

    finally:
        cur.close()
        conn.close()
