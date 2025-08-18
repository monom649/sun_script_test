#!/usr/bin/env python3
"""
Vercel Function: Search API - Simplified
"""

import json
from datetime import datetime

def handler(request):
    """Vercel Function handler for search"""
    
    try:
        # CORS headers
        headers = {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
        
        # OPTIONS request (CORS preflight)
        if request.method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': headers,
                'body': ''
            }
        
        # Only allow POST
        if request.method != 'POST':
            return {
                'statusCode': 405,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'Method not allowed',
                    'error_code': 'METHOD_NOT_ALLOWED'
                })
            }
        
        # Get request data
        try:
            if hasattr(request, 'get_json'):
                data = request.get_json()
            elif hasattr(request, 'json'):
                data = request.json
            else:
                # Try to get body and parse JSON
                body = getattr(request, 'body', '{}')
                data = json.loads(body) if isinstance(body, str) else {}
        except:
            data = {}
        
        # Get keyword
        keyword = data.get('keyword', '').strip()
        if not keyword:
            return {
                'statusCode': 400,
                'headers': headers,
                'body': json.dumps({
                    'success': False,
                    'error': 'キーワードを入力してください',
                    'error_code': 'MISSING_KEYWORD'
                })
            }
        
        # Return demo data (since database is not available on Vercel)
        demo_results = [
            {
                'management_id': 'DEMO001',
                'title': f'「{keyword}」を含むデモ動画',
                'broadcast_date': '25/08/18',
                'character_name': 'サンサン',
                'dialogue': f'こんにちは！今日は{keyword}について話すよ！',
                'voice_instruction': '元気よく',
                'filming_instruction': '笑顔で',
                'editing_instruction': 'テロップ追加',
                'row_number': 1
            },
            {
                'management_id': 'DEMO002', 
                'title': f'「{keyword}」デモ動画2',
                'broadcast_date': '25/08/17',
                'character_name': 'くもりん',
                'dialogue': f'{keyword}って面白いよね！みんなも一緒に覚えよう！',
                'voice_instruction': '優しく',
                'filming_instruction': '手を振って',
                'editing_instruction': '音楽追加',
                'row_number': 15
            }
        ]
        
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({
                'success': True,
                'keyword': keyword,
                'results': demo_results,
                'count': len(demo_results),
                'debug_info': {
                    'mode': 'demo',
                    'message': 'デモデータを表示中（データベース未接続）',
                    'timestamp': datetime.now().isoformat()
                }
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        # Error handling
        print(f"Search API Error: {str(e)}")
        
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            },
            'body': json.dumps({
                'success': False,
                'error': f'サーバーエラー: {str(e)}',
                'error_code': 'INTERNAL_SERVER_ERROR'
            })
        }