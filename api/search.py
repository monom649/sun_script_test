from http.server import BaseHTTPRequestHandler
import json
import sqlite3
import os
import urllib.request
import tempfile

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        try:
            # Set headers
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                try:
                    data = json.loads(post_data.decode('utf-8'))
                except:
                    data = {}
            else:
                data = {}
            
            # Get search parameters
            keyword = data.get('keyword', '').strip()
            character_filter = data.get('character_filter', '').strip()
            sort_order = data.get('sort_order', 'management_id_asc')
            limit = data.get('limit', 50)
            
            if not keyword:
                response = {
                    'success': False,
                    'error': 'キーワードを入力してください'
                }
            else:
                # Search in real database from Dropbox
                try:
                    # Dropbox direct download URL for reorganized database
                    dropbox_url = 'https://www.dropbox.com/scl/fi/ofuqpug3tstgpdqu0dvcr/youtube_search_complete_all.db?rlkey=y4al959fd7tdozin51mc9yblz&st=juxz0zgt&dl=1'
                    
                    # Download database to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
                        urllib.request.urlretrieve(dropbox_url, temp_db.name)
                        db_path = temp_db.name
                    
                    # Connect and search
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Build dynamic query for reorganized database
                    # Search across all content types and join with scripts table
                    base_query = """
                    SELECT s.management_id, s.title, s.broadcast_date, 
                           COALESCE(cd.character_name, '') as character_name,
                           COALESCE(cd.dialogue_text, sd.description_text, ve.effect_description, ai.audio_description, tn.note_text, '') as dialogue,
                           COALESCE(cd.voice_instruction, '') as voice_instruction,
                           COALESCE(sd.filming_instruction, '') as filming_instruction,
                           '' as editing_instruction,
                           s.script_url,
                           COALESCE(cd.row_number, sd.row_number, ve.row_number, ai.row_number, tn.row_number, 0) as row_number,
                           CASE 
                               WHEN cd.id IS NOT NULL THEN 'dialogue'
                               WHEN sd.id IS NOT NULL THEN 'scene_description'
                               WHEN ve.id IS NOT NULL THEN 'visual_effect'
                               WHEN ai.id IS NOT NULL THEN 'audio_instruction'
                               WHEN tn.id IS NOT NULL THEN 'technical_note'
                               ELSE 'title'
                           END as content_type
                    FROM scripts s
                    LEFT JOIN character_dialogue cd ON s.id = cd.script_id
                    LEFT JOIN scene_descriptions sd ON s.id = sd.script_id
                    LEFT JOIN visual_effects ve ON s.id = ve.script_id
                    LEFT JOIN audio_instructions ai ON s.id = ai.script_id
                    LEFT JOIN technical_notes tn ON s.id = tn.script_id
                    WHERE (s.title LIKE ? OR 
                           cd.dialogue_text LIKE ? OR cd.character_name LIKE ? OR
                           sd.description_text LIKE ? OR
                           ve.effect_description LIKE ? OR
                           ai.audio_description LIKE ? OR
                           tn.note_text LIKE ?)
                    """
                    
                    query_params = [f'%{keyword}%'] * 7  # 7 parameters for the 7 LIKE conditions
                    
                    # Add character filter
                    if character_filter:
                        base_query += " AND cd.character_name LIKE ?"
                        query_params.append(f'%{character_filter}%')
                    
                    # Add sorting
                    sort_map = {
                        'management_id_asc': 'ORDER BY s.management_id ASC, row_number ASC',
                        'management_id_desc': 'ORDER BY s.management_id DESC, row_number ASC',
                        'broadcast_date_asc': 'ORDER BY s.broadcast_date ASC, s.management_id ASC, row_number ASC',
                        'broadcast_date_desc': 'ORDER BY s.broadcast_date DESC, s.management_id ASC, row_number ASC'
                    }
                    
                    order_clause = sort_map.get(sort_order, 'ORDER BY s.management_id ASC, row_number ASC')
                    base_query += f" {order_clause} LIMIT ?"
                    query_params.append(limit)
                    
                    cursor.execute(base_query, query_params)
                    results = cursor.fetchall()
                    conn.close()
                    
                    # Clean up temporary file
                    os.unlink(db_path)
                    
                    # Format results
                    formatted_results = []
                    for row in results:
                        formatted_results.append({
                            'management_id': row[0] or '',
                            'title': row[1] or '',
                            'broadcast_date': row[2] or '',
                            'character_name': row[3] or '',
                            'dialogue': row[4] or '',
                            'voice_instruction': row[5] or '',
                            'filming_instruction': row[6] or '',
                            'editing_instruction': row[7] or '',
                            'script_url': row[8] or '',
                            'row_number': row[9] or 0,
                            'content_type': row[10] or 'unknown'
                        })
                    
                    response = {
                        'success': True,
                        'keyword': keyword,
                        'character_filter': character_filter,
                        'sort_order': sort_order,
                        'limit': limit,
                        'results': formatted_results,
                        'count': len(formatted_results),
                        'database_info': f'検索対象: 整理済みデータベース（セリフ・指示文・効果音を分離済み）'
                    }
                    
                except Exception as db_error:
                    response = {
                        'success': False,
                        'error': f'データベースエラー: {str(db_error)}'
                    }
            
            # Send response
            response_json = json.dumps(response, ensure_ascii=False)
            self.wfile.write(response_json.encode('utf-8'))
            
        except Exception as e:
            # Error response
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            error_response = {
                'success': False,
                'error': f'サーバーエラー: {str(e)}'
            }
            self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))