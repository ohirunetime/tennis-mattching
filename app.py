import psycopg2
import uuid
from flask import Flask, render_template, redirect, url_for ,session ,request,g , flash
import datetime
import os

app = Flask(__name__)

app.secret_key = 'hogehoge'


DATABASE_URL=os.environ["DATABASE_URL"]
conn=psycopg2.connect(DATABASE_URL)


# 基本ルート------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/')
def index():
    cur = conn.cursor()
    cur.execute('select facility_id,name,description from facility_profile')
    facility=cur.fetchall()
    conn.commit()
    cur.close()
    return render_template('index.html',facilitys=facility)


@app.route('/info')
def info():
    return render_template('info.html')


@app.route('/facility/<int:facility_id>')
def show_facility(facility_id):
    cur = conn.cursor()
    cur.execute('select id,start_time,finish_time,description,facility_id from facility_time where facility_id = %s' ,(facility_id,))
    facility_times=cur.fetchall()
    conn.commit()
    cur.close()
    return render_template('show.html',facility_times=facility_times)


@app.route('/user/<int:user_id>')
def show_user(user_id):
    cur=conn.cursor()
    cur.execute('select name , description , sex , age , level from user_profile where user_id = %s ',(user_id,))
    user=cur.fetchone()
    conn.commit()
    cur.close()
    return render_template('show_user.html',user=user)


# 通知関連-------------------------------------------------------------------------------------


@app.route('/reservation')
def reservation():
    user_id=session.get('user_id')

    if user_id is None:
        g.user=None
        return render_template('login.html')
    else:
        cur=conn.cursor()
        cur.execute('select matching.id , user_one_id , user_two_id ,facility_time_id , status ,name, start_time , finish_time , facility_time.description ,url from matching \
        inner join facility_time\
        on matching.facility_time_id=facility_time.id\
        inner join facility_profile\
        on facility_time.facility_id=facility_profile.facility_id\
        where user_one_id= %s or user_two_id = %s',(user_id,user_id))

        reservations=cur.fetchall()

        conn.commit()
        cur.close()
        return render_template('reservation.html',reservations=reservations)



# エラーハンドル---------------------------------------------------------------------------------------


@app.errorhandler(404)
def page_not_found(error):
  return render_template('page_not_found.html'), 404

@app.errorhandler(500)
def page_not_found(error):
  return render_template('page_not_found.html'), 500

@app.errorhandler(403)
def page_forbidden(e):
    return render_template('page_not_found.html'), 500



# ユーザー認証関連------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/createUUID',methods=["GET","POST"])
def createUUID():

    if request.method=="GET":
        user_id=session.get('user_id')
        if user_id is None:
            g.user=None
            return render_template('create_user.html')
        else:
            return render_template('index.html')

    if request.method=="POST":
        UUID=str(uuid.uuid4())
        cur = conn.cursor()
        cur.execute('insert into user_uuid (uuid,created_at) values (%s,current_timestamp)',(UUID,))
        conn.commit()
        cur.close()
        return render_template('login.html',UUID=UUID)




@app.route('/login',methods=["GET","POST"])
def login():

    if request.method == 'GET':
        user_id=session.get('user_id')
        if user_id is None:
            g.user=None
            return render_template('login.html')

        else:
            return render_template('index.html')


    if request.method =="POST":
        uuid=str(request.form["uuid"])
        cur=conn.cursor()
        cur.execute("select * from user_uuid where user_uuid.uuid= %s",(uuid,))
        user=cur.fetchone()
        conn.commit()
        cur.close()


        if user is not None:
            session.clear()
            session['user_id']=user[0]
            cur=conn.cursor()
            cur.execute("select * from user_uuid left outer join user_profile on user_uuid.id =user_profile.user_id where user_uuid.uuid= %s",(uuid,))
            user_profile=cur.fetchone()

            conn.commit()
            cur.close()

            if user_profile[3] is None:
                return render_template('dashboard.html',user=user)
            else:
                session['user_sex']=user_profile[5]
                session['user_age']=user_profile[6]
                session['user_level']=user_profile[7]



                flash('ログインしました')



                return render_template('success_login.html')

        else:
            flash('ログイン失敗しました')
            return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('ログアウトしました')
    return redirect(url_for('index'))





@app.before_request
def load_logged_in_user():
    user_id=session.get('user_id')

    if user_id is None:
        g.user=None

    else:
        cur=conn.cursor()
        cur.execute('select * from user_uuid where id = %s',(user_id,))
        g.user=cur.fetchone()
        conn.commit()
        cur.close()



