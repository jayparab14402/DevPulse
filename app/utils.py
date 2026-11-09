
from sqlalchemy import select
from .models import ErrorEvent
from .database import get_db
from datetime import datetime as dt


def fetch_data(get_db):

    with get_db as session:
        query = select(ErrorEvent)

        main_query = session.scalars(query).all()
        print(f"Total records: {len(main_query)}")
        for event in main_query:
            print(
                event.id,
                event.service,
                event.level,
                event.message
            )
        return main_query
        

def add_record(db, data):
    try:
        # with db as write_session:
        obj = ErrorEvent(
            service = data.service,
            level = data.level,
            message = data.message,
            status_code = data.status_code
        )
        db.add(obj)
        db.commit()
        db.refresh(obj)
        print("DATA ADDED IN DB", obj)
        print("DATA ADDED IN DB with 1", obj.id)
    # print("DATA ADDED IN DB with 2", type(obj))
        
        return obj
    except Exception as e:
        db.rollback()
        print(f"------------------ {e} ------------------")
            


# if __name__=="__main__":
#     # add_record(get_db)
#     fetch_data(get_db)



















# from sqlalchemy import select
# from .models import ErrorEvent
# from .database import get_db


# def fetch_data():
#     try:
#         with get_db() as session:
#             statement = select(ErrorEvent)
#             events = session.scalars(statement).all()

#             print(f"Total records: {len(events)}")

#             for event in events:
#                 print(
#                     event.id,
#                     event.service,
#                     event.level,
#                     event.message
#                 )

#     except Exception as e:
#         print("ERROR:", e)


# if __name__ == "__main__":
#     fetch_data()