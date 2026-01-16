from aiohttp import web # For web server response handling
import json # For JSON handling
from datetime import datetime # For handling date and time

# Internal modules
import modules.engine_common as engc # For common engine functions and definitions
import modules.engine_web as engw # For basic engine functions and defenitions

# -------------------------------------------------------
# Generate HTML page with user's library
async def library_html(request):
    encrypted = request.match_info.get('user', '')

    # Decrypt user ID
    try:
        user_id = engw.decrypt_from_url(encrypted)
        user_id = int(user_id)
    except Exception:
        return web.Response(text="Invalid link", content_type='text/html')
    
    # Fetch books from database
    async with engc.pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT *
            FROM books
            WHERE user_id = $1
            ORDER BY category ASC, book_id ASC
        """, user_id)

    if len(rows) == 0:
        # Answer if no books found
        return web.Response(text="No books found", content_type='text/html')

    else:
        # Prepare JSON data
        json_list = []
        for row in rows:
            json_list.append({
                "book_id": row["book_id"],
                "category": row["category"],
                "title": row["title"],
                "authors": row["authors"],
                "authors_full_names": row["authors_full_names"],
                "pages": row["pages"],
                "publisher": row["publisher"],
                "year": row["year"],
                "isbn": row["isbn"],
                "favorites": row["favorites"],
                "likes": row["likes"],
                "cover_filename": engw.AWS_EXTERNAL_URL + "/" + str(row["cover_filename"]),
                "photo_filename": engw.AWS_EXTERNAL_URL + "/" + str(row["photo_filename"]),
                "brief_filename": engw.AWS_EXTERNAL_URL + "/" + str(row["brief_filename"]),
                "brief2_filename": engw.AWS_EXTERNAL_URL + "/" + str(row["brief2_filename"]),
                "brief": row["brief"],
                "annotation": row["annotation"],
                "datetime": row["datetime"].isoformat()
            })
        json_data = json.dumps(json_list, ensure_ascii=False, indent=4)

        # Prepare HTML content
        with open('web/template.html', 'r', encoding='utf-8') as f:
            html_content = f.read()
        html_content = html_content.replace('[]//*BOOKS*', json_data)

        # Return HTML response
        return web.Response(text=html_content, content_type='text/html')
