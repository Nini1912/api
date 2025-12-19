from fastapi import FastAPI, HTTPException
from db import get_connection

app = FastAPI(
    title="Georgian Dictionary API",
    version="1.0"
)

@app.get("api/v1/word/{word}")
def get_word(word: str):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT w.id, w.word, wt.name
        FROM words w
        JOIN word_types wt ON w.word_type_id = wt.id
        WHERE w.word = %s
    """, (word,))

    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Word not found")

    word_id, word_text, word_type = row

    cur.execute("""
        SELECT definition, example
        FROM definitions
        WHERE word_id = %s
    """, (word_id,))

    definitions = [
        {"definition": d, "example": e}
        for d, e in cur.fetchall()
    ]

    cur.close()
    conn.close()

    return {
        "word": word_text,
        "word_type": word_type,
        "definitions": definitions
    }


@app.get("/api/v1/search")
def search(q: str, limit: int = 20):
    conn = get_connection()
    cur = conn.cursor()

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

    cur.close()
    conn.close()

    return {"query": q, "results": results}

@app.get("api/v1/word-type/{type_name}")
def get_words_by_type(type_name: str, limit: int = 50):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT w.word
        FROM words w
        JOIN word_types wt ON w.word_type_id = wt.id
        WHERE wt.name = %s
        ORDER BY w.word
        LIMIT %s
    """, (type_name, limit))

    words = [row[0] for row in cur.fetchall()]

    cur.close()
    conn.close()

    return words
