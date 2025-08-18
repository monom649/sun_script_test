from http.server import BaseHTTPRequestHandler
import json
import urllib.parse

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
                # Demo data
                demo_results = [
                    {
                        'management_id': 'DEMO001',
                        'title': f'「{keyword}」を含むデモ動画1',
                        'broadcast_date': '25/08/18',
                        'character_name': 'サンサン',
                        'dialogue': f'こんにちは！今日は{keyword}について話すよ！みんなで一緒に楽しもう！'
                    },
                    {
                        'management_id': 'DEMO002', 
                        'title': f'「{keyword}」を含むデモ動画2',
                        'broadcast_date': '25/08/17',
                        'character_name': 'くもりん',
                        'dialogue': f'{keyword}って本当に面白いよね！みんなも一緒に覚えよう！'
                    }
                ]
                
                response = {
                    'success': True,
                    'keyword': keyword,
                    'results': demo_results,
                    'count': len(demo_results)
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