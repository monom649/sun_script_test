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
                    
                    # Check if database has new schema by checking for tables
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='character_dialogue'")
                    has_new_schema = cursor.fetchone() is not None
                    
                    if has_new_schema:
                        # Use new reorganized database schema - simplified query
                        base_query = """
                        SELECT s.management_id, s.title, s.broadcast_date, 
                               cd.character_name, cd.dialogue_text as dialogue,
                               cd.voice_instruction, '' as filming_instruction, '' as editing_instruction,
                               s.script_url, cd.row_number, 'dialogue' as content_type
                        FROM character_dialogue cd
                        JOIN scripts s ON cd.script_id = s.id
                        WHERE cd.dialogue_text LIKE ? OR cd.character_name LIKE ? OR s.title LIKE ?
                        """
                        query_params = [f'%{keyword}%', f'%{keyword}%', f'%{keyword}%']
                    else:
                        # Fallback to original schema
                        base_query = """
                        SELECT management_id, title, broadcast_date, character_name, dialogue, 
                               voice_instruction, filming_instruction, editing_instruction, script_url, row_number, 'original' as content_type
                        FROM script_lines 
                        WHERE (dialogue LIKE ? OR character_name LIKE ? OR title LIKE ?)
                        """
                        query_params = [f'%{keyword}%', f'%{keyword}%', f'%{keyword}%']
                    
                    # Add character filter
                    if character_filter:
                        if has_new_schema:
                            base_query += " AND cd.character_name LIKE ?"
                        else:
                            base_query += " AND character_name LIKE ?"
                        query_params.append(f'%{character_filter}%')
                    
                    # Add sorting
                    if has_new_schema:
                        sort_map = {
                            'management_id_asc': 'ORDER BY s.management_id ASC, cd.row_number ASC',
                            'management_id_desc': 'ORDER BY s.management_id DESC, cd.row_number ASC',
                            'broadcast_date_asc': 'ORDER BY s.broadcast_date ASC, s.management_id ASC, cd.row_number ASC',
                            'broadcast_date_desc': 'ORDER BY s.broadcast_date DESC, s.management_id ASC, cd.row_number ASC'
                        }
                    else:
                        sort_map = {
                            'management_id_asc': 'ORDER BY management_id ASC, row_number ASC',
                            'management_id_desc': 'ORDER BY management_id DESC, row_number ASC',
                            'broadcast_date_asc': 'ORDER BY broadcast_date ASC, management_id ASC, row_number ASC',
                            'broadcast_date_desc': 'ORDER BY broadcast_date DESC, management_id ASC, row_number ASC'
                        }
                    
                    order_clause = sort_map.get(sort_order, list(sort_map.values())[0])
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