create table "user" (
    id uuid primary key,
    public_id varchar(32) not null unique,
    password varchar(64) not null,
    email varchar(64) not null,
    user_salt varchar(32) not null,
    created_timestamp timestamp not null default (now() at time zone 'utc')
);
create table "session" (
    id uuid primary key,
    user_id uuid not null,
    ip varchar(15),
    country varchar(16),
    user_agent varchar(32),
    is_active bool not null default true,
    expired_at timestamp not null,
    refresh_id uuid not null,
    created_timestamp timestamp not null default (now() at time zone 'utc')
);
