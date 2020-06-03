create table user_profile (
  name text,
  description text,
  sex integer,
  age integer,
  level integer,
  user_id int references user_uuid(id) on delete cascade unique
);

alter table user_profile add column sex int;
alter table user_profile add column age int;
alter table user_profile add column level int;