def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return render_template('login.html')
        return view(**kwargs)

    return wrapped_view



# ユーザーprofile関連------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/profile',methods=["GET"])
def profile():
    user_id=session.get('user_id')

    if user_id is None:
        g.user = None
        return render_template('login.html')
    else:
        cur = conn.cursor()
        cur.execute('select name , description , sex , age , level from user_profile where user_id = %s',(user_id,))
        user=cur.fetchone()
        conn.commit()
        cur.close()

        return render_template('profile.html',user=user)




@app.route('/create_profile',methods=["GET","POST"])
def create_profile():

    if request.method =="POST":
        user_id=session.get('user_id')

        if user_id is None:
            g.user=None
            return render_template('index.html')
        else:
            name=request.form["name"]
            sex=request.form["sex"]
            age=request.form["age"]
            level=request.form["level"]

            description=request.form["description"]
            print(name,description)

            cur=conn.cursor()
            cur.execute('select * from user_profile where user_id=%s',(user_id,))
            profile=cur.fetchone()
            conn.commit()
            cur.close()
            if profile is None:
                cur=conn.cursor()
                cur.execute('insert into user_profile (name,sex,age,level,description,user_id) values (%s,%s,%s,%s,%s,%s)',(name,sex,age,level,description,user_id))

                conn.commit()
                cur.close()
                return render_template('success_profile.html')

            return render_template('index.html')




@app.route('/edit_profile',methods=["GET","POST"])
def edit_profile():

    if request.method == "POST":
        user_id=session.get('user_id')

        if user_id is None:
            g.user=None
            return render_template('index.html')

        else:
            name=request.form["name"]
            age=request.form["age"]
            sex=request.form["sex"]
            level=request.form["level"]
            description=request.form["description"]
            cur=conn.cursor()
            cur.execute('update user_profile set name = %s, age = %s ,sex = %s , level = %s , description = %s from user_uuid\
            where user_profile.user_id=%s',(name,age,sex,level,description,user_id))

            cur.execute('select name , description , sex , age , level from user_profile where user_id = %s',(user_id,))
            user=cur.fetchone()
            conn.commit()
            cur.close()

            flash ('プロフィールを変更しました')

            return render_template('profile.html',user=user)













# 施設基本ルート------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/facility_index',methods=["GET","POST"])
def facility_index():

    facility_id=session.get('facility_id')

    if facility_id is None:
        g.facility=None
        return render_template('facility_login.html')
    else:
        date=datetime.date.today() + datetime.timedelta(days=1)

        return render_template('facility_index.html',date=date)






@app.route('/facility_reservation',methods=["GET","POST"])
def facility_reservation():

    facility_id=session.get('facility_id')

    if facility_id is None:
        g.facility=None
        return render_template('facility_login.html')
    else:
        status = str('2')
        cur=conn.cursor()
        cur.execute('select start_time , finish_time , user_one_id , user_two_id from matching inner join facility_time\
        on matching.facility_time_id=facility_time.id\
        where status=%s and facility_time.facility_id=%s\
        order by facility_time.start_time asc' ,(status,facility_id))
        reservations=cur.fetchall()

        conn.commit()
        cur.close()
        return render_template('facility_reservation.html',reservations=reservationsm)






@app.route('/show_facility_time')
def show_facility_time():
    facility_id=session.get('facility_id')

    if facility_id is None:
        g.facility=None
        return render_template('facility_login.html')
    else:
        cur=conn.cursor()
        cur.execute('select * from facility_time where facility_id = %s',(facility_id,))
        facility_times=cur.fetchall()
        conn.commit()
        cur.close()
        return render_template('facility_time_show.html',facility_times=facility_times)






# 施設認証関連------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


@app.route('/create_facility',methods=["GET","POST"])
def create_facility():

    if request.method=="GET":
        facility_id=session.get('facility_id')
        if facility_id is None:
            g.facility=None
            return render_template('create_facility.html')
        else:
            return render_template('index.html')

    if request.method=="POST":
        UUID=str(uuid.uuid4())
        cur = conn.cursor()
        cur.execute('insert into facility_uuid (uuid,created_at) values (%s,current_timestamp)',(UUID,))
        conn.commit()
        cur.close()
        return render_template('facility_login.html',UUID=UUID)


