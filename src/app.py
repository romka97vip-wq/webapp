import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, request, jsonify

app = Flask(__name__)


def get_db_connection():
    return psycopg2.connect(
        host=os.environ['DB_HOST'],
        port=os.environ['DB_PORT'],
        user=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        database=os.environ['DB_NAME'],
    )


@app.route('/api/visit', methods=['POST'])
def record_visit():
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'unknown')
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO visits (ip, user_agent) VALUES (%s, %s) RETURNING id;',
            (ip, user_agent),
        )
        visit_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'status': 'ok', 'visit_id': visit_id}), 201
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT COUNT(*) AS total FROM visits;')
        total = cur.fetchone()['total']

        cur.execute('''
            SELECT DATE(visited_at) AS day, COUNT(*) AS count
            FROM visits
            GROUP BY DATE(visited_at)
            ORDER BY day DESC
            LIMIT 7;
        ''')
        by_day = cur.fetchall()

        cur.execute('''
            SELECT ip, COUNT(*) AS count
            FROM visits
            GROUP BY ip
            ORDER BY count DESC
            LIMIT 10;
        ''')
        by_ip = cur.fetchall()

        cur.close()
        conn.close()

        return jsonify({
            'total_visits': total,
            'by_day': [dict(r) for r in by_day],
            'top_ips': [dict(r) for r in by_ip],
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/stats', methods=['GET'])
def stats_page():
    pod_name = os.environ.get('HOSTNAME', 'unknown')
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM visits;')
        total = cur.fetchone()[0]

        cur.execute('''
            SELECT DATE(visited_at) AS day, COUNT(*) AS count
            FROM visits
            GROUP BY DATE(visited_at)
            ORDER BY day DESC
            LIMIT 7;
        ''')
        by_day = cur.fetchall()
        cur.close()
        conn.close()

        html = f'<h1>CV Site Visit Stats</h1>'
        html += f'<p>Served by pod: <b>{pod_name}</b></p>'
        html += f'<p><b>Total visits:</b> {total}</p>'
        html += '<h2>Last 7 days</h2>'
        html += '<table border="1" cellpadding="8"><tr><th>Day</th><th>Visits</th></tr>'
        for day, count in by_day:
            html += f'<tr><td>{day}</td><td>{count}</td></tr>'
        html += '</table>'
        return html
    except Exception as e:
        return f'<h1>Error</h1><pre>{e}</pre>', 500


@app.route('/health', methods=['GET'])
def health():
    return {'status': 'ok'}, 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
