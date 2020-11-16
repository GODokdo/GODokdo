import pymysql

class OpenMysql:
    def __enter__(self):
        self.db = pymysql.connect(
            user='god', 
            passwd='fafm2903f20@#T234', 
            host='192.168.1.231', 
            db='god', 
            charset='utf8'
        )
        self.cursor = self.db.cursor(pymysql.cursors.DictCursor)
        return self
    def execute(self, sql, data=None):
        if data is not None:
            self.affected_row = self.cursor.execute(sql, data)
        else:
            self.affected_row = self.cursor.execute(sql)
        return self.cursor.fetchall()
    def commit(self):
        self.db.commit()
    def __exit__(self, exc_type, exc_value, traceback):
        self.db.close()