@app.route('/login_facility',methods=["GET","POST"])
def login_facility():

    if request.method == 'GET':
        facility_id=session.get('facility_id')
        if facility_id is None:
            g.facility=None
            return render_template('facility_login.html')

        else:
            return render_template('index.html')


    if request.method =="POST":
        facility_uuid=str(request.form["facility_uuid"])
        cur=conn.cursor()
        cur.execute("select * from facility_uuid where uuid= %s",(facility_uuid,))
        facility=cur.fetchone()
        conn.commit()
        cur.close()


        if facility is not None:
            session.clear()
            session['facility_id']=facility[0]
            print(facility)

            cur=conn.cursor()
            cur.execute("select * from facility_profile where facility_id= %s",(facility[0],))
            facility_profile=cur.fetchone()
            conn.commit()
            cur.close()

            if facility_profile is None:
                return render_template('dashboard_facility.html',facility=facility_profile)
            else:
                return render_template('success_login.html')



@app.route('/logout_facility')
def logout_facility():
    session.clear()
    return redirect(url_for('index'))



@app.before_request
def load_logged_in_facility():
    facility_id=session.get('facility_id')

    if facility_id is None:
        g.facility=None
    else:
        cur=conn.cursor()
        cur.execute('select * from facility_uuid where id = %s',(facility_id,))
        g.facility=cur.fetchone()
        conn.commit()
        cur.close()



