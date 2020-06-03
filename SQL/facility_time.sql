create table facility_time (
  id serial primary key,
  start_time timestamp ,
  finish_time timestamp ,
  description text,
  field int,
  facility_id int references facility_uuid(id) on delete cascade,
  created_at timestamp;
);
