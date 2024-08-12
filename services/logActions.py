from model.log import Log
from sqlalchemy.orm import sessionmaker
from connectors.mysql_connectors import connection

class LogManager:
    def __init__(self, user_id, action):
        self.user_id = user_id
        self.action = action
        self.before_data = None
        self.after_data= None

    def set_before(self, before_data):
        self.before_data = before_data

    def set_after(self, after_data):
        self.after_data = after_data

    def save(self):
        log = Log(
            user_id=self.user_id,
            action=self.action,
            before=self.before_data,
            after=self.after_data
        )

        Session = sessionmaker(connection)
        db = Session()
        db.begin()
        try:
            db.add(log)
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"ERROR: {str(e)}")
        finally:
            db.close()