def login_required_facility(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.facility is None:
            return render_template('facility_login.html')
        return view(**kwargs)

    return wrapped_view




# 施設profile------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

@app.route('/create_profile_facility',methods=["GET","POST"])
def create_profile_facility():

    if request.method =="POST":
        facility_id=session.get('facility_id')

        if facility_id is None:
            g.facility=None
            return render_template('index.html')
        else:
            name=request.form["name"]
            description=request.form["description"]
            url=request.form["url"]
            print(name,description)

            cur=conn.cursor()
            cur.execute('select * from facility_profile where facility_id=%s',(facility_id,))
            facility_profile=cur.fetchone()
            conn.commit()
            cur.close()
            if facility_profile is None:
                cur=conn.cursor()
                cur.execute('insert into facility_profile (name,description,url,facility_id) values (%s,%s,%s,%s)',(name,description,url,facility_id))
                conn.commit()
                cur.close()
                return render_template('facility_index.html')

            return render_template('index.html')




@app.route('/profile_facility',methods=["GET","POST"])
def profile_facility():
    facility_id=session.get('facility_id')

    if facility_id is None:
        g.user = None
        return render_template('facility_login.html')
    else:
        cur = conn.cursor()
        cur.execute('select * from facility_profile where facility_id = %s',(facility_id,))
        facility=cur.fetchone()
        conn.commit()
        cur.close()

        return render_template('facility_profile.html',facility=facility)








#施設投稿-------------------------------------------------------------------------------------------------------------




@app.route('/create_facility_time',methods=["GET","POST"])

def create_facility_time():

    if request.method == "POST":
        facility_id=session.get('facility_id')


        if facility_id is None:
            g.facility=None
            return render_template('facility_index.html')
        else:
            start_time=request.form["start_time"]
            finish_time=request.form["finish_time"]
            field=request.form["field"]
            description=request.form["description"]

            cur=conn.cursor()
            cur.execute('insert into facility_time (start_time,finish_time,description,field,facility_id) values (%s,%s,%s,%s,%s)',(start_time,finish_time,description,field,facility_id))

            cur.execute('insert into facility_field (field,created_at) values (%s,current_timestamp)',(field,))
            conn.commit()
            cur.close()
            date=datetime.date.today() + datetime.timedelta(days=1)
            return render_template('facility_index.html',date=date)




@app.route('/delete_facility_time',methods=["GET","POST"])
def delete_facility_time():

    if request.method =="POST":
        facility_id=session.get('facility_id')

        if facility_id is None:
            g.facility=None
            return render_template('facility_login.html')
        else:

            post_id=request.form["post_id"]
            cur=conn.cursor()
            cur.execute('delete from facility_time where id = %s',(post_id,))
            conn.commit()
            cur.close()
            return render_template('facility_index.html')





# maching special ------------------------------------------------------------------------------------------------------------------------

@app.route('/time/<int:facility_time_id>')
def addmatching(facility_time_id):
    user_id=session.get('user_id')

    if user_id is None:
        g.user=None
        return render_template('guest.html')
    else:
        sex=session.get('user_sex')
        age=session.get('user_age')
        level=session.get('user_level')
        status = str('1')
        print(sex,age,level)
        cur = conn.cursor()
        cur.execute('select start_time , finish_time , facility_time.description , field , status , matching.sex , matching.age , matching.level , name ,  user_one_id , matching.id , facility_time.id  from facility_time inner join matching \
        on facility_time.id=matching.facility_time_id\
        inner join user_profile \
        on matching.user_one_id=user_profile.user_id\
        where facility_time_id=%s and status=%s and matching.sex in (0 , %s) and  matching.age in (0 , %s) and matching.level = %s ',(facility_time_id,status,sex,age,level))
        users=cur.fetchall()
        conn.commit()
        cur.close()
        return render_template('result.html',users=users)






@app.route('/matching',methods=["GET","POST"])
def matching():

    if request.method == "POST":
        user_id=session.get('user_id')
        facility_time_id=request.form["facility_time_id"]
        sex=request.form["sex"]
        age=request.form["age"]
        level=request.form["level"]
        cur=conn.cursor()
        cur.execute('insert into matching (user_one_id,facility_time_id,sex,age,level,status,created_at ) values (%s,%s,%s,%s,%s,%s,current_timestamp)',(user_id,facility_time_id,sex,age,level,"1"))

        cur.execute('select matching.id , user_one_id , user_two_id ,facility_time_id , status ,name, start_time , finish_time , facility_time.description ,url from matching \
        inner join facility_time\
        on matching.facility_time_id=facility_time.id\
        inner join facility_profile\
        on facility_time.facility_id=facility_profile.facility_id\
        where user_one_id= %s or user_two_id = %s',(user_id,user_id))

        reservations=cur.fetchall()
        conn.commit()
        cur.close()

        flash('募集を開始しました！')

        return render_template('reservation.html',reservations=reservations)


@app.route('/join_matching',methods=["GET","POST"])
def join_matching():

    if request.method == "POST":
        user_id=session.get('user_id')
        matching_id=request.form["matching_id"]
        status=str('2')
        cur=conn.cursor()

        cur.execute('update matching set status = %s ,user_two_id = %s where matching.id = %s',(status,user_id,matching_id))

        cur.execute('select matching.id , user_one_id , user_two_id ,facility_time_id , status ,name, start_time , finish_time , facility_time.description ,url from matching \
        inner join facility_time\
        on matching.facility_time_id=facility_time.id\
        inner join facility_profile\
        on facility_time.facility_id=facility_profile.facility_id\
        where user_one_id= %s or user_two_id = %s',(user_id,user_id))

        reservations=cur.fetchall()
        conn.commit()
        cur.close()

        flash('予約しました！')

        return render_template('reservation.html',reservations=reservations)



@app.route('/cancel_matching',methods=["GET","POST"])
def cancel_matching():

    if request.method == "POST":
        user_id=session.get('user_id')
        matching_id=request.form["matching_id"]
        status=str('1')
        cur=conn.cursor()

        cur.execute('update matching set status = %s ,user_two_id = null where matching.id = %s',(status,matching_id))

        cur.execute('select matching.id , user_one_id , user_two_id ,facility_time_id , status ,name, start_time , finish_time , facility_time.description ,url from matching \
        inner join facility_time\
        on matching.facility_time_id=facility_time.id\
        inner join facility_profile\
        on facility_time.facility_id=facility_profile.facility_id\
        where user_one_id= %s or user_two_id = %s',(user_id,user_id))

        reservations=cur.fetchall()
        conn.commit()
        cur.close()

        flash('予約を取り消しました！')

        return render_template('reservation.html',reservations=reservations)




@app.route('/delete_matching',methods=["GET","POST"])
def delete_matching():

    if request.method == "POST":
        user_id=session.get('user_id')

        matching_id=request.form["matching_id"]
        cur=conn.cursor()
        cur.execute('delete from matching where id = %s',(matching_id,))

        cur.execute('select matching.id , user_one_id , user_two_id ,facility_time_id , status ,name, start_time , finish_time , facility_time.description ,url from matching \
        inner join facility_time\
        on matching.facility_time_id=facility_time.id\
        inner join facility_profile\
        on facility_time.facility_id=facility_profile.facility_id\
        where user_one_id= %s or user_two_id = %s',(user_id,user_id))

        reservations=cur.fetchall()
        conn.commit()
        cur.close()

        flash('募集を取り消しました！')

        return render_template('reservation.html',reservations=reservations)




# --------------------------------------------------------------------------------------------------------------------------


if __name__ == '__main__':
    app.run()
