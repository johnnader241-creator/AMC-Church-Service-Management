from datetime import date, timedelta
from sqlalchemy import select, or_, and_, func
from ..models import ServiceAssignment, ServiceYear, Service, Meeting, ServiceTransfer, Event, Participant

def overlapping_assignment(db, servant_id, service_id, start_date, end_date, exclude_id=None):
    q=select(ServiceAssignment).where(ServiceAssignment.servant_id==servant_id,ServiceAssignment.service_id==service_id,ServiceAssignment.start_date<=end_date,ServiceAssignment.end_date>=start_date)
    if exclude_id: q=q.where(ServiceAssignment.assignment_id!=exclude_id)
    return db.scalar(q)

def servant_day_conflict(db, servant_id, service_day, start_date, end_date, exclude_id=None):
    q=(select(ServiceAssignment,Service.day_of_week).join(Service,Service.service_id==ServiceAssignment.service_id)
       .where(ServiceAssignment.servant_id==servant_id,Service.day_of_week==service_day,ServiceAssignment.start_date<=end_date,ServiceAssignment.end_date>=start_date))
    if exclude_id: q=q.where(ServiceAssignment.assignment_id!=exclude_id)
    return db.first(q)

def get_open_year(db):
    return db.scalar(select(ServiceYear).where(ServiceYear.status=='OPEN',ServiceYear.is_archived==False).order_by(ServiceYear.start_date.desc()))

def in_service_year(year,start_date,end_date): return year and year.start_date<=start_date<=year.end_date and year.start_date<=end_date<=year.end_date

def fridays(start_date,end_date,weekday):
    target=3 if weekday=='THURSDAY' else 4
    d=start_date
    while d.weekday()!=target: d+=timedelta(days=1)
    while d<=end_date:
        yield d; d+=timedelta(days=7)

def generate_meetings(db, year, created_by=None):
    services=db.scalars(select(Service).where(Service.status=='ACTIVE')).all(); batch=f'GEN-{year.service_year_id}-{date.today().strftime("%Y%m%d%H%M%S")}'
    created=[]
    for s in services:
        for d in fridays(year.start_date,year.end_date,s.day_of_week):
            exists=db.scalar(select(Meeting).where(Meeting.service_id==s.service_id,Meeting.meeting_date==d))
            if not exists:
                created.append(Meeting(meeting_id=None,service_year_id=year.service_year_id,service_id=s.service_id,meeting_date=d,day_of_week=s.day_of_week,status='SCHEDULED',generation_batch_id=batch,updated_by=created_by))
    return created,batch

def transfer_window_open(today):
    # natural window from last Friday of month through first Friday of next month.
    first_this=today.replace(day=1)
    next_month=(first_this.replace(day=28)+timedelta(days=4)).replace(day=1)
    last_day=next_month-timedelta(days=1)
    last_friday=last_day-timedelta(days=(last_day.weekday()-4)%7)
    first_friday_next=next_month+timedelta(days=(4-next_month.weekday())%7)
    return last_friday<=today<=first_friday_next

def is_url(s): return isinstance(s,str) and s.lower().startswith(('http://','https://'))
