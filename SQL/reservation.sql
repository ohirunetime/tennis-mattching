create table reservation (
  id serial primary key,
  user_id int references user_uuid(id) on delete cascade,
  facility_time_id int references facility_time(id) on delete cascade,
  created_at timestamp
);
