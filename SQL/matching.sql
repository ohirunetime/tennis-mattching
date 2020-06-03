create type mood as ENUM('0','1','2');
create table matching (
  id serial primary key,
  user_one_id int references user_uuid(id) on delete cascade,
  facility_time_id int references facility_time(id) on delete cascade,
  status mood default '0',
  created_at timestamp,
  user_two_id int references user_uuid(id) on delete cascade,
  sex integer,
  age integer,
  level integer
);

alter table matching add column sex integer;
alter table matching add column age integer;
alter table matching add column level integer;

alter table matching add column user_two_id int references user_uuid(id) on delete cascade;
