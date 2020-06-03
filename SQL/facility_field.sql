create table facility_field (
  field int,
  facility_id int references facility_uuid(id) on delete cascade unique,
  created_at timestamp
);
