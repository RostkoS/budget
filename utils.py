from flask import session, Response
from models import User, Category, Record
from datetime import datetime


def get_user():
    return session.get('user_id')

def get_family_id():
    user = User.query.get(get_user())
    return user.family_id if user else None

def get_user_email():
    user_id = get_user()
    if user_id:
        user = User.query.get(user_id)  
        if user:
            return user.email  
    return None  

def export_csv(records, filename):
    def generate():
        output = []
        output.append(["ID", "Date", "Amount", "Category", "Type", "User", "Tags"]) 

        for record in records:
            date_value = record.date
            if isinstance(date_value, str):  
                try:
                    date_value = datetime.strptime(date_value, "%Y-%m-%d") 
                except ValueError:
                    pass  

            formatted_date = date_value.strftime("%Y-%m-%d") if isinstance(date_value, datetime) else date_value

            tags = ", ".join(tag.name for tag in getattr(record, "tags", [])) 

            output.append([
                record.id, 
                formatted_date,
                record.amount, 
                record.category, 
                record.type, 
                record.user.email,
                tags 
            ])

        csv_data = "\n".join(",".join(map(str, row)) for row in output)
        return csv_data.encode("utf-8-sig")  

    response = Response(generate(), content_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return response