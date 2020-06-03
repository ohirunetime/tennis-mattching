create table facility_profile (
  name text,
  description text,
  url text,
  facility_id int references facility_uuid(id) on delete cascade unique
);
