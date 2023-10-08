import sqlite3


class Database():
    def __init__(self, db_path: str) -> None:
        if sqlite3.threadsafety != 3:
            raise Exception('SQLite must be thread safe')

        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

        with self._conn:
            self._conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS pipeline_executions (
                    trace_id TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    start_at DATETIME DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
                    PRIMARY KEY (trace_id)
                )
                ''')

            self._conn.execute('''
                CREATE TABLE IF NOT EXISTS pipeline_step_updates (
                    trace_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    error TEXT NULL,
                    start_at DATETIME NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
                    end_at DATETIME NULL
                )
            ''')

    def insert_pipeline_start(self, trace_id: str, domain: str) -> None:
        with self._conn:
            self._conn.execute(
                '''
                INSERT INTO pipeline_executions
                (trace_id, domain)
                VALUES (?, ?)
                ''',
                (trace_id, domain))
            self._conn.commit()

    def insert_pipeline_step_start(self, trace_id: str, topic: str) -> None:
        with self._conn:
            self._conn.execute(
                '''
                INSERT INTO pipeline_step_updates
                (trace_id, topic)
                VALUES (?, ?)
                ''',
                (trace_id, topic))

            self._conn.commit()

    def insert_pipeline_step_end(self, trace_id: str, topic: str, error: str | None) -> None:
        with self._conn:
            self._conn.execute(
                '''
                UPDATE pipeline_step_updates
                SET error = ?, end_at = strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
                WHERE trace_id = ? and topic = ?
                ''',
                (error, trace_id, topic))

            self._conn.commit()

    def fetch_pipeline_executions(self, count: int, last_trace_id: str | None) -> None:
        with self._conn:
            result_set = self._conn.execute(
                '''
                WITH last_start_at (value) AS (
                    SELECT
                    (
                        SELECT start_at
                        FROM pipeline_step_updates
                        WHERE trace_id = :last_trace_id
                        UNION ALL
                        SELECT NULL
                    )
                    LIMIT 1
                )
                SELECT
                    e.trace_id,
                    e.domain,
                    e.start_at execution_start_at,
                    u.topic,
                    u.error,
                    u.start_at,
                    u.end_at
                FROM
                    pipeline_step_updates u
                RIGHT JOIN (
                    SELECT *
                    FROM pipeline_executions
                    WHERE start_at < (SELECT COALESCE(value, '9999-12-31')
                                    FROM last_start_at)
                    ORDER BY start_at DESC
                    LIMIT :count
                ) e ON u.trace_id = e.trace_id
                ORDER BY
                    execution_start_at DESC,
                    e.trace_id ASC
                ''', {
                    'last_trace_id': last_trace_id,
                    'count': count
                })

            rows = list(result_set)

        executions = []

        current_trace_id = None

        for row in rows:
            if row['trace_id'] != current_trace_id:
                current_trace_id = row['trace_id']
                executions.append({
                    'trace_id': row['trace_id'],
                    'domain': row['domain'],
                    'start_at': row['execution_start_at'],
                    'updates': [],
                })
            if row['topic']:
                executions[-1]['updates'].append({
                    'topic': row['topic'],
                    'error': row['error'],
                    'start_at': row['start_at'],
                    'end_at': row['end_at'],
                })

        return executions

    def close(self):
        self._conn.close()
