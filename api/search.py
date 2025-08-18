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
            
            # Get keyword
            keyword = data.get('keyword', '').strip()
            
            if not keyword:
                response = {
                    'success': False,
                    'error': 'キーワードを入力してください'
                }
            else:
                # Search in real database from Dropbox
                try:
                    # Dropbox direct download URL
                    dropbox_url = 'https://www.dropbox.com/scl/fi/jrns72qaqx1xu79yq3ndj/youtube_search_complete_all.db?rlkey=9jg1jmc4obzbtyc3ofn8yf2od&st=ijyc2fsc&dl=1'
                    
                    # Download database to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
                        urllib.request.urlretrieve(dropbox_url, temp_db.name)
                        db_path = temp_db.name
                    
                    # Connect and search
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    
                    # Search query with LIKE for partial matches
                    query = """
                    SELECT management_id, title, broadcast_date, character_name, dialogue, voice_instruction, filming_instruction, editing_instruction, row_number
                    FROM script_lines 
                    WHERE dialogue LIKE ? OR character_name LIKE ? OR title LIKE ?
                    ORDER BY row_number LIMIT 50
                    """
                    
                    search_pattern = f'%{keyword}%'
                    cursor.execute(query, (search_pattern, search_pattern, search_pattern))
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
                            'row_number': row[8] or 0
                        })
                    
                    response = {
                        'success': True,
                        'keyword': keyword,
                        'results': formatted_results,
                        'count': len(formatted_results),
                        'database_info': f'検索対象: 完全なデータベース（258,137行の実際の台本データ）'
